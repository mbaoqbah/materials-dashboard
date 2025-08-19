import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

def export_reports(db_path="data/app.db", out_dir="reports"):
    engine = create_engine(f"sqlite:///{db_path}", future=True)

    with engine.connect() as conn:
        materials = pd.read_sql("SELECT * FROM materials", conn)
        movements = pd.read_sql("""
            SELECT m.*, mt.description
            FROM material_movements m
            LEFT JOIN materials mt ON mt.material_code = m.material_code
        """, conn)
        phases = pd.read_sql("SELECT * FROM phases", conn)
        worklog = pd.read_sql("SELECT * FROM worklog", conn)

    # Report 1: Count materials received per project
    r1 = movements.groupby("project_no", dropna=False)["material_code"].count().reset_index(name="materials_count")

    # Report 2: Sum quantities per project
    r2 = movements.groupby("project_no", dropna=False)["qty"].sum().reset_index(name="total_qty")

    # Report 3: Project phases status
    r3 = phases.copy()

    # Report 4: Work hours per project and phase
    r4 = worklog.groupby(["project_no","phase_name"], dropna=False)["hours_worked"].sum().reset_index(name="hours_total")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_path = f"{out_dir}/dashboard_reports_{ts}.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        materials.to_excel(writer, index=False, sheet_name="materials_master")
        movements.to_excel(writer, index=False, sheet_name="material_movements")
        r1.to_excel(writer, index=False, sheet_name="materials_count_per_project")
        r2.to_excel(writer, index=False, sheet_name="qty_sum_per_project")
        r3.to_excel(writer, index=False, sheet_name="project_phases")
        r4.to_excel(writer, index=False, sheet_name="work_hours")

    return xlsx_path

if __name__ == "__main__":
    out = export_reports()
    print("Reports exported to:", out)
