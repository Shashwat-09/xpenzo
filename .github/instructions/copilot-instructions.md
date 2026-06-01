---
applyTo: "**"
---

# Copilot Global Instructions

## 🧠 RULE #1 — READ CONTEXT FIRST (MANDATORY)
Before responding to ANYTHING, every agent MUST:
1. Read `#file:.github/context/project-context.md` completely
2. Read `#file:.github/context/chat-history.md` for recent decisions
3. Confirm with: ✅ Context loaded — [project name], last activity: [last log entry]
4. Only then proceed with the task

If these files don't exist yet, create them before starting work.

---

## 🔄 RULE #2 — UPDATE CONTEXT AFTER EVERY RESPONSE
After every response, every agent MUST append a summary to `.github/context/chat-history.md` in this format:

```
## [DATE TIME] [AGENT NAME] — [one line summary of what was done]
- **Decided:** [key decision made]
- **Built/Produced:** [what was created or changed]
- **Context updated:** [yes/no — what section in project-context.md was updated]
- **Next recommended:** [what should happen next]
---
```

---

## 📋 RULE #3 — UPDATE PROJECT CONTEXT WHEN THINGS CHANGE
If a response changes or establishes anything permanent, the agent MUST update the relevant section in `.github/context/project-context.md`:
- New stack choice → update **Tech Stack** section
- New schema → update **Database Schema** section
- New API endpoints → update **API Contracts** section
- New env variable → update **Environment Variables** section
- Feature completed → move to **Completed Features** section
- Important decision → append to **Key Decisions** table
- Found issue or deferred work → append to **Known Issues**

---

## ⚠️ NEVER skip reading context. NEVER skip updating context.
## Every agent, every chat, every time — no exceptions.
