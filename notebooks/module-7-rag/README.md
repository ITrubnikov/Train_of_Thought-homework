# Модуль 7 — RAG, который работает

Заготовки к [Модулю 7: RAG, который работает](https://itrubnikov.github.io/Train_of_Thought/docs/modules/07-rag/).

RAG (Retrieval-Augmented Generation) — это «модель + база знаний».
Перед тем как ответить на вопрос, система ищет релевантные куски в
вашей базе документов и **дополняет** ими промпт. Так LLM перестаёт
отвечать «по памяти» и начинает работать на ваших актуальных данных,
да ещё и со ссылкой на источник.

В папке два ноутбука: сначала разминка про эмбеддинги (главный кубик
RAG), потом полный рабочий пайплайн.

## Что нужно сделать до начала

- Для разминки (`day-2-embeddings.ipynb`) — Kaggle/Colab и прикреплённый
  `GOOGLE_API_KEY` (см. [Модуль 1.5](../module-1-5-modern-tools/)).
- Для основного ноутбука (`notebook.ipynb`) ключ **не нужен** для retrieval-части:
  весь поиск (chunk → embed → store → hybrid → rerank) идёт локально на CPU. Ключ
  `MINIMAX_API_KEY` (берётся на [platform.minimax.io](https://platform.minimax.io/))
  нужен только последнему шагу — генерации ответа через MiniMax; без него
  этот шаг аккуратно пропускается, и `Run all` всё равно проходит.

Ноутбук запускается и **локально** (своя машина), и в Colab/Kaggle — см. «Как запустить».

## Файлы в папке

| Файл | Зачем |
| --- | --- |
| [`day-2-embeddings.ipynb`](day-2-embeddings.ipynb) | **Разминка (ДЗ 0).** Адаптация Day 2 из [Kaggle 5-Day GenAI Intensive](https://www.kaggle.com/learn-guide/5-day-genai). Эмбеддинги через `text-embedding-004` (Gemini), cosine similarity, тепловая карта похожести. Показывает «геометрию слов», на которой стоит весь RAG. |
| [`notebook.ipynb`](notebook.ipynb) | **Полный RAG-пайплайн (ДЗ 1).** Маленькая FAQ-база поддержки → naive cosine-поиск (numpy) → Chroma (персистентность + метаданные) → hybrid (BM25 + dense через RRF) → reranking (cross-encoder) → генерация ответа через MiniMax со ссылкой на источник и анти-галлюцинацией. Retrieval работает без ключа; генерация — опционально. Активность — в финальной секции «Задачи». |

## Что вы делаете в ноутбуке `notebook.ipynb`

1. Заводите базу знаний: `id + текст чанка + метаданные` (source, topic).
2. Считаете эмбеддинги и делаете наивный cosine-поиск на numpy — baseline из лекции.
3. Перекладываете то же хранилище в Chroma и получаете персистентность,
   метаданные и фильтры по `where`.
4. Добавляете BM25 и сливаете с dense через **Reciprocal Rank Fusion** —
   видите запрос (`ошибка E-451`, артикул `SKU-90210`), где чисто
   векторный поиск мажет, а hybrid вытягивает нужный чанк наверх.
5. Прогоняете top-N кандидатов через cross-encoder (**reranking**) и
   видите, как меняется порядок.
6. Собираете контекст в промпт и просите модель (MiniMax) ответить только
   по нему, сославшись на источник; на вопрос вне базы бот честно говорит «не знаю».
7. Бонус: мини-eval retrieval (`recall@3`) без внешних зависимостей —
   мостик к [Модулю 9. Evals](https://itrubnikov.github.io/Train_of_Thought/docs/modules/09-evals/).

## Как запустить `notebook.ipynb`

### Вариант A — локально (рекомендуется)

```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-7-rag

python3 -m venv .venv && source .venv/bin/activate     # отдельное окружение
pip install sentence-transformers chromadb rank-bm25 openai python-dotenv numpy jupyterlab

# ключ нужен только для генерации; retrieval работает и без него:
echo "MINIMAX_API_KEY=ваш-ключ" > .env                  # ключ — на platform.minimax.io
# (или: export MINIMAX_API_KEY=ваш-ключ)

jupyter lab notebook.ipynb                               # затем Run all
```

Первый запуск качает модели эмбеддингов и reranker (несколько сотен мегабайт),
дальше всё из кэша. GPU не нужен. Без ключа ноутбук пройдёт целиком — пропустит
только шаг генерации. `.env` лежит локально и в git не коммитится.

### Вариант B — Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-7-rag/notebook.ipynb)

Нажмите бейдж, затем `Runtime → Run all`. GPU не нужен. Первая ячейка
ставит зависимости и качает модели. Для шага генерации добавьте ключ
через `Secrets` (значок ключа слева, имя `MINIMAX_API_KEY`) — без него
ноутбук всё равно пройдёт целиком.

### Вариант C — Kaggle
1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → GitHub` и вставьте ссылку на `notebook.ipynb` из этого репозитория.
3. Accelerator оставьте `None` (CPU достаточно).
4. (Опционально) добавьте ключ через `Add-ons → Secrets` (имя `MINIMAX_API_KEY`), затем `Run All`.

## ДЗ к модулю

Полное ДЗ описано в [самой лекции](https://itrubnikov.github.io/Train_of_Thought/docs/modules/07-rag/).

**ДЗ 0 (разминка).** Откройте `day-2-embeddings.ipynb`, замените дефолтные
8 фраз на свои, постройте heatmap, распечатайте топ-3 ближайших соседа и
запишите одно наблюдение про эмбеддинги. Прислать как `[Модуль 7, ДЗ 0] {ссылка}`.

**ДЗ 1 (основное).** В `notebook.ipynb`:
- замените `KB` на свои 15-30 коротких чанков из реальных текстов (не демо про доставку);
- найдите и запишите запрос, где dense-поиск мажет, а hybrid вытягивает нужный чанк;
- сделайте так, чтобы `answer(...)` ссылался на источник (`[source: ...]`) и в чанках были метаданные;
- задайте вопрос вне базы и убедитесь, что бот отвечает «не знаю», а не сочиняет.

Артефакт — публичная ссылка на прогнанный ноутбук (или скриншоты локального
прогона), в чат курса как `[Модуль 7, ДЗ 1] {ссылка}`.

## Подводные камни

- **Первый запуск долгий.** Качаются веса embedding-модели и cross-encoder
  (несколько сотен мегабайт). Дальше всё из кэша.
- **Чисто векторный поиск мажет на точных токенах** — коды, артикулы, имена.
  Это не баг, а повод для hybrid: BM25 берёт дословный матч, dense — смысл.
- **Reranker медленный** — его не пускают на всю базу. Схема: hybrid достаёт
  широкий top-N дёшево, cross-encoder сужает до точного top-k.
- **MiniMax-M3 — reasoning-модель.** Она «думает» перед ответом; ноутбук
  убирает блоки `<think>...</think>` и оставляет только ответ. Для скорости
  можно поставить `MODEL = "MiniMax-M2.7-highspeed"`.
- **Без ключа генерация пропускается, а не падает.** Это сделано специально,
  чтобы `Run all` всегда проходил. Ответы модели увидите, добавив `MINIMAX_API_KEY`.
- **Не коммитьте ключ.** Только `.env` (локально) / Secrets / userdata. Утёкший
  ключ — чужие запросы за ваш счёт.
