# MCP-сервер поверх ЖИВОГО игрового API Cognopolis (https://kindomklaster.com) —
# «обёртка над игровым API» из домашки модуля 14.5.
#
# Контракт tools — дословно лесоруб из 11.5 (move / gather / get_map / get_character),
# но за ними не мок-лес, а настоящий житель поселения. Под-токен жителя сервер
# берёт из окружения COGNOPOLIS_TOKEN — клиент передаёт его при запуске подпроцесса
# (stdio), в сам протокол токен не попадает.
#
# Запуск: COGNOPOLIS_TOKEN=<под-токен> python cognopolis_mcp_server.py
import os
from typing import Literal

import requests
from fastmcp import FastMCP

BASE_URL = os.environ.get("COGNOPOLIS_BASE_URL", "https://kindomklaster.com").rstrip("/")
TOKEN = os.environ.get("COGNOPOLIS_TOKEN", "")

mcp = FastMCP("cognopolis")


def _request(method: str, path: str, json: dict | None = None, auth: bool = False) -> dict:
    """Один HTTP-вызов живого API. Ошибку сервера возвращаем как {error: {code, message}} —
    та же обучающая пара, что в 11.5: по code агент ветвится, по message чинит план."""
    headers = {"Authorization": f"Bearer {TOKEN}"} if auth else {}
    try:
        r = requests.request(method, BASE_URL + path, json=json, headers=headers, timeout=15)
    except requests.RequestException as exc:
        return {"error": {"code": "transport_error", "message": str(exc)}}
    if r.status_code >= 400:
        try:
            err = r.json().get("error", {})
        except Exception:
            err = {}
        return {"error": {"code": err.get("code", "http_error"),
                          "message": err.get("message", r.text[:200])}}
    return r.json()


@mcp.tool
def move(direction: Literal["north", "south", "east", "west"]) -> dict:
    """Шагнуть жителем на одну клетку в сторону direction. Возврат на дом (0, 0)
    сам разгружает рюкзак на склад (авто-банк) — отдельного deposit в живом мире нет.
    Ответ — конверт {result, cooldown, character}; нарушение правила — {error: {code, message}}."""
    return _request("POST", f"/actions/move/{direction}", json={}, auth=True)


@mcp.tool
def gather(resource: Literal["wood", "stone"] | None = None) -> dict:
    """Добыть ресурс с клетки, на которой стоит житель (дерево -> wood, камень -> stone).
    Без resource берёт то, что есть на клетке; с resource — только ожидаемое."""
    return _request("POST", "/actions/gather", json={"resource": resource}, auth=True)


@mcp.tool
def get_character() -> dict:
    """Показать своего жителя: позиция, hp, рюкзак, склад и казна поселения.
    Чтение, мир не меняет; кулдаун не ставит."""
    return _request("GET", "/character", auth=True)


@mcp.tool
def get_map() -> dict:
    """Карта поселения: тайлы (home, tree, rock, ...) и живые враги. Чтение, мир не меняет.
    Дубль ресурса cognopolis://map как tool — осознанный трейд-офф из лекции: часть агентных
    клиентов (включая ToolCollection.from_mcp) умеет подтягивать только tools."""
    return _request("GET", "/map")


@mcp.resource("cognopolis://map")
def map_resource() -> dict:
    """Та же карта поселения, но правильным примитивом — resource: данные на чтение со своим URI."""
    return _request("GET", "/map")


if __name__ == "__main__":
    mcp.run()  # stdio: клиент запускает этот файл подпроцессом и передаёт COGNOPOLIS_TOKEN в env
