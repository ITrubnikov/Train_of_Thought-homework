# MCP-сервер поверх ЖИВОГО игрового API Cognopolis (https://kindomklaster.com) —
# «обёртка над игровым API» из домашки модуля 14.5.
#
# Контракт tools — дословно лесоруб из 11.5 (move / gather / get_map / get_character),
# но за ними не мок-лес, а настоящий житель поселения. Одно добавление живого мира —
# wait_events: ждущее чтение Хроники (long-poll GET /events/wait), с ним петля агента
# становится «жду -> действую -> жду» вместо опроса по таймеру. Ждать умеет именно МОСТ:
# родной MCP движка (python -m server.mcp_server) поднимается отдельным процессом, а шина
# пробуждения живёт в памяти процесса игры, поэтому ждун внутри него не услышал бы ни
# одного события. Под-токен жителя сервер берёт из окружения COGNOPOLIS_TOKEN — клиент
# передаёт его при запуске подпроцесса (stdio), в сам протокол токен не попадает.
#
# Запуск: python cognopolis_mcp_server.py
# Токен: скопируйте .env-example в .env и впишите COGNOPOLIS_TOKEN — либо передайте
# переменной окружения (настоящее окружение важнее .env).
import os
from pathlib import Path
from typing import Literal

import requests
from fastmcp import FastMCP


def _load_dotenv() -> None:
    """Подхватить .env рядом с файлом (шаблон — .env-example). Настоящие переменные
    окружения ВАЖНЕЕ: .env заполняет только пропуски — так клиент (ноутбук, Claude
    Code) может передать токен через env подпроцесса, не трогая файл."""
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

BASE_URL = os.environ.get("COGNOPOLIS_BASE_URL", "https://kindomklaster.com").rstrip("/")
TOKEN = os.environ.get("COGNOPOLIS_TOKEN", "")

mcp = FastMCP("cognopolis")


def _request(method: str, path: str, json: dict | None = None, auth: bool = False,
             params: dict | None = None, timeout: float = 15) -> dict:
    """Один HTTP-вызов живого API. Ошибку сервера возвращаем как {error: {code, message}} —
    та же обучающая пара, что в 11.5: по code агент ветвится, по message чинит план.

    `timeout` — окно ожидания ОТВЕТА, а не игрового такта. Поднимает его только ждущий вызов
    (`wait_events`): там сервер молча держит соединение и отвечает ПОСЛЕ своего окна, поэтому
    клиент обязан ждать дольше сервера, иначе оборвёт связь ровно в момент отправки ответа."""
    headers = {"Authorization": f"Bearer {TOKEN}"} if auth else {}
    try:
        r = requests.request(method, BASE_URL + path, json=json, headers=headers,
                             params=params, timeout=timeout)
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
def wait_events(since: int | None = None, timeout: float = 25.0, limit: int = 50) -> list:
    """ЖДАТЬ новостей о своём жителе вместо опроса по кругу: вызов возвращается, как только в
    Хронике жителя появилась запись, — или пустым списком, когда окно timeout вышло молча.

    Так петля агента становится «жду -> действую -> жду»: новость приходит через миллисекунды
    после того, как мир её записал, а не «проверю ещё разок». События отдаются новыми сверху.

    since — ТВОЙ курсор, его ведёшь ты, а не сервер: приезжает только то, у чего seq > since.
    Передавай наибольший seq, который уже видел. Без since отсчёт идёт «с этого момента» —
    придёт только то, что случится после вызова.
    timeout — сколько сервер может держать ответ, 0..25 секунд (0 = ответить сразу).

    ПУСТОЙ СПИСОК — ЭТО НОРМА, а не ошибка и не «новостей больше не будет»: за это окно ничего
    не произошло, приходи снова с тем же since. Соединение может оборваться и раньше срока
    (выкатка перезапускает сервер) — просто позови ещё раз: курсор у тебя свой, ничего не потеряно.

    ЭТО НЕ ЗАМЕНА ОЖИДАНИЮ ТАКТА. Кулдаун жителя — не событие: истечение такта в Хронику не
    пишется, и ждун о нём не проснётся. На character_on_cooldown по-прежнему просто повтори тот
    же вызов; wait_events будит, когда что-то произошло В МИРЕ."""
    params: dict = {"limit": limit, "timeout": timeout}
    if since is not None:
        params["since"] = since
    # +5 с поверх серверного окна: ответ по таймауту рождается ПОСЛЕ него, и клиент, ждущий
    # ровно столько же, оборвал бы соединение в момент отправки ответа.
    return _request("GET", "/events/wait", auth=True, params=params, timeout=timeout + 5)


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
