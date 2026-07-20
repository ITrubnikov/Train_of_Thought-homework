"""Лесоруб с умениями — агент на живой игре Cognopolis. Шаблон к модулю 13.6.

Тот же агент, что в шаблоне 11.5 (move / gather / get_map / get_character на
РЕАЛЬНОМ API игры https://kindomklaster.com, под-токен жителя, мозг — локальная
модель из LM Studio), но поверх — слой скиллов из лекции 13.6: библиотека
`skills/<name>/SKILL.md`, витрина (name + description) в инструкциях агента и
ПЯТЫЙ инструмент load_skill, которым модель сама подтягивает тело умения по
имени. Контракт tools — из 11.5 без изменений; progressive disclosure здесь
живой: в контексте всегда только витрина, тело грузится по совпадению
описания с задачей, и вызов load_skill виден в чате.

Устройство:
- cognopolis_tools.py — инструменты move/gather/get_map/get_character на
  живом API Cognopolis (тонкий клиент на requests, Bearer под-токен);
- skills_runtime.py    — учебный парсер SKILL.md, витрина и load_skill
  (тот же код, что в ноутбуке 13.6, без скриптового селектора);
- skills/              — библиотека умений (supply-run, scout-map);
- helpers.py           — подпорки под слабую модель (затравка фактов,
  факт-чек), вынесены отдельно — к скиллам не относятся;
- app.py               — модель, ToolCallingAgent и чат на Gradio (этот файл).

Интерфейс поднимается даже без бэкенда: агент создаётся лениво, при первом
сообщении; без LM Studio или без под-токена персонажа он вежливо объясняет,
чего не хватает."""

import json
import os
from pathlib import Path

import gradio as gr
import requests
from smolagents import OpenAIServerModel, ToolCallingAgent
from smolagents.gradio_ui import stream_to_gradio

import cognopolis_tools
import helpers
import skills_runtime

# LM Studio: дефолтный адрес его OpenAI-совместимого сервера (Шаг 7 ноутбука).
LM_BASE = os.getenv("LM_BASE", "http://localhost:1234/v1")

# Библиотека умений — рядом с app.py; правится на диске без рестарта.
SKILLS_DIR = Path(__file__).parent / "skills"

# --- Состояние процесса (ленивое; интерфейс живёт и без бэкенда) ------------
_agent = None
_agent_key = None          # чем определён текущий агент: (токен, модель, витрина)
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


def _load_skills():
    """Прочитать библиотеку умений с диска (перечитывается при каждом вызове)."""
    return skills_runtime.load_skills(SKILLS_DIR)


def _skills_fingerprint(skills):
    """Витрина как ключ: правка name/description на диске пересобирает агента.

    Тело в отпечаток не входит нарочно: его агент и так читает с диска свежим
    при каждом load_skill — пересборка не нужна."""
    return tuple((s["name"], s["description"]) for s in skills)


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


def build_instructions(skills):
    """System-слой агента: ПРАВИЛА МИРА (что умеет инструмент) + витрина умений.

    Ключевое отличие от 11.5: базовые инструкции несут только МЕХАНИКУ мира —
    что делает каждый инструмент, как считать направление, что дом банкует сам.
    ПОРЯДОК действий под конкретную задачу (какую цель искать, сколько добывать,
    когда возвращаться, как проверить) здесь НЕ описан — он живёт в теле умения,
    и модель подтягивает его сама через load_skill. Это и есть разделение из
    лекции 13.6: tool — механика, skill — процедура поверх механики. Если
    процедуру вписать сюда, skill станет декоративным — модель не будет его
    подтягивать, ведь всё уже в контексте. Витрина (name + description) — ровно
    то, что по progressive disclosure всегда лежит в контексте; тело — нет."""
    return (
        "Ты управляешь РЕАЛЬНЫМ жителем поселения Cognopolis на сетке 7x7 (x и y "
        "от 0 до 6). Мир персистентный: житель стоит там, где закончил прошлый "
        "раз, а НЕ обязательно дома.\n\n"
        "У тебя есть БИБЛИОТЕКА УМЕНИЙ — заученных процедур (name: description):\n"
        + skills_runtime.skills_index(skills) + "\n"
        "ЖЁСТКОЕ ПРАВИЛО ПОРЯДКА. Прежде чем звать get_character, get_map, move "
        "или gather, сверь задачу с описаниями умений выше. Если задача совпала с "
        "описанием умения — твой САМЫЙ ПЕРВЫЙ вызов инструмента обязан быть "
        "load_skill(name=<это умение>). Тело умения — пошаговая процедура; получив "
        "его, следуй его шагам и его проверке. НЕ выполняй задачу по памяти: "
        "порядок действий, сколько добывать и как проверить результат записаны "
        "ТОЛЬКО в теле умения — в этих инструкциях их нет. Если ни одно описание "
        "не подошло — действуй по правилам мира сам.\n\n"
        "КАК УСТРОЕН МИР (что делает каждый инструмент — механика на случай, когда "
        "умение не подошло; ПОРЯДОК под задачу берётся из умения, не отсюда):\n"
        "- get_character — прочитать своё РЕАЛЬНОЕ [x, y], рюкзак (inventory) и "
        "склад (stored). Не предполагай, что ты дома [0, 0].\n"
        "- get_map — тайлы: content 'tree' даёт wood, 'rock' даёт stone; на тайлы "
        "с врагами (goblin, wolf, ogre) не ходи — это драка.\n"
        "- move меняет ОДНУ координату: east = x+1, west = x-1, south = y+1, "
        "north = y-1. Чтобы дойти до [tx, ty]: если твой x больше tx — иди west, "
        "меньше — east; если твой y больше ty — north, меньше — south. После "
        "КАЖДОГО move читай новый [x, y] из ответа. Ошибка at_map_edge — ты выбрал "
        "сторону НАРУЖУ карты, возьми противоположную.\n"
        "- gather добывает ресурс с тайла, на котором стоишь РОВНО; ресурс падает "
        "в рюкзак (inventory) — это ещё НЕ склад.\n"
        "- Отдельного deposit НЕТ: дом [0, 0] сам разгружает рюкзак на склад (в "
        "ответе move появляется banked). Пока ты не на [0, 0], добытое не сдано.\n"
        "- Ошибка инструмента — не провал, а подсказка: читай code и message. "
        "character_on_cooldown значит «занят долю секунды» — повтори тот же вызов."
    )


def _set_cogno_snapshot(character: dict):
    """Колбэк инструментов Cognopolis: запомнить последнего character для панели."""
    global _cogno_snapshot
    _cogno_snapshot = character


# Подпорки под слабую локальную модель (затравка фактов + факт-чек) вынесены
# в helpers.py: это не про скиллы, а про «как докрутить слабый мозг».
# Маршрутной затравки из 11.5 тут нет — процедуру несёт skill.


def _is_scout_task(text: str) -> bool:
    """Разведка (scout-map) — задача только на чтение, склад тут ни при чём.

    helpers.fact_check заточен под «добудь/сдай»: после разведки он честно, но
    невпопад писал бы «wood пока не видно». Ловим разведку по тексту задачи и
    даём ей свою проверку — «мир не тронут» (см. _scout_fact_check)."""
    return any(w in text.lower() for w in ("развед", "scout"))


def _scout_fact_check(before: dict, after: dict) -> str:
    """Факт-чек разведки: позиция, рюкзак и склад должны остаться как были.

    Та же идея «проверяем состоянием, а не словами», что в helpers.fact_check,
    только критерий успеха обратный — ни одного действия-мутации."""
    x, y = after.get("x"), after.get("y")
    untouched = (
        [before.get("x"), before.get("y")] == [x, y]
        and (before.get("inventory") or {}) == (after.get("inventory") or {})
        and (before.get("stored") or {}) == (after.get("stored") or {})
    )
    facts = f"Проверка по факту (get_character): позиция [{x}, {y}]."
    if untouched:
        return ("✅ " + facts + " Позиция, рюкзак и склад не изменились — "
                "разведка мир не тронула, как и обещает scout-map.")
    return ("⚠️ " + facts + " Мир изменился (позиция, рюкзак или склад), а "
            "разведка должна только читать. Посмотрите в трейсе, зачем агент "
            "звал move или gather.")


def _ensure_agent(cogno_token: str, base_url: str):
    """Собрать (или переиспользовать) агента под токен+адрес+модель+витрину.

    Ключ включает id модели LM Studio и отпечаток витрины умений: загрузили
    другую модель или поправили description в SKILL.md на диске — ключ
    меняется, и агент пересобирается при следующем сообщении (живое демо
    «сломай описание» без рестарта)."""
    global _agent, _agent_key
    model_hint = _detect_lm_model()
    skills = _load_skills()
    key = (cogno_token, base_url, model_hint, _skills_fingerprint(skills))
    if _agent is not None and _agent_key == key:
        return _agent
    client = cognopolis_tools.CognopolisClient(base_url, cogno_token)
    # Пятый инструмент — load_skill; тело он читает с диска при каждом вызове
    # (правка тела SKILL.md видна сразу, без пересборки агента).
    tools = cognopolis_tools.build_tools(client, _set_cogno_snapshot) + [
        skills_runtime.LoadSkillTool(_load_skills)
    ]
    # max_steps с запасом: на реальной игре маршрут длиннее и кулдаун съедает
    # шаги на повторы — это часть цикла, а не сбой.
    _agent = ToolCallingAgent(
        tools=tools, model=_make_model(), max_steps=40,
        instructions=build_instructions(skills),
    )
    _agent_key = key
    return _agent


def world_state_text():
    """Снимок реального персонажа для боковой панели (последний известный)."""
    return json.dumps(
        _cogno_snapshot or {"note": "впишите под-токен и отправьте команду персонажу"},
        ensure_ascii=False, indent=2,
    )


def skills_panel_text():
    """Витрина для боковой панели: name + description каждого умения с диска.

    Перечитывает skills/ при каждом вызове — панель честно показывает то, что
    сейчас лежит в файлах (в том числе сломанное описание из эксперимента)."""
    skills = _load_skills()
    if not skills:
        return "Библиотека пуста: в skills/ не нашлось ни одного SKILL.md."
    lines = [f"- **{s['name']}** — {s['description']}" for s in skills]
    lines.append("\nТело подтянет сам агент инструментом load_skill.")
    return "\n".join(lines)


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
    # затравку ФАКТОВ: где житель стоит и где ресурсы/враги (мир персистентный,
    # карта 7x7 — небольшая локальная модель иначе теряется). Готового маршрута
    # затравка не даёт — процедуру несёт skill.
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
    task = helpers.facts_seed(char, gmap, text) + "\n\nЗадача: " + text

    # Живой агентный цикл think -> act -> observe; шаги стримятся в чат.
    try:
        fresh = _agent is None or _agent_key is None
        agent = _ensure_agent(cogno_token, base_url)
        if fresh:
            model_name = getattr(agent.model, "model_id", "?")
            who = char.get("name") or char.get("id", "?")
            n_skills = len(_load_skills())
            history.append(gr.ChatMessage(
                role="assistant",
                content=(f"Подключено к жителю Cognopolis «{who}». "
                         f"Модель: {model_name}. Умений в библиотеке: {n_skills}."),
            ))
            yield history, world_state_text()
        # Страховка: память агента копится через прогоны (reset_agent_memory=False
        # ради непрерывности чата) — не даём ей расти бесконечно.
        if len(agent.memory.steps) > 40:
            agent.memory.reset()
        generation = _world_generation
        for msg in stream_to_gradio(agent, task=task, reset_agent_memory=False):
            if _world_generation != generation:
                # «Сбросить» нажали во время прогона: останавливаем стрим и
                # оставляем чат чистым, как и обещает кнопка.
                yield [], world_state_text()
                return
            history.append(msg)
            yield history, world_state_text()
        # Факт-чек: слова агента vs реальное состояние. Слабая модель склонна
        # объявить успех, не вернувшись на склад — показываем правду из игры.
        # У разведки проверка своя: «мир не тронут», а не дельта склада.
        try:
            final_char = probe.get_character()
            _set_cogno_snapshot(final_char)
            check = (_scout_fact_check(char, final_char) if _is_scout_task(text)
                     else helpers.fact_check(char, final_char, text))
            history.append(gr.ChatMessage(role="assistant", content=check))
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
    """Кнопка «Сбросить»: чистим чат и память агента, перечитываем витрину.

    Реальный мир не трогаем; панель «Библиотека умений» обновляется с диска —
    так эксперимент «сломай описание» виден без перезагрузки страницы."""
    _do_reset()
    return [], world_state_text(), skills_panel_text()


with gr.Blocks(title="Лесоруб с умениями — агент на живой игре Cognopolis",
               fill_height=True) as demo:
    gr.Markdown(
        "## Лесоруб с умениями — агент на живой игре Cognopolis\n"
        "Шаблон к модулю 13.6: smolagents-агент с инструментами move, gather, "
        "get_map, get_character — контракт tools из 11.5 без изменений — плюс "
        "ПЯТЫЙ инструмент load_skill и библиотека умений skills/*/SKILL.md. "
        "В инструкциях агента живёт только витрина (name + description); тело "
        "умения модель подтягивает сама, и вызов load_skill виден в чате. "
        "Агент ходит на **реальный API игры** https://kindomklaster.com и ведёт "
        "вашего настоящего жителя. Впишите под-токен персонажа ниже и "
        "попросите, например: «Пополни склад деревом».\n\n"
        f"*Модель (мозг): локальный LM Studio ({LM_BASE}), подхватывается сама.*"
    )
    token_input = gr.Textbox(
        type="password",
        label="Под-токен персонажа Cognopolis (обязательно)",
        placeholder="Character.token вашего жителя",
    )
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Лесоруб с умениями", type="messages", scale=1)
            with gr.Row():
                text_input = gr.Textbox(
                    lines=1,
                    label="Сообщение агенту",
                    placeholder="Пополни склад деревом",
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
            skills_box = gr.Markdown(
                # Тоже callable: витрина перечитывается с диска на каждую
                # загрузку страницы (и по кнопке «Сбросить»).
                value=skills_panel_text,
                label="Библиотека умений",
                container=True,
            )
            reset_btn = gr.Button("Сбросить")

    stored_message = gr.State("")
    text_input.submit(
        store_message, [text_input], [stored_message, text_input]
    ).then(respond, [stored_message, chatbot, token_input], [chatbot, state_box])
    send_btn.click(
        store_message, [text_input], [stored_message, text_input]
    ).then(respond, [stored_message, chatbot, token_input], [chatbot, state_box])
    reset_btn.click(reset_click, None, [chatbot, state_box, skills_box])


if __name__ == "__main__":
    # ssr_mode=False: экспериментальный SSR-режим Gradio 5 поднимает отдельный
    # Node.js-сервер, который на HF Spaces валит контейнер (в логе рантайма
    # «Stopping Node.js server...» перед RUNTIME_ERROR). Нам SSR не нужен —
    # это обычный чат, серверный рендер только добавляет точку отказа.
    demo.launch(ssr_mode=False)
