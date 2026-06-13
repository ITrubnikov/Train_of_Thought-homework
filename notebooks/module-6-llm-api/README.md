# Модуль 6 — LLM API на практике

Домашка к [Модулю 6: LLM API на практике](https://itrubnikov.github.io/Train_of_Thought/docs/modules/06-llm-api/).

Здесь вы соберёте три маленькие утилиты на реальном API: **summarizer** (со streaming), **классификатор писем** (structured output) и **переводчик-редактор** (многоходовый диалог). На выходе — три работающие функции в вашем ноутбуке.

## Что нужно сделать до начала
- **Нужен API-ключ.** В отличие от прошлых модулей, здесь без ключа ничего не запустится — модуль весь про вызовы API.
- Ноутбук написан на **Anthropic SDK** (как лекция). Достаточно ключа Anthropic. Если у вас только OpenAI — адаптируйте утилиты по двойникам из лекции.
- Откройте `notebook.ipynb` в Colab (бейдж ниже) — зависимости ставятся первой ячейкой.
- Ключ: локально — скопируйте `.env.example` в `.env` и впишите ключ; в Colab/Kaggle — через Secrets (см. раздел «Как запустить»).

## Файлы в папке
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Скелет с 3 `TODO`. На выходе: summarizer со streaming, классификатор писем на structured output (плюс «сломанная» наивная версия для сравнения) и переводчик-редактор на многоходовом диалоге. Каждая ячейка что-то печатает или явно падает с подсказкой. |
| `.env.example` | Шаблон для ключа. Реальный `.env` не коммитим. |

## Что вы делаете в ноутбуке
1. Ставите `anthropic`, `openai`, `python-dotenv`, `pydantic` и создаёте клиента.
2. **TODO 1. summarizer.** Реализуете `summarize(text)` через `client.messages.stream(...)`: печатаете токены потоком из `stream.text_stream`, возвращаете `final.content[0].text`, печатаете `usage`.
3. **TODO 2. классификатор писем.** Сначала запускаете наивную версию `classify_naive` (через `json.loads`) и ловите, где она ломается. Потом реализуете `classify` через `client.messages.parse(output_format=EmailLabel)` — и получаете гарантированную схему.
4. **TODO 3. переводчик-редактор.** Многоходовый диалог: перевести фразу, затем по второй реплике («сделай официальнее») получить правку. Убеждаетесь, что без добавления ответа в `messages` модель теряет контекст.
5. В последней markdown-ячейке записываете вывод одной фразой: что удивило больше всего.

## Как запустить
### Вариант A — Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-6-llm-api/notebook.ipynb)

Нажмите бейдж. Добавьте ключ через `🔑 Secrets` (имя `ANTHROPIC_API_KEY`), затем `Runtime → Run all`. GPU не нужен. Первая ячейка подтянет ключ из Colab Secrets автоматически.

### Вариант B — Kaggle
1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → GitHub` и вставьте ссылку на `notebook.ipynb` из этого репозитория.
3. Accelerator оставьте `None` (CPU достаточно).
4. Добавьте ключ через `Add-ons → Secrets` (имя `ANTHROPIC_API_KEY`), затем `Run All`.

### Вариант C — локально
```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-6-llm-api
cp .env.example .env   # впишите свой ключ
python -m venv .venv && source .venv/bin/activate
pip install anthropic openai python-dotenv pydantic
jupyter lab notebook.ipynb
```

## ДЗ к модулю
Самопроверка — всё проверяется без преподавателя:
- [ ] **TODO 1:** `summarize` выдаёт ответ потоком (текст появляется по мере генерации), возвращает строку и печатает `usage`.
- [ ] **TODO 2:** запущена наивная версия и записан пример, где `json.loads` сломался (обёртка из тройных backtick, лишний текст или выдуманная категория); рабочая версия `classify` возвращает провалидированный `EmailLabel`.
- [ ] **TODO 3:** переводчик-редактор корректно правит перевод во второй реплике; показано, что без ведения истории модель теряет контекст.
- [ ] Ключ нигде не захардкожен — только `.env` / Secrets.
- [ ] В последней markdown-ячейке одной фразой записан вывод: что удивило больше всего.

## Подводные камни
- **`max_tokens` у Anthropic обязателен.** Забыли — ошибка; поставили мало — ответ обрежется на середине, `stop_reason` станет `"max_tokens"`. Всегда проверяйте `stop_reason`.
- **Наивный `json.loads` ломается предсказуемо.** Модель оборачивает JSON в тройные backtick, дописывает «Вот ваш JSON:» или придумывает значение поля. Это не ваша ошибка — это и есть повод для structured output.
- **API stateless.** В TODO 3 модель «помнит» разговор только потому, что вы сами добавляете её ответ обратно в `messages`. Уберите эту строку — и второй вызов не будет знать, что переводилось.
- **streaming не ускоряет генерацию.** Он лишь показывает токены по мере готовности. Если ждёте «быстрее» — не дождётесь; выигрыш только в отзывчивости (time to first token).
- **Не коммитьте `.env`.** В репозитории только `.env.example`. Реальный ключ — в `.env` (он в `.gitignore`) или в Colab/Kaggle Secrets. Утёкший ключ = чужие запросы за ваш счёт.
