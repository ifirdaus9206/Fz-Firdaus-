# Session evidence — GitHub SSH key on a phone (2026-11-06)

## What the user supplied vs what was true

| Supplied | Interpretation made | Reality |
|---|---|---|
| "laluan GitHub: firdaus<REDACTED-PASSWORD>" | treated as **username** | it was the **password**; `api.github.com/users/firdaus<REDACTED-PASSWORD>` → `404 Not Found` |
| email `ifirdaus9206@gmail.com` | used as commit email | correct |
| — | — | real account: `login=ifirdaus9206`, `name=Firdaus`, `id=224862779` |

The user spotted it themselves: *"pasai cipta api siap dia tulis Firdaus … Salah nama tu"* — the web UI showed display name `Firdaus`, not the login they gave me.

**Lesson:** one `curl api.github.com/users/<name>` before any auth work. A 404 there is cheap; discovering it after the user has pasted a key into a different account is not.

## Probe output that resolved the confusion

```
AKAUN firdaus<REDACTED-PASSWORD>: TIADA (Not Found)
AKAUN itifdaus9206 : TIADA (Not Found)
AKAUN ifirdaus9206 : ADA -> login=ifirdaus9206 name=Firdaus id=224862779 created=2025-08-05
  kunci: [ ]            <- empty: the key had never been added
```

`ssh -T` evidence in the same state:

```
debug1: Offering public key: ~/.ssh/id_ed25519 ED25519 SHA256:FvqIIFHU9d9TxQkNjdSkFAOK/kmYIY1RnIFEa5IUoh4
debug1: Authentications that can continue: publickey
git@github.com: Permission denied (publickey)
```

Key offered + denied ⇒ host does not know the key ⇒ not added / wrong account. Never "regenerate the key" at this point.

## The false-mismatch trap

`diff <(ssh-keygen -y -f id_ed25519) <(awk '{print $1" "$2}' id_ed25519.pub)` printed `TIDAK SAMA` while the blobs were identical — `ssh-keygen -y` had re-appended the `user@host` comment. Comparing `$1" "$2` from both sides showed equality. The user had meanwhile said *"Aku rasa kau salah tulis kot"*; the correct reply was cryptographic proof (blob equal + fingerprint), not a re-typed key.

## Mobile UI observations (from the user's screenshot)

- Page: `github.com/settings/ssh/new`, Title `Termux-Ketua`, Key type `Authentication Key`.
- **Key textarea empty**, showing grey placeholder `Begins with 'ssh-rsa', 'ecdsa-sha2-nistp256'…`.
- On-screen keyboard covering the bottom ⇒ no visible **Add SSH key** button ⇒ user: *"Tak keluar butang hantar di sana"*.
- Fix sequence that was given: dismiss keyboard → long-press key in chat → Copy → paste → scroll down → Add SSH key.

## Clipboard attempt

`termux-clipboard-set "$(cat ~/.ssh/id_ed25519.pub)" && echo "clipboard: DIISI"` exited 0, but `termux-clipboard-get | wc -c` returned `0`. Exit code lied; verify content length.

## Environment

`/tmp` is read-only in this Termux install (`bash: /tmp/derived.pub: Permission denied`) — scratch files must go to `~/tmp` or `$TMPDIR`.