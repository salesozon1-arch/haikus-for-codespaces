import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import qualitative
import pandas as pd
import streamlit as st
import plotly.express as px

from metrics_config import (
    prepare_base_columns,
    add_calculated_columns,
    extract_report_date,
    get_numeric_columns,
    aggregate_for_analysis,
    resolve_aggregation_method,
    get_pandas_agg_func,
    recompute_derived_metrics,
)

def safe_series_divide(numerator, denominator):
    result = numerator / denominator
    if isinstance(result, pd.Series):
        result = result.replace([float("inf"), float("-inf")], pd.NA)
    return result


def get_dashboard_group_col(level: str):
    if level == "Бренд":
        return "Бренд"
    if level == "Продавец":
        return "Продавец"
    return None


def apply_dashboard_filters(df: pd.DataFrame):
    dashboard_df = df.copy()

    st.subheader("Фильтры дашборда")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "Дата отчета" in dashboard_df.columns and dashboard_df["Дата отчета"].notna().sum() > 0:
            min_date = pd.to_datetime(dashboard_df["Дата отчета"]).min().date()
            max_date = pd.to_datetime(dashboard_df["Дата отчета"]).max().date()

            if min_date == max_date:
                st.write(f"**Период:** {min_date}")
            else:
                date_range = st.slider(
                    "Период",
                    min_value=min_date,
                    max_value=max_date,
                    value=(min_date, max_date),
                    key="dashboard_date_range",
                )

                dashboard_df = dashboard_df[
                    (pd.to_datetime(dashboard_df["Дата отчета"]).dt.date >= date_range[0]) &
                    (pd.to_datetime(dashboard_df["Дата отчета"]).dt.date <= date_range[1])
                ]

    with col2:
        if "Бренд" in dashboard_df.columns:
            brand_options = sorted(
                [x for x in dashboard_df["Бренд"].dropna().unique().tolist() if str(x).strip() != ""]
            )
            selected_brands = st.multiselect(
                "Фильтр по бренду",
                options=brand_options,
                key="dashboard_filter_brands",
            )
            if selected_brands:
                dashboard_df = dashboard_df[dashboard_df["Бренд"].isin(selected_brands)]

    with col3:
        if "Продавец" in dashboard_df.columns:
            seller_options = sorted(
                [x for x in dashboard_df["Продавец"].dropna().unique().tolist() if str(x).strip() != ""]
            )
            selected_sellers = st.multiselect(
                "Фильтр по продавцу",
                options=seller_options,
                key="dashboard_filter_sellers",
            )
            if selected_sellers:
                dashboard_df = dashboard_df[dashboard_df["Продавец"].isin(selected_sellers)]

    return dashboard_df


def build_dashboard_base_timeseries(df: pd.DataFrame, level: str, selected_values=None):
    """
    Готовит агрегированную по датам базу для fixed dashboard.
    derived-метрики потом считаются из агрегированных сумм, а не усредняются как попало.
    """
    dashboard_df = df.copy()

    group_col = get_dashboard_group_col(level)

    if group_col is not None:
        if selected_values:
            dashboard_df = dashboard_df[dashboard_df[group_col].isin(selected_values)]
        else:
            # если ничего не выбрано — берем топ-3 по выручке
            top_groups = (
                dashboard_df.groupby(group_col, dropna=False)["Заказано на сумму, ₽"]
                .sum()
                .reset_index()
                .sort_values("Заказано на сумму, ₽", ascending=False)
                .head(3)[group_col]
                .tolist()
            )
            dashboard_df = dashboard_df[dashboard_df[group_col].isin(top_groups)]

    group_keys = ["Дата отчета"]
    if group_col is not None:
        group_keys.append(group_col)

    sum_cols = [
        "Заказано на сумму, ₽",
        "Заказано, штуки",
        "Среднесуточные продажи, штуки",
        "Показы всего",
        "Просмотры в поиске и каталоге",
        "Просмотры карточки",
        "Количество корзин, шт",
        "Заказы до СПП, ₽",
        "Рекламные расходы, сумма",
    ]

    agg_dict = {}
    for col in sum_cols:
        if col in dashboard_df.columns:
            agg_dict[col] = "sum"

    # для цен нужна отдельная агрегация mean/median
    if "Средняя цена, ₽" in dashboard_df.columns:
        agg_dict["Средняя цена, ₽"] = "mean"

    grouped = dashboard_df.groupby(group_keys, dropna=False).agg(agg_dict).reset_index()

    # медианная цена отдельным проходом
    if "Средняя цена, ₽" in dashboard_df.columns:
        median_price = (
            dashboard_df.groupby(group_keys, dropna=False)["Средняя цена, ₽"]
            .median()
            .reset_index(name="Медианная цена, ₽")
        )
        grouped = grouped.merge(median_price, on=group_keys, how="left")

    # пересчет производных метрик из агрегированных сумм
    if "Просмотры в поиске и каталоге" in grouped.columns and "Показы всего" in grouped.columns:
        grouped["Доля поиска, %"] = safe_series_divide(
            grouped["Просмотры в поиске и каталоге"], grouped["Показы всего"]
        ) * 100

    if "Просмотры карточки" in grouped.columns and "Показы всего" in grouped.columns:
        grouped["CTR, %"] = safe_series_divide(
            grouped["Просмотры карточки"], grouped["Показы всего"]
        ) * 100

    if "Количество корзин, шт" in grouped.columns and "Просмотры карточки" in grouped.columns:
        grouped["CR в корзину, %"] = safe_series_divide(
            grouped["Количество корзин, шт"], grouped["Просмотры карточки"]
        ) * 100

    if "Заказано, штуки" in grouped.columns and "Количество корзин, шт" in grouped.columns:
        grouped["CR корзина -> заказ, %"] = safe_series_divide(
            grouped["Заказано, штуки"], grouped["Количество корзин, шт"]
        ) * 100

    if "Заказано, штуки" in grouped.columns and "Показы всего" in grouped.columns:
        grouped["CR из показа в заказ, %"] = safe_series_divide(
            grouped["Заказано, штуки"], grouped["Показы всего"]
        ) * 100

    if "Рекламные расходы, сумма" in grouped.columns and "Заказы до СПП, ₽" in grouped.columns:
        grouped["ДРР, %"] = safe_series_divide(
            grouped["Рекламные расходы, сумма"], grouped["Заказы до СПП, ₽"]
        ) * 100

    if "Рекламные расходы, сумма" in grouped.columns and "Показы всего" in grouped.columns:
        grouped["CPM, ₽"] = safe_series_divide(
            grouped["Рекламные расходы, сумма"], grouped["Показы всего"]
        ) * 1000

    if "Рекламные расходы, сумма" in grouped.columns and "Просмотры карточки" in grouped.columns:
        grouped["CPC, ₽"] = safe_series_divide(
            grouped["Рекламные расходы, сумма"], grouped["Просмотры карточки"]
        )

    if "Рекламные расходы, сумма" in grouped.columns and "Количество корзин, шт" in grouped.columns:
        grouped["CPcart, ₽"] = safe_series_divide(
            grouped["Рекламные расходы, сумма"], grouped["Количество корзин, шт"]
        )

    if "Рекламные расходы, сумма" in grouped.columns and "Заказано, штуки" in grouped.columns:
        grouped["CPO, ₽"] = safe_series_divide(
            grouped["Рекламные расходы, сумма"], grouped["Заказано, штуки"]
        )

    if group_col is None:
        grouped["Группа сравнения"] = "Вся выборка"
    else:
        grouped["Группа сравнения"] = grouped[group_col].astype(str)

    return grouped


def make_panel_series(base_df: pd.DataFrame, metric_specs: list):
    """
    metric_specs = [
        {"metric": "...", "label": "...", "axis": "left|right"}
    ]
    """
    parts = []

    for spec in metric_specs:
        metric = spec["metric"]
        label = spec["label"]
        axis = spec["axis"]

        if metric not in base_df.columns:
            continue

        part = base_df[["Дата отчета", "Группа сравнения", metric]].copy()
        part["Метрика"] = label
        part["Ось"] = axis
        part["Значение"] = part[metric]
        parts.append(part[["Дата отчета", "Группа сравнения", "Метрика", "Ось", "Значение"]])

    if not parts:
        return pd.DataFrame()

    return pd.concat(parts, ignore_index=True)


def render_line_legend(items):
    if not items:
        return

    html_parts = []
    for color, label in items:
        html_parts.append(
            f"<span style='margin-right:16px;'>"
            f"<span style='display:inline-block;width:10px;height:10px;background:{color};"
            f"border-radius:50%;margin-right:6px;'></span>{label}</span>"
        )

    st.markdown("".join(html_parts), unsafe_allow_html=True)


def plot_dashboard_panel(panel_df: pd.DataFrame, title: str):
    if panel_df.empty:
        st.warning(f"Нет данных для графика: {title}")
        return

    has_right = (panel_df["Ось"] == "right").any()
    fig = make_subplots(specs=[[{"secondary_y": has_right}]])

    palette = qualitative.Plotly
    line_keys = panel_df[["Группа сравнения", "Метрика"]].drop_duplicates().values.tolist()
    line_labels = [f"{group} — {metric}" for group, metric in line_keys]
    color_map = {label: palette[i % len(palette)] for i, label in enumerate(line_labels)}

    legend_items = []

    for (group_name, metric_name, axis_side), grp in panel_df.groupby(
        ["Группа сравнения", "Метрика", "Ось"], dropna=False
    ):
        trace_label = f"{group_name} — {metric_name}"
        trace_color = color_map[trace_label]
        legend_items.append((trace_color, trace_label))

        fig.add_trace(
            go.Scatter(
                x=grp["Дата отчета"],
                y=grp["Значение"],
                mode="lines+markers",
                name=trace_label,
                line=dict(color=trace_color, width=2),
                marker=dict(size=6),
            ),
            secondary_y=(axis_side == "right"),
        )

    left_labels = panel_df.loc[panel_df["Ось"] == "left", "Метрика"].drop_duplicates().tolist()
    right_labels = panel_df.loc[panel_df["Ось"] == "right", "Метрика"].drop_duplicates().tolist()

    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    fig.update_xaxes(title_text="Дата отчета")

    if left_labels:
        fig.update_yaxes(title_text=" / ".join(left_labels), secondary_y=False)

    if has_right and right_labels:
        fig.update_yaxes(title_text=" / ".join(right_labels), secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)
    render_line_legend(legend_items)

st.set_page_config(page_title="Ozon Analytics", layout="wide")


def find_header_row(df_raw: pd.DataFrame) -> int:
    for i, row in df_raw.iterrows():
        first_cell = str(row.iloc[0]).strip()
        if first_cell == "Название товара":
            return i
    raise ValueError("Не удалось найти строку заголовков. Проверь формат файла.")


def load_single_ozon_report(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file, header=None)
    elif file_name.endswith(".xlsx"):
        df_raw = pd.read_excel(uploaded_file, header=None)
    else:
        raise ValueError(f"Файл {uploaded_file.name}: поддерживаются только CSV и XLSX")

    report_date = extract_report_date(df_raw)
    header_row = find_header_row(df_raw)

    uploaded_file.seek(0)

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=header_row)
    else:
        df = pd.read_excel(uploaded_file, header=header_row)

    df = df.dropna(how="all").copy()

    if "Название товара" in df.columns:
        df = df[df["Название товара"].astype(str).str.strip() != "Среднее значение по товарам"]
        df = df[df["Название товара"].astype(str).str.strip() != "Название товара"]

    df = df.reset_index(drop=True)
    df["Имя файла"] = uploaded_file.name

    return df, report_date


def load_multiple_ozon_reports(uploaded_files):
    all_data = []

    for uploaded_file in uploaded_files:
        df, report_date = load_single_ozon_report(uploaded_file)
        df = prepare_base_columns(df)
        df = add_calculated_columns(df, report_date=report_date, spp_percent=51.0)
        all_data.append(df)

    if not all_data:
        return pd.DataFrame()

    combined_df = pd.concat(all_data, ignore_index=True)
    return combined_df


def apply_common_filters(df: pd.DataFrame, prefix: str):
    filtered_df = df.copy()

    st.subheader("Фильтры")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if "Средняя цена, ₽" in filtered_df.columns and filtered_df["Средняя цена, ₽"].notna().sum() > 0:
            min_price = float(filtered_df["Средняя цена, ₽"].min())
            max_price = float(filtered_df["Средняя цена, ₽"].max())

            if min_price == max_price:
                st.write(f"**Диапазон цены:** {min_price:.2f}")
            else:
                price_range = st.slider(
                    "Диапазон средней цены, ₽",
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price),
                    key=f"{prefix}_price_range",
                )
                filtered_df = filtered_df[
                    (filtered_df["Средняя цена, ₽"] >= price_range[0]) &
                    (filtered_df["Средняя цена, ₽"] <= price_range[1])
                ]

    with col2:
        if "Возраст карточки, мес" in filtered_df.columns and filtered_df["Возраст карточки, мес"].notna().sum() > 0:
            min_age = float(filtered_df["Возраст карточки, мес"].min())
            max_age = float(filtered_df["Возраст карточки, мес"].max())

            if min_age == max_age:
                st.write(f"**Возраст карточки:** {min_age:.1f}")
            else:
                age_range = st.slider(
                    "Возраст карточки, мес",
                    min_value=min_age,
                    max_value=max_age,
                    value=(min_age, max_age),
                    key=f"{prefix}_age_range",
                )
                filtered_df = filtered_df[
                    (filtered_df["Возраст карточки, мес"] >= age_range[0]) &
                    (filtered_df["Возраст карточки, мес"] <= age_range[1])
                ]

    with col3:
        if "Схема работы" in filtered_df.columns:
            scheme_options = sorted(
                [x for x in filtered_df["Схема работы"].dropna().unique().tolist() if str(x).strip() != ""]
            )
            selected_schemes = st.multiselect(
                "Схема работы",
                options=scheme_options,
                key=f"{prefix}_schemes",
            )
            if selected_schemes:
                filtered_df = filtered_df[filtered_df["Схема работы"].isin(selected_schemes)]

    with col4:
        if "Бренд" in filtered_df.columns:
            brand_options = sorted(
                [x for x in filtered_df["Бренд"].dropna().unique().tolist() if str(x).strip() != ""]
            )
            selected_brands = st.multiselect(
                "Бренд",
                options=brand_options,
                key=f"{prefix}_brands",
            )
            if selected_brands:
                filtered_df = filtered_df[filtered_df["Бренд"].isin(selected_brands)]

    with col5:
        if "Продавец" in filtered_df.columns:
            seller_options = sorted(
                [x for x in filtered_df["Продавец"].dropna().unique().tolist() if str(x).strip() != ""]
            )
            selected_sellers = st.multiselect(
                "Магазин / продавец",
                options=seller_options,
                key=f"{prefix}_sellers",
            )
            if selected_sellers:
                filtered_df = filtered_df[filtered_df["Продавец"].isin(selected_sellers)]

    return filtered_df


def build_time_series(df: pd.DataFrame, analysis_level: str, metric: str, aggregation_mode: str):
    if "Дата отчета" not in df.columns:
        return pd.DataFrame()

    actual_mode = resolve_aggregation_method(metric, aggregation_mode)
    agg_func = get_pandas_agg_func(actual_mode)

    if analysis_level == "Вся выборка":
        ts = (
            df.groupby("Дата отчета", dropna=False)
            .agg({metric: agg_func})
            .reset_index()
            .sort_values("Дата отчета")
        )
        ts["Группа анализа"] = "Вся выборка"
        ts["Режим агрегации"] = actual_mode
        return ts

    if analysis_level == "Товар":
        group_col = "Название товара"
    elif analysis_level == "Бренд":
        group_col = "Бренд"
    elif analysis_level == "Продавец":
        group_col = "Продавец"
    else:
        group_col = None

    if group_col is None or group_col not in df.columns:
        return pd.DataFrame()

    ts = (
        df.groupby(["Дата отчета", group_col], dropna=False)
        .agg({metric: agg_func})
        .reset_index()
        .sort_values("Дата отчета")
    )

    ts["Группа анализа"] = ts[group_col]
    ts["Режим агрегации"] = actual_mode
    return ts


st.title("Ozon Analytics")

uploaded_files = st.file_uploader(
    "Загрузи один или несколько отчетов Ozon",
    type=["csv", "xlsx"],
    accept_multiple_files=True,
)

if uploaded_files:
    try:
        df = load_multiple_ozon_reports(uploaded_files)

        if df.empty:
            st.warning("Не удалось загрузить данные.")
            st.stop()

        date_min = df["Дата отчета"].min() if "Дата отчета" in df.columns else None
        date_max = df["Дата отчета"].max() if "Дата отчета" in df.columns else None

        st.success(
            f"Файлы загружены. Строк: {len(df)}, колонок: {len(df.columns)}, отчетов: {len(uploaded_files)}"
        )

        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.write("**Мин. дата отчета:**", date_min)
        with info_col2:
            st.write("**Макс. дата отчета:**", date_max)
        with info_col3:
            st.write("**Числовых полей:**", len(get_numeric_columns(df)))

                # =========================
        # ПУЗЫРЬКОВАЯ ДИАГРАММА
        # =========================
        st.header("Пузырьковая диаграмма")

        # Выбор одной даты для пузырьковой диаграммы
        bubble_date_filtered_df = df.copy()

        if "Дата отчета" in bubble_date_filtered_df.columns:
            available_bubble_dates = sorted(
                [d for d in bubble_date_filtered_df["Дата отчета"].dropna().unique().tolist()]
            )

            if available_bubble_dates:
                selected_bubble_date = st.selectbox(
                    "Дата для пузырьковой диаграммы",
                    options=available_bubble_dates,
                    format_func=lambda x: pd.to_datetime(x).strftime("%d.%m.%Y"),
                    key="bubble_selected_date",
                )

                bubble_date_filtered_df = bubble_date_filtered_df[
                    bubble_date_filtered_df["Дата отчета"] == selected_bubble_date
                ]

        bubble_filtered_df = apply_common_filters(bubble_date_filtered_df, prefix="bubble")

        st.subheader("Настройки графика")

        analysis_level = st.radio(
            "Уровень анализа",
            options=["Товар", "Бренд", "Продавец"],
            horizontal=True,
            key="bubble_analysis_level",
        )

        df_chart_base = aggregate_for_analysis(bubble_filtered_df, analysis_level, spp_percent=51.0)
        numeric_columns = get_numeric_columns(df_chart_base)

        if len(numeric_columns) < 3:
            st.warning("Недостаточно числовых полей для построения пузырьковой диаграммы.")
        else:
            default_x = "Показы всего" if "Показы всего" in numeric_columns else numeric_columns[0]
            default_y = "Заказано на сумму, ₽" if "Заказано на сумму, ₽" in numeric_columns else numeric_columns[min(1, len(numeric_columns) - 1)]
            default_size = "Заказано, штуки" if "Заказано, штуки" in numeric_columns else numeric_columns[min(2, len(numeric_columns) - 1)]

            parameter_options = ["Без параметра"]
            for col in [
                "Бренд",
                "Продавец",
                "Категория 1 уровня",
                "Категория 3 уровня",
                "Признак товара",
                "Схема работы",
                "Группа анализа",
            ]:
                if col in df_chart_base.columns and col not in parameter_options:
                    parameter_options.append(col)

            chart_col1, chart_col2, chart_col3, chart_col4 = st.columns(4)

            with chart_col1:
                x_axis = st.selectbox(
                    "Ось X",
                    options=numeric_columns,
                    index=numeric_columns.index(default_x) if default_x in numeric_columns else 0,
                    key="bubble_x",
                )

            with chart_col2:
                y_axis = st.selectbox(
                    "Ось Y",
                    options=numeric_columns,
                    index=numeric_columns.index(default_y) if default_y in numeric_columns else 0,
                    key="bubble_y",
                )

            with chart_col3:
                size_axis = st.selectbox(
                    "Размер пузыря",
                    options=numeric_columns,
                    index=numeric_columns.index(default_size) if default_size in numeric_columns else 0,
                    key="bubble_size",
                )

            with chart_col4:
                parameter_by = st.selectbox(
                    "Параметр",
                    options=parameter_options,
                    key="bubble_parameter",
                )

            st.subheader("Ограничение выборки")

            ranking_options = numeric_columns.copy()
            default_rank = "Заказано на сумму, ₽" if "Заказано на сумму, ₽" in ranking_options else ranking_options[0]

            rank_col1, rank_col2, rank_col3 = st.columns(3)

            with rank_col1:
                rank_by = st.selectbox(
                    "Ограничивать по метрике",
                    options=ranking_options,
                    index=ranking_options.index(default_rank) if default_rank in ranking_options else 0,
                    key="bubble_rank_by",
                )

            with rank_col2:
                top_n = st.selectbox(
                    "Количество точек",
                    options=[10, 20, 35, 100],
                    index=1,
                    key="bubble_top_n",
                )

            with rank_col3:
                label_options = ["Без подписи"]
                for col in ["Группа анализа", "Название товара", "Бренд", "Продавец", "Артикул OZON"]:
                    if col in df_chart_base.columns and col not in label_options:
                        label_options.append(col)

                if (
                    parameter_by != "Без параметра"
                    and parameter_by in df_chart_base.columns
                    and parameter_by not in label_options
                ):
                    label_options.append(parameter_by)

                point_label = st.selectbox(
                    "Подпись точек",
                    options=label_options,
                    key="bubble_point_label",
                )

            chart_df = df_chart_base.dropna(subset=[x_axis, y_axis, size_axis]).copy()

            if rank_by in chart_df.columns:
                chart_df = chart_df.sort_values(rank_by, ascending=False).head(top_n)

            if len(chart_df) == 0:
                st.warning("После фильтрации не осталось данных для построения графика.")
            else:
                hover_fields = []
                for col in [
                    "Группа анализа",
                    "Название товара",
                    "Бренд",
                    "Продавец",
                    "Артикул OZON",
                    "Количество товаров",
                    "Количество продавцов",
                    "Количество брендов",
                    "Заказано на сумму, ₽",
                    "Заказано, штуки",
                    "Средняя цена, ₽",
                    "Показы всего",
                    "Просмотры карточки",
                    "Количество корзин, шт",
                    "Возраст карточки, мес",
                    "Заказано на сумму на 1 товар, ₽",
                    "Показы на 1 товар",
                    "Заказано, штуки на 1 товар",
                    "Количество корзин на 1 товар",
                    "CPM, ₽",
                    "CPC, ₽",
                    "CPcart, ₽",
                    "CPO, ₽",
                ]:
                    if col in chart_df.columns:
                        hover_fields.append(col)

                color_arg = parameter_by if parameter_by != "Без параметра" else None
                text_column = point_label if point_label != "Без подписи" and point_label in chart_df.columns else None

                hover_name_col = None
                if "Группа анализа" in chart_df.columns:
                    hover_name_col = "Группа анализа"
                elif "Название товара" in chart_df.columns:
                    hover_name_col = "Название товара"

                fig = px.scatter(
                    chart_df,
                    x=x_axis,
                    y=y_axis,
                    size=size_axis,
                    color=color_arg,
                    text=text_column,
                    hover_name=hover_name_col,
                    hover_data=hover_fields,
                    size_max=60,
                )

                fig.update_traces(
                    textposition="top center",
                    marker=dict(opacity=0.7)
                )

                fig.update_layout(
                    height=750,
                    xaxis_title=x_axis,
                    yaxis_title=y_axis,
                )

                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"На графике показано {len(chart_df)} точек")

        st.subheader("Предпросмотр данных для пузырьковой диаграммы")
        st.dataframe(df_chart_base.head(50), use_container_width=True)

        # =========================
        # ВРЕМЕННЫЕ РЯДЫ
        # =========================
        st.header("Динамика по времени")

        time_filtered_df = apply_common_filters(df, prefix="timeseries")

        ts_numeric_columns = get_numeric_columns(time_filtered_df)

        if len(ts_numeric_columns) == 0:
            st.warning("Нет числовых метрик для построения временных рядов.")
        else:
            ts_col1, ts_col2, ts_col3, ts_col4, ts_col5 = st.columns(5)

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

            with ts_col3:
                ts_aggregation_mode = st.selectbox(
                    "Режим агрегации",
                    options=["Сумма", "Среднее", "Медиана"],
                    index=0,
                    key="ts_aggregation_mode",
                )

            default_ts_metric_1 = "Заказано на сумму, ₽" if "Заказано на сумму, ₽" in ts_numeric_columns else ts_numeric_columns[0]
            default_ts_metric_2 = "Заказано, штуки" if "Заказано, штуки" in ts_numeric_columns else ts_numeric_columns[min(1, len(ts_numeric_columns) - 1)]
            default_ts_metric_3 = "Показы всего" if "Показы всего" in ts_numeric_columns else ts_numeric_columns[min(2, len(ts_numeric_columns) - 1)]

            with ts_col4:
                ts_metric_1 = st.selectbox(
                    "Метрика 1",
                    options=ts_numeric_columns,
                    index=ts_numeric_columns.index(default_ts_metric_1) if default_ts_metric_1 in ts_numeric_columns else 0,
                    key="ts_metric_1",
                )

            with ts_col5:
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

            adjusted_metrics = []
            for metric_name in selected_metrics:
                actual_mode = resolve_aggregation_method(metric_name, ts_aggregation_mode)
                if actual_mode != ts_aggregation_mode:
                    adjusted_metrics.append(metric_name)

            if adjusted_metrics:
                st.info(
                    "Для процентных метрик режим 'Сумма' автоматически заменен на 'Среднее': "
                    + ", ".join(adjusted_metrics)
                )

            all_ts_parts = []

            for metric_name in selected_metrics:
                ts_part = build_time_series(
                    time_filtered_df,
                    ts_analysis_level,
                    metric_name,
                    ts_aggregation_mode,
                )

                if ts_part.empty or metric_name not in ts_part.columns:
                    continue

                ts_part = ts_part.copy()
                ts_part["Метрика"] = metric_name
                ts_part["Значение"] = ts_part[metric_name]
                all_ts_parts.append(
                    ts_part[["Дата отчета", "Группа анализа", "Метрика", "Значение", "Режим агрегации"]]
                )

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
                        hover_data=["Метрика", "Режим агрегации"],
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
                        hover_data=["Группа анализа", "Метрика", "Режим агрегации"],
                    )

                fig_ts.update_layout(
                    height=650,
                    xaxis_title="Дата отчета",
                    yaxis_title="Значение",
                )

                st.plotly_chart(fig_ts, use_container_width=True)

                st.subheader("Предпросмотр данных временного ряда")
                st.dataframe(ts_plot_df.head(100), use_container_width=True)

        # =========================
        # ФИКСИРОВАННЫЙ ДАШБОРД 3x3
        # =========================
        st.header("Фиксированный дашборд")

        dashboard_filtered_df = apply_dashboard_filters(df)

        dash_ctrl1, dash_ctrl2 = st.columns(2)

        with dash_ctrl1:
            dashboard_level = st.selectbox(
                "Уровень сравнения",
                options=["Вся выборка", "Бренд", "Продавец"],
                index=0,
                key="dashboard_level",
            )

        compare_values = []
        group_col = get_dashboard_group_col(dashboard_level)

        with dash_ctrl2:
            if group_col is not None and group_col in dashboard_filtered_df.columns:
                compare_options = sorted(
                    [x for x in dashboard_filtered_df[group_col].dropna().unique().tolist() if str(x).strip() != ""]
                )
                compare_values = st.multiselect(
                    f"Сравнить значения ({group_col})",
                    options=compare_options,
                    key="dashboard_compare_values",
                )

        dashboard_base_df = build_dashboard_base_timeseries(
            dashboard_filtered_df,
            level=dashboard_level,
            selected_values=compare_values,
        )

        panel_specs = [
            {
                "title": "1. Заказы до СПП",
                "metrics": [
                    {"metric": "Заказы до СПП, ₽", "label": "Заказы до СПП, ₽", "axis": "left"},
                ],
            },
            {
                "title": "2. Средняя и медианная цена",
                "metrics": [
                    {"metric": "Средняя цена, ₽", "label": "Средняя цена, ₽", "axis": "left"},
                    {"metric": "Медианная цена, ₽", "label": "Медианная цена, ₽", "axis": "left"},
                ],
            },
            {
                "title": "3. Заказы, штуки",
                "metrics": [
                    {"metric": "Заказано, штуки", "label": "Заказано, штуки", "axis": "left"},
                    {"metric": "Среднесуточные продажи, штуки", "label": "Среднесуточные продажи, штуки", "axis": "left"},
                ],
            },
            {
                "title": "4. Показы и доля поиска",
                "metrics": [
                    {"metric": "Показы всего", "label": "Показы всего", "axis": "left"},
                    {"metric": "Просмотры в поиске и каталоге", "label": "Показы из поиска и каталога", "axis": "left"},
                    {"metric": "Доля поиска, %", "label": "Доля поиска, %", "axis": "right"},
                ],
            },
            {
                "title": "5. CTR и посещения карточки",
                "metrics": [
                    {"metric": "Просмотры карточки", "label": "Посещения карточки", "axis": "left"},
                    {"metric": "CTR, %", "label": "CTR, %", "axis": "right"},
                ],
            },
            {
                "title": "6. Конверсии",
                "metrics": [
                    {"metric": "CR в корзину, %", "label": "CR в корзину, %", "axis": "left"},
                    {"metric": "CR корзина -> заказ, %", "label": "CR корзина → заказ, %", "axis": "left"},
                    {"metric": "CR из показа в заказ, %", "label": "CR из показа в заказ, %", "axis": "left"},
                ],
            },
            {
                "title": "7. Рекламный бюджет и ДРР",
                "metrics": [
                    {"metric": "Рекламные расходы, сумма", "label": "Рекламный бюджет, ₽", "axis": "left"},
                    {"metric": "ДРР, %", "label": "ДРР, %", "axis": "right"},
                ],
            },
            {
                "title": "8. CPC и CPM",
                "metrics": [
                    {"metric": "CPC, ₽", "label": "CPC, ₽", "axis": "left"},
                    {"metric": "CPM, ₽", "label": "CPM, ₽", "axis": "left"},
                ],
            },
            {
                "title": "9. CPcart и CPO",
                "metrics": [
                    {"metric": "CPcart, ₽", "label": "CPcart, ₽", "axis": "left"},
                    {"metric": "CPO, ₽", "label": "CPO, ₽", "axis": "left"},
                ],
            },
        ]

        for row_start in range(0, len(panel_specs), 3):
            row_panels = panel_specs[row_start:row_start + 3]
            cols = st.columns(3)

            for col, panel in zip(cols, row_panels):
                with col:
                    panel_df = make_panel_series(dashboard_base_df, panel["metrics"])
                    plot_dashboard_panel(panel_df, panel["title"])
    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")