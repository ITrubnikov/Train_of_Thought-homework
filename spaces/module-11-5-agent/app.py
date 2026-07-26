"""Лесоруб — агент на живой игре Cognopolis. Учебная копия к модулю 11.5.

Тот же «хороший» контракт tools, что вы собрали в мок-лесу ноутбука
(move / gather / get_map + говорящие ошибки {code, message}), но здесь он
ходит на РЕАЛЬНЫЙ API игры https://kindomklaster.com и ведёт НАСТОЯЩЕГО
жителя поселения по его под-токену (Character.token). Мок-леса тут нет —
только живая игра; без под-токена агент вежливо просит его вписать.

Мозг агента — локальная модель из LM Studio через его OpenAI-совместимый
сервер http://localhost:1234/v1 (OpenAIServerModel), без ключей. Контракт
tools от модели не зависит — это и есть тезис лекции «tool это контракт».

Главное отличие этой копии: в cognopolis_tools.py лежат ДВА набора
инструментов с разбором дизайна по чек-листу A→H из лекции. Хороший
(move/gather/get_map/get_character) активен; плохой (god-tool do_action из
Блока 1 ноутбука, перенесённый на живой API) закомментирован — переключатель
в build_tools() там же. app.py при этом не меняется ни на строку: агенту всё
равно, какой набор ему выдали, — в этом и эксперимент.

Устройство:
- cognopolis_tools.py — оба набора инструментов на живом API Cognopolis
  (тонкий клиент на requests, Bearer под-токен) + комментарии по дизайну;
- helpers.py          — подпорки под слабую модель (затравка-маршрут,
  факт-чек), вынесены отдельно — к дизайну tools не относятся;
- app.py              — модель, ToolCallingAgent и чат на Gradio (этот файл).

Интерфейс поднимается даже без бэкенда: агент создаётся лениво, при первом
сообщении; без LM Studio или без под-токена персонажа он вежливо объясняет,
чего не хватает."""

import json
import os

import gradio as gr
import requests
from smolagents import OpenAIServerModel, ToolCallingAgent
from smolagents.gradio_ui import stream_to_gradio

import cognopolis_tools
import helpers

# LM Studio: дефолтный адрес его OpenAI-совместимого сервера (Шаг 7 ноутбука).
LM_BASE = os.getenv("LM_BASE", "http://localhost:1234/v1")

# --- Состояние процесса (ленивое; интерфейс живёт и без бэкенда) ------------
_agent = None
_agent_key = None          # чем определён текущий агент: (токен, модель)
_cogno_snapshot = None     # последний известный character из живого API

# Поколение: каждый сброс увеличивает счётчик, и бегущий прогон агента
# замечает это между шагами и останавливается (см. respond).
_world_generation = 0

NO_LMSTUDIO_MESSAGE = (
    "Агент пока спит: локальный запуск ждёт LM Studio (это модель-мозг), а "
    f"сервер {LM_BASE} не отвечает (или в нём не загружена разговорная модель).\n\n"
    "Откройте LM Studio, во вкладке Developer нажмите Start server и загрузите "
    "инструкт-модель с поддержкой tool use (в каталоге помечены молотком; "
    "например Qwen2.5-7B-Instruct), затем напишите снова."
)

NO_CHARACTER_TOKEN_MESSAGE = (
    "Нужен под-токен персонажа Cognopolis: этот агент играет только в живую "
    "игру, мок-леса тут нет.\n\n"
    "Впишите под-токен своего жителя (Character.token) в поле «Под-токен "
    "персонажа Cognopolis» вверху и отправьте команду снова. Токен остаётся "
    "в этом локальном процессе и уходит только на сам API игры."
)


def _detect_lm_model():
    """Спросить у LM Studio, какая разговорная модель доступна (Шаг 7 ноутбука).

    Возвращает id модели или None, если сервер молчит. Переопределить выбор
    можно переменной окружения LM_MODEL_ID.

    Гоча автодетекта: /v1/models при включённом JIT loading отдаёт все
    СКАЧАННЫЕ модели, а не загруженную в память — первым может оказаться
    что угодно. Поэтому сперва спрашиваем расширенный /api/v0/models и берём
    модель со state=loaded (текстовые llm приоритетнее мультимодальных vlm),
    и только для старых LM Studio без /api/v0 падаем на грубую эвристику."""
    forced = os.getenv("LM_MODEL_ID")
    if forced:
        return forced
    root = LM_BASE.rsplit("/v1", 1)[0]
    try:
        r = requests.get(f"{root}/api/v0/models", timeout=2)
        r.raise_for_status()
        models = r.json().get("data", [])
        for want_type in ("llm", "vlm"):
            loaded = [m["id"] for m in models
                      if m.get("state") == "loaded" and m.get("type") == want_type]
            if loaded:
                return loaded[0]
    except Exception:  # noqa: BLE001 — старый LM Studio без /api/v0, идём дальше
        pass
    try:
        r = requests.get(f"{LM_BASE}/models", timeout=2)
        r.raise_for_status()
        ids = [item["id"] for item in r.json().get("data", [])]
        chat_ids = [i for i in ids if "embed" not in i.lower()]
        return chat_ids[0] if chat_ids else None
    except Exception:  # noqa: BLE001 — любой сбой значит «сервера нет»
        return None


def _make_model():
    """Модель-мозг из LM Studio (одна строка лекции «какой модели отдать tools»)."""
    return OpenAIServerModel(
        model_id=_detect_lm_model(),
        api_base=LM_BASE,
        api_key="lm-studio",  # LM Studio ключ не проверяет, но клиенту нужна заглушка
        max_tokens=2096,
        temperature=0.2,  # локальные 4-8B путаются на 0.5 — держим их на рельсах
    )


# Установка агента: семантика мира + «ошибка это вход следующего шага».
# Контракт tools одинаков для всех моделей; установка выравнивает небольшие
# локальные модели (LM Studio), которые путаются в координатах и сдаются
# на первой ошибке. Это system-слой агента, а не часть контракта инструментов.
# Написана под ХОРОШИЙ набор (упоминает get_character, get_map, move). С плохим
# do_action эти подсказки не спасают — у агента просто нет названных tools;
# это тоже часть эксперимента: промптом плохой контракт не чинится.
INSTRUCTIONS = (
    "Ты управляешь РЕАЛЬНЫМ жителем поселения Cognopolis на сетке 7x7 (x и y "
    "от 0 до 6). Мир персистентный: житель стоит там, где закончил прошлый "
    "раз, а НЕ обязательно дома. Поэтому порядок строгий:\n"
    "1) СНАЧАЛА вызови get_character и прочитай своё РЕАЛЬНОЕ [x, y] — не "
    "предполагай, что ты дома [0, 0].\n"
    "2) Вызови get_map. Тайлы с content 'tree' дают wood, 'rock' — stone. "
    "Выбери ближайший нужный тайл; НЕ ходи на тайлы с врагами (goblin, wolf, "
    "ogre) — это драка.\n"
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
    "Если в сообщении дан «Рекомендуемый план» — выполняй ВСЕ его шаги по "
    "порядку до конца, включая возврат домой; по одному вызову за раз.\n"
    "ПРОВЕРКА перед final_answer: вызови get_character. Задача «добыть и сдать» "
    "выполнена ТОЛЬКО если нужный ресурс лежит в stored (склад), а в inventory "
    "(рюкзак) его нет, и твоя позиция [0, 0]. Если ресурс всё ещё в inventory — "
    "ты НЕ сдал: иди на [0, 0]. Не объявляй успех без этого подтверждения.\n"
    "Ошибка от инструмента — не провал, а подсказка: прочитай её code и "
    "message и продолжай. character_on_cooldown значит, что житель ещё занят "
    "предыдущим делом (шаг ~1 с, добыча ~10 с; сколько именно осталось — в "
    "message). Инструмент досиживает такт сам, так что этот код ты увидишь "
    "редко; увидел — просто повтори тот же вызов, это не провал."
)


def _set_cogno_snapshot(character: dict):
    """Колбэк инструментов Cognopolis: запомнить последнего character для панели."""
    global _cogno_snapshot
    _cogno_snapshot = character


# Подпорки под слабую локальную модель (затравка-маршрут + факт-чек) вынесены
# в helpers.py: это не про дизайн tools, а про «как докрутить слабый мозг».
# На сильной модели helpers можно не использовать.


def _ensure_agent(cogno_token: str, base_url: str):
    """Собрать (или переиспользовать) агента под текущие токен+адрес+модель.

    Ключ включает id модели LM Studio: если в LM Studio загрузили другую
    модель, ключ меняется и агент пересобирается — без ручной сверки."""
    global _agent, _agent_key
    model_hint = _detect_lm_model()
    key = (cogno_token, base_url, model_hint)
    if _agent is not None and _agent_key == key:
        return _agent
    client = cognopolis_tools.CognopolisClient(base_url, cogno_token)
    # Какой набор tools достанется агенту (хороший или закомментированный
    # плохой), решает переключатель в cognopolis_tools.build_tools().
    tools = cognopolis_tools.build_tools(client, _set_cogno_snapshot)
    # max_steps с запасом: на реальной игре маршрут длиннее и кулдаун съедает
    # шаги на повторы — это часть цикла, а не сбой.
    _agent = ToolCallingAgent(
        tools=tools, model=_make_model(), max_steps=40, instructions=INSTRUCTIONS
    )
    _agent_key = key
    return _agent


def world_state_text():
    """Снимок реального персонажа для боковой панели (последний известный)."""
    return json.dumps(
        _cogno_snapshot or {"note": "впишите под-токен и отправьте команду персонажу"},
        ensure_ascii=False, indent=2,
    )


def _do_reset():
    """Очистить агента и снимок панели; поколение растёт, чтобы остановить прогон.

    Реальный мир Cognopolis не трогаем — он общий и живой."""
    global _agent, _agent_key, _world_generation, _cogno_snapshot
    _world_generation += 1
    _agent = None
    _agent_key = None
    _cogno_snapshot = None


def store_message(message):
    """Сохранить текст из поля ввода и очистить поле (паттерн шаблона 10.2)."""
    return message, ""


def respond(message, history, cogno_token):
    """Обработать сообщение: проверить токен/LM Studio, запустить агента на игре."""
    text = (message or "").strip()
    cogno_token = (cogno_token or "").strip()
    # Адрес игры фиксирован; для своего Cognopolis-сервера — env COGNO_BASE_URL.
    base_url = os.getenv("COGNO_BASE_URL", cognopolis_tools.DEFAULT_BASE_URL)

    if not text:
        yield history, world_state_text()
        return

    history = history + [gr.ChatMessage(role="user", content=text)]
    yield history, world_state_text()

    # Мозг агента: без LM Studio не падаем, а объясняем, чего не хватает.
    if _detect_lm_model() is None:
        history.append(gr.ChatMessage(role="assistant", content=NO_LMSTUDIO_MESSAGE))
        yield history, world_state_text()
        return

    # Игра только онлайн: без под-токена не работаем и не подменяем мок-лесом.
    if not cogno_token:
        history.append(gr.ChatMessage(role="assistant", content=NO_CHARACTER_TOKEN_MESSAGE))
        yield history, world_state_text()
        return

    # Проверим под-токен и покажем персонажа в панели — честная обучающая
    # ошибка, если токен невалиден, а не падение в середине. Заодно соберём
    # «затравку»: где житель стоит и где ресурсы/враги (мир персистентный,
    # карта 7x7 — небольшая локальная модель иначе теряется в ходьбе).
    probe = cognopolis_tools.CognopolisClient(base_url, cogno_token)
    try:
        char = probe.get_character()
        _set_cogno_snapshot(char)
        yield history, world_state_text()
        gmap = probe.get_map()
    except cognopolis_tools.GameError as exc:
        history.append(gr.ChatMessage(
            role="assistant",
            content=(
                f"Не удалось подключиться к персонажу Cognopolis: "
                f"{exc.code} — {exc.message}\n\n"
                "Проверьте под-токен персонажа (Character.token) и адрес игры."
            ),
        ))
        yield history, world_state_text()
        return
    task = helpers.task_seed(char, gmap, text) + "\n\nЗадача: " + text

    # Живой агентный цикл think -> act -> observe; шаги стримятся в чат.
    try:
        fresh = _agent is None or _agent_key is None
        agent = _ensure_agent(cogno_token, base_url)
        if fresh:
            model_name = getattr(agent.model, "model_id", "?")
            who = char.get("name") or char.get("id", "?")
            history.append(gr.ChatMessage(
                role="assistant",
                content=f"Подключено к жителю Cognopolis «{who}». Модель: {model_name}.",
            ))
            yield history, world_state_text()
        generation = _world_generation
        # Память агента сбрасываем ПЕРЕД каждым прогоном (reset_agent_memory=True).
        # Каждая задача самодостаточна: task_seed + свежие get_character/get_map
        # несут всё состояние живого мира заново. А НЕсброс копил контекст через
        # прогоны до сотен тысяч токенов, и слабая локальная 7B тонула в своей
        # истории — на первом же шаге фабриковала final_answer «уже сдал», не
        # сделав ни одного вызова инструмента. Непрерывность здесь даёт сам
        # ПЕРСИСТЕНТНЫЙ мир (житель стоит, где закончил), а не память агента.
        for msg in stream_to_gradio(agent, task=task, reset_agent_memory=True):
            if _world_generation != generation:
                # «Сбросить» нажали во время прогона: останавливаем стрим и
                # оставляем чат чистым, как и обещает кнопка.
                yield [], world_state_text()
                return
            history.append(msg)
            yield history, world_state_text()
        # Факт-чек: слова агента vs реальное состояние. Слабая модель склонна
        # объявить успех, не вернувшись на склад — показываем правду из игры.
        try:
            final_char = probe.get_character()
            _set_cogno_snapshot(final_char)
            history.append(gr.ChatMessage(
                role="assistant", content=helpers.fact_check(char, final_char, text)))
            yield history, world_state_text()
        except cognopolis_tools.GameError:
            pass
    except Exception as exc:  # noqa: BLE001 — любую беду показываем в чате
        hint = (
            "Частые причины: LM Studio выгрузил модель или сервер остановлен; "
            "модель без поддержки tool use (в каталоге LM Studio ищите значок-молоток)."
        )
        history.append(gr.ChatMessage(
            role="assistant",
            content=f"Агент упал с ошибкой: {exc!r}\n\n{hint}",
        ))
        yield history, world_state_text()


def reset_click():
    """Кнопка «Сбросить»: чистим чат и память агента (реальный мир не трогаем)."""
    _do_reset()
    return [], world_state_text()


with gr.Blocks(title="Лесоруб — агент на живой игре Cognopolis", fill_height=True) as demo:
    gr.Markdown(
        "## Лесоруб — агент на живой игре Cognopolis\n"
        "smolagents-агент с инструментами move, gather, get_map, get_character. "
        "Тот же контракт tools, что в мок-лесу ноутбука, но здесь он ходит на "
        "**реальный API игры** https://kindomklaster.com и ведёт вашего "
        "настоящего жителя. Впишите под-токен персонажа ниже и попросите, "
        "например: «Добудь одно дерево (wood) и сдай его на склад» — в чате "
        "видно вызовы tools, конверт {result, cooldown, character} и обучающие "
        "ошибки {code, message}.\n\n"
        f"*Модель (мозг): локальный LM Studio ({LM_BASE}), подхватывается сама.*"
    )
    token_input = gr.Textbox(
        type="password",
        label="Под-токен персонажа Cognopolis (обязательно)",
        placeholder="Character.token вашего жителя",
    )
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Лесоруб", type="messages", scale=1)
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
                # Именно функция, не вызов: callable Gradio перевычисляет на
                # каждую загрузку страницы.
                value=world_state_text,
                language="json",
                label="Персонаж (живой мир)",
            )
            reset_btn = gr.Button("Сбросить")

    stored_message = gr.State("")
    text_input.submit(
        store_message, [text_input], [stored_message, text_input]
    ).then(respond, [stored_message, chatbot, token_input], [chatbot, state_box])
    send_btn.click(
        store_message, [text_input], [stored_message, text_input]
    ).then(respond, [stored_message, chatbot, token_input], [chatbot, state_box])
    reset_btn.click(reset_click, None, [chatbot, state_box])


if __name__ == "__main__":
    # ssr_mode=False: экспериментальный SSR-режим Gradio 5 поднимает отдельный
    # Node.js-сервер, который на HF Spaces валит контейнер (в логе рантайма
    # «Stopping Node.js server...» перед RUNTIME_ERROR). Нам SSR не нужен —
    # это обычный чат, серверный рендер только добавляет точку отказа.
    demo.launch(ssr_mode=False)
