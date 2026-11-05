# `gh auth login --web` from a non-interactive agent shell (Termux, 2026-11-06)

Context: `~/.hermes20` had a working git repo, a tested backup script, and no remote. The last
step was human: authenticate `gh`. `gh auth status` → *"You are not logged into any GitHub
hosts."* No `GITHUB_TOKEN`/`GH_TOKEN` in `.env`, no `~/.config/gh/`, no `~/.git-credentials`,
no global `credential.helper`.

## What did NOT work (all looped on the same prompt)

Target output was the one-time code. Every attempt died at:

```
? Authenticate Git with your GitHub credentials? (Y/n)
```

1. **PTY session + `process submit "y"`** — prompt redrawn, no progress after 4 minutes.
   `submit` writes `y` + Enter; the survey prompt did not advance.
2. **`printf 'Y\n' | script -qec "gh auth login … --web" /dev/null`** — the `Y` echoed once,
   then the prompt was re-rendered; `gh` re-asks on EOF instead of accepting the piped answer.
3. **Hand-written Python pty driver**
   (`pty.openpty()` + `subprocess.Popen(stdin=slave)` + `select()` + write `Y\r` on detecting
   the prompt) — identical loop. The write lands before gh enters raw mode or is flushed by the
   redraw; either way the answer is lost. Do not spend more time on this path.

Reading `^C` on the process each time was safe: no partial auth state was written
(`gh auth status` still reported "not logged into any GitHub hosts").

## What worked

```bash
git config --global credential.https://github.com.helper '!gh auth git-credential'
```

That records the answer to "authenticate git with your GitHub credentials?" as configuration,
so gh no longer asks. Then:

```bash
# background process; do NOT add `timeout`
gh auth login --hostname github.com --git-protocol https --web
```

Immediate output:

```
! First copy your one-time code: 8399-6AB2
Open this URL to continue in your web browser: https://github.com/login/device
```

The process then stays alive polling GitHub. Two runs produced two different codes
(`FA26-09F3`, then `8399-6AB2`) — the earlier code dies with the process that minted it, so
always read the newest line and re-issue rather than reusing a stale code.

## Sequencing learned

- A first probe wrapped in `timeout 60` printed a valid-looking code and then killed the
  poller at 60 s. The code was useless. Never bound this command with a timeout.
- Authorization is a browser action by the owner: give code + URL in one short message, and say
  the code expires (~15 min) plus "ask me to regenerate" — do not ask them to run terminal
  commands.
- After they authorize, `gh auth status` is the proof; then `git remote add origin <private URL>`
  and let the nightly script push. Verify the repo is private instead of trusting the flag.

## Repo-side fallbacks that are *not* better

`gh auth login --with-token` (paste a PAT) works but forces the owner to create and transmit a
credential; the device code is safer and shorter for them. Keep `--with-token` as the fallback
only when a token already exists in the environment.
