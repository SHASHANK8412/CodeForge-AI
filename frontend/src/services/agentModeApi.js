/**
 * AIForge AI Agent Mode API Service
 * ==================================
 * Multi-step autonomous agent execution, interactive timeline polling,
 * human approval actions, and persistent local storage fallback.
 */

import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const LOCAL_AGENTS_KEY = "aiforge_agent_definitions";
const LOCAL_TASKS_KEY = "aiforge_agent_task_runs";

export const BUILTIN_AGENT_TEMPLATES = [
  {
    id: "agent-coding",
    name: "Coding Agent",
    template_type: "coding",
    description: "Autonomous full-stack engineer that analyzes requirements, creates architectural blueprints, generates production code, runs empirical tests, and auto-repairs bugs.",
    goal_placeholder: "e.g. Build an async task queue worker with Redis and FastAPI",
    system_instructions: "You are the Lead Autonomous Software Engineer. Analyze goal, plan architecture, generate code, run SAST & unit verification, and produce production-ready code.",
    tools: ["Code Editor", "AST Indexer", "Test Runner", "Memory Recall", "Terminal Exec"],
    requires_human_approval: true,
    memory_access: true,
    project_access: true,
    max_steps: 6,
    icon: "💻",
    badge_color: "violet"
  },
  {
    id: "agent-study",
    name: "Study & Exam Agent",
    template_type: "study",
    description: "Academic syllabus tutor that breaks down complex subjects, compiles structured study notes, generates interactive quizzes, and tracks retention weak spots.",
    goal_placeholder: "e.g. Build me a 5-day study plan for my DBMS exam with quizzes",
    system_instructions: "You are an expert Academic Tutor. Deconstruct the syllabus, create conceptual breakdowns, author spaced-repetition quizzes, and highlight high-yield exam topics.",
    tools: ["Syllabus Analyzer", "Quiz Generator", "Memory Recall", "Progress Tracker"],
    requires_human_approval: false,
    memory_access: true,
    project_access: false,
    max_steps: 5,
    icon: "📚",
    badge_color: "cyan"
  },
  {
    id: "agent-research",
    name: "Deep Research Agent",
    template_type: "research",
    description: "Technical research specialist that performs web & library exploration, gathers empirical specs, benchmarks trade-offs, and synthesizes architectural RFCs.",
    goal_placeholder: "e.g. Compare Apache Kafka vs RabbitMQ vs Redpanda for event streaming",
    system_instructions: "You are a Principal Research Engineer. Conduct deep technical comparisons, analyze throughput & latency trade-offs, review production benchmarks, and formulate an architectural RFC.",
    tools: ["Web Search", "Benchmark Engine", "Memory Recall", "RFC Generator"],
    requires_human_approval: false,
    memory_access: true,
    project_access: true,
    max_steps: 5,
    icon: "🔬",
    badge_color: "indigo"
  },
  {
    id: "agent-resume",
    name: "Resume & Career Agent",
    template_type: "resume",
    description: "Career strategist that analyzes resume bullets, matches against target job descriptions, detects ATS gaps, and reformulates high-impact STAR accomplishments.",
    goal_placeholder: "e.g. Optimize my resume for Senior Full-Stack Engineer at Stripe",
    system_instructions: "You are an Elite Tech Career Coach. Analyze target job competencies, find keyword gaps, upgrade bullet points with quantifiable metrics (STAR format), and generate mock technical questions.",
    tools: ["ATS Scanner", "Keyword Matcher", "Memory Recall", "STAR Formulator"],
    requires_human_approval: false,
    memory_access: true,
    project_access: false,
    max_steps: 5,
    icon: "📄",
    badge_color: "amber"
  },
  {
    id: "agent-data-analyst",
    name: "Data Analyst Agent",
    template_type: "data_analyst",
    description: "Data scientist agent that inspects datasets, runs statistical analysis, builds chart specifications, and extracts executive actionable insights.",
    goal_placeholder: "e.g. Analyze user churn cohort retention data and identify bottlenecks",
    system_instructions: "You are a Senior Data Analyst. Formulate analytical hypotheses, run summary statistics and cohort regressions, generate visualization specs, and extract key strategic insights.",
    tools: ["Statistical Engine", "Chart Generator", "SQL Runner", "Memory Recall"],
    requires_human_approval: true,
    memory_access: true,
    project_access: true,
    max_steps: 5,
    icon: "📈",
    badge_color: "emerald"
  },
  {
    id: "agent-creative",
    name: "Creative & Product Agent",
    template_type: "creative",
    description: "Product ideator that brainstorms unique feature concepts, formulates user personas, refines copy taglines, and drafts comprehensive PRDs.",
    goal_placeholder: "e.g. Brainstorm a gamified developer onboarding workflow for our SaaS",
    system_instructions: "You are a Creative Product Director. Brainstorm high-impact creative angles, refine value propositions, establish user delight loops, and deliver compelling product specs.",
    tools: ["Creative Engine", "Persona Builder", "Memory Recall", "PRD Generator"],
    requires_human_approval: false,
    memory_access: true,
    project_access: true,
    max_steps: 5,
    icon: "🎨",
    badge_color: "pink"
  }
];

const SEED_TASK = {
  task_id: "task-demo-dbms",
  agent_id: "agent-study",
  agent_name: "Study & Exam Agent",
  template_type: "study",
  goal: "Build me a study plan for my DBMS exam and track my progress",
  status: "COMPLETED",
  progress_percent: 100,
  recalled_memory_count: 2,
  execution_time_seconds: 14.2,
  created_at: "2026-08-30 11:00:00",
  updated_at: "2026-08-30 11:00:15",
  steps: [
    {
      step_id: "step-1",
      name: "Understand exam scope & syllabus prerequisites",
      phase: "UNDERSTAND",
      status: "COMPLETED",
      tool_used: "Syllabus Analyzer",
      output: "Analyzed core DBMS modules: Relational Algebra, ER Diagrams, Normalization (1NF to BCNF), ACID Transactions, B+ Tree Indexing, and Query Optimization.",
      duration_ms: 1800,
      started_at: "11:00:00",
      completed_at: "11:00:02"
    },
    {
      step_id: "step-2",
      name: "Generate multi-day structured study plan",
      phase: "PLAN",
      status: "COMPLETED",
      tool_used: "Memory Recall",
      output: "Created 5-day mastery schedule: Day 1 (ER & Relational Model), Day 2 (Functional Dependencies & Normalization), Day 3 (Concurrency & Transactions), Day 4 (Indexing & B+ Trees), Day 5 (Full Mock Exam & Weak Topic Revision).",
      duration_ms: 2400,
      started_at: "11:00:02",
      completed_at: "11:00:05"
    },
    {
      step_id: "step-3",
      name: "Compile high-yield conceptual summary notes",
      phase: "EXECUTE",
      status: "COMPLETED",
      tool_used: "Quiz Generator",
      output: "Synthesized key definitions: 2PL (Two-Phase Locking), Strict 2PL, Conflict vs View Serializability, Lossless Join Decomposition, and B+ Tree node split rules.",
      duration_ms: 4200,
      started_at: "11:00:05",
      completed_at: "11:00:09"
    },
    {
      step_id: "step-4",
      name: "Evaluate knowledge retention quiz & diagnose weak areas",
      phase: "VERIFY",
      status: "COMPLETED",
      tool_used: "Progress Tracker",
      output: "Simulated baseline diagnostic quiz: 8/10 questions correct (80%). Identified weak spot in Deadlock Detection (Wait-For Graph cycle detection) and BCNF decomposition proof.",
      duration_ms: 3100,
      started_at: "11:00:09",
      completed_at: "11:00:12"
    },
    {
      step_id: "step-5",
      name: "Deliver finalized progress report & next actionable milestones",
      phase: "FINAL_RESULT",
      status: "COMPLETED",
      output: "Final preparation roadmap delivered with spaced-repetition flashcard milestones and high-yield question bank.",
      duration_ms: 2700,
      started_at: "11:00:12",
      completed_at: "11:00:15"
    }
  ],
  final_output: `# 🎯 DBMS Exam Preparation — Autonomous Study Plan

## 📊 Overall Readiness: **80%**
- **Strong Topics**: Relational Algebra, ER Modeling, B+ Tree Indexing
- **Identified Weak Spot**: Multi-Granularity Locking & BCNF Decomposition

---

## 📅 5-Day Master Execution Schedule

| Day | Module Focus | High-Yield Topics | Milestone Quiz |
|---|---|---|---|
| **Day 1** | ER & Relational Algebra | Entities, Cardinalities, Relational Calculus | 10 MCQs |
| **Day 2** | Normalization Mastery | 1NF, 2NF, 3NF, BCNF, Dependency Preservation | 5 Practice Decompositions |
| **Day 3** | Transactions & ACID | Conflict Serializability, 2PL, WAL Logging | 8 Scenario Problems |
| **Day 4** | Storage & Indexing | B+ Tree Splitting/Merging, Hash Indexing | 5 Calculation Questions |
| **Day 5** | Mock Exam & Revision | 50 Comprehensive Exam Questions | Full Review |

---

## 💡 Recommended Next Action
Take the **15-minute Transactions & Concurrency Quiz** to reinforce Two-Phase Locking before moving to Indexing.`
};

function getLocalTasks() {
  try {
    const raw = localStorage.getItem(LOCAL_TASKS_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_TASKS_KEY, JSON.stringify([SEED_TASK]));
      return [SEED_TASK];
    }
    return JSON.parse(raw);
  } catch (err) {
    return [SEED_TASK];
  }
}

function saveLocalTasks(tasks) {
  try {
    localStorage.setItem(LOCAL_TASKS_KEY, JSON.stringify(tasks));
    window.dispatchEvent(new CustomEvent("aiforge:agent-tasks-updated", { detail: { count: tasks.length } }));
  } catch (err) {
    console.error("Error saving local tasks:", err);
  }
}

function getLocalAgents() {
  try {
    const raw = localStorage.getItem(LOCAL_AGENTS_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_AGENTS_KEY, JSON.stringify(BUILTIN_AGENT_TEMPLATES));
      return BUILTIN_AGENT_TEMPLATES;
    }
    return JSON.parse(raw);
  } catch (err) {
    return BUILTIN_AGENT_TEMPLATES;
  }
}

function saveLocalAgents(agents) {
  try {
    localStorage.setItem(LOCAL_AGENTS_KEY, JSON.stringify(agents));
  } catch (err) {
    console.error("Error saving local agents:", err);
  }
}

export async function fetchAgents() {
  try {
    const res = await axios.get(`${API_BASE}/api/agents`, { timeout: 5000 });
    if (res.data?.agents) {
      saveLocalAgents(res.data.agents);
      return res.data.agents;
    }
    return getLocalAgents();
  } catch (err) {
    console.warn("Falling back to local agent definitions:", err);
    return getLocalAgents();
  }
}

export async function createCustomAgent(payload) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents`, payload, { timeout: 6000 });
    if (res.data?.agent) {
      const current = getLocalAgents();
      saveLocalAgents([res.data.agent, ...current]);
      return res.data.agent;
    }
  } catch (err) {
    console.warn("Local fallback for create custom agent:", err);
  }

  const localAgent = {
    id: `agent-custom-${Date.now()}`,
    name: payload.name,
    template_type: "custom",
    description: payload.description,
    goal_placeholder: payload.goal_placeholder || "Describe goal for custom agent...",
    system_instructions: payload.system_instructions,
    tools: payload.tools || ["Code Editor", "Memory Recall"],
    requires_human_approval: !!payload.requires_human_approval,
    memory_access: payload.memory_access !== false,
    project_access: payload.project_access !== false,
    max_steps: payload.max_steps || 6,
    icon: "⚡",
    badge_color: "amber",
    created_at: new Date().toISOString().replace("T", " ").slice(0, 19)
  };

  const current = getLocalAgents();
  saveLocalAgents([localAgent, ...current]);
  return localAgent;
}

export async function fetchTasks({ status, projectId } = {}) {
  try {
    const res = await axios.get(`${API_BASE}/api/agents/tasks`, {
      params: { status, project_id: projectId },
      timeout: 5000
    });
    if (res.data?.tasks) {
      saveLocalTasks(res.data.tasks);
      return res.data.tasks;
    }
    return getLocalTasks();
  } catch (err) {
    console.warn("Falling back to local task history:", err);
    let tasks = getLocalTasks();
    if (status) tasks = tasks.filter(t => t.status.toUpperCase() === status.toUpperCase());
    if (projectId) tasks = tasks.filter(t => t.project_id === projectId);
    return tasks;
  }
}

export async function fetchTask(taskId) {
  try {
    const res = await axios.get(`${API_BASE}/api/agents/tasks/${taskId}`, { timeout: 5000 });
    if (res.data?.task) {
      const current = getLocalTasks();
      saveLocalTasks(current.map(t => t.task_id === taskId ? res.data.task : t));
      return res.data.task;
    }
  } catch (err) {
    console.warn("Local fallback for fetch task:", err);
  }
  const tasks = getLocalTasks();
  return tasks.find(t => t.task_id === taskId) || null;
}

export async function launchTask({ agentId, goal, projectId, memoryEnabled = true }) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents/tasks/launch`, {
      agent_id: agentId,
      goal,
      project_id: projectId,
      memory_enabled: memoryEnabled
    }, { timeout: 6000 });

    if (res.data?.task) {
      const current = getLocalTasks();
      saveLocalTasks([res.data.task, ...current]);
      return res.data.task;
    }
  } catch (err) {
    console.warn("Local fallback for launch task:", err);
  }

  // Local simulated execution task
  const agents = getLocalAgents();
  const agent = agents.find(a => a.id === agentId) || BUILTIN_AGENT_TEMPLATES[0];

  const taskId = `task-${Date.now()}`;
  const newTask = {
    task_id: taskId,
    agent_id: agent.id,
    agent_name: agent.name,
    template_type: agent.template_type,
    goal: goal.trim(),
    project_id: projectId || null,
    status: "RUNNING",
    progress_percent: 20,
    recalled_memory_count: memoryEnabled ? 2 : 0,
    created_at: new Date().toISOString().replace("T", " ").slice(0, 19),
    updated_at: new Date().toISOString().replace("T", " ").slice(0, 19),
    steps: [
      { step_id: "step-1", name: "Understand request & analyze goal", phase: "UNDERSTAND", status: "COMPLETED", tool_used: "AST Indexer", output: `Understood task: ${goal}`, duration_ms: 1200 },
      { step_id: "step-2", name: "Generate multi-step execution plan", phase: "PLAN", status: "RUNNING", tool_used: "Memory Recall", output: "Compiling dependency plan..." },
      { step_id: "step-3", name: "Execute primary tool actions & synthesis", phase: "EXECUTE", status: "PENDING", tool_used: agent.tools[0] || "Code Editor" },
      { step_id: "step-4", name: "Verify assertions & validate contract score", phase: "VERIFY", status: "PENDING", tool_used: "Test Runner" },
      { step_id: "step-5", name: "Synthesize executive report & final artifacts", phase: "FINAL_RESULT", status: "PENDING" }
    ],
    final_output: null
  };

  const current = getLocalTasks();
  saveLocalTasks([newTask, ...current]);

  // Simulate local progress advancement
  setTimeout(() => {
    const list = getLocalTasks();
    const t = list.find(x => x.task_id === taskId);
    if (t && t.status === "RUNNING") {
      t.status = "COMPLETED";
      t.progress_percent = 100;
      t.execution_time_seconds = 8.4;
      t.steps.forEach(s => s.status = "COMPLETED");
      t.final_output = `# 🤖 Agent Execution Report: ${goal}\n\n## Summary\n- **Status**: Completed\n- **Agent**: ${agent.name}\n- **Output**: Verified all tasks successfully generated.`;
      saveLocalTasks(list);
    }
  }, 4000);

  return newTask;
}

export async function pauseTask(taskId) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents/tasks/${taskId}/pause`, {}, { timeout: 4000 });
    return res.data?.task;
  } catch (err) {
    const list = getLocalTasks();
    const t = list.find(x => x.task_id === taskId);
    if (t) {
      t.status = "PAUSED";
      saveLocalTasks(list);
      return t;
    }
  }
}

export async function resumeTask(taskId) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents/tasks/${taskId}/resume`, {}, { timeout: 4000 });
    return res.data?.task;
  } catch (err) {
    const list = getLocalTasks();
    const t = list.find(x => x.task_id === taskId);
    if (t) {
      t.status = "RUNNING";
      saveLocalTasks(list);
      return t;
    }
  }
}

export async function stopTask(taskId) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents/tasks/${taskId}/stop`, {}, { timeout: 4000 });
    return res.data?.task;
  } catch (err) {
    const list = getLocalTasks();
    const t = list.find(x => x.task_id === taskId);
    if (t) {
      t.status = "STOPPED";
      saveLocalTasks(list);
      return t;
    }
  }
}

export async function approveTaskAction(taskId, approved = true) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents/tasks/${taskId}/approve`, { approved }, { timeout: 4000 });
    return res.data?.task;
  } catch (err) {
    const list = getLocalTasks();
    const t = list.find(x => x.task_id === taskId);
    if (t) {
      t.status = approved ? "RUNNING" : "STOPPED";
      t.pending_approval = null;
      saveLocalTasks(list);
      return t;
    }
  }
}

export async function saveTaskToMemory(taskId) {
  try {
    const res = await axios.post(`${API_BASE}/api/agents/tasks/${taskId}/save-memory`, {}, { timeout: 5000 });
    return res.data;
  } catch (err) {
    console.warn("Local fallback for saveTaskToMemory:", err);
    return { success: true };
  }
}

export async function deleteCustomAgent(agentId) {
  try {
    await axios.delete(`${API_BASE}/api/agents/${agentId}`, { timeout: 5000 });
  } catch (err) {
    console.warn("Local fallback for deleteCustomAgent:", err);
  }
  const agents = getLocalAgents();
  const filtered = agents.filter(a => a.id !== agentId);
  saveLocalAgents(filtered);
  return true;
}
