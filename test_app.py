"""
test_app.py - Verification Test Suite
Project: Student Skill Graph & Team Builder
Tests SQLite database, NetworkX graph, recommendation engine, and Flask endpoints.
"""

import os
import unittest
import database as db
import recommendation as rec
import graph_builder as gb
from app import app


class SkillGraphTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_1_database_tables_and_seed(self):
        """Verify all 7 SQLite tables and seeded records exist."""
        conn = db.get_db_connection()
        cursor = conn.cursor()
        
        tables = [
            "students", "skills", "student_skills",
            "projects", "project_skills", "teams", "team_members"
        ]
        for t in tables:
            count = cursor.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
            self.assertGreaterEqual(count, 0, f"Table {t} should be accessible")
        
        # Verify demo students count >= 10
        student_count = cursor.execute("SELECT COUNT(*) FROM students;").fetchone()[0]
        self.assertGreaterEqual(student_count, 10, "Should have seeded at least 10 demo students")
        
        # Verify demo skills count >= 10
        skill_count = cursor.execute("SELECT COUNT(*) FROM skills;").fetchone()[0]
        self.assertGreaterEqual(skill_count, 10, "Should have seeded at least 10 demo skills")
        conn.close()

    def test_2_networkx_graph_builder(self):
        """Verify NetworkX graph builds nodes, edges, and centrality."""
        graph_data = gb.build_skill_network()
        self.assertIn("nodes", graph_data)
        self.assertIn("edges", graph_data)
        self.assertIn("stats", graph_data)
        self.assertGreater(graph_data["stats"]["total_nodes"], 0)
        self.assertGreater(graph_data["stats"]["total_edges"], 0)
        self.assertGreater(len(graph_data["stats"]["top_connected_skills"]), 0)

    def test_3_recommendation_algorithm(self):
        """Verify transparent rule-based matching generates balanced teams."""
        # Test recommendation for project 1 (Smart Campus Management System)
        proposals = rec.generate_recommended_teams(project_id=1, num_proposals=2)
        self.assertIsInstance(proposals, list)
        self.assertGreaterEqual(len(proposals), 1)
        
        prop = proposals[0]
        self.assertIn("team_name", prop)
        self.assertIn("coverage_score", prop)
        self.assertGreater(prop["coverage_score"], 50.0, "Coverage should be substantial")
        self.assertIn("members", prop)
        self.assertEqual(len(prop["members"]), 4, "Team size should match project requirement of 4")
        self.assertIn("explanation", prop)
        self.assertIn("matched_skills", prop)

    def test_4_flask_routes(self):
        """Verify key API endpoints return HTTP 200."""
        # Root route redirects unauthenticated visitors to login
        res = self.app.get("/", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/api/students")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/api/skills")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/api/projects")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/api/graph")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/api/stats")
        self.assertEqual(res.status_code, 200)

        res = self.app.get("/api/dbms-showcase")
        self.assertEqual(res.status_code, 200)

        # Test safe SELECT query endpoint
        res = self.app.post("/api/query", json={"query": "SELECT COUNT(*) FROM students;"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

    def test_5_login_and_auth(self):
        """Verify login page, student login, faculty login, and logout."""
        # 1. GET /login
        res = self.app.get("/login")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Student Skill Graph", res.data)
        self.assertIn(b"Student Login", res.data)
        self.assertIn(b"Faculty Login", res.data)

        # 2a. Student Login - Wrong Password should FAIL (HTTP 401)
        res = self.app.post("/api/login", json={
            "role": "student",
            "email": "aditya@college.edu",
            "password": "wrong_password_123"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn("error", data)
        self.assertIn("Incorrect password", data["error"])

        # 2b. Student Login - Correct Password should SUCCEED (HTTP 200)
        res = self.app.post("/api/login", json={
            "role": "student",
            "email": "aditya@college.edu",
            "password": "student123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "student")
        self.assertIn("Aditya", data["user"]["name"])

        # 3a. Faculty Login - Wrong Password should FAIL (HTTP 401)
        res = self.app.post("/api/login", json={
            "role": "faculty",
            "email": "faculty@college.edu",
            "password": "wrong_faculty_pass"
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn("error", data)
        self.assertIn("Incorrect password", data["error"])

        # 3b. Faculty Login - Correct Password should SUCCEED (HTTP 200)
        res = self.app.post("/api/login", json={
            "role": "faculty",
            "email": "faculty@college.edu",
            "password": "faculty123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "faculty")

        # 4a. Student Registration with Custom Password
        import random
        rand_email = f"test_student_{random.randint(1000, 9999)}@college.edu"
        custom_password = "my_secret_pass_789"
        res = self.app.post("/api/register", json={
            "name": "Test Student Custom Pass",
            "email": rand_email,
            "department": "Computer Science",
            "year": 2,
            "availability": "High",
            "interests": "Machine Learning, Databases",
            "password": custom_password
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # 4b. Verify newly registered student cannot login with wrong password
        res = self.app.post("/api/login", json={
            "role": "student",
            "email": rand_email,
            "password": "wrong_pass"
        })
        self.assertEqual(res.status_code, 401)

        # 4c. Verify newly registered student succeeds with custom password
        res = self.app.post("/api/login", json={
            "role": "student",
            "email": rand_email,
            "password": custom_password
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

        # 5. Faculty Registration (demonstrating INSERT INTO faculty)
        rand_fac_email = f"prof_{random.randint(1000, 9999)}@college.edu"
        res = self.app.post("/api/register-faculty", json={
            "name": "Dr. Testing Faculty",
            "email": rand_fac_email,
            "department": "Computer Science & Engineering",
            "designation": "Associate Professor",
            "password": "faculty123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["role"], "Faculty")

        # Verify active session has registered faculty details
        sess_res = self.app.get("/api/session")
        sess_data = sess_res.get_json()
        self.assertEqual(sess_data["role"], "faculty")
        self.assertEqual(sess_data["user_name"], "Dr. Testing Faculty")

        # Verify index page renders faculty name and faculty portal
        index_res = self.app.get("/")
        self.assertEqual(index_res.status_code, 200)
        self.assertIn(b"Dr. Testing Faculty", index_res.data)
        self.assertIn(b"Faculty Portal", index_res.data)

        # 6. Login as newly registered faculty
        res = self.app.post("/api/login", json={
            "role": "faculty",
            "email": rand_fac_email,
            "password": "faculty123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["role"], "faculty")

        # Verify index page still renders faculty name after login
        index_res = self.app.get("/")
        self.assertEqual(index_res.status_code, 200)
        self.assertIn(b"Dr. Testing Faculty", index_res.data)

        # 7. Logout
        res = self.app.post("/api/logout")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["redirect"], "/login")

    def test_6_role_based_access_control(self):
        """Verify students are strictly blocked from faculty administrative endpoints."""
        # 1. Login as Student
        res = self.app.post("/api/login", json={
            "role": "student",
            "email": "aditya@college.edu",
            "password": "student123"
        })
        self.assertEqual(res.status_code, 200)

        # 2. Student attempt to create a project -> MUST FAIL (HTTP 403)
        res = self.app.post("/api/projects", json={
            "project_name": "Unauthorized Student Project",
            "description": "Should be blocked by RBAC",
            "team_size": 3
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access Denied", res.get_json()["error"])

        # 3. Student attempt to approve a team -> MUST FAIL (HTTP 403)
        res = self.app.put("/api/teams/1/status", json={"status": "Approved"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access Denied", res.get_json()["error"])

        # 4. Student attempt to save/approve a team directly -> MUST FAIL (HTTP 403)
        res = self.app.post("/api/teams", json={
            "project_id": 1,
            "team_name": "Unauthorized Team",
            "member_ids": [1, 2],
            "coverage_score": 90.0
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access Denied", res.get_json()["error"])

        # 5. Student attempt unauthorized escalation to faculty -> MUST FAIL (HTTP 403)
        res = self.app.post("/api/session", json={"role": "faculty"})
        self.assertEqual(res.status_code, 403)
        self.assertIn("Unauthorized", res.get_json()["error"])

        # 6. Login as Faculty
        res = self.app.post("/api/login", json={
            "role": "faculty",
            "email": "faculty@college.edu",
            "password": "faculty123"
        })
        self.assertEqual(res.status_code, 200)

        # 7. Faculty authorized to create project -> MUST SUCCEED (HTTP 200)
        res = self.app.post("/api/projects", json={
            "project_name": "Faculty Capstone Verification",
            "description": "Created with faculty authorization",
            "team_size": 4,
            "required_skills": [{"skill_id": 1, "importance": "High"}]
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])

        # 8. Faculty authorized to update team status -> MUST SUCCEED (HTTP 200)
        res = self.app.put("/api/teams/1/status", json={"status": "Approved"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])


if __name__ == "__main__":
    unittest.main()


