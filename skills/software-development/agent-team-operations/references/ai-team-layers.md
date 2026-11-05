# The 11 layers of an AI agent team (and how to score a setup)

Distilled from a practitioner walkthrough (Indonesian YouTube, "full setup AI team on Hermes",
video `oZh7SpRN1sk`). One-line thesis: **Hermes is one layer; the system around it is what makes
agents useful.** Installing Hermes alone gives a chatbot that is harder to use than a chatbot.

## Layers, in build order

| # | Layer | What it means in practice | Common state found | Fix |
|---|---|---|---|---|
| 1 | Infrastructure | A machine that runs 24/7, isolated from personal data (mini PC / VPS) | Termux phone: OS can kill processes | VPS, or wake-lock + keeper cron (fragile) |
| 2 | Brain / model | Model per role; strongest for the lead, cheap/free for light roles | One model for everything | Pin a model per profile |
| 3 | Channel | Telegram for the owner, WhatsApp for customers (paid, official) | Telegram bot + gateway | — |
| 4 | Team structure | One profile per job, not one agent for all jobs | One profile with hundreds of text personas | 4–6 real profiles |
| 5 | Lead agent | Manages sub-agents, onboards new ones, troubleshoots | Lead doing the work itself | Doctrine + SOUL.md |
| 6 | Board / dashboard | Kanban, "office" view, who works / who sleeps | Tabs of state, no assignment view | Runs panel |
| 7 | Short-term memory | profile / soul / user / memory / agent.md | Present | keep it small |
| 8 | Long-term memory | Obsidian vault, bidirectional links, written by the agents | Not connected | point agents at a vault |
| 9 | Knowledge | LLM Wiki = SOP / FAQ / facts (≠ memory) | Not set up | `knowledge_base/` in wiki form (recipe: `knowledge-base-wiki.md`) |
| 10 | Workspace | One folder per agent, write only there | Shared folder | `workspaces/<agent>/` |
| 11 | SOP = skills | Skills as the agent's procedures | Usually strong | — |
| 12 | Backup | Nightly git push of the home, done by an agent | Missing | cron + `no_agent` script |
| 13 | External tools (MCP) | Universal port to third-party systems | Missing | add only when a real system must be touched |
| 14 | Automation | Cron + workflows (often built by the lead, not by hand) | Partial | cron per role |

## Rules worth quoting back to the owner

- **Memory vs knowledge:** memory is experience (what happened to us); wiki is factual reference
  (SOP, prices, FAQ). Storing facts as memory bloats context and biases answers.
- **Don't buy the newest model.** Value sits in the SOPs, workflows and accumulated context. New
  models arrive monthly; the team's configuration is what compounds.
- **Don't build N profiles because the roster has N agents.** Cost and maintenance scale with
  profiles; 4–6 covers finance / sales / marketing / ops / engineering / assistant.
- **Isolation is safety.** Agents are probabilistic; run them where deleting the wrong folder does
  not destroy the owner's life's work.

## Scoring a setup (do this before proposing anything)

For each layer write one of: `ADA` / `SEPARA` / `TIADA`, plus the **evidence path** that proves it
(config file, directory, cron id, API response). Present that table before the priority list —
the owner's complaint is usually explained by exactly one `TIADA` row (typically #4 or #5), and the
rest are upgrades, not emergencies.
