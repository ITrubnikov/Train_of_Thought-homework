# Модуль 3 — CatBoost и компания за один вечер

Заготовка к [Модулю 3: CatBoost и компания за один вечер](https://itrubnikov.github.io/Train_of_Thought/docs/modules/03-catboost/).

Модуль **опциональный** — если ваша цель только LLM-агенты, можно
пропустить. Если же хочется почувствовать, чем «правая ветка карты ML»
из [Модуля 2](https://itrubnikov.github.io/Train_of_Thought/docs/modules/02-ml-map/)
отличается от LLM на практике, — это идеальная одновечерняя задача.

## Что нужно сделать до начала

- Аккаунт Kaggle (для GPU не нужен, обычного хватит) **или** Google-аккаунт для Colab.
- Никаких API-ключей и Secrets — всё локально, без обращений к LLM.

## Файлы в папке

| Файл | Зачем |
| --- | --- |
| [`notebook.ipynb`](notebook.ipynb) | Скелет с 4 `TODO`. Грузит Telco Customer Churn, обучает бейзлайн логрегрессии, дальше вы дописываете CatBoost / XGBoost / LightGBM / SHAP. Цель — обогнать бейзлайн (AUC ≥ 0.84) и научиться читать SHAP. |

## Что вы делаете в ноутбуке

1. Грузите [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (7 043 строки, 16 категориальных фичей).
2. Обучаете бейзлайн — логистическую регрессию с OneHotEncoder. Получаете AUC ≈ 0.82.
3. **TODO 1.** Обучаете `CatBoostClassifier` с `cat_features` + `early_stopping_rounds`. Цель — AUC ≥ 0.84 без feature engineering'а.
4. **TODO 2.** Строите `shap.summary_plot` для CatBoost-модели, сохраняете `shap_summary.png`, отвечаете одной фразой про топ-3 фичи оттока.
5. **TODO 3.** Для одного клиента с `P(churn) > 0.8` строите `waterfall_plot`, сохраняете `shap_waterfall.png`, описываете одной фразой, что в его профиле триггерит модель.

## Как запустить

### Вариант A — Colab (одной кнопкой)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-3-catboost/notebook.ipynb)

`Файл → Сохранить копию на Диске` → дописать `TODO` → запустить все
ячейки → `Поделиться → у кого есть ссылка → Просмотр` → прислать
ссылку в чат курса.

### Вариант B — Kaggle Notebooks

`Create → New Notebook → File → Import Notebook` → выберите
`notebook.ipynb` из своего форка этого репо (или прямо
[raw-ссылку с GitHub](https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-3-catboost/notebook.ipynb)).

### Вариант C — локально

```bash
pip install jupyter pandas scikit-learn catboost shap matplotlib
jupyter notebook notebook.ipynb
```

GPU не нужен — на CPU всё обучается за 10—30 секунд.

## ДЗ к модулю

Полное ДЗ описано в [самой лекции](https://itrubnikov.github.io/Train_of_Thought/docs/modules/03-catboost/#домашнее-задание). Кратко:

**ДЗ 1 (обязательно, ~45—60 мин).** Заполнить 3 `TODO` в этом ноутбуке.
Критерии приёма:

- [ ] CatBoost AUC ≥ 0.84.
- [ ] В сравнительной таблице видны цифры обеих моделей (LogReg и CatBoost).
- [ ] `shap_summary.png` сохранён, топ-фичи биологически осмысленны.
- [ ] `shap_waterfall.png` сохранён + одна фраза-объяснение.
- [ ] Ссылка на ноутбук прислана в чат курса как `[Модуль 3, ДЗ 1] {ссылка}`.

**ДЗ 2 (опционально, ~60 мин).** Взять **любой** Kaggle-датасет
(Bank Marketing, House Prices, Credit Default, Adult Income) и
повторить пайплайн без подсказок.

## Подводные камни

- **`cat_features` забыли** → CatBoost либо ругнётся `ValueError`, либо обучится с AUC ~0.55. Всегда: `cat_features = X.select_dtypes(include='object').columns.tolist()`.
- **`eval_set` забыли** → `early_stopping_rounds` не работает, модель жарит все 1000 итераций и переобучается.

## Лицензия

Код — MIT (см. [LICENSE](../../LICENSE) в корне репо). Датасет —
Telco Customer Churn, опубликован IBM и доступен на Kaggle под
открытой лицензией.
