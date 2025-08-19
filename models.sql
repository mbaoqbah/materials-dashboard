
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS materials (
    material_code TEXT PRIMARY KEY,
    description   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    project_no    TEXT PRIMARY KEY,
    project_start DATE,
    project_end   DATE
);

CREATE TABLE IF NOT EXISTS material_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_code TEXT NOT NULL,
    qty           REAL NOT NULL,
    received_date DATE NOT NULL,
    material_request_no TEXT,
    project_no    TEXT,
    current_location TEXT,
    FOREIGN KEY (material_code) REFERENCES materials(material_code),
    FOREIGN KEY (project_no) REFERENCES projects(project_no)
);

CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_no  TEXT NOT NULL,
    phase_name  TEXT NOT NULL,
    phase_type  TEXT,
    phase_start DATE,
    phase_end   DATE,
    status      TEXT,
    FOREIGN KEY (project_no) REFERENCES projects(project_no)
);

CREATE TABLE IF NOT EXISTS worklog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_no   TEXT NOT NULL,
    phase_name   TEXT NOT NULL,
    employee_id  TEXT,
    employee_name TEXT,
    start_time   DATE,
    end_time     DATE,
    hours_worked REAL,
    FOREIGN KEY (project_no) REFERENCES projects(project_no)
);
