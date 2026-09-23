"""
app.py - Main Flask Application Backend
Project: Student Skill Graph & Team Builder
Course Context: Python & DBMS College Project

Exposes RESTful APIs for:
- Student Profile and Skill Management (CRUD)
- Project Definition and Skill Weight Assignment (CRUD)
- Transparent Rule-Based Team Recommendation Algorithm
- NetworkX Graph Generation and Centrality Metrics
- DBMS Viva Showcase and SQL Join Inspector
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import database as db
import recommendation as rec
import graph_builder as gb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static"
)
app.secret_key = "college_project_secret_key_student_skills_graph"

# Ensure database tables exist and sample data is seeded
db.init_db()


# ==========================================
# Frontend Routes
# ==========================================

@app.route("/index")
@app.route("/index.html")
@app.route("/api")
@app.route("/api/")
@app.route("/api/index")
@app.route("/api/index.py")
@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("index.html")


@app.route("/login.html")
@app.route("/login")
def login_page():
    """Renders the dedicated Student and Faculty Login page."""
    if session.get("logged_in"):
        return redirect(url_for("index"))
    students = db.get_all_students()
    faculty_members = db.get_all_faculty()
    return render_template("login.html", students=students, faculty_members=faculty_members)


@app.route("/logout")
def logout():
    """Clears the session and redirects to the login page."""
    session.clear()
    return redirect(url_for("login_page"))


@app.errorhandler(404)
def page_not_found(e):
    """
    Fallback handler for SPA navigation and Vercel serverless rewrites.
    Renders index.html for authenticated users or redirects to login.
    """
    if request.path.startswith("/api/") and not (request.path.startswith("/api/index") or request.path in ["/api", "/api/"]):
        return jsonify({"error": "API route not found", "path": request.path}), 404
    if not session.get("logged_in"):
        return redirect(url_for("login_page"))
    return render_template("index.html")


# ==========================================
# Authentication & Session APIs
# ==========================================

@app.route("/api/login", methods=["POST"])
def api_login():
    """
    Demonstrates student and faculty authentication.
    Queries the SQLite students or faculty tables for email verification.
    """
    data = request.json or {}
    role = data.get("role", "student")
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "").strip()

    if not email:
        return jsonify({"error": "Email address is required"}), 400

    if role == "faculty":
        # Check SQLite faculty table
        faculty = db.get_faculty_by_email(email)
        if faculty:
            stored_password = faculty.get("password") or "faculty123"
            if password != stored_password:
                return jsonify({
                    "error": "Incorrect password. Please enter the correct password."
                }), 401

            session["logged_in"] = True
            session["role"] = "faculty"
            session["faculty_id"] = faculty["faculty_id"]
            session["user_name"] = faculty["name"]
            return jsonify({
                "success": True,
                "role": "faculty",
                "redirect": "/#faculty-dash",
                "user": faculty
            })

        # Demo fallback for standard demo emails
        valid_faculty_emails = ["faculty@college.edu", "raman@college.edu", "prof@college.edu"]
        if email in valid_faculty_emails or "faculty" in email or "prof" in email:
            if password != "faculty123":
                return jsonify({
                    "error": "Incorrect password. Please enter the correct password."
                }), 401

            session["logged_in"] = True
            session["role"] = "faculty"
            session["user_name"] = "Dr. S. K. Raman"
            return jsonify({
                "success": True,
                "role": "faculty",
                "redirect": "/#faculty-dash",
                "user": {
                    "name": "Dr. S. K. Raman",
                    "email": email,
                    "department": "Computer Science & Engineering",
                    "role": "Faculty"
                }
            })
        else:
            return jsonify({
                "error": f"No faculty member found with email '{email}'. Please check credentials or register as new faculty."
            }), 404

    else:
        # Student authentication against SQLite students table
        student = db.get_student_by_email(email)
        if not student:
            return jsonify({
                "error": f"No student found with email '{email}'. Please check spelling or pick a sample account below."
            }), 404

        # Password check: if password is wrong, do not log in
        stored_password = student.get("password") or "student123"
        if password != stored_password:
            return jsonify({
                "error": "Incorrect password. Please enter the correct password."
            }), 401

        session["logged_in"] = True
        session["role"] = "student"
        session["student_id"] = student["student_id"]
        session["user_name"] = student["name"]

        return jsonify({
            "success": True,
            "role": "student",
            "student_id": student["student_id"],
            "redirect": "/#student-dash",
            "user": student
        })


@app.route("/api/register", methods=["POST"])
def api_register():
    """
    Registers a new student profile in SQLite students table.
    Demonstrates DBMS INSERT operation with validation.
    """
    data = request.json or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()

    if not name or not email:
        return jsonify({"error": "Name and Email are required"}), 400

    # Check for existing email constraint
    existing = db.get_student_by_email(email)
    if existing:
        return jsonify({"error": "A student with this email address already exists in the database."}), 409

    try:
        new_id = db.create_student(data)
        session["logged_in"] = True
        session["role"] = "student"
        session["student_id"] = new_id
        session["user_name"] = name

        return jsonify({
            "success": True,
            "message": "Student profile created successfully in SQLite!",
            "student_id": new_id,
            "redirect": "/#student-dash"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/register-faculty", methods=["POST"])
def api_register_faculty():
    """
    Registers a new faculty profile in SQLite faculty table.
    Demonstrates DBMS INSERT operation with unique email constraint.
    """
    data = request.json or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    department = (data.get("department") or "Computer Science & Engineering").strip()
    designation = (data.get("designation") or "Assistant Professor").strip()
    password = (data.get("password") or "faculty123").strip()

    if not name or not email:
        return jsonify({"error": "Name and Email are required"}), 400

    # Check for existing email in faculty table
    existing = db.get_faculty_by_email(email)
    if existing:
        return jsonify({"error": "A faculty member with this email address already exists in the database."}), 409

    try:
        new_id = db.create_faculty({
            "name": name,
            "email": email,
            "department": department,
            "designation": designation,
            "password": password
        })
        session["logged_in"] = True
        session["role"] = "faculty"
        session["faculty_id"] = new_id
        session["user_name"] = name

        return jsonify({
            "success": True,
            "message": "Faculty profile registered successfully in SQLite!",
            "faculty_id": new_id,
            "redirect": "/#faculty-dash",
            "user": {
                "faculty_id": new_id,
                "name": name,
                "email": email,
                "department": department,
                "designation": designation,
                "role": "Faculty"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/faculty", methods=["GET"])
def list_faculty():
    """Returns all registered faculty members from SQLite."""
    faculty = db.get_all_faculty()
    return jsonify(faculty)


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """API endpoint to logout and clear session."""
    session.clear()
    return jsonify({"success": True, "redirect": "/login"})


@app.route("/api/session", methods=["GET", "POST"])
def manage_session():
    """
    Manages active user session.
    Allows switching between Student accounts, but prevents unauthorized escalation to Faculty.
    """
    if request.method == "POST":
        data = request.json or {}
        requested_role = data.get("role")
        student_id = data.get("student_id", 1)

        if requested_role == "faculty":
            # Security check: disallow unauthorized switch to faculty if not authenticated as faculty
            if session.get("role") != "faculty":
                return jsonify({
                    "error": "Unauthorized: Cannot switch to Faculty without faculty authentication. Please use Faculty Login."
                }), 403
            session["role"] = "faculty"
            return jsonify({
                "success": True,
                "role": "faculty",
                "user_name": session.get("user_name", "Dr. S. K. Raman")
            })

        elif requested_role == "student":
            session["logged_in"] = True
            session["role"] = "student"
            session["student_id"] = int(student_id)
            student = db.get_student_by_id(student_id)
            if student:
                session["user_name"] = student["name"]
            return jsonify({
                "success": True,
                "role": "student",
                "student_id": int(student_id),
                "user_name": session.get("user_name", "Student")
            })

    # Check if user is authenticated
    if not session.get("logged_in"):
        return jsonify({
            "logged_in": False,
            "role": None,
            "student_id": None,
            "user_name": None,
            "faculty_id": None
        })

    user_name = session.get("user_name")
    if not user_name:
        if session.get("role") == "faculty":
            user_name = "Dr. S. K. Raman"
        else:
            st = db.get_student_by_id(session.get("student_id", 1))
            user_name = st["name"] if st else "Student"
        session["user_name"] = user_name

    return jsonify({
        "logged_in": True,
        "role": session.get("role", "student"),
        "student_id": session.get("student_id"),
        "user_name": session.get("user_name"),
        "faculty_id": session.get("faculty_id", None)
    })


# ==========================================
# Student CRUD APIs
# ==========================================

@app.route("/api/students", methods=["GET"])
def list_students():
    """Demonstrates SELECT all students with skill counts."""
    students = db.get_all_students()
    return jsonify(students)


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    """Demonstrates SELECT single student with INNER JOIN skills."""
    student = db.get_student_by_id(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student)


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """Demonstrates UPDATE operation on students table."""
    data = request.json or {}
    try:
        db.update_student_profile(student_id, data)
        return jsonify({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/students/<int:student_id>/skills", methods=["POST"])
def add_skill_to_student(student_id):
    """Demonstrates INSERT / UPSERT into student_skills junction table."""
    data = request.json or {}
    skill_id = data.get("skill_id")
    proficiency = data.get("proficiency", "Intermediate")

    if not skill_id:
        return jsonify({"error": "skill_id is required"}), 400

    try:
        db.add_student_skill(student_id, skill_id, proficiency)
        return jsonify({"success": True, "message": "Skill added/updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/students/<int:student_id>/skills/<int:skill_id>", methods=["DELETE"])
def remove_skill_from_student(student_id, skill_id):
    """Demonstrates DELETE operation from student_skills junction table."""
    try:
        db.remove_student_skill(student_id, skill_id)
        return jsonify({"success": True, "message": "Skill removed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==========================================
# Skills APIs
# ==========================================

@app.route("/api/skills", methods=["GET", "POST"])
def manage_skills():
    """Retrieve all skills or create a new one."""
    if request.method == "POST":
        data = request.json or {}
        name = data.get("skill_name")
        category = data.get("category", "General")
        if not name:
            return jsonify({"error": "skill_name is required"}), 400
        new_id = db.create_skill(name, category)
        if not new_id:
            return jsonify({"error": "Skill already exists or failed to create"}), 400
        return jsonify({"success": True, "skill_id": new_id, "message": "Skill created"})

    skills = db.get_all_skills()
    return jsonify(skills)


# ==========================================
# Projects APIs
# ==========================================

@app.route("/api/projects", methods=["GET", "POST"])
def manage_projects():
    """Retrieve all projects or create a new one with required skills (Faculty only for POST)."""
    if request.method == "POST":
        if session.get("role") != "faculty":
            return jsonify({
                "error": "Access Denied: Only faculty members are authorized to create projects."
            }), 403

        data = request.json or {}
        name = data.get("project_name")
        description = data.get("description", "")
        team_size = data.get("team_size", 4)
        required_skills = data.get("required_skills", [])

        if not name:
            return jsonify({"error": "Project name is required"}), 400

        project_id = db.create_project(name, description, team_size, required_skills)
        return jsonify({"success": True, "project_id": project_id, "message": "Project created successfully"})

    projects = db.get_all_projects()
    return jsonify(projects)


@app.route("/api/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    project = db.get_project_by_id(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project)


# ==========================================
# Recommendation API
# ==========================================

@app.route("/api/recommend", methods=["POST"])
def recommend_team():
    """
    Executes the transparent Python rule-based team recommendation algorithm.
    Reads candidate profiles and requirements directly from SQLite.
    """
    data = request.json or {}
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"error": "project_id is required"}), 400

    proposals = rec.generate_recommended_teams(project_id, num_proposals=2)
    return jsonify(proposals)


# ==========================================
# Teams APIs
# ==========================================

@app.route("/api/teams", methods=["GET", "POST"])
def manage_teams():
    """Retrieve saved teams or save a newly approved/generated team (Faculty only for POST)."""
    if request.method == "POST":
        if session.get("role") != "faculty":
            return jsonify({
                "error": "Access Denied: Only faculty members are authorized to approve and save teams."
            }), 403

        data = request.json or {}
        project_id = data.get("project_id")
        team_name = data.get("team_name", "Team Custom")
        coverage_score = data.get("coverage_score", 0.0)
        member_ids = data.get("member_ids", [])
        status = data.get("status", "Recommended")

        if not project_id or not member_ids:
            return jsonify({"error": "project_id and member_ids are required"}), 400

        team_id = db.save_team(project_id, team_name, coverage_score, member_ids, status)
        return jsonify({"success": True, "team_id": team_id, "message": "Team saved successfully"})

    teams = db.get_all_teams()
    return jsonify(teams)


@app.route("/api/teams/<int:team_id>/status", methods=["PUT"])
def update_team_status(team_id):
    """Approve or reject a team (Faculty only)."""
    if session.get("role") != "faculty":
        return jsonify({
            "error": "Access Denied: Only faculty members are authorized to approve or reject teams."
        }), 403

    data = request.json or {}
    status = data.get("status")
    if status not in ["Approved", "Rejected", "Recommended"]:
        return jsonify({"error": "Invalid status"}), 400

    db.update_team_status(team_id, status)
    return jsonify({"success": True, "message": f"Team marked as {status}"})


# ==========================================
# NetworkX Graph API
# ==========================================

@app.route("/api/graph", methods=["GET"])
def get_graph():
    """
    Builds the NetworkX graph and returns serialized nodes, edges,
    and topological centrality metrics for frontend rendering.
    """
    graph_data = gb.build_skill_network()
    return jsonify(graph_data)


# ==========================================
# Faculty Analytics & Chart.js Data
# ==========================================

@app.route("/api/stats", methods=["GET"])
def get_analytics():
    """Returns aggregated KPIs and distributions for Chart.js."""
    stats = db.get_faculty_stats()
    return jsonify(stats)


# ==========================================
# DBMS & SQL Viva Showcase
# ==========================================

@app.route("/api/dbms-showcase", methods=["GET"])
def get_dbms_showcase():
    """
    Provides structured SQL definitions, relations, and core queries
    for the student to present directly during their viva examination.
    """
    showcase = {
        "tables": [
            {
                "name": "students",
                "purpose": "Stores core student entity records",
                "pk": "student_id (INTEGER AUTOINCREMENT)",
                "fks": "None",
                "sample_query": "SELECT * FROM students WHERE department = 'Computer Science';"
            },
            {
                "name": "skills",
                "purpose": "Dictionary of technical and soft competencies",
                "pk": "skill_id (INTEGER AUTOINCREMENT)",
                "fks": "None",
                "sample_query": "SELECT * FROM skills ORDER BY category, skill_name;"
            },
            {
                "name": "student_skills",
                "purpose": "M:N junction linking students to skills with proficiency attribute",
                "pk": "id (INTEGER AUTOINCREMENT)",
                "fks": "student_id -> students, skill_id -> skills (ON DELETE CASCADE)",
                "sample_query": "SELECT s.name, sk.skill_name, ss.proficiency FROM student_skills ss INNER JOIN students s ON ss.student_id = s.student_id INNER JOIN skills sk ON ss.skill_id = sk.skill_id;"
            },
            {
                "name": "projects",
                "purpose": "Academic or industry capstone projects created by faculty",
                "pk": "project_id (INTEGER AUTOINCREMENT)",
                "fks": "None",
                "sample_query": "SELECT project_name, team_size, status FROM projects WHERE status = 'Open';"
            },
            {
                "name": "project_skills",
                "purpose": "M:N junction defining required competencies and importance",
                "pk": "id (INTEGER AUTOINCREMENT)",
                "fks": "project_id -> projects, skill_id -> skills (ON DELETE CASCADE)",
                "sample_query": "SELECT p.project_name, sk.skill_name, ps.importance FROM project_skills ps INNER JOIN projects p ON ps.project_id = p.project_id INNER JOIN skills sk ON ps.skill_id = sk.skill_id;"
            },
            {
                "name": "teams",
                "purpose": "Recommended or approved teams formed for a project",
                "pk": "team_id (INTEGER AUTOINCREMENT)",
                "fks": "project_id -> projects (ON DELETE CASCADE)",
                "sample_query": "SELECT t.team_name, p.project_name, t.coverage_score, t.status FROM teams t INNER JOIN projects p ON t.project_id = p.project_id;"
            },
            {
                "name": "team_members",
                "purpose": "M:N junction mapping students assigned to approved teams",
                "pk": "id (INTEGER AUTOINCREMENT)",
                "fks": "team_id -> teams, student_id -> students (ON DELETE CASCADE)",
                "sample_query": "SELECT tm.team_id, s.name, s.department FROM team_members tm INNER JOIN students s ON tm.student_id = s.student_id;"
            }
        ],
        "key_joins": [
            {
                "title": "3-Way Relational JOIN: Student Skills Inspection",
                "sql": """SELECT s.name, s.department, sk.skill_name, ss.proficiency
FROM students s
INNER JOIN student_skills ss ON s.student_id = ss.student_id
INNER JOIN skills sk ON ss.skill_id = sk.skill_id
WHERE sk.category = 'Programming';""",
                "concept": "Demonstrates INNER JOIN across two 1:N relations to resolve an M:N relationship with attributes."
            },
            {
                "title": "Aggregation with GROUP BY & COUNT: Most In-Demand Skills",
                "sql": """SELECT sk.skill_name, COUNT(ps.project_id) AS demand_count
FROM skills sk
INNER JOIN project_skills ps ON sk.skill_id = ps.skill_id
GROUP BY sk.skill_id
ORDER BY demand_count DESC;""",
                "concept": "Demonstrates aggregation function COUNT() grouped by primary key."
            },
            {
                "title": "LEFT OUTER JOIN: Students Without Assigned Teams",
                "sql": """SELECT s.student_id, s.name, s.department
FROM students s
LEFT JOIN team_members tm ON s.student_id = tm.student_id
WHERE tm.team_id IS NULL;""",
                "concept": "Demonstrates LEFT OUTER JOIN to discover unassigned records."
            }
        ]
    }
    return jsonify(showcase)


# ==========================================
# Interactive SQL Query Console (Viva Exam)
# ==========================================

@app.route("/api/query", methods=["POST"])
def execute_custom_query():
    """
    Executes read-only SELECT queries for viva examiner live evaluation.
    Enforces security by blocking data-modifying statements.
    """
    data = request.json or {}
    sql = (data.get("query") or "").strip()

    if not sql:
        return jsonify({"error": "Query cannot be empty"}), 400

    # Ensure query is strictly read-only for safety
    first_word = sql.split()[0].upper()
    if first_word not in ["SELECT", "EXPLAIN", "PRAGMA"]:
        return jsonify({"error": "Only SELECT, EXPLAIN, and PRAGMA queries are permitted in the viva console."}), 400

    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        # Extract column names
        columns = [col[0] for col in cursor.description] if cursor.description else []
        results = [dict(row) for row in rows]
        conn.close()

        return jsonify({
            "success": True,
            "columns": columns,
            "row_count": len(results),
            "rows": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==========================================
# Reset Database Utility
# ==========================================

@app.route("/api/reset-db", methods=["POST"])
def reset_database():
    """Resets database back to clean demo state for repeat testing."""
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()
    return jsonify({"success": True, "message": "Database reset to initial demo state"})


if __name__ == "__main__":
    print("================================================================")
    print(" Student Skill Graph & Team Builder (Python Flask + SQLite) ")
    print(" Server running on: http://127.0.0.1:5000")
    print("================================================================")
    app.run(debug=True, host="127.0.0.1", port=5000)
