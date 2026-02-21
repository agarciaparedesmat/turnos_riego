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
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")

    # Normalizar nombres
    df.columns = df.columns.astype(str).str.strip().str.upper()

    # Seleccionar solo columnas necesarias
    df = df.loc[:, ["FECHA", "HORA", "TURNO"]]

    return df


df = cargar_datos()

st.subheader("Filtros")

turnos = ["(Todos)"] + sorted(df["TURNO"].unique().tolist())
turno_sel = st.selectbox("Turno", turnos)

if turno_sel != "(Todos)":
    df_view = df[df["TURNO"] == turno_sel]
else:
    df_view = df

st.subheader("Calendario")

# Ordenar por fecha
df_view = df_view.sort_values("FECHA")

# Convertir y formatear fecha
df_view["FECHA"] = pd.to_datetime(df_view["FECHA"])
df_view["FECHA"] = df_view["FECHA"].dt.strftime("%d/%m/%y")

st.dataframe(df_view, use_container_width=True)
