# Модуль 10 — smolagents

Заготовки к [Модулю 10: smolagents](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-smolagents/).

**smolagents** — лёгкий агент-фреймворк от Hugging Face. Его философия:
агент = LLM + Python-функции-инструменты, цикл — пишет за тебя
библиотека, ты пишешь только функции. По сравнению с LangChain и
LlamaIndex — **минимум абстракций**: 30—50 строк на работающего агента.

## Что нужно сделать до начала

- Аккаунт Hugging Face, выпущен Read-токен и прикреплён к Kaggle Secrets
  как `HF_TOKEN` (см. [Модуль 1.5](../module-1-5-modern-tools/)).
- Базовое понимание function calling из [Модуля 8](../module-8-what-is-agent/).

## Файлы в папке

| Файл | Зачем |
| --- | --- |
| [`tools.ipynb`](tools.ipynb) | Адаптация ноутбука [Unit 2.1 / Tools](https://huggingface.co/learn/agents-course/unit2/smolagents/tools) из официального [HF Agents Course](https://huggingface.co/learn/agents-course). Два способа сделать tool в smolagents (`@tool`-декоратор vs subclass `Tool`), default toolbox, шеринг через HF Hub, импорт из Spaces / LangChain / MCP. История проходит через персонажа Альфреда, дворецкого Уэйнов, который готовит супергеройскую вечеринку. |

## Что вы делаете в ноутбуке

1. **`@tool`-декоратор** — простейший способ: оборачиваем обычную
   Python-функцию, smolagents сам читает аннотации и docstring,
   собирает JSON-схему для LLM.
2. **Subclass `Tool`** — для сложных инструментов с явной schema:
   `name`, `description`, `inputs`, `output_type`, `forward()`.
3. **Default toolbox** — встроенные инструменты `DuckDuckGoSearchTool`,
   `PythonInterpreterTool`, `FinalAnswerTool` и т.д.
4. **Шеринг** — `push_to_hub()` публикует ваш tool в HF Hub.
5. **Импорт чужих инструментов** — `load_tool()`, `Tool.from_space()`
   (любой Gradio Space становится инструментом), `Tool.from_langchain()`,
   `ToolCollection.from_mcp()` (любой MCP-сервер).

К концу ноутбука у вас в руках агент, который умеет искать в DuckDuckGo,
генерировать картинки через FLUX Space и обращаться к MCP-серверу.

## Сравнение с тем, что мы уже делали

| Что | Модуль 8 (Gemini function calling) | Модуль 10 (smolagents) |
| --- | --- | --- |
| Кто пишет цикл? | SDK Google | smolagents |
| Где модель крутится? | Gemini API (Google) | любая LLM (HF, OpenRouter, локально) |
| Как описывают tool? | Python-функция + типы + docstring | то же самое + `@tool` либо subclass |
| Tool из HF Hub? | нельзя | да (`load_tool`, `from_space`) |
| MCP-серверы? | нельзя без обёртки | да, нативно |

Тот же агент, что в модуле 8 (SQL-чат), здесь делается за столько же
строк, но переносится на любой LLM-бэкенд.

## ДЗ к модулю

Полный список — в [самой лекции](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-smolagents/). Минимально:

- Переписать SQL-агента из Модуля 8 на smolagents с тем же
  набором функций (`list_tables` / `describe_table` / `execute_query`).
- Добавить хотя бы один tool из default toolbox или из HF Spaces.
- Опубликовать свой собственный tool в HF Hub через `push_to_hub()`.

Артефакт — публичный Kaggle/Colab-ноутбук + ссылка на ваш tool в HF Hub,
в чат как `[Модуль 10, ДЗ {N}] {ссылка}`.

## Источник

Ноутбук — это копия [оригинала из HF Agents Course](https://huggingface.co/agents-course/notebooks/blob/main/unit2/smolagents/tools.ipynb)
под Apache 2.0. Все правки и комментарии на русском — наши.

Учебный канон: [HF Agents Course Unit 2](https://huggingface.co/learn/agents-course/unit2) (smolagents +
LlamaIndex + LangGraph) — мы будем проходить его параллельно нашим
модулям 10, 14, 15.
