from __future__ import annotations

from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo
import calendar
import io

import pandas as pd
import streamlit as st

# PDF (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# -----------------------------
# Config
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "data" / "turnos_2026.xlsx"
TZ = ZoneInfo("Europe/Madrid")

st.set_page_config(page_title="Turnos de riego", layout="wide")
st.title("💧 Consulta de turnos y horario de riego (2026)")

modo_movil = st.toggle("📱 Modo móvil", value=False)


# -----------------------------
# Helpers
# -----------------------------
def parse_hora(h: str) -> time:
    """Convierte strings tipo '0 AM', '8 AM', '4 PM' a datetime.time."""
    s = str(h).strip().upper()
    parts = s.split()
    if len(parts) != 2:
        raise ValueError(f"Formato de HORA no soportado: {h}")

    hour = int(parts[0])
    ampm = parts[1]

    if ampm == "AM":
        if hour == 12:
            hour = 0
    elif ampm == "PM":
        if hour != 12:
            hour += 12
    else:
        raise ValueError(f"AM/PM no reconocido: {h}")

    return time(hour=hour, minute=0)


def build_pdf(df: pd.DataFrame, titulo: str) -> bytes:
    """Genera un PDF simple con la agenda filtrada."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, titulo)

    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(x, y, f"Generado: {datetime.now(TZ).strftime('%d/%m/%Y %H:%M')}")

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, "FECHA")
    c.drawString(x + 120, y, "HORA")
    c.drawString(x + 220, y, "TURNO")
    y -= 12
    c.line(x, y, width - 40, y)
    y -= 18

    c.setFont("Helvetica", 10)

    for _, r in df.iterrows():
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y, "FECHA")
            c.drawString(x + 120, y, "HORA")
            c.drawString(x + 220, y, "TURNO")
            y -= 12
            c.line(x, y, width - 40, y)
            y -= 18
            c.setFont("Helvetica", 10)

        c.drawString(x, y, r["FECHA_STR"])
        c.drawString(x + 120, y, str(r["HORA"]))
        c.drawString(x + 220, y, str(r["TURNO"]))
        y -= 16

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def render_month_calendar(df_month: pd.DataFrame, year: int, month: int) -> None:
    """Render calendario mensual (grid) con los turnos en cada día y 'hoy' resaltado."""
    df_month = df_month.copy()
    df_month["DAY"] = df_month["FECHA"].dt.day

    events_by_day: dict[int, list[str]] = {}
    for _, r in df_month.iterrows():
        d = int(r["DAY"])
        events_by_day.setdefault(d, []).append(f"{r['HORA']} · {r['TURNO']}")

    cal = calendar.Calendar(firstweekday=0)  # Lunes
    weeks = cal.monthdayscalendar(year, month)
    headers = ["L", "M", "X", "J", "V", "S", "D"]

    today_local = datetime.now(TZ).date()
    is_current_month = year == today_local.year and month == today_local.month
    today_day = today_local.day if is_current_month else None

    rows = []
    for w in weeks:
        row = []
        for day in w:
            if day == 0:
                row.append("")
                continue

            evs = events_by_day.get(day, [])
            if evs:
                lines = "<br>".join(evs[:2])
                if len(evs) > 2:
                    lines += "<br>…"
                inner = f"<b>{day:02d}</b><br>{lines}"
            else:
                inner = f"<b>{day:02d}</b>"

            highlight = today_day is not None and day == today_day
            if highlight:
                cell = f"<div style='background:#fff3cd; border-radius:8px; padding:6px;'>{inner}</div>"
            else:
                cell = inner

            row.append(cell)
        rows.append(row)

    table_html = "<table style='width:100%; border-collapse:collapse;'>"
    table_html += (
        "<tr>"
        + "".join(
            f"<th style='border:1px solid #ddd; padding:8px; text-align:center; background:#f4f6f8;'>{h}</th>"
            for h in headers
        )
        + "</tr>"
    )

    for r in rows:
        table_html += (
            "<tr>"
            + "".join(
                f"<td style='border:1px solid #ddd; padding:8px; vertical-align:top; height:86px;'>{cell}</td>"
                for cell in r
            )
            + "</tr>"
        )

    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)


# -----------------------------
# Load
# -----------------------------
@st.cache_data
def cargar_datos() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")

    df.columns = df.columns.astype(str).str.strip().str.upper()
    df = df.loc[:, ["FECHA", "HORA", "TURNO"]].copy()

    df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    df = df.dropna(subset=["FECHA", "HORA", "TURNO"])

    df["HORA"] = df["HORA"].astype(str).str.strip()
    df["TURNO"] = df["TURNO"].astype(str).str.strip()

    df["HORA_T"] = df["HORA"].apply(parse_hora)
    df["DT"] = df.apply(
        lambda r: datetime.combine(r["FECHA"].date(), r["HORA_T"], tzinfo=TZ), axis=1
    )

    df = df.sort_values("DT").reset_index(drop=True)
    return df


df = cargar_datos()

# -----------------------------
# Colores por persona
# -----------------------------
palette = [
    "#4da6ff",
    "#22c55e",
    "#f59e0b",
    "#a855f7",
    "#ef4444",
    "#06b6d4",
    "#84cc16",
    "#f97316",
]
personas = sorted(df["TURNO"].unique().tolist())
color_map = {p: palette[i % len(palette)] for i, p in enumerate(personas)}

# Meses presentes
df["MONTH_LABEL"] = df["FECHA"].dt.strftime("%m/%Y")
months_present = sorted(df["MONTH_LABEL"].unique().tolist())

# -----------------------------
# UI Layout: filtros arriba en columnas si NO móvil
# -----------------------------
st.subheader("Filtros")

if modo_movil:
    turno_sel = st.selectbox("Turno", ["(Todos)"] + personas)
    mes_sel = st.selectbox("Mes", ["(Todos)"] + months_present)
    q = st.text_input("Búsqueda rápida", value="").strip()
else:
    c1, c2, c3 = st.columns([1, 1, 2])
    turno_sel = c1.selectbox("Turno", ["(Todos)"] + personas)
    mes_sel = c2.selectbox("Mes", ["(Todos)"] + months_present)
    q = c3.text_input("Búsqueda rápida (turno / hora / fecha)", value="").strip()

df_view = df.copy()

if turno_sel != "(Todos)":
    df_view = df_view[df_view["TURNO"] == turno_sel]

if mes_sel != "(Todos)":
    df_view = df_view[df_view["MONTH_LABEL"] == mes_sel]

# -----------------------------
# Atajos: Hoy / Esta semana
# -----------------------------
st.subheader("Atajos")
a1, a2, a3 = st.columns(3)
hoy_click = a1.button("📌 Hoy", use_container_width=True)
semana_click = a2.button("📅 Esta semana", use_container_width=True)
reset_click = a3.button("🔄 Quitar atajos", use_container_width=True)

if "rango_atajo" not in st.session_state:
    st.session_state["rango_atajo"] = None  # (start_dt, end_dt)

today = datetime.now(TZ).date()
start_week = today - pd.Timedelta(days=today.weekday())  # lunes
end_week = start_week + pd.Timedelta(days=7)  # próximo lunes (exclusivo)

if hoy_click:
    st.session_state["rango_atajo"] = (
        datetime.combine(today, time(0, 0), tzinfo=TZ),
        datetime.combine(today + pd.Timedelta(days=1), time(0, 0), tzinfo=TZ),
    )

if semana_click:
    st.session_state["rango_atajo"] = (
        datetime.combine(start_week, time(0, 0), tzinfo=TZ),
        datetime.combine(end_week, time(0, 0), tzinfo=TZ),
    )

if reset_click:
    st.session_state["rango_atajo"] = None

if st.session_state["rango_atajo"] is not None:
    a, b = st.session_state["rango_atajo"]
    df_view = df_view[(df_view["DT"] >= a) & (df_view["DT"] < b)]

# -----------------------------
# Búsqueda rápida (aplica después de filtros/atajos)
# -----------------------------
if q:
    tmp = df_view.copy()
    tmp["FECHA_STR"] = tmp["FECHA"].dt.strftime("%d/%m/%y")
    mask = (
        tmp["TURNO"].str.contains(q, case=False, na=False)
        | tmp["HORA"].astype(str).str.contains(q, case=False, na=False)
        | tmp["FECHA_STR"].str.contains(q, case=False, na=False)
    )
    df_view = tmp[mask].drop(columns=["FECHA_STR"])

# -----------------------------
# Próximo turno
# -----------------------------
st.subheader("⏳ Próximo turno")

now = datetime.now(TZ)
df_future = df_view[df_view["DT"] >= now].copy()

if df_future.empty:
    st.info("No hay turnos futuros para los filtros seleccionados.")
else:
    nxt = df_future.sort_values("DT").iloc[0]
    delta = nxt["DT"] - now

    days = delta.days
    hours = delta.seconds // 3600
    mins = (delta.seconds % 3600) // 60

    st.markdown(
        f"""
        <div style="padding:12px;border-radius:12px;background:#f4f6f8;border-left:6px solid {color_map.get(nxt['TURNO'], '#4da6ff')};">
            <strong>{nxt['DT'].strftime('%d/%m/%y')}</strong> · 🕒 {nxt['HORA']} · 👤 {nxt['TURNO']}<br>
            <span style="opacity:0.8;">En {days} días, {hours} h, {mins} min</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Próximos 5 turnos
# -----------------------------
st.subheader("➡️ Próximos 5 turnos")

df_next5 = df_view[df_view["DT"] >= now].sort_values("DT").head(5).copy()
if df_next5.empty:
    st.info("No hay próximos turnos con los filtros actuales.")
else:
    df_next5["FECHA_STR"] = df_next5["FECHA"].dt.strftime("%d/%m/%y")
    for _, row in df_next5.iterrows():
        color = color_map.get(row["TURNO"], "#4da6ff")
        st.markdown(
            f"""
            <div style="
                padding:12px;
                border-radius:10px;
                margin-bottom:8px;
                background-color:#f4f6f8;
                border-left:6px solid {color};
            ">
                <strong>{row['FECHA_STR']}</strong>
                &nbsp;&nbsp;🕒 {row['HORA']}
                &nbsp;&nbsp;👤 {row['TURNO']}
            </div>
            """,
            unsafe_allow_html=True,
        )

# -----------------------------
# Calendario mensual (grid)
# -----------------------------
st.subheader("🗓️ Calendario mensual")

if mes_sel == "(Todos)":
    st.info("Selecciona un mes para ver el calendario mensual.")
else:
    month = int(mes_sel.split("/")[0])
    year = int(mes_sel.split("/")[1])

    if modo_movil:
        st.info("Modo móvil: calendario mensual oculto (usa la agenda).")
    else:
        render_month_calendar(df_view, year, month)

# -----------------------------
# Agenda (tarjetas)
# -----------------------------
st.subheader("📅 Agenda")

df_agenda = df_view.sort_values("DT").copy()
df_agenda["FECHA_STR"] = df_agenda["FECHA"].dt.strftime("%d/%m/%y")

if df_agenda.empty:
    st.info("No hay turnos que mostrar con los filtros actuales.")
else:
    if modo_movil:
        for _, row in df_agenda.iterrows():
            color = color_map.get(row["TURNO"], "#4da6ff")
            st.markdown(
                f"<div style='padding:10px;border-radius:10px;margin-bottom:6px;background:#f4f6f8;border-left:6px solid {color};'>"
                f"<strong>{row['FECHA_STR']}</strong> · {row['HORA']} · {row['TURNO']}</div>",
                unsafe_allow_html=True,
            )
    else:
        for _, row in df_agenda.iterrows():
            color = color_map.get(row["TURNO"], "#4da6ff")
            st.markdown(
                f"""
                <div style="
                    padding:12px;
                    border-radius:10px;
                    margin-bottom:8px;
                    background-color:#f4f6f8;
                    border-left:6px solid {color};
                ">
                    <strong>{row['FECHA_STR']}</strong>
                    &nbsp;&nbsp;🕒 {row['HORA']}
                    &nbsp;&nbsp;👤 {row['TURNO']}
                </div>
                """,
                unsafe_allow_html=True,
            )

# -----------------------------
# Exportar PDF
# -----------------------------
st.subheader("🧾 Exportar")

pdf_df = df_agenda[["FECHA_STR", "HORA", "TURNO"]].copy()
titulo_pdf = f"Agenda de riego 2026 - {turno_sel} - {mes_sel}"
pdf_bytes = build_pdf(pdf_df, titulo_pdf)

st.download_button(
    label="⬇️ Descargar PDF (agenda filtrada)",
    data=pdf_bytes,
    file_name="agenda_riego_2026.pdf",
    mime="application/pdf",
)
