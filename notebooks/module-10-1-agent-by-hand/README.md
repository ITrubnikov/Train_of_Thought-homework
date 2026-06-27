# Модуль 10.1 — Агент руками: цикл ReAct без фреймворка

Домашка к [Модулю 10.1: Агент руками](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-1-agent-by-hand/).

Здесь вы соберёте агента **руками** — без фреймворка и без automatic function calling. Своя петля Thought -> Action -> Observation в ~50 строк голого Python: системный промпт-контракт, стоп-токен, парсинг JSON-действия, ручной вызов тула, подача реального результата обратно в контекст. Артефакт — ноутбук с трейсом прогона минимум на два шага.

В модуле 10 вы видели `CodeAgent.run()` как магию. Здесь — то же самое, но руками: фреймворк прячет петлю, а вы её пишете и видите, что именно он прячет.

## Что нужно до начала
- **Бесплатный HF-токен** (huggingface.co -> Settings -> Access Tokens, роль `read`). Без него ноутбук модель не позовёт — будет `401`. Тот же токен, что в модулях 10 и 10.7, нового не нужно.
- Модель — открытая instruct через HF Inference (`Qwen/Qwen2.5-Coder-32B-Instruct`), интерфейс OpenAI-совместимый `chat.completions.create(..., stop=["Observation:"])`. Тратит бесплатные месячные кредиты HF.
- GPU не нужен — мы только зовём Inference API, ничего локально не считаем.

## Файлы
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Пошагово: дамми-тул -> демо галлюцинации без стопа -> промпт-контракт -> ручная петля до `Final Answer:`. `Run all` проходит (нужен `HF_TOKEN`). |

## Что вы делаете
1. **Дамми-тул** `get_weather(location)` — пустышка с зашитой строкой. Учебный тул, чтобы видеть границу: что делает код, а что — модель.
2. **Демо галлюцинации.** Без стоп-токена модель сама дописывает `Observation:` — придумывает результат тула, которого не было. Это ключевое демо: модель верит собственной выдумке.
3. **Фикс стоп-токеном.** `stop=["Observation:"]` обрывает генерацию ровно перед `Observation:` и возвращает управление вашему коду — теперь реальный тул зовёте вы.
4. **Парсинг действия.** Действие модели — JSON-блок с ключами `action` (имя тула) и `action_input` (аргументы). Вы его вынимаете, зовёте Python-функцию, подаёте её результат обратно как `Observation:`.
5. **Петля** Thought -> Action -> Observation, повтор пока модель не выдаст `Final Answer:`.

## Как запустить ноутбук
### Вариант A — Colab (проще всего)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-10-1-agent-by-hand/notebook.ipynb)

Добавьте `HF_TOKEN` через `Secrets` (иконка ключа слева), затем `Runtime -> Run all`.

### Вариант B — Kaggle
1. Kaggle -> `Create -> New Notebook -> File -> Import Notebook`, вставьте raw-URL ноутбука: `https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-10-1-agent-by-hand/notebook.ipynb`
2. `Add-ons -> Secrets`: создайте секрет `HF_TOKEN` с вашим токеном.
3. `Run All`.

### Вариант C — локально
```bash
pip install huggingface_hub
export HF_TOKEN=hf_...
jupyter lab notebook.ipynb
```

MiniMax (OpenAI-совместимый `api.minimax.io/v1`, модель `MiniMax-M3`, ключ в `.env`) — альтернатива: тот же `chat.completions.create(..., stop=[...])`, переключается сменой одной строки клиента.

## ДЗ — самопроверка
- [ ] Ноутбук прогнан; петля дошла до `Final Answer:` минимум за два шага (добавьте второй тул и вопрос, требующий двух действий).
- [ ] В трейсе видно: модель остановилась на стоп-токене, код позвал реальный тул, результат ушёл обратно как `Observation:`.

Полный разбор задания и критерии приёмки — в [лекции 10.1](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-1-agent-by-hand/).

## Подводные камни
- **Нет `HF_TOKEN` -> `401 Unauthorized`.** Токен всегда через Secrets (Colab/Kaggle) или `export`, никогда не хардкодьте в ячейке. Роль токена — `read`.
- **Модель не держит формат -> `json.loads` падает.** Если в выводе лишняя проза или сломанный JSON, парсер не вынет действие. Ужесточите системный промпт (жёстче проговорите формат `action`/`action_input`, «только один JSON-блок, ничего лишнего»). Это и есть мотивация фреймворка из лекции: ручной парсинг хрупкий.
- **Забыли `stop=["Observation:"]` -> галлюцинация.** Модель сама допишет `Observation:` с выдуманным результатом и поедет дальше по фантазии. Стоп-токен — сердце ручного цикла.

## Что дальше
Та же петля, но фреймворк делает её за вас одним методом — [Модуль 10.2: Первый агент на smolagents](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-2-first-agent/). Сравните: сколько кода ушло и что вы потеряли в контроле.
