# Модуль 10.2 — Первый агент на smolagents, пошагово

Домашка к [Модулю 10.2: Первый агент на smolagents, пошагово](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-2-first-agent/).

В модуле 10.1 вы собрали петлю ReAct руками: системный промпт, стоп-токен, парсинг JSON, ручной вызов тула. Здесь та же петля прячется за одним методом `CodeAgent.run()`, а ваша работа сводится к двум вещам: написать **свои** `@tool` и собрать агента под **свою** задачу. Артефакт — работающий smolagents-агент с вашими инструментами и вывод build-twice: что вы потеряли в контроле и что выиграли в удобстве по сравнению с 10.1.

## Что нужно до начала

- **Бесплатный HF-токен** (huggingface.co → Settings → Access Tokens, роль `read`). Без него модель не позвать.
- Знакомство с ручной петлёй из [модуля 10.1](https://github.com/ITrubnikov/Train_of_Thought-homework/tree/main/notebooks/module-10-1-agent-by-hand) — на неё мы будем опираться в сравнении.
- Зависимости (`smolagents`) ставятся первой ячейкой ноутбука.

## Файлы

| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Пошагово: свой `@tool` (типы + docstring с `Args:`) → `CodeAgent` + `InferenceClientModel` → `agent.run(...)` → сравнение с петлёй из 10.1. `Run all` проходит (нужен `HF_TOKEN`). |

## Что вы делаете в ноутбуке

1. Пишете свой `@tool`: типы аргументов + docstring с секцией `Args:`. Это **контракт** — именно из него smolagents строит схему инструмента для модели. Нет docstring — модель не знает, что тул умеет.
2. Собираете `CodeAgent(tools=[...], model=InferenceClientModel(...))` и запускаете `agent.run(...)`. Модель сама решает, какой тул и с какими аргументами позвать.
3. **Build-twice:** сравниваете с ручной петлёй из 10.1. То, что вы писали сами (петля, стоп-токен, парсинг действия, подача `Observation` обратно), теперь делает `run()` за вас. Считаете, сколько строк ушло и что вы отдали фреймворку из контроля.

Ключевая мысль: дефолтный агент с `tools=[final_answer]` по умолчанию **не умеет ничего** — это пустой каркас. Вся работа — дописать инструменты в этот список под свою задачу.

## Как запустить ноутбук

### A. Colab (проще всего)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-10-2-first-agent/notebook.ipynb)

Добавьте `HF_TOKEN` через `Secrets` (значок ключа слева), затем `Runtime → Run all`. GPU не нужен.

### B. Kaggle

`File → Import Notebook → URL`:

```
https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-10-2-first-agent/notebook.ipynb
```

Затем `Add-ons → Secrets` добавьте `HF_TOKEN` и `Run all`.

### C. Локально

```bash
pip install smolagents
export HF_TOKEN=hf_...
jupyter lab notebook.ipynb
```

## ДЗ — самопроверка

Полное задание — в [лекции 10.2](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-2-first-agent/). Кратко:

- [ ] Написаны 2-3 **своих** `@tool` под свою задачу (не SQL-агент из ДЗ1 модуля 10, не пример из лекции).
- [ ] Собран `CodeAgent` с вашими инструментами, прогнаны 2-3 осмысленных запроса; в логах видно, какой тул агент позвал.
- [ ] Сделан build-twice-вывод: сколько строк было в 10.1 против здесь, что потеряли в контроле, что выиграли в удобстве.

Артефакт — публичная ссылка на ноутбук, в чат как `[Модуль 10.2, ДЗ 1] {ссылка}`.

## Подводные камни

- **`@tool` без docstring** не виден модели. smolagents строит схему инструмента из типов аргументов и docstring с секцией `Args:`. Нет описания — модель не понимает, когда и как звать тул.
- **Пустой список инструментов → агент ничего не умеет.** Дефолтный `tools=[final_answer]` (как в шаблоне `First_agent_template`) — это пустой каркас. Пока вы не дописали свои тулы, агент не делает ничего полезного.
- **Version drift: `HfApiModel` vs `InferenceClientModel`.** В живом `First_agent_template/app.py` модель создаётся как `HfApiModel`, а в тексте туториала местами встречается `InferenceClientModel` — типовая засада версий smolagents. Мы используем `InferenceClientModel`; если копируете чужой пример и видите `ImportError`/`AttributeError` на классе модели — это первое, что нужно проверить.

## Деплой

Превратить вашего агента в живой веб-чат на HF Spaces (duplicate Space, секрет `HF_TOKEN`, Gradio, `sdk_version`) — отдельная тема: [Модуль 10.7. Деплой агента](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-7-deploy-agent/).
