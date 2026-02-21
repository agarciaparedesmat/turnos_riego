import pandas as pd
import streamlit as st

st.set_page_config(page_title="Turnos de riego", layout="centered")

st.title("💧 Consulta de turnos y horario de riego (2026)")

# TODO: luego lo conectamos a Excel/CSV.
data = [
    {"FECHA": "04/01/2026", "HORA": "4 PM", "TURNO": "RICO"},
    {"FECHA": "12/01/2026", "HORA": "0 AM", "TURNO": "MONTSE"},
    {"FECHA": "18/01/2026", "HORA": "8 AM", "TURNO": "RICO"},
    {"FECHA": "25/01/2026", "HORA": "4 PM", "TURNO": "AMELIA"},
    {"FECHA": "02/02/2026", "HORA": "0 AM", "TURNO": "RICO"},
]

df = pd.DataFrame(data)

st.subheader("Filtros")
turnos = ["(Todos)"] + sorted(df["TURNO"].unique().tolist())
turno_sel = st.selectbox("Turno", turnos)

if turno_sel != "(Todos)":
    df_view = df[df["TURNO"] == turno_sel].copy()
else:
    df_view = df.copy()

st.subheader("Calendario")
st.dataframe(df_view, use_container_width=True)
