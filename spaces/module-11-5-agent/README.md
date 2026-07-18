---
title: Lumberjack Agent 11.5
emoji: 🪓
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
short_description: Лесоруб из Модуля 11.5 — хорошие tools в чате на HF Spaces
---

# Лесоруб — Приложение А к Модулю 11.5

Готовая HF Space-заготовка к домашке [Модуля 11.5: Дизайн инструментов](https://itrubnikov.github.io/Train_of_Thought/docs/modules/11-5-tool-design/). Тот же хороший набор tools, что вы собрали в ноутбуке, — `move`, `gather`, `deposit`, `get_map` с `enum` в схеме, обучающими ошибками `{code, message}` и конвертом `{result, cooldown, state}` — отдан живой модели через `ToolCallingAgent` и обёрнут в чат `GradioUI` по механике [Модуля 10.7: Деплой агента](https://itrubnikov.github.io/Train_of_Thought/docs/modules/10-7-deploy-agent/). Напишите агенту в чате: «Добудь одно дерево и сдай его на склад» — и смотрите, как контракт ведёт модель к цели.

## Как развернуть

### Вариант A — создать Space из этих файлов
1. huggingface.co → **New → Space**, SDK — **Gradio**.
2. Загрузите `app.py`, `requirements.txt`, `README.md` (через *Files → Add file* или `git push` в репозиторий Space).
3. **Settings → Variables and secrets → New secret**: `HF_TOKEN` = бесплатный токен (huggingface.co → Settings → Access Tokens, роль `read`).
4. Space соберётся сам → откройте чат и дайте агенту задачу лесоруба.

### Вариант B — локально
```bash
pip install -r requirements.txt
export HF_TOKEN=hf_...
python app.py     # откроется http://127.0.0.1:7860
```

## Модель
`app.py` вызывает `InferenceClientModel()` без аргументов — в smolagents 1.26.0 это `Qwen/Qwen3-Next-80B-A3B-Thinking`: умная, но заметно дороже по кредитам, чем 7B-coder из Модуля 10.7. Хотите экономнее, модель недоступна или кончились кредиты — впишите другую из [hf.co/models?inference=warm](https://huggingface.co/models?inference=warm): `InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-7B-Instruct")`.

## Подводные камни
- **`sdk_version` только 5.x.** gradio 4.x падает на Python 3.13 (`ModuleNotFoundError: audioop`), на котором HF собирает Spaces.
- **Нет секрета `HF_TOKEN` → агент молчит.** Токен только в секрете, никогда в `app.py`.
- **Бесплатный Space засыпает** — первый ответ после простоя идёт дольше; каждый вызов агента тратит бесплатные кредиты HF Inference.
- **`max_steps=12` в `app.py` бережёт квоту**: даже заблудившийся агент не сделает больше 12 шагов за задачу.
- **Лес общий на процесс.** `Forest` — глобальный объект: все, кто откроет чат, играют в одном лесу. Для учебного демо это нормально.
