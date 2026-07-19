"""Подпорки для СЛАБОЙ модели — вынесены из app.py специально, отдельным файлом.

Это НЕ про дизайн инструментов (тема урока 11.5) — контракт tools живёт в
`cognopolis_tools.py` и одинаков для любой модели. Здесь — приёмы «как
докрутить агента, когда мозг слабоват»: маленькая локальная 7B на живой карте
7x7 сама теряется в навигации и любит соврать «готово». Два приёма:

1) `task_seed` — детерминированная затравка: посчитать позицию + маршрут
   заранее и подсунуть агенту как план. Агент всё равно ходит настоящими
   move/gather — но не блуждает. Сильной модели затравка не мешает.
2) `fact_check` — проверка результата состоянием, а не словами: сравнить склад
   до/после прогона и честно сказать, сдал агент ресурс или только заявил.

Мораль урока: когда агент «тупит», сначала чините контракт (это `cognopolis_
tools.py`); а вот эти подпорки — уже про слабость КОНКРЕТНОЙ модели, и их
честно держать отдельно, чтобы не путать с дизайном tools. На сильной модели
весь этот файл можно выкинуть.
"""


def route_dirs(cx: int, cy: int, tx: int, ty: int) -> list[str]:
    """Манхэттен-маршрут [cx,cy]→[tx,ty] как список move-направлений (x, потом y).

    Соответствие направлений — как на сервере: east = x+1, west = x-1,
    south = y+1, north = y-1."""
    dirs: list[str] = []
    dirs += ["east"] * (tx - cx) if tx > cx else ["west"] * (cx - tx)
    dirs += ["south"] * (ty - cy) if ty > cy else ["north"] * (cy - ty)
    return dirs


def resource_for(text: str) -> str:
    """Какой ресурс просят в задаче (по тексту): камень → stone, иначе wood."""
    return "stone" if any(w in text.lower() for w in ("камен", "stone", "rock")) else "wood"


def task_seed(character: dict, gmap: dict, text: str) -> str:
    """Факты о живом мире + готовый маршрут — опора для слабой локальной модели.

    Мир персистентный, карта 7x7: qwen-7B иначе не считает направление (уходит
    к краю). Позицию и карту всё равно берём инструментами (get_character +
    get_map), а маршрут считаем детерминированно и предлагаем как план — агент
    исполняет его настоящими move/gather (сильной модели план не мешает, слабой
    спасает демо). Ресурс выбираем по тексту задачи (камень/stone → rock)."""
    cx, cy = character.get("x", 0), character.get("y", 0)
    by_kind: dict[str, list] = {}
    for tile in gmap.get("tiles", []):
        by_kind.setdefault(tile.get("content"), []).append((tile.get("x"), tile.get("y")))
    want_stone = any(w in text.lower() for w in ("камен", "stone", "rock"))
    kind, res = ("rock", "stone") if want_stone else ("tree", "wood")
    targets = by_kind.get(kind, [])
    enemies = by_kind.get("goblin", []) + by_kind.get("wolf", []) + by_kind.get("ogre", [])

    facts = (
        f"Ты сейчас стоишь на [{cx}, {cy}]. Дом (склад) на [0, 0]. "
        f"Ближайший ресурс {res} по клеткам: "
        f"{[list(t) for t in targets] or 'нет'}. "
        f"Клетки с врагами (не заходи): {[list(e) for e in enemies] or 'нет'}."
    )
    if not targets:
        return facts + f" Ресурса {res} на карте нет — сообщи об этом."

    tx, ty = min(targets, key=lambda t: abs(t[0] - cx) + abs(t[1] - cy))
    to_res = route_dirs(cx, cy, tx, ty)
    to_home = route_dirs(tx, ty, 0, 0)
    plan = ", ".join(f"move {d}" for d in to_res) or "(ты уже на клетке ресурса)"
    home = ", ".join(f"move {d}" for d in to_home) or "(ты уже дома)"
    return (
        facts + f" Рекомендуемый план до [{tx}, {ty}]: {plan}, затем gather. "
        f"Чтобы сдать на склад — вернись домой: {home} (дом [0, 0] сдаёт "
        f"{res} сам). Делай по одному вызову за раз, сверяя [x, y] в ответе."
    )


def fact_check(before: dict, after: dict, text: str) -> str:
    """Слова агента vs правда из игры: сдал ли он ресурс на склад НА САМОМ ДЕЛЕ.

    Считаем дельту склада (stored) до/после — так «в stored уже был wood с
    прошлого раза» не выдаётся за успех этого прогона. `banked` случается
    только на доме [0, 0]."""
    res = resource_for(text)
    x, y = after.get("x"), after.get("y")
    inv = after.get("inventory") or {}
    before_stored = (before.get("stored") or {}).get(res, 0)
    after_stored = (after.get("stored") or {}).get(res, 0)
    delta = after_stored - before_stored
    need_bank = any(w in text.lower() for w in ("сда", "склад", "storehouse", "deposit", "банк"))
    facts = (
        f"Проверка по факту (get_character): позиция [{x}, {y}], "
        f"рюкзак {dict(inv) or '{}'}, склад {dict(after.get('stored') or {}) or '{}'}."
    )
    if not need_bank:
        got = (inv.get(res, 0) or 0) + max(delta, 0)
        return ("✅ " + facts + f" {res} добыт." if got > 0
                else "ℹ️ " + facts + f" {res} пока не видно — проверьте прогон.")
    if delta > 0 and [x, y] == [0, 0]:
        return "✅ " + facts + f" Склад пополнился на {delta} {res} — сдано на самом деле."
    if inv.get(res, 0):
        return ("⚠️ " + facts + f" {res} ещё в РЮКЗАКЕ, житель не на доме [0, 0] — "
                "на склад НЕ сдан (агент поторопился с ответом). Попросите его "
                "вернуться на [0, 0] — дом сдаст сам.")
    return ("⚠️ " + facts + f" Склад по {res} не пополнился — задача не выполнена "
            "(агент мог не добыть ресурс или не дойти до дома).")
