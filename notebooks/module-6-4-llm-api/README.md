# Модуль 6.4 — LLM API на практике (прямой SDK)

Домашка к [Модулю 6.4: LLM API на практике](https://itrubnikov.github.io/Train_of_Thought/docs/modules/06-4-llm-api/).

Здесь вы соберёте три маленькие утилиты на реальном API: **summarizer** (со streaming), **классификатор писем** (structured output) и **переводчик-редактор** (многоходовый диалог). На выходе — три работающие функции в вашем ноутбуке.

## Что нужно сделать до начала
- **Нужен API-ключ.** В отличие от прошлых модулей, здесь без ключа ничего не запустится — модуль весь про вызовы API.
- Ноутбук написан на **Anthropic SDK** (как лекция). Достаточно ключа Anthropic. Если у вас только OpenAI — адаптируйте утилиты по двойникам из лекции.
- Откройте `notebook.ipynb` в Colab (бейдж ниже) — зависимости ставятся первой ячейкой.
- Ключ: локально — скопируйте `.env.example` в `.env` и впишите ключ; в Colab/Kaggle — через Secrets (см. раздел «Как запустить»).

## Файлы в папке
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Рабочий ноутбук (`Run all` проходит целиком): summarizer (streaming), классификатор (structured output + наивная версия в `try/except` для сравнения), переводчик-редактор (многоходовый диалог). Активность — в финальной секции «Задачи». Каждая ячейка печатает результат. |
| `.env.example` | Шаблон для ключа. Реальный `.env` не коммитим. |

## Что в ноутбуке (всё рабочее, `Run all` проходит целиком)
1. Ставите `anthropic`, `openai`, `python-dotenv`, `pydantic` и создаёте клиента.
2. **summarizer.** `summarize(text)` через `client.messages.stream(...)`: токены потоком из `stream.text_stream`, возврат `final.content[0].text`, печать `usage`.
3. **классификатор писем.** Наивная версия `classify_naive` (через `json.loads`, обёрнута в `try/except`) — видно, устойчива ли; затем `classify` через `client.messages.parse(output_format=EmailLabel)` — гарантированная схема.
4. **переводчик-редактор.** Многоходовый диалог: перевод, затем правка по второй реплике; видно, что историю ведёте вы (stateless).
5. **Задачи** в конце: меняете рабочий код (свой текст, новое поле в схеме, убрать ведение истории, OpenAI-двойник) и записываете короткие выводы.

## Как запустить
### Вариант A — Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-6-4-llm-api/notebook.ipynb)

Нажмите бейдж. Добавьте ключ через `🔑 Secrets` (имя `ANTHROPIC_API_KEY`), затем `Runtime → Run all`. GPU не нужен. Первая ячейка подтянет ключ из Colab Secrets автоматически.

### Вариант B — Kaggle
1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → GitHub` и вставьте ссылку на `notebook.ipynb` из этого репозитория.
3. Accelerator оставьте `None` (CPU достаточно).
4. Добавьте ключ через `Add-ons → Secrets` (имя `ANTHROPIC_API_KEY`), затем `Run All`.

### Вариант C — локально
```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-6-4-llm-api
cp .env.example .env   # впишите свой ключ
python -m venv .venv && source .venv/bin/activate
pip install anthropic openai python-dotenv pydantic
jupyter lab notebook.ipynb
```

## ДЗ к модулю
Самопроверка — всё проверяется без преподавателя:
- [ ] Ноутбук прогнан целиком (`Run all`) — три утилиты отработали, вывод виден.
- [ ] Записан пример, где наивный `json.loads` сломался/соврал (обёртка из тройных backtick, лишний текст или выдуманная категория), а structured output — нет.
- [ ] Сделаны задачи-доработки (мин. 3 из 5) с короткими выводами.
- [ ] Ключ нигде не захардкожен — только `.env` / Secrets.

## Подводные камни
- **`max_tokens` у Anthropic обязателен.** Забыли — ошибка; поставили мало — ответ обрежется на середине, `stop_reason` станет `"max_tokens"`. Всегда проверяйте `stop_reason`.
- **Наивный `json.loads` ломается предсказуемо.** Модель оборачивает JSON в тройные backtick, дописывает «Вот ваш JSON:» или придумывает значение поля. Это не ваша ошибка — это и есть повод для structured output.
- **API stateless.** В переводчике модель «помнит» разговор только потому, что вы сами добавляете её ответ обратно в `messages`. Уберите эту строку (задача 4) — и второй вызов не будет знать, что переводилось.
- **streaming не ускоряет генерацию.** Он лишь показывает токены по мере готовности. Если ждёте «быстрее» — не дождётесь; выигрыш только в отзывчивости (time to first token).
- **Не коммитьте `.env`.** В репозитории только `.env.example`. Реальный ключ — в `.env` (он в `.gitignore`) или в Colab/Kaggle Secrets. Утёкший ключ = чужие запросы за ваш счёт.
