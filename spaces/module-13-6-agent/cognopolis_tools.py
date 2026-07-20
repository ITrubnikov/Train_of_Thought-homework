"""Те же инструменты лесоруба, но на РЕАЛЬНОМ API игры Cognopolis.

Тезис лекции 11.5 в чистом виде: контракт tools не меняется, меняется только
то, куда они ходят. В 13.6 он же — фундамент скиллов: слой умений (витрина +
load_skill) живёт выше, в app.py и skills_runtime.py, а этот файл — без
правок. Мок-лес (`tools.py`) и этот файл дают один и тот же набор имён
(move / gather / get_map) с одним конвертом ответа и обучающими ошибками
{code, message} — но здесь за ними живой многопользовательский мир, а агент
управляет НАСТОЯЩИМ жителем поселения по его под-токену.

Авторизация — `Authorization: Bearer <под-токен персонажа>` (Character.token).
Действия возвращают конверт `{result, cooldown, character}`; нарушения правил
приходят как `{"error": {"code", "message"}}` — те же говорящие ошибки, что
студент видел в мок-лесу (no_resource_here, inventory_full, at_map_edge,
character_on_cooldown...). Дом (0,0) авто-банкует рюкзак сам — отдельного
deposit тут нет, поэтому вместо него инструмент get_character (посмотреть себя).

Клиент — тонкая обёртка на requests (та же зависимость, что у мок-части), чтобы
шаблон оставался самодостаточным и не тянул внешний SDK.
"""

import requests
from smolagents import Tool

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
    """Минимальный клиент живого API Cognopolis (ровно то, что нужно лесорубу)."""

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


# --- Инструменты агента: те же имена и тот же конверт, что в мок-лесу ---------

class _CognoTool(Tool):
    """Общий предок: держит клиента и колбэк обновления панели состояния."""

    def __init__(self, client: CognopolisClient, on_state):
        super().__init__()
        self.client = client
        self.on_state = on_state

    def _envelope(self, env: dict) -> dict:
        """Обновить панель из поля character конверта и вернуть его агенту."""
        if isinstance(env, dict) and env.get("character"):
            self.on_state(env["character"])
        return env


class MoveTool(_CognoTool):
    name = "move"
    description = (
        "Шаг на одну клетку в сторону direction по карте поселения. "
        "Возврат на дом (0, 0) сам разгружает рюкзак на склад (авто-банк)."
    )
    inputs = {
        "direction": {
            "type": "string",
            "enum": DIRECTIONS,
            "description": "Куда шагнуть: north, south, east или west.",
        }
    }
    output_type = "object"

    def forward(self, direction: str) -> dict:
        try:
            return self._envelope(self.client.move_dir(direction))
        except GameError as exc:
            return {"error": {"code": exc.code, "message": exc.message}}


class GatherTool(_CognoTool):
    name = "gather"
    description = (
        "Добыть ресурс с клетки, на которой стоит житель (дерево -> wood, камень -> stone). "
        "Без resource берёт то, что есть на клетке; с resource — только ожидаемое."
    )
    inputs = {
        "resource": {
            "type": "string",
            "enum": ["wood", "stone"],
            "nullable": True,
            "description": "Ожидаемый ресурс: wood или stone. По умолчанию — любой.",
        }
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
    )
    inputs = {}
    output_type = "object"

    def forward(self) -> dict:
        try:
            return self.client.get_map()
        except GameError as exc:
            return {"error": {"code": exc.code, "message": exc.message}}


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


def build_tools(client: CognopolisClient, on_state):
    """Готовый набор инструментов лесоруба поверх живого API Cognopolis."""
    return [
        MoveTool(client, on_state),
        GatherTool(client, on_state),
        GetCharacterTool(client, on_state),
        GetMapTool(client, on_state),
    ]
