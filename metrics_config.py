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

def aggregate_for_analysis(df: pd.DataFrame, analysis_level: str) -> pd.DataFrame:
    """
    Агрегация данных под график:
    - Товар: без агрегации
    - Бренд: группировка по бренду
    - Продавец: группировка по продавцу
    """

    if analysis_level == "Товар":
        result = df.copy()
        result["Группа анализа"] = result["Название товара"] if "Название товара" in result.columns else result.index.astype(str)
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
        "Заказы до СПП, ₽",
        "Рекламные расходы, сумма",
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
        "СПП, %",
    ]

    agg_dict = {}

    for col in sum_cols:
        if col in df.columns:
            agg_dict[col] = "sum"

    for col in mean_cols:
        if col in df.columns:
            agg_dict[col] = "mean"

    grouped = (
        df.groupby(group_col, dropna=False)
        .agg(agg_dict)
        .reset_index()
    )

    grouped["Количество товаров"] = df.groupby(group_col, dropna=False).size().values
    grouped["Группа анализа"] = grouped[group_col]

    if analysis_level == "Бренд" and "Продавец" in df.columns:
        seller_counts = df.groupby(group_col, dropna=False)["Продавец"].nunique().reset_index(name="Количество продавцов")
        grouped = grouped.merge(seller_counts, on=group_col, how="left")

    if analysis_level == "Продавец" and "Бренд" in df.columns:
        brand_counts = df.groupby(group_col, dropna=False)["Бренд"].nunique().reset_index(name="Количество брендов")
        grouped = grouped.merge(brand_counts, on=group_col, how="left")

    if "Заказано на сумму, ₽" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Заказано на сумму на 1 товар, ₽"] = grouped["Заказано на сумму, ₽"] / grouped["Количество товаров"]

    if "Показы всего" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Показы на 1 товар"] = grouped["Показы всего"] / grouped["Количество товаров"]

    if "Заказано, штуки" in grouped.columns and "Количество товаров" in grouped.columns:
        grouped["Заказано, штуки на 1 товар"] = grouped["Заказано, штуки"] / grouped["Количество товаров"]

    return grouped

        # =========================
        # ВРЕМЕННЫЕ РЯДЫ
        # =========================
        st.header("Динамика по времени")

        time_filtered_df = apply_common_filters(df, prefix="timeseries")

        ts_numeric_columns = get_numeric_columns(time_filtered_df)
        if len(ts_numeric_columns) == 0:
            st.warning("Нет числовых метрик для построения временных рядов.")
        else:
            ts_col1, ts_col2, ts_col3, ts_col4 = st.columns(4)

            with ts_col1:
                ts_analysis_level = st.selectbox(
                    "Уровень агрегации",
                    options=["Вся выборка", "Бренд", "Продавец", "Товар"],
                    index=0,
                    key="ts_analysis_level",
                )

            with ts_col2:
                metrics_count = st.selectbox(
                    "Количество метрик",
                    options=[1, 2, 3],
                    index=0,
                    key="ts_metrics_count",
                )

            default_ts_metric_1 = "Заказано на сумму, ₽" if "Заказано на сумму, ₽" in ts_numeric_columns else ts_numeric_columns[0]
            default_ts_metric_2 = "Заказано, штуки" if "Заказано, штуки" in ts_numeric_columns else ts_numeric_columns[min(1, len(ts_numeric_columns) - 1)]
            default_ts_metric_3 = "Показы всего" if "Показы всего" in ts_numeric_columns else ts_numeric_columns[min(2, len(ts_numeric_columns) - 1)]

            with ts_col3:
                ts_metric_1 = st.selectbox(
                    "Метрика 1",
                    options=ts_numeric_columns,
                    index=ts_numeric_columns.index(default_ts_metric_1) if default_ts_metric_1 in ts_numeric_columns else 0,
                    key="ts_metric_1",
                )

            with ts_col4:
                ts_top_n = st.selectbox(
                    "Количество линий",
                    options=[1, 3, 5, 10],
                    index=1,
                    key="ts_top_n",
                )

            extra_metric_cols = st.columns(2)

            selected_metrics = [ts_metric_1]

            with extra_metric_cols[0]:
                if metrics_count >= 2:
                    remaining_for_2 = [m for m in ts_numeric_columns if m != ts_metric_1]
                    default_index_2 = 0
                    if default_ts_metric_2 in remaining_for_2:
                        default_index_2 = remaining_for_2.index(default_ts_metric_2)

                    ts_metric_2 = st.selectbox(
                        "Метрика 2",
                        options=remaining_for_2,
                        index=default_index_2,
                        key="ts_metric_2",
                    )
                    selected_metrics.append(ts_metric_2)

            with extra_metric_cols[1]:
                if metrics_count >= 3:
                    remaining_for_3 = [m for m in ts_numeric_columns if m not in selected_metrics]
                    default_index_3 = 0
                    if default_ts_metric_3 in remaining_for_3:
                        default_index_3 = remaining_for_3.index(default_ts_metric_3)

                    ts_metric_3 = st.selectbox(
                        "Метрика 3",
                        options=remaining_for_3,
                        index=default_index_3,
                        key="ts_metric_3",
                    )
                    selected_metrics.append(ts_metric_3)

            all_ts_parts = []

            for metric_name in selected_metrics:
                ts_part = build_time_series(time_filtered_df, ts_analysis_level, metric_name)

                if ts_part.empty or metric_name not in ts_part.columns:
                    continue

                ts_part = ts_part.copy()
                ts_part["Метрика"] = metric_name
                ts_part["Значение"] = ts_part[metric_name]
                all_ts_parts.append(ts_part[["Дата отчета", "Группа анализа", "Метрика", "Значение"]])

            if not all_ts_parts:
                st.warning("Недостаточно данных для построения временного ряда.")
            else:
                ts_plot_df = pd.concat(all_ts_parts, ignore_index=True)

                if ts_analysis_level == "Вся выборка":
                    fig_ts = px.line(
                        ts_plot_df.sort_values("Дата отчета"),
                        x="Дата отчета",
                        y="Значение",
                        color="Метрика",
                        markers=True,
                    )
                else:
                    total_by_group = (
                        ts_plot_df.groupby("Группа анализа", dropna=False)["Значение"]
                        .sum()
                        .reset_index()
                        .sort_values("Значение", ascending=False)
                        .head(ts_top_n)
                    )

                    keep_groups = total_by_group["Группа анализа"].tolist()
                    ts_plot_df = ts_plot_df[ts_plot_df["Группа анализа"].isin(keep_groups)].copy()

                    ts_plot_df["Линия"] = (
                        ts_plot_df["Группа анализа"].astype(str)
                        + " | "
                        + ts_plot_df["Метрика"].astype(str)
                    )

                    fig_ts = px.line(
                        ts_plot_df.sort_values("Дата отчета"),
                        x="Дата отчета",
                        y="Значение",
                        color="Линия",
                        markers=True,
                        hover_data=["Группа анализа", "Метрика"],
                    )

                fig_ts.update_layout(
                    height=650,
                    xaxis_title="Дата отчета",
                    yaxis_title="Значение",
                )

                st.plotly_chart(fig_ts, use_container_width=True)

                st.subheader("Предпросмотр данных временного ряда")
                st.dataframe(ts_plot_df.head(100), use_container_width=True)