# Модуль 10.7 — Деплой агента: HF Spaces

Домашка к [Модулю 10.7: Деплой агента](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-7-deploy-agent/).

Здесь вы соберёте smolagents-агента с инструментом, добавите **свой** `@tool` и развернёте агента как живой веб-чат на HF Spaces по трём файлам. Артефакт — Space с вашим агентом, ссылку на который можно дать другу.

## Что нужно до начала
- **Бесплатный HF-токен** (huggingface.co → Settings → Access Tokens, роль `read`). Без него ни ноутбук, ни Space модель не позовут.
- Ноутбук на **smolagents** + открытая модель через HF Inference (тратит бесплатные месячные кредиты HF).
- Откройте `notebook.ipynb` в Colab (бейдж ниже) — зависимости ставятся первой ячейкой.

## Файлы
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Пошагово: агент с инструментом → свой `@tool` → три файла Space → шаги деплоя. `Run all` проходит (нужен `HF_TOKEN`). |

Готовый Space-шаблон лежит рядом в репозитории: [`spaces/module-10-7-agent/`](https://github.com/ITrubnikov/Train_of_Thought-homework/tree/main/spaces/module-10-7-agent) (`app.py`, `requirements.txt`, `README.md`).

## Что в ноутбуке
1. Установка `smolagents` + токен `HF_TOKEN`.
2. Первый агент: `@tool word_count` + `CodeAgent` + `InferenceClientModel`; `agent.run(...)`.
3. Свой инструмент: конвертер `c_to_f`; агент с двумя инструментами выбирает нужный.
4. Три файла Space (`app.py` с `GradioUI(agent).launch()`, `requirements.txt`, `README.md` с YAML-шапкой) и шаги деплоя.

## Как запустить ноутбук
### Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-10-7-deploy-agent/notebook.ipynb)

Добавьте `HF_TOKEN` через `Secrets`, затем `Runtime → Run all`. GPU не нужен.

### Локально
```bash
pip install smolagents python-dotenv
export HF_TOKEN=hf_...
jupyter lab notebook.ipynb
```

## Как задеплоить агента (артефакт ДЗ)
1. huggingface.co → **New → Space**, SDK — **Gradio**.
2. Залейте `app.py` / `requirements.txt` / `README.md` из `spaces/module-10-7-agent/` (с вашим инструментом) — через *Files → Add file* или `git push` в репозиторий Space.
3. **Settings → Variables and secrets → New secret**: `HF_TOKEN` = ваш токен.
4. Дождитесь сборки → откройте URL → чат с агентом.

## ДЗ — самопроверка
- [ ] Ноутбук прогнан, агент с инструментом ответил.
- [ ] Добавлен **свой** `@tool`; в логах видно, что агент его вызвал.
- [ ] Space собрался (`sdk_version` 5.x, секрет `HF_TOKEN`), по URL открывается чат.
- [ ] Ссылка на Space записана; токен нигде не захардкожен.

## Подводные камни
- **`sdk_version` в README — только 5.x.** gradio 4.x падает на Python 3.13 (`ModuleNotFoundError: audioop`), на котором HF собирает Spaces.
- **Нет секрета `HF_TOKEN` → агент молчит.** Ключ всегда секретом, никогда в `app.py` (публичный Space показывает код).
- **`@tool` без докстринга** не виден агенту — smolagents строит описание инструмента из докстринга (описание + `Args`).
- **CodeAgent исполняет сгенерированный код.** Для недоверенных входов нужен sandbox — см. модуль 9.5 и доку smolagents про secure code execution.
- **Бесплатный Space засыпает** — первый ответ после простоя идёт дольше (холодный старт), это норма. И каждый вызов тратит бесплатные кредиты HF Inference.
