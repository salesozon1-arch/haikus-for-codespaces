import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ozon Analytics", layout="wide")

st.title("Ozon Analytics")
st.write("Первая заготовка приложения работает.")

uploaded_file = st.file_uploader("Загрузи CSV или Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Предпросмотр данных")
    st.dataframe(df.head(20), use_container_width=True)