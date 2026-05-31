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
| [`notebook.ipynb`](notebook.ipynb) | Скелет с 3 `TODO`. Грузит House Prices (Ames Housing), обучает бейзлайн Ridge-регрессии, дальше вы дописываете CatBoost и SHAP. Цель — обогнать бейзлайн (RMSE ≤ 0.135 на log-цене) и научиться читать SHAP. |
| `solution.ipynb` | Эталонное решение **для преподавателя** и для самопроверки после своей попытки. Открывайте только когда `TODO` уже честно попытались сделать сами — иначе пропустите главный кайф «вот оно работает». |

## Что вы делаете в ноутбуке

1. Грузите [House Prices — Advanced Regression Techniques](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques) (Ames Housing, 1 460 домов, 80 признаков, 43 категориальных) через `sklearn.datasets.fetch_openml` — никакой Kaggle API не нужен.
2. Обучаете бейзлайн — `Ridge` (линейная регрессия с L2-регуляризацией) с OneHotEncoder и StandardScaler. Получаете RMSE ≈ 0.135—0.14 на log(SalePrice) — это уже сильный бейзлайн, CatBoost обгонит его лишь немного.
3. **TODO 1.** Обучаете `CatBoostRegressor` с `cat_features` + `early_stopping_rounds`. Цель — RMSE ≤ 0.135 без feature engineering'а.
4. **TODO 2.** Строите `shap.summary_plot` для CatBoost-модели, сохраняете `shap_summary.png`, отвечаете одной фразой про топ-3 фичи, двигающие цену.
5. **TODO 3.** Для **самого дорогого** дома в тесте строите `waterfall_plot`, сохраняете `shap_waterfall.png`, описываете одной фразой, какие фичи задрали его цену.

## Как запустить

### Вариант A — Colab (одной кнопкой)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ITrubnikov/Train_of_Thought-homework/blob/main/notebooks/module-3-catboost/notebook.ipynb)

`Файл → Сохранить копию на Диске` → дописать `TODO` → запустить все
ячейки → `Поделиться → у кого есть ссылка → Просмотр` → прислать
ссылку в чат курса.

### Вариант B — Kaggle Notebooks (требует 4 клика подготовки)

У Kaggle-ноутбуков по умолчанию **выключен внешний интернет**, поэтому
`fetch_openml` оттуда обычно не дотягивается до OpenML (а если и
дотягивается — их сервера регулярно отвечают 504). На Kaggle правильно
брать данные **из подключённого competition'а**, и это занимает 30 секунд.

**Полный workflow с нуля:**

1. **Создайте ноутбук из этого файла.**
   - На Kaggle сверху-слева: `+ Create` → `New Notebook`.
   - В новом ноутбуке: `File → Import Notebook → URL`, вставьте
     raw-ссылку: `https://raw.githubusercontent.com/ITrubnikov/Train_of_Thought-homework/main/notebooks/module-3-catboost/notebook.ipynb`.
2. **Подключите датасет House Prices.**
   - Справа найдите панель **«Notebook»** → секция **«Input»** →
     кнопка **`+ Add Input`**.
   - В открывшемся окне переключите вкладку наверху на **«Competitions»**
     (по умолчанию там «Your Work» / «Datasets»).
   - В поиске наберите `House Prices`. Выберите карточку
     **«House Prices — Advanced Regression Techniques»** (Ongoing,
     5132 Teams, Getting Started — с иконкой домика с табличкой
     «SOLD»). Жмите **`+`** справа.
   - Закройте окно — в правой панели под «COMPETITIONS» появится
     этот competition с файлами `train.csv`, `test.csv`,
     `sample_submission.csv`, `data_description.txt`.
3. **Прогоните ячейки сверху вниз.** Kaggle монтирует подключённый
   competition в работающий kernel сразу — рестарт обычно не нужен.
   Загрузочная ячейка использует
   `glob.glob('/kaggle/input/**/train.csv', recursive=True)` — это
   ловит и плоский (`/kaggle/input/<slug>/`), и вложенный
   (`/kaggle/input/competitions/<slug>/`) layout, который Kaggle
   использует для разных типов аккаунтов.

В любой свободной ячейке можно проверить, что данные на месте:

```python
import glob
print(glob.glob('/kaggle/input/**/train.csv', recursive=True))
```

Должен вывести один путь типа
`/kaggle/input/competitions/house-prices-advanced-regression-techniques/train.csv`.
Если пусто — competition не подключился (вернитесь к шагу 2). В
редких случаях kernel не видит свежесмонтированные данные — тогда
`Run → Restart Session` и снова сверху.

**Альтернатива на Kaggle:** включить `Notebook → Internet → On`
(требует phone-verified аккаунт). Тогда `fetch_openml` отработает
как в Colab — но это менее надёжно, OpenML регулярно отвечает 504.

### Вариант C — локально

```bash
pip install jupyter pandas scikit-learn catboost shap matplotlib
jupyter notebook notebook.ipynb
```

GPU не нужен — на CPU всё обучается за 20—40 секунд.

## ДЗ к модулю

Полное ДЗ описано в [самой лекции](https://itrubnikov.github.io/Train_of_Thought/docs/modules/03-catboost/#домашнее-задание). Кратко:

**ДЗ 1 (обязательно, ~45—60 мин).** Заполнить 3 `TODO` в этом ноутбуке.
Критерии приёма:

- [ ] CatBoost RMSE ≤ 0.135 на log-цене.
- [ ] В сравнительной таблице видны цифры обеих моделей (Ridge и CatBoost).
- [ ] `predicted_vs_actual.png` сохранён — обе модели плотно лежат на диагонали (на этой табличке Ridge и CatBoost близки, и это нормально).
- [ ] `line_vs_function.png` сохранён — Ridge даёт прямую линию, CatBoost рисует ступенчатую кривую.
- [ ] `shap_summary.png` сохранён, топ-фичи биологически осмысленны (`OverallQual`, `GrLivArea`, `Neighborhood`).
- [ ] `shap_waterfall.png` сохранён + одна фраза-объяснение.
- [ ] Ссылка на ноутбук прислана в чат курса как `[Модуль 3, ДЗ 1] {ссылка}`.

**ДЗ 2 (опционально, ~60 мин).** Взять **любой другой** Kaggle-датасет
(Telco Churn, Bank Marketing, Credit Default, Adult Income, Titanic)
и повторить пайплайн без подсказок.

## Подводные камни

- **`HTTPError` / `A network error occurred` / `504 Gateway Time-out` на `fetch_openml`** → вы на Kaggle либо без интернета, либо OpenML лёг (у них регулярно). Подключите competition-датасет через `Add Input → Competitions → "House Prices"`. См. «Вариант B — Kaggle Notebooks» выше. Если включали Internet, но он всё равно даёт 504 — это сервер OpenML, не Kaggle. Лекарство — competition-путь, он не требует HTTP вообще.
- **`FileNotFoundError: /kaggle/input/.../train.csv`** → competition не подключён, либо подключён, но kernel его не видит. Sanity-check: `!ls /kaggle/input/` должен показать папки с данными. Если папки есть, а ячейка падает — перезапустите загрузочную ячейку. Если `/kaggle/input/` пуст — подключите competition (см. шаг 2) и в редком случае сделайте `Run → Restart Session`.
- **`!ls /kaggle/input/` показывает `competitions`, а не имя датасета** → это вложенный layout. Реальный путь — `/kaggle/input/competitions/<slug>/train.csv`. Загрузочная ячейка в ноутбуке использует `glob.glob('/kaggle/input/**/train.csv', recursive=True)` и сама разруливает оба варианта — править ничего не нужно.
- **`cat_features` забыли** → CatBoost либо ругнётся `ValueError`, либо обучится с ужасным качеством. Всегда: `cat_features = X.select_dtypes(include='object').columns.tolist()`.
- **`NaN` в категориальной колонке** → `CatBoostError`. Лекарство — одна строка: `X[c] = X[c].fillna('missing').astype(str)` для всех cat-колонок до `.fit()`. В Ames Housing таких колонок ~16 (PoolQC, FireplaceQu и т.п.).
- **`eval_set` забыли** → `early_stopping_rounds` не работает, модель жарит все `iterations` и переобучается.
- **Учим на сыром `SalePrice`** вместо `log(SalePrice)` → RMSE будет в долларах (десятки тысяч) и абсолютно бесполезен для сравнения. Используйте `np.log1p(y)` для обучения и `np.expm1(pred)` для интерпретации.

## Лицензия

Код — MIT (см. [LICENSE](../../LICENSE) в корне репо). Датасет —
Ames Housing (Dean De Cock, 2011), public domain, опубликован на
Kaggle и в OpenML.
