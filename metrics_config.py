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
    "Дата отчета": {"type": "date", "source": "calculated"},
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
}

DATE_COLUMNS = {
    "Дата создания карточки товара",
    "Дата отчета",
}


def extract_report_date(df_raw: pd.DataFrame):
    """
    Ищет дату формирования отчета в служебной шапке:
    'Дата формирования: 03.30.26'
    """
    for _, row in df_raw.iterrows():
        first_cell = str(row.iloc[0]).strip()
        second_cell = str(row.iloc[1]).strip() if len(row) > 1 else ""

        if "Дата формирования" in first_cell:
            date_str = second_cell or first_cell.replace("Дата формирования:", "").strip()
            parsed = pd.to_datetime(date_str, errors="coerce")
            if pd.notna(parsed):
                return parsed

            # запасной вариант для формата MM.DD.YY
            try:
                return datetime.strptime(date_str, "%m.%d.%y")
            except Exception:
                return pd.NaT

    return pd.NaT


def clean_hour_value(value):
    """
    '29 ч' -> 29
    """
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
    """
    Артикул OZON извлекается из ссылки как число после последнего слеша.
    Пример:
    https://www.ozon.ru/product/2806697905 -> 2806697905
    """
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

    df["СПП, %"] = spp_percent

    if "Заказано на сумму, ₽" in df.columns:
        # формула по твоей логике:
        # Заказы до СПП = Заказано на сумму / (100 - СПП) * 100
        denominator = 100 - spp_percent
        if denominator != 0:
            df["Заказы до СПП, ₽"] = df["Заказано на сумму, ₽"] / denominator * 100
        else:
            df["Заказы до СПП, ₽"] = pd.NA

    if "Доля рекламных расходов, %" in df.columns and "Заказы до СПП, ₽" in df.columns:
        df["Рекламные расходы, сумма"] = df["Заказы до СПП, ₽"] * df["Доля рекламных расходов, %"] / 100

    return df


def get_numeric_columns(df: pd.DataFrame):
    numeric_cols = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
    return numeric_cols