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

clf = pipeline("sentiment-analysis")  # дефолт: distilbert SST-2, ~250 МБ
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
