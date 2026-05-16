# Модуль 1.5 — Где живёт современный ИИ

Материалы к [Модулю 1.5: Где живёт современный ИИ](https://itrubnikov.github.io/Train_of_Thought/docs/modules/01-5-modern-tools/).

Цель модуля — за один присест завести Kaggle / Hugging Face / Google AI
Studio и потрогать каждый из них руками. К концу модуля у вас должна
быть настроенная среда для всех следующих ДЗ.

## Структура папки

```
lesson/      ← что лектор показывает на занятии (можно подсматривать)
homework/    ← что вы делаете сами, чтобы сдать модуль
```

### lesson/

| Файл | Зачем |
| --- | --- |
| [`lesson/presenter-demo.ipynb`](lesson/presenter-demo.ipynb) | Демо, которое лектор крутит с экрана: все три площадки + бонус по function calling. После каждой ячейки — разбор «что произошло, что значит вывод». Публичная копия на Kaggle: [kaggle.com/code/hohusss/module-1-5-demo](https://www.kaggle.com/code/hohusss/module-1-5-demo). |

### homework/

Три коротких задачи, по одной на площадку. Каждая — ~10 минут.

| Файл | Что делает студент |
| --- | --- |
| [`homework/practice-kaggle.ipynb`](homework/practice-kaggle.ipynb) | Подключает публичный датасет, гоняет pandas, считает метрику, строит график. |
| [`homework/practice-huggingface.ipynb`](homework/practice-huggingface.ipynb) | `pipeline("sentiment-analysis")` × `load_dataset("imdb")`, accuracy на 50 примерах, разбор ошибок. |
| [`homework/practice-aistudio.ipynb`](homework/practice-aistudio.ipynb) | Sentiment через Gemini API, structured output (enum), эксперимент с температурой. |
| [`homework/spaces-practice.md`](homework/spaces-practice.md) | Опционально и эффектно: дублируете готовый Space `agents-course/First_agent_template`, добавляете свой tool, получаете публичный URL агента. ~15—20 мин. |

## Что нужно сделать до начала

1. **Аккаунт Kaggle** с пройденным phone verify ([kaggle.com/settings](https://www.kaggle.com/settings)).
2. **API-ключ Gemini** из [aistudio.google.com](https://aistudio.google.com/) → положить в Kaggle Secrets как `GOOGLE_API_KEY`.
3. **Read-токен Hugging Face** (опционально) → положить как `HF_TOKEN`.

Пошаговая инструкция по этим трём пунктам — в [`lesson/presenter-demo.ipynb`](lesson/presenter-demo.ipynb).

## Workflow для homework

1. **Fork** этот репозиторий.
2. В Kaggle: **Create → New Notebook → File → Import Notebook** →
   перетащите нужный `.ipynb` из своего форка `homework/`.
3. Прикрепите `GOOGLE_API_KEY` через **Add-ons → Secrets**.
4. Прогоните сверху вниз, заполните все `TODO:` ячейки.
5. **Save Version → Save & Run All (Commit) → Share → Public**.
6. Ссылку — в чат курса.

## Технические заметки

- Ячейки с HF-моделями принудительно используют **CPU** (`device=-1` /
  `device="cpu"`). Kaggle иногда выдаёт **Tesla P100** (CUDA capability
  sm_60), несовместимую со свежим PyTorch. Маленькие модели на CPU
  работают быстро, GPU им не нужен.
- Регенерация `.ipynb`-файлов — через [`_build.py`](_build.py). Правьте
  только Python-код, потом `python3 _build.py` и коммитьте результат.
