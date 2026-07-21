"""Лесоруб со справочником — agentic RAG на живой игре Cognopolis. Шаблон к модулю 14.

Тот же лесоруб, что в 11.5 (smolagents) и 14.5 (MCP), — но собран на LlamaIndex,
и у агента впервые ДВА сорта инструментов:

- действия в мире: move / gather / get_character / get_map (FunctionTool,
  контракт из 11.5 без единого изменения — cognopolis_tools.py);
- знания: handbook — поиск по справочнику поселенца (куски настоящей вики
  игры, проиндексированные локально — handbook.py).

Пуант лекции 14 живьём: классический RAG ищет всегда — агент решает, КОГДА
искать. Спросите «что теряется при гибели в бою?» — он полистает справочник и
ответит, не сделав ни шага. Попросите «добудь дерево и сдай» — пойдёт рубить,
а в справочник заглянет, только если засомневается в правилах.

Мозг — локальная модель из LM Studio через OpenAILike (без ключей). Какую
модель взять, приложение спрашивает у LM Studio само; дропдаун «Модель-мозг»
позволяет выбрать руками, «↻ Обновить» перечитывает список без перезапуска.

Устройство:
- cognopolis_tools.py — клиент живого API + 4 инструмента-действия («функция
  с паспортом»: имя/description/схема — из самой функции);
- handbook.py        — Loading → Indexing → Querying над knowledge/*.md и
  инструмент handbook (две двери, переключатель HANDBOOK_DOOR);
- knowledge/         — сам справочник: 5 страниц, подрезанных из вики игры;
- helpers.py         — подпорки под слабую модель (затравка, маршрут,
  факт-чек), к LlamaIndex отношения не имеют;
- app.py             — модель, агент, чат на Gradio (этот файл).

Интерфейс поднимается даже без бэкенда: индекс и агент создаются лениво.
Без LM Studio живёт keyless-часть — поиск по справочнику в боковой панели:
retrieval бесплатен и офлайн, платный только синтез (урок модуля 14).
"""

import asyncio
import json
import os
import threading
from pathlib import Path

import gradio as gr
import requests

from llama_index.core.agent.workflow import AgentStream, AgentWorkflow, ToolCallResult
from llama_index.core.workflow import Context
from llama_index.llms.openai_like import OpenAILike

import cognopolis_tools
import handbook
# Подпорки слабой модели (затравка/маршрут/факт-чек) — НЕ инструменты агента;
# на сильной модели helpers.py можно выкинуть.
import helpers


def _load_dotenv() -> None:
    """Прочитать .env рядом с app.py (шаблон — .env-example).

    Настоящие переменные окружения важнее: .env заполняет только пропуски."""
    env_file = Path(__file__).with_name(".env")
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# LM Studio: дефолтный адрес его OpenAI-совместимого сервера.
LM_BASE = os.getenv("LM_BASE", "http://localhost:1234/v1")
# Адрес игры фиксирован на прод; для своего Cognopolis-сервера — .env.
BASE_URL = os.getenv("COGNOPOLIS_BASE_URL", cognopolis_tools.DEFAULT_BASE_URL).rstrip("/")

# --- Состояние процесса (ленивое; интерфейс живёт и без бэкенда) ------------
_index = None              # VectorStoreIndex над knowledge/ (строится один раз)
_index_lock = threading.Lock()
_agent = None
_agent_key = None          # чем определён текущий агент: (токен, модель)
_ctx = None                # Context агента — «память, которую держат в руках»
_cogno_snapshot = None     # последний известный character из живого API

# Поколение: каждый сброс увеличивает счётчик, и бегущий прогон агента
# замечает это между событиями и останавливается (см. respond).
_world_generation = 0

NO_LMSTUDIO_MESSAGE = (
    "Агент пока спит: локальный запуск ждёт LM Studio (это модель-мозг), а "
    f"сервер {LM_BASE} не отвечает (или в нём нет ни одной модели).\n\n"
    "Откройте LM Studio, во вкладке Developer нажмите Start server (или "
    "`lms server start` в терминале) и скачайте инструкт-модель с поддержкой "
    "tool use (в каталоге помечены молотком; например Qwen2.5-7B-Instruct), "
    "затем нажмите «↻ Обновить» у дропдауна модели и напишите снова.\n\n"
    "Пока модели нет, работает keyless-часть шаблона: поиск по справочнику "
    "в боковой панели — retrieval живёт без LLM."
)

NO_CHARACTER_TOKEN_MESSAGE = (
    "Нужен под-токен персонажа Cognopolis: этот агент играет только в живую "
    "игру, мок-мира тут нет.\n\n"
    "Впишите под-токен своего жителя (Character.token) в поле «Под-токен "
    "персонажа Cognopolis» вверху и отправьте команду снова. Токен остаётся "
    "в этом локальном процессе и уходит только на сам API игры."
)

# Системные инструкции — правила МИРА и порядок работы. Контракт инструментов
# сюда не переписываем: их «паспорта» агент читает сам. Написаны под слабую
# локальную модель (LM Studio): сильной они не мешают, слабую держат на рельсах.
LIVE_INSTRUCTIONS = (
    "Ты управляешь РЕАЛЬНЫМ жителем поселения Cognopolis на сетке 7x7 (x и y "
    "от 0 до 6). Мир персистентный: житель стоит там, где закончил прошлый "
    "раз, а НЕ обязательно дома.\n"
    "У тебя два сорта инструментов: ДЕЙСТВИЯ в мире (move, gather, "
    "get_character, get_map) и ЗНАНИЯ (handbook — справочник правил игры). "
    "Правила ниже покрывают только добычу; про всё остальное — бой, гибель, "
    "враги, респаун, кулдауны, коды ошибок — СНАЧАЛА спроси handbook, а не "
    "угадывай. Состояние мира справочник не знает: позицию и карту бери "
    "инструментами. Если вопрос человека — чисто про правила игры, ответь по "
    "справочнику и не делай действий в мире.\n"
    "Порядок работы над задачей в мире:\n"
    "1) СНАЧАЛА вызови get_character и прочитай своё РЕАЛЬНОЕ [x, y] — не "
    "предполагай, что ты дома [0, 0].\n"
    "2) Вызови get_map. Тайлы с content 'tree' дают wood, 'rock' — stone. "
    "Выбери ближайший нужный тайл; на тайлы с врагами (goblin, wolf, ogre) "
    "НЕ ходи — сборщику там делать нечего, обходи их по другой оси.\n"
    "3) Иди к цели [tx, ty], меняя ОДНУ координату за один move. Правило "
    "направлений: если твой x больше tx — иди west (x уменьшается); если "
    "меньше — east; если твой y больше ty — north (y уменьшается); если "
    "меньше — south (east = x+1, west = x-1, south = y+1, north = y-1). "
    "После КАЖДОГО move читай новый [x, y] из ответа: он должен приближаться "
    "к цели. Если пришла ошибка at_map_edge — ты выбрал сторону НАРУЖУ карты, "
    "выбери противоположную.\n"
    "4) Когда стоишь РОВНО на тайле ресурса — вызови gather. Ресурс попадёт в "
    "рюкзак (inventory), это ещё НЕ склад.\n"
    "5) Чтобы «сдать на склад», ОБЯЗАТЕЛЬНО вернись на дом [0, 0] тем же "
    "правилом — только дом разгружает рюкзак на склад (в ответе move появится "
    "banked). Отдельного deposit нет; пока ты не на [0, 0], ресурс не сдан.\n"
    "Если в сообщении дан «Рекомендуемый маршрут» — выполняй ВСЕ его шаги по "
    "порядку до конца, включая возврат домой; по одному вызову за раз.\n"
    "ПРОВЕРКА перед финальным ответом: вызови get_character. Задача «добыть и "
    "сдать» выполнена ТОЛЬКО если нужный ресурс лежит в stored (склад), а в "
    "inventory (рюкзак) его нет, и твоя позиция [0, 0]. Если ресурс всё ещё в "
    "inventory — ты НЕ сдал: иди на [0, 0]. Не объявляй успех без проверки.\n"
    "Ошибка от инструмента — не провал, а подсказка: прочитай её code и "
    "message и продолжай. character_on_cooldown значит «занят долю секунды» — "
    "повтори тот же вызов."
)


# --- Селектор моделей LM Studio (тот же приём, что в 14.5) -------------------

AUTO_MODEL = ""  # значение пункта «Автовыбор» в дропдауне


def _lm_models():
    """Список моделей LM Studio: [(id, state, type), ...].

    Гоча автодетекта: /v1/models при включённом JIT loading отдаёт все
    СКАЧАННЫЕ модели, а не загруженную в память — первым может оказаться
    что угодно. Поэтому сперва спрашиваем расширенный /api/v0/models, где у
    модели есть state (loaded/not-loaded) и type (llm/vlm/embeddings), и
    только для старых LM Studio без /api/v0 падаем на грубую эвристику."""
    root = LM_BASE.rsplit("/v1", 1)[0]
    try:
        r = requests.get(f"{root}/api/v0/models", timeout=2)
        r.raise_for_status()
        return [(m["id"], m.get("state"), m.get("type"))
                for m in r.json().get("data", [])
                if m.get("type") in ("llm", "vlm")]
    except Exception:  # noqa: BLE001 — старый LM Studio без /api/v0, идём дальше
        pass
    try:
        r = requests.get(f"{LM_BASE}/models", timeout=2)
        r.raise_for_status()
        return [(item["id"], None, None) for item in r.json().get("data", [])
                if "embed" not in item["id"].lower()]
    except Exception:  # noqa: BLE001 — любой сбой значит «сервера нет»
        return []


def _pick_default(models):
    """Автовыбор: env LM_MODEL_ID > загруженная llm > загруженная vlm > первая."""
    forced = os.getenv("LM_MODEL_ID")
    if forced:
        return forced
    for want_type in ("llm", "vlm"):
        loaded = [mid for mid, state, mtype in models
                  if state == "loaded" and mtype == want_type]
        if loaded:
            return loaded[0]
    return models[0][0] if models else None


def _resolve_model(model_choice, models):
    """Выбор из дропдауна; пусто/Автовыбор/пропавший id → автовыбор."""
    ids = [mid for mid, _, _ in models]
    if model_choice and model_choice != AUTO_MODEL and model_choice in ids:
        return model_choice
    return _pick_default(models)


def model_choices(selected=None):
    """Наполнить дропдаун: ● — загружена в память, ○ — подгрузится на лету."""
    models = _lm_models()
    choices = [("Автовыбор (загруженная, иначе первая доступная)", AUTO_MODEL)]
    for mid, state, mtype in models:
        mark = "● " if state == "loaded" else "○ "
        label = mark + mid + (f" · {mtype}" if mtype else "")
        choices.append((label, mid))
    keep = selected if selected in [v for _, v in choices] else AUTO_MODEL
    return gr.update(choices=choices, value=keep)


def _make_llm(model_id):
    """Мозг из LM Studio — OpenAILike, та же строка, что в Блоке 5 ноутбука.

    is_function_calling_model управляет сборкой агента: с True
    AgentWorkflow.from_tools_or_functions соберёт FunctionAgent (нативный
    tool calling), с False — сам откатится на ReActAgent (текстовый цикл
    рассуждений, работает с любой моделью). Модель без «молотка» в каталоге
    LM Studio → поставьте LM_TOOL_CALLING=0 в .env."""
    return OpenAILike(
        model=model_id,
        api_base=LM_BASE,
        api_key="lm-studio",  # LM Studio ключ не проверяет, но клиенту нужна заглушка
        is_chat_model=True,
        is_function_calling_model=os.getenv("LM_TOOL_CALLING", "1") != "0",
        context_window=32768,  # дефолтные 3900 обрезали бы затравку с картой
        max_tokens=2096,
        temperature=0.2,  # локальные 4-8B путаются на 0.5 — держим их на рельсах
    )


# --- Индекс справочника (ленивый, один на процесс) ---------------------------

def _ensure_index():
    """Собрать индекс при первом обращении. Первый раз качает эмбеддер (~0.5 ГБ)."""
    global _index
    with _index_lock:
        if _index is None:
            _index = handbook.build_index()
    return _index


# --- Пробы живого API (для панели и затравки; НЕ инструменты агента) ---------

def _probe_character(token: str) -> dict:
    """Проверить под-токен и снять жителя ДО прогона — честная обучающая
    ошибка сразу, а не падение в середине."""
    r = requests.get(f"{BASE_URL}/character",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if r.status_code >= 400:
        try:
            err = r.json().get("error", {})
        except Exception:  # noqa: BLE001
            err = {}
        raise RuntimeError(f"{err.get('code', 'http_error')}: "
                           f"{err.get('message', r.text[:200])}")
    return r.json()


def _probe_map() -> dict:
    """Карта для затравки (публичный эндпоинт). Сбой не роняет чат."""
    try:
        r = requests.get(f"{BASE_URL}/map", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:  # noqa: BLE001
        return {"tiles": []}


def _set_cogno_snapshot(character: dict):
    """Колбэк инструментов: запомнить последнего character для панели."""
    global _cogno_snapshot
    _cogno_snapshot = character


# --- Агент -------------------------------------------------------------------

def _ensure_agent(cogno_token: str, model_id: str):
    """Собрать (или переиспользовать) агента под текущие токен+модель.

    Память агента — Context — живёт рядом: лекция называет её «объектом,
    который вы явно держите в руках», вот он и лежит в глобальной переменной.
    По умолчанию каждый прогон стартует с ЧИСТЫМ Context: накопленная история
    топит слабую локальную 7B (проверено в 11.5/14.5 — модель фабрикует
    «уже сдал» без единого вызова), а непрерывность даёт сам персистентный
    мир. Настоящая память диалога — AGENT_MEMORY=1 в .env: тогда Context
    переживает прогоны до кнопки «Сбросить», и уточнения вроде «а теперь то
    же с камнем» начинают работать."""
    global _agent, _agent_key, _ctx
    key = (cogno_token, model_id)
    rebuilt = False
    if _agent is None or _agent_key != key:
        llm = _make_llm(model_id)
        client = cognopolis_tools.CognopolisClient(BASE_URL, cogno_token)
        tools = cognopolis_tools.build_world_tools(client, _set_cogno_snapshot)
        tools.append(handbook.build_handbook_tool(_ensure_index(), llm))
        _agent = AgentWorkflow.from_tools_or_functions(
            tools, llm=llm, system_prompt=LIVE_INSTRUCTIONS,
        )
        _agent_key = key
        rebuilt = True
    if rebuilt or _ctx is None or os.getenv("AGENT_MEMORY", "0") != "1":
        _ctx = Context(_agent)
    return _agent, _ctx


# --- Тексты боковых панелей ---------------------------------------------------

def world_state_text():
    """Снимок реального персонажа для боковой панели (последний известный)."""
    return json.dumps(
        _cogno_snapshot or {"note": "впишите под-токен и отправьте команду персонажу"},
        ensure_ascii=False, indent=2,
    )


def agent_tools_text():
    """Список инструментов агента: 4 действия + справочник (и какая дверь)."""
    client = cognopolis_tools.CognopolisClient(BASE_URL, "")
    lines = []
    for t in cognopolis_tools.build_world_tools(client, lambda c: None):
        # description у FunctionTool начинается со строки-сигнатуры — паспорт
        # для модели; человеку в панель идёт первое предложение docstring.
        doc = t.metadata.description.split("\n", 1)[-1]
        first = " ".join(doc.split()).split(". ")[0].rstrip(".")
        lines.append(f"- `{t.metadata.name}` — {first}.")
    door = os.getenv("HANDBOOK_DOOR", "retriever").strip().lower()
    door_note = ("query engine: куски пересказывает LLM"
                 if door == "query_engine"
                 else "retriever: куски справочника дословно, без LLM-пересказа")
    lines.append(f"- `handbook` — справочник поселенца ({door_note}).")
    return "\n".join(lines)


def handbook_search(query):
    """Дверь-retriever для человека: топ-3 куска со score, целиком без LLM."""
    try:
        return handbook.search(_ensure_index(), query)
    except Exception as exc:  # noqa: BLE001 — обычно это первая загрузка эмбеддера
        return (f"Поиск не получился: {exc!r}\n\n"
                "Если это первый запуск — подождите, пока докачается "
                "эмбеддинг-модель (~0.5 ГБ), и попробуйте снова.")


# --- Сброс и ввод --------------------------------------------------------------

def _do_reset():
    """Очистить агента, память (Context) и снимок панели; поколение растёт,
    чтобы остановить бегущий прогон. Реальный мир не трогаем — он общий."""
    global _agent, _agent_key, _ctx, _world_generation, _cogno_snapshot
    _world_generation += 1
    _agent = None
    _agent_key = None
    _ctx = None
    _cogno_snapshot = None


def store_message(message):
    """Сохранить текст из поля ввода и очистить поле (паттерн шаблона 10.2)."""
    return message, ""


def _trim(text: str, limit: int = 600) -> str:
    text = str(text)
    return text if len(text) <= limit else text[:limit] + f"… (+{len(text) - limit} символов)"


# --- Цикл агента ----------------------------------------------------------------

async def respond(message, history, cogno_token, model_choice):
    """Обработать сообщение: гейты → затравка → живой стрим событий агента.

    Асинхронный генератор: AgentWorkflow стримит события (ToolCallResult,
    AgentStream), Gradio 5 умеет async-генераторы из коробки — мост руками
    не нужен. Каждый yield — пара (чат, панель персонажа)."""
    text = (message or "").strip()
    cogno_token = (cogno_token or "").strip()

    if not text:
        yield history, world_state_text()
        return

    history = history + [gr.ChatMessage(role="user", content=text)]
    yield history, world_state_text()

    # Мозг: без LM Studio не падаем, а объясняем, чего не хватает.
    # Все пробы — через to_thread: respond крутится на общем event loop
    # Gradio, и голый requests заморозил бы весь интерфейс на свой timeout.
    models = await asyncio.to_thread(_lm_models)
    if not models and not os.getenv("LM_MODEL_ID"):
        history.append(gr.ChatMessage(role="assistant", content=NO_LMSTUDIO_MESSAGE))
        yield history, world_state_text()
        return
    model_id = _resolve_model(model_choice, models)

    # Игра только онлайн: без под-токена не работаем и не подменяем мок-миром.
    if not cogno_token:
        history.append(gr.ChatMessage(role="assistant", content=NO_CHARACTER_TOKEN_MESSAGE))
        yield history, world_state_text()
        return

    # Проба токена ДО прогона + материал для затравки (мир персистентный).
    try:
        char = await asyncio.to_thread(_probe_character, cogno_token)
        _set_cogno_snapshot(char)
        yield history, world_state_text()
    except Exception as exc:  # noqa: BLE001
        history.append(gr.ChatMessage(
            role="assistant",
            content=(f"Не удалось подключиться к персонажу Cognopolis: {exc}\n\n"
                     "Проверьте под-токен персонажа (Character.token) и адрес игры."),
        ))
        yield history, world_state_text()
        return

    # Подпорки — только задачам-действиям: маршрутная подсказка командует
    # «иди», и подмешанная к чистому вопросу она уводит агента рубить вместо
    # справочника (поймано живым прогоном). Вопрос уходит как есть — решение
    # «листать ли handbook» остаётся за агентом, в этом и пуант урока.
    if helpers.is_world_task(text):
        gmap = await asyncio.to_thread(_probe_map)
        task = helpers.facts_seed(char, gmap, text)
        if os.getenv("WEAK_MODEL_ROUTE", "1") != "0":
            task += "\n" + helpers.route_hint(char, gmap, text)
        task += "\n\nЗадача: " + text
    else:
        task = text

    try:
        fresh = _agent is None
        # Сборка агента (и индекса) — в отдельном потоке: первый раз она качает
        # эмбеддер и строит индекс, event loop блокировать нельзя.
        agent, ctx = await asyncio.to_thread(_ensure_agent, cogno_token, model_id)
        if fresh:
            who = char.get("name") or char.get("id", "?")
            history.append(gr.ChatMessage(
                role="assistant",
                content=(f"Подключено к жителю Cognopolis «{who}». Модель: {model_id}. "
                         f"Инструменты:\n{agent_tools_text()}"),
            ))
            yield history, world_state_text()

        generation = _world_generation
        # max_iterations: дефолтные 20 LLM-ходов библиотеки — впритык для
        # живой карты (худший маршрут + заходы в справочник + повторы по
        # кулдауну легко переваливают за 20). Даём запас, как max_steps=40
        # в шаблонах 11.5/14.5.
        handler = agent.run(user_msg=task, ctx=ctx, max_iterations=60)
        streaming = False  # открыт ли сейчас «печатающийся» пузырь ответа
        async for ev in handler.stream_events():
            if _world_generation != generation:
                # «Сбросить» нажали во время прогона: гасим воркфлоу и чат.
                await handler.cancel_run()
                yield [], world_state_text()
                return
            if isinstance(ev, ToolCallResult):
                # Окно в решения агента: какой инструмент, с чем, что ответил.
                args = json.dumps(ev.tool_kwargs, ensure_ascii=False)
                out = _trim(ev.tool_output.content)
                history.append(gr.ChatMessage(
                    role="assistant",
                    content=f"`{ev.tool_name}({args})`\n\n```\n{out}\n```",
                    metadata={"title": f"🔧 {ev.tool_name}"},
                ))
                streaming = False
                yield history, world_state_text()
            elif isinstance(ev, AgentStream) and ev.delta:
                if streaming:
                    history[-1].content += ev.delta
                else:
                    history.append(gr.ChatMessage(role="assistant", content=ev.delta))
                    streaming = True
                yield history, world_state_text()
        await handler  # дождаться финала воркфлоу (и поднять его ошибку, если была)
        if _world_generation != generation:
            return  # «Сбросить» нажали на самом финале — чат уже чист, не пачкаем

        # Факт-чек: слова агента vs реальное состояние. Слабая модель склонна
        # объявить успех, не вернувшись на склад, — показываем правду из игры.
        # Чистым вопросам про правила факт-чек не нужен: мир они не трогали.
        if helpers.is_world_task(text):
            try:
                final_char = await asyncio.to_thread(_probe_character, cogno_token)
                if _world_generation != generation:
                    return
                _set_cogno_snapshot(final_char)
                history.append(gr.ChatMessage(
                    role="assistant", content=helpers.fact_check(char, final_char, text)))
                yield history, world_state_text()
            except Exception:  # noqa: BLE001 — факт-чек не должен ронять чат
                pass
    except Exception as exc:  # noqa: BLE001 — любую беду показываем в чате
        if _world_generation != generation:
            return
        hint = (
            "Частые причины: LM Studio выгрузил модель или сервер остановлен; "
            "модель без поддержки tool use (в каталоге LM Studio ищите значок-"
            "молоток) — для такой поставьте LM_TOOL_CALLING=0 в .env, агент "
            "пересоберётся как ReActAgent. «Max iterations reached» — агент "
            "выбрал лимит ходов: упростите задачу или повторите. После правок "
            "нажмите «Сбросить»."
        )
        history.append(gr.ChatMessage(
            role="assistant",
            content=f"Агент упал с ошибкой: {exc!r}\n\n{hint}",
        ))
        yield history, world_state_text()


def reset_click():
    """Кнопка «Сбросить»: чистим чат, агента и Context (мир не трогаем)."""
    _do_reset()
    return [], world_state_text()


# --- Gradio UI -------------------------------------------------------------------

def build_demo():
    """Собрать интерфейс (функция, а не код при импорте: `import app` из
    тестов не должен тянуть ничего тяжёлого)."""
    with gr.Blocks(title="Лесоруб со справочником — agentic RAG на живой игре",
                   fill_height=True) as demo:
        gr.Markdown(
            "## Лесоруб со справочником — agentic RAG на живой игре Cognopolis\n"
            "LlamaIndex-агент с двумя сортами инструментов: действия в мире "
            "(move, gather, get_character, get_map) и база знаний (`handbook` — "
            "справочник поселенца, куски настоящей вики игры). Агент ходит на "
            "**реальный API игры** https://kindomklaster.com и сам решает, когда "
            "листать справочник, а когда шагать. Спросите «что теряется при "
            "гибели в бою?» — и посмотрите, какой инструмент он выберет; "
            "попросите «добудь одно дерево (wood) и сдай его на склад» — и "
            "следите за вызовами в чате.\n\n"
            f"*Модель (мозг): локальный LM Studio ({LM_BASE}), выбирается ниже. "
            "Поиск по справочнику справа работает и без модели — retrieval "
            "бесплатен, платный только синтез.*"
        )
        token_input = gr.Textbox(
            type="password",
            label="Под-токен персонажа Cognopolis (обязательно)",
            placeholder="Character.token вашего жителя",
            value=os.getenv("COGNOPOLIS_TOKEN", ""),
            info="Можно не вписывать руками: скопируйте .env-example в .env и "
                 "заполните COGNOPOLIS_TOKEN — поле предзаполнится само.",
        )
        with gr.Row():
            model_dropdown = gr.Dropdown(
                choices=[("Автовыбор (загруженная, иначе первая доступная)", AUTO_MODEL)],
                value=AUTO_MODEL,
                label="Модель-мозг (LM Studio)",
                info="● загружена · ○ подгрузится на лету",
                scale=5,
            )
            refresh_btn = gr.Button("↻ Обновить", scale=1)
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Лесоруб со справочником",
                                     type="messages", scale=1)
                with gr.Row():
                    text_input = gr.Textbox(
                        lines=1,
                        label="Сообщение агенту",
                        placeholder="Добудь одно дерево (wood) и сдай его на склад",
                        scale=5,
                    )
                    send_btn = gr.Button("Отправить", variant="primary", scale=1)
            with gr.Column(scale=1):
                state_box = gr.Code(
                    # Именно функция, не вызов: callable Gradio перевычисляет
                    # на каждую загрузку страницы.
                    value=world_state_text,
                    language="json",
                    label="Персонаж (живой мир)",
                )
                gr.Markdown("**Справочник (retriever, без LLM)** — первая из "
                            "«трёх дверей к индексу»: топ-3 куска со score, "
                            "живёт без модели и без ключей.")
                hb_query = gr.Textbox(
                    lines=1, show_label=False,
                    placeholder="как сдать ресурсы на склад?",
                )
                hb_btn = gr.Button("Искать в справочнике")
                hb_out = gr.Markdown("")
                tools_box = gr.Markdown(value=agent_tools_text,
                                        label="Инструменты агента", container=True)
                reset_btn = gr.Button("Сбросить")

        stored_message = gr.State("")
        text_input.submit(
            store_message, [text_input], [stored_message, text_input]
        ).then(respond, [stored_message, chatbot, token_input, model_dropdown],
               [chatbot, state_box])
        send_btn.click(
            store_message, [text_input], [stored_message, text_input]
        ).then(respond, [stored_message, chatbot, token_input, model_dropdown],
               [chatbot, state_box])
        hb_query.submit(handbook_search, [hb_query], [hb_out])
        hb_btn.click(handbook_search, [hb_query], [hb_out])
        reset_btn.click(reset_click, None, [chatbot, state_box])
        refresh_btn.click(model_choices, model_dropdown, model_dropdown)
        demo.load(model_choices, model_dropdown, model_dropdown)
    return demo


if __name__ == "__main__":
    # ssr_mode=False: экспериментальный SSR-режим Gradio 5 поднимает отдельный
    # Node.js-сервер — лишняя точка отказа, а на HF Spaces он валит контейнер.
    build_demo().launch(ssr_mode=False)
