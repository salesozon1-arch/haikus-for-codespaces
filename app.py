import pandas as pd
import streamlit as st

from metrics_config import (
    prepare_base_columns,
    add_calculated_columns,
    extract_report_date,
    get_numeric_columns,
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
            st.write("**Числовые поля для графиков:**", len(get_numeric_columns(df)))

        st.subheader("Предпросмотр данных")
        st.dataframe(df.head(30), use_container_width=True)

        st.subheader("Список колонок")
        st.write(list(df.columns))

    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")