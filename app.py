from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "data" / "turnos_2026.xlsx"

st.set_page_config(page_title="Turnos de riego", layout="centered")

st.title("💧 Consulta de turnos y horario de riego (2026)")


# Cargar datos
@st.cache_data
def cargar_datos():
    return pd.read_excel(EXCEL_PATH, engine="openpyxl")


df = cargar_datos()

# Nos quedamos solo con las 3 columnas correctas
df = df[["FECHA", "HORA", "TURNO"]].copy()

st.subheader("Filtros")

turnos = ["(Todos)"] + sorted(df["TURNO"].unique().tolist())
turno_sel = st.selectbox("Turno", turnos)

if turno_sel != "(Todos)":
    df_view = df[df["TURNO"] == turno_sel]
else:
    df_view = df

st.subheader("Calendario")
st.dataframe(df_view, use_container_width=True)
