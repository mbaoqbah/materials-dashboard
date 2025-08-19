import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import altair as alt
import os
from reports import export_reports

st.set_page_config(page_title="Materials & Projects Dashboard", layout="wide")

DB_PATH = "data/app.db"
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

st.title("📊 Materials & Projects Dashboard")

# Sidebar: Upload data
st.sidebar.header("تحميل/تحديث البيانات (Excel)")
materials_file = st.sidebar.file_uploader("Materials Master (material_code, description)", type=["xlsx"])
movements_file = st.sidebar.file_uploader("Material Movements", type=["xlsx"])
phases_file = st.sidebar.file_uploader("Project Phases", type=["xlsx"])
worklog_file = st.sidebar.file_uploader("Employee Work Log", type=["xlsx"])

def save_uploaded_file(uploaded_file, path):
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())

def run_etl(materials_path, movements_path, phases_path, worklog_path):
    import subprocess, sys
    cmd = [sys.executable, "etl.py",
           "--materials", materials_path,
           "--movements", movements_path,
           "--phases", phases_path,
           "--worklog", worklog_path,
           "--db", DB_PATH]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        st.error(result.stderr)
    else:
        st.success("تم تحديث قاعدة البيانات بنجاح ✅")

if st.sidebar.button("تحديث قاعدة البيانات"):
    if all([materials_file, movements_file, phases_file, worklog_file]):
        os.makedirs("data", exist_ok=True)
        save_uploaded_file(materials_file, "data/materials.xlsx")
        save_uploaded_file(movements_file, "data/movements.xlsx")
        save_uploaded_file(phases_file, "data/phases.xlsx")
        save_uploaded_file(worklog_file, "data/worklog.xlsx")
        run_etl("data/materials.xlsx", "data/movements.xlsx", "data/phases.xlsx", "data/worklog.xlsx")
    else:
        st.warning("رجاءً ارفع كل الملفات الأربعة.")

# Load data
@st.cache_data(show_spinner=False)
def load_tables():
    with engine.connect() as conn:
        materials = pd.read_sql("SELECT * FROM materials", conn)
        movements = pd.read_sql("""
            SELECT m.*, mt.description
            FROM material_movements m
            LEFT JOIN materials mt ON mt.material_code = m.material_code
        """, conn)
        phases = pd.read_sql("SELECT * FROM phases", conn)
        worklog = pd.read_sql("SELECT * FROM worklog", conn)
    return materials, movements, phases, worklog

if os.path.exists(DB_PATH):
    materials, movements, phases, worklog = load_tables()
else:
    st.info("قم بتشغيل ETL أولاً أو ارفع ملفات Excel من الشريط الجانبي.")
    materials = movements = phases = worklog = pd.DataFrame()

# Filters
with st.sidebar:
    st.header("فلاتر")
    projects = sorted(list(set(movements["project_no"].dropna()))) if not movements.empty else []
    project_sel = st.selectbox("اختر مشروع", ["(الكل)"] + projects)
    date_range = None
    if not movements.empty:
        min_d = pd.to_datetime(movements["received_date"], errors="coerce").min()
        max_d = pd.to_datetime(movements["received_date"], errors="coerce").max()
        date_range = st.date_input("نطاق التاريخ (استلام المواد)", value=(min_d, max_d))

# KPIs
col1, col2, col3, col4 = st.columns(4)
if not movements.empty:
    dfm = movements.copy()
    if project_sel != "(الكل)":
        dfm = dfm[dfm["project_no"] == project_sel]
    if date_range and isinstance(date_range, tuple) and len(date_range)==2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        dfm = dfm[(pd.to_datetime(dfm["received_date"])>=start) & (pd.to_datetime(dfm["received_date"])<=end)]
    k_projects = dfm["project_no"].nunique()
    k_total_items = dfm["material_code"].count()
    k_total_qty = dfm["qty"].sum()
    k_locations = dfm["current_location"].nunique()
else:
    k_projects = k_total_items = k_total_qty = k_locations = 0

col1.metric("عدد المشاريع", k_projects)
col2.metric("عدد المواد المستلمة (سجلات)", int(k_total_items))
col3.metric("إجمالي الكميات", float(k_total_qty))
col4.metric("عدد المواقع الحالية", int(k_locations))

st.markdown("---")

# Charts
if not movements.empty:
    dfm = movements.copy()
    if project_sel != "(الكل)":
        dfm = dfm[dfm["project_no"] == project_sel]
    if date_range and isinstance(date_range, tuple) and len(date_range)==2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        dfm = dfm[(pd.to_datetime(dfm["received_date"])>=start) & (pd.to_datetime(dfm["received_date"])<=end)]

    # 1) Materials per project (count)
    per_project = dfm.groupby("project_no", dropna=False)["material_code"].count().reset_index(name="materials_count")
    chart1 = alt.Chart(per_project).mark_bar().encode(
        x=alt.X("project_no:N", title="Project No"),
        y=alt.Y("materials_count:Q", title="عدد المواد المستلمة")
    ).properties(title="عدد المواد المستلمة لكل مشروع")
    st.altair_chart(chart1, use_container_width=True)

    # 2) Quantities per project (sum qty)
    qty_project = dfm.groupby("project_no", dropna=False)["qty"].sum().reset_index(name="total_qty")
    chart2 = alt.Chart(qty_project).mark_bar().encode(
        x=alt.X("project_no:N", title="Project No"),
        y=alt.Y("total_qty:Q", title="إجمالي الكميات")
    ).properties(title="إجمالي الكميات لكل مشروع")
    st.altair_chart(chart2, use_container_width=True)

    # 3) Timeline of receipts
    dfm["received_date"] = pd.to_datetime(dfm["received_date"], errors="coerce")
    timeline = dfm.groupby("received_date")["qty"].sum().reset_index()
    chart3 = alt.Chart(timeline).mark_line(point=True).encode(
        x=alt.X("received_date:T", title="تاريخ الاستلام"),
        y=alt.Y("qty:Q", title="إجمالي الكميات اليومية")
    ).properties(title="حركة استلام المواد عبر الزمن")
    st.altair_chart(chart3, use_container_width=True)

# Phases Gantt-like
st.subheader("مراحل المشروع (Gantt)")
if not phases.empty:
    ph = phases.copy()
    if project_sel != "(الكل)":
        ph = ph[ph["project_no"] == project_sel]
    ph["phase_start"] = pd.to_datetime(ph["phase_start"], errors="coerce")
    ph["phase_end"] = pd.to_datetime(ph["phase_end"], errors="coerce")
    gantt = alt.Chart(ph).mark_bar().encode(
        x=alt.X("phase_start:T", title="Start"),
        x2=alt.X2("phase_end:T"),
        y=alt.Y("phase_name:N", title="Phase"),
        tooltip=["project_no","phase_name","phase_type","status","phase_start","phase_end"]
    ).properties(height=400)
    st.altair_chart(gantt, use_container_width=True)
else:
    st.info("لا توجد مراحل بعد.")

# Worklog summary
st.subheader("سجل عمل الموظفين")
if 'worklog' in locals() and not worklog.empty:
    wl = worklog.copy()
    if project_sel != "(الكل)":
        wl = wl[wl["project_no"] == project_sel]
    hours = wl.groupby(["employee_name"], dropna=False)["hours_worked"].sum().reset_index(name="hours_total")
    chart_w = alt.Chart(hours).mark_bar().encode(
        x=alt.X("employee_name:N", title="الموظف"),
        y=alt.Y("hours_total:Q", title="إجمالي الساعات")
    ).properties(title="إجمالي ساعات العمل لكل موظف")
    st.altair_chart(chart_w, use_container_width=True)
else:
    st.info("لا يوجد سجل عمل موظفين بعد.")

# Data tables
st.markdown("---")
st.subheader("الجداول التفصيلية")
with st.expander("Materials Master"):
    if materials is not None:
        st.dataframe(materials)
with st.expander("Material Movements"):
    if movements is not None:
        st.dataframe(movements)
with st.expander("Project Phases"):
    if phases is not None:
        st.dataframe(phases)
with st.expander("Employee Work Log"):
    if 'worklog' in locals() and worklog is not None:
        st.dataframe(worklog)

# Export reports
st.markdown("---")
if st.button("تصدير تقارير Excel"):
    out = export_reports(db_path=DB_PATH, out_dir="reports")
    st.success(f"تم إنشاء التقارير: {out}")
    st.download_button("تحميل ملف التقارير", data=open(out, "rb").read(), file_name=os.path.basename(out))
