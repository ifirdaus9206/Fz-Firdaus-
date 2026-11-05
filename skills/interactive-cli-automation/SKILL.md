---
name: interactive-cli-automation
description: "Drive prompt-driven CLIs over a pty session."
version: 1.0.0
author: Ketua
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [CLI, PTY, Automation, Auth, gh, Termux]
    related_skills: [github-auth, hermes-agent]
---

# Driving Interactive CLIs from a Non-Interactive Agent

Use when a CLI must be run but it **asks questions** (device-code login, `[Y/n]`, password
prompt, REPL menu) and flags cannot skip them. Examples: `gh auth login --web`, `ssh-keygen`,
`git credential` prompts, `aws configure`, first-run wizards.

**Core rule: any prompt-driven command must run with `pty=true` in the background.**
A plain `terminal(background=true, ...)` call has no TTY: the program prints its banner, then
blocks forever with **no visible prompt and no error**. It looks "running" on poll and you
learn nothing. That silent hang is the #1 trap.

## Steps

1. **Check for a non-interactive path first.** Try env vars / flags before resorting to PTY
   (`GH_PROMPT_DISABLED`, `-y`, `--yes`, `DEBIAN_FRONTEND=noninteractive`, `--with-token`).
2. **Launch under a PTY, in the background:** `terminal(command="<cli>", background=True, pty=True)`.
3. **Poll, then `wait` ~15-20s** so it prints its prompt: `process(action="poll", session_id=...)`
   then `process(action="wait", timeout=20)`. A `wait` that times out while still running is normal.
4. **Read the question.** For a `[Y/n]` / "press Enter" prompt answer with
   `process(action="submit", data="")` (blank line = Enter) or `data="y"`.
5. **Relay any one-time code verbatim**, with the exact URL and numbered steps. Put a device
   code on its own line in bold — never bury it in prose.
6. **State the expiry window** (GitHub device codes: ~15 min) and offer a fresh one if it lapses.
7. **Verify independently after the user confirms** (`gh auth status`, `ssh -T git@github.com`) and
   quote the real output as proof. A user's "dah" is not proof.
8. Kill stale sessions before re-running, or two PTY instances fight over the same flow.

## Pitfalls

- **Never send an account password to a CLI or API that expects a token.** GitHub, most cloud
  APIs, and git-over-HTTPS all reject password auth. If the user volunteers a password in chat:
  say plainly it cannot be used, confirm you stored it nowhere, and offer token / device-code /
  SSH key instead. Do not quietly retry with it.
- Device-code flows need the **user's browser**; you cannot finish them yourself. Present it as
  their step, not a failure.
- Custom `.bashrc` banners appear in PTY output before the real prompt — ignore them.
- `2>&1 | head -40` inside the background command can swallow the prompt and hide ANSI escapes;
  prefer no pipe when the goal is to read an interactive prompt.
- On Termux/Android the "open browser" step usually fails harmlessly; the CLI keeps polling after
  Enter, so submitting a blank line is still correct.

## References

- `references/gh-device-login.md` — worked transcript of `gh auth login --web` over PTY.
