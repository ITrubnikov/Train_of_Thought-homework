# MCP-сервер лесоруба из лекции 14.5 — тот же мок-лес и контракт, что в 11.5/13.6,
# но контракт вынесен из проекта в сервис: любой MCP-клиент подключается без обвязки.
#
# Запуск (stdio, как в лекции): python woodcutter_server.py
import time

from fastmcp import FastMCP


class Forest:
    """Мок-лес: сетка 5x5, лесоруб, рюкзак, склад и кулдаун — дословно из модуля 11.5."""

    COOLDOWN = 0.3  # в лекции 11.5 — 1.0; меньше — только ради времени прогона, правила те же

    def __init__(self):
        self.size = 5
        self.nodes = {(1, 2): "wood", (3, 1): "wood", (2, 4): "stone"}
        self.pos = (0, 0)        # где стоит лесоруб
        self.home = (0, 0)       # клетка склада
        self.backpack = {}       # например, {"wood": 3}
        self.cap = 5             # вместимость рюкзака
        self.stock = {}          # что уже сдано на склад
        self.busy_until = 0.0    # когда закончится кулдаун

    def cooldown_left(self):
        return max(0.0, self.busy_until - time.monotonic())

    def start_cooldown(self):
        self.busy_until = time.monotonic() + self.COOLDOWN


forest = Forest()

DIRECTIONS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def _err(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


mcp = FastMCP("woodcutter")  # имя сервера, его увидит клиент


@mcp.tool
def move(direction: str) -> dict:
    """Шагнуть на одну клетку мок-леса.

    Args:
        direction: направление — "north", "south", "east" или "west".
    """
    wait = forest.cooldown_left()
    if wait > 0:
        return _err("on_cooldown", f"Лесоруб занят ещё {wait:.1f} с — подождите и повторите.")
    if direction not in DIRECTIONS:
        return _err("unknown_direction",
                    "Допустимые направления: north, south, east, west.")
    dx, dy = DIRECTIONS[direction]
    x, y = forest.pos[0] + dx, forest.pos[1] + dy
    if not (0 <= x < forest.size and 0 <= y < forest.size):
        return _err("at_map_edge", "Дальше леса нет — выберите другое направление.")
    forest.pos = (x, y)
    forest.start_cooldown()
    return {"result": {"pos": [x, y]}, "cooldown": Forest.COOLDOWN}


@mcp.tool
def gather(resource: str | None = None) -> dict:
    """Добыть один ресурс с клетки, на которой стоит лесоруб. Без resource берёт узел
    под ногами; с resource — только ожидаемый, иначе вернёт no_resource_here."""
    wait = forest.cooldown_left()
    if wait > 0:
        return _err("on_cooldown", f"Лесоруб занят ещё {wait:.1f} с — подождите и повторите.")
    node = forest.nodes.get(forest.pos)
    if node is None or (resource is not None and node != resource):
        return _err("no_resource_here",
                    "На этой клетке нет нужного узла — найдите его в карте и подойдите move.")
    if sum(forest.backpack.values()) >= forest.cap:
        return _err("inventory_full", "Рюкзак полон — вернитесь на склад и сдайте deposit.")
    forest.backpack[node] = forest.backpack.get(node, 0) + 1
    forest.start_cooldown()
    return {"result": {"gathered": node, "backpack": dict(forest.backpack)},
            "cooldown": Forest.COOLDOWN}


@mcp.tool
def deposit() -> dict:
    """Сложить рюкзак на склад. Работает, только стоя на складе."""
    wait = forest.cooldown_left()
    if wait > 0:
        return _err("on_cooldown", f"Лесоруб занят ещё {wait:.1f} с — подождите и повторите.")
    if forest.pos != forest.home:
        return _err("not_at_home", "Склад на клетке [0, 0] — сначала дойдите до него move.")
    if not forest.backpack:
        return _err("backpack_empty", "Рюкзак пуст — сдавать нечего, сначала gather.")
    for item, qty in forest.backpack.items():
        forest.stock[item] = forest.stock.get(item, 0) + qty
    deposited = dict(forest.backpack)
    forest.backpack = {}
    forest.start_cooldown()
    return {"result": {"deposited": deposited, "stock": dict(forest.stock)},
            "cooldown": Forest.COOLDOWN}


@mcp.resource("woodcutter://map")
def get_map() -> dict:
    """Карта мок-леса: где лесоруб, узлы ресурсов и склад. Только чтение."""
    return {"pos": list(forest.pos), "home": list(forest.home),
            "nodes": [{"pos": list(p), "resource": r} for p, r in forest.nodes.items()]}


if __name__ == "__main__":
    mcp.run()  # по умолчанию — транспорт stdio
