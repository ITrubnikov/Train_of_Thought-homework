# Модуль 14.5 — MCP: универсальный язык tool-сервера, своими руками

Домашка к Модулю 14.5 «MCP: универсальный язык tool-сервера» — лекция на сайте курса.

Здесь вы выносите контракт лесоруба из [модуля 11.5](https://github.com/ITrubnikov/Train_of_Thought-homework/tree/main/notebooks/module-11-5-tool-design) в отдельный MCP-сервер — и смотрите на него глазами клиентов. Мир достаётся в наследство: тот же мок-лес (сетка 5×5, узлы дерева и камня, рюкзак на 5, склад, кулдаун — чистый Python без сети) и финальный «хороший» набор `move` / `gather` / `deposit` / `get_map`. Новое — уровень выше: контракт перестаёт быть кодом внутри проекта и становится сервисом. Вы разбираете и запускаете сервер-файл на FastMCP (tools плюс resource `woodcutter://map`) — настоящий файл в папке `mcp-server/`, — делаете discovery руками (`tools/list`, `resources/list`, `tools/call` поверх JSON-RPC), поднимаете его stdio-подпроцессом, проверяете эксперимент «убери инструмент», подключаете два клиента — свой smolagents-агент через `ToolCollection.from_mcp` и клиент, который вы не писали (MCP Inspector / Claude Code), — а в живой части оборачиваете в MCP настоящий игровой API Cognopolis и отправляете агента управлять своим жителем. На выходе — рабочий MCP-сервер, инструменты которого видны из двух разных клиентов.

## Что нужно сделать до начала

- **API-ключи не нужны.** Ядро (Блоки 1–3, Задачи 1–2 и discovery-часть Задачи 3) работает целиком без ключей и без сети к игре; интернет нужен один раз — поставить библиотеки.
- **Python 3.10+** — требование `fastmcp`. В Colab/Kaggle это уже так; локально проверьте `python --version` (системный python3 на macOS — 3.9, не подойдёт) и при нужде создайте свежее окружение, например `uv venv --python 3.11`.
- Аккаунт Colab или Kaggle — или локальный Python. GPU не нужен.
- Желательно — прочитать лекцию 14.5 и пройти практику 11.5 (контракт лесоруба) и [13.6](https://github.com/ITrubnikov/Train_of_Thought-homework/tree/main/notebooks/module-13-6-skills) (тот же мок-лес): сервер этого модуля оборачивает ровно их наследство.
- Опционально, для Блоков 4–5: локальный OpenAI-совместимый сервер модели из Модулей 6.1/6.2 — LM Studio (порт 1234) или Ollama (порт 11434) с instruct-моделью, умеющей tool calling (например, `qwen2.5:7b`). Токенов не нужно; без запущенного сервера блоки делают мягкий пропуск.
- Опционально, для Блока 5 и живой части Задачи 3: **под-токен жителя** Cognopolis — копируется в интерфейсе игры на экране «Жители» (или тестовый аккаунт, если преподаватель дал доступ). Токен передаётся только через переменную окружения `COGNOPOLIS_TOKEN` или `getpass` — никогда текстом в ячейке.
- Для Блока 6 и Задачи 4 — клиент, который вы не писали: MCP Inspector (нужен Node.js для `npx`), Claude Code, Claude Desktop или Cursor. Эти шаги делаются в терминале на вашей машине и проверяются там же.

## Файлы в папке

| Файл | Зачем |
| --- | --- |
| [`notebook.ipynb`](notebook.ipynb) | Рабочий ноутбук (`Run all` проходит целиком keyless, 0 ошибок). Симптом M×N, разбор MCP-сервера лесоруба на FastMCP, discovery и вызовы через fastmcp-клиент (in-process и stdio), эксперимент «убери инструмент», smolagents-клиент через `ToolCollection.from_mcp`, MCP-обёртка живого игрового API, секция «Задачи». Каждая ячейка печатает результат. |
| [`mcp-server/`](mcp-server/) | Папка серверов — артефакт модуля. Пути к ней ноутбук держит в `SERVER_DIR` (ячейка «Файлы урока»); эти же файлы вы подключаете к Inspector и Claude Code в Блоке 6 и Задаче 4. |
| [`mcp-server/woodcutter_server.py`](mcp-server/woodcutter_server.py) | Канонический MCP-сервер лесоруба: мок-лес 5×5 из 11.5, tools `move` / `gather` / `deposit` с обучающими ошибками, resource `woodcutter://map`. Без ключей и сети. |
| [`mcp-server/cognopolis_mcp_server.py`](mcp-server/cognopolis_mcp_server.py) | MCP-обёртка живого API kindomklaster.com: `move` через `Literal` (честный enum в схеме), карта и tool-ом, и resource-ом, авто-банк на доме вместо `deposit`. Под-токен — только из env `COGNOPOLIS_TOKEN`. |
| [`mcp-server/README.md`](mcp-server/README.md) | Как запустить серверы по stdio и подключить клиентов (fastmcp, smolagents, Inspector, Claude Code) без ноутбука. |
| [`mcp-server/requirements.txt`](mcp-server/requirements.txt) | Зависимости серверов (`fastmcp`, `requests`) для запуска вне ноутбука. |

Учебные варианты (`woodcutter_server_v2.py`, `woodcutter_server_stock.py`, `map_as_tool_server.py`, `cognopolis_mcp_server_v2.py`) ноутбук пишет в ту же папку `mcp-server/` по ходу прогона — варианты Задач 1 и 3 импортируют канонические файлы и обязаны лежать рядом с ними.

Рядом в репозитории — [`spaces/module-14-5-agent/`](../../spaces/module-14-5-agent/): готовый локальный чат-агент на **живой игре Cognopolis** (LM Studio + под-токен жителя), максимально близкий к уроку. Ключевая разница с зеркалами 11.5 и 13.6: в файле агента нет ни одного определения игрового tool — инструменты приезжают из вашего `cognopolis_mcp_server.py` через `ToolCollection.from_mcp` (сервер стартует stdio-подпроцессом, под-токен уходит ему через env). Раньше tools были кодом самого файла агента; теперь их отдаёт MCP-сервер, и файл агента про инструменты не знает ничего.

## Что вы делаете в ноутбуке (`Run all` проходит целиком)

1. **Блок 1 (ядро, keyless) — симптом M×N.** Наследство 11.5 упирается в потолок: под каждого клиента — своя обвязка, а Claude Desktop и Cursor не подключить вовсе (дерево клиентов из лекции). M клиентов × N сервисов превращается в M + N, когда контракт выносится в сервис, — это и есть главный термин лекции.
2. **Блок 2 (ядро, keyless) — свой MCP-сервер.** Готовый файл `mcp-server/woodcutter_server.py`: тот же мок-лес и контракт tools `move` / `gather` / `deposit` с обучающими ошибками, плюс карта правильным примитивом — resource `woodcutter://map`; ноутбук печатает ключевые фрагменты через `Path.read_text`, целиком файл читаете в папке. Дальше in-process fastmcp-клиент: `tools/list` со схемами, собранными из type hints и docstring, `resources/list`, пустой `prompts/list`, цепочка `call_tool` со всеми обучающими ошибками (`no_resource_here`, `at_map_edge`, `unknown_direction`, `on_cooldown`) и `read_resource`. Разбор трёх примитивов: tool — действие (`POST`), resource — чтение (`GET`), prompt — шаблон-процедура от сервера.
3. **Блок 3 (ядро, keyless) — транспорт и discovery.** `Client("woodcutter_server.py")` поднимает сервер stdio-подпроцессом: каталог тот же, мир свежий. Эксперимент «убери инструмент» (шаг 5 домашки лекции): ноутбук кодом генерирует из канонического файла `mcp-server/woodcutter_server_v2.py` без `deposit` (`read_text` → вырезать функцию → `write_text`) — и действие пропадает из `tools/list` без единой правки на стороне клиента. Плюс короткий разбор JSON-RPC 2.0 под капотом.
4. **Блок 4 (опционально, нужен локальный сервер) — клиент №1: smolagents.** `ToolCollection.from_mcp(StdioServerParameters(...), trust_remote_code=True)` на мок-сервере, локальная модель (автодетект LM Studio/Ollama, мягкий пропуск) — агент рубит мок-лес через MCP; факт-чек вызовов по `agent.memory.steps`. Попутно — трейд-офф вживую: `from_mcp` умеет только tools, resource-карта до агента не доезжает.
5. **Блок 5 (опционально, нужны под-токен и локальный сервер) — живая игра.** Готовый файл `mcp-server/cognopolis_mcp_server.py` — MCP-обёртка живого API kindomklaster.com: `move` с `Literal` (честный enum в схеме), карта и tool-ом, и resource-ом, авто-банк рюкзака на доме `(0, 0)` вместо `deposit`. Прямой Client-чек (`get_character`, resource `cognopolis://map`), затем агент: «Добудь одно дерево (wood) и вернись домой» — факт-чек по `stored.wood` до/после.
6. **Блок 6 — клиент №2, который вы не писали.** MCP Inspector CLI (`npx -y @modelcontextprotocol/inspector --cli python mcp-server/woodcutter_server.py --method tools/list`) и Claude Code (`claude mcp add woodcutter -- python mcp-server/woodcutter_server.py`; для живого — `claude mcp add cognopolis --env COGNOPOLIS_TOKEN=... -- python mcp-server/cognopolis_mcp_server.py`). Критерий из лекции: те же инструменты видны из двух клиентов.
7. **Задачи** в конце: второй resource `woodcutter://stock` и его появление в `resources/list`; карта, нарочно оформленная tool-ом, — что теряется (GET против POST) и почему живой сервер держит оба примитива; новый узкий tool `get_events` для живого сервера и discovery без правок клиента; мостик — свой сервер в конфиге Claude Desktop / Claude Code. Задачи 1–2 и discovery Задачи 3 — keyless; каждая содержит рабочий образец, который вы меняете под себя.

## Как запустить

### Вариант A — Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-14-5-mcp/notebook.ipynb)

Нажмите бейдж, затем `Runtime → Run all`. Первая ячейка сама поставит `fastmcp`, `smolagents[mcp]` и `openai`; следом ячейка «Файлы урока» заметит, что папки `mcp-server/` рядом нет (в Colab ноутбук приезжает одним файлом), и сама скачает серверные файлы raw-ссылками из репозитория. Ключи не нужны — ядро keyless. Блоки 4–5 в Colab мягко пропустятся: им нужны локальный сервер модели и под-токен, которых в облачном ноутбуке нет, — для живых прогонов запускайте вариант C.

### Вариант B — Kaggle

1. Зайдите на [kaggle.com](https://www.kaggle.com/) → `Create → New Notebook`.
2. `File → Import Notebook → URL`, вставьте raw-ссылку: `https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-14-5-mcp/notebook.ipynb`.
3. **Включите интернет:** `Notebook options → Internet → On` (нужен phone-verified аккаунт) — иначе первая ячейка не сможет поставить библиотеки. Accelerator оставьте `None`, CPU достаточно.
4. `Run All`. Ячейка «Файлы урока» сама скачает серверные файлы в `mcp-server/` raw-ссылками (интернет уже включён на шаге 3). Блоки 4–5 в Kaggle мягко пропустятся (нужны локальный сервер модели и под-токен) — для живых прогонов запускайте вариант C.

### Вариант C — локально

```bash
git clone https://github.com/ITrubnikov/Train_of_Thought-homework.git
cd Train_of_Thought-homework/notebooks/module-14-5-mcp
python3 -m venv .venv && source .venv/bin/activate   # python3 --version должен быть 3.10+
# если системный python старее (на macOS это 3.9) - запасной путь: uv venv --python 3.11
pip install jupyter fastmcp "smolagents[mcp]" openai
jupyter lab notebook.ipynb
```

GPU не нужен — keyless-прогон отрабатывает за пару минут (паузы — честные ожидания кулдауна). `requests` приезжает вместе со `smolagents`; `openai` нужен `OpenAIServerModel` в Блоках 4–5 — smolagents сам его не тянет. Для Блока 5 задайте под-токен до запуска Jupyter (`export COGNOPOLIS_TOKEN=...`) или включите `ASK_TOKEN = True` в ячейке токена.

## ДЗ к модулю

Артефакт домашки — **рабочий MCP-сервер, инструменты которого видны из двух разных клиентов**: вашего (smolagents) и того, который вы не писали (Inspector / Claude Code / Claude Desktop). Критерии приёма — из лекции, всё проверяется без преподавателя:

- [ ] Ноутбук прогнан целиком (`Run all`) keyless без ошибок.
- [ ] Сервер поднимается по stdio и отдаёт `tools/list`; хотя бы одно чтение оформлено как resource, а не tool (Блоки 2–3).
- [ ] Одни и те же инструменты видны из smolagents (`ToolCollection.from_mcp`, Блок 4) **и** из клиента, который вы не писали (Блок 6 / Задача 4).
- [ ] Удаление инструмента отражается в `tools/list` без правок на стороне клиента (Блок 3).
- [ ] **Задача 1.** Второй resource `woodcutter://stock` появился в `resources/list`.
- [ ] **Задача 2.** Карта оформлена tool-ом, потеря разделения GET/POST увидена и объяснена, канонический сервер остался с картой-resource.
- [ ] **Задача 3.** Новый узкий tool живого сервера (например, `get_events`) виден клиенту через discovery без правок на его стороне.
- [ ] **Задача 4.** Свой сервер прописан в Claude Code / Claude Desktop, инструменты появились в интерфейсе.

Артефакт для сдачи — публичная ссылка на прогнанный ноутбук, в чат курса как `[Модуль 14.5, ДЗ] {ссылка}`.

## Спецификация MCP

Протокол живёт и меняется: на момент курса стабильная ревизия — `2025-11-25` (три примитива сервера, транспорты stdio и Streamable HTTP, JSON-RPC 2.0), в release-candidate `2026-07-28` базовый слой делают stateless. Неизменным остаётся ядро, которое вы собрали в этом ноутбуке, — примитивы, discovery и «контракт, вынесенный в сервис». Сверяйтесь с первоисточником: [спецификация](https://modelcontextprotocol.io/specification) и [обзор архитектуры](https://modelcontextprotocol.io/docs/learn/architecture) (роли host / client / server) на modelcontextprotocol.io.

## Подводные камни

- **Первая ячейка требует интернета и Python 3.10+.** Библиотеки ставятся с PyPI; в Kaggle без `Internet → On` установка молча не пройдёт. Версию Python ячейка проверяет сама и честно падает с подсказкой, если интерпретатор старее 3.10.
- **Серверные файлы живут в папке `mcp-server/` рядом с ноутбуком.** `Client(...)` и `StdioServerParameters` получают пути через `SERVER_DIR` из ячейки «Файлы урока»; она же скачает `woodcutter_server.py` и `cognopolis_mcp_server.py` raw-ссылками из репозитория, если папки нет (так происходит в Colab/Kaggle). Перенесли ноутбук — перенесите папку вместе с ним или дайте ячейке скачать файлы заново. Учебные варианты ноутбук пишет туда же: файлы Задач 1 и 3 импортируют канонические серверы и обязаны лежать рядом с ними.
- **In-process и stdio — разные миры.** In-process клиент делит `forest` с ноутбуком (карта видит ваши ходы), stdio-подпроцесс каждый раз поднимает свежий мир. Это не баг, а наглядная разница между «объект в моём процессе» и «отдельный сервер».
- **`ToolCollection.from_mcp` умеет только tools.** Resources до smolagents-агента не доезжают — потому в мок-блоке карта уходит в instructions, а живой сервер держит карту и tool-ом, и resource-ом. Осознанный трейд-офф из лекции, в ноутбуке он проговаривается дважды.
- **Токен — только env или getpass.** Флаг `ASK_TOKEN` в Блоке 5 по умолчанию `False`, чтобы `Run all` не замирал на вводе; поставьте `True` или задайте `COGNOPOLIS_TOKEN` в окружении. Токен не печатается и не сохраняется в ноутбуке — проследите, чтобы так и осталось в сдаваемой версии.
- **Живой мир держит ритм.** Кулдаун ~1 секунда; ранний повтор отвечает `character_on_cooldown` с точным временем ожидания — это правило дано агенту в instructions, без него он спамит. Возврат на дом `(0, 0)` сам сдаёт рюкзак (поле `banked` в ответе `move`) — отдельного `deposit` в живом мире нет.
- **Добыча за раз может быть больше 1.** Если на складе поселения лежат инструменты (например, топор), `gather` приносит больше — инструменты общие. Факт-чек Блока 5 потому сверяет дельту `stored.wood`, а не «ровно +1».
- **Блоки 4–5 без сервера модели и токена — это норма.** Ячейки печатают причину и мягко пропускаются, keyless-прогон остаётся зелёным. В Colab/Kaggle они пропускаются всегда.
- **MCP Inspector требует Node.js.** `npx -y @modelcontextprotocol/inspector` скачает клиент сам, но `npx` приезжает с Node. Это шаг в терминале вашей машины, не ячейка ноутбука.

## Лицензия

Код — MIT (см. [LICENSE](../../LICENSE) в корне репо). Мир, tools, коды ошибок и форма конверта совпадают с модулями 11.5/13.6 и учебной игрой Cognopolis; термины (три примитива, транспорт, discovery, «контракт, вынесенный в сервис») — с лекцией модуля 14.5 (часть курса «От нуля до своих агентов»).
