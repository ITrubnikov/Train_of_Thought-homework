# Модуль 6.7 — Стоимость, латентность, маршрутизация моделей

Домашка к [Модулю 6.7: Стоимость, латентность, маршрутизация моделей](https://itrubnikov.github.io/Train_of_Thought/docs/modules/06-7-cost-latency/).

Здесь вы соберёте **калькулятор стоимости вызова по usage-токенам** (input / output / cache, цены из словаря `PRICES`) + **замер латентности** (TTFT и tokens/sec через стриминг) + **роутер `small→big`** с escalate-on-uncertainty и fallback на ошибки. На выходе — несколько работающих функций в ноутбуке, которые считают **реальную** цену и скорость из `response.usage`, а не из головы.

Главный принцип канона: **числа — из прогона кода, а не выдуманные.** Калькулятор включает pure-python self-check (`assert` на известных токенах), который проходит даже без ключа.

## Что нужно сделать до начала
- **Нужен API-ключ Anthropic.** Без ключа реальные замеры не запустятся — модуль про вызовы API (self-check формулы стоимости работает и без ключа).
- Ноутбук написан на **Anthropic SDK** (как лекция). Если у вас только OpenAI — адаптируйте по двойникам из лекции 6.4 (флагман `gpt-5.5`, дешёвый `gpt-5.4-mini`); точные цены сверяйте с прайсингом OpenAI.
- Откройте `notebook.ipynb` в Colab (бейдж ниже) — зависимости ставятся первой ячейкой.
- Ключ: локально — скопируйте `.env.example` в `.env` и впишите ключ; в Colab/Kaggle — через Secrets (см. «Как запустить»).

## Файлы в папке
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Рабочий ноутбук на Anthropic SDK (`Run all` проходит целиком): калькулятор стоимости из `usage` + self-check, два счёта (Haiku vs Opus), `count_tokens`, замер TTFT/throughput, prompt caching, роутер `small→big`, fallback/batch. Активность — в финальной секции «Задачи». Каждая ячейка печатает результат. |
| `.env.example` | Шаблон для ключа. Реальный `.env` не коммитим. |

## Что в ноутбуке (всё рабочее, `Run all` проходит целиком)
1. Ставите `anthropic`, `openai`, `python-dotenv`, `pydantic` и создаёте клиента (`MODEL` = Haiku, `FLAGSHIP` = Opus).
2. **Калькулятор стоимости** — словарь `PRICES` ($/Mtok) + функция `cost()` по `input` / `cache_read` (×0.1) / `cache_creation` (×1.25) / `output`. Плюс **self-check** с `assert`-ами (работает без ключа).
3. **Один классификатор писем** — печатает ярлык, `usage` и реальную цену одного вызова.
4. **Два счёта** — тот же промпт на Haiku и Opus по набору писем; суммарная цена и где ярлыки разошлись.
5. **count_tokens** — оценка входа ДО запуска на той же модели (не tiktoken — он врёт на Claude).
6. **Латентность** — TTFT и tokens/sec через `client.messages.stream` + `time.perf_counter()`.
7. **Prompt caching** — стабильный system-префикс; на 2-м запросе `cache_read_input_tokens > 0`, считаем экономию.
8. **Роутер small→big** — Haiku с уверенностью через structured output; неуверенные → Opus; цена роутера vs «всё на Opus».
9. **Fallback + Batch** — try/except с фолбэком модели при ошибке; скелет batch-запроса (−50%).
10. **(опц.) MiniMax** — дешёвый сторонний провайдер через OpenAI-совместимый клиент (`base_url` + `model` + ключ); сравнение цены `MiniMax-M2.5` ($0.15/$0.90 за Mtok) с Haiku/Opus. Нужен отдельный `MINIMAX_API_KEY`; без него блок мягко пропускается — `Run all` не ломается.
11. **Задачи** в конце: меняете рабочий код (длинный CoT, ломаете кэш, двигаете порог роутера, добавляете третью модель, встраиваете MiniMax как самый дешёвый tier) и записываете короткие выводы.

## Как запустить
### Вариант A — Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-6-7-cost-latency/notebook.ipynb)

Нажмите бейдж. Добавьте ключ через `Secrets` (имя `ANTHROPIC_API_KEY`), затем `Runtime → Run all`. GPU не нужен. Первая ячейка подтянет ключ из Colab Secrets автоматически.

### Вариант B — Kaggle
1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → GitHub` и вставьте ссылку на `notebook.ipynb`:
   `https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-6-7-cost-latency/notebook.ipynb`
3. Accelerator оставьте `None` (CPU достаточно).
4. Добавьте ключ через `Add-ons → Secrets` (имя `ANTHROPIC_API_KEY`), затем `Run All`.

### Вариант C — локально
```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-6-7-cost-latency
cp .env.example .env   # впишите свой ключ
python -m venv .venv && source .venv/bin/activate
pip install anthropic openai python-dotenv pydantic
jupyter lab notebook.ipynb
```

## ДЗ к модулю
Самопроверка — всё проверяется без преподавателя:
- [ ] Ноутбук прогнан целиком (`Run all`) — калькулятор, замер латентности и роутер отработали.
- [ ] Зафиксирован числовой результат прогона: реальная цена из `usage` (суммарная Haiku vs Opus, экономия роутера).
- [ ] Self-check формулы стоимости прошёл (`assert`-ы, работает без ключа).
- [ ] Сделаны задачи-доработки (мин. 4 из 6) с короткими выводами.
- [ ] Ключ нигде не захардкожен — только `.env` / Secrets.

## Подводные камни
- **Числа — из usage, не из головы.** Цены $/Mtok берём из `PRICES` (значения из лекции, сверяйтесь с прайсингом Anthropic), а токены — из реального `resp.usage`. Цифры в выводах ячеек — результат прогона.
- **Output дороже input в ~5×.** На Opus $25 vs $5 за Mtok. Длинный CoT-вывод — главный пожиратель счёта; режьте лишнюю генерацию там, где она не нужна.
- **Не tiktoken для Claude.** Чужой OpenAI-токенайзер занижает Claude-токены на ~15–20% (на коде/не-английском больше). Считайте через `client.messages.count_tokens` на той же модели.
- **Кэш проверяйте по `cache_read_input_tokens`.** `datetime.now()`, uuid, несортированный `json.dumps` в начале префикса молча ломают кэш — и вы платите полную цену. Минимальная длина префикса зависит от модели (порядка нескольких тысяч токенов) — проверяйте эмпирически.
- **effort не на всех моделях.** Haiku 4.5 параметр `effort` не поддерживает (ошибка); `max`/`xhigh` — только Opus-tier и Sonnet 4.6.
- **Стриминг для длинного вывода.** Вывод > 16K токенов стримьте обязательно (Opus до 128K только в стриме), иначе HTTP-таймаут SDK или обрезка по `max_tokens`.
- **Ретрай уже есть в SDK.** SDK сам ретраит 408/409/429/5xx с backoff (`max_retries=2`). Кастомный цикл нужен только за пределами этого; на 529 разумнее фолбэк на менее загруженную Haiku, чем тупой повтор.
- **Не коммитьте `.env`.** В репозитории только `.env.example`. Реальный ключ — в `.env` (он в `.gitignore`) или в Colab/Kaggle Secrets. Утёкший ключ = чужие запросы за ваш счёт.