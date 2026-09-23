# Student Skill Graph & Team Builder
> *“Turn scattered student skills into balanced, project-ready teams.”*

A complete academic web application built specifically for **Python and DBMS** college coursework and viva presentations.

The platform addresses a fundamental college dilemma: students usually form capstone project teams based on casual friendships rather than complementary technical proficiencies, leading to unbalanced teams with duplicated skills and critical gaps. SkillGraph solves this by combining an **SQLite Relational Database (DBMS)**, a **NetworkX Topological Skill Graph**, and an **explainable Python rule-based recommendation algorithm**.

---

## 🌟 Key Features

1. **Student Profile Management**: Full CRUD operations for student records (name, email, department, year, availability, interests).
2. **Skill Inventory & Proficiency Levels**: Add, adjust, or delete skills with ratings (`Beginner`, `Intermediate`, `Advanced`, `Expert`).
3. **Faculty Project Definition**: Create capstone projects with specific prerequisites and importance ratings (`High`, `Medium`, `Low`).
4. **NetworkX Skill Graph**: Tripartite topological network model (Students ↔ Skills ↔ Projects) featuring node degrees and degree centrality.
5. **Rule-Based Recommendation Engine**: Transparent, explainable Python matching algorithm maximizing complementary skills while penalizing redundancy.
6. **Faculty Approval Workflow**: Faculty can review, approve, or reject recommended teams, with atomic SQLite database status updates.
7. **Interactive DBMS & SQL Viva Showcase**: Live SQL console, relational schema documentation, and 3-way `JOIN` query explanations built directly into the UI for viva evaluation.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, Modern CSS3, Vanilla JavaScript | Responsive dashboard with sidebar navigation |
| **Backend** | Python Flask (3.1+) | RESTful APIs, session management, algorithm execution |
| **Database** | SQLite3 | Relational database with strict primary/foreign keys |
| **Graph Theory** | NetworkX | Graph data modeling, bipartite/tripartite relationships, centrality |
| **Visualization** | Vis.js Network & Chart.js | Interactive force-directed graph canvas & distribution charts |

---

## 🗄️ Relational Database Schema (DBMS Requirements)

The database (`skills.db`) implements 7 normalized tables demonstrating **1:N** and **M:N** relationships with foreign keys and cascade rules:

```
[ students ] 1 ───< M [ student_skills ] M >─── 1 [ skills ]
                             ∧
                             │
[ projects ] 1 ───< M [ project_skills ] M >─── 1 [ skills ]
     │
     └── 1 ───< M [ teams ] 1 ───< M [ team_members ] M >─── 1 [ students ]
```

### 1. `students`
- `student_id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `name`: `TEXT NOT NULL`
- `email`: `TEXT NOT NULL UNIQUE`
- `department`: `TEXT NOT NULL`
- `year`: `INTEGER NOT NULL`
- `availability`: `TEXT NOT NULL`
- `interests`: `TEXT NOT NULL`

### 2. `skills`
- `skill_id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `skill_name`: `TEXT NOT NULL UNIQUE`
- `category`: `TEXT NOT NULL`

### 3. `student_skills` (M:N Junction: Students ↔ Skills)
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `student_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES students(student_id) ON DELETE CASCADE`
- `skill_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES skills(skill_id) ON DELETE CASCADE`
- `proficiency`: `TEXT NOT NULL` (`Beginner`, `Intermediate`, `Advanced`, `Expert`)
- `UNIQUE(student_id, skill_id)`

### 4. `projects`
- `project_id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `project_name`: `TEXT NOT NULL`
- `description`: `TEXT`
- `team_size`: `INTEGER NOT NULL DEFAULT 4`
- `status`: `TEXT NOT NULL DEFAULT 'Open'`

### 5. `project_skills` (M:N Junction: Projects ↔ Skills)
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `project_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES projects(project_id) ON DELETE CASCADE`
- `skill_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES skills(skill_id) ON DELETE CASCADE`
- `importance`: `TEXT NOT NULL` (`High`, `Medium`, `Low`)
- `UNIQUE(project_id, skill_id)`

### 6. `teams`
- `team_id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `project_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES projects(project_id) ON DELETE CASCADE`
- `team_name`: `TEXT NOT NULL`
- `status`: `TEXT NOT NULL DEFAULT 'Recommended'` (`Recommended`, `Approved`, `Rejected`)
- `coverage_score`: `REAL NOT NULL DEFAULT 0.0`

### 7. `team_members` (M:N Junction: Teams ↔ Students)
- `id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `team_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES teams(team_id) ON DELETE CASCADE`
- `student_id`: `INTEGER NOT NULL`, `FOREIGN KEY REFERENCES students(student_id) ON DELETE CASCADE`
- `UNIQUE(team_id, student_id)`

### 8. `faculty`
- `faculty_id`: `INTEGER PRIMARY KEY AUTOINCREMENT`
- `name`: `TEXT NOT NULL`
- `email`: `TEXT NOT NULL UNIQUE`
- `department`: `TEXT NOT NULL`
- `designation`: `TEXT NOT NULL DEFAULT 'Assistant Professor'`
- `password`: `TEXT NOT NULL DEFAULT 'faculty123'`

---

## ⚡ How to Run in VS Code

### Step 1: Open Terminal in VS Code
Open the project folder in VS Code and open a PowerShell terminal (`Ctrl + ~`).

### Step 2: Install Dependencies
```powershell
py -m pip install -r requirements.txt
```
*(Dependencies are lightweight: `Flask` and `networkx`)*

### Step 3: Run the Flask Application
```powershell
py app.py
```

### Step 4: Open in Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🎓 Viva & Presentation Guide

### 1. Explain the Recommendation Algorithm (Python)
When the examiner asks: *"How does the recommendation algorithm work?"*

> **Answer:**
> "The matching algorithm in `recommendation.py` is an explainable, rule-based heuristic. 
> 1. It reads required skills and importance weights (`High=3`, `Medium=2`, `Low=1`) for the chosen project.
> 2. It queries candidate student proficiencies (`Beginner=1`, `Intermediate=2`, `Advanced=3`, `Expert=4`), availability bonus, and domain affinity.
> 3. Instead of picking candidates with identical skills, it maximizes **marginal coverage gain** while applying a **redundancy penalty** if a skill is already covered by an existing team member.
> 4. The overall skill coverage percentage is calculated as the ratio of achieved proficiency over maximum possible score.
> 5. Finally, it produces a transparent explanation detailing which member covers each specific required competency."

### 2. Explain the NetworkX Graph (Python)
When the examiner asks: *"How is NetworkX used?"*

> **Answer:**
> "In `graph_builder.py`, we construct a heterogeneous graph using Python's `networkx.Graph()`.
> - **Nodes**: Students (diamonds), Skills (dots color-coded by category), and Projects (boxes).
> - **Edges**: Weighted connections representing proficiency levels (Student ↔ Skill) and requirements (Project ↔ Skill).
> - We calculate topological graph metrics like **Degree Centrality** (`nx.degree_centrality(G)`) to identify which technical skills are most central to the college ecosystem."

### 3. Explain Key DBMS Concepts Implemented
When the examiner asks: *"Show me the SQL JOIN queries and database integrity rules."*

> **Answer:**
> Open the **DBMS & SQL Viva** tab on the website to show:
> 1. **Foreign Key Enforcement**: Enabled via `PRAGMA foreign_keys = ON;`.
> 2. **Cascading Deletes**: `ON DELETE CASCADE` ensures that deleting a student cleanly removes their junction records in `student_skills` and `team_members`.
> 3. **3-Way INNER JOIN**:
>    ```sql
>    SELECT s.name, s.department, sk.skill_name, ss.proficiency
>    FROM students s
>    INNER JOIN student_skills ss ON s.student_id = ss.student_id
>    INNER JOIN skills sk ON ss.skill_id = sk.skill_id;
>    ```
> 4. **Aggregation & Grouping**:
>    ```sql
>    SELECT s.skill_name, COUNT(ss.student_id) AS student_count
>    FROM skills s
>    LEFT JOIN student_skills ss ON s.skill_id = ss.skill_id
>    GROUP BY s.skill_id
>    ORDER BY student_count DESC;
>    ```
> 5. **Interactive Console**: Use the live SQL Console in the UI to run queries directly in front of the examiner.

---

## 🧪 Quick Demo Script for Evaluation

1. **Home Tab**: Walk through the problem, solution, and architecture diagram.
2. **Student Dashboard & Profile**:
   - Show Aditya Sharma's profile.
   - Go to **My Profile** → Edit availability to `Medium` → Click **Update Profile in SQLite**. Notice the live JSON inspector updating.
   - Go to **My Skills** → Add a new skill (e.g., `Cyber Security` with `Advanced` proficiency) → Watch it appear in the database table.
3. **NetworkX Skill Graph**:
   - Switch to **NetworkX Graph** tab.
   - Drag nodes around, filter by "Students & Skills", and click on any node to inspect its degree centrality and attributes.
4. **Team Builder (Recommendation)**:
   - Select `Smart Campus Management System` (requires Python, Database, UI/UX, Communication).
   - Click **Generate Teams**.
   - Review **TEAM NOVA** (92.5% coverage). Point out how Aditya & Rohit bring Python/Database, Aryan brings UI/UX, and Pranab brings Communication without duplication!
   - Click **Approve Team**.
5. **Faculty Analytics**:
   - Show the live Chart.js charts for most common skills and skill categories.
   - Verify that the newly approved team appears in the database records table.
6. **DBMS & SQL Viva Showcase**:
   - Show the 7 table schemas and run a query in the interactive console!

---

## 📁 Project Structure

```
skill/
├── app.py                 # Flask server, REST routes, SQL query runner
├── database.py            # SQLite schema creation, CRUD methods, seed data
├── recommendation.py      # Rule-based team matching algorithm
├── graph_builder.py       # NetworkX graph modeling and centrality analysis
├── test_app.py            # Automated test suite
├── requirements.txt       # Python dependencies (Flask, NetworkX)
├── README.md              # Documentation and viva presentation guide
├── templates/
│   └── index.html         # Single-page dashboard interface
└── static/
    ├── css/
    │   └── style.css      # Professional dashboard design system
    └── js/
        └── app.js         # Frontend interactivity, Chart.js, Vis-Network
```
