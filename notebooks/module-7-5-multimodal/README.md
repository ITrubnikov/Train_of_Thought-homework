# Модуль 7.5 — Мультимодальность: vision и audio

Домашка к [Модулю 7.5: Мультимодальность](https://itrubnikov.github.io/Train_of_Thought/docs/modules/07-5-multimodal/).

Здесь вы соберёте **агента-бухгалтера**: он смотрит на PDF-чек (текстом или картинкой) и возвращает **структурированный JSON** с позициями и суммой — с валидацией `pydantic` и repair-повтором. Плюс увидите, что audio — это отдельный пайплайн: распознаёте речь **локально через `faster-whisper`** (без ключа) и скармливаете распознанный текст тому же агенту.

Главный принцип канона: картинка — **не новый API**, а ещё один `content part` в том же `messages`-вызове, который вы уже знаете из модуля 6.4.

## Что нужно сделать до начала
- **Нужен API-ключ MiniMax** (`MINIMAX_API_KEY`) для vision-вызовов. Без ключа vision-ячейки **мягко пропускаются** — `Run all` проходит целиком, а ASR и проверки инвариантов работают у всех.
- Ноутбук написан на **OpenAI-совместимом клиенте** MiniMax (`base_url=https://api.minimax.io/v1`, модель `MiniMax-M3` — у неё есть приём картинок через `image_url`; у MiniMax есть и другие vision-модели, напр. `MiniMax-VL-01`, но для домашки берём M3).
- Откройте `notebook.ipynb` в Colab (бейдж ниже) — зависимости ставятся первой ячейкой. GPU не нужен.
- Ключ: локально — скопируйте `.env.example` в `.env` и впишите ключ; в Colab/Kaggle — через Secrets (см. «Как запустить»).
- Скачивать картинки/чек **не нужно** — они генерируются прямо в ноутбуке. Из файлов рядом только `fixtures/voice.wav` (диктовка чека для ASR); в Colab/Kaggle он подтягивается из репо автоматически.

## Файлы в папке
| Файл | Зачем |
| --- | --- |
| `notebook.ipynb` | Рабочий ноутбук (`Run all` проходит целиком): картинка как content part, OCR глазами модели, PDF текстом vs рендером, чек → JSON с валидацией и repair, локальный ASR через Whisper. Активность — в финальной секции «Задачи». Каждая ячейка печатает результат. |
| `fixtures/voice.wav` | Короткая голосовая диктовка чека (RU, ~6 сек) для демо распознавания речи. |
| `.env.example` | Шаблон для ключа. Реальный `.env` не коммитим. |

## Что в ноутбуке (всё рабочее, `Run all` проходит целиком)
1. Ставите зависимости (`openai`, `pydantic`, `pymupdf`, `reportlab`, `faster-whisper`, …) и создаёте MiniMax-клиента; флаг `HAS_KEY` включает мягкий skip vision без ключа.
2. **Картинка как content part** — рисуете график (matplotlib) и просите модель описать тренд: текст + картинка в одном `content`, `detail="high"`, `thinking: disabled`.
3. **OCR глазами модели** — картинка с текстом (PIL) → «перепиши дословно».
4. **PDF: текст vs картинка** — генерируете чек (reportlab), проходите оба пути одним `pymupdf`: `get_text()` (дёшево) и рендер страницы в PNG (для сканов).
5. **Чек → JSON** — схема `Receipt`/`Item`, функция `extract_receipt` с build-twice/repair; печатает валидированный JSON.
6. **Проверка инвариантов** — `check_receipt`: сходится ли `sum(qty*price)` с `total` (ловит галлюцинацию цифры). Self-check работает без ключа.
7. **Audio** — `faster-whisper` распознаёт `voice.wav` локально (ключ не нужен), распознанный текст уходит в тот же агент.
8. **Задачи** в конце: меняете рабочий код (detail/токены, текст vs картинка, новое поле схемы, поймать галлюцинацию на размытом скане, своя диктовка) и записываете короткие выводы.

## Как запустить
### Вариант A — Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-7-5-multimodal/notebook.ipynb)

Нажмите бейдж. Добавьте ключ через `Secrets` (значок ключа слева, имя `MINIMAX_API_KEY`), затем `Runtime → Run all`. GPU не нужен. `voice.wav` подтянется из репо автоматически.

### Вариант B — Kaggle
1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → GitHub` и вставьте ссылку на `notebook.ipynb`:
   `https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-7-5-multimodal/notebook.ipynb`
3. Accelerator оставьте `None` (CPU достаточно).
4. Включите Internet (Settings → Internet on) — нужен для установки пакетов и загрузки `voice.wav`.
5. Добавьте ключ через `Add-ons → Secrets` (имя `MINIMAX_API_KEY`), затем `Run All`.

### Вариант C — локально
```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-7-5-multimodal
cp .env.example .env   # впишите свой MINIMAX_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install "openai>=1.40" python-dotenv pydantic pymupdf reportlab faster-whisper matplotlib pillow
jupyter lab notebook.ipynb
```

## ДЗ к модулю
Самопроверка — всё проверяется без преподавателя:
- [ ] Ноутбук прогнан целиком (`Run all`) — vision-вызовы, чек → JSON и локальный ASR отработали.
- [ ] Зафиксирован реальный JSON чека из прогона (а не из головы); проверка инвариантов подтвердила корректность `total`.
- [ ] Сделаны задачи-доработки (минимум 3 из 5) с короткими выводами.
- [ ] Ключ нигде не захардкожен — только `.env` / Colab Secrets.

## Подводные камни
- **«Run all падает на vision без ключа»** — не должно: vision-ячейки мягко пропускаются (`[skip] нет MINIMAX_API_KEY`). Если падает — проверьте, что ключ либо задан, либо отсутствует целиком (а не пустой битый).
- **MiniMax: через этот OpenAI-совместимый API картинки принимает `MiniMax-M3`.** Если подставить в `image_url` другое имя модели — получите ошибку (vision-веса вроде `MiniMax-VL-01` живут отдельно, не на этом эндпоинте).
- **`usage` у MiniMax — это `prompt_tokens` / `completion_tokens`** (OpenAI-формат), не `input_tokens`/`output_tokens` как у Anthropic.
- **Whisper качает модель один раз** (~70–150 МБ для `base`). На Kaggle включите Internet, иначе и пакеты, и модель не подтянутся.
- **Audio на вход модель не принимает.** Если хочется «скормить mp3 напрямую» — нет: сначала ASR (Whisper) в текст, потом обычный LLM-вызов.

## Что дальше
[Модуль 8. Что такое агент](https://itrubnikov.github.io/Train_of_Thought/docs/modules/08-what-is-agent/) — модель начинает не только смотреть, но и действовать; vision станет одним из её инструментов (computer use).

## Лицензия
MIT (см. `LICENSE` в корне репозитория).
