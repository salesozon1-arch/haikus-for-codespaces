import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ozon Analytics", layout="wide")


def find_header_row(df_raw: pd.DataFrame) -> int:
    for i, row in df_raw.iterrows():
        first_cell = str(row.iloc[0]).strip()
        if first_cell == "Название товара":
            return i
    raise ValueError("Не удалось найти строку заголовков. Проверь формат файла.")


def load_ozon_report(uploaded_file) -> pd.DataFrame:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file, header=None)
    elif file_name.endswith(".xlsx"):
        df_raw = pd.read_excel(uploaded_file, header=None)
    else:
        raise ValueError("Поддерживаются только CSV и XLSX")

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
    return df


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    text_columns = {
        "Название товара",
        "Ссылка на товар",
        "Продавец",
        "Бренд",
        "Категория 1 уровня",
        "Категория 3 уровня",
        "Признак товара",
        "Схема работы",
        "Дата создания карточки товара",
    }

    df = df.copy()

    for col in df.columns:
        if col in text_columns:
            continue

        cleaned = (
            df[col]
            .astype(str)
            .str.replace("\xa0", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )

        cleaned = cleaned.replace({"": None, "nan": None, "None": None})
        converted = pd.to_numeric(cleaned, errors="coerce")

        if converted.notna().sum() > 0:
            df[col] = converted

    return df


st.title("Ozon Analytics")

uploaded_file = st.file_uploader("Загрузи отчет Ozon", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        df = load_ozon_report(uploaded_file)
        df = convert_numeric_columns(df)

        st.success(f"Файл загружен. Строк: {len(df)}, колонок: {len(df.columns)}")

        st.subheader("Колонки")
        st.write(list(df.columns))

        st.subheader("Предпросмотр данных")
        st.dataframe(df.head(20), use_container_width=True)

    except Exception as e:
        st.error(f"Ошибка загрузки файла: {e}")