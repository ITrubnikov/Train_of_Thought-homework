# Модуль 5.1 — Публикуем модель на HuggingFace Hub

Два ноутбука к [уроку 5.1](https://itrubnikov.github.io/Train_of_Thought/docs/modules/05-1-publish-model/).

## Как запустить

- **`notebook.ipynb`** — демо: берём готовую `HOhus/pushkin-nano-bpe` и публикуем
  под своим именем. Бонус-шаг (Шаг 4) — конвертация в GGUF и заливка
  `<username>/pushkin-nano-bpe-GGUF` для LM Studio (готовый пример:
  `HOhus/pushkin-nano-bpe-GGUF`). Открыть в
  [Colab](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-5-1-publish-model/notebook.ipynb).
- **`notebook-blank.ipynb`** — то же, но шаг публикации пишешь сам. Открыть в
  [Colab](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-5-1-publish-model/notebook-blank.ipynb).

## Что нужно

Аккаунт HuggingFace и токен со scope **write**
(huggingface.co/settings/tokens). В Colab удобно положить его в Secrets как
`HF_TOKEN` или вызвать `notebook_login()`.
