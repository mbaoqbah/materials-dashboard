import argparse
import pandas as pd
from sqlalchemy import create_engine, text

def upsert(engine, df: pd.DataFrame, table: str, unique_cols: list):
    # Simple upsert: delete matching keys then insert
    with engine.begin() as conn:
        if not df.empty:
            # Build delete statements by unique keys
            for _, row in df.iterrows():
                where = " AND ".join([f"{c} = :{c}" for c in unique_cols])
                conn.execute(text(f"DELETE FROM {table} WHERE {where}"), {c: row[c] for c in unique_cols})
            df.to_sql(table, conn, if_exists="append", index=False)

def ensure_projects_from_movements(engine):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO projects (project_no, project_start, project_end)
            SELECT DISTINCT project_no, MIN(received_date), MAX(received_date)
            FROM material_movements
            WHERE project_no IS NOT NULL AND project_no <> ''
            GROUP BY project_no
            ON CONFLICT(project_no) DO NOTHING;
        """))

def load_materials(engine, path):
    df = pd.read_excel(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={"materialcode":"material_code"})
    df = df[["material_code","description"]]
    df["material_code"] = df["material_code"].astype(str).str.strip()
    df["description"] = df["description"].astype(str).str.strip()
    upsert(engine, df.drop_duplicates(subset=["material_code"]), "materials", ["material_code"])

def load_movements(engine, path):
    df = pd.read_excel(path, dtype={"Material Request No": str, "Project No": str})
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Expected columns: material_code, qty, received_date, material_request_no, project_no, project_start, project_end, current_location
    df["material_code"] = df["material_code"].astype(str).str.strip()
    # Insert into movements
    mov_cols = ["material_code","qty","received_date","material_request_no","project_no","current_location"]
    upsert(engine, df[mov_cols], "material_movements", ["material_code","received_date","project_no","material_request_no"])
    # Maintain projects table from project_start/end if provided
    if "project_start" in df.columns or "project_end" in df.columns:
        proj = df[["project_no","project_start","project_end"]].drop_duplicates()
        proj = proj[proj["project_no"].notna() & (proj["project_no"]!="")]
        upsert(engine, proj, "projects", ["project_no"])
    ensure_projects_from_movements(engine)

def load_phases(engine, path):
    df = pd.read_excel(path, dtype={"Project No": str})
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Expected: project_no, phase_name, phase_type, phase_start, phase_end, status
    upsert(engine, df, "phases", ["project_no","phase_name"])

def load_worklog(engine, path):
    df = pd.read_excel(path, dtype={"Project No": str})
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # Expected: project_no, phase_name, employee_id, employee_name, start_time, end_time, hours_worked
    upsert(engine, df, "worklog", ["project_no","phase_name","employee_id","start_time","end_time"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--materials", required=True)
    parser.add_argument("--movements", required=True)
    parser.add_argument("--phases", required=True)
    parser.add_argument("--worklog", required=True)
    parser.add_argument("--db", default="data/app.db")
    args = parser.parse_args()

    engine = create_engine(f"sqlite:///{args.db}", future=True)

    # Create schema
    with engine.begin() as conn:
        with open("models.sql","r",encoding="utf-8") as f:
            conn.exec_driver_sql(f.read())

    load_materials(engine, args.materials)
    load_movements(engine, args.movements)
    load_phases(engine, args.phases)
    load_worklog(engine, args.worklog)

    print("ETL completed successfully. Database:", args.db)
