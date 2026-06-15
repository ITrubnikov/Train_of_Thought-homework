---
title: My First Agent 10.7
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
short_description: smolagents-агент с инструментами в чате на HF Spaces
---

# My First Agent — модуль 10.7

Готовая HF Space-заготовка к [Модулю 10.7: Деплой агента](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-7-deploy-agent/). smolagents-агент с двумя инструментами (`word_count`, `c_to_f`), обёрнутый в чат через `GradioUI`. Открывайте чат и просите агента посчитать слова или перевести температуру — он сам выберет нужный инструмент и покажет ход рассуждения.

## Как развернуть и тестить

### Вариант A — создать Space из этих файлов
1. huggingface.co → **New → Space**, SDK — **Gradio**.
2. Загрузите `app.py`, `requirements.txt`, `README.md` (через *Files → Add file* или `git push` в репозиторий Space).
3. **Settings → Variables and secrets → New secret**: `HF_TOKEN` = бесплатный токен (huggingface.co → Settings → Access Tokens, роль `read`).
4. Space соберётся сам → открывайте чат.

### Вариант B — Duplicate (когда Space опубликован)
**⋮ → Duplicate this Space**, добавьте свой секрет `HF_TOKEN`.

### Вариант C — локально
```bash
pip install -r requirements.txt
export HF_TOKEN=hf_...
python app.py     # откроется http://127.0.0.1:7860
```

## Сделайте своим (домашка 10.7)
Добавьте свой `@tool` — обычную функцию с докстрингом (описание + секция `Args`, по ним smolagents строит описание инструмента) — и впишите её в `tools=[...]`. Например:

```python
@tool
def reverse(text: str) -> str:
    """Переворачивает строку задом наперёд.

    Args:
        text: строка для разворота.
    """
    return text[::-1]
```

## Грабли (из лекции 10.7)
- **`sdk_version` только 5.x.** gradio 4.x падает на Python 3.13 (`ModuleNotFoundError: audioop`), на котором HF собирает Spaces.
- **Нет секрета `HF_TOKEN` → агент молчит.** Ключ всегда секретом, никогда в `app.py`.
- **CodeAgent исполняет сгенерированный моделью код.** Для недоверенных входов нужен sandbox (E2B/Docker) — см. модуль 9.5 и доку smolagents про secure code execution.
- **Free Space засыпает** — первый ответ после простоя идёт дольше; каждый вызов тратит бесплатные кредиты HF Inference.

## Модель
По умолчанию `Qwen/Qwen2.5-Coder-32B-Instruct` (CodeAgent пишет код, coder-модель подходит). Если недоступна/кончились кредиты — впишите другую из [hf.co/models?inference=warm](https://huggingface.co/models?inference=warm) в `InferenceClientModel(model_id=...)`.
