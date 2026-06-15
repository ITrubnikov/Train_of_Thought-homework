# Модуль 6.5 — Prompt engineering как ремесло

Домашка к [Модулю 6.5: Prompt engineering как ремесло](https://itrubnikov.github.io/Train_of_Thought/docs/modules/06-5-prompt-engineering/).

Здесь вы соберёте **библиотеку из пяти переиспользуемых prompt-шаблонов** на реальном API: **extractor** (structured output), **classifier** (few-shot + enum), **reasoner** (chain-of-thought), **summarizer** (роль + формат) и **safe-answerer** (delimit-and-trust против инъекций). Плюс сквозное демо **prompt caching**. На выходе — пять работающих функций в вашем ноутбуке, которые можно носить из проекта в проект.

## Два пути — выберите по тому, какой ключ у вас есть
- **`notebook.ipynb`** — канон на **Anthropic SDK** (как лекция). Полное покрытие, включая structured output и демо prompt caching. Нужен платный ключ Anthropic.
- **`notebook-hf.ipynb`** — **бесплатная альтернатива** на открытой модели через Hugging Face Inference. Нужен только бесплатный HF-токен. Роли/few-shot/CoT/инъекции переносятся один-в-один; structured output показан честным путём «JSON → валидация → репромпт» (у открытых моделей он не гарантирован провайдером), а prompt caching — фича провайдера, его разбирает основной ноутбук. Берите этот путь, если нет ключа Anthropic.

Хотите кликать приёмы в браузере без кода — рядом есть интерактивная **HF Space-заготовка** [`spaces/module-6-5-prompt-lab`](https://github.com/ITrubnikov/Train_of_Thought-homework/tree/main/spaces/module-6-5-prompt-lab): Gradio-чат с редактируемым system-промптом, пресетами приёмов и вкладкой structured output. Разворачивается через Duplicate Space + секрет `HF_TOKEN`.

## Что нужно сделать до начала
- **Нужен API-ключ Anthropic.** Без ключа ничего не запустится — модуль весь про вызовы API.
- Ноутбук написан на **Anthropic SDK** (как лекция). Если у вас только OpenAI — адаптируйте шаблоны по двойникам из лекции 6.4.
- Откройте `notebook.ipynb` в Colab (бейдж ниже) — зависимости ставятся первой ячейкой.
- Ключ: локально — скопируйте `.env.example` в `.env` и впишите ключ; в Colab/Kaggle — через Secrets (см. раздел «Как запустить»).

## Файлы в папке
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Рабочий ноутбук на Anthropic SDK (`Run all` проходит целиком): пять prompt-шаблонов + демо prompt caching. Активность — в финальной секции «Задачи». Каждая ячейка печатает результат. |
| `notebook-hf.ipynb` | Бесплатная альтернатива на открытой модели через HF Inference (`Run all` проходит на бесплатном HF-токене): те же приёмы, structured output через «JSON + валидация + репромпт». |
| `.env.example` | Шаблон для ключа. Реальный `.env` не коммитим. |

## Что в ноутбуке (всё рабочее, `Run all` проходит целиком)
1. Ставите `anthropic`, `openai`, `python-dotenv`, `pydantic` и создаёте клиента.
2. **extractor** — `messages.parse` + Pydantic-схема с `Literal`-полями; границу `score` (0..100) проверяете `assert`-ом, потому что схема её не ловит.
3. **classifier** — few-shot из двух примеров задаёт грань; ответ одним словом из фиксированного набора.
4. **reasoner** — chain-of-thought: рассуждение по шагам, затем итог отдельной строкой.
5. **summarizer** — роль и формат живут в `system`; формат меняется без правки `user`-данных.
6. **safe-answerer** — delimit-and-trust: ответ строго по тексту между `<doc>`; в документ подложена инъекция, шаблон её не исполняет.
7. **prompt caching** — большой стабильный `system` с `cache_control`; на втором запросе видно `cache_read_input_tokens > 0`.
8. **Задачи** в конце: меняете рабочий код (поле в схеме, убрать few-shot, выключить CoT, сменить формат, усилить инъекцию, сломать кэш) и записываете короткие выводы.

## Как запустить
### Вариант A — Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-6-5-prompt-engineering/notebook.ipynb)

Нажмите бейдж. Добавьте ключ через `Secrets` (имя `ANTHROPIC_API_KEY`), затем `Runtime → Run all`. GPU не нужен. Первая ячейка подтянет ключ из Colab Secrets автоматически.

**Бесплатный путь без ключа Anthropic** (открытая модель через HF):

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-6-5-prompt-engineering/notebook-hf.ipynb)

Тот же бейдж, но для `notebook-hf.ipynb`. Добавьте бесплатный HF-токен через `Secrets` (имя `HF_TOKEN`), затем `Run all`. Токен заводится на huggingface.co → Settings → Access Tokens.

### Вариант B — Kaggle
1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → GitHub` и вставьте ссылку на `notebook.ipynb` из этого репозитория.
3. Accelerator оставьте `None` (CPU достаточно).
4. Добавьте ключ через `Add-ons → Secrets` (имя `ANTHROPIC_API_KEY`), затем `Run All`.

### Вариант C — локально
```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-6-5-prompt-engineering
cp .env.example .env   # впишите свой ключ
python -m venv .venv && source .venv/bin/activate
pip install anthropic openai python-dotenv pydantic
jupyter lab notebook.ipynb
```

## ДЗ к модулю
Самопроверка — всё проверяется без преподавателя:
- [ ] Ноутбук прогнан целиком (`Run all`) — пять шаблонов и демо кэша отработали.
- [ ] Записан пример, где few-shot или CoT меняет исход.
- [ ] Записан пример, где delimit-and-trust не дал сработать инъекции.
- [ ] Показано попадание в кэш (`cache_read_input_tokens > 0`) на втором запросе.
- [ ] Сделаны задачи-доработки (мин. 4 из 6) с короткими выводами.
- [ ] Ключ нигде не захардкожен — только `.env` / Secrets.

## Подводные камни
- **Структуру гарантирует схема, границы — нет.** `Literal`/enum не дадут придумать значение вне списка, но числовой диапазон (`score` 0..100) схема не навяжет — проверяйте сами после парсинга.
- **few-shot не бесплатен.** Каждый пример — токены в каждом запросе. Пять похожих хуже одного точного; примеры одного класса заставят модель думать, что других не бывает.
- **CoT нужен не везде.** На простой классификации рассуждение жжёт токены, замедляет ответ и ломает строгий формат. Включайте там, где есть что рассуждать.
- **Тихие ломатели кэша.** `datetime.now()`, несортированный JSON, UUID, переменный набор инструментов в начале промпта меняют байты префикса — и кэш каждый раз пишется заново. Проверяйте `cache_read_input_tokens`. Слишком короткий префикс (порядка нескольких тысяч токенов, порог зависит от модели) тоже молча не кэшируется.
- **Внешний текст — данные, не команды.** delimit-and-trust резко снижает наивные инъекции, но это первый рубеж, а не полная защита (см. модуль 9.5).
- **Не коммитьте `.env`.** В репозитории только `.env.example`. Реальный ключ — в `.env` (он в `.gitignore`) или в Colab/Kaggle Secrets. Утёкший ключ = чужие запросы за ваш счёт.
