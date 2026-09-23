"""
database.py - SQLite Database Management Layer
Project: Student Skill Graph & Team Builder
Course Context: Python & DBMS College Project

Demonstrates:
- SQLite3 integration in Python
- DDL: CREATE TABLE with PRIMARY KEY, FOREIGN KEY, and ON DELETE CASCADE
- DML: INSERT, UPDATE, DELETE, and SELECT operations
- Relational JOINs: INNER JOIN, LEFT JOIN, GROUP BY, aggregation
- Transaction management and connection pooling
"""

import sqlite3
import os
import shutil

import tempfile

ORIGINAL_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.db")

def get_db_path():
    """
    Returns the appropriate path for the SQLite database.
    On Vercel (or serverless environments where root directory is read-only),
    copies the seeded skills.db to /tmp/skills.db so write operations (INSERT/UPDATE/DELETE) succeed.
    """
    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
        tmp_db = os.path.join(tmp_dir, "skills.db")
        if not os.path.exists(tmp_db):
            if os.path.exists(ORIGINAL_DB_PATH):
                try:
                    shutil.copy2(ORIGINAL_DB_PATH, tmp_db)
                except Exception as e:
                    print(f"Warning: Failed to copy SQLite database to temp: {e}")
        return tmp_db
    return ORIGINAL_DB_PATH

DB_PATH = get_db_path()


def get_db_connection():
    """
    Establish a connection to the SQLite database with Foreign Keys enabled
    and dictionary-like Row access.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    # Crucial DBMS concept: Enable Foreign Key constraint enforcement in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Initialize SQLite schema for all 7 required tables.
    If the database is newly created, populates realistic college demo data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            year INTEGER NOT NULL,
            availability TEXT NOT NULL,
            interests TEXT NOT NULL,
            password TEXT NOT NULL DEFAULT 'student123'
        );
    """)

    # Ensure password column exists on existing students table
    cursor.execute("PRAGMA table_info(students);")
    student_cols = [row["name"] for row in cursor.fetchall()]
    if "password" not in student_cols:
        cursor.execute("ALTER TABLE students ADD COLUMN password TEXT NOT NULL DEFAULT 'student123';")
        conn.commit()

    # 2. skills table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL
        );
    """)

    # 3. student_skills table (Many-to-Many junction between students and skills)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            proficiency TEXT NOT NULL CHECK(proficiency IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
            UNIQUE(student_id, skill_id)
        );
    """)

    # 4. projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            description TEXT,
            team_size INTEGER NOT NULL DEFAULT 4,
            status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open', 'In Progress', 'Completed'))
        );
    """)

    # 5. project_skills table (Many-to-Many junction between projects and skills)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            importance TEXT NOT NULL CHECK(importance IN ('High', 'Medium', 'Low')),
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
            UNIQUE(project_id, skill_id)
        );
    """)

    # 6. teams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            team_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Recommended' CHECK(status IN ('Recommended', 'Approved', 'Rejected')),
            coverage_score REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
        );
    """)

    # 7. team_members table (Many-to-Many junction between teams and students)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            UNIQUE(team_id, student_id)
        );
    """)

    # 8. faculty table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL,
            designation TEXT NOT NULL DEFAULT 'Assistant Professor',
            password TEXT NOT NULL DEFAULT 'faculty123'
        );
    """)

    conn.commit()

    # Seed initial faculty record if empty
    cursor.execute("SELECT COUNT(*) FROM faculty;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO faculty (name, email, department, designation, password)
            VALUES ('Dr. S. K. Raman', 'faculty@college.edu', 'Computer Science & Engineering', 'Faculty Advisor & Professor', 'faculty123');
        """)
        conn.commit()

    # Seed initial data if students table is empty
    cursor.execute("SELECT COUNT(*) FROM students;")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn):
    """Seed comprehensive realistic college data for demonstration."""
    cursor = conn.cursor()

    # 1. Insert Skills
    skills_data = [
        ("Python", "Programming"),
        ("SQL", "Database"),
        ("Database", "Database"),
        ("Java", "Programming"),
        ("C++", "Programming"),
        ("JavaScript", "Web Development"),
        ("React", "Web Development"),
        ("Machine Learning", "AI / Data Science"),
        ("Data Science", "AI / Data Science"),
        ("UI/UX", "Design"),
        ("Cyber Security", "Security"),
        ("Communication", "Soft Skills"),
        ("Presentation", "Soft Skills"),
        ("PostgreSQL", "Database"),
        ("Project Management", "Management")
    ]
    cursor.executemany(
        "INSERT INTO skills (skill_name, category) VALUES (?, ?);",
        skills_data
    )

    # Map skill_name to skill_id
    cursor.execute("SELECT skill_id, skill_name FROM skills;")
    skill_map = {row["skill_name"]: row["skill_id"] for row in cursor.fetchall()}

    # 2. Insert Students
    students_data = [
        ("Aditya Sharma", "aditya@college.edu", "Computer Science", 2, "High", "Full-stack Web, Database Systems"),
        ("Rohit Verma", "rohit@college.edu", "Information Technology", 2, "High", "Backend Engineering, Relational DBMS"),
        ("Aryan Gupta", "aryan@college.edu", "Computer Science", 3, "Medium", "Frontend Design, UI/UX Prototyping"),
        ("Pranab Mukherjee", "pranab@college.edu", "Computer Science", 2, "High", "Project Coordination, Public Speaking"),
        ("Sneha Patel", "sneha@college.edu", "Data Science", 3, "High", "Machine Learning, Predictive Analytics"),
        ("Ananya Iyer", "ananya@college.edu", "Information Technology", 2, "Medium", "Frontend Web Apps, React Components"),
        ("Vikram Singh", "vikram@college.edu", "Cyber Security", 3, "High", "Network Defense, Systems Programming"),
        ("Pooja Nair", "pooja@college.edu", "Computer Science", 2, "Medium", "Enterprise Java, Database Optimization"),
        ("Rahul Joshi", "rahul@college.edu", "Data Science", 2, "High", "Deep Learning, Natural Language Processing"),
        ("Meera Rao", "meera@college.edu", "Design & Computing", 3, "High", "Human-Computer Interaction, Design Systems"),
        ("Karthik Menon", "karthik@college.edu", "Computer Science", 1, "Medium", "Algorithm Design, C++ Competitive Coding"),
        ("Tanvi Deshmukh", "tanvi@college.edu", "Information Technology", 3, "High", "Full-stack JavaScript, Modern Web"),
        ("Nikhil Kulkarni", "nikhil@college.edu", "Computer Science", 2, "High", "SQL Query Tuning, Cloud Databases"),
        ("Divya Sen", "divya@college.edu", "Cyber Security", 2, "Medium", "Security Auditing, Technical Communication")
    ]

    cursor.executemany(
        """
        INSERT INTO students (name, email, department, year, availability, interests)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        students_data
    )

    # Map student name to student_id
    cursor.execute("SELECT student_id, name FROM students;")
    student_map = {row["name"]: row["student_id"] for row in cursor.fetchall()}

    # 3. Insert Student Skills
    student_skills_data = [
        # Aditya: Python (Advanced), SQL (Intermediate), Database (Intermediate)
        (student_map["Aditya Sharma"], skill_map["Python"], "Advanced"),
        (student_map["Aditya Sharma"], skill_map["SQL"], "Intermediate"),
        (student_map["Aditya Sharma"], skill_map["Database"], "Intermediate"),

        # Rohit: Database (Advanced), SQL (Advanced), Python (Advanced)
        (student_map["Rohit Verma"], skill_map["Database"], "Advanced"),
        (student_map["Rohit Verma"], skill_map["SQL"], "Advanced"),
        (student_map["Rohit Verma"], skill_map["Python"], "Advanced"),

        # Aryan: UI/UX (Advanced), React (Intermediate), JavaScript (Intermediate)
        (student_map["Aryan Gupta"], skill_map["UI/UX"], "Advanced"),
        (student_map["Aryan Gupta"], skill_map["React"], "Intermediate"),
        (student_map["Aryan Gupta"], skill_map["JavaScript"], "Intermediate"),

        # Pranab: Communication (Advanced), Presentation (Advanced), Project Management (Intermediate)
        (student_map["Pranab Mukherjee"], skill_map["Communication"], "Advanced"),
        (student_map["Pranab Mukherjee"], skill_map["Presentation"], "Advanced"),
        (student_map["Pranab Mukherjee"], skill_map["Project Management"], "Intermediate"),

        # Sneha: Machine Learning (Advanced), Data Science (Advanced), Python (Advanced)
        (student_map["Sneha Patel"], skill_map["Machine Learning"], "Advanced"),
        (student_map["Sneha Patel"], skill_map["Data Science"], "Advanced"),
        (student_map["Sneha Patel"], skill_map["Python"], "Advanced"),

        # Ananya: React (Advanced), JavaScript (Advanced), UI/UX (Intermediate)
        (student_map["Ananya Iyer"], skill_map["React"], "Advanced"),
        (student_map["Ananya Iyer"], skill_map["JavaScript"], "Advanced"),
        (student_map["Ananya Iyer"], skill_map["UI/UX"], "Intermediate"),

        # Vikram: Cyber Security (Advanced), C++ (Advanced), Python (Intermediate)
        (student_map["Vikram Singh"], skill_map["Cyber Security"], "Advanced"),
        (student_map["Vikram Singh"], skill_map["C++"], "Advanced"),
        (student_map["Vikram Singh"], skill_map["Python"], "Intermediate"),

        # Pooja: Java (Advanced), Database (Intermediate), SQL (Intermediate)
        (student_map["Pooja Nair"], skill_map["Java"], "Advanced"),
        (student_map["Pooja Nair"], skill_map["Database"], "Intermediate"),
        (student_map["Pooja Nair"], skill_map["SQL"], "Intermediate"),

        # Rahul: Machine Learning (Intermediate), Python (Advanced), Communication (Intermediate)
        (student_map["Rahul Joshi"], skill_map["Machine Learning"], "Intermediate"),
        (student_map["Rahul Joshi"], skill_map["Python"], "Advanced"),
        (student_map["Rahul Joshi"], skill_map["Communication"], "Intermediate"),

        # Meera: UI/UX (Expert), Presentation (Advanced), Communication (Advanced)
        (student_map["Meera Rao"], skill_map["UI/UX"], "Expert"),
        (student_map["Meera Rao"], skill_map["Presentation"], "Advanced"),
        (student_map["Meera Rao"], skill_map["Communication"], "Advanced"),

        # Karthik: C++ (Advanced), Java (Intermediate), SQL (Beginner)
        (student_map["Karthik Menon"], skill_map["C++"], "Advanced"),
        (student_map["Karthik Menon"], skill_map["Java"], "Intermediate"),
        (student_map["Karthik Menon"], skill_map["SQL"], "Beginner"),

        # Tanvi: JavaScript (Advanced), React (Intermediate), UI/UX (Intermediate)
        (student_map["Tanvi Deshmukh"], skill_map["JavaScript"], "Advanced"),
        (student_map["Tanvi Deshmukh"], skill_map["React"], "Intermediate"),
        (student_map["Tanvi Deshmukh"], skill_map["UI/UX"], "Intermediate"),

        # Nikhil: Database (Advanced), PostgreSQL (Advanced), Python (Intermediate)
        (student_map["Nikhil Kulkarni"], skill_map["Database"], "Advanced"),
        (student_map["Nikhil Kulkarni"], skill_map["PostgreSQL"], "Advanced"),
        (student_map["Nikhil Kulkarni"], skill_map["Python"], "Intermediate"),

        # Divya: Cyber Security (Intermediate), Python (Intermediate), Communication (Advanced)
        (student_map["Divya Sen"], skill_map["Cyber Security"], "Intermediate"),
        (student_map["Divya Sen"], skill_map["Python"], "Intermediate"),
        (student_map["Divya Sen"], skill_map["Communication"], "Advanced")
    ]

    cursor.executemany(
        """
        INSERT INTO student_skills (student_id, skill_id, proficiency)
        VALUES (?, ?, ?);
        """,
        student_skills_data
    )

    # 4. Insert Projects
    projects_data = [
        ("Smart Campus Management System", "A comprehensive web portal for attendance, room booking, and student announcements.", 4, "Open"),
        ("AI Healthcare Diagnosis Assistant", "An intelligent diagnostic tool analyzing patient symptoms and lab records.", 4, "Open"),
        ("Modern E-Commerce Platform", "Next-generation multi-vendor shopping cart with real-time inventory and payment gateway.", 3, "Open"),
        ("Campus Network Threat Scanner", "Security auditing utility for monitoring network vulnerability and anomalies.", 3, "Open")
    ]

    cursor.executemany(
        """
        INSERT INTO projects (project_name, description, team_size, status)
        VALUES (?, ?, ?, ?);
        """,
        projects_data
    )

    cursor.execute("SELECT project_id, project_name FROM projects;")
    project_map = {row["project_name"]: row["project_id"] for row in cursor.fetchall()}

    # 5. Insert Project Skills
    project_skills_data = [
        # Smart Campus: Python (High), Database (High), UI/UX (Medium), Communication (Medium)
        (project_map["Smart Campus Management System"], skill_map["Python"], "High"),
        (project_map["Smart Campus Management System"], skill_map["Database"], "High"),
        (project_map["Smart Campus Management System"], skill_map["UI/UX"], "Medium"),
        (project_map["Smart Campus Management System"], skill_map["Communication"], "Medium"),

        # AI Healthcare: Python (High), Machine Learning (High), Data Science (Medium), Presentation (Medium)
        (project_map["AI Healthcare Diagnosis Assistant"], skill_map["Python"], "High"),
        (project_map["AI Healthcare Diagnosis Assistant"], skill_map["Machine Learning"], "High"),
        (project_map["AI Healthcare Diagnosis Assistant"], skill_map["Data Science"], "Medium"),
        (project_map["AI Healthcare Diagnosis Assistant"], skill_map["Presentation"], "Medium"),

        # E-Commerce Platform: React (High), JavaScript (High), Database (Medium), UI/UX (High)
        (project_map["Modern E-Commerce Platform"], skill_map["React"], "High"),
        (project_map["Modern E-Commerce Platform"], skill_map["JavaScript"], "High"),
        (project_map["Modern E-Commerce Platform"], skill_map["Database"], "Medium"),
        (project_map["Modern E-Commerce Platform"], skill_map["UI/UX"], "High"),

        # Campus Threat Scanner: Cyber Security (High), Python (High), C++ (Medium), Communication (Low)
        (project_map["Campus Network Threat Scanner"], skill_map["Cyber Security"], "High"),
        (project_map["Campus Network Threat Scanner"], skill_map["Python"], "High"),
        (project_map["Campus Network Threat Scanner"], skill_map["C++"], "Medium"),
        (project_map["Campus Network Threat Scanner"], skill_map["Communication"], "Low"),
    ]

    cursor.executemany(
        """
        INSERT INTO project_skills (project_id, skill_id, importance)
        VALUES (?, ?, ?);
        """,
        project_skills_data
    )

    # 6. Insert 1 Pre-existing Approved Sample Team (Demonstrating teams and team_members)
    p1_id = project_map["Smart Campus Management System"]
    cursor.execute("""
        INSERT INTO teams (project_id, team_name, status, coverage_score)
        VALUES (?, 'TEAM NOVA', 'Approved', 92.5);
    """, (p1_id,))
    team_id = cursor.lastrowid

    # Members: Aditya, Rohit, Aryan, Pranab
    team_members_data = [
        (team_id, student_map["Aditya Sharma"]),
        (team_id, student_map["Rohit Verma"]),
        (team_id, student_map["Aryan Gupta"]),
        (team_id, student_map["Pranab Mukherjee"])
    ]
    cursor.executemany(
        """
        INSERT INTO team_members (team_id, student_id)
        VALUES (?, ?);
        """,
        team_members_data
    )

    conn.commit()


# ==========================================
# CRUD Operations & Query Demonstrations
# ==========================================

def get_all_students():
    """Demonstrates SELECT with GROUP_CONCAT and LEFT JOIN."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            s.student_id, s.name, s.email, s.department, s.year, s.availability, s.interests,
            COUNT(ss.skill_id) AS skill_count
        FROM students s
        LEFT JOIN student_skills ss ON s.student_id = ss.student_id
        GROUP BY s.student_id
        ORDER BY s.student_id ASC;
    """
    students = [dict(row) for row in cursor.execute(query).fetchall()]
    conn.close()
    return students


def get_student_by_id(student_id):
    """Demonstrates SELECT single row and JOIN to fetch student skills."""
    conn = get_db_connection()
    cursor = conn.cursor()
    student = cursor.execute("SELECT * FROM students WHERE student_id = ?;", (student_id,)).fetchone()
    if not student:
        conn.close()
        return None

    student_dict = dict(student)

    # Fetch skills via INNER JOIN
    skills_query = """
        SELECT 
            ss.id AS record_id,
            s.skill_id,
            s.skill_name,
            s.category,
            ss.proficiency
        FROM student_skills ss
        INNER JOIN skills s ON ss.skill_id = s.skill_id
        WHERE ss.student_id = ?
        ORDER BY s.skill_name ASC;
    """
    student_dict["skills"] = [dict(row) for row in cursor.execute(skills_query, (student_id,)).fetchall()]

    # Fetch active projects for this student
    projects_query = """
        SELECT 
            p.project_id, p.project_name, t.team_name, t.status AS team_status
        FROM team_members tm
        INNER JOIN teams t ON tm.team_id = t.team_id
        INNER JOIN projects p ON t.project_id = p.project_id
        WHERE tm.student_id = ?;
    """
    student_dict["projects"] = [dict(row) for row in cursor.execute(projects_query, (student_id,)).fetchall()]

    conn.close()
    return student_dict


def get_student_by_email(email):
    """Demonstrates SELECT student by unique email."""
    if not email:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    student = cursor.execute(
        "SELECT * FROM students WHERE LOWER(email) = LOWER(?);",
        (email.strip(),)
    ).fetchone()
    conn.close()
    return dict(student) if student else None


def create_student(data):
    """
    Demonstrates INSERT operation into students table.
    Creates a new student profile and returns the new student_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    password = (data.get("password") or "student123").strip() or "student123"
    cursor.execute("""
        INSERT INTO students (name, email, department, year, availability, interests, password)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        data.get("name", "").strip(),
        data.get("email", "").strip().lower(),
        data.get("department", "Computer Science"),
        int(data.get("year", 1)),
        data.get("availability", "High"),
        data.get("interests", "Full-stack Web, Relational Databases"),
        password
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_faculty():
    """Demonstrates SELECT all records from faculty table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    faculty = [dict(row) for row in cursor.execute("SELECT faculty_id, name, email, department, designation FROM faculty ORDER BY faculty_id ASC;").fetchall()]
    conn.close()
    return faculty


def get_faculty_by_email(email):
    """Demonstrates SELECT faculty member by unique email."""
    if not email:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM faculty WHERE LOWER(email) = LOWER(?);", (email.strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_faculty_by_id(faculty_id):
    """Demonstrates SELECT faculty member by primary key."""
    if not faculty_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM faculty WHERE faculty_id = ?;", (faculty_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_faculty(data):
    """
    Demonstrates INSERT operation into faculty table.
    Creates a new faculty member profile and returns new faculty_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO faculty (name, email, department, designation, password)
        VALUES (?, ?, ?, ?, ?);
    """, (
        data.get("name", "").strip(),
        data.get("email", "").strip().lower(),
        data.get("department", "Computer Science & Engineering"),
        data.get("designation", "Assistant Professor"),
        data.get("password", "faculty123").strip() or "faculty123"
    ))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_student_profile(student_id, data):
    """Demonstrates UPDATE operation on SQLite table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET name = ?, email = ?, department = ?, year = ?, availability = ?, interests = ?
        WHERE student_id = ?;
    """, (
        data.get("name"),
        data.get("email"),
        data.get("department"),
        int(data.get("year", 1)),
        data.get("availability"),
        data.get("interests"),
        student_id
    ))
    conn.commit()
    conn.close()
    return True


def add_student_skill(student_id, skill_id, proficiency):
    """Demonstrates INSERT OR REPLACE in junction table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO student_skills (student_id, skill_id, proficiency)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, skill_id) DO UPDATE SET proficiency = excluded.proficiency;
    """, (student_id, skill_id, proficiency))
    conn.commit()
    conn.close()
    return True


def remove_student_skill(student_id, skill_id):
    """Demonstrates DELETE operation on junction table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM student_skills
        WHERE student_id = ? AND skill_id = ?;
    """, (student_id, skill_id))
    conn.commit()
    conn.close()
    return True


def get_all_skills():
    """Retrieve all available skills."""
    conn = get_db_connection()
    cursor = conn.cursor()
    skills = [dict(row) for row in cursor.execute("SELECT * FROM skills ORDER BY category, skill_name;").fetchall()]
    conn.close()
    return skills


def create_skill(skill_name, category):
    """Insert a new skill."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO skills (skill_name, category) VALUES (?, ?);", (skill_name.strip(), category.strip()))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_all_projects():
    """
    Demonstrates complex relational query:
    Fetches projects with required skills (nested aggregation via JOIN).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    projects = [dict(row) for row in cursor.execute("SELECT * FROM projects ORDER BY project_id DESC;").fetchall()]

    for proj in projects:
        skills_query = """
            SELECT 
                s.skill_id,
                s.skill_name,
                s.category,
                ps.importance
            FROM project_skills ps
            INNER JOIN skills s ON ps.skill_id = s.skill_id
            WHERE ps.project_id = ?
            ORDER BY 
                CASE ps.importance
                    WHEN 'High' THEN 1
                    WHEN 'Medium' THEN 2
                    WHEN 'Low' THEN 3
                    ELSE 4
                END;
        """
        proj["required_skills"] = [dict(r) for r in cursor.execute(skills_query, (proj["project_id"],)).fetchall()]

        # Check existing teams with member details
        teams_query = """
            SELECT team_id, team_name, status, coverage_score
            FROM teams
            WHERE project_id = ?
            ORDER BY team_id DESC;
        """
        teams = [dict(r) for r in cursor.execute(teams_query, (proj["project_id"],)).fetchall()]
        for t in teams:
            m_query = """
                SELECT s.student_id, s.name, s.department, s.year, s.email
                FROM team_members tm
                INNER JOIN students s ON tm.student_id = s.student_id
                WHERE tm.team_id = ?;
            """
            t["members"] = [dict(m) for m in cursor.execute(m_query, (t["team_id"],)).fetchall()]
        proj["teams"] = teams

    conn.close()
    return projects


def get_project_by_id(project_id):
    """Fetch single project with required skills."""
    conn = get_db_connection()
    cursor = conn.cursor()
    proj = cursor.execute("SELECT * FROM projects WHERE project_id = ?;", (project_id,)).fetchone()
    if not proj:
        conn.close()
        return None

    proj_dict = dict(proj)
    skills_query = """
        SELECT s.skill_id, s.skill_name, s.category, ps.importance
        FROM project_skills ps
        INNER JOIN skills s ON ps.skill_id = s.skill_id
        WHERE ps.project_id = ?;
    """
    proj_dict["required_skills"] = [dict(r) for r in cursor.execute(skills_query, (project_id,)).fetchall()]
    conn.close()
    return proj_dict


def create_project(project_name, description, team_size, required_skills):
    """
    Demonstrates multi-table transactional INSERT.
    Inserts into `projects` then links rows in `project_skills`.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO projects (project_name, description, team_size, status)
        VALUES (?, ?, ?, 'Open');
    """, (project_name, description, int(team_size)))
    project_id = cursor.lastrowid

    for item in required_skills:
        skill_id = item.get("skill_id")
        importance = item.get("importance", "Medium")
        cursor.execute("""
            INSERT INTO project_skills (project_id, skill_id, importance)
            VALUES (?, ?, ?);
        """, (project_id, skill_id, importance))

    conn.commit()
    conn.close()
    return project_id


def save_team(project_id, team_name, coverage_score, member_ids, status="Recommended"):
    """
    Insert a newly formed team and its member associations.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO teams (project_id, team_name, status, coverage_score)
        VALUES (?, ?, ?, ?);
    """, (project_id, team_name, status, float(coverage_score)))
    team_id = cursor.lastrowid

    for sid in member_ids:
        cursor.execute("""
            INSERT INTO team_members (team_id, student_id)
            VALUES (?, ?);
        """, (team_id, sid))

    conn.commit()
    conn.close()
    return team_id


def update_team_status(team_id, status):
    """Approve or reject a recommended team."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE teams SET status = ? WHERE team_id = ?;", (status, team_id))

    if status == "Approved":
        # Also mark project as In Progress
        cursor.execute("""
            UPDATE projects
            SET status = 'In Progress'
            WHERE project_id = (SELECT project_id FROM teams WHERE team_id = ?);
        """, (team_id,))

    conn.commit()
    conn.close()
    return True


def get_all_teams():
    """
    Fetch all teams with their project name, coverage score, and full member details.
    Demonstrates 3-way JOIN across teams, projects, and students.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            t.team_id,
            t.team_name,
            t.status,
            t.coverage_score,
            p.project_id,
            p.project_name,
            p.team_size
        FROM teams t
        INNER JOIN projects p ON t.project_id = p.project_id
        ORDER BY t.team_id DESC;
    """
    teams = [dict(row) for row in cursor.execute(query).fetchall()]

    for team in teams:
        members_query = """
            SELECT 
                s.student_id,
                s.name,
                s.email,
                s.department,
                s.year,
                s.availability
            FROM team_members tm
            INNER JOIN students s ON tm.student_id = s.student_id
            WHERE tm.team_id = ?;
        """
        members = [dict(m) for m in cursor.execute(members_query, (team["team_id"],)).fetchall()]
        
        # Attach each member's skills
        for m in members:
            sk_q = """
                SELECT s.skill_name, ss.proficiency
                FROM student_skills ss
                INNER JOIN skills s ON ss.skill_id = s.skill_id
                WHERE ss.student_id = ?;
            """
            m["skills"] = [dict(r) for r in cursor.execute(sk_q, (m["student_id"],)).fetchall()]
        
        team["members"] = members

    conn.close()
    return teams


def get_faculty_stats():
    """
    Aggregation metrics and distributions for Chart.js in Faculty Dashboard.
    Demonstrates COUNT, GROUP BY, and aggregations.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # KPI counts
    total_students = cursor.execute("SELECT COUNT(*) FROM students;").fetchone()[0]
    total_skills = cursor.execute("SELECT COUNT(*) FROM skills;").fetchone()[0]
    total_projects = cursor.execute("SELECT COUNT(*) FROM projects;").fetchone()[0]
    total_teams = cursor.execute("SELECT COUNT(*) FROM teams;").fetchone()[0]
    approved_teams = cursor.execute("SELECT COUNT(*) FROM teams WHERE status = 'Approved';").fetchone()[0]

    # Chart 1: Most common skills among students (Skill Distribution)
    skill_dist_query = """
        SELECT s.skill_name, COUNT(ss.student_id) AS student_count
        FROM skills s
        LEFT JOIN student_skills ss ON s.skill_id = ss.skill_id
        GROUP BY s.skill_id
        ORDER BY student_count DESC
        LIMIT 10;
    """
    skill_distribution = [dict(r) for r in cursor.execute(skill_dist_query).fetchall()]

    # Chart 2: Skills by Category
    category_query = """
        SELECT category, COUNT(skill_id) AS count
        FROM skills
        GROUP BY category
        ORDER BY count DESC;
    """
    category_distribution = [dict(r) for r in cursor.execute(category_query).fetchall()]

    # Chart 3: Department breakdown
    dept_query = """
        SELECT department, COUNT(student_id) AS count
        FROM students
        GROUP BY department;
    """
    dept_distribution = [dict(r) for r in cursor.execute(dept_query).fetchall()]

    conn.close()

    return {
        "kpis": {
            "total_students": total_students,
            "total_skills": total_skills,
            "total_projects": total_projects,
            "total_teams": total_teams,
            "approved_teams": approved_teams
        },
        "skill_distribution": skill_distribution,
        "category_distribution": category_distribution,
        "dept_distribution": dept_distribution
    }
