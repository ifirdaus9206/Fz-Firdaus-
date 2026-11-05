---
name: git-host-ssh-provisioning
description: "Set up and verify SSH keys for GitHub or GitLab."
version: 1.0.0
author: Ketua (curator)
license: MIT
platforms: [linux, macos, android-termux, windows]
metadata:
  hermes:
    tags: [SSH, GitHub, GitLab, Auth, Verification, Mobile, Termux]
    related_skills: [github-auth, github-repo-management, safe-git-config-backup]
---

# Git Host SSH Provisioning & Verification

Set up SSH access to a git host (GitHub, GitLab, Bitbucket, self-hosted Gitea) for a **human user who must do the paste step**, and prove it worked with real command output. Written for the case where you are on a phone/Termux and the user is tapping a web UI — the failure modes there are almost never the key, they are identity and UI.

`github-auth` (bundled) has the generic setup steps. **This skill carries the parts that actually bite: confirming which account, proving the key is intact, and driving a mobile paste.**

## When to use

- User asks to "log in to GitHub", "set up SSH", "push to a repo" and auth is missing.
- `ssh -T git@github.com` returns `Permission denied (publickey)`.
- User says "I think you typed the key wrong" or "no submit button appeared".
- Any time credentials for a git host are being arranged for a *user-owned* account.

## Rule 0 — Identity before keys

Never derive the username from a password, an email prefix, a folder name, or a URL slug the user typed loosely. Verify it:

```bash
curl -s https://api.github.com/users/<username>      # 404 => wrong username
curl -s https://api.github.com/users/<username>/keys # [] => key not registered there
```

Facts to report back to the user:
- `login` = the real account name (what auth checks)
- `name` = display name, often just a first name — **not** the login
- `/keys` list = whether their paste landed at all

Public SSH keys are readable unauthenticated, so this check works without any credentials on your side. It distinguishes "user pasted into the wrong account" from "user has not pasted" in one second — both of which look identical to `Permission denied (publickey)`.

## Step 1 — Generate or locate the key

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || ssh-keygen -t ed25519 -C "<user-email>" -f ~/.ssh/id_ed25519 -N ""
ssh-keygen -lf ~/.ssh/id_ed25519.pub     # fingerprint, quote this to the user
```

## Step 2 — Prove the public key matches the private key (before blaming the paste)

```bash
A=$(awk '{print $1" "$2}' ~/.ssh/id_ed25519.pub)
B=$(ssh-keygen -y -f ~/.ssh/id_ed25519 | awk '{print $1" "$2}')
[ "$A" = "$B" ] && echo "KEY OK" || echo "KEY CORRUPT"
```

**Pitfall that cost a whole round trip:** `ssh-keygen -y` re-appends the comment, so a plain `diff` of full lines reports a mismatch on a perfectly good key. Compare fields 1–2 only (or md5sum the blob).

Give the user something human-comparable: the `SHA256:...` fingerprint or the **last 8 characters** of the blob. Nobody verifies 68 base64 chars on a phone.

## Step 3 — Drive the paste on mobile

GitHub's "Add new SSH key" page, mobile browser:
- **Key type must be `Authentication Key`.** A `Signing Key` never satisfies `ssh -T`.
- The Key textarea shows grey placeholder text ("Begins with 'ssh-rsa'…") that reads like content. It is empty until pasted — users interpret an empty field + no button as "the agent typed it wrong".
- The green **Add SSH key** button is below the fold, **hidden behind the on-screen keyboard**. The button is disabled while Key is empty.

Instruction order that works:
1. Dismiss the keyboard (small `v` at bottom-right, or Back).
2. Long-press the key inside the chat message → Copy → paste into Key.
3. Scroll down → **Add SSH key**.
4. Reply "dah" → you re-test immediately.

Clipboard automation is unreliable: `termux-clipboard-set "$(cat ~/.ssh/id_ed25519.pub)" && echo filled` can exit 0 with an empty clipboard. Always confirm with `termux-clipboard-get | wc -c` (0 = failed) and fall back to long-press copy.

## Step 4 — Verify with evidence, not assertion

```bash
timeout 25 ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes -T git@github.com 2>&1 | tail -3
```

Success = `Hi <login>! You've successfully authenticated`. Note it prints to **stderr**, so `| tail` needs `2>&1`.

If it still fails, escalate the evidence one level rather than retrying blindly:

```bash
ssh -o BatchMode=yes -T -v git@github.com 2>&1 | grep -iE "Offering|Authentications that can continue|denied"
```

`Offering public key: ... SHA256:xxx` + `Permission denied` = key sent, key unknown to host → wrong account or not added. No `Offering` line at all = key file/permissions problem locally (`chmod 600`).

## Step 5 — Wire git and confirm the account behind the key

```bash
git config --global user.name "<name>"
git config --global user.email "<email>"
git config --global credential.helper store   # only if also using HTTPS
git config --global url."git@github.com:".insteadOf "https://github.com/"
git ls-remote git@github.com:<login>/<repo>.git   # real read test
```

## Reporting style (this user)

- Lead with the **test result as raw output**, then a one-line plain-language meaning ("GitHub tidak mengenali kunci ini").
- State your own error plainly and immediately when a fact was wrong ("Akaun sebetulnya `ifirdaus9206`; `firdaus120723` itu password — aku tersilap"). Do not bury it.
- No jargon chains; numbered taps, one screen at a time.
- End with a 3–4 numbered option list; the user answers by number.

## Environment notes (Termux/Android)

- `/tmp` is **not writable** in Termux. Use `~/tmp` (or `$TMPDIR`) for scratch files in verification one-liners.
- Termux:API calls can silently no-op; verify the side effect instead of trusting an exit code.

## Reference

- `references/github-mobile-ssh-session.md` — the concrete 404 / empty-keys transcript and fingerprint from the session that produced this skill.
- `scripts/verify-git-ssh.sh` — one-shot probe: identity check, key integrity, verbose ssh diagnosis.