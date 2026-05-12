# Модуль 1.5 — Где живёт современный ИИ

Заготовки к [Модулю 1.5: Где живёт современный ИИ](https://itrubnikov.github.io/Train_of_Thought/docs/modules/01-5-modern-tools/).

Это первый «технический» модуль курса. Цель — за один присест
завести Kaggle / Hugging Face / Google AI Studio и потрогать каждый
из них руками. К концу модуля у вас должна быть настроенная среда
для всех следующих ДЗ.

## Что нужно сделать до начала

1. **Аккаунт Kaggle** с пройденным phone verify ([kaggle.com/settings](https://www.kaggle.com/settings)).
2. **API-ключ Gemini** из [aistudio.google.com](https://aistudio.google.com/) → положить в Kaggle Secrets как `GOOGLE_API_KEY`.
3. **Read-токен Hugging Face** (опционально, но полезно) → положить как `HF_TOKEN`.

Подробности — в [`kaggle-tour.ipynb`](kaggle-tour.ipynb) (пошагово).

## Файлы в папке

### Демо для лекции

| Файл | Зачем |
| --- | --- |
| [`presenter-demo.ipynb`](presenter-demo.ipynb) | **Главный файл модуля.** Плотный ноутбук на 7—10 минут, который лектор показывает с экрана. После каждой кодовой ячейки идёт разбор «что произошло, что значит вывод, что попробовать поменять». Все три площадки + бонус по function calling. Импортируйте этот файл в Kaggle, чтобы повторить демо у себя. |

### Подробные туры по площадкам

| Файл | Зачем |
| --- | --- |
| [`kaggle-tour.ipynb`](kaggle-tour.ipynb) | Пошаговая экскурсия по Kaggle: phone verify, GPU, Secrets, публикация. ~25 мин. |
| [`huggingface-tour.ipynb`](huggingface-tour.ipynb) | Пошаговая экскурсия по Hugging Face: Hub, model card, `pipeline`, `load_dataset`, Spaces. ~20 мин. |

### Практика — одна задача на площадку

После демо студенты делают три отдельные мини-задачи, по одной на
каждую площадку. Все три — стартовые ноутбуки с TODO-блоками.

| Файл | Что делает студент | Время |
| --- | --- | --- |
| [`practice-kaggle.ipynb`](practice-kaggle.ipynb) | Подключает публичный датасет, гоняет pandas, считает метрику, строит график | ~10 мин |
| [`practice-huggingface.ipynb`](practice-huggingface.ipynb) | `pipeline("sentiment-analysis")` × `load_dataset("imdb")`, accuracy на 50 примерах, разбор ошибок | ~10 мин |
| [`practice-aistudio.ipynb`](practice-aistudio.ipynb) | Sentiment через Gemini API, structured output (enum), эксперимент с температурой | ~10 мин |
| [`spaces-practice.md`](spaces-practice.md) | Web-workflow (не ноутбук): дублируете готовый Space `agents-course/First_agent_template`, добавляете свой tool, получаете публичный URL агента | ~15—20 мин |

### Опциональный deep-dive

| Файл | Зачем |
| --- | --- |
| [`day-1-prompting.ipynb`](day-1-prompting.ipynb) | Адаптация Day 1 из [Kaggle 5-Day GenAI Intensive](https://www.kaggle.com/learn-guide/5-day-genai). Идёт глубже базовой практики: zero/few-shot, CoT, ReAct, code execution в одном ноутбуке. Только если успели три основные практики и хочется ещё. |

## Как использовать (workflow)

1. **Fork** этот репозиторий.
2. В Kaggle: **Create → New Notebook → File → Import Notebook** →
   вкладка `File` → перетащите нужный `.ipynb` из своего форка.
3. Прикрепите `GOOGLE_API_KEY` через **Add-ons → Secrets**.
4. Прогоните сверху вниз.
5. **Save Version → Save & Run All (Commit) → Share → Public**.
6. Ссылку в чат курса.

## Технические заметки

- Все ячейки с HF-моделями принудительно используют **CPU** (`device=-1` /
  `device="cpu"`). Это потому, что Kaggle иногда выдаёт **Tesla P100**
  (CUDA capability sm_60), несовместимую со свежим PyTorch. Маленькие
  модели на CPU работают быстро, GPU им не нужен.
- Регенерация `.ipynb`-файлов — через [`_build.py`](_build.py). Правьте
  только Python-код, потом запускайте `python3 _build.py` и коммитьте
  результат.
