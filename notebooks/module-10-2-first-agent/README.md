# Модуль 10.2 — Клонируй живого агента: Space с котиком

Домашка к [Модулю 10.2: Клонируй живого агента](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-2-first-agent/).

Здесь **нет ноутбука** — и это намеренно. Агент это целостная система (модель + инструменты + петля + чат + хостинг), и щёлкать её по ячейкам неинтересно. Вместо этого вы **клонируете готовый живой Space**, включаете генерацию котика, добавляете свой инструмент — и получаете работающего агента по ссылке. Внутри это smolagents `CodeAgent` — та же петля, что вы писали руками в [модуле 10.1](https://github.com/ITrubnikov/Train_of_Thought-homework/tree/main/notebooks/module-10-1-agent-by-hand), только за одним методом `run()`.

## Что нужно до начала

- Аккаунт **Hugging Face**.
- **Бесплатный HF-токен** (huggingface.co → Settings → Access Tokens, роль `read`). Он же `HF_TOKEN`, что в модулях 10 и 10.7.
- Ничего ставить локально не нужно — всё происходит в браузере, в вашем Space.

## Артефакт

Не файл, а **ваша живая копия агента по URL**: Space, который по запросу «нарисуй котика» рисует картинку и умеет ваш собственный `@tool`.

## Шаги

1. **Duplicate.** Откройте шаблон [`agents-course/First_agent_template`](https://huggingface.co/spaces/agents-course/First_agent_template) → меню **⋮ → Duplicate this Space**. Получите личную копию со своим URL.
2. **Секрет `HF_TOKEN`.** В вашем Space: **Settings → Variables and secrets → New secret**, имя `HF_TOKEN`, значение — ваш токен. Без него агент молчит.
3. **Включите котика.** Вкладка **Files** → `app.py` (правка прямо в браузере). Найдите строку сборки агента и добавьте `image_generation_tool` в список инструментов:
   ```python
   # было:
   agent = CodeAgent(tools=[final_answer], model=model, ...)
   # стало:
   agent = CodeAgent(tools=[final_answer, image_generation_tool], model=model, ...)
   ```
   Сохраните — Space пересоберётся сам.
4. **Поговорите с агентом.** Откройте чат Space → «нарисуй котика» (или *generate an image of a cat*). Агент сам вызовет `image_generation_tool` и вернёт картинку.
5. **Сделайте своим.** Допишите в `app.py` собственный `@tool` (типы аргументов + docstring с секцией `Args:` — это контракт, из него строится схема для модели) и впишите его в `tools=[...]`. Спросите агента так, чтобы он позвал ваш инструмент.

## ДЗ — самопроверка

Полное задание — в [лекции 10.2](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-2-first-agent/). Кратко:

- [ ] Ваша копия Space открывается по URL, секрет `HF_TOKEN` положен.
- [ ] «нарисуй котика» → в чате появилась картинка (значит `image_generation_tool` в `tools=[...]`).
- [ ] Добавлен **свой** `@tool`, и видно, что агент его вызывает.

Артефакт — ссылка на ваш Space (можно со скриншотом котика), в чат как `[Модуль 10.2, ДЗ 1] {ссылка на Space}`.

## Подводные камни

- **Нет секрета `HF_TOKEN` → агент молчит.** Сборка прошла, но модель не вызвать. Ключ всегда секретом (Settings → Secrets), никогда в `app.py` — публичный Space показывает код всем.
- **Котик не рисуется → `image_generation_tool` не в `tools=[...]`.** В шаблоне инструмент объявлен, но по умолчанию агенту не выдан (`tools=[final_answer]`). Список `tools=[...]` — это «руки» агента; пока инструмента там нет, агент про него не знает.
- **Version drift: `HfApiModel` vs `InferenceClientModel`.** В живом `app.py` модель может создаваться как `HfApiModel`, а в тексте туториала — как `InferenceClientModel`. Это одно и то же, класс переименовали между версиями smolagents. Видите `ImportError`/`AttributeError` на имени класса — сверьте с версией пакета в Space.

## Деплой своего Space с нуля

Здесь вы **клонировали** готовый Space. Как собрать **свой с нуля** из трёх файлов (`app.py`, `requirements.txt`, `README.md`) и пройти грабли продакшена (`sdk_version`, засыпание, кредиты, безопасность исполнения кода) — в [Модуле 10.7. Деплой агента](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-7-deploy-agent/).
