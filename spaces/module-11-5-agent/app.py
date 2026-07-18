"""Приложение А к Модулю 11.5 — лесоруб уезжает на HF Spaces.

Хороший набор tools из домашки (move, gather, deposit, get_map), отданный живой
модели через ToolCallingAgent и обёрнутый в веб-чат GradioUI — по механике
Модуля 10.7 «Деплой агента». Классы Forest и все инструменты скопированы из
notebooks/module-11-5-tool-design/notebook.ipynb без изменений.

Для работы чата на HF Spaces нужен секрет HF_TOKEN
(Space -> Settings -> Variables and secrets). При импорте файла как модуля
сеть не трогается: живой блок внизу спрятан под if __name__ == "__main__".
"""
from smolagents import tool, Tool

import time


class Forest:
    """Мок-лес: сетка 5x5, лесоруб, рюкзак, склад и кулдаун."""

    COOLDOWN = 0.3  # в лекции 1.0; здесь меньше, чтобы Run all занимал ~минуту, — правила те же

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

    def backpack_load(self):
        return sum(self.backpack.values())


forest = Forest()


def reset_forest():
    """Свежий мир перед каждым сценарием. Tools ниже смотрят на глобальную forest."""
    global forest
    forest = Forest()


@tool
def get_map() -> dict:
    """Карта леса: позиция лесоруба, узлы ресурсов и клетка склада. Мир не меняет."""
    return {"pos": list(forest.pos), "home": list(forest.home),
            "nodes": [{"pos": list(p), "resource": r} for p, r in forest.nodes.items()]}


class GatherTool(Tool):
    name = "gather"
    description = (
        "Добыть один ресурс с клетки, на которой стоит лесоруб. "
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
        wait = forest.cooldown_left()
        if wait > 0:
            return {"error": {"code": "on_cooldown",
                              "message": f"Лесоруб занят ещё {wait:.1f} с — подождите и повторите."}}
        node = forest.nodes.get(forest.pos)
        if node is None or (resource is not None and node != resource):
            return {"error": {"code": "no_resource_here",
                              "message": "На этой клетке нет нужного узла — "
                                         "найдите его через get_map и подойдите move."}}
        if forest.backpack_load() >= forest.cap:
            return {"error": {"code": "inventory_full",
                              "message": f"Рюкзак полон ({forest.cap}/{forest.cap}) — "
                                         "вернитесь на склад (0, 0) и позовите deposit."}}
        forest.backpack[node] = forest.backpack.get(node, 0) + 1
        forest.start_cooldown()
        return {"result": {"gathered": node, "amount": 1},
                "cooldown": Forest.COOLDOWN,
                "state": {"pos": list(forest.pos),
                          "backpack": dict(forest.backpack), "cap": forest.cap}}


class MoveTool(Tool):
    name = "move"
    description = (
        "Шаг на одну клетку в сторону direction. "
        "Зовите, когда до нужного узла или склада не хватает шага."
    )
    inputs = {
        "direction": {
            "type": "string",
            "enum": ["north", "south", "east", "west"],
            "description": "Куда шагнуть: north, south, east или west.",
        }
    }
    output_type = "object"

    def forward(self, direction: str) -> dict:
        wait = forest.cooldown_left()
        if wait > 0:
            return {"error": {"code": "on_cooldown",
                              "message": f"Лесоруб занят ещё {wait:.1f} с — подождите и повторите."}}
        dx, dy = {"north": (0, -1), "south": (0, 1),
                  "east": (1, 0), "west": (-1, 0)}[direction]
        x, y = forest.pos
        forest.pos = (min(max(x + dx, 0), forest.size - 1),
                      min(max(y + dy, 0), forest.size - 1))
        forest.start_cooldown()
        return {"result": {"pos": list(forest.pos)},
                "cooldown": Forest.COOLDOWN,
                "state": {"pos": list(forest.pos),
                          "backpack": dict(forest.backpack), "cap": forest.cap}}


@tool
def deposit() -> dict:
    """Сдать содержимое рюкзака на склад. Работает только на клетке склада (0, 0)."""
    wait = forest.cooldown_left()
    if wait > 0:
        return {"error": {"code": "on_cooldown",
                          "message": f"Лесоруб занят ещё {wait:.1f} с — подождите и повторите."}}
    if forest.pos != forest.home:
        return {"error": {"code": "not_at_storehouse",
                          "message": f"Склад на клетке (0, 0), а вы — на {forest.pos}. "
                                     "Дойдите до склада и повторите deposit."}}
    banked, forest.backpack = forest.backpack, {}
    for res, n in banked.items():
        forest.stock[res] = forest.stock.get(res, 0) + n
    forest.start_cooldown()
    return {"result": {"banked": banked},
            "cooldown": forest.COOLDOWN,
            "state": {"pos": list(forest.pos), "backpack": {}, "stock": forest.stock}}


move, gather = MoveTool(), GatherTool()
if __name__ == "__main__":
    # На Spaces app.py запускается как главный скрипт -> чат стартует сам.
    # При импорте (смоук в ноутбуке-приложении) __name__ другой -> блок молчит.
    from smolagents import InferenceClientModel, ToolCallingAgent, GradioUI

    model = InferenceClientModel()   # HF_TOKEN возьмёт из Secrets Space
    agent = ToolCallingAgent(tools=[move, gather, deposit, get_map], model=model, max_steps=12)
    GradioUI(agent).launch()
