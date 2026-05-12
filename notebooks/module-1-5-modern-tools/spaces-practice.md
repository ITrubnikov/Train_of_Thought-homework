# Практика: HF Spaces — свой агент за 15 минут

> **Курс «От нуля до своих агентов» — Модуль 1.5.**
> Опциональная 4-я практика лекции. На предыдущих трёх вы трогали
> Kaggle, HF (`pipeline`, `load_dataset`) и Gemini API. Сейчас
> добавим последний кубик: **HF Spaces** — место, где живут публичные
> демо моделей и агентов.
>
> Время: ~15—20 минут. Артефакт: публичная ссылка на ваш Space.

## Что такое Spaces

**HF Space** — это **бесплатный Docker-контейнер с публичным URL**, в
котором живёт ваше веб-демо (Gradio, Streamlit или статический сайт).
Кто-то выкладывает чат-бота — это Space. Кто-то выкладывает генератор
картинок — тоже Space. По сути это Vercel/Netlify, но заточенный под
ML/AI-демо и бесплатный для CPU-инстансов.

В этом упражнении мы возьмём **готовый Space с агентом** от Hugging
Face Agents Course и за 15 минут сделаем его **своим**.

## Что делаем

1. Дублируем шаблон [`agents-course/First_agent_template`](https://huggingface.co/spaces/agents-course/First_agent_template).
2. Внутри — `app.py` со smolagents-агентом и Gradio-UI. **Никаких
   деталей smolagents знать не надо** — фреймворк подробно разберём в
   Модуле 10. Сейчас задача: понять механику Spaces.
3. Добавляем **свой собственный tool** в `app.py`.
4. Получаем публичный URL вида `https://huggingface.co/spaces/<вы>/First_agent_template`.

## Шаги

### 1. Дублируем шаблон

1. Откройте https://huggingface.co/spaces/agents-course/First_agent_template
2. Правый верхний угол → **три точки** → **Duplicate this Space**
   (или используйте кнопку **Duplicate** прямо на странице).
3. В диалоге:
   - Owner — ваш HF-аккаунт.
   - Space name — оставьте `First_agent_template` или придумайте своё.
   - Visibility — **Public** (бесплатный CPU доступен только публичным).
   - Hardware — `CPU basic` (бесплатно).
4. Нажмите **Duplicate Space**. Через 1—2 минуты ваш Space начнёт
   собирать Docker-образ.

### 2. Прикрепляем HF_TOKEN

Шаблон ходит на HF Inference API за моделью `Qwen2.5-Coder-32B`,
поэтому ему нужен ваш токен:

1. На странице вашего Space сверху: вкладка **Settings**.
2. Скрольните до секции **Variables and secrets**.
3. **New secret** → имя `HF_TOKEN`, значение — ваш Read-токен с
   https://huggingface.co/settings/tokens.
4. Save.

После сохранения секрета — Space автоматически перезапустится.

### 3. Открываем `app.py` в браузере

1. Вкладка **Files** наверху.
2. Откройте `app.py` — это сердце Space.
3. Найдите блок:

   ```python
   @tool
   def my_custom_tool(arg1: str, arg2: int) -> str:
       """A tool that does nothing yet

       Args:
           arg1: the first argument
           arg2: the second argument
       """
       return "What magic will you build ?"
   ```

   Это **заглушка-tool, которую вам предлагают заменить на своё**.

### 4. Заменяем заглушку на свой tool

Кликните на `app.py` → **Edit** (карандаш) → откроется web-редактор.

Возьмите любую идею и превратите её в tool. Несколько примеров «на
голову»:

```python
@tool
def reverse_string(text: str) -> str:
    """Развернуть строку задом наперёд.

    Args:
        text: исходная строка для разворота.
    """
    return text[::-1]
```

```python
@tool
def word_count(text: str) -> int:
    """Посчитать количество слов в тексте.

    Args:
        text: текст, в котором надо посчитать слова.
    """
    return len(text.split())
```

```python
@tool
def is_palindrome(text: str) -> bool:
    """Проверить, является ли строка палиндромом.

    Args:
        text: строка для проверки (регистр и пробелы игнорируются).
    """
    cleaned = "".join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]
```

Сразу после блока с tool'ом найдите строку:

```python
agent = CodeAgent(
    model=model,
    tools=[final_answer],  # <-- сюда добавляйте свои tools
    ...
)
```

И вставьте имя вашего tool'а:

```python
agent = CodeAgent(
    model=model,
    tools=[final_answer, reverse_string],  # <-- ваш tool здесь
    ...
)
```

**Важно:** `final_answer` оставляйте — без него агент не сможет
формально завершать ответ.

### 5. Коммитим изменения

Внизу web-редактора — поле **Commit message** и кнопка **Commit
changes to main**.

1. Напишите осмысленное сообщение, например `Add reverse_string tool`.
2. Commit.

Space увидит изменение → автоматически пересоберёт контейнер
(~1—2 минуты) → запустит новую версию.

### 6. Тестируем

1. Вернитесь на главную страницу Space — там Gradio-UI.
2. В чат-окне напишите задачу, использующую ваш tool:
   - `Разверни строку "Hugging Face"`
   - `Сколько слов в предложении "Я учусь делать агентов"?`
   - `Является ли "А роза упала на лапу Азора" палиндромом?`
3. Агент **сам поймёт**, что надо звать ваш tool, и вернёт результат.

Если что-то пошло не так — вкладка **Logs** сверху покажет
стек-трейс. 90% случаев — опечатка в типах или docstring.

## Сдача

Артефакт — публичная ссылка вида
`https://huggingface.co/spaces/<ваш-логин>/<имя-space>`.

В чат курса: `[Модуль 1.5, практика Spaces] {ссылка}`.

## Чек перед сдачей

- [ ] Space — **публичный** (открывается из инкогнито);
- [ ] `HF_TOKEN` прикреплён в Secrets, агент отвечает без ошибок;
- [ ] вы заменили `my_custom_tool` на свой собственный (не оставили
      «What magic will you build ?»);
- [ ] ваш tool реально вызывается на одном из ваших запросов
      (видно в **Logs** или в ответе агента).

## Что вы только что сделали

В терминологии курса вы:

- **Развернули свой агентный сервис** в публичную сеть. Без
  настройки Docker, без оплаты сервера, без CI/CD.
- **Подцепили tool в smolagents-агента** — поэтому в Модуле 10, когда
  будем разбирать smolagents глубоко, у вас уже будет рабочая площадка.
- **Получили публичный URL**, который можно показать друзьям как
  «вот мой first AI agent».

Это та же механика, которую дальше будем использовать в Модуле 16
(свой агент в игровом полигоне) и в финале курса (агент в игре).

## Источники

- [HF Agents Course — Unit 1 / Dummy Agent Tutorial](https://huggingface.co/learn/agents-course/unit1/tutorial) — оригинал этого упражнения.
- [`agents-course/First_agent_template`](https://huggingface.co/spaces/agents-course/First_agent_template) — Space-шаблон.
- [HF Spaces docs](https://huggingface.co/docs/hub/spaces) — общая документация.
