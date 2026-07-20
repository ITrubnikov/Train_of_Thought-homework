# MCP-серверы модуля 14.5

Эта папка — артефакт домашки модуля 14.5 «MCP: универсальный язык tool-сервера»: два MCP-сервера на FastMCP, которые разбирает [`notebook.ipynb`](../notebook.ipynb) (лежит на уровень выше). Серверы самодостаточны — их можно запускать и подключать к клиентам и без ноутбука.

## Файлы

| Файл | Что это |
| --- | --- |
| [`woodcutter_server.py`](woodcutter_server.py) | Учебный сервер лесоруба: мок-лес 5×5 из модуля 11.5 (чистый Python, без сети и ключей), tools `move` / `gather` / `deposit` с обучающими ошибками `{error: {code, message}}` и resource `woodcutter://map`. |
| [`cognopolis_mcp_server.py`](cognopolis_mcp_server.py) | MCP-обёртка живого игрового API [kindomklaster.com](https://kindomklaster.com): tools `move` (через `Literal` — честный enum в схеме) / `gather` / `get_character` / `get_map` плюс resource `cognopolis://map`. Карта нарочно отдана обоими примитивами — часть агентных клиентов умеет только tools. Отдельного `deposit` нет: шаг на дом `(0, 0)` сам сдаёт рюкзак (авто-банк). |
| [`requirements.txt`](requirements.txt) | Зависимости серверов для запуска вне ноутбука. |

Учебные варианты — `woodcutter_server_v2.py` (эксперимент «убери инструмент»), `woodcutter_server_stock.py`, `map_as_tool_server.py`, `cognopolis_mcp_server_v2.py` — появляются в этой папке после прогона ноутбука. Варианты Задач 1 и 3 импортируют канонические файлы (`from woodcutter_server import ...`) и обязаны лежать рядом с ними — потому всё и живёт в одной папке.

## Запуск (stdio)

Нужен **Python 3.10+** — требование `fastmcp` (системный python3 на macOS — 3.9, не подойдёт; запасной путь — `uv venv --python 3.11`).

```bash
pip install -r requirements.txt

# мок-лес: без ключей и без сети
python woodcutter_server.py

# живой сервер: под-токен жителя ТОЛЬКО через переменную окружения
COGNOPOLIS_TOKEN=<под-токен> python cognopolis_mcp_server.py
```

`mcp.run()` без аргументов поднимает транспорт stdio: сервер молча ждёт JSON-RPC-сообщения в stdin. Это нормально — руками его запускают редко: обычно это делает сам клиент, подпроцессом. Под-токен жителя копируется в интерфейсе игры на экране «Жители»; в код, в протокол и в git он попадать не должен — только окружение или `getpass`.

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
    env={**os.environ},   # COGNOPOLIS_TOKEN уже должен лежать в окружении
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
claude mcp add cognopolis --env COGNOPOLIS_TOKEN=<под-токен> -- python cognopolis_mcp_server.py
```

Claude Desktop и Cursor подключаются той же парой «команда + аргументы» в конфиге (`claude_desktop_config.json` → `mcpServers`); готовый фрагмент с абсолютными путями собирает ячейка Задачи 4 в ноутбуке.
