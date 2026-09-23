"""
recommendation.py - Transparent Rule-Based Team Matching Engine
Project: Student Skill Graph & Team Builder
Course Context: Python & DBMS College Project

Algorithm Description (Rule-Based Heuristic Matching):
1. Target Analysis: Extracts required skills and weights (High=3, Medium=2, Low=1).
2. Student Candidate Scoring:
   - Proficiency mapping: Beginner=1, Intermediate=2, Advanced=3, Expert=4.
   - Availability bonus: High=1.2, Medium=1.0, Low=0.7.
   - Interest affinity bonus: Keywords matching project name or description.
3. Complementary Greedy Selection:
   - Selects the first member providing the highest coverage for high-priority skills.
   - For subsequent members, evaluates the MARGINAL GAIN (new or improved skill coverage),
     penalizing duplicate skills to ensure diverse, complementary strengths.
4. Metric Computation:
   - Skill Coverage Percentage = (Sum of team max proficiency achieved / Max possible score) * 100.
   - List of Matched Skills & Missing Gaps.
   - Human-readable explanation generation for presentation.
"""

from database import get_db_connection, get_project_by_id


PROFICIENCY_SCORES = {
    "Beginner": 1,
    "Intermediate": 2,
    "Advanced": 3,
    "Expert": 4
}

IMPORTANCE_WEIGHTS = {
    "High": 3.0,
    "Medium": 2.0,
    "Low": 1.0
}

AVAILABILITY_WEIGHTS = {
    "High": 1.2,
    "Full-Time": 1.2,
    "Medium": 1.0,
    "Part-Time": 0.9,
    "Low": 0.7
}


def compute_interest_affinity(student_interests, project_name, project_desc):
    """
    Computes a bonus if student's stated interests overlap with project keywords.
    """
    if not student_interests:
        return 1.0
    
    text = (project_name + " " + (project_desc or "")).lower()
    interests = [i.strip().lower() for i in student_interests.split(",") if i.strip()]
    
    matches = 0
    for item in interests:
        for word in item.split():
            if len(word) > 2 and word in text:
                matches += 1
                break
                
    return 1.0 + min(0.3, matches * 0.1)


def generate_recommended_teams(project_id, num_proposals=2):
    """
    Generates balanced, complementary student team recommendations for a project.
    Returns a list of proposed teams with scores, matched skills, gaps, and explanations.
    """
    project = get_project_by_id(project_id)
    if not project or not project.get("required_skills"):
        return {"error": "Project not found or has no required skills defined."}

    req_skills = project["required_skills"]
    team_size = int(project.get("team_size", 4))
    
    # Map required skill_id to importance weight
    req_weights = {
        s["skill_id"]: {
            "name": s["skill_name"],
            "category": s["category"],
            "importance": s["importance"],
            "weight": IMPORTANCE_WEIGHTS.get(s["importance"], 2.0)
        }
        for s in req_skills
    }

    # Total possible maximum score if every required skill was covered at Expert level (4)
    max_possible_weighted_score = sum(
        info["weight"] * 4.0 for info in req_weights.values()
    )

    # Fetch all students and their skill proficiencies from SQLite
    conn = get_db_connection()
    cursor = conn.cursor()

    students_raw = cursor.execute("""
        SELECT student_id, name, email, department, year, availability, interests
        FROM students;
    """).fetchall()

    student_pool = []
    for s in students_raw:
        sid = s["student_id"]
        # Fetch this student's skills
        s_skills = cursor.execute("""
            SELECT ss.skill_id, s.skill_name, ss.proficiency
            FROM student_skills ss
            INNER JOIN skills s ON ss.skill_id = s.skill_id
            WHERE ss.student_id = ?;
        """, (sid,)).fetchall()

        skills_dict = {
            row["skill_id"]: {
                "name": row["skill_name"],
                "proficiency": row["proficiency"],
                "score": PROFICIENCY_SCORES.get(row["proficiency"], 1)
            }
            for row in s_skills
        }

        student_pool.append({
            "student_id": sid,
            "name": s["name"],
            "email": s["email"],
            "department": s["department"],
            "year": s["year"],
            "availability": s["availability"],
            "interests": s["interests"],
            "skills": skills_dict
        })

    conn.close()

    if len(student_pool) < team_size:
        team_size = len(student_pool)

    # Generate up to `num_proposals` diverse teams using different seed approaches
    team_names = ["TEAM NOVA", "TEAM APEX", "TEAM CATALYST"]
    proposals = []

    for prop_idx in range(min(num_proposals, len(team_names))):
        team_name = team_names[prop_idx]
        selected_members = []
        selected_ids = set()

        # Track the best coverage the team currently has for each required skill
        team_skill_coverage = {sk_id: 0 for sk_id in req_weights.keys()}

        # Pick members one-by-one maximizing marginal complementary gain
        for slot in range(team_size):
            best_candidate = None
            best_marginal_score = -1

            # Candidate evaluation loop
            for candidate in student_pool:
                cid = candidate["student_id"]
                if cid in selected_ids:
                    continue

                # Don't pick the exact same starting student for proposal 2 to guarantee team diversity
                if slot == 0 and prop_idx > 0 and cid == proposals[0]["members"][0]["student_id"]:
                    continue

                avail_factor = AVAILABILITY_WEIGHTS.get(candidate["availability"], 1.0)
                interest_bonus = compute_interest_affinity(
                    candidate["interests"], project["project_name"], project.get("description", "")
                )

                # Calculate Marginal Gain: how much this student improves uncovered or under-covered skills
                marginal_gain = 0.0
                redundancy_penalty = 0.0

                for req_id, req_info in req_weights.items():
                    cur_covered = team_skill_coverage[req_id]
                    if req_id in candidate["skills"]:
                        cand_score = candidate["skills"][req_id]["score"]
                        if cand_score > cur_covered:
                            # Student improves this skill!
                            improvement = cand_score - cur_covered
                            marginal_gain += improvement * req_info["weight"]
                        else:
                            # Redundant duplicate skill already covered by someone else
                            redundancy_penalty += 0.25 * req_info["weight"]

                # Total candidate score for this slot
                score = (marginal_gain * avail_factor * interest_bonus) - redundancy_penalty

                # Break ties with general skill breadth
                score += len(candidate["skills"]) * 0.1

                if score > best_marginal_score:
                    best_marginal_score = score
                    best_candidate = candidate

            if best_candidate:
                selected_members.append(best_candidate)
                selected_ids.add(best_candidate["student_id"])
                # Update current team coverage
                for req_id in req_weights.keys():
                    if req_id in best_candidate["skills"]:
                        team_skill_coverage[req_id] = max(
                            team_skill_coverage[req_id],
                            best_candidate["skills"][req_id]["score"]
                        )

        # Calculate final coverage metrics for this proposed team
        actual_weighted_score = sum(
            team_skill_coverage[req_id] * req_weights[req_id]["weight"]
            for req_id in req_weights.keys()
        )
        
        coverage_pct = round(min(100.0, (actual_weighted_score / max_possible_weighted_score) * 100), 1)

        # Identify matched skills and provider students
        matched_skills = []
        missing_skills = []

        for req_id, req_info in req_weights.items():
            providers = []
            for m in selected_members:
                if req_id in m["skills"]:
                    providers.append(f"{m['name']} ({m['skills'][req_id]['proficiency']})")
            
            if providers:
                matched_skills.append({
                    "skill_name": req_info["name"],
                    "importance": req_info["importance"],
                    "best_score": team_skill_coverage[req_id],
                    "provided_by": ", ".join(providers)
                })
            else:
                missing_skills.append({
                    "skill_name": req_info["name"],
                    "importance": req_info["importance"]
                })

        # Generate Explainable Summary for Viva
        member_summaries = []
        for m in selected_members:
            # Highlight which required skills this member brings
            key_skills = [
                f"{m['skills'][sk_id]['name']} ({m['skills'][sk_id]['proficiency']})"
                for sk_id in req_weights
                if sk_id in m["skills"]
            ]
            if not key_skills:
                # Other skills
                key_skills = [f"{v['name']} ({v['proficiency']})" for v in list(m["skills"].values())[:2]]
            
            summary = f"{m['name']} [{', '.join(key_skills)}]" if key_skills else m["name"]
            member_summaries.append(summary)

        explanation = (
            f"This team was recommended because its {len(selected_members)} members collectively achieve "
            f"{coverage_pct}% skill coverage across {len(matched_skills)}/{len(req_weights)} required competencies "
            f"while minimizing skill overlap. Complementary strengths: "
            + "; ".join(member_summaries) + "."
        )

        # Format members for JSON response
        formatted_members = []
        for m in selected_members:
            formatted_members.append({
                "student_id": m["student_id"],
                "name": m["name"],
                "email": m["email"],
                "department": m["department"],
                "year": m["year"],
                "availability": m["availability"],
                "interests": m["interests"],
                "skills_summary": [
                    {"name": sk["name"], "proficiency": sk["proficiency"]}
                    for sk in m["skills"].values()
                ]
            })

        proposals.append({
            "team_name": team_name,
            "project_id": project_id,
            "project_name": project["project_name"],
            "coverage_score": coverage_pct,
            "members": formatted_members,
            "member_ids": [m["student_id"] for m in selected_members],
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "explanation": explanation
        })

    return proposals
