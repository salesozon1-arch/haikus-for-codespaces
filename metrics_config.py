import re
from datetime import datetime
import pandas as pd


FIELD_SPECS = {
    "Название товара": {"type": "text", "source": "base"},
    "Ссылка на товар": {"type": "text", "source": "base"},
    "Артикул OZON": {"type": "text", "source": "calculated"},
    "Продавец": {"type": "text", "source": "base"},
    "Бренд": {"type": "text", "source": "base"},
    "Категория 1 уровня": {"type": "text", "source": "base"},
    "Категория 3 уровня": {"type": "text", "source": "base"},
    "Признак товара": {"type": "category", "source": "base"},
    "Заказано на сумму, ₽": {"type": "currency", "source": "base"},
    "Динамика оборота, %": {"type": "percent", "source": "base"},
    "Заказано, штуки": {"type": "number", "source": "base"},
    "Средняя цена, ₽": {"type": "currency", "source": "base"},
    "Минимальная цена, ₽": {"type": "currency", "source": "base"},
    "Доля выкупа, %": {"type": "percent", "source": "base"},
    "Упущенные продажи, ₽": {"type": "currency", "source": "base"},
    "Дней без остатка": {"type": "number", "source": "base"},
    "Ср. время доставки до покупателя, часы": {"type": "number", "source": "base"},
    "Среднесуточные продажи, ₽": {"type": "currency", "source": "base"},
    "Среднесуточные продажи, штуки": {"type": "number", "source": "base"},
    "Остаток на конец периода, штуки": {"type": "number", "source": "base"},
    "Схема работы": {"type": "category", "source": "base"},
    "Объем товара, л": {"type": "number", "source": "base"},
    "Показы всего": {"type": "number", "source": "base"},
    "Просмотры в поиске и каталоге": {"type": "number", "source": "base"},
    "Просмотры карточки": {"type": "number", "source": "base"},
    "Конверсия из показа в заказ, %": {"type": "percent", "source": "base"},
    "В корзину из поиска и каталога, %": {"type": "percent", "source": "base"},
    "В корзину из карточки, %": {"type": "percent", "source": "base"},
    "Скидка за счет акций": {"type": "percent", "source": "base"},
    "Доля оборота в акциях, %": {"type": "percent", "source": "base"},
    "Дней в акциях": {"type": "number", "source": "base"},
    "Дней с продвижением": {"type": "number", "source": "base"},
    "Доля рекламных расходов, %": {"type": "percent", "source": "base"},
    "Дата создания карточки товара": {"type": "date", "source": "base"},
    "Возраст карточки, мес": {"type": "number", "source": "calculated"},
    "СПП, %": {"type": "percent", "source": "calculated"},
    "Заказы до СПП, ₽": {"type": "currency", "source": "calculated"},
    "Рекламные расходы, сумма": {"type": "currency", "source": "calculated"},
    "Количество корзин, шт": {"type": "number", "source": "calculated"},
    "CPM, ₽": {"type": "currency", "source": "calculated"},
    "CPC, ₽": {"type": "currency", "source": "calculated"},
    "CPcart, ₽": {"type": "currency", "source": "calculated"},
    "CPO, ₽": {"type": "currency", "source": "calculated"},
    "Дата отчета": {"type": "date", "source": "calculated"},
    "Доля поиска, %": {"type": "percent", "source": "calculated"},
    "CR в корзину, %": {"type": "percent", "source": "calculated"},
    "CR корзина -> заказ, %": {"type": "percent", "source": "calculated"},
    "CTR, %": {"type": "percent", "source": "calculated"},
}


TEXT_COLUMNS = {
    "Название товара",
    "Ссылка на товар",
    "Артикул OZON",
    "Продавец",
    "Бренд",
    "Категория 1 уровня",
    "Категория 3 уровня",
    "Признак товара",
    "Схема работы",
}

PERCENT_COLUMNS = {
    "Динамика оборота, %",
    "Доля выкупа, %",
    "Конверсия из показа в заказ, %",
    "В корзину из поиска и каталога, %",
    "В корзину из карточки, %",
    "Скидка за счет акций",
    "Доля оборота в акциях, %",
    "Доля рекламных расходов, %",
    "СПП, %",
    "Доля поиска, %",
    "CR в корзину, %",
    "CR корзина -> заказ, %",
    "CTR, %",
}

DATE_COLUMNS = {
    "Дата создания карточки товара",
    "Дата отчета",
}


def extract_report_date(df_raw: pd.DataFrame):
    """
    Ищет дату формирования в шапке отчета.
    Ожидаемый пример: 03.30.26
    """
    for _, row in df_raw.iterrows():
        first_cell = str(row.iloc[0]).strip()
        second_cell = str(row.iloc[1]).strip() if len(row) > 1 else ""

        if "Дата формирования" in first_cell:
            date_str = second_cell or first_cell.replace("Дата формирования:", "").strip()

            parsed = pd.to_datetime(date_str, errors="coerce")
            if pd.notna(parsed):
                return parsed

            try:
                return datetime.strptime(date_str, "%m.%d.%y")
            except Exception:
                return pd.NaT

    return pd.NaT


def clean_hour_value(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().lower()
    text = text.replace("ч", "").strip()
    text = text.replace(",", ".")

    try:
        return float(text)
    except Exception:
        return pd.NA


def extract_ozon_article(url):
    if pd.isna(url):
        return None

    text = str(url).strip().rstrip("/")
    match = re.search(r"/(\d+)(?:\?|$)", text)
    if match:
        return match.group(1)

    if "/" in text:
        return text.split("/")[-1]

    return None


def parse_date_column(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def clean_numeric_value(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    text = text.replace("\xa0", "")
    text = text.replace(" ", "")
    text = text.replace(",", ".")

    if text in {"", "nan", "None", "NaT"}:
        return pd.NA

    try:
        return float(text)
    except Exception:
        return pd.NA


def safe_divide(numerator, denominator):
    result = numerator / denominator
    if isinstance(result, pd.Series):
        result = result.replace([float("inf"), float("-inf")], pd.NA)
    return result


def recompute_derived_metrics(df: pd.DataFrame, spp_percent: float = 51.0) -> pd.DataFrame:
    """
    Пересчитывает производные метрики из уже имеющихся базовых колонок.
    Эту функцию можно безопасно вызывать:
    - после загрузки исходного файла
    - после агрегации по бренду/продавцу
    - после агрегации для временных рядов
    """
    df = df.copy()

    # СПП
    df["СПП, %"] = spp_percent

    # Заказы до СПП
    if "Заказано на сумму, ₽" in df.columns:
        denominator = 100 - spp_percent
        if denominator != 0:
            df["Заказы до СПП, ₽"] = df["Заказано на сумму, ₽"] / denominator * 100
        else:
            df["Заказы до СПП, ₽"] = pd.NA

    # Рекламные расходы, сумма
    if "Доля рекламных расходов, %" in df.columns and "Заказы до СПП, ₽" in df.columns:
        df["Рекламные расходы, сумма"] = (
            df["Заказы до СПП, ₽"] * df["Доля рекламных расходов, %"] / 100
        )

    # Количество корзин
    if (
        "Просмотры в поиске и каталоге" in df.columns
        and "В корзину из поиска и каталога, %" in df.columns
        and "Просмотры карточки" in df.columns
        and "В корзину из карточки, %" in df.columns
    ):
        df["Количество корзин, шт"] = (
            df["Просмотры в поиске и каталоге"] * df["В корзину из поиска и каталога, %"] / 100
            + df["Просмотры карточки"] * df["В корзину из карточки, %"] / 100
        )

    # CPM
    if "Рекламные расходы, сумма" in df.columns and "Показы всего" in df.columns:
        df["CPM, ₽"] = safe_divide(df["Рекламные расходы, сумма"], df["Показы всего"]) * 1000

    # CPC
    if "Рекламные расходы, сумма" in df.columns and "Просмотры карточки" in df.columns:
        df["CPC, ₽"] = safe_divide(df["Рекламные расходы, сумма"], df["Просмотры карточки"])

    # CPcart
    if "Рекламные расходы, сумма" in df.columns and "Количество корзин, шт" in df.columns:
        df["CPcart, ₽"] = safe_divide(df["Рекламные расходы, сумма"], df["Количество корзин, шт"])

    # CPO
    if "Рекламные расходы, сумма" in df.columns and "Заказано, штуки" in df.columns:
        df["CPO, ₽"] = safe_divide(df["Рекламные расходы, сумма"], df["Заказано, штуки"])

    # =========================
    # ВОРОНКА И ТРАФИК
    # =========================

    # Доля поиска
    if "Просмотры в поиске и каталоге" in df.columns and "Показы всего" in df.columns:
        df["Доля поиска, %"] = safe_divide(
            df["Просмотры в поиске и каталоге"],
            df["Показы всего"]
        ) * 100

    # CTR (показы -> карточка)
    if "Просмотры карточки" in df.columns and "Показы всего" in df.columns:
        df["CTR, %"] = safe_divide(
            df["Просмотры карточки"],
            df["Показы всего"]
        ) * 100

    # CR в корзину
    if "Количество корзин, шт" in df.columns and "Просмотры карточки" in df.columns:
        df["CR в корзину, %"] = safe_divide(
            df["Количество корзин, шт"],
            df["Просмотры карточки"]
        ) * 100

    # CR корзина -> заказ
    if "Заказано, штуки" in df.columns and "Количество корзин, шт" in df.columns:
        df["CR корзина -> заказ, %"] = safe_divide(
            df["Заказано, штуки"],
            df["Количество корзин, шт"]
        ) * 100
        
    return df


def prepare_base_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "Ср. время доставки до покупателя, часы" in df.columns:
        df["Ср. время доставки до покупателя, часы"] = df[
            "Ср. время доставки до покупателя, часы"
        ].apply(clean_hour_value)

    for col, spec in FIELD_SPECS.items():
        if col not in df.columns:
            continue

        if col in TEXT_COLUMNS:
            df[col] = df[col].astype(str).replace({"nan": None})
        elif col in DATE_COLUMNS:
            df[col] = parse_date_column(df[col])
        elif spec["type"] in {"number", "currency", "percent"}:
            df[col] = df[col].apply(clean_numeric_value)

    return df


def add_calculated_columns(df: pd.DataFrame, report_date=None, spp_percent=51.0) -> pd.DataFrame:
    df = df.copy()

    if "Ссылка на товар" in df.columns:
        df["Артикул OZON"] = df["Ссылка на товар"].apply(extract_ozon_article)

    if report_date is not None and pd.notna(report_date):
        df["Дата отчета"] = pd.to_datetime(report_date)
    else:
        df["Дата отчета"] = pd.NaT

    if "Дата создания карточки товара" in df.columns:
        create_date = pd.to_datetime(df["Дата создания карточки товара"], errors="coerce")
        base_date = pd.to_datetime(df["Дата отчета"], errors="coerce")
        age_months = ((base_date - create_date).dt.days / 30.44).round(1)
        df["Возраст карточки, мес"] = age_months

    df = recompute_derived_metrics(df, spp_percent=spp_percent)

    return df


def get_numeric_columns(df: pd.DataFrame):
    numeric_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
    return numeric_cols


def aggregate_for_analysis(df: pd.DataFrame, analysis_level: str, spp_percent: float = 51.0) -> pd.DataFrame:
    """
    Агрегация для пузырьковой диаграммы.
    Процентные и удельные метрики после группировки пересчитываются заново где возможно.
    """

    if analysis_level == "Товар":
        result = df.copy()
        result["Группа анализа"] = (
            result["Название товара"] if "Название товара" in result.columns else result.index.astype(str)
        )
        return result

    group_col = None
    if analysis_level == "Бренд":
        group_col = "Бренд"
    elif analysis_level == "Продавец":
        group_col = "Продавец"

    if group_col is None or group_col not in df.columns:
        return df.copy()

    sum_cols = [
        "Заказано на сумму, ₽",
        "Заказано, штуки",
        "Упущенные продажи, ₽",
        "Среднесуточные продажи, ₽",
        "Среднесуточные продажи, штуки",
        "Остаток на конец периода, штуки",
        "Показы всего",
        "Просмотры в поиске и каталоге",
        "Просмотры карточки",
        "Количество корзин, шт",
    ]

    mean_cols = [
        "Динамика оборота, %",
        "Средняя цена, ₽",
        "Минимальная цена, ₽",
        "Доля выкупа, %",
        "Дней без остатка",
        "Ср. время доставки до покупателя, часы",
        "Объем товара, л",
        "Конверсия из показа в заказ, %",
        "В корзину из поиска и каталога, %",
        "В корзину из карточки, %",
        "Скидка за счет акций",
        "Доля оборота в акциях, %",
        "Дней в акциях",
        "Дней с продвижением",
        "Доля рекламных расходов, %",
        "Возраст карточки, мес",
    ]

    agg_dict = {}

    for col in sum_cols:
        if col in df.columns:
            agg_dict[col] = "sum"

    for col in mean_cols:
        if col in df.columns:
            agg_dict[col] = "mean"

    grouped = df.groupby(group_col, dropna=False).agg(agg_dict).reset_index()

    grouped["Количество товаров"] = df.groupby(group_col, dropna=False).size().values
    grouped["Группа анализа"] = grouped[group_col]

    if analysis_level == "Бренд" and "Продавец" in df.columns:
        seller_counts = (
            df.groupby(group_col, dropna=False)["Продавец"]
            .nunique()
            .reset_index(name="Количество продавцов")
        )
        grouped = grouped.merge(seller_counts, on=group_col, how="left")

    if analysis_level == "Продавец" and "Бренд" in df.columns:
        brand_counts = (
            df.groupby(group_col, dropna=False)["Бренд"]
            .nunique()
            .reset_index(name="Количество брендов")
        )
        grouped = grouped.merge(brand_counts, on=group_col, how="left")

    # Пересчет производных метрик после агрегации
    grouped = recompute_derived_metrics(grouped, spp_percent=spp_percent)

    if "Заказано на сумму, ₽" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Заказано на сумму на 1 товар, ₽"] = safe_divide(
            grouped["Заказано на сумму, ₽"], grouped["Количество товаров"]
        )

    if "Показы всего" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Показы на 1 товар"] = safe_divide(
            grouped["Показы всего"], grouped["Количество товаров"]
        )

    if "Заказано, штуки" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Заказано, штуки на 1 товар"] = safe_divide(
            grouped["Заказано, штуки"], grouped["Количество товаров"]
        )

    if "Количество корзин, шт" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Количество корзин на 1 товар"] = safe_divide(
            grouped["Количество корзин, шт"], grouped["Количество товаров"]
        )

    return grouped


def get_percent_columns():
    return PERCENT_COLUMNS.copy()


def resolve_aggregation_method(metric_name: str, aggregation_mode: str) -> str:
    if metric_name in get_percent_columns() and aggregation_mode == "Сумма":
        return "Среднее"
    return aggregation_mode


def get_pandas_agg_func(aggregation_mode: str) -> str:
    mapping = {
        "Сумма": "sum",
        "Среднее": "mean",
        "Медиана": "median",
    }
    return mapping.get(aggregation_mode, "sum")