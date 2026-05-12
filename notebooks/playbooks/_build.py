"""Generate Kaggle and Hugging Face playbook notebooks.

Run: `python _build.py` (no deps beyond stdlib).
Re-run whenever you change the content lists below — the .ipynb files are
regenerated deterministically.
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


def write(name: str, cells: list[dict]) -> None:
    path = HERE / f"{name}.ipynb"
    path.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=1))
    print(f"wrote {path}")


# -----------------------------------------------------------------------
# KAGGLE TOUR
# -----------------------------------------------------------------------

kaggle = [
    md("""# Playbook: Kaggle Tour

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
> Это не урок-теория, это **демо-сценарий** для живой практики.
> Веду демонстрацию в Kaggle UI и время от времени запускаю ячейки этой
> ноутбука — чтобы все вместе видели, что получилось.
>
> Длительность: ~25 минут.
> Что в конце: у каждого ученика — свой работающий Kaggle-ноутбук с
> подключённым GPU и привязанным секретом `GOOGLE_API_KEY`.
"""),

    md("""## 0. Что мы делаем сегодня

Три задачи на эту демонстрацию:

1. Завести аккаунт на Kaggle и пройти phone verify (без него нет GPU и
   нет Secrets — это два самых ценных бесплатных ресурса).
2. Создать первый ноутбук, переключить его на GPU T4 и убедиться, что
   GPU действительно подключён.
3. Положить API-ключ Google AI Studio в Kaggle Secrets, достать его из
   кода и сделать первый запрос к Gemini.

Это база, на которой будут стоять все следующие ДЗ курса.
"""),

    md("""## 1. Регистрация и phone verify (web, не код)

1. Открыть https://www.kaggle.com → **Register**.
2. Регистрация через Google-аккаунт быстрее всего и сразу даёт тот
   аккаунт, который пригодится для AI Studio.
3. Подтвердить почту по ссылке из письма.
4. Зайти в https://www.kaggle.com/settings → секция **Phone verification**.
5. Указать номер, ввести код из SMS.

**Почему phone verify — обязательный шаг:**
без него Kaggle не показывает кнопку Accelerator (GPU/TPU) в ноутбуке
и не даёт работать с Secrets. Это анти-абьюз мера, обойти нельзя.

**Если номер не из поддерживаемого региона:** заведите аккаунт на
номер, к которому есть доступ (виртуальный SIM, друг, рабочий номер).
"""),

    md("""## 2. Создаём первый ноутбук (web)

1. Слева в боковом меню: **Code** → **+ New Notebook**.
2. Откроется Jupyter в браузере. По умолчанию даётся CPU.
3. Справа есть панель **Notebook options**. Главные настройки там:
   - **Accelerator** — `None` / `GPU T4 x2` / `GPU P100` / `TPU VM`.
   - **Persistence** — `Files only` достаточно (переменные между
     запусками всё равно теряются, оставляем по умолчанию).
   - **Language** — Python.

Сейчас оставим Accelerator = `None` — для следующей ячейки GPU не
нужен. Включим его на шаге 3, чтобы заодно посмотреть, как это
выглядит.
"""),

    md("""### 2.1 Sanity check — что мы вообще запускаем

Первая ячейка любого нового ноутбука у меня — это «привет, какая среда».
Это занимает 3 секунды и сразу видно: правильная версия Python, какая
ОС, есть ли GPU.
"""),

    code("""import sys
import platform

print("Python:", sys.version.split()[0])
print("Platform:", platform.platform())
"""),

    md("""## 3. Включаем GPU и проверяем

Справа в **Notebook options** → **Accelerator** → выбираем
**GPU T4 x2**. Ноутбук перезапустится (ядро будет новое).

После перезапуска проверим, что GPU действительно подключён, через
`nvidia-smi`. Если в выводе видна строка `Tesla T4` — всё хорошо.
"""),

    code("""!nvidia-smi 2>/dev/null | head -20 || echo "GPU не подключён — переключите Accelerator справа"
"""),

    md("""**Что важно запомнить:**

- GPU-квота — около 30 часов в неделю на верифицированный аккаунт.
  Сбрасывается каждую субботу.
- Когда ноутбук «активный» (вкладка открыта или код выполняется) —
  квота тикает. Когда вы закрыли вкладку и нажали `Stop session`
  внизу — не тикает.
- На учебные ДЗ 30 часов хватает с большим запасом. Сжигают её обычно
  «забыл выключить, ушёл спать, проснулся — кончилось».
"""),

    md("""## 4. Secrets — главный приём всего курса

Сейчас нам нужен API-ключ Google AI Studio. Параллельно у меня в
соседней вкладке открыт https://aistudio.google.com → **Get API key**.
Создаю ключ, копирую (он начинается с `AIza...`).

Дальше — **не вставляю ключ в код**. Вставляю в Kaggle Secrets:

1. В верхнем меню ноутбука: **Add-ons** → **Secrets**.
2. **Add a new secret**.
3. Label: `GOOGLE_API_KEY` (имя в верхнем регистре, без пробелов).
4. Value: сам ключ.
5. **Обязательно ставим галочку «Attach to notebook»** — иначе ноутбук
   секрет не увидит.

В коде секрет достаётся вот так:
"""),

    code("""from kaggle_secrets import UserSecretsClient

GOOGLE_API_KEY = UserSecretsClient().get_secret("GOOGLE_API_KEY")
print("Ключ загружен, длина:", len(GOOGLE_API_KEY), "символов")
# Сам ключ НИКОГДА не печатаем. Только длину — для проверки, что он
# не пустой.
"""),

    md("""**Самая частая ошибка:** `No user secrets exist for kernel id ...`
Лечится одной галкой «Attach to notebook» рядом с именем секрета.
В 90% случаев студент создаёт секрет, но забывает его прикрепить.
"""),

    md("""## 5. Первый запрос к Gemini — проверяем end-to-end

Теперь, когда у нас есть ключ, делаем первый осмысленный запрос —
просто чтобы убедиться, что вся цепочка (Kaggle → Secrets → Gemini API
→ ответ) работает.
"""),

    code("""!pip install -q google-genai
"""),

    code("""from google import genai

client = genai.Client(api_key=GOOGLE_API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Поздоровайся со студентами курса \\"От нуля до своих агентов\\" одним предложением.",
)

print(response.text)
"""),

    md("""Если ответ пришёл — поздравляем, всё работает.

Если упало с `User location is not supported` — это региональное
ограничение Gemini API. Лечится: (а) VPN, (б) выпустить ключ из самого
Kaggle-ноутбука (Google видит запрос с серверов GCP).
"""),

    md("""## 6. Datasets — подключаем готовый датасет за один клик

Kaggle сам по себе — это огромная коллекция датасетов. Можно
подключить любой к своему ноутбуку без скачивания.

1. Справа в панели — **+ Add Input**.
2. **Datasets** → поиск по названию (например, `imdb dataset`).
3. Нажимаем на иконку плюса рядом с нужным датасетом.

После подключения файлы появляются в `/kaggle/input/<dataset-slug>/`.
Покажем:
"""),

    code("""import os

# Эту ячейку имеет смысл запускать ПОСЛЕ того, как вы подключили
# какой-нибудь датасет через UI. Если ничего не подключали — список
# будет пустым.
input_root = "/kaggle/input"
if os.path.isdir(input_root):
    for name in sorted(os.listdir(input_root)):
        print("-", name)
else:
    print("Нет подключённых датасетов. Добавьте через '+ Add Input'.")
"""),

    md("""## 7. Сохранение и публикация

Когда ДЗ готово:

1. Сверху: **Save Version** → **Save & Run All (Commit)** — это полный
   прогон ноутбука сверху вниз с нуля. Кэш ячеек сбрасывается. Долго,
   но именно так Kaggle сохраняет финальную версию.
2. **Share** → **Public** — теперь ссылку видно всем.
3. Скопируйте URL вида `https://www.kaggle.com/code/<your-id>/<slug>` —
   это и есть артефакт для сдачи.

**Перед публикацией обязательно:**

- Убрать из вывода ячеек всё, что может содержать ваш ключ.
- Если случайно напечатали — удалите ячейку, нажмите `Save & Run All`
  ещё раз, и **сразу отзовите ключ** в AI Studio. Раскрытый ключ —
  бесплатный билет в чужие эксперименты на ваш счёт.
"""),

    md("""## 8. Что должно получиться у каждого

К концу демонстрации у каждого ученика должно быть:

- [ ] Аккаунт Kaggle с пройденным phone verify.
- [ ] Хотя бы один ноутбук, в котором запускался `!nvidia-smi` с GPU.
- [ ] Секрет `GOOGLE_API_KEY` создан и прикреплён к ноутбуку.
- [ ] Ячейка `client.models.generate_content(...)` вернула осмысленный
      ответ.

Если хоть один пункт не получился — это блокер на ближайшие модули.
Останавливаемся и разбираем индивидуально, остальная группа делает
паузу.

**Следующий шаг — playbook по Hugging Face.**
"""),
]

write("kaggle-tour", kaggle)


# -----------------------------------------------------------------------
# HUGGING FACE TOUR
# -----------------------------------------------------------------------

hf = [
    md("""# Playbook: Hugging Face Tour

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
> Демо-сценарий, по которому я провожу живую экскурсию по HF.
> Часть времени — переключаемся в браузер и смотрим UI Hub,
> часть — запускаем код прямо здесь, в этом ноутбуке.
>
> Длительность: ~20 минут.
> Что в конце: у каждого — токен HF в Kaggle Secrets, запущенный
> `pipeline(\"sentiment-analysis\")`, загруженный датасет IMDB, понимание,
> что такое model card и Space.

> **Предпосылка:** запускать этот ноутбук имеет смысл уже в Kaggle —
> чтобы переиспользовать настроенную среду из `kaggle-tour.ipynb`.
"""),

    md("""## 0. Зачем нам Hugging Face

Простой ответ: это GitHub для весов моделей и датасетов. Без него
работа с открытыми моделями превращается в «скачайте zip-архив с
сайта университета 2019 года».

Длинный ответ: HF Hub даёт три вещи:

1. **Готовые модели** — миллион+ моделей с открытыми весами. Каждая —
   как репозиторий с карточкой README, файлами весов и примерами.
2. **Готовые датасеты** — тысячи стандартизованных датасетов, которые
   подключаются строкой кода.
3. **Spaces** — бесплатный хостинг для демо-приложений на Gradio или
   Streamlit. На Spaces поднимают тысячи live-демо моделей.

Плюс библиотеки `transformers`, `datasets`, `huggingface_hub` —
которыми всё это используется из кода.
"""),

    md("""## 1. Регистрация и токен (web)

1. Открыть https://huggingface.co/join, зарегистрироваться.
2. Подтвердить почту.
3. Профиль (правый верхний угол) → **Settings** → **Access Tokens**.
4. **New token** → Type = **Read** (Write нужен только когда вы сами
   публикуете модель).
5. Имя: `train-of-thought-course`.
6. **Скопировать токен сразу** — второй раз он не покажется.

**Положить токен в Kaggle Secrets:**
`Add-ons` → `Secrets` → `Add a new secret` → имя `HF_TOKEN`, значение —
сам токен. Галка **Attach to notebook** обязательна.

Достаём в коде:
"""),

    code("""from kaggle_secrets import UserSecretsClient

HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
print("HF токен загружен, длина:", len(HF_TOKEN), "символов")
"""),

    md("""## 2. Экскурсия по Hub (web — переключаемся в браузер)

Открываем https://huggingface.co и идём по верхнему меню:

- **Models** — фильтры слева: задача (Text Generation, Image
  Classification...), язык, лицензия, размер. Покажу:
  - `meta-llama/Llama-3.1-8B-Instruct` — образцовая open-weights LLM.
  - `sentence-transformers/all-MiniLM-L6-v2` — крошечная (~25M)
    embedding-модель, дефолт для семантического поиска.
  - `distilbert-base-uncased-finetuned-sst-2-english` — классификатор
    настроения, на котором мы скоро запустим `pipeline`.
- **Datasets** — фильтры по задаче и языку. Покажу:
  - `imdb` — 50k отзывов, бинарная разметка POSITIVE/NEGATIVE.
  - `c4` — гигантский веб-корпус, на котором обучали T5.
- **Spaces** — открываем 2-3 демо: `gradio/hello_world`, любой
  свежий vision-демо.

**Что в каждой странице важно показать:**

- слева **Files** — здесь живут сами веса (обычно `.safetensors` или
  `.bin`);
- сверху **Use this model** — кнопка с готовым сниппетом кода;
- внизу карточка с **license**, **datasets used**, **community**.
"""),

    md("""## 3. Анатомия model card

На примере одной модели разбираем, что читать **перед** тем как взять её
в работу. Идём на:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

Три блока, которые надо прочесть всегда:

1. **License** — указана сверху и сбоку. `apache-2.0`, `mit` —
   используете коммерчески спокойно. `llama3`, `gemma` — есть
   оговорки. `cc-by-nc` — некоммерчески. Просто «опубликовано на HF»
   не значит «можно где угодно».
2. **Intended uses / Out-of-scope use** — часто авторы сами пишут
   «работает только на английском», «не для медицинских решений», и
   так далее.
3. **Model size / Inference requirements** — сколько ГБ памяти ест.
   На Kaggle T4 (15 ГБ VRAM) модель в 7B параметров с fp16 поместится
   впритык. 70B — не поместится никак.

**Правило большого пальца для размера в памяти:**

- fp32 (полная точность): N миллиардов параметров × 4 ГБ
- fp16/bf16: N × 2 ГБ
- int8 (квантизация): N × 1 ГБ
- int4: N × 0.5 ГБ

Llama-3.1-8B → 16 ГБ в fp16 → впритык на T4 → имеет смысл взять
int4-квантизованную версию.
"""),

    md("""## 4. Первая модель за 3 строки — pipeline

Самое простое API HF — `pipeline`. Под капотом он:

1. Идёт на Hub, скачивает дефолтную модель для указанной задачи.
2. Кладёт её в локальный кэш (`~/.cache/huggingface/` или `HF_HOME`).
3. Поднимает токенизатор + модель + пост-обработку результата.

Три строки — и вы делаете то, что в 2018-м стоило недели работы.
"""),

    code("""!pip install -q transformers
"""),

    code("""from transformers import pipeline

# device=-1 — принудительно CPU. На Kaggle бывает старый GPU (Tesla
# P100), который несовместим со свежим PyTorch. Для крошечной distilbert
# CPU быстрее по запуску и надёжнее.
clf = pipeline("sentiment-analysis", device=-1)  # дефолт: distilbert SST-2, ~250 МБ
print(clf("This course is unexpectedly fun."))
print(clf("Honestly, I'm just here for the certificate."))
print(clf("I had high hopes but the second module was a slog."))
"""),

    md("""**Что произошло:**

- `pipeline("sentiment-analysis")` без аргументов взял дефолтную модель
  для этой задачи — `distilbert-base-uncased-finetuned-sst-2-english`.
  Это исторический классификатор на SST-2 датасете.
- Вернулся список словарей вида `{'label': 'POSITIVE', 'score': 0.99}`.
- В скоре — уверенность модели, не вероятность правды.

**Если хотите другую модель** — передайте её id в `model=`:
"""),

    code("""# Многоязычная sentiment-модель — работает на русском, английском, испанском, и т.д.
multi = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
)
print(multi("Этот курс мне очень нравится!"))
print(multi("Не понимаю, что тут происходит."))
"""),

    md("""## 5. Датасеты за 2 строки — load_dataset

Та же история с датасетами. Стандартизованный API, кэширование, не
надо качать архивы.
"""),

    code("""!pip install -q datasets
"""),

    code("""from datasets import load_dataset

# Первые 100 примеров из test-сплита IMDB
ds = load_dataset("imdb", split="test[:100]")
print("Тип:", type(ds).__name__)
print("Размер:", len(ds))
print("Поля:", ds.column_names)
print("Пример:")
print(" текст:", ds[0]["text"][:200], "...")
print(" метка:", ds[0]["label"], "(0 = негативный, 1 = позитивный)")
"""),

    md("""**Считаем accuracy на лету:** прогоним sentiment-классификатор
на этих 100 отзывах и сравним с настоящими метками.
"""),

    code("""correct = 0
for row in ds:
    pred = clf(row["text"][:512])[0]["label"]  # обрезаем, чтобы влезло в 512 токенов
    true_label = "POSITIVE" if row["label"] == 1 else "NEGATIVE"
    if pred == true_label:
        correct += 1

print(f"Accuracy на 100 отзывах IMDB: {correct}/{len(ds)} = {correct/len(ds):.0%}")
"""),

    md("""**Что важно заметить:**

- Эта модель училась на SST-2 (короткие фразы), а IMDB — длинные отзывы.
  Поэтому accuracy не идеальная. Это нормальная история «модель из
  одной задачи на соседней работает хуже».
- Обрезка до 512 символов грубая. В проде надо токенизировать и считать
  длину в токенах. Об этом — в Модуле 5.5.
"""),

    md("""## 6. Кэш и место на диске

Каждый вызов `pipeline(...)` или `load_dataset(...)` качает данные в
кэш `~/.cache/huggingface/`. На Kaggle это часть рабочей папки, лимит
порядка 20 ГБ.

Если планируете жонглировать большими моделями — переместите кэш во
временную папку Kaggle, у которой больше места:
"""),

    code("""import os

os.environ["HF_HOME"] = "/kaggle/temp/hf"  # /kaggle/temp — больше места
# После смены HF_HOME перезапустите ядро ноутбука: Run → Restart.
print("HF_HOME =", os.environ["HF_HOME"])
"""),

    code("""# Посмотреть, что сейчас в кэше:
!du -sh ~/.cache/huggingface 2>/dev/null || echo "Кэш пуст или папки нет"
"""),

    md("""## 7. Spaces — куда выкладывать своё демо

Spaces — это бесплатный хостинг для веб-приложений с моделями. Под
капотом — Docker-контейнер с Gradio или Streamlit. Подходит, чтобы:

- показать друзьям работу своей модели;
- сделать публичное демо к ДЗ или к pet-project'у;
- быстро попробовать чужую модель прямо в браузере.

Создание Space:

1. На сайте HF: **+ New Space**.
2. SDK: **Gradio** (самое простое) или **Streamlit**.
3. Hardware: **CPU basic** бесплатный.
4. Создать → у вас репозиторий с шаблоном `app.py`.

Самый короткий `app.py` на Gradio:

```python
import gradio as gr
from transformers import pipeline

clf = pipeline("sentiment-analysis")

def classify(text):
    result = clf(text)[0]
    return f"{result['label']} (score={result['score']:.2f})"

gr.Interface(fn=classify, inputs="text", outputs="text").launch()
```

Push в репозиторий → Space сам пересоберётся и поднимет публичный
URL. Подробнее будет в Модуле 16 (свой агент), когда придёт время
показать миру работу своего bota.
"""),

    md("""## 8. Что должно получиться у каждого

К концу демонстрации:

- [ ] Аккаунт HF создан, токен `Read` выпущен.
- [ ] Токен лежит в Kaggle Secrets как `HF_TOKEN`.
- [ ] `pipeline("sentiment-analysis")` запустился, ответ на свою фразу
      пришёл.
- [ ] `load_dataset("imdb")` отработал, видно поля и пример.
- [ ] Открыли хотя бы одну карточку модели на HF и прочитали лицензию.

Следующий шаг — играем по этой инфраструктуре в основное ДЗ Модуля 1.5
(см. лекцию: «Hello-ноутбук со всеми тремя площадками»).
"""),
]

write("huggingface-tour", hf)




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

write("practice-kaggle", practice_kaggle)


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

write("practice-huggingface", practice_hf)


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

write("practice-aistudio", practice_ai)


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

write("presenter-demo", demo)
