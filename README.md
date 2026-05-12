# Train_of_Thought — homework

Этот репозиторий — рабочая папка для домашек курса
**«От нуля до своих агентов»** ([itrubnikov.github.io/Train_of_Thought](https://itrubnikov.github.io/Train_of_Thought/)).

Здесь живёт всё, что вы будете запускать руками:

- `notebooks/` — заранее подготовленные Jupyter-ноутбуки, в основном под
  Kaggle. Каждый ноутбук привязан к конкретному модулю курса (см. таблицу
  ниже).
- На корневом уровне будут появляться шаблоны под более поздние ДЗ
  (промпт-файлы, JSON-схемы, MCP-серверы для игры).

Все ноутбуки рассчитаны на бесплатный тариф **Kaggle Notebooks** + ключ
**Google AI Studio** (тоже бесплатный). Никакой подписки покупать не
надо.

---

## Зачем мне Kaggle, если у меня есть свой ноутбук?

Короткий ответ: чтобы не настраивать у себя CUDA, не выбирать Python-версию,
не платить за GPU и не отправлять чужой ключ из своего терминала.

Длинный — три причины:

1. **Бесплатный GPU.** Kaggle даёт верифицированным аккаунтам ~30 часов
   GPU T4 (×2) в неделю. На локальной машине без видеокарты это
   единственный реалистичный способ что-то поучить или прогнать
   inference open-weights модели типа 7B.
2. **Воспроизводимая среда.** Python, основные библиотеки и драйверы
   уже стоят. Если у вас не работает — у проверяющего тоже не работает.
   На локалке — наоборот: «у меня же запустилось» в чистом виде.
3. **Secrets для API-ключей.** Kaggle хранит ваши ключи (Gemini, HF,
   OpenAI) в зашифрованном виде и подсовывает их в ноутбук одним вызовом
   `UserSecretsClient().get_secret(...)`. Это значит, что (а) ключ никогда
   не попадает в код и (б) когда вы делаете ноутбук публичным — он там
   не светится.

Если у вас уже есть Colab Pro / своя GPU-машина / VS Code with remote SSH —
можно запускать локально, просто игнорируя ячейки с `kaggle_secrets`
и подставляя ключ через `os.environ`. Но дефолт курса — Kaggle, и
все инструкции в лекциях написаны под него.

---

## Как этим пользоваться (общий workflow)

1. **Сделайте форк этого репозитория** (кнопка **Fork** справа сверху на
   GitHub). Все ваши решения вы будете коммитить в свой форк.
2. **Зарегистрируйтесь на Kaggle** и подтвердите телефон (обязательно для
   GPU и Secrets) — [kaggle.com/settings](https://www.kaggle.com/settings).
3. **Выпустите ключ Gemini** на [aistudio.google.com](https://aistudio.google.com/)
   → *Get API key* → положите его в Kaggle Secrets с именем
   `GOOGLE_API_KEY` (`Add-ons` → `Secrets` → `Add a new secret` → галочка
   *Attach to notebook*).
4. **Загрузите нужный ноутбук в Kaggle**:
   - Способ A — через Kaggle UI: `Create` → `New Notebook` → `File` →
     `Import Notebook` → выберите `.ipynb` из своего форка (скачать его
     с GitHub можно одной кнопкой «Download raw»).
   - Способ B — оригинал с Kaggle Code: открываете
     [Kaggle 5-Day GenAI Intensive](https://www.kaggle.com/learn-guide/5-day-genai),
     находите соответствующий день, жмёте **Copy and Edit**. Так у вас
     сразу будет редактируемая копия со всеми ссылками на изображения и
     `kaggle_secrets`.
5. **Прогоните ноутбук сверху вниз.** В каждом блоке, где написано
   *«поменяйте промпт на свой»* — действительно меняйте. Без этого
   ДЗ не считается.
6. **Опубликуйте ноутбук** (`Share` → `Public`) и пришлите ссылку в чат
   курса как `[Модуль N, ДЗ M] {ссылка}`.

Параллельно сохраните финальную версию `.ipynb` в свой форк репозитория
(в `solutions/module-N/` или просто рядом с оригиналом — на ваше
усмотрение). Это страховка: если Kaggle когда-нибудь поломает ваш
аккаунт, у вас всё ещё будет код.

---

## Карта ноутбуков → модулей

Ноутбуки разделены на две группы.

### Наши playbook'и (живая практика на занятии)

| Ноутбук | Модуль курса | Когда использовать |
| --- | --- | --- |
| [`notebooks/playbooks/kaggle-tour.ipynb`](notebooks/playbooks/kaggle-tour.ipynb) | [Модуль 1.5 — Где живёт современный ИИ](https://itrubnikov.github.io/Train_of_Thought/docs/modules/01-5-modern-tools/) | Пошаговая демонстрация Kaggle: phone verify, GPU, Secrets, первый запрос к Gemini. ~25 мин. |
| [`notebooks/playbooks/huggingface-tour.ipynb`](notebooks/playbooks/huggingface-tour.ipynb) | [Модуль 1.5 — Где живёт современный ИИ](https://itrubnikov.github.io/Train_of_Thought/docs/modules/01-5-modern-tools/) | Пошаговая демонстрация HF: Hub, model card, `pipeline`, `load_dataset`, Spaces. ~20 мин. |

Эти ноутбуки — наши собственные, под MIT. Сгенерированы из
`notebooks/playbooks/_build.py`; чтобы поправить контент — правьте `.py`,
запускайте `python3 _build.py`, коммитьте оба файла вместе.

### Адаптации Kaggle 5-Day GenAI Intensive

| Ноутбук | Модуль курса | Что вы делаете |
| --- | --- | --- |
| [`notebooks/kaggle-5day-genai/day-1-prompting.ipynb`](notebooks/kaggle-5day-genai/day-1-prompting.ipynb) | [Модуль 1.5 — Где живёт современный ИИ](https://itrubnikov.github.io/Train_of_Thought/docs/modules/01-5-modern-tools/) | Первое касание Gemini API, базовые параметры (temperature, top-p), zero/few-shot, CoT, ReAct. |
| [`notebooks/kaggle-5day-genai/day-2-embeddings.ipynb`](notebooks/kaggle-5day-genai/day-2-embeddings.ipynb) | [Модуль 7 — RAG](https://itrubnikov.github.io/Train_of_Thought/docs/modules/07-rag/) | Эмбеддинги через `text-embedding-004`, cosine similarity, тепловая карта похожести. Это основание для всего RAG. |
| [`notebooks/kaggle-5day-genai/day-3-function-calling.ipynb`](notebooks/kaggle-5day-genai/day-3-function-calling.ipynb) | [Модуль 8 — Что такое агент](https://itrubnikov.github.io/Train_of_Thought/docs/modules/08-what-is-agent/) | Первый «настоящий» агент: Gemini + 3 функции над SQLite + автоматический tool-calling loop. |

Эти три ноутбука — модифицированные копии материалов
[Kaggle 5-Day GenAI Intensive](https://www.kaggle.com/learn-guide/5-day-genai)
от Google, под Apache 2.0 (см. шапки самих ноутбуков). Все правки и
довески — наши.

---

## Подводные камни (которые поймает каждый второй)

- **`No user secrets exist for kernel id ...`** — секрет добавлен в
  аккаунт, но не *прикреплён* к ноутбуку. В `Add-ons` → `Secrets` рядом
  с именем секрета должна стоять галка «Attach to notebook».
- **`User location is not supported`** в ответе Gemini API — выпустите
  ключ из-под VPN или из самого Kaggle-ноутбука (Google видит запрос с
  серверов GCP и обычно его пропускает).
- **GPU не виден в ноутбуке** — справа в `Notebook options` →
  `Accelerator` переключите на `GPU T4 x2`. Доступно только после phone
  verify.
- **Перед публикацией не убрали отладочные принты ключа** — нажмите
  `Run All` после удаления, чтобы вывод обновился, и только потом
  `Share` → `Public`. Раскрытый ключ — это автоматический счёт «за
  чужие эксперименты».

---

## Лицензия

Код в этом репозитории — под MIT (см. [LICENSE](./LICENSE)). Ноутбуки
из `notebooks/kaggle-5day-genai/` — под их оригинальной Apache 2.0
лицензией от Google, копия лицензии есть в первой ячейке каждого
ноутбука.
