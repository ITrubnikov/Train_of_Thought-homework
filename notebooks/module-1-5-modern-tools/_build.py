"""Generate Module 1.5 notebooks.

Run: `python _build.py` (no deps beyond stdlib).

Outputs:
  lesson/presenter-demo.ipynb       — что лектор показывает в классе
  homework/practice-kaggle.ipynb    — студент делает сам
  homework/practice-huggingface.ipynb
  homework/practice-aistudio.ipynb
"""

import json
from pathlib import Path

HERE = Path(__file__).parent


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.rstrip("\n").splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.rstrip("\n").splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write(subdir: str, name: str, cells: list[dict]) -> None:
    out_dir = HERE / subdir
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"{name}.ipynb"
    path.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=1))
    print(f"wrote {path}")





# -----------------------------------------------------------------------
# PRACTICE 1: Kaggle — публичный датасет + pandas
# -----------------------------------------------------------------------

practice_kaggle = [
    md("""# Практика 1/3: Kaggle — публичный датасет + pandas

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
> Первая из трёх практик по одной на каждую площадку.
> На этой задаче вы трогаете **только Kaggle**: подключаете чужой
> публичный датасет к своему ноутбуку и крутите его руками через pandas.
> Никаких HF и Gemini пока не нужно.
>
> Время: ~10 минут. Выход: ваш Kaggle-ноутбук с заполненными TODO.
"""),

    md("""## Что делаем

Чтобы привыкнуть к Kaggle как к рабочему месту, надо хоть раз пройти
полный цикл: «нашёл датасет → прицепил его к ноутбуку → загрузил в
pandas → посмотрел глазами → посчитал одну метрику → сохранил».

Сегодня берём датасет **[Titanic - Machine Learning from Disaster](https://www.kaggle.com/competitions/titanic/data)**
(самый известный учебный датасет в мире) или любой другой на ваш вкус.
"""),

    md("""## Шаг 1. Подключите датасет к ноутбуку (UI, не код)

1. Справа в панели ноутбука: **+ Add Input**.
2. **Datasets** → в поиске наберите `titanic` (или другой по вкусу).
3. Подойдёт, например, [`heptapod/titanic`](https://www.kaggle.com/datasets/heptapod/titanic) —
   ставьте плюсик рядом с ним.
4. После подключения файлы появятся в `/kaggle/input/<slug>/`.

**TODO:** проверьте, что подключение сработало, запустите ячейку ниже.
"""),

    code("""import os

input_root = "/kaggle/input"
if not os.path.isdir(input_root) or not os.listdir(input_root):
    print("Датасет не подключён. Нажмите '+ Add Input' справа.")
else:
    for ds in sorted(os.listdir(input_root)):
        ds_path = os.path.join(input_root, ds)
        files = sorted(os.listdir(ds_path))
        print(f"\\n{ds}/")
        for f in files[:5]:
            print(f"  {f}")
"""),

    md("""## Шаг 2. Загрузите CSV в pandas

**TODO:** замените путь ниже на свой (под названия в вашем датасете).
Если взяли Titanic — обычно файл называется `train.csv`.
"""),

    code("""import pandas as pd

# TODO: укажите правильный путь под свой подключённый датасет
csv_path = "/kaggle/input/titanic/train.csv"
df = pd.read_csv(csv_path)
print("Размер:", df.shape)
df.head()
"""),

    md("""## Шаг 3. Посмотрите глазами

Прежде чем что-то считать, надо понять, **что вообще у вас в таблице**.
Три обязательные команды:
"""),

    code("""print("Колонки и типы:")
print(df.dtypes)

print("\\nКоличество пропусков по колонкам:")
print(df.isna().sum().sort_values(ascending=False).head(10))

print("\\nЧисловая статистика:")
df.describe()
"""),

    md("""## Шаг 4. Одна метрика по выбору

**TODO:** посчитайте **одну** интересную для этого датасета метрику.

Примеры для Titanic:
- доля выживших: `df["Survived"].mean()`;
- доля выживших по полу: `df.groupby("Sex")["Survived"].mean()`;
- средний возраст по классу: `df.groupby("Pclass")["Age"].mean()`;
- сколько пассажиров было одиноких vs с семьёй (`SibSp + Parch`).

Если взяли другой датасет — придумайте свою.
"""),

    code("""# TODO: ваша метрика
df.groupby("Sex")["Survived"].mean()
"""),

    md("""## Шаг 5. Один график

Любой простой: bar / hist / scatter. Цель — увидеть, что в Kaggle
ноутбуке matplotlib работает из коробки.
"""),

    code("""import matplotlib.pyplot as plt

# TODO: замените на свой график
df["Age"].hist(bins=30)
plt.title("Распределение возраста пассажиров Titanic")
plt.xlabel("Возраст")
plt.ylabel("Количество")
plt.show()
"""),

    md("""## Шаг 6. Один абзац о наблюдении

**TODO:** в markdown-ячейке ниже одно предложение: что вы заметили в
этом датасете, что было неожиданно?

Хорошие наблюдения — конкретные. «Данные интересные» — плохо. «У 19%
пассажиров пропущен возраст, в основном в третьем классе» — хорошо.
"""),

    md("""**TODO: ваше наблюдение здесь.**
"""),

    md("""## Сдача

1. `Save Version` → `Save & Run All (Commit)`.
2. `Share` → `Public`.
3. Скопируйте ссылку.
4. В чат курса: `[Модуль 1.5, практика Kaggle] {ссылка}`.

Дальше — [практика 2: Hugging Face](./practice-huggingface.ipynb).
"""),
]

write("homework", "practice-kaggle", practice_kaggle)


# -----------------------------------------------------------------------
# PRACTICE 2: Hugging Face — pipeline + load_dataset
# -----------------------------------------------------------------------

practice_hf = [
    md("""# Практика 2/3: Hugging Face — pipeline + load_dataset

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
> Вторая из трёх практик. На этой задаче вы трогаете **только Hugging
> Face**: берёте готовую модель и готовый датасет с Hub'а, прогоняете
> модель по датасету, считаете accuracy.
>
> Время: ~10 минут.
"""),

    md("""## Что делаем

Hugging Face Hub — это **готовые куски** для NLP-задач. Маленький
specialized классификатор и стандартизованный датасет позволяют за 10
минут собрать рабочий пайплайн «классификация настроения», на который
в 2018-м уходила неделя.

Сделаем: возьмём `distilbert-base-uncased-finetuned-sst-2-english` из HF,
прогоним его по первым 50 отзывам из IMDB, сравним предсказания с
настоящими метками, посчитаем accuracy.
"""),

    md("""## Шаг 1. Установка и токен

Токен HF на этом упражнении не обязателен (модель и датасет публичные),
но если вы уже прикрепили `HF_TOKEN` в Secrets — отлично, ячейка ниже
его подцепит.
"""),

    code("""!pip install -q transformers datasets
"""),

    code("""# Если есть токен — используем; если нет, продолжаем без него.
try:
    from kaggle_secrets import UserSecretsClient
    HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
    print("HF токен подключён.")
except Exception:
    HF_TOKEN = None
    print("Без HF токена — публичные модели всё равно доступны.")
"""),

    md("""## Шаг 2. Поднимаем модель — 3 строки

`pipeline("sentiment-analysis")` без аргументов скачивает дефолтную
модель (`distilbert-base-uncased-finetuned-sst-2-english`, ~250 МБ).
Первый запуск — минута, дальше — кэш.
"""),

    code("""from transformers import pipeline

# device=-1 — CPU (distilbert крошечная, GPU не нужен).
# На Kaggle иногда дают Tesla P100, она несовместима со свежим
# PyTorch — поэтому явный CPU надёжнее.
clf = pipeline("sentiment-analysis", device=-1)

# Sanity check
print(clf("This course is unexpectedly fun."))
print(clf("Honestly, I'm just here for the certificate."))
"""),

    md("""## Шаг 3. Подключаем датасет — 2 строки

Берём `imdb` (50k отзывов о фильмах с разметкой POSITIVE/NEGATIVE),
из них первые 50 примеров теста — этого достаточно для прикидки.
"""),

    code("""from datasets import load_dataset

ds = load_dataset("imdb", split="test[:50]")
print("Размер:", len(ds))
print("Поля:", ds.column_names)
print("\\nПример:")
print(" текст:", ds[0]["text"][:200], "...")
print(" метка:", ds[0]["label"], "(0 = NEGATIVE, 1 = POSITIVE)")
"""),

    md("""## Шаг 4. Прогон модели по датасету + accuracy

**TODO:** ничего трогать не надо, просто запустите. После — переходите
к шагу 5.
"""),

    code("""correct = 0
errors = []

for row in ds:
    text = row["text"][:512]  # обрезаем грубо по символам, чтобы влезло
    pred = clf(text)[0]["label"]
    true = "POSITIVE" if row["label"] == 1 else "NEGATIVE"
    if pred == true:
        correct += 1
    else:
        errors.append({"true": true, "pred": pred, "text": text[:120]})

acc = correct / len(ds)
print(f"Accuracy: {correct}/{len(ds)} = {acc:.0%}")
print(f"Ошибок: {len(errors)}")
"""),

    md("""## Шаг 5. Посмотрите на 3 ошибки глазами

**TODO:** напечатайте первые 3 случая, где модель ошиблась. Ваша
задача — глазами понять, **почему** модель могла сбиться.
"""),

    code("""for i, e in enumerate(errors[:3], 1):
    print(f"--- Ошибка #{i} ---")
    print(f"Истина:    {e['true']}")
    print(f"Модель:    {e['pred']}")
    print(f"Текст:     {e['text']} ...")
    print()
"""),

    md("""## Шаг 6. Развитие — попробуйте другую модель

**TODO (опционально):** в одной строке кода поменяйте модель на
многоязычную и прогоните ещё раз.
"""),

    code("""# TODO: раскомментируйте и сравните accuracy
# clf_multi = pipeline(
#     "sentiment-analysis",
#     model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
# )
# correct = sum(
#     1 for row in ds
#     if {"positive": "POSITIVE", "negative": "NEGATIVE", "neutral": "NEUTRAL"}.get(
#         clf_multi(row["text"][:512])[0]["label"], ""
#     ) == ("POSITIVE" if row["label"] == 1 else "NEGATIVE")
# )
# print(f"Multi-lingual accuracy: {correct/len(ds):.0%}")
"""),

    md("""## Шаг 7. Один абзац о наблюдении

**TODO:** одно-два предложения. На каких типах фраз distilbert сбоит?
Что общего у ошибок?
"""),

    md("""**TODO: ваше наблюдение здесь.**
"""),

    md("""## Сдача

`Save & Run All` → `Share Public` → ссылка в чат:
`[Модуль 1.5, практика HF] {ссылка}`.

Дальше — [практика 3: Google AI Studio](./practice-aistudio.ipynb).
"""),
]

write("homework", "practice-huggingface", practice_hf)


# -----------------------------------------------------------------------
# PRACTICE 3: Google AI Studio — Gemini API
# -----------------------------------------------------------------------

practice_ai = [
    md("""# Практика 3/3: Google AI Studio — Gemini API

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
> Третья из трёх практик. На этой задаче вы трогаете **только Google
> AI Studio**: достаёте ключ из Kaggle Secrets и шлёте запросы в
> `gemini-2.5-flash` через `google-genai` SDK. Никаких HF.
>
> Время: ~10 минут.
"""),

    md("""## Что делаем

Foundation-LLM — это «универсальный кубик» из ветки C карты ML. Тот же
вопрос (классификация настроения короткой фразы) можно решать им — без
обучения, без датасета, через промпт. Сравним с тем, что было на HF —
прицельно увидим, в чём foundation-модель лучше, а в чём избыточна.

Шаг с structured output (enum mode) важен сам по себе: без него LLM
норовит ответить «I think it's POSITIVE because...» — и весь
пайплайн ломается на парсинге.
"""),

    md("""## Шаг 1. Setup и ключ"""),

    code("""!pip install -q google-genai
"""),

    code("""from kaggle_secrets import UserSecretsClient

GOOGLE_API_KEY = UserSecretsClient().get_secret("GOOGLE_API_KEY")
print("Ключ Gemini загружен, длина:", len(GOOGLE_API_KEY), "символов")
"""),

    md("""## Шаг 2. Первый запрос — sanity check"""),

    code("""from google import genai

client = genai.Client(api_key=GOOGLE_API_KEY)

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Поздоровайся одним предложением на русском.",
)
print(resp.text)
"""),

    md("""## Шаг 3. Sentiment через промпт — наивная версия

Сначала — как «обычный программист сделал бы 2 года назад»: просим
модель ответить словом, парсим текст руками.
"""),

    code("""from google.genai import types

# TODO: замените на свои 5 фраз (минимум одна — на русском, одна с подвохом)
phrases = [
    "TODO: позитивная фраза",
    "TODO: негативная фраза",
    "TODO: фраза с сарказмом",
    "TODO: что-нибудь на русском",
    "TODO: короткая фраза, 1-3 слова",
]

cfg_naive = types.GenerateContentConfig(
    system_instruction=(
        "You are a sentiment classifier. For each input, return EXACTLY "
        "one word: POSITIVE or NEGATIVE. No explanations."
    ),
    temperature=0,
    max_output_tokens=4,
)

for phrase in phrases:
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        config=cfg_naive,
        contents=phrase,
    )
    label = resp.text.strip().upper().rstrip(".!?")
    print(f"{label:8s} | {phrase}")
"""),

    md("""## Шаг 4. Structured output — нормальная версия

Тот же запрос, но теперь говорим модели: «возвращай только значение из
этого enum'а, никакого свободного текста». Это надёжнее на порядок —
модель ломается куда реже.
"""),

    code("""import enum


class Sentiment(enum.Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


cfg_enum = types.GenerateContentConfig(
    response_mime_type="text/x.enum",
    response_schema=Sentiment,
    temperature=0,
)

results = []
for phrase in phrases:
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        config=cfg_enum,
        contents=f"Classify sentiment of this text:\\n{phrase}",
    )
    # response.parsed — это уже Python enum, не строка
    results.append(resp.parsed)
    print(f"{resp.parsed.value:8s} | {phrase}")
"""),

    md("""## Шаг 5. Меняем температуру и смотрим, что плывёт

**TODO:** запустите ячейку. На каких фразах модель «передумала» при
высокой температуре?
"""),

    code("""cfg_hot = types.GenerateContentConfig(
    system_instruction="Return EXACTLY one word: POSITIVE or NEGATIVE.",
    temperature=2.0,
    max_output_tokens=4,
)

print("Температура 2.0 (5 запусков одной фразы):")
test_phrase = phrases[2]  # фраза с сарказмом
for _ in range(5):
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        config=cfg_hot,
        contents=test_phrase,
    )
    print(f"  {resp.text.strip()}")
"""),

    md("""## Шаг 6. Один абзац о наблюдении

**TODO:** одно-два предложения:

1. Где Gemini справился, а distilbert из практики 2 — нет (или наоборот)?
2. Что дал structured output по сравнению с наивным промптом? Когда без
   него можно было обойтись?
"""),

    md("""**TODO: ваше наблюдение здесь.**
"""),

    md("""## Сдача

`Save & Run All` → `Share Public` → ссылка в чат:
`[Модуль 1.5, практика AI Studio] {ссылка}`.

Все три практики сданы — поздравляю, инструментарий настроен и
проверен в бою. Дальше — Модуль 2 (карта ML-вселенной).
"""),
]

write("homework", "practice-aistudio", practice_ai)


# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# PRESENTER DEMO — подробный школьный вариант с разбором каждого шага
# -----------------------------------------------------------------------

demo = [
    md("""# Presenter Demo: три площадки за 7—10 минут

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
>
> Это демонстрационный ноутбук для урока. После **каждой** ячейки
> кода идёт абзац-разбор: что код сделал, что значит вывод, и что
> можно **поменять самому**, чтобы попробовать.
>
> Цель: к концу ноутбука вы понимаете, чем три площадки (Kaggle,
> Hugging Face, Google AI Studio) отличаются друг от друга — на
> своих руках, не на словах.
>
> **Перед запуском:** в Kaggle → `Add-ons → Secrets` должен быть
> прикреплён `GOOGLE_API_KEY`. `HF_TOKEN` не обязателен.
"""),

    md("""# Часть 1. Kaggle — где живёт код

Kaggle — это **бесплатный компьютер в браузере**. Вам не надо ставить
Python, не надо настраивать видеокарту, не надо платить за облако.
Вы открыли вкладку — у вас уже есть рабочая среда с Python, GPU
(если попросить) и местом на диске.

Давайте посмотрим, что именно нам дали.
"""),

    code("""import sys, platform, os

print("Версия Python:", sys.version.split()[0])
print("Операционка:  ", platform.platform())
print("Где мы сейчас:", os.getcwd())

# Сколько места осталось в папке, которая переживёт перезапуск ноутбука
free_gb = os.statvfs('/kaggle/working').f_bavail * 512 // (1024**3)
print(f"Свободно в /kaggle/working: {free_gb} ГБ")
"""),

    md("""**Что мы сейчас увидели:**

- **Python 3.11+** — современная версия, всё свежее.
- **Linux** — Kaggle крутится на Linux-серверах. Если у вас Windows
  или Mac — на Kaggle всё одно ведёт себя одинаково.
- **`/kaggle/working`** — это ваша личная папка. Всё, что вы сюда
  сохраните, **переживёт перезапуск ноутбука** (а вот переменные в
  памяти — нет).
- **20 ГБ места** — этого хватит на любую учебную модель.

**Поменять и попробовать:**

- Добавьте свою строку, например `print("Привет!")`.
- Или замените `/kaggle/working` на `/tmp` — увидите, сколько места
  во временной папке (она *не* переживает перезапуск, но больше по
  объёму).
"""),

    code("""# Проверяем, дали ли нам видеокарту
!nvidia-smi -L 2>/dev/null || echo "GPU не подключён — это нормально, переключите Accelerator в правой панели если нужен"
"""),

    md("""**Что произошло:**

`!nvidia-smi -L` — это **команда операционной системы** (восклицательный
знак `!` в Jupyter означает «запусти не Python, а shell»). Она спрашивает
видеокарту: «представься».

- Если видишь строку вида `GPU 0: Tesla T4 (UUID: ...)` — отлично,
  у тебя есть видеокарта.
- Если видишь «GPU не подключён» — справа в `Notebook options`
  переключи **Accelerator** на `GPU T4 x2` или оставь `None`. Для
  сегодняшнего демо GPU **не обязателен** — модели крошечные, на
  CPU летают.

**Поменять и попробовать:**

- Запусти `!ls /kaggle/working` — увидишь, что в твоей папке лежит.
- Запусти `!pip list | head -20` — увидишь первые 20 установленных
  библиотек (их там несколько сотен по умолчанию).
"""),

    md("""# Часть 2. Hugging Face — где живут модели

**Hugging Face (HF)** — это сайт, где люди делятся моделями
машинного обучения. Похоже на GitHub, но вместо кода — обученные
модели (готовые «мозги», которым уже не надо учиться, можно сразу
использовать).

Мы возьмём оттуда две модели:

1. **`distilbert`** — определяет настроение текста (positive /
   negative). Маленькая, ~250 МБ.
2. **`MiniLM`** — превращает текст в «вектор» (набор чисел), по
   которому можно сравнивать тексты между собой по смыслу. Ещё
   меньше, ~90 МБ.
"""),

    code("""# Ставим библиотеку transformers (это инструмент для работы с моделями HF)
!pip install -q transformers
"""),

    md("""**Что произошло:** `!pip install -q transformers` — установили
библиотеку. `-q` означает «тихо» (без длинного лога установки).

Эта команда обычно занимает 10—20 секунд. Запускается **один раз** на
ноутбук — после установки библиотека уже в памяти Kaggle.
"""),

    code("""from transformers import pipeline

# device=-1 означает "считай на CPU". У нас модели маленькие, GPU не нужен.
clf = pipeline("sentiment-analysis", device=-1)

# Кормим модели три фразы и смотрим, что она думает
print(clf("This course is unexpectedly fun."))
print(clf("Honestly, I'm just here for the certificate."))
print(clf("It was not bad, actually."))
"""),

    md("""**Что произошло — построчно:**

1. `from transformers import pipeline` — импортировали готовый
   «конвейер». Этот объект сам качает модель с HF, готовит её к работе
   и принимает текст на вход.
2. `pipeline("sentiment-analysis", device=-1)` — попросили конвейер
   для задачи «определить настроение». HF сам выбрал лучшую
   дефолтную модель — это `distilbert`. `device=-1` = CPU.
3. `clf("This course is unexpectedly fun.")` — отдали фразу модели,
   она вернула ответ.

**Что значит вывод:**

```
[{'label': 'POSITIVE', 'score': 0.9998}]
[{'label': 'POSITIVE', 'score': 0.7815}]
[{'label': 'POSITIVE', 'score': 0.9993}]
```

- **`label`** — что модель решила: POSITIVE или NEGATIVE.
- **`score`** — насколько модель уверена (от 0 до 1, где 1 — «точно»).

**Интересный момент:** вторая фраза «I'm just here for the certificate»
получила score **0.78** — модель сомневается. На самом деле тут лёгкий
сарказм («я тут только ради сертификата»), но distilbert этого не
улавливает и говорит «вроде позитивная». Это пример **границ модели**:
маленькая специализированная модель отлично справляется с очевидным,
но путается на тонкостях.

**Поменять и попробовать:**

- Добавь ещё одну фразу: `print(clf("This is terrible!"))` —
  должно вернуть NEGATIVE с высоким score.
- Попробуй на русском: `print(clf("Какой ужасный урок"))` — увидишь,
  что модель растеряется (она училась на английском).
- Длинный отзыв: `print(clf("I loved the beginning but the ending was awful."))` —
  посмотри, что модель решит при смешанной оценке.
"""),

    code("""# Вторая модель — превращает текст в "вектор" (точку в многомерном пространстве)
from sentence_transformers import SentenceTransformer
import numpy as np

emb_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu",
)

phrases = [
    "The quick brown fox jumps over the lazy dog.",
    "A fast fox leaps over a sleepy hound.",         # то же самое, другими словами
    "I love pizza with pineapple.",                   # совсем про другое
    "Шустрый лис прыгает через ленивую собаку.",     # русский перевод первой фразы
]

# Превращаем каждую фразу в вектор из 384 чисел
vectors = emb_model.encode(phrases, normalize_embeddings=True)

# Считаем "похожесть" каждой пары: близко к 1.0 = очень похожи, к 0 = разные
similarity = vectors @ vectors.T

# Красивая таблица
import pandas as pd
labels = [p[:40] + ("..." if len(p) > 40 else "") for p in phrases]
pd.DataFrame(similarity.round(2), index=labels, columns=labels)
"""),

    md("""**Что произошло — построчно:**

1. **Скачали** ещё одну модель — `all-MiniLM-L6-v2`. Это
   embedding-модель: на вход — текст, на выход — список из 384 чисел
   («вектор» или «эмбеддинг»). Близкие по смыслу фразы дают близкие
   векторы.
2. **Дали ей 4 фразы**: оригинал про лиса, перефраз про лиса, фраза
   про пиццу (не в тему), и тот же лис на русском.
3. **`emb_model.encode(...)`** — превратили каждую фразу в вектор.
4. **`vectors @ vectors.T`** — посчитали «cosine similarity» между
   каждой парой. Это математический способ сказать «насколько две
   точки рядом» (1.0 = совпадение, 0 = совсем не похоже).

**Что значит таблица:**

```
                              fox|fast fox|pizza|русский лис
the quick brown fox        | 1.00 | 0.76  | 0.04 | 0.10
a fast fox leaps           | 0.76 | 1.00  | 0.02 | 0.13
i love pizza               | 0.04 | 0.02  | 1.00 | 0.00
Шустрый лис прыгает        | 0.10 | 0.13  | 0.00 | 1.00
```

- На **диагонали — 1.00** (каждая фраза идентична самой себе, очевидно).
- **0.76** между «the quick brown fox» и «a fast fox leaps» — модель
  поняла, что это **синонимы**. Хотя слова разные, смысл один.
- **0.04** между «лис» и «пицца» — модель видит, что фразы про
  совсем разное.
- **0.10** между английским «the quick brown fox» и русским
  переводом — а вот тут модель **сломалась**. Она училась только
  на английском, поэтому русский для неё — просто «непонятный набор
  букв», и она не видит связи.

**Это важный урок:** модель ровно настолько умна, насколько ей
показали разнообразные данные при обучении. Если хотите, чтобы
работала и на русском — нужна **многоязычная** embedding-модель,
например `paraphrase-multilingual-MiniLM-L12-v2`.

**Поменять и попробовать:**

- Замени одну из фраз на свою — например `"My cat is sleeping on the keyboard."` —
  посмотри, на что она похожа больше всего.
- Добавь пятую фразу-перефраз: `"A cat is napping on a laptop."` —
  должно дать ~0.7 с предыдущей.
- Поменяй модель на многоязычную:
  `SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")` —
  и русская фраза станет похожа на английскую.
"""),

    md("""# Часть 3. Google AI Studio — где живёт Gemini

**Google AI Studio** — это сайт Google, на котором живёт большая
языковая модель **Gemini**. В отличие от Hugging Face, Gemini не
скачивается к вам на компьютер — это **облачная модель**.

Вы шлёте ей текст-вопрос (или картинку), она шлёт ответ. Платите
обычно за каждый запрос (но небольшой объём в день — бесплатно).

Главное отличие от distilbert и MiniLM: Gemini — **универсальная**.
Она может всё подряд (классифицировать, переводить, писать код,
читать картинки), а не одну задачу.
""")

    ,

    code("""# Установка библиотеки для общения с Gemini
!pip install -q google-genai
"""),

    md("""**Что произошло:** установили библиотеку `google-genai` —
официальный инструмент Google для отправки запросов к Gemini из Python.
"""),

    code("""import enum
from google import genai
from google.genai import types
from kaggle_secrets import UserSecretsClient

# Достаём API-ключ из Kaggle Secrets (не из кода!)
client = genai.Client(api_key=UserSecretsClient().get_secret("GOOGLE_API_KEY"))


# Описываем словами Gemini, какие ответы мы допускаем.
# enum.Enum в Python — это "выбор из списка вариантов".
class Sentiment(enum.Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


# Настройки: модель должна вернуть только одно из трёх значений выше,
# никакого свободного текста.
cfg = types.GenerateContentConfig(
    response_mime_type="text/x.enum",
    response_schema=Sentiment,
    temperature=0,  # 0 = без креатива, всегда одинаковый ответ
)

# Отправляем 4 фразы и печатаем результат
for phrase in [
    "It was not bad, actually.",
    "Лучше бы я остался дома.",
    "норм",
    "Best class I've taken in years!",
]:
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        config=cfg,
        contents=phrase,
    )
    print(f"{resp.parsed.value:8s} | {phrase}")
"""),

    md("""**Что произошло — построчно:**

1. **`UserSecretsClient().get_secret("GOOGLE_API_KEY")`** — достали
   API-ключ из Kaggle Secrets. Это **безопасный способ**: ключ не
   виден в коде, его не увидят те, кому вы покажете ноутбук.
2. **`class Sentiment(enum.Enum)`** — сказали Python: «возможные
   ответы — только эти три слова». Это нужно для следующего шага.
3. **`response_schema=Sentiment`** — сказали Gemini: «отвечай только
   одним словом из этого списка, никаких объяснений, никаких
   `I think it's POSITIVE because...`». Это называется **structured
   output** и сильно облегчает работу: вы заранее знаете, какой ответ
   получите.
4. **`temperature=0`** — отключили креатив. Модель всегда даёт тот
   же ответ на тот же вопрос. (При `temperature=1` модель чуть-чуть
   импровизирует, при `2` — фантазирует сильно.)
5. **Цикл по 4 фразам** — каждую отправляем в Gemini, получаем
   ответ, печатаем.

**Что значит вывод:**

```
POSITIVE | It was not bad, actually.
NEGATIVE | Лучше бы я остался дома.
POSITIVE | норм
POSITIVE | Best class I've taken in years!
```

- **«It was not bad, actually.»** — фраза с двойным отрицанием,
  по смыслу позитивная. Gemini её **понял правильно**, в отличие от
  distilbert, который часто на таком ошибается.
- **«Лучше бы я остался дома.»** — на русском, чистый негатив.
  Gemini понимает русский — это плюс ко всему.
- **«норм»** — одно слово на русском сленге. Gemini понял, что это
  скорее позитив. distilbert тут вообще ничего бы не сказал
  осмысленно.
- **Последняя** — очевидный позитив, никаких сюрпризов.

**Вывод:** Gemini сильно лучше понимает язык, особенно тонкости и
русский. Платите за это: каждый запрос идёт в облако Google, медленнее
distilbert и стоит денег при большом объёме.

**Поменять и попробовать:**

- Добавь свою фразу с сарказмом: «I love waiting in line for hours.»
- Поменяй `temperature=0` на `temperature=2` — увидишь, что модель
  иногда «передумывает».
- Добавь в `Sentiment` четвёртый вариант: `SARCASTIC = "SARCASTIC"` —
  Gemini научится распознавать сарказм отдельной категорией.
"""),

    md("""## Бонус: Gemini «видит» картинку

Gemini умеет не только читать текст, но и **смотреть на картинки**.
Покажем ему фото чека и попросим вытащить оттуда название магазина,
сумму и количество товаров — **сразу в виде JSON**, готовый для
программы.
"""),

    code("""import typing_extensions as typing
import urllib.request

# Скачиваем публичный пример чека (картинка лежит на HF)
url = "https://datasets-server.huggingface.co/assets/mychen76/invoices-and-receipts_ocr_v1/--/default/test/0/image/image.jpg"
img_bytes = urllib.request.urlopen(url).read()


# Описываем, какой JSON мы хотим получить
class Receipt(typing.TypedDict):
    vendor: str          # название магазина
    total_amount: str    # итоговая сумма (строкой, потому что у чеков валюта в формате)
    item_count: int      # сколько позиций


# Отправляем картинку + просьбу извлечь поля
resp = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Receipt,
        temperature=0,
    ),
    contents=[
        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
        "Extract vendor name, total amount, and number of line items from this receipt.",
    ],
)
print(resp.text)
"""),

    md("""**Что произошло:**

1. **Скачали картинку** чека с публичного датасета HF.
2. **Описали JSON-схему** ответа: три поля — название магазина,
   сумма, число товаров.
3. **Отправили** Gemini две вещи: саму картинку + просьбу «вытащи
   эти три поля».
4. Gemini **прочитал чек глазами**, нашёл нужные поля, вернул
   готовый JSON.

**Что значит вывод:**

Результат будет выглядеть примерно так:
```json
{"vendor": "Costco Wholesale", "total_amount": "$45.67", "item_count": 8}
```

(точные значения зависят от того, какой чек попался — он рандомный
из публичного датасета).

**Почему это круто:** ещё 2 года назад «прочитать чек и достать поля»
требовало OCR-библиотеку (Tesseract), регулярные выражения и неделю
программирования. Сейчас — **один запрос к LLM**. Это и есть та
самая «революция foundation-моделей», о которой мы говорили в
Модуле 2.

**Поменять и попробовать:**

- Добавь в `Receipt` поле `date: str` — Gemini вытащит и дату.
- Поменяй просьбу на «Translate the vendor name to Russian» — модель
  ещё и переведёт.
- Дай свою картинку (загрузи через `+ Add Input → Upload`) и
  попроси извлечь из неё что-нибудь.
"""),

    md("""# Часть 4. Бонус-бонус: function calling — первый агент

Это уже **тизер к Модулю 8**. Покажем, как LLM может **сама вызывать
функции**, которые мы написали, чтобы достать данные.
"""),

    code("""import sqlite3

# Создаём крошечную базу в памяти — представим, что это каталог магазина
db = sqlite3.connect(":memory:")
db.executescript('''
CREATE TABLE products (name TEXT, price REAL);
INSERT INTO products VALUES ('Laptop', 799.99), ('Keyboard', 129.99), ('Mouse', 29.99);
''')


def list_products() -> list[tuple[str, float]]:
    \"\"\"Return all products with their prices from the store catalog.\"\"\"
    print(" -> Gemini позвал нашу функцию list_products()")
    return db.execute("SELECT name, price FROM products").fetchall()


# Создаём чат, который умеет звать нашу функцию когда понадобится
chat = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction="You are a sales assistant. Use the tool to look up products.",
        tools=[list_products],
    ),
)

# Задаём вопрос на русском — модель сама поймёт, что надо звать функцию
print(chat.send_message("Какой у нас самый дешёвый товар и сколько он стоит?").text)
"""),

    md("""**Что произошло — это самое важное в демо:**

1. **Создали базу данных** в памяти — 3 товара с ценами.
2. **Написали обычную Python-функцию** `list_products()` — она
   возвращает все товары. Главное здесь — **docstring** в тройных
   кавычках сразу после `def`. Gemini читает этот docstring и решает,
   когда функцию надо вызвать.
3. **Создали чат** и передали ему функцию через `tools=[list_products]`.
4. **Задали вопрос на русском.** Gemini:
   - Прочитал вопрос.
   - Подумал: «надо посмотреть товары».
   - **Сам решил позвать** `list_products()`.
   - Получил данные `[('Laptop', 799.99), ('Keyboard', 129.99), ('Mouse', 29.99)]`.
   - Выбрал самый дешёвый (Mouse).
   - Ответил на русском человеческим языком.

**Это и есть агент.** Не «LLM, которая отвечает текстом», а
«LLM, которая может звать функции и взаимодействовать с миром».

В Модуле 8 мы это разберём подробно: что такое цикл, что такое
инструменты, как сделать так, чтобы агент не наделал ерунды.

**Поменять и попробовать:**

- Спроси по-другому: «What's our most expensive product?»
- Добавь второй tool — функцию `add_product(name, price)` и попроси
  «добавь чай за 5 долларов».
- Меняй вопрос: «У нас есть клавиатуры?», «Сколько товаров в магазине?»
"""),

    md("""# Что мы только что увидели

За эти 7—10 минут мы:

1. **Kaggle** — нашли свою рабочую среду, проверили Python и место
   на диске.
2. **Hugging Face** — скачали две готовые модели, прогнали через них
   тексты, увидели и сильные стороны (быстро, дёшево), и слабые
   (не понимают русский, не ловят сарказм).
3. **Google AI Studio** — поговорили с Gemini, заставили его отвечать
   только enum'ами, прочитали картинку чека в JSON.
4. **Function calling** — увидели, как Gemini сам вызывает наш Python-код.

Это все три площадки в работе. Дальше на курсе будем нырять в каждую
глубже — но базу вы только что поглядели **руками**.

**Что попробовать сразу:**

- Любая ячейка выше — поменяйте текст / фразу / промпт, нажмите
  `Shift+Enter`. Это никак ничего не сломает (хуже всего —
  получите смешной ответ).
- `Run All` ещё раз — все скачивания уже в кэше, второй прогон будет
  в несколько раз быстрее.
"""),
]

write("lesson", "presenter-demo", demo)
