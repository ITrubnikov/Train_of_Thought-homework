"""Инструменты лесоруба на РЕАЛЬНОМ API игры Cognopolis — с разбором дизайна.

Тезис лекции 11.5 в чистом виде: контракт tools не меняется, меняется только
то, куда они ходят. Тот же набор имён (move / gather / get_map), тот же конверт
ответа и те же обучающие ошибки {code, message}, что в мок-лесу ноутбука, — но
здесь за ними живой многопользовательский мир, а агент управляет НАСТОЯЩИМ
жителем поселения по его под-токену.

В файле ДВА набора инструментов — переключатель в build_tools() внизу:

- ХОРОШИЙ (активен) — узкие tools по одной цели, прошедшие чек-лист A→H
  из лекции; у ключевых строк стоят пометки, какую букву они закрывают;
- ПЛОХОЙ (закомментирован) — тот самый god-tool do_action(action, target)
  из Блока 1 ноутбука, перенесённый на живой API. Раскомментируйте его,
  переключите build_tools — и посмотрите, как та же модель на той же игре
  начинает угадывать строки и ходить по кругу.

Шпаргалка по чек-листу A→H (полный разбор — в лекции 11.5):
  A имя и сигнатура    B description    C аргументы (enum)   D конверт ответа
  E обучающие ошибки   F идемпотентность G blast radius       H лимиты ответа

Авторизация — `Authorization: Bearer <под-токен персонажа>` (Character.token).
Действия возвращают конверт `{result, cooldown, character}`; нарушения правил
приходят как `{"error": {"code", "message"}}` (no_resource_here,
inventory_full, at_map_edge, character_on_cooldown...). Дом (0,0) авто-банкует
рюкзак сам — отдельного deposit тут нет, вместо него get_character.

Клиент — тонкая обёртка на requests, чтобы шаблон оставался самодостаточным.
"""

import time

import requests
from smolagents import Tool, tool  # noqa: F401 — tool нужен плохому набору (закомментирован ниже)

DEFAULT_BASE_URL = "https://kindomklaster.com"

# 4 стороны света — этого хватает, чтобы дойти до любого тайла на сетке
# (сервер поддерживает и диагонали, но enum держим простым, как в мок-лесу).
DIRECTIONS = ["north", "south", "east", "west"]


class GameError(Exception):
    """Нарушение правила со стороны сервера — несёт канонический код ошибки."""

    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status_code = status_code


class CognopolisClient:
    """Минимальный клиент живого API Cognopolis (ровно то, что нужно лесорубу).

    Заметьте, чего здесь НЕТ: shell, произвольных URL, «выполни что угодно».
    Клиент умеет ровно 4 вызова, нужных лесорубу, — это буква G чек-листа:
    blast radius инструмента не шире задачи."""

    def __init__(self, base_url: str, token: str, timeout: float = 15.0):
        self.base = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.token = token
        self.timeout = timeout

    def _request(self, method: str, path: str, json: dict | None = None,
                 auth: bool = False) -> dict:
        headers = {}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            r = requests.request(method, self.base + path, json=json,
                                 headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise GameError("transport_error", str(exc), 0) from exc
        if r.status_code >= 400:
            try:
                err = r.json().get("error", {})
            except Exception:  # noqa: BLE001 — тело не JSON
                err = {}
            raise GameError(err.get("code", "http_error"),
                            err.get("message", r.text[:200]), r.status_code)
        return r.json()

    def move_dir(self, direction: str) -> dict:
        return self._request("POST", f"/actions/move/{direction}", json={}, auth=True)

    def gather(self, resource: str | None = None) -> dict:
        return self._request("POST", "/actions/gather", json={"resource": resource}, auth=True)

    def get_map(self) -> dict:
        return self._request("GET", "/map")

    def get_character(self) -> dict:
        return self._request("GET", "/character", auth=True)


# =============================================================================
# ХОРОШИЙ набор — герой лекции. Узкие tools по одной цели; пометки у строк
# показывают, какую букву чек-листа A→H закрывает каждое решение.
# =============================================================================


# ── ожидание такта (D-111 «работа видна») ──────────────────────────────────────
# Действие ставит жителя В РАБОТУ, и работа эта длится: шаг — около секунды, добыча
# и бой — около десяти, крафт — десятки секунд (длительность конкретного рецепта движок
# объявляет в GET /recipes → seconds). Агент-инструментальщик ждать не умеет: тулы «поспи»
# у него нет, а «повтори тот же вызов» на длинном такте только жжёт шаги — на каждый ранний
# вызов сервер отвечает character_on_cooldown, и мир не двигается.
# Поэтому такт досиживает сам инструмент, и ровно столько, сколько сказал сервер: число
# берётся из поля cooldown ТОГО ЖЕ конверта, ни одной зашитой константы.
WAIT_CAP_S = 60.0   # предохранитель: странное число с сервера не подвесит Space навсегда


def _wait_cooldown(env: dict) -> None:
    """Дождаться конца такта по полю cooldown конверта действия."""
    try:
        pause = float((env or {}).get("cooldown") or 0.0)
    except (TypeError, ValueError):
        return
    if pause > 0:
        time.sleep(min(pause, WAIT_CAP_S))


class _CognoTool(Tool):
    """Общий предок: держит клиента и колбэк обновления панели состояния."""

    def __init__(self, client: CognopolisClient, on_state):
        super().__init__()
        self.client = client
        self.on_state = on_state

    def _envelope(self, env: dict) -> dict:
        """Буква D: конверт {result, cooldown, character} отдаём агенту ЦЕЛИКОМ.

        result — что случилось; cooldown — когда можно следующий ход;
        character — состояние под следующий шаг (позиция, рюкзак). Модель
        планирует по этим полям, а панель app.py — рисует их человеку."""
        if isinstance(env, dict) and env.get("character"):
            self.on_state(env["character"])
        _wait_cooldown(env)                     # такт досиживаем ЗА агента — см. выше
        return env


class MoveTool(_CognoTool):
    name = "move"                                       # A: глагол, одна цель
    description = (                                     # B: что делает, когда звать,
        "Шаг на одну клетку в сторону direction по карте поселения. "
        "Возврат на дом (0, 0) сам разгружает рюкзак на склад (авто-банк)."
    )                                                   #    и побочный эффект (авто-банк)
    inputs = {
        "direction": {
            "type": "string",
            "enum": DIRECTIONS,                         # C: закрытый список вместо
            "description": "Куда шагнуть: north, south, east или west.",
        }                                               #    свободной строки — модель
    }                                                   #    не изобретает синонимы
    output_type = "object"

    def forward(self, direction: str) -> dict:
        try:
            return self._envelope(self.client.move_dir(direction))
        except GameError as exc:                        # E: ошибка сервера доходит до
            return {"error": {"code": exc.code,         #    агента как {code, message} —
                              "message": exc.message}}  #    по code он ветвится, по
                                                        #    message чинит план.
                                                        # F: кулдаун сервера на мутациях
                                                        #    (character_on_cooldown) —
                                                        #    слепой ретрай не сделает
                                                        #    второй шаг молча.


class GatherTool(_CognoTool):
    name = "gather"                                     # A: глагол, одна цель
    description = (
        "Добыть ресурс с клетки, на которой стоит житель (дерево -> wood, камень -> stone). "
        "Без resource берёт то, что есть на клетке; с resource — только ожидаемое."
    )
    inputs = {
        "resource": {
            "type": "string",
            "enum": ["wood", "stone"],                  # C: enum + осмысленный дефолт
            "nullable": True,                           #    (без аргумента — «что есть
            "description": "Ожидаемый ресурс: wood или stone. По умолчанию — любой.",
        }                                               #    на клетке»)
    }
    output_type = "object"

    def forward(self, resource: str | None = None) -> dict:
        try:
            return self._envelope(self.client.gather(resource))
        except GameError as exc:
            return {"error": {"code": exc.code, "message": exc.message}}


class GetMapTool(_CognoTool):
    name = "get_map"
    description = (
        "Карта поселения: размер, тайлы и их содержимое "
        "(home, tree, rock, empty и т.д.). Чтение, мир не меняет."
    )                                                   # B/F: «мир не меняет» — чтение
    inputs = {}                                         #      безопасно повторять
    output_type = "object"

    def forward(self) -> dict:
        try:
            return self.client.get_map()                # H: карта 7x7 — ответ мал по
        except GameError as exc:                        #    построению; будь мир большим,
            return {"error": {"code": exc.code,         #    сюда просился бы limit/radius
                              "message": exc.message}}


class GetCharacterTool(_CognoTool):
    name = "get_character"
    description = (
        "Показать своего жителя: позиция, рюкзак, hp, склад. "
        "Чтение, мир не меняет. Замена deposit — банк на доме (0, 0) автоматический."
    )
    inputs = {}
    output_type = "object"

    def forward(self) -> dict:
        try:
            char = self.client.get_character()
            self.on_state(char)
            return char
        except GameError as exc:
            return {"error": {"code": exc.code, "message": exc.message}}


# =============================================================================
# ПЛОХОЙ набор — антигерой лекции, закомментирован. Тот же do_action(action,
# target) из Блока 1 ноутбука, только ходит он теперь на ЖИВОЙ API: сервер
# отвечает теми же честными конвертами и обучающими ошибками, а этот tool всё
# съедает и отдаёт модели огрызки. Сервер хороший — контракт плохой.
#
# Как попробовать (и увидеть разницу своими глазами):
#   1) раскомментируйте блок ниже (до конца секции);
#   2) в build_tools() раскомментируйте ОДНУ помеченную строку
#      `return build_bad_tools(client)` — ранний return перекроет хороший
#      набор (вернуть хороший — снова закомментировать её);
#   3) перезапустите app.py и дайте агенту ту же задачу:
#      «Добудь одно дерево (wood) и сдай его на склад».
# Модель, база и сервер те же — поменялся только контракт. Смотрите в чате,
# как агент угадывает строки action/target, получает немое invalid и ходит
# по кругу; панель «Персонаж» перестаёт обновляться по ходу шагов агента
# (конверт с character выброшен) — правду показывают только снимок в начале
# сообщения и факт-чек в конце.
# =============================================================================

# def build_bad_tools(client: CognopolisClient):
#     """God-tool на живом API. Провалы чек-листа разобраны в комментариях."""
#
#     # A: одно имя на все действия — модель не видит, что умеет агент,
#     #    пока не угадает правильную пару строк.
#     # B: docstring ниже — skinny description: «что именно можно делать»,
#     #    «когда звать» и побочные эффекты модели никто не сказал, а других
#     #    источников у неё нет. smolagents соберёт схему без единой жалобы —
#     #    честный docstring не спасает плохой контракт.
#     @tool
#     def do_action(action: str, target: str) -> dict:
#         """Выполнить действие в поселении.
#
#         Args:
#             action: какое действие выполнить.
#             target: цель действия.
#         """
#         try:
#             # C: свободные строки + внутренние имена вместо enum: правильные
#             #    заклинания relocate/n и harvest_node/self_tile нигде не
#             #    объявлены — их можно только угадать (или выучить из ошибок,
#             #    но ошибки тут немые — см. E).
#             if action == "relocate" and target in ("n", "s", "e", "w"):
#                 full = {"n": "north", "s": "south", "e": "east", "w": "west"}[target]
#                 client.move_dir(full)
#                 return {"ok": True}                   # D: конверт выброшен — где
#                                                       #    житель теперь, что в
#                                                       #    рюкзаке, был ли банк на
#                                                       #    доме — агенту не видно
#             if action == "harvest_node" and target == "self_tile":
#                 client.gather()
#                 return {"ok": True}                   # D: добыл — а ЧТО добыл?
#             # Ни карты, ни «посмотреть себя» этот набор не даёт вовсе:
#             # агент играет вслепую в персистентном мире, где он даже не
#             # знает, откуда стартует.
#             return {"error": "invalid"}               # E: неизвестный глагол — и
#                                                       #    немой отказ без подсказки
#         except GameError:
#             # E: сервер прислал обучающую пару {code, message} (например,
#             #    character_on_cooldown — «подожди и повтори»), а tool её
#             #    съел и оставил модель наедине с "invalid".
#             # F: из-за этого же кулдаун неотличим от настоящей ошибки —
#             #    агент не знает, что нужно просто повторить тот же вызов.
#             return {"error": "invalid"}
#
#     return [do_action]


def build_tools(client: CognopolisClient, on_state):
    """Набор инструментов лесоруба. Переключатель хороший/плохой — здесь."""
    # ПЛОХОЙ набор — для эксперимента: раскомментируйте build_bad_tools выше
    # и строку ниже (ранний return перекроет хороший набор):
    # return build_bad_tools(client)
    # ХОРОШИЙ набор (активен): узкие tools, enum, обучающие ошибки, конверт.
    return [
        MoveTool(client, on_state),
        GatherTool(client, on_state),
        GetCharacterTool(client, on_state),
        GetMapTool(client, on_state),
    ]
