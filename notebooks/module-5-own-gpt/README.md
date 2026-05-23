# Модуль 5 — Свой GPT за час: от датасета до HuggingFace Hub

Заготовка к [Модулю 5: Свой GPT за час](https://itrubnikov.github.io/Train_of_Thought/docs/modules/05-own-gpt/).

Самый «инженерный» модуль курса до агентов: за 90 минут pretrain'им
крошечный трансформер на корпусе Пушкина двумя разными способами
(char-level руками + BPE через `transformers.Trainer`) и заливаем обе
модели на HuggingFace Hub.

## Что нужно сделать до начала

- Аккаунт **HuggingFace** + Personal Access Token со scope `write`
  ([настройки](https://huggingface.co/settings/tokens)).
- Аккаунт **Kaggle** или **Google Colab** для GPU (T4 хватит).
- Прочесть [Preflight: HuggingFace, Colab, Kaggle](https://itrubnikov.github.io/Train_of_Thought/docs/extras/preflight-tools)
  — там про токены и Secrets.

## Файлы в папке

| Файл | Зачем |
| --- | --- |
| [`data/README.md`](data/README.md) | Три способа получить корпус Пушкина (HF datasets / Wikisource / az.lib.ru). Public-domain, размер 0.5—5 МБ. |
| [`data/prepare_corpus.py`](data/prepare_corpus.py) | Скрипт-помощник: склейка нескольких `.txt`, конвертация кодировок, базовая чистка. |

⚠ **Готового notebook.ipynb здесь пока нет.** Этот модуль идёт
«ноутбуком прямо из лекции» — код лежит блоками в самой [лекции
модуля 5](https://itrubnikov.github.io/Train_of_Thought/docs/modules/05-own-gpt/),
вы копируете секции в свой Kaggle/Colab-ноутбук по мере прохождения.
Так задумано: модуль про то, чтобы вы один раз руками собрали
pretraining-пайплайн, а не нажали «Run All». Если решим завернуть
в shipped-ноутбук — он появится здесь как `notebook.ipynb`.

## Что вы делаете

1. Берёте корпус Пушкина (см. `data/README.md`, лёгкий вариант — HF dataset).
2. **Заход 1: char-level + ручной PyTorch.** Маленький GPT по схеме
   nanoGPT, словарь = уникальные символы корпуса, ~80 строк
   PyTorch, ручной train loop. Цель — увидеть, что модель учит ритм
   и окончания, но не смысл.
3. **Заход 2: BPE-1024 + `transformers.Trainer`.** Тот же датасет,
   токенизатор BPE на 1024 merge-операций, готовый `GPT2Config` +
   `Trainer`. Цель — увидеть, во что превращается тот же workflow в
   «инженерном» виде.
4. **Push to Hub.** Обе модели заливаются в свой HF-аккаунт через
   `model.push_to_hub("username/pushkin-nano")` и
   `model.push_to_hub("username/pushkin-nano-bpe")`.
5. **Сравнение.** В конце сэмплируете обе модели одним и тем же
   стартовым промптом и видите, как BPE даёт более «слитный» текст.

## Как запустить

### Вариант A — Kaggle Notebooks (рекомендуется, GPU T4 бесплатно)

`Create → New Notebook` → ноутбук пишете руками, копируя секции из
[лекции](https://itrubnikov.github.io/Train_of_Thought/docs/modules/05-own-gpt/).
Включите `Accelerator → GPU T4`. HF token — через `Add-ons → Secrets`
с именем `HF_TOKEN`.

### Вариант B — Google Colab

`File → New Notebook` → включите runtime T4 GPU. HF token подкладывайте
через `notebook_login()` или Colab Secrets (`HF_TOKEN`).

### Вариант C — Локально с GPU

```bash
pip install torch transformers datasets huggingface_hub
huggingface-cli login
# дальше копируйте код из лекции по секциям
```

## ДЗ к модулю

Полный текст ДЗ — в [самой лекции](https://itrubnikov.github.io/Train_of_Thought/docs/modules/05-own-gpt/#домашнее-задание).

**Критерии приёмки (кратко):**

- [ ] На HF Hub лежит ваша `username/pushkin-nano` (char-level).
- [ ] На HF Hub лежит ваша `username/pushkin-nano-bpe` (BPE-1024).
- [ ] В model card обеих моделей — пример генерации и две строки
  про датасет.
- [ ] В чат курса прислана ссылка как `[Модуль 5, ДЗ] {ссылка на профиль HF}`.

## Подводные камни

- **HF token со scope `read`** — push отвалится с 401. Нужен `write`.
- **OOM на T4 при BPE-варианте** — уменьшите `block_size` до 128
  и `per_device_train_batch_size` до 8.
- **Корпус в Windows-1251** — конвертируйте через
  `iconv -f windows-1251 -t utf-8 file.txt > pushkin.txt`. Если
  забыли — будет каша в `chars = sorted(set(text))`.
- **Char-level модель учит структуру, но без смысла** — это **не
  баг**, это главный урок модуля.

## Лицензия

MIT (см. [LICENSE](../../LICENSE) в корне репо). Корпус Пушкина —
public domain (умер в 1837).
