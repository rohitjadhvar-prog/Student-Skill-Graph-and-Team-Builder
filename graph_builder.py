"""
graph_builder.py - NetworkX Graph Construction and Analysis Engine
Project: Student Skill Graph & Team Builder
Course Context: Python & DBMS College Project

Demonstrates:
- NetworkX graph creation (nodes, edges, node attributes, edge weights)
- Tripartite graph model: Students, Skills, Projects
- Graph metrics: Degree centrality, node degree, density
- Conversion of NetworkX graph into visualization-ready JSON (for Vis-Network)
"""

import networkx as nx
from database import get_db_connection


# Color scheme for different entity types
NODE_COLORS = {
    "student": "#3B82F6",    # Blue
    "skill": "#10B981",      # Emerald Green
    "project": "#8B5CF6"     # Purple
}

CATEGORY_COLORS = {
    "Programming": "#10B981",
    "Database": "#F59E0B",
    "Web Development": "#06B6D4",
    "AI / Data Science": "#EC4899",
    "Design": "#8B5CF6",
    "Security": "#EF4444",
    "Soft Skills": "#6366F1",
    "Management": "#14B8A6"
}


def build_skill_network(filter_project_id=None, filter_student_id=None):
    """
    Constructs a NetworkX graph representing students, skills, and projects.
    Returns serialized nodes, edges, and network statistics.
    """
    G = nx.Graph()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch and add Skill nodes
    skills = cursor.execute("SELECT skill_id, skill_name, category FROM skills;").fetchall()
    for sk in skills:
        node_id = f"skill_{sk['skill_id']}"
        cat = sk["category"]
        color = CATEGORY_COLORS.get(cat, NODE_COLORS["skill"])
        G.add_node(
            node_id,
            raw_id=sk["skill_id"],
            label=sk["skill_name"],
            entity_type="skill",
            category=cat,
            color=color,
            shape="dot",
            size=22,
            title=f"<b>Skill:</b> {sk['skill_name']}<br><b>Category:</b> {cat}"
        )

    # 2. Fetch and add Student nodes
    students = cursor.execute("""
        SELECT student_id, name, department, year, availability, interests
        FROM students;
    """).fetchall()

    for st in students:
        node_id = f"student_{st['student_id']}"
        G.add_node(
            node_id,
            raw_id=st["student_id"],
            label=st["name"],
            entity_type="student",
            department=st["department"],
            year=st["year"],
            availability=st["availability"],
            interests=st["interests"],
            color=NODE_COLORS["student"],
            shape="diamond",
            size=25,
            title=f"<b>Student:</b> {st['name']}<br><b>Dept:</b> {st['department']} (Year {st['year']})<br><b>Availability:</b> {st['availability']}"
        )

    # 3. Fetch and add Project nodes
    projects = cursor.execute("""
        SELECT project_id, project_name, team_size, status
        FROM projects;
    """).fetchall()

    for p in projects:
        node_id = f"project_{p['project_id']}"
        G.add_node(
            node_id,
            raw_id=p["project_id"],
            label=p["project_name"],
            entity_type="project",
            team_size=p["team_size"],
            status=p["status"],
            color=NODE_COLORS["project"],
            shape="box",
            size=30,
            title=f"<b>Project:</b> {p['project_name']}<br><b>Team Size:</b> {p['team_size']}<br><b>Status:</b> {p['status']}"
        )

    # 4. Add Student -> Skill edges (weighted by proficiency)
    prof_weights = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}
    student_skills = cursor.execute("""
        SELECT student_id, skill_id, proficiency
        FROM student_skills;
    """).fetchall()

    for row in student_skills:
        u = f"student_{row['student_id']}"
        v = f"skill_{row['skill_id']}"
        weight = prof_weights.get(row["proficiency"], 1)
        G.add_edge(
            u, v,
            relationship="has_skill",
            proficiency=row["proficiency"],
            weight=weight,
            title=f"Proficiency: {row['proficiency']}",
            color={"color": "#94A3B8", "opacity": 0.6},
            width=weight
        )

    # 5. Add Project -> Skill edges (weighted by importance)
    imp_weights = {"High": 3, "Medium": 2, "Low": 1}
    project_skills = cursor.execute("""
        SELECT project_id, skill_id, importance
        FROM project_skills;
    """).fetchall()

    for row in project_skills:
        u = f"project_{row['project_id']}"
        v = f"skill_{row['skill_id']}"
        weight = imp_weights.get(row["importance"], 2)
        G.add_edge(
            u, v,
            relationship="requires_skill",
            importance=row["importance"],
            weight=weight,
            dashes=True,
            title=f"Required Importance: {row['importance']}",
            color={"color": "#C084FC", "opacity": 0.8},
            width=weight * 1.5
        )

    # 6. Add Student -> Project edges (from approved/recommended teams)
    team_memberships = cursor.execute("""
        SELECT tm.student_id, t.project_id, t.team_name, t.status
        FROM team_members tm
        INNER JOIN teams t ON tm.team_id = t.team_id;
    """).fetchall()

    for row in team_memberships:
        u = f"student_{row['student_id']}"
        v = f"project_{row['project_id']}"
        G.add_edge(
            u, v,
            relationship="team_member",
            team_name=row["team_name"],
            status=row["status"],
            title=f"Team: {row['team_name']} ({row['status']})",
            color={"color": "#F59E0B", "opacity": 0.9},
            width=3
        )

    conn.close()

    # NetworkX Analysis Metrics
    degree_centrality = nx.degree_centrality(G)
    density = round(nx.density(G), 4)

    # Find top 3 most connected skills
    skill_degrees = [
        (node, G.nodes[node]["label"], G.degree(node))
        for node in G.nodes if G.nodes[node]["entity_type"] == "skill"
    ]
    skill_degrees.sort(key=lambda x: x[2], reverse=True)
    top_skills = [{"name": s[1], "degree": s[2]} for s in skill_degrees[:5]]

    # Prepare data for frontend visualization
    vis_nodes = []
    for n, attr in G.nodes(data=True):
        vis_nodes.append({
            "id": n,
            "label": attr.get("label", n),
            "entity_type": attr.get("entity_type"),
            "raw_id": attr.get("raw_id"),
            "color": attr.get("color"),
            "shape": attr.get("shape", "dot"),
            "size": attr.get("size", 20),
            "title": attr.get("title", ""),
            "department": attr.get("department"),
            "year": attr.get("year"),
            "category": attr.get("category"),
            "availability": attr.get("availability"),
            "interests": attr.get("interests"),
            "team_size": attr.get("team_size"),
            "status": attr.get("status"),
            "degree": G.degree(n),
            "centrality": round(degree_centrality.get(n, 0), 3)
        })

    vis_edges = []
    for u, v, attr in G.edges(data=True):
        edge_data = {
            "from": u,
            "to": v,
            "relationship": attr.get("relationship"),
            "title": attr.get("title", ""),
            "color": attr.get("color", "#94A3B8"),
            "width": attr.get("width", 1),
            "dashes": attr.get("dashes", False)
        }
        vis_edges.append(edge_data)

    return {
        "nodes": vis_nodes,
        "edges": vis_edges,
        "stats": {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "graph_density": density,
            "student_nodes": sum(1 for _, a in G.nodes(data=True) if a.get("entity_type") == "student"),
            "skill_nodes": sum(1 for _, a in G.nodes(data=True) if a.get("entity_type") == "skill"),
            "project_nodes": sum(1 for _, a in G.nodes(data=True) if a.get("entity_type") == "project"),
            "top_connected_skills": top_skills
        }
    }
