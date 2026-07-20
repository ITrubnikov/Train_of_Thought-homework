# MCP-серверы модуля 14.5

Эта папка — артефакт домашки модуля 14.5 «MCP: универсальный язык tool-сервера»: два MCP-сервера на FastMCP, которые разбирает [`notebook.ipynb`](../notebook.ipynb) (лежит на уровень выше). Серверы самодостаточны — их можно запускать и подключать к клиентам и без ноутбука.

## Файлы

| Файл | Что это |
| --- | --- |
| [`woodcutter_server.py`](woodcutter_server.py) | Учебный сервер лесоруба: мок-лес 5×5 из модуля 11.5 (чистый Python, без сети и ключей), tools `move` / `gather` / `deposit` с обучающими ошибками `{error: {code, message}}` и resource `woodcutter://map`. |
| [`cognopolis_mcp_server.py`](cognopolis_mcp_server.py) | MCP-обёртка живого игрового API [kindomklaster.com](https://kindomklaster.com): tools `move` (через `Literal` — честный enum в схеме) / `gather` / `get_character` / `get_map` плюс resource `cognopolis://map`. Карта нарочно отдана обоими примитивами — часть агентных клиентов умеет только tools. Отдельного `deposit` нет: шаг на дом `(0, 0)` сам сдаёт рюкзак (авто-банк). |
| [`requirements.txt`](requirements.txt) | Зависимости серверов для запуска вне ноутбука. |
| [`.env-example`](.env-example) | Шаблон для `.env`: скопируйте, впишите под-токен жителя — живой сервер подхватит его сам. Сам `.env` закрыт `.gitignore`-ом и в git не попадает. |

Учебные варианты — `woodcutter_server_v2.py` (эксперимент «убери инструмент»), `woodcutter_server_stock.py`, `map_as_tool_server.py`, `cognopolis_mcp_server_v2.py` — появляются в этой папке после прогона ноутбука. Варианты Задач 1 и 3 импортируют канонические файлы (`from woodcutter_server import ...`) и обязаны лежать рядом с ними — потому всё и живёт в одной папке.

## Запуск (stdio)

Нужен **Python 3.10+** — требование `fastmcp` (системный python3 на macOS — 3.9, не подойдёт).

```bash
# окружение (один раз)
uv venv --python 3.11 .venv        # или python3 -m venv .venv, если python3 >= 3.10
source .venv/bin/activate
pip install -r requirements.txt

# токен (один раз): скопируйте шаблон и впишите под-токен своего жителя
cp .env-example .env

# мок-лес: без ключей, без сети и без .env
python woodcutter_server.py

# живой сервер: токен возьмётся из .env
python cognopolis_mcp_server.py
```

### Прод или локальная игра

Живой сервер ходит в тот мир, который назван в `COGNOPOLIS_BASE_URL`; по умолчанию это живая игра `https://kindomklaster.com`, и менять ничего не нужно. Если же у вас запущен локальный движок игры — впишите в `.env` строку `COGNOPOLIS_BASE_URL=http://localhost:8000` (в `.env-example` она уже есть закомментированной), и обёртка целиком переключится на него: контракт tools, клиенты и их конфиги не меняются вовсе — это тот же трюк «меняется провод, не контракт», что и с транспортом.

Одна гоча: **под-токен должен быть из того же мира**. У локальной игры свои жители и свои токены (копируются на её экране «Жители», как и на проде) — прод-токен против локального движка даст `invalid_token`, и наоборот. Переключая `COGNOPOLIS_BASE_URL`, меняйте и `COGNOPOLIS_TOKEN`.

`mcp.run()` без аргументов поднимает транспорт stdio: сервер молча ждёт JSON-RPC-сообщения в stdin. Это нормально — руками его запускают редко: обычно это делает сам клиент, подпроцессом. Под-токен жителя копируется в интерфейсе игры на экране «Жители» и живёт в `.env` (файл закрыт `.gitignore`-ом) либо в переменной окружения `COGNOPOLIS_TOKEN` — настоящее окружение важнее `.env`, так клиент может передать токен подпроцессу, не трогая файл. В код, в протокол и в git токен попадать не должен.

## Как подключить клиентов

**fastmcp-клиент** (Python, сам поднимет stdio-подпроцесс по пути к файлу):

```python
from fastmcp import Client

async with Client("woodcutter_server.py") as client:
    print(sorted(t.name for t in await client.list_tools()))
```

**smolagents** — `ToolCollection.from_mcp`; токен уходит подпроцессу через `env`, не через протокол:

```python
import os, sys
from mcp import StdioServerParameters
from smolagents import ToolCollection

params = StdioServerParameters(
    command=sys.executable,
    args=["cognopolis_mcp_server.py"],
    env={**os.environ},   # токен: из вашего окружения, а если там нет — сервер возьмёт из .env
)
with ToolCollection.from_mcp(params, trust_remote_code=True) as tc:
    print(sorted(t.name for t in tc.tools))
```

**MCP Inspector** — отладочный клиент от авторов протокола (нужен Node.js для `npx`):

```bash
npx -y @modelcontextprotocol/inspector --cli python woodcutter_server.py --method tools/list
```

**Claude Code** — одной командой на сервер:

```bash
claude mcp add woodcutter -- python woodcutter_server.py
claude mcp add cognopolis -- python cognopolis_mcp_server.py   # токен возьмётся из .env
```

Если `.env` не заполняли, токен можно передать и напрямую:
`claude mcp add cognopolis --env COGNOPOLIS_TOKEN=<под-токен> -- python cognopolis_mcp_server.py`.

Claude Desktop и Cursor подключаются той же парой «команда + аргументы» в конфиге (`claude_desktop_config.json` → `mcpServers`); готовый фрагмент с абсолютными путями собирает ячейка Задачи 4 в ноутбуке.
