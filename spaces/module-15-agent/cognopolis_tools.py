"""Инструменты лесоруба на РЕАЛЬНОМ API игры Cognopolis — для LangGraph/LangChain.

Контракт — дословно тот, что вы собрали в 11.5 и гоняли на smolagents, MCP и
LlamaIndex: узкие инструменты move / gather / get_character / get_map, конверт
ответа {result, cooldown, character} целиком, обучающие ошибки {code, message}.
Новое здесь — ЧЕМ контракт оформлен: LangChain собирает «паспорт» инструмента
из самой функции — имя из имени, description из docstring, схема аргументов из
type hints (Literal превращается в enum). Ровно тот же приём, что FunctionTool
в модуле 14, — меняется фреймворк, контракт не меняется ни на строчку.

Чек-лист A→H из лекции 11.5 никуда не делся: буквы A (имя), B (description) и
C (аргументы-enum) закрывает аккуратно написанная функция, буквы D (конверт
целиком) и E (ошибки как {code, message}) — наша забота, смотрите _envelope и
except GameError ниже.

Авторизация — `Authorization: Bearer <под-токен персонажа>` (Character.token).
Дом (0, 0) авто-банкует рюкзак сам — отдельного deposit нет, вместо него
get_character. Клиент — тонкая обёртка на requests, чтобы шаблон оставался
самодостаточным.
"""

import json
from typing import Literal, Optional

import requests

DEFAULT_BASE_URL = "https://kindomklaster.com"

# 4 стороны света — этого хватает, чтобы дойти до любого тайла на сетке
# (сервер поддерживает и диагонали, но enum держим простым, как в 11.5).
Direction = Literal["north", "south", "east", "west"]


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

    def _request(self, method: str, path: str, json_body: dict | None = None,
                 auth: bool = False) -> dict:
        headers = {}
        if auth:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            r = requests.request(method, self.base + path, json=json_body,
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
        return self._request("POST", f"/actions/move/{direction}", json_body={}, auth=True)

    def gather(self, resource: str | None = None) -> dict:
        return self._request("POST", "/actions/gather",
                             json_body={"resource": resource}, auth=True)

    def get_map(self) -> dict:
        return self._request("GET", "/map")

    def get_character(self) -> dict:
        return self._request("GET", "/character", auth=True)


def build_world_tools(client: CognopolisClient, on_state) -> list:
    """Четыре инструмента-действия над живым миром — голыми функциями.

    Список функций уходит сразу в две детали LangGraph: `llm.bind_tools(tools)`
    кладёт их паспорта в каждый вызов модели, `ToolNode(tools)` исполняет
    вызовы. on_state — колбэк app.py: каждый конверт с `character` обновляет
    боковую панель. Инструменты возвращают строку-JSON: результат всё равно
    едет модели текстом, а json.dumps делает это честно — конверт доезжает до
    агента ЦЕЛИКОМ и без питоньих кавычек (буква D чек-листа)."""

    def _envelope(env: dict) -> str:
        if isinstance(env, dict) and env.get("character"):
            on_state(env["character"])
        return json.dumps(env, ensure_ascii=False)

    def _game_error(exc: GameError) -> str:
        # Буква E: ошибка сервера доходит до агента как {code, message} —
        # по code он ветвится, по message чинит план сам.
        return json.dumps({"error": {"code": exc.code, "message": exc.message}},
                          ensure_ascii=False)

    def move(direction: Direction) -> str:
        """Шаг на одну клетку в сторону direction (north, south, east или west)
        по карте поселения. Возврат на дом (0, 0) сам разгружает рюкзак на склад
        (авто-банк). Возвращает конверт {result, cooldown, character}."""
        try:
            return _envelope(client.move_dir(direction))
        except GameError as exc:
            return _game_error(exc)

    def gather(resource: Optional[Literal["wood", "stone"]] = None) -> str:
        """Добыть ресурс с клетки, на которой стоит житель (дерево -> wood,
        камень -> stone). Без аргумента берёт то, что есть на клетке; с
        resource — только ожидаемое. Добытое падает в рюкзак (inventory), это
        ещё НЕ склад. Возвращает конверт {result, cooldown, character}."""
        try:
            return _envelope(client.gather(resource))
        except GameError as exc:
            return _game_error(exc)

    def get_character() -> str:
        """Показать своего жителя: позиция [x, y], hp, рюкзак (inventory),
        склад (stored). Чтение, мир не меняет. Замена deposit: банк на доме
        (0, 0) автоматический, проверяй сдачу по stored."""
        try:
            char = client.get_character()
            on_state(char)
            return json.dumps(char, ensure_ascii=False)
        except GameError as exc:
            return _game_error(exc)

    def get_map() -> str:
        """Карта поселения: размер и тайлы с содержимым (home, tree, rock,
        empty, враги goblin/wolf/ogre). Чтение, мир не меняет — безопасно
        повторять."""
        try:
            return json.dumps(client.get_map(), ensure_ascii=False)
        except GameError as exc:
            return _game_error(exc)

    # Паспорт каждой функции LangChain собирает сам: имя, docstring, схему
    # аргументов (Literal -> enum, буква C). Никаких обёрток — голые функции
    # понимают и bind_tools, и ToolNode.
    return [move, gather, get_character, get_map]
