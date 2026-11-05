# Worked transcript: `gh auth login --web` over PTY (Termux)

Context: user gave a GitHub email + account password and asked to "log in". GitHub killed
password auth for git/API in 2021, so the password is useless for automation. `gh` was
installed but `gh auth status` said "You are not logged into any GitHub hosts".

## What failed

Plain background, no pty:

```
terminal(command="cd ~ && GH_PROMPT_DISABLED= gh auth login --hostname github.com --git-protocol https --web 2>&1 | head -40", background=True)
```

Poll/wait 15s three times → only the shell welcome banner, no prompt, process "running"
forever. Reason: no TTY, plus the `| head -40` pipe, so the prompt was never rendered.

## What worked

```
terminal(command="gh auth login --hostname github.com --git-protocol https --web", background=True, pty=True)
process(action="poll", session_id="<id>")            # banner only
process(action="wait", session_id="<id>", timeout=20)
```

`wait` times out (normal) but by then the output contains:

```
! First copy your one-time code: 9910-EC78
Press Enter to open https://github.com/login/device in your browser...
```

Then:

```
process(action="submit", session_id="<id>", data="")   # blank line = Enter
```

On Termux the browser-open fails harmlessly; the CLI keeps polling.

## What to tell the user

- Code in bold on its own line, with the URL **github.com/login/device**, plus numbered steps
  (open URL → sign in as `<username>` → enter code → Continue → Authorize github → reply "dah").
- Say the code is valid ~15 minutes and offer to mint a new one if it lapses.
- Say explicitly that their password was not stored anywhere.

## Verify afterwards (proof, not vibes)

```
gh auth status
git config --global --get user.name; git config --global --get user.email
gh repo list --limit 5
```

## Non-interactive alternatives (prefer these when available)

- Token: `echo "$TOKEN" | gh auth login --with-token && gh auth setup-git`
- SSH: `ssh-keygen -t ed25519 -C "<email>" -f ~/.ssh/id_ed25519 -N ""` then paste the `.pub`
  at github.com/settings/keys, verify with `ssh -T git@github.com`
- git-only: `git config --global credential.helper store`, then use a PAT as the password.
