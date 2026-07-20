"""Мини-runtime скиллов: учебный парсер SKILL.md, витрина и инструмент load_skill.

Парсер — ТОТ ЖЕ код, что в Блоке 2 ноутбука 13.6 (учебный, без pyyaml):
`parse_skill` понимает frontmatter с `name:` и `description:` (в строку или
свёрнутым блоком `>-`), `load_skills` обходит `skills/*/SKILL.md`,
`skills_index` собирает витрину — только name + description.

Селектора из ноутбука здесь НЕТ, и это не упущение: скриптовый селектор был
keyless-заменой модели, а в space описание читает сама живая модель — это и
есть прод-режим progressive disclosure. Витрина уходит в instructions агента,
тело скилла модель подтягивает сама инструментом load_skill (ниже).
"""

from pathlib import Path

from smolagents import Tool


def parse_skill(text):
    """SKILL.md -> {"name", "description", "body"}; ошибка парсинга -> None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)          # закрывающая пара фронтматтера
    except ValueError:
        return None
    front, body = lines[1:end], "\n".join(lines[end + 1:]).strip()
    name, description, i = "", "", 0
    while i < len(front):
        line = front[i]
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value in (">-", ">"):         # свёрнутый блок: строки с отступом клеим пробелом
                folded = []
                while i + 1 < len(front) and front[i + 1].startswith(" "):
                    folded.append(front[i + 1].strip())
                    i += 1
                value = " ".join(folded)
            description = value
        i += 1
    return {"name": name, "description": description, "body": body}


def load_skills(skills_dir):
    """Обойти skills/*/SKILL.md; вернуть список распарсенных dict."""
    skills = []
    for path in sorted(Path(skills_dir).glob("*/SKILL.md")):
        skill = parse_skill(path.read_text(encoding="utf-8"))
        if skill:
            skills.append(skill)
    return skills


def skills_index(skills):
    """«Витрина»: только name + description. В контексте агента живёт ТОЛЬКО это."""
    return "\n".join(f"- {s['name']}: {s['description']}" for s in skills)


class LoadSkillTool(Tool):
    """Execution по требованию: подтянуть тело скилла, когда триггер сработал.

    Конструктор принимает либо готовый список скиллов, либо callable без
    аргументов, который его возвращает (в app.py передаётся загрузчик с диска —
    так правка тела SKILL.md видна агенту сразу, без пересборки)."""

    name = "load_skill"
    description = (
        "Загрузить полный текст умения (skill) из библиотеки по имени. "
        "Зови, когда описание умения в списке совпало с задачей."
    )
    inputs = {"name": {"type": "string",
                       "description": "Имя умения из списка, например supply-run."}}
    output_type = "any"   # тело строкой либо конверт с обучающей ошибкой

    def __init__(self, skills):
        super().__init__()
        self._skills = skills

    def _current(self):
        return self._skills() if callable(self._skills) else self._skills

    def forward(self, name: str):
        skills = self._current()
        for skill in skills:
            if skill["name"] == name:
                return skill["body"]
        known = ", ".join(sorted(s["name"] for s in skills))
        return {"error": {"code": "unknown_skill",
                          "message": f"Нет такого умения. Доступны: {known}."}}
