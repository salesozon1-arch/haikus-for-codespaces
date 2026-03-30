import pandas as pd
import streamlit as st
import plotly.express as px

from metrics_config import (
    prepare_base_columns,
    add_calculated_columns,
    extract_report_date,
    get_numeric_columns,
    aggregate_for_analysis,
)

st.set_page_config(page_title="Ozon Analytics", layout="wide")


def find_header_row(df_raw: pd.DataFrame) -> int:
    for i, row in df_raw.iterrows():
        first_cell = str(row.iloc[0]).strip()
        if first_cell == "Название товара":
            return i
    raise ValueError("Не удалось найти строку заголовков. Проверь формат файла.")


def load_ozon_report(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file, header=None)
    elif file_name.endswith(".xlsx"):
        df_raw = pd.read_excel(uploaded_file, header=None)
    else:
        raise ValueError("Поддерживаются только CSV и XLSX")

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

    return df, report_date


st.title("Ozon Analytics")

uploaded_file = st.file_uploader("Загрузи отчет Ozon", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        df, report_date = load_ozon_report(uploaded_file)
        df = prepare_base_columns(df)
        df = add_calculated_columns(df, report_date=report_date, spp_percent=51.0)

        st.success(f"Файл загружен. Строк: {len(df)}, колонок: {len(df.columns)}")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Дата отчета:**", report_date)
        with col2:
            st.write("**Числовых полей в исходных данных:**", len(get_numeric_columns(df)))

        st.subheader("Настройки графика")

        analysis_level = st.radio(
            "Уровень анализа",
            options=["Товар", "Бренд", "Продавец"],
            horizontal=True
        )

        df_filtered = df.copy()

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            if "Средняя цена, ₽" in df_filtered.columns and df_filtered["Средняя цена, ₽"].notna().sum() > 0:
                min_price = float(df_filtered["Средняя цена, ₽"].min())
                max_price = float(df_filtered["Средняя цена, ₽"].max())

                if min_price == max_price:
                    st.write(f"**Диапазон средней цены, ₽:** {min_price:.2f}")
                else:
                    price_range = st.slider(
                        "Диапазон средней цены, ₽",
                        min_value=min_price,
                        max_value=max_price,
                        value=(min_price, max_price),
                    )
                    df_filtered = df_filtered[
                        (df_filtered["Средняя цена, ₽"] >= price_range[0]) &
                        (df_filtered["Средняя цена, ₽"] <= price_range[1])
                    ]

        with filter_col2:
            if "Схема работы" in df_filtered.columns:
                scheme_options = sorted(
                    [x for x in df_filtered["Схема работы"].dropna().unique().tolist() if str(x).strip() != ""]
                )
                selected_schemes = st.multiselect("Схема работы", options=scheme_options)
                if selected_schemes:
                    df_filtered = df_filtered[df_filtered["Схема работы"].isin(selected_schemes)]

        with filter_col3:
            if "Возраст карточки, мес" in df_filtered.columns and df_filtered["Возраст карточки, мес"].notna().sum() > 0:
                min_age = float(df_filtered["Возраст карточки, мес"].min())
                max_age = float(df_filtered["Возраст карточки, мес"].max())

                if min_age == max_age:
                    st.write(f"**Возраст карточки, мес:** {min_age:.1f}")
                else:
                    age_range = st.slider(
                        "Возраст карточки, мес",
                        min_value=min_age,
                        max_value=max_age,
                        value=(min_age, max_age),
                    )
                    df_filtered = df_filtered[
                        (df_filtered["Возраст карточки, мес"] >= age_range[0]) &
                        (df_filtered["Возраст карточки, мес"] <= age_range[1])
                    ]

        # Агрегация уже после фильтров
        df_chart_base = aggregate_for_analysis(df_filtered, analysis_level)
        numeric_columns = get_numeric_columns(df_chart_base)

        if len(numeric_columns) < 3:
            st.warning("Недостаточно числовых полей для построения графика.")
            st.stop()

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
                index=numeric_columns.index(default_x) if default_x in numeric_columns else 0
            )

        with chart_col2:
            y_axis = st.selectbox(
                "Ось Y",
                options=numeric_columns,
                index=numeric_columns.index(default_y) if default_y in numeric_columns else 0
            )

        with chart_col3:
            size_axis = st.selectbox(
                "Размер пузыря",
                options=numeric_columns,
                index=numeric_columns.index(default_size) if default_size in numeric_columns else 0
            )

        with chart_col4:
            parameter_by = st.selectbox("Параметр", options=parameter_options)

        st.subheader("Ограничение выборки")

        ranking_options = numeric_columns.copy()
        default_rank = "Заказано на сумму, ₽" if "Заказано на сумму, ₽" in ranking_options else ranking_options[0]

        rank_col1, rank_col2, rank_col3 = st.columns(3)

        with rank_col1:
            rank_by = st.selectbox(
                "Ограничивать по метрике",
                options=ranking_options,
                index=ranking_options.index(default_rank) if default_rank in ranking_options else 0
            )

        with rank_col2:
            top_n = st.selectbox(
                "Количество точек",
                options=[10, 20, 35, 100],
                index=1
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

            point_label = st.selectbox("Подпись точек", options=label_options)

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
                "Возраст карточки, мес",
                "Заказано на сумму на 1 товар, ₽",
                "Показы на 1 товар",
                "Заказано, штуки на 1 товар",
            ]:
                if col in chart_df.columns:
                    hover_fields.append(col)

            color_arg = parameter_by if parameter_by != "Без параметра" else None

            text_column = None
            if point_label != "Без подписи" and point_label in chart_df.columns:
                text_column = point_label

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

        st.subheader("Предпросмотр данных")
        st.dataframe(df_chart_base.head(50), use_container_width=True)

    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")