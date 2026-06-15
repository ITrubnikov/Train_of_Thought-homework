"""
Мой первый агент — заготовка к модулю 10.7 «Деплой агента: HF Spaces».

smolagents-агент с одним инструментом, обёрнутый в чат через GradioUI.
Деплоится на HF Spaces как есть. Нужен бесплатный HF-токен в секрете HF_TOKEN
(Space → Settings → Variables and secrets).

Замените/добавьте свой @tool (домашка модуля 10.7) — это и есть учебная правка.
"""
from smolagents import CodeAgent, InferenceClientModel, tool, GradioUI


@tool
def word_count(text: str) -> int:
    """Считает количество слов в тексте.

    Args:
        text: текст, в котором нужно посчитать слова.
    """
    return len(text.split())


@tool
def c_to_f(celsius: float) -> float:
    """Переводит температуру из Цельсия в Фаренгейты.

    Args:
        celsius: температура в градусах Цельсия.
    """
    return celsius * 9 / 5 + 32


# Открытая модель через HF Inference. Ключ берётся из секрета HF_TOKEN автоматически.
model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct")
agent = CodeAgent(tools=[word_count, c_to_f], model=model)

GradioUI(agent).launch()
