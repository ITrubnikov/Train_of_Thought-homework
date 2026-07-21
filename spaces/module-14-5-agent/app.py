"""Лесоруб через MCP — агент на живой игре Cognopolis. Шаблон к модулю 14.5.

Тот же чат-агент на живой игре, что в проектах 11.5 и 13.6 (реальный API
https://kindomklaster.com, настоящий житель по его под-токену, мозг —
локальная модель из LM Studio), но с главным поворотом лекции 14.5: в этом
файле НЕТ ни одного игрового инструмента. В 11.5 tools были классами прямо в
коде проекта (cognopolis_tools.py), в 13.6 — те же плюс load_skill; здесь
файл агента про инструменты не знает ничего. Он запускает MCP-сервер
cognopolis_mcp_server.py stdio-подпроцессом, забирает у него каталог
(initialize + tools/list по JSON-RPC — всё спрятано в ToolCollection.from_mcp)
и отдаёт агенту то, что сервер объявил. Допишете серверу новый tool — агент
увидит его без единой правки этого файла: «контракт, вынесенный в сервис».

Устройство:
- cognopolis_mcp_server.py — MCP-сервер поверх живого API Cognopolis
  (дословно тот же файл, что в папке mcp-server/ домашки 14.5): tools move / gather /
  get_character / get_map, resource cognopolis://map, под-токен из env
  COGNOPOLIS_TOKEN;
- app.py — модель из LM Studio, ToolCollection.from_mcp и чат на Gradio
  (этот файл; игровых инструментов в нём не определено).

MCP-соединение (stdio-подпроцесс сервера) открывается при первом сообщении и
живёт между сообщениями чата; закрывается кнопкой «Сбросить» и при смене
токена — под-токен сервер читает из окружения один раз, на старте подпроцесса.

Интерфейс поднимается даже без бэкенда: соединение и агент создаются лениво,
при первом сообщении; без LM Studio или без под-токена персонажа агент
вежливо объясняет, чего не хватает."""

import json
import os
import sys
from pathlib import Path

import gradio as gr
import requests
from mcp import StdioServerParameters
from smolagents import OpenAIServerModel, ToolCallingAgent, ToolCollection
from smolagents.gradio_ui import stream_to_gradio

# Подпорки под СЛАБУЮ локальную модель (затравка фактов, маршрут, факт-чек) —
# те же, что в шаблонах 11.5 и 13.6, честно вынесены отдельным файлом. Это НЕ
# игровые инструменты (их агент по-прежнему берёт только из MCP-сервера), а
# внешняя обвязка мозга; на сильной модели helpers.py можно выкинуть.
import helpers


def _load_dotenv() -> None:
    """Подхватить .env рядом с app.py (шаблон — .env-example): токен и переопределения
    LM_MODEL_ID / LM_BASE / COGNOPOLIS_BASE_URL. Настоящие переменные окружения ВАЖНЕЕ —
    .env заполняет только пропуски. Тот же загрузчик встроен в cognopolis_mcp_server.py,
    так что подпроцесс сервера видит тот же .env сам."""
    env_file = Path(__file__).with_name(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()

# LM Studio: дефолтный адрес его OpenAI-совместимого сервера.
LM_BASE = os.getenv("LM_BASE", "http://localhost:1234/v1")

# Адрес живой игры. Тот же env читает и сервер в подпроцессе (подпроцесс
# наследует окружение) — панель и инструменты смотрят в один мир.
BASE_URL = os.getenv("COGNOPOLIS_BASE_URL", "https://kindomklaster.com").rstrip("/")

# Сервер, у которого агент возьмёт инструменты, — файл рядом с app.py.
SERVER_PATH = Path(__file__).parent / "cognopolis_mcp_server.py"

# --- Состояние процесса (ленивое; интерфейс живёт и без бэкенда) ------------
_mcp_cm = None             # контекст-менеджер from_mcp: __enter__ сделан, ждёт __exit__
_tool_collection = None    # ToolCollection с инструментами, приехавшими из сервера
_agent = None
_agent_key = None          # чем определён текущий агент: (токен, модель)
_cogno_snapshot = None     # последний известный character из живого API

# Поколение: каждый сброс увеличивает счётчик, и бегущий прогон агента
# замечает это между шагами и останавливается (см. respond).
_world_generation = 0

NO_LMSTUDIO_MESSAGE = (
    "Агент пока спит: локальный запуск ждёт LM Studio (это модель-мозг), а "
    f"сервер {LM_BASE} не отвечает.\n\n"
    "Откройте LM Studio, во вкладке Developer нажмите **Start server** (или в "
    "терминале `lms server start`). Загружать модель заранее не обязательно — "
    "выбранную из списка LM Studio подтянет на лету; но лучше брать инструкт-"
    "модель с поддержкой tool use (в каталоге помечены молотком; например "
    "Qwen2.5-7B-Instruct). Затем нажмите «↻ Обновить» над списком моделей, "
    "выберите мозг и напишите снова."
)

NO_CHARACTER_TOKEN_MESSAGE = (
    "Нужен под-токен персонажа Cognopolis: этот агент играет только в живую "
    "игру, мок-леса тут нет.\n\n"
    "Впишите под-токен своего жителя (Character.token) в поле «Под-токен "
    "персонажа Cognopolis» вверху и отправьте команду снова. Токен остаётся "
    "в этом локальном процессе, уходит подпроцессу MCP-сервера через "
    "переменную окружения и дальше — только на сам API игры."
)

# Инструкции агенту — МЕХАНИКА живого мира. Заметьте: про сами инструменты тут
# ни слова лишнего (их описания агент берёт из каталога MCP-сервера) — здесь
# только правила мира и как считать шаги, потому что именно на навигации слабая
# локальная 7B срывается. Модель из 11.5/13.6, та же кухня.
LIVE_INSTRUCTIONS = (
    "Ты управляешь РЕАЛЬНЫМ жителем поселения Cognopolis на сетке 7x7 (x и y от 0 "
    "до 6) через инструменты MCP-сервера. Мир персистентный: житель стоит там, где "
    "закончил прошлый раз, а НЕ обязательно дома.\n\n"
    "КАК УСТРОЕН МИР:\n"
    "- get_character — прочитать своё РЕАЛЬНОЕ [x, y], рюкзак (inventory) и склад "
    "(stored). Не предполагай, что ты дома [0, 0].\n"
    "- get_map — тайлы: content 'tree' даёт wood, 'rock' даёт stone; на тайлы с "
    "врагами (goblin, wolf, ogre) не ходи — это драка.\n"
    "- move меняет ОДНУ координату: east = x+1, west = x-1, south = y+1, north = "
    "y-1. Чтобы дойти до [tx, ty]: если твой x больше tx — иди west, меньше — east; "
    "если твой y больше ty — north, меньше — south. После КАЖДОГО move читай новый "
    "[x, y] из ответа и решай следующий шаг по нему, не считай весь путь наперёд. "
    "Ошибка at_map_edge — шаг был НАРУЖУ карты, возьми противоположную сторону.\n"
    "- gather добывает ресурс с тайла, на котором стоишь РОВНО; добыча падает в "
    "рюкзак (inventory) — это ещё НЕ склад. Ошибка no_resource_here — ты не на "
    "клетке ресурса, сначала встань на неё.\n"
    "- Отдельного deposit НЕТ: дом [0, 0] сам разгружает рюкзак на склад (в ответе "
    "move появляется banked). Пока ты не на [0, 0], добытое НЕ сдано.\n"
    "- Ошибка инструмента — не провал, а подсказка: читай code и message. "
    "character_on_cooldown значит «занят долю секунды» — повтори тот же вызов.\n\n"
    "ПОРЯДОК. Если в задаче дан «Рекомендуемый маршрут» — иди строго по нему, шаг "
    "за шагом, сверяя [x, y] в ответе каждого move; не блуждай и не выдумывай свой "
    "путь. Если маршрута нет — начни с get_character и get_map, найди цель по карте "
    "и иди к ней. Заявляй задачу выполненной ТОЛЬКО после того, как get_character "
    "покажет результат в складе (stored)."
)


# Значение выпадающего списка «выбрать модель самому не хочу — реши сам».
AUTO_MODEL = ""


def _lm_models():
    """Список разговорных моделей LM Studio: [(id, state, type), ...].

    Пустой список = сервер молчит (не запущен Start server). Спрашиваем
    расширенный /api/v0/models — он различает state (loaded/not-loaded) и type
    (llm / vlm / embeddings); берём только разговорные (llm, vlm), эмбеддеры
    выкидываем. На старом LM Studio без /api/v0 падаем на /v1/models, где ни
    state, ни типа нет (тогда state=type=None, и в UI просто нет пометок).

    Гоча: /v1/models при включённом JIT loading отдаёт ВСЕ скачанные модели, а
    не загруженную в память — поэтому для «какая сейчас в памяти» нужен именно
    /api/v0/models со state=loaded (см. _pick_default)."""
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
    """Автовыбор модели из списка _lm_models: приоритет — загруженная llm.

    Переопределяется переменной окружения LM_MODEL_ID. Дальше: загруженная в
    память llm > загруженная vlm > первая доступная (её LM Studio подгрузит на
    лету, JIT). None — если список пуст (сервер молчит)."""
    forced = os.getenv("LM_MODEL_ID")
    if forced:
        return forced
    for want_type in ("llm", "vlm"):
        for mid, state, mtype in models:
            if state == "loaded" and mtype == want_type:
                return mid
    return models[0][0] if models else None


def _detect_lm_model():
    """Автовыбор модели (обёртка над _lm_models + _pick_default)."""
    return _pick_default(_lm_models())


def _resolve_model(model_choice, models):
    """Какую модель реально отдать агенту по выбору из выпадающего списка.

    Пусто/AUTO или устаревший id (модель уже удалили/выгрузили из каталога) →
    автовыбор. Иначе — ровно то, что выбрал пользователь (LM Studio подгрузит
    её на лету, если она ещё не в памяти)."""
    chosen = (model_choice or "").strip()
    available = {mid for mid, _, _ in models}
    return chosen if chosen in available else _pick_default(models)


def _make_model(model_id):
    """Модель-мозг из LM Studio (одна строка лекции «какой модели отдать tools»)."""
    return OpenAIServerModel(
        model_id=model_id,
        api_base=LM_BASE,
        api_key="lm-studio",  # LM Studio ключ не проверяет, но клиенту нужна заглушка
        max_tokens=2096,
        temperature=0.2,  # локальные 4-8B путаются на 0.5 — держим их на рельсах
    )


def model_choices(selected=None):
    """Пункты выпадающего списка моделей: Автовыбор + все чат-модели LM Studio.

    Метка показывает состояние: ● загружена в память, ○ скачана но не загружена
    (LM Studio подгрузит её на лету при первом сообщении), плюс тип (llm/vlm).
    Значение пункта — id модели (или AUTO для автовыбора). Возвращает gr.update,
    чтобы обновлять список и при загрузке страницы, и по кнопке «Обновить»;
    текущий выбор сохраняем, если он ещё доступен."""
    models = _lm_models()
    choices = [("Автовыбор (загруженная, иначе первая доступная)", AUTO_MODEL)]
    for mid, state, mtype in models:
        mark = "● " if state == "loaded" else ("○ " if state == "not-loaded" else "")
        suffix = f"  · {mtype}" if mtype else ""
        choices.append((f"{mark}{mid}{suffix}", mid))
    values = {v for _, v in choices}
    keep = selected if selected in values else AUTO_MODEL
    return gr.update(choices=choices, value=keep)


def _probe_character(token: str) -> dict:
    """Прямая проба живого API: валиден ли под-токен и где стоит житель.

    Это НЕ инструмент агента — свои инструменты агент берёт из MCP-сервера.
    Здесь просто один requests-вызов для панели «Персонаж (живой мир)» и
    честной обучающей ошибки ДО запуска прогона, а не падения в середине."""
    r = requests.get(BASE_URL + "/character",
                     headers={"Authorization": f"Bearer {token}"}, timeout=15)
    if r.status_code >= 400:
        try:
            err = r.json().get("error", {})
        except Exception:  # noqa: BLE001 — тело не JSON
            err = {}
        raise RuntimeError(f"{err.get('code', 'http_error')}: "
                           f"{err.get('message', r.text[:200])}")
    return r.json()


def _probe_map() -> dict:
    """Прямая проба карты живого мира — для затравки под слабую модель.

    Как и _probe_character, это НЕ инструмент агента: свои инструменты агент
    берёт из MCP-сервера. Это внешняя разведка живого API (get_map публичный,
    без токена), чтобы app.py собрал facts_seed/route_hint ДО прогона — иначе
    слабая 7B пропускает get_map и уходит вслепую. При любом сбое возвращаем
    пустую карту: затравка честно скажет «ресурса не видно», а не уронит чат."""
    try:
        r = requests.get(BASE_URL + "/map", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:  # noqa: BLE001 — нет карты значит нет затравки, не беда
        return {"tiles": []}


def _set_cogno_snapshot(character: dict):
    """Запомнить последнего character для боковой панели."""
    global _cogno_snapshot
    _cogno_snapshot = character


def _open_mcp(token: str):
    """Поднять MCP-сервер stdio-подпроцессом и забрать у него инструменты.

    from_mcp — контекст-менеджер: __enter__ запускает подпроцесс
    `python cognopolis_mcp_server.py` и делает discovery (initialize +
    tools/list по JSON-RPC), __exit__ гасит подпроцесс. В ноутбуке он живёт
    в блоке `with` на один прогон; в чате прогонов много, поэтому здесь мы
    входим в контекст руками и держим соединение открытым между сообщениями,
    а закрываем в _close_mcp (кнопка «Сбросить» или смена токена).
    Под-токен уезжает подпроцессу через env — в сам протокол он не попадает."""
    global _mcp_cm, _tool_collection
    _mcp_cm = ToolCollection.from_mcp(
        StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER_PATH)],
            env={**os.environ, "COGNOPOLIS_TOKEN": token},
        ),
        trust_remote_code=True,
    )
    _tool_collection = _mcp_cm.__enter__()
    return _tool_collection


def _close_mcp():
    """Закрыть MCP-соединение (и stdio-подпроцесс сервера), если оно открыто."""
    global _mcp_cm, _tool_collection
    if _mcp_cm is not None:
        try:
            _mcp_cm.__exit__(None, None, None)
        except Exception:  # noqa: BLE001 — подпроцесс мог умереть сам, это не беда
            pass
    _mcp_cm = None
    _tool_collection = None


def _ensure_agent(cogno_token: str, model_id: str):
    """Собрать (или переиспользовать) агента под токен + выбранную модель LM Studio.

    Ключ включает id модели: выбрали в выпадающем списке другой мозг — ключ
    сменился, и агент пересобирается при следующем сообщении (живое демо
    «переключи модель» без рестарта). Но MCP-соединение зависит ТОЛЬКО от
    токена: COGNOPOLIS_TOKEN сервер читает из окружения один раз, на старте
    подпроцесса. Поэтому смена одной лишь модели переиспользует уже открытый
    каталог tools и лишь заново оборачивает его агентом; перезапускаем
    подпроцесс discovery только при смене токена (или если соединения ещё нет).
    Список tools агент в любом случае берёт из каталога сервера — в этом файле
    их определений нет."""
    global _agent, _agent_key
    key = (cogno_token, model_id)
    if _agent is not None and _agent_key == key and _tool_collection is not None:
        return _agent
    # Токен сменился (или соединения нет) — переоткрываем подпроцесс сервера.
    # Сменилась ТОЛЬКО модель при живом соединении — каталог оставляем как есть.
    token_changed = _agent_key is None or _agent_key[0] != cogno_token
    if _tool_collection is None or token_changed:
        _close_mcp()
        _open_mcp(cogno_token)
    # max_steps с запасом: на реальной игре маршрут длинный, а кулдаун съедает
    # шаги на повторы — это часть цикла, а не сбой.
    _agent = ToolCallingAgent(
        tools=[*_tool_collection.tools],
        model=_make_model(model_id),
        max_steps=40,
        instructions=LIVE_INSTRUCTIONS,
    )
    _agent_key = key
    return _agent


def world_state_text():
    """Снимок реального персонажа для боковой панели (последний известный)."""
    return json.dumps(
        _cogno_snapshot or {"note": "впишите под-токен и отправьте команду персонажу"},
        ensure_ascii=False, indent=2,
    )


def mcp_tools_text():
    """Панель «Инструменты из MCP-сервера»: что сервер объявил в tools/list.

    Пока соединения нет — честно так и пишем: в app.py игровые инструменты
    не определены, им неоткуда взяться, кроме как из каталога сервера."""
    if _tool_collection is None:
        return (
            "Соединения с MCP-сервером ещё нет — оно откроется при первом "
            "сообщении агенту. В app.py игровые инструменты не определены: "
            "их объявляет сервер cognopolis_mcp_server.py."
        )
    lines = []
    for t in _tool_collection.tools:
        first_sentence = (t.description or "").strip().split(".")[0].strip()
        lines.append(f"- `{t.name}` — {first_sentence}.")
    return ("Каталог tools/list сервера cognopolis_mcp_server.py "
            "(приехал по MCP, в app.py этих определений нет):\n" + "\n".join(lines))


def _do_reset():
    """Очистить агента, снимок панели и закрыть MCP-соединение.

    Поколение растёт, чтобы остановить бегущий прогон. Реальный мир
    Cognopolis не трогаем — он общий и живой."""
    global _agent, _agent_key, _world_generation, _cogno_snapshot
    _world_generation += 1
    _agent = None
    _agent_key = None
    _cogno_snapshot = None
    _close_mcp()


def store_message(message):
    """Сохранить текст из поля ввода и очистить поле (паттерн шаблона 10.2)."""
    return message, ""


def respond(message, history, cogno_token, model_choice):
    """Обработать сообщение: проверить токен/LM Studio, запустить агента на игре."""
    text = (message or "").strip()
    cogno_token = (cogno_token or "").strip()

    if not text:
        yield history, world_state_text(), mcp_tools_text()
        return

    history = history + [gr.ChatMessage(role="user", content=text)]
    yield history, world_state_text(), mcp_tools_text()

    # Мозг агента: без LM Studio не падаем, а объясняем, чего не хватает.
    # Пустой список моделей = сервер не отвечает (не нажат Start server).
    models = _lm_models()
    if not models:
        history.append(gr.ChatMessage(role="assistant", content=NO_LMSTUDIO_MESSAGE))
        yield history, world_state_text(), mcp_tools_text()
        return
    # Какую модель отдать агенту: выбор из выпадающего списка (или автовыбор
    # загруженной, если выбран «Автовыбор» или модель из списка исчезла).
    model_id = _resolve_model(model_choice, models)

    # Игра только онлайн: без под-токена не работаем и не подменяем мок-лесом.
    if not cogno_token:
        history.append(gr.ChatMessage(role="assistant", content=NO_CHARACTER_TOKEN_MESSAGE))
        yield history, world_state_text(), mcp_tools_text()
        return

    # Проба под-токена ДО прогона: честная обучающая ошибка, если токен
    # невалиден, и свежий персонаж в панели, если всё хорошо.
    try:
        char = _probe_character(cogno_token)
    except Exception as exc:  # noqa: BLE001 — любую причину показываем в чате
        history.append(gr.ChatMessage(
            role="assistant",
            content=(
                f"Не удалось подключиться к персонажу Cognopolis: {exc}\n\n"
                "Проверьте под-токен персонажа (Character.token) и адрес игры."
            ),
        ))
        yield history, world_state_text(), mcp_tools_text()
        return
    _set_cogno_snapshot(char)
    yield history, world_state_text(), mcp_tools_text()

    # Затравка под СЛАБУЮ локальную модель (тот же приём, что в 11.5/13.6):
    # внешней пробой берём карту и кладём прямо в задачу факты о мире + готовый
    # маршрут. Это НЕ инструменты агента — их он по-прежнему берёт из MCP; это
    # разведка мира, чтобы 7B не пропускала get_map и не блуждала к краю.
    # WEAK_MODEL_ROUTE=0 убирает маршрут — на модели посильнее навигацию она
    # ведёт сама по фактам затравки и правилам мира из инструкций.
    gmap = _probe_map()
    task = helpers.facts_seed(char, gmap, text)
    if os.getenv("WEAK_MODEL_ROUTE", "1") != "0":
        task += "\n" + helpers.route_hint(char, gmap, text)
    task += "\n\nЗадача: " + text

    # Живой агентный цикл think -> act -> observe; шаги стримятся в чат.
    try:
        fresh = _agent is None or _tool_collection is None
        agent = _ensure_agent(cogno_token, model_id)
        if fresh:
            model_name = getattr(agent.model, "model_id", "?")
            who = char.get("name") or char.get("id", "?")
            tool_names = ", ".join(t.name for t in _tool_collection.tools)
            history.append(gr.ChatMessage(
                role="assistant",
                content=(f"Подключено к жителю Cognopolis «{who}». "
                         f"Модель: {model_name}. Инструменты приехали из "
                         f"MCP-сервера (tools/list): {tool_names}."),
            ))
            yield history, world_state_text(), mcp_tools_text()
        generation = _world_generation
        # Память агента сбрасываем ПЕРЕД каждым прогоном (урок зеркал 11.5/13.6):
        # накопленная через прогоны история топит слабую локальную 7B — она
        # фабрикует final_answer, не сделав ни одного вызова. Непрерывность даёт
        # сам ПЕРСИСТЕНТНЫЙ мир (житель стоит, где закончил), а не память агента.
        for msg in stream_to_gradio(agent, task=task, reset_agent_memory=True):
            if _world_generation != generation:
                # «Сбросить» нажали во время прогона: останавливаем стрим и
                # оставляем чат чистым, как и обещает кнопка.
                yield [], world_state_text(), mcp_tools_text()
                return
            history.append(msg)
            yield history, world_state_text(), mcp_tools_text()
        # Правда из игры после прогона: слабая модель склонна объявить успех,
        # не вернувшись на склад. Сверяем СОСТОЯНИЕМ, а не словами — дельта
        # склада (stored) до/после, как в 11.5/13.6: char был снят ДО прогона.
        try:
            final_char = _probe_character(cogno_token)
            _set_cogno_snapshot(final_char)
            history.append(gr.ChatMessage(
                role="assistant", content=helpers.fact_check(char, final_char, text)))
            yield history, world_state_text(), mcp_tools_text()
        except Exception:  # noqa: BLE001 — панель просто останется прежней
            pass
    except Exception as exc:  # noqa: BLE001 — любую беду показываем в чате
        hint = (
            "Частые причины: LM Studio выгрузил модель или сервер остановлен; "
            "модель без поддержки tool use (в каталоге LM Studio ищите "
            "значок-молоток). Если не помогло — нажмите «Сбросить»: соединение "
            "с MCP-сервером откроется заново."
        )
        history.append(gr.ChatMessage(
            role="assistant",
            content=f"Агент упал с ошибкой: {exc!r}\n\n{hint}",
        ))
        yield history, world_state_text(), mcp_tools_text()


def reset_click():
    """Кнопка «Сбросить»: чистим чат и память, закрываем MCP-соединение.

    Реальный мир не трогаем. При следующем сообщении соединение откроется
    заново и discovery пройдёт с нуля — на этом держится эксперимент
    «допиши серверу инструмент» из README."""
    _do_reset()
    return [], world_state_text(), mcp_tools_text()


def build_demo():
    """Собрать Gradio-интерфейс.

    Именно функцией, а не при импорте модуля: так `import app` (например, из
    тестов) не запускает ничего тяжёлого, а сам интерфейс не требует ни
    LM Studio, ни токена — они понадобятся при первом сообщении."""
    with gr.Blocks(title="Лесоруб через MCP — агент на живой игре Cognopolis",
                   fill_height=True) as demo:
        gr.Markdown(
            "## Лесоруб через MCP — агент на живой игре Cognopolis\n"
            "Шаблон к модулю 14.5: smolagents-агент, в коде которого НЕТ игровых "
            "инструментов. app.py запускает MCP-сервер cognopolis_mcp_server.py "
            "stdio-подпроцессом и берёт tools из его каталога "
            "(ToolCollection.from_mcp) — в проектах 11.5 и 13.6 те же move, "
            "gather, get_map, get_character были классами в файле проекта. "
            "Агент ходит на **реальный API игры** https://kindomklaster.com и "
            "ведёт вашего настоящего жителя. Впишите под-токен персонажа ниже, "
            "выберите модель-мозг и попросите, например: «Добудь одно дерево "
            "(wood) и вернись домой на (0, 0)».\n\n"
            f"*Модель (мозг): локальный LM Studio ({LM_BASE}). Выберите её в "
            "списке ниже — «Автовыбор» берёт загруженную в память, а если "
            "ничего не загружено — первую скачанную (LM Studio подтянет её).*"
        )
        token_input = gr.Textbox(
            type="password",
            label="Под-токен персонажа Cognopolis (обязательно)",
            placeholder="Character.token вашего жителя",
            value=os.getenv("COGNOPOLIS_TOKEN", ""),   # предзаполняется из .env / окружения
            info="Можно не вписывать руками: скопируйте .env-example в .env и впишите токен там.",
        )
        with gr.Row():
            model_dropdown = gr.Dropdown(
                # choices/value наполняются на загрузке страницы через demo.load
                # (сервер LM Studio может быть ещё не запущен в момент импорта).
                choices=[("Автовыбор (загруженная, иначе первая доступная)", AUTO_MODEL)],
                value=AUTO_MODEL,
                label="Модель-мозг (LM Studio)",
                info="● загружена в память · ○ подгрузится на лету при первом сообщении",
                scale=5,
            )
            refresh_btn = gr.Button("↻ Обновить", scale=1)
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Лесоруб через MCP", type="messages", scale=1)
                with gr.Row():
                    text_input = gr.Textbox(
                        lines=1,
                        label="Сообщение агенту",
                        placeholder="Добудь одно дерево (wood) и вернись домой на (0, 0)",
                        scale=5,
                    )
                    send_btn = gr.Button("Отправить", variant="primary", scale=1)
            with gr.Column(scale=1):
                state_box = gr.Code(
                    # Именно функция, не вызов: callable Gradio перевычисляет на
                    # каждую загрузку страницы.
                    value=world_state_text,
                    language="json",
                    label="Персонаж (живой мир)",
                )
                tools_box = gr.Markdown(
                    # Тоже callable: каталог перечитывается на каждую загрузку
                    # страницы (и по кнопке «Сбросить»).
                    value=mcp_tools_text,
                    label="Инструменты из MCP-сервера",
                    container=True,
                )
                reset_btn = gr.Button("Сбросить")

        stored_message = gr.State("")
        respond_inputs = [stored_message, chatbot, token_input, model_dropdown]
        text_input.submit(
            store_message, [text_input], [stored_message, text_input]
        ).then(respond, respond_inputs, [chatbot, state_box, tools_box])
        send_btn.click(
            store_message, [text_input], [stored_message, text_input]
        ).then(respond, respond_inputs, [chatbot, state_box, tools_box])
        reset_btn.click(reset_click, None, [chatbot, state_box, tools_box])
        # Список моделей — живой: наполняем на загрузке страницы и по кнопке
        # «Обновить» (запустили Start server / загрузили другую модель — видно сразу).
        refresh_btn.click(model_choices, model_dropdown, model_dropdown)
        demo.load(model_choices, model_dropdown, model_dropdown)
    return demo


if __name__ == "__main__":
    # ssr_mode=False: экспериментальный SSR-режим Gradio 5 поднимает отдельный
    # Node.js-сервер, который на HF Spaces валит контейнер (в логе рантайма
    # «Stopping Node.js server...» перед RUNTIME_ERROR). Нам SSR не нужен —
    # это обычный чат, серверный рендер только добавляет точку отказа.
    build_demo().launch(ssr_mode=False)
