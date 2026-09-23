/**
 * app.js - Client Application Logic
 * Student Skill Graph & Team Builder
 * Course Context: Python & DBMS Academic Project
 */

// Global State
let currentRole = "student";
let currentStudentId = 1;
let allStudents = [];
let allSkills = [];
let allProjects = [];
let networkInstance = null;
let rawGraphData = null;
let currentGraphFilter = "all";
let skillsChart = null;
let categoryChart = null;

// ==========================================
// Initialization
// ==========================================
document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();
  await loadSession();
  await loadGlobalData();
  await refreshActiveView();
  
  // Hash routing
  window.addEventListener("hashchange", handleHashChange);
  if (window.location.hash) {
    handleHashChange();
  }
});

// ==========================================
// Navigation & Tab Management
// ==========================================
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const tabName = item.getAttribute("data-tab");
      switchTab(tabName);
    });
  });
}

function switchTab(tabName) {
  // Security guard: intercept unauthorized access
  if (currentRole === "student" && ["faculty-dash", "create-project", "student-roster"].includes(tabName)) {
    showToast("Faculty Access Required: This feature is reserved for Faculty members.", "error");
    tabName = "student-dash";
    window.location.hash = "student-dash";
  } else if (currentRole === "faculty" && ["my-skills", "my-profile"].includes(tabName)) {
    showToast("Individual Student Mode: Log in as a student to edit personal student skills.", "info");
    tabName = "faculty-dash";
    window.location.hash = "faculty-dash";
  } else if (currentRole === "faculty" && tabName === "recommendations") {
    showToast("Build Team is a student feature for finding project teammates.", "info");
    tabName = "faculty-dash";
    window.location.hash = "faculty-dash";
  }

  // Update sidebar active link
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-tab") === tabName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  // Update tabs visibility
  document.querySelectorAll(".content-tab").forEach(tab => {
    tab.classList.remove("active");
  });
  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) {
    targetTab.classList.add("active");
  }

  // Update breadcrumb
  const breadcrumb = document.getElementById("breadcrumb-current");
  const tabTitles = {
    "home": "Home & Overview",
    "student-dash": "Student Dashboard",
    "my-skills": "My Skills & Proficiency",
    "my-profile": "My Student Profile",
    "skill-graph": "NetworkX Skill Graph",
    "projects": currentRole === "faculty" ? "Manage Projects" : "Explore Projects",
    "recommendations": currentRole === "faculty" ? "Team Approvals & Builder" : "Rule-Based Team Builder",
    "faculty-dash": "Faculty Analytics",
    "create-project": "Create New Project",
    "student-roster": "Student Directory & Roster",
    "dbms-showcase": "DBMS & SQL Viva Showcase"
  };
  if (breadcrumb) {
    breadcrumb.textContent = tabTitles[tabName] || "Dashboard";
  }

  window.location.hash = tabName;
  onTabOpened(tabName);
}

function handleHashChange() {
  const hash = window.location.hash.replace("#", "");
  if (hash) {
    switchTab(hash);
  }
}

async function onTabOpened(tabName) {
  if (tabName === "student-dash" || tabName === "my-skills" || tabName === "my-profile") {
    await loadStudentData(currentStudentId);
  } else if (tabName === "skill-graph") {
    await loadAndRenderGraph();
  } else if (tabName === "projects") {
    await loadProjects();
  } else if (tabName === "recommendations") {
    await loadRecommendationsTab();
  } else if (tabName === "faculty-dash") {
    await loadFacultyDashboard();
  } else if (tabName === "create-project") {
    setupCreateProjectForm();
  } else if (tabName === "student-roster") {
    await loadStudentRoster();
  } else if (tabName === "dbms-showcase") {
    await loadDbmsShowcase();
  }
}

// ==========================================
// Session & Identity Management
// ==========================================
let currentUserName = "";

async function loadSession() {
  try {
    const res = await fetch("/api/session");
    const data = await res.json();
    currentRole = data.role || "student";
    currentStudentId = data.student_id || 1;
    currentUserName = data.user_name || "";
    updateIdentityUI();
  } catch (err) {
    console.error("Failed to load session:", err);
  }
}

function updateIdentityUI() {
  // Apply body classes for CSS visibility rules
  if (currentRole === "faculty") {
    document.body.classList.remove("is-student");
    document.body.classList.add("is-faculty");
  } else {
    document.body.classList.remove("is-faculty");
    document.body.classList.add("is-student");
  }

  const badge = document.getElementById("active-role-badge");
  const avatar = document.getElementById("active-avatar");
  const nameEl = document.getElementById("active-user-name");
  const subEl = document.getElementById("active-user-sub");
  const idLabel = document.getElementById("active-identity-label");
  const navProjects = document.getElementById("nav-projects-label");
  const navRec = document.getElementById("nav-recommendations-label");
  const projectsSub = document.getElementById("projects-tab-sub");

  if (currentRole === "faculty") {
    if (badge) {
      badge.textContent = "Faculty";
      badge.style.background = "rgba(139, 92, 246, 0.2)";
      badge.style.color = "var(--accent)";
    }
    if (idLabel) idLabel.textContent = "Faculty Portal";
    if (avatar) {
      avatar.textContent = "Prof";
      avatar.style.borderColor = "var(--accent)";
    }
    if (nameEl) nameEl.textContent = currentUserName || "Dr. S. K. Raman";
    if (subEl) subEl.textContent = "Faculty Advisor & Evaluator";
    if (navProjects) navProjects.textContent = "Manage Projects";
    if (projectsSub) projectsSub.textContent = "Faculty capstone projects with skill prerequisites and team size targets";
  } else {
    if (badge) {
      badge.textContent = "Student";
      badge.style.background = "var(--primary-light)";
      badge.style.color = "var(--primary)";
    }
    if (idLabel) idLabel.textContent = "Student Portal";
    if (avatar) avatar.style.borderColor = "var(--primary)";
    if (navProjects) navProjects.textContent = "Explore Projects";
    if (navRec) navRec.textContent = "Team Builder";
    if (projectsSub) projectsSub.textContent = "Browse open projects and evaluate which match your verified skills";

    const currentStudent = allStudents.find(s => s.student_id == currentStudentId);
    if (currentStudent) {
      const initials = currentStudent.name.split(" ").map(w => w[0]).slice(0, 2).join("");
      if (avatar) avatar.textContent = initials.toUpperCase();
      if (nameEl) nameEl.textContent = currentStudent.name;
      if (subEl) subEl.textContent = `${currentStudent.department} • Year ${currentStudent.year}`;
    }
  }
}

function openStudentSwitcherModal() {
  const modal = document.getElementById("role-modal");
  if (modal) modal.classList.remove("hidden");
  populateStudentPicker();
}

function openRoleSwitcherModal() {
  openStudentSwitcherModal();
}

function closeRoleSwitcherModal() {
  const modal = document.getElementById("role-modal");
  if (modal) modal.classList.add("hidden");
}

function populateStudentPicker() {
  const select = document.getElementById("student-picker-select");
  if (!select) return;
  select.innerHTML = allStudents.map(s => `
    <option value="${s.student_id}" ${s.student_id == currentStudentId ? 'selected' : ''}>
      ${s.name} (${s.department}, Year ${s.year})
    </option>
  `).join("");
}

async function setStudent(studentId) {
  try {
    studentId = parseInt(studentId);
    const res = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: "student", student_id: studentId })
    });
    const data = await res.json();
    if (data.success) {
      currentRole = "student";
      currentStudentId = studentId;
      currentUserName = data.user_name || "";
      closeRoleSwitcherModal();
      updateIdentityUI();
      showToast(`Active student switched to profile #${studentId}`, "success");
      await loadStudentData(studentId);
      switchTab("student-dash");
    } else {
      showToast(data.error || "Failed to switch student", "error");
    }
  } catch (err) {
    showToast("Error switching student", "error");
  }
}

async function setRole(role) {
  if (role === "faculty" && currentRole !== "faculty") {
    showToast("Direct role escalation disabled. Please authenticate via Faculty Login.", "error");
    setTimeout(() => {
      window.location.href = "/login";
    }, 600);
    return;
  }
}

// ==========================================
// Data Fetching Helpers
// ==========================================
async function loadGlobalData() {
  try {
    const [studentsRes, skillsRes, projectsRes] = await Promise.all([
      fetch("/api/students"),
      fetch("/api/skills"),
      fetch("/api/projects")
    ]);
    allStudents = await studentsRes.json();
    allSkills = await skillsRes.json();
    allProjects = await projectsRes.json();
    updateIdentityUI();
  } catch (err) {
    console.error("Failed to load global data:", err);
  }
}

async function refreshActiveView() {
  await loadStudentData(currentStudentId);
}

// ==========================================
// Student Dashboard & Profile
// ==========================================
async function loadStudentData(studentId) {
  try {
    const res = await fetch(`/api/students/${studentId}`);
    if (!res.ok) return;
    const student = await res.json();

    // 1. Update Student Dash KPIs
    const countEl = document.getElementById("dash-skill-count");
    if (countEl) countEl.textContent = student.skills ? student.skills.length : 0;
    
    const projEl = document.getElementById("dash-project-count");
    if (projEl) projEl.textContent = student.projects ? student.projects.length : 0;

    const availEl = document.getElementById("dash-availability");
    if (availEl) availEl.textContent = student.availability || "High";

    const deptEl = document.getElementById("dash-dept");
    if (deptEl) deptEl.textContent = `${student.department} (Yr ${student.year})`;

    // 2. Render Student Skills Pills in Dashboard
    const skillsListEl = document.getElementById("dash-skills-list");
    if (skillsListEl) {
      if (!student.skills || student.skills.length === 0) {
        skillsListEl.innerHTML = `<p class="text-muted">No skills registered yet. Click Manage to add skills.</p>`;
      } else {
        skillsListEl.innerHTML = student.skills.map(sk => `
          <div class="skill-pill">
            <span>${sk.skill_name}</span>
            <span class="badge-prof ${sk.proficiency}">${sk.proficiency}</span>
          </div>
        `).join("");
      }
    }

    // 3. Render Student Teams / Projects
    const teamsListEl = document.getElementById("dash-teams-list");
    if (teamsListEl) {
      if (!student.projects || student.projects.length === 0) {
        teamsListEl.innerHTML = `<p class="text-muted">Not assigned to any approved teams yet. Check Projects or generate team recommendations.</p>`;
      } else {
        teamsListEl.innerHTML = student.projects.map(p => `
          <div class="member-card mb-2">
            <div class="member-card-header">
              <div class="member-card-avatar"><i class="fa-solid fa-folder"></i></div>
              <div class="member-card-meta">
                <h4>${p.project_name}</h4>
                <p>Team: <strong>${p.team_name}</strong> • Status: <span class="badge-prof Advanced">${p.team_status}</span></p>
              </div>
            </div>
          </div>
        `).join("");
      }
    }

    // 4. Render Recommended Projects for Student
    renderRecommendedProjectsForStudent(student);

    // 5. Populate Profile Tab Form & Record Inspector
    populateProfileForm(student);

    // 6. Populate Skills Management Tab
    populateSkillsManagementTab(student);

  } catch (err) {
    console.error("Error loading student data:", err);
  }
}

function renderRecommendedProjectsForStudent(student) {
  const container = document.getElementById("dash-recommended-projects");
  if (!container) return;

  const studentSkillNames = new Set((student.skills || []).map(s => s.skill_name.toLowerCase()));
  
  const matches = allProjects.map(proj => {
    let matchedCount = 0;
    (proj.required_skills || []).forEach(req => {
      if (studentSkillNames.has(req.skill_name.toLowerCase())) {
        matchedCount++;
      }
    });
    return { project: proj, matches: matchedCount };
  });

  matches.sort((a, b) => b.matches - a.matches);
  const topProjects = matches.slice(0, 2);

  container.innerHTML = topProjects.map(item => `
    <div class="project-card">
      <div class="project-card-header">
        <h4 class="project-title">${item.project.project_name}</h4>
        <span class="badge-prof Advanced">${item.matches} Skills Matched</span>
      </div>
      <p class="project-desc">${item.project.description}</p>
      <div class="project-skills-list">
        ${(item.project.required_skills || []).map(sk => `
          <span class="skill-pill">
            ${sk.skill_name}
            <span class="badge-imp ${sk.importance}">${sk.importance}</span>
          </span>
        `).join("")}
      </div>
      <button class="btn-sm btn-primary" onclick="prepareRecommendationForProject(${item.project.project_id})">
        <i class="fa-solid fa-wand-magic-sparkles"></i> Build Team for This
      </button>
    </div>
  `).join("");
}

function populateProfileForm(student) {
  const nameInput = document.getElementById("prof-name");
  const emailInput = document.getElementById("prof-email");
  const deptInput = document.getElementById("prof-dept");
  const yearInput = document.getElementById("prof-year");
  const availInput = document.getElementById("prof-availability");
  const interestsInput = document.getElementById("prof-interests");

  if (nameInput) nameInput.value = student.name || "";
  if (emailInput) emailInput.value = student.email || "";
  if (deptInput) deptInput.value = student.department || "Computer Science";
  if (yearInput) yearInput.value = student.year || 2;
  if (availInput) availInput.value = student.availability || "High";
  if (interestsInput) interestsInput.value = student.interests || "";
}

async function handleUpdateProfile(event) {
  event.preventDefault();
  const payload = {
    name: document.getElementById("prof-name").value,
    email: document.getElementById("prof-email").value,
    department: document.getElementById("prof-dept").value,
    year: parseInt(document.getElementById("prof-year").value),
    availability: document.getElementById("prof-availability").value,
    interests: document.getElementById("prof-interests").value
  };

  try {
    const res = await fetch(`/api/students/${currentStudentId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      showToast("Student profile updated successfully in SQLite!", "success");
      await loadGlobalData();
      await loadStudentData(currentStudentId);
    } else {
      showToast(result.error || "Failed to update profile", "error");
    }
  } catch (err) {
    showToast("Server error updating profile", "error");
  }
}

// ==========================================
// Skills Management (Add / Remove / Modify)
// ==========================================
function populateSkillsManagementTab(student) {
  // Populate skill select options
  const select = document.getElementById("skill-select");
  if (select) {
    select.innerHTML = '<option value="">-- Choose Skill --</option>' + allSkills.map(sk => `
      <option value="${sk.skill_id}">${sk.skill_name} (${sk.category})</option>
    `).join("");
  }

  // Populate current skills table
  const tbody = document.getElementById("skills-table-body");
  if (!tbody) return;

  if (!student.skills || student.skills.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-muted text-center">No skills registered. Add one above!</td></tr>`;
    return;
  }

  tbody.innerHTML = student.skills.map(sk => `
    <tr>
      <td><strong>${sk.skill_name}</strong></td>
      <td><span class="text-secondary">${sk.category}</span></td>
      <td><span class="badge-prof ${sk.proficiency}">${sk.proficiency}</span></td>
      <td>
        <button class="btn-remove-skill" onclick="handleRemoveSkill(${sk.skill_id})" title="Delete Skill from Profile">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>
  `).join("");
}

async function handleAddStudentSkill(event) {
  event.preventDefault();
  const skillId = parseInt(document.getElementById("skill-select").value);
  const proficiency = document.getElementById("proficiency-select").value;

  if (!skillId) {
    showToast("Please select a skill", "error");
    return;
  }

  try {
    const res = await fetch(`/api/students/${currentStudentId}/skills`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skill_id: skillId, proficiency: proficiency })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Skill recorded in SQLite `student_skills`!", "success");
      await loadStudentData(currentStudentId);
    } else {
      showToast(data.error || "Failed to save skill", "error");
    }
  } catch (err) {
    showToast("Server communication error", "error");
  }
}

async function handleRemoveSkill(skillId) {
  if (!confirm("Are you sure you want to remove this skill from your profile?")) return;

  try {
    const res = await fetch(`/api/students/${currentStudentId}/skills/${skillId}`, {
      method: "DELETE"
    });
    const data = await res.json();
    if (data.success) {
      showToast("Skill deleted from SQLite `student_skills`", "success");
      await loadStudentData(currentStudentId);
    } else {
      showToast(data.error || "Failed to remove skill", "error");
    }
  } catch (err) {
    showToast("Error deleting skill", "error");
  }
}

async function handleCreateNewSkill(event) {
  event.preventDefault();
  const name = document.getElementById("new-skill-name").value.trim();
  const category = document.getElementById("new-skill-category").value;

  if (!name) return;

  try {
    const res = await fetch("/api/skills", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skill_name: name, category: category })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Skill '${name}' inserted into SQLite 'skills' table!`, "success");
      document.getElementById("new-skill-name").value = "";
      await loadGlobalData();
      populateSkillsManagementTab(allStudents.find(s => s.student_id == currentStudentId));
    } else {
      showToast(data.error || "Skill could not be created", "error");
    }
  } catch (err) {
    showToast("Error creating new skill", "error");
  }
}

// ==========================================
// NetworkX Graph Visualization (Vis.js)
// ==========================================
async function loadAndRenderGraph() {
  try {
    const res = await fetch("/api/graph");
    rawGraphData = await res.json();

    // Update Stats in Toolbar
    document.getElementById("graph-node-count").textContent = rawGraphData.stats.total_nodes;
    document.getElementById("graph-edge-count").textContent = rawGraphData.stats.total_edges;
    document.getElementById("graph-density").textContent = rawGraphData.stats.graph_density;

    // Render Centrality List
    const centralityContainer = document.getElementById("centrality-badges");
    if (centralityContainer && rawGraphData.stats.top_connected_skills) {
      centralityContainer.innerHTML = rawGraphData.stats.top_connected_skills.map(sk => `
        <div class="skill-pill">
          <span><strong>${sk.name}</strong></span>
          <span class="badge-prof Intermediate">${sk.degree} connections</span>
        </div>
      `).join("");
    }

    renderVisNetwork(rawGraphData.nodes, rawGraphData.edges);
  } catch (err) {
    console.error("Error loading NetworkX graph:", err);
  }
}

function renderVisNetwork(nodesArray, edgesArray) {
  const container = document.getElementById("network-canvas");
  if (!container) return;

  const data = {
    nodes: new vis.DataSet(nodesArray),
    edges: new vis.DataSet(edgesArray)
  };

  const options = {
    nodes: {
      font: {
        color: "#F8FAFC",
        size: 13,
        face: "Inter"
      },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      smooth: {
        type: "continuous"
      },
      arrows: {
        to: { enabled: false }
      }
    },
    physics: {
      barnesHut: {
        gravitationalConstant: -3500,
        centralGravity: 0.35,
        springLength: 95,
        springConstant: 0.04,
        damping: 0.09
      },
      stabilization: {
        iterations: 150
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      zoomView: true
    }
  };

  if (networkInstance) {
    networkInstance.destroy();
  }

  networkInstance = new vis.Network(container, data, options);

  // Click event listener
  networkInstance.on("click", (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const clickedNode = nodesArray.find(n => n.id === nodeId);
      if (clickedNode) {
        showNodeInspector(clickedNode);
      }
    }
  });
}

function filterGraph(filterType) {
  currentGraphFilter = filterType;

  // Update button active state
  document.querySelectorAll(".btn-filter").forEach(btn => {
    btn.classList.remove("active");
  });
  event.target.classList.add("active");

  if (!rawGraphData) return;

  let filteredNodes = rawGraphData.nodes;
  let filteredEdges = rawGraphData.edges;

  if (filterType === "students-skills") {
    filteredNodes = rawGraphData.nodes.filter(n => n.entity_type === "student" || n.entity_type === "skill");
    const allowedNodeIds = new Set(filteredNodes.map(n => n.id));
    filteredEdges = rawGraphData.edges.filter(e => allowedNodeIds.has(e.from) && allowedNodeIds.has(e.to));
  } else if (filterType === "projects-skills") {
    filteredNodes = rawGraphData.nodes.filter(n => n.entity_type === "project" || n.entity_type === "skill");
    const allowedNodeIds = new Set(filteredNodes.map(n => n.id));
    filteredEdges = rawGraphData.edges.filter(e => allowedNodeIds.has(e.from) && allowedNodeIds.has(e.to));
  }

  renderVisNetwork(filteredNodes, filteredEdges);
}

function handleGraphSearch() {
  const query = document.getElementById("graph-search-input").value.toLowerCase().trim();
  if (!query || !networkInstance || !rawGraphData) return;

  const match = rawGraphData.nodes.find(n => n.label.toLowerCase().includes(query));
  if (match) {
    networkInstance.focus(match.id, {
      scale: 1.2,
      animation: { duration: 600, easingFunction: "easeInOutQuad" }
    });
    networkInstance.selectNodes([match.id]);
    showNodeInspector(match);
  }
}

function showNodeInspector(node) {
  const inspector = document.getElementById("node-inspector");
  const title = document.getElementById("inspector-title");
  const content = document.getElementById("inspector-content");

  inspector.classList.remove("hidden");
  title.innerHTML = `<span style="color: ${node.color}">●</span> ${node.label}`;

  let html = `<p><strong>Entity Type:</strong> <span class="badge-role">${node.entity_type.toUpperCase()}</span></p>`;

  if (node.entity_type === "student") {
    html += `
      <p><strong>Department:</strong> ${node.department}</p>
      <p><strong>Year of Study:</strong> Year ${node.year}</p>
      <p><strong>Availability:</strong> ${node.availability}</p>
      <p><strong>Interests:</strong> ${node.interests}</p>
      <p><strong>Degree Centrality:</strong> ${node.centrality}</p>
      <p><strong>Connected Skills:</strong> ${node.degree}</p>
    `;
  } else if (node.entity_type === "skill") {
    html += `
      <p><strong>Skill Category:</strong> ${node.category}</p>
      <p><strong>Network Centrality:</strong> ${node.centrality}</p>
      <p><strong>Total Connections:</strong> ${node.degree}</p>
    `;
  } else if (node.entity_type === "project") {
    html += `
      <p><strong>Required Team Size:</strong> ${node.team_size}</p>
      <p><strong>Status:</strong> ${node.status}</p>
      <p><strong>Linked Prerequisites:</strong> ${node.degree}</p>
    `;
  }

  content.innerHTML = html;
}

function closeInspector() {
  document.getElementById("node-inspector").classList.add("hidden");
}

// ==========================================
// Projects View
// ==========================================
async function loadProjects() {
  try {
    const res = await fetch("/api/projects");
    allProjects = await res.json();
    const container = document.getElementById("projects-container");
    if (!container) return;

    // If Faculty, update KPI overview bar at top of Manage Projects tab
    if (currentRole === "faculty") {
      const totalProjects = allProjects.length;
      let approvedTeamsCount = 0;
      const allocatedStudentIds = new Set();
      let projectsWithApprovedTeams = 0;

      allProjects.forEach(p => {
        const appTeams = (p.teams || []).filter(t => t.status === "Approved");
        approvedTeamsCount += appTeams.length;
        if (appTeams.length > 0) projectsWithApprovedTeams++;
        appTeams.forEach(t => {
          (t.members || []).forEach(m => allocatedStudentIds.add(m.student_id));
        });
      });

      const totalEl = document.getElementById("fac-proj-total");
      const appEl = document.getElementById("fac-proj-approved-teams");
      const studEl = document.getElementById("fac-proj-students-allocated");
      const pendEl = document.getElementById("fac-proj-pending");

      if (totalEl) totalEl.textContent = totalProjects;
      if (appEl) appEl.textContent = approvedTeamsCount;
      if (studEl) studEl.textContent = allocatedStudentIds.size;
      if (pendEl) pendEl.textContent = totalProjects - projectsWithApprovedTeams;
    }

    if (allProjects.length === 0) {
      container.innerHTML = `<div class="empty-state"><h3>No projects yet. Click Create New Project!</h3></div>`;
      return;
    }

    container.innerHTML = allProjects.map(p => {
      const approvedTeams = (p.teams || []).filter(t => t.status === "Approved");
      const otherTeams = (p.teams || []).filter(t => t.status !== "Approved");

      return `
      <div class="project-card">
        <div class="project-card-header">
          <h3 class="project-title">${p.project_name}</h3>
          <span class="badge-prof ${p.status === 'Approved' || p.status === 'In Progress' ? 'Advanced' : 'Intermediate'}">
            ${p.status}
          </span>
        </div>
        <p class="project-desc">${p.description || "No description provided."}</p>
        <div class="project-meta-row">
          <span><i class="fa-solid fa-users"></i> Target Team Size: <strong>${p.team_size}</strong></span>
          <span><i class="fa-solid fa-layer-group"></i> Skills Required: <strong>${(p.required_skills || []).length}</strong></span>
        </div>
        <div class="project-skills-list">
          ${(p.required_skills || []).map(sk => `
            <span class="skill-pill">
              ${sk.skill_name}
              <span class="badge-imp ${sk.importance}">${sk.importance}</span>
            </span>
          `).join("")}
        </div>

        ${currentRole === 'faculty' ? `
          <!-- FACULTY VIEW: APPROVED & FORMED TEAMS INFORMATION -->
          <div class="faculty-teams-section mt-3" style="border-top: 1px solid var(--border-color); padding-top: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 6px;">
                <i class="fa-solid fa-shield-halved" style="color: ${approvedTeams.length > 0 ? 'var(--success)' : 'var(--text-muted)'};"></i>
                Approved Teams (${approvedTeams.length})
              </span>
              <span class="badge-prof ${approvedTeams.length > 0 ? 'Advanced' : 'Intermediate'}" style="font-size: 10px;">
                ${approvedTeams.length > 0 ? `${approvedTeams.length} Active` : 'Unassigned'}
              </span>
            </div>

            ${approvedTeams.length > 0 ? approvedTeams.map(t => `
              <div class="approved-team-card mb-2" style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: var(--radius-sm); padding: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                  <div>
                    <strong style="color: var(--success); font-size: 13px;"><i class="fa-solid fa-circle-check"></i> ${t.team_name}</strong>
                    <span style="font-size: 11px; color: var(--text-muted); margin-left: 4px;">(#Team ${t.team_id})</span>
                  </div>
                  <span class="badge-prof Advanced" style="font-size: 10px;">${t.coverage_score}% Skill Match</span>
                </div>

                <div style="margin-top: 6px;">
                  <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; font-weight: 600;">
                    Assigned Team Members (${(t.members || []).length}/${p.team_size}):
                  </div>
                  <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    ${(t.members && t.members.length > 0) ? t.members.map(m => `
                      <span class="skill-pill" style="font-size: 11px; padding: 3px 8px; background: var(--bg-surface-elevated); border: 1px solid rgba(16, 185, 129, 0.25);">
                        <i class="fa-solid fa-user-graduate" style="color: var(--primary); font-size: 10px; margin-right: 3px;"></i>
                        <strong>${m.name}</strong> <span class="text-muted">(${m.department}, Yr ${m.year})</span>
                      </span>
                    `).join("") : `<span class="text-muted" style="font-size: 11px;">No member records found.</span>`}
                  </div>
                </div>

                <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center; border-top: 1px dashed rgba(16, 185, 129, 0.2); padding-top: 6px;">
                  <span style="font-size: 10px; color: var(--text-muted);">
                    <i class="fa-solid fa-database" style="color: var(--success);"></i> Live in SQLite teams table
                  </span>
                  <button class="btn-sm btn-outline-danger" onclick="updateTeamStatus(${t.team_id}, 'Rejected')" style="padding: 2px 8px; font-size: 10px;">
                    <i class="fa-solid fa-rotate-left"></i> Revoke Approval
                  </button>
                </div>
              </div>
            `).join("") : `
              <div style="background: var(--bg-primary); border: 1px dashed var(--border-color); border-radius: var(--radius-sm); padding: 10px; text-align: center;">
                <p class="text-muted" style="font-size: 11px; margin: 0;">
                  <i class="fa-solid fa-hourglass-half" style="color: var(--warning); margin-right: 4px;"></i>
                  No approved teams yet. Students can propose teams matching prerequisites.
                </p>
              </div>
            `}

            ${otherTeams.length > 0 ? `
              <div class="mt-2">
                <details style="font-size: 11px; color: var(--text-secondary);">
                  <summary style="cursor: pointer; font-weight: 600; color: var(--warning); padding: 2px 0;">
                    <i class="fa-solid fa-clock-rotate-left"></i> Pending Proposals (${otherTeams.length})
                  </summary>
                  <div class="mt-2" style="display: flex; flex-direction: column; gap: 6px;">
                    ${otherTeams.map(ot => `
                      <div style="background: var(--bg-primary); padding: 8px 10px; border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--border-color);">
                        <div>
                          <strong style="color: var(--text-primary); font-size: 12px;">${ot.team_name}</strong>
                          <span style="font-size: 10px; color: var(--text-muted); margin-left: 4px;">(${ot.coverage_score}% coverage)</span>
                          <span class="badge-prof ${ot.status === 'Recommended' ? 'Intermediate' : 'Beginner'}" style="font-size: 9px; margin-left: 4px;">${ot.status}</span>
                        </div>
                        ${ot.status !== 'Approved' ? `
                          <button class="btn-sm btn-primary" onclick="updateTeamStatus(${ot.team_id}, 'Approved')" style="padding: 3px 8px; font-size: 10px;">
                            <i class="fa-solid fa-check"></i> Approve
                          </button>
                        ` : ''}
                      </div>
                    `).join("")}
                  </div>
                </details>
              </div>
            ` : ''}
          </div>
        ` : `
          <!-- STUDENT VIEW -->
          ${approvedTeams.length > 0 ? `
            <div class="mt-3">
              <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: var(--radius-sm); padding: 8px 12px; display: flex; align-items: center; justify-content: space-between;">
                <span style="font-size: 12px; color: var(--success); font-weight: 600;">
                  <i class="fa-solid fa-circle-check"></i> Team Finalized (${approvedTeams[0].team_name})
                </span>
                <span class="badge-prof Advanced" style="font-size: 10px;">${approvedTeams[0].coverage_score}% Match</span>
              </div>
            </div>
          ` : `
            <div class="mt-3">
              <button class="btn-primary btn-block" onclick="prepareRecommendationForProject(${p.project_id})">
                <i class="fa-solid fa-wand-magic-sparkles"></i> Build Team
              </button>
            </div>
          `}
        `}
      </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Error loading projects:", err);
  }
}

function prepareRecommendationForProject(projectId) {
  switchTab("recommendations");
  const select = document.getElementById("rec-project-select");
  if (select) {
    select.value = projectId;
    loadProjectRequirementsPreview();
    triggerRecommendation();
  }
}

// ==========================================
// Team Recommendation Engine
// ==========================================
async function loadRecommendationsTab() {
  const select = document.getElementById("rec-project-select");
  if (!select) return;

  await loadGlobalData();
  select.innerHTML = '<option value="">-- Choose Project --</option>' + allProjects.map(p => `
    <option value="${p.project_id}">${p.project_name} (Team Size: ${p.team_size})</option>
  `).join("");
}

function loadProjectRequirementsPreview() {
  const select = document.getElementById("rec-project-select");
  const projectId = select.value;
  const previewBox = document.getElementById("rec-project-preview");
  const skillsContainer = document.getElementById("rec-preview-skills");

  if (!projectId) {
    previewBox.classList.add("hidden");
    return;
  }

  const project = allProjects.find(p => p.project_id == projectId);
  if (!project || !project.required_skills) {
    previewBox.classList.add("hidden");
    return;
  }

  previewBox.classList.remove("hidden");
  skillsContainer.innerHTML = project.required_skills.map(sk => `
    <div class="skill-pill">
      <span>${sk.skill_name}</span>
      <span class="badge-imp ${sk.importance}">${sk.importance}</span>
    </div>
  `).join("");
}

async function triggerRecommendation() {
  const select = document.getElementById("rec-project-select");
  const projectId = select.value;

  if (!projectId) {
    showToast("Please select a project first", "error");
    return;
  }

  const resultsContainer = document.getElementById("recommendation-results");
  resultsContainer.innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-gear fa-spin icon-empty"></i>
      <h3>Calculating Optimal Skill Coverage...</h3>
      <p>Python rule-based heuristic evaluating student proficiencies, complementarity, and availability...</p>
    </div>
  `;

  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: parseInt(projectId) })
    });
    const proposals = await res.json();

    if (proposals.error) {
      resultsContainer.innerHTML = `<div class="empty-state"><h3>${proposals.error}</h3></div>`;
      return;
    }

    resultsContainer.innerHTML = proposals.map((prop, idx) => `
      <div class="recommendation-card">
        <div class="rec-header">
          <div class="rec-team-title">
            <i class="fa-solid fa-shield-halved" style="color: var(--primary)"></i>
            ${prop.team_name}
            <span class="coverage-pill">${prop.coverage_score}% Skill Coverage</span>
          </div>
          <div class="rec-actions">
            ${currentRole === 'faculty' ? `
              <button class="btn-primary" onclick="handleApproveTeam(${prop.project_id}, '${prop.team_name}', ${prop.coverage_score}, [${prop.member_ids.join(',')}])">
                <i class="fa-solid fa-check-circle"></i> Approve Team (Faculty)
              </button>
              <button class="btn-outline-danger" onclick="handleRejectTeam(${prop.project_id}, '${prop.team_name}')">
                <i class="fa-solid fa-xmark"></i> Reject
              </button>
            ` : `
              <span class="badge-student-action">
                <i class="fa-solid fa-graduation-cap"></i> Recommended Balanced Formation • Pending Faculty Approval
              </span>
            `}
          </div>
        </div>

        <!-- Explainable Reason for Viva -->
        <div class="rec-explanation-box">
          <strong><i class="fa-solid fa-circle-info"></i> Recommendation Explanation:</strong><br>
          ${prop.explanation}
        </div>

        <!-- Matched Skills vs Gaps Breakdown -->
        <div class="skills-coverage-summary">
          <div>
            <h4 class="mb-2" style="color: var(--success); font-weight: 700;">
              <i class="fa-solid fa-check"></i> Matched Competencies (${prop.matched_skills.length}):
            </h4>
            <div class="styled-list">
              ${prop.matched_skills.map(ms => `
                <div>
                  <strong>${ms.skill_name}</strong> (${ms.importance} Importance) — Covered by: <span class="text-secondary">${ms.provided_by}</span>
                </div>
              `).join("")}
            </div>
          </div>
          <div>
            <h4 class="mb-2" style="color: ${prop.missing_skills.length > 0 ? 'var(--danger)' : 'var(--text-muted)'}; font-weight: 700;">
              <i class="fa-solid fa-triangle-exclamation"></i> Potential Gaps (${prop.missing_skills.length}):
            </h4>
            <div class="styled-list">
              ${prop.missing_skills.length === 0 
                ? '<p class="text-muted">None! 100% of required prerequisites are covered by team members.</p>'
                : prop.missing_skills.map(gs => `<div><strong>${gs.skill_name}</strong> (${gs.importance} Importance)</div>`).join("")
              }
            </div>
          </div>
        </div>

        <!-- Member Profiles -->
        <h4 class="mb-2" style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 16px 0 10px;">
          Proposed Team Members:
        </h4>
        <div class="members-grid">
          ${prop.members.map(m => `
            <div class="member-card">
              <div class="member-card-header">
                <div class="member-card-avatar">
                  ${m.name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase()}
                </div>
                <div class="member-card-meta">
                  <h4>${m.name}</h4>
                  <p>${m.department} • Year ${m.year}</p>
                </div>
              </div>
              <div class="project-skills-list">
                ${m.skills_summary.slice(0, 4).map(sk => `
                  <span class="skill-pill" style="font-size: 11px;">
                    ${sk.name}
                    <span class="badge-prof ${sk.proficiency}">${sk.proficiency}</span>
                  </span>
                `).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `).join("");

  } catch (err) {
    resultsContainer.innerHTML = `<div class="empty-state"><h3>Server error generating recommendations</h3></div>`;
  }
}

async function handleApproveTeam(projectId, teamName, coverageScore, memberIds) {
  if (currentRole !== "faculty") {
    showToast("Access Denied: Only faculty members can approve teams.", "error");
    return;
  }

  try {
    const res = await fetch("/api/teams", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: projectId,
        team_name: teamName,
        coverage_score: coverageScore,
        member_ids: memberIds,
        status: "Approved"
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Team '${teamName}' officially Approved and stored in SQLite!`, "success");
      await loadGlobalData();
      switchTab("faculty-dash");
    } else {
      showToast(data.error || "Failed to approve team", "error");
    }
  } catch (err) {
    showToast("Server error approving team", "error");
  }
}

function handleRejectTeam(projectId, teamName) {
  if (currentRole !== "faculty") {
    showToast("Access Denied: Only faculty members can reject teams.", "error");
    return;
  }
  showToast(`Team '${teamName}' proposal rejected. Try tweaking student skills or project prerequisites!`, "info");
}

// ==========================================
// Student Roster (Faculty Exclusive)
// ==========================================
let _allRosterStudents = [];

async function loadStudentRoster() {
  const container = document.getElementById("roster-container");
  if (!container) return;
  try {
    const res = await fetch("/api/students");
    const students = await res.json();
    _allRosterStudents = students;
    renderStudentRoster(students);
  } catch (err) {
    console.error("Error loading roster:", err);
  }
}

function renderStudentRoster(students) {
  const container = document.getElementById("roster-container");
  if (!container) return;

  if (!students || students.length === 0) {
    container.innerHTML = `<div class="empty-state"><h3>No student records found matching query.</h3></div>`;
    return;
  }

  container.innerHTML = students.map(s => {
    const initials = s.name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
    return `
      <div class="student-roster-card">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div class="avatar" style="border-color: var(--accent); color: var(--text-primary); font-size: 13px;">${initials}</div>
            <div>
              <h4 style="font-size: 15px; font-weight: 700; color: var(--text-primary);">${s.name}</h4>
              <p class="text-secondary" style="font-size: 12px;">${s.department} • Year ${s.year}</p>
            </div>
          </div>
          <span class="badge-role" style="background: rgba(139, 92, 246, 0.15); color: var(--accent);">ID: #${s.student_id}</span>
        </div>
        <div style="display: flex; gap: 14px; font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
          <span><i class="fa-solid fa-clock"></i> Availability: <strong style="color: var(--text-primary);">${s.availability || 'High'}</strong></span>
          <span><i class="fa-solid fa-layer-group"></i> Total Skills: <strong style="color: var(--text-primary);">${s.skill_count || 0}</strong></span>
        </div>
        <div style="margin-top: 4px;">
          <span class="text-muted" style="font-size: 11px; text-transform: uppercase; font-weight: 600;">Interests:</span>
          <p style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">${s.interests || 'General Engineering'}</p>
        </div>
      </div>
    `;
  }).join("");
}

function handleRosterSearch() {
  const input = document.getElementById("roster-search-input");
  if (!input || !_allRosterStudents) return;
  const q = input.value.toLowerCase().trim();
  const filtered = _allRosterStudents.filter(s => 
    s.name.toLowerCase().includes(q) || 
    s.department.toLowerCase().includes(q) || 
    (s.interests && s.interests.toLowerCase().includes(q))
  );
  renderStudentRoster(filtered);
}

// ==========================================
// Faculty Analytics Dashboard
// ==========================================
async function loadFacultyDashboard() {
  try {
    const [statsRes, teamsRes] = await Promise.all([
      fetch("/api/stats"),
      fetch("/api/teams")
    ]);
    const stats = await statsRes.json();
    const teams = await teamsRes.json();

    // KPIs
    document.getElementById("fac-students-count").textContent = stats.kpis.total_students;
    document.getElementById("fac-skills-count").textContent = stats.kpis.total_skills;
    document.getElementById("fac-projects-count").textContent = stats.kpis.total_projects;
    document.getElementById("fac-teams-count").textContent = stats.kpis.approved_teams;

    // Render Charts
    renderSkillsDistributionChart(stats.skill_distribution);
    renderCategoryDistributionChart(stats.category_distribution);

    // Render Teams Table
    renderAllTeamsTable(teams);
  } catch (err) {
    console.error("Error loading faculty stats:", err);
  }
}

function renderSkillsDistributionChart(data) {
  const ctx = document.getElementById("chart-skills-dist");
  if (!ctx) return;

  const labels = data.map(d => d.skill_name);
  const counts = data.map(d => d.student_count);

  if (skillsChart) skillsChart.destroy();

  skillsChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Number of Students",
        data: counts,
        backgroundColor: "#3B82F6",
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, color: "#94A3B8" },
          grid: { color: "#334155" }
        },
        x: {
          ticks: { color: "#94A3B8" },
          grid: { display: false }
        }
      }
    }
  });
}

function renderCategoryDistributionChart(data) {
  const ctx = document.getElementById("chart-categories-dist");
  if (!ctx) return;

  const labels = data.map(d => d.category);
  const counts = data.map(d => d.count);

  if (categoryChart) categoryChart.destroy();

  categoryChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: [
          "#3B82F6", "#10B981", "#F59E0B", "#EC4899",
          "#8B5CF6", "#EF4444", "#06B6D4", "#6366F1"
        ],
        borderWidth: 2,
        borderColor: "#1E293B"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: "#94A3B8", font: { size: 11 } }
        }
      }
    }
  });
}

function renderAllTeamsTable(teams) {
  const tbody = document.getElementById("all-teams-tbody");
  if (!tbody) return;

  if (teams.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No teams created yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = teams.map(t => `
    <tr>
      <td>#${t.team_id}</td>
      <td><strong>${t.team_name}</strong></td>
      <td>${t.project_name}</td>
      <td><span class="badge-prof Advanced">${t.coverage_score}%</span></td>
      <td>
        ${(t.members || []).map(m => m.name).join(", ")}
      </td>
      <td>
        <span class="badge-prof ${t.status === 'Approved' ? 'Advanced' : 'Beginner'}">${t.status}</span>
      </td>
      <td>
        ${t.status !== 'Approved' ? `
          <button class="btn-sm btn-primary" onclick="updateTeamStatus(${t.team_id}, 'Approved')">Approve</button>
        ` : `
          <button class="btn-sm btn-outline-danger" onclick="updateTeamStatus(${t.team_id}, 'Rejected')">Reject</button>
        `}
      </td>
    </tr>
  `).join("");
}

async function updateTeamStatus(teamId, status) {
  try {
    const res = await fetch(`/api/teams/${teamId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Team status set to ${status}`, "success");
      await loadGlobalData();
      await loadProjects();
      await loadFacultyDashboard();
    }
  } catch (err) {
    showToast("Error updating team status", "error");
  }
}

// ==========================================
// Create Project Form
// ==========================================
function setupCreateProjectForm() {
  const container = document.getElementById("project-skills-rows");
  if (!container || container.children.length > 0) return;

  // Add 3 default skill rows
  addProjectSkillRow();
  addProjectSkillRow();
  addProjectSkillRow();
}

function addProjectSkillRow() {
  const container = document.getElementById("project-skills-rows");
  if (!container) return;

  const row = document.createElement("div");
  row.className = "form-row mt-2 align-end project-skill-entry";
  row.innerHTML = `
    <div class="form-group flex-2 mb-0">
      <label>Skill</label>
      <select class="form-control proj-skill-id" required>
        <option value="">-- Choose Skill --</option>
        ${allSkills.map(s => `<option value="${s.skill_id}">${s.skill_name} (${s.category})</option>`).join("")}
      </select>
    </div>
    <div class="form-group flex-1 mb-0">
      <label>Importance</label>
      <select class="form-control proj-skill-imp" required>
        <option value="High" selected>High</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
      </select>
    </div>
    <button type="button" class="btn-outline-danger btn-sm" style="margin-bottom: 2px;" onclick="this.parentElement.remove()">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;
  container.appendChild(row);
}

async function handleCreateProject(event) {
  event.preventDefault();
  const name = document.getElementById("proj-name").value.trim();
  const desc = document.getElementById("proj-desc").value.trim();
  const teamSize = parseInt(document.getElementById("proj-team-size").value);

  const skillEntries = document.querySelectorAll(".project-skill-entry");
  const requiredSkills = [];

  skillEntries.forEach(entry => {
    const sId = entry.querySelector(".proj-skill-id").value;
    const imp = entry.querySelector(".proj-skill-imp").value;
    if (sId) {
      requiredSkills.push({
        skill_id: parseInt(sId),
        importance: imp
      });
    }
  });

  if (requiredSkills.length === 0) {
    showToast("Please add at least one required skill for the project", "error");
    return;
  }

  try {
    const res = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_name: name,
        description: desc,
        team_size: teamSize,
        required_skills: requiredSkills
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast("Project and prerequisites committed to SQLite!", "success");
      document.getElementById("create-project-form").reset();
      await loadGlobalData();
      switchTab("projects");
    } else {
      showToast(data.error || "Failed to create project", "error");
    }
  } catch (err) {
    showToast("Error saving project", "error");
  }
}

// ==========================================
// DBMS & SQL Viva Showcase
// ==========================================
async function loadDbmsShowcase() {
  try {
    const res = await fetch("/api/dbms-showcase");
    const data = await res.json();

    // Render Schema Cards
    const schemaGrid = document.getElementById("dbms-schema-grid");
    if (schemaGrid) {
      schemaGrid.innerHTML = data.tables.map(t => `
        <div class="schema-table-card">
          <div class="schema-table-header">
            <span class="schema-table-name"><i class="fa-solid fa-table"></i> ${t.name}</span>
          </div>
          <p class="schema-table-desc">${t.purpose}</p>
          <div class="schema-table-keys">
            <div><strong>PK:</strong> <code>${t.pk}</code></div>
            <div><strong>FKs:</strong> <code>${t.fks}</code></div>
          </div>
        </div>
      `).join("");
    }

    // Render Joins List
    const joinsContainer = document.getElementById("dbms-joins-list");
    if (joinsContainer) {
      joinsContainer.innerHTML = data.key_joins.map(j => `
        <div class="join-demo-card">
          <h4>${j.title}</h4>
          <p class="join-concept">${j.concept}</p>
          <pre class="code-box">${j.sql}</pre>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading DBMS showcase:", err);
  }
}

async function runCustomSql() {
  const query = document.getElementById("custom-sql-input").value.trim();
  const outputContainer = document.getElementById("sql-console-output");

  if (!query) {
    showToast("Please enter a SQL query", "error");
    return;
  }

  outputContainer.innerHTML = `<p class="text-muted">Executing on skills.db...</p>`;

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const result = await res.json();

    if (!result.success) {
      outputContainer.innerHTML = `<div class="callout callout-info" style="border-left-color: var(--danger); color: var(--danger);"><strong>Error:</strong> ${result.error}</div>`;
      return;
    }

    if (result.rows.length === 0) {
      outputContainer.innerHTML = `<p class="text-muted">Query executed successfully. 0 rows returned.</p>`;
      return;
    }

    // Render Table
    let tableHtml = `
      <p class="text-muted mb-2">Returned ${result.row_count} rows:</p>
      <div style="overflow-x: auto;">
        <table class="table">
          <thead>
            <tr>${result.columns.map(c => `<th>${c}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${result.rows.map(row => `
              <tr>${result.columns.map(c => `<td>${row[c] !== null ? row[c] : '<em>NULL</em>'}</td>`).join("")}</tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
    outputContainer.innerHTML = tableHtml;
  } catch (err) {
    outputContainer.innerHTML = `<p class="text-danger">Failed to execute query.</p>`;
  }
}

// ==========================================
// Utilities & Toast Notifications
// ==========================================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-info')}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

async function fetchLiveStats() {
  await loadGlobalData();
  await refreshActiveView();
  showToast("All data synchronized with SQLite", "success");
}

async function resetDatabasePrompt() {
  if (!confirm("Reset database to clean initial sample college data? This will restore original students, projects, and skills.")) {
    return;
  }

  try {
    const res = await fetch("/api/reset-db", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast("Database reset to initial demo state!", "success");
      await loadGlobalData();
      await refreshActiveView();
    }
  } catch (err) {
    showToast("Error resetting database", "error");
  }
}

async function handleLogout() {
  try {
    const res = await fetch("/api/logout", { method: "POST" });
    const data = await res.json();
    showToast("Logged out successfully. Redirecting to login...", "info");
    setTimeout(() => {
      window.location.href = data.redirect || "/login";
    }, 350);
  } catch (err) {
    window.location.href = "/login";
  }
}

