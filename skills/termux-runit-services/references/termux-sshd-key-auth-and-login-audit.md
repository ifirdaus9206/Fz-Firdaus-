# Termux sshd: installing a remote host's key, proving it, and auditing logins

Companion to `references/termux-sshd-8022-provisioning.md` (which covers *enabling* sshd and the
`passwd`-over-pty path). This one covers the case: **the user hands you a PC's public key and a
one-block script, and wants confirmation before they try from the PC.**

Session that produced this: phone `192.168.0.41`, sshd already up under runit, user supplied
`ssh-ed25519 … sofia-pc@DESKTOP-P7NSMTR` and a block ending in
`ssh -p 8022 -i ~/.ssh/id_ed25519 termux@192.168.0.41 "echo SAMBUNGAN_BERJAYA; whoami"`.

## What the install actually needs

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh
KEY='ssh-ed25519 AAAA… sofia-pc@DESKTOP-P7NSMTR'
touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
grep -qxF "$KEY" ~/.ssh/authorized_keys || echo "$KEY" >> ~/.ssh/authorized_keys
sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys
wc -c ~/.ssh/authorized_keys     # 106 bytes = exactly one ed25519 line + newline
ls -l ~/.ssh/authorized_keys     # -rw------- u0_a221
```

`grep -qxF` before `>>` makes a re-run idempotent — a double-append is silently harmless to sshd but
destroys your "how many keys are trusted?" answer.

## Termux usernames: there is no /etc/passwd

`grep -E 'termux|u0_a' $PREFIX/etc/passwd` returns nothing; `id` shows `uid=10221(u0_a221)`.
Termux's sshd does **not** look the login name up in a local account, so the name in the `ssh`
command is cosmetic. Verified end-to-end on the same key:

```
Accepted publickey for u0_a221 from 127.0.0.1 port 60156 ssh2: ED25519 SHA256:CViePN7…
Accepted publickey for termux  from 127.0.0.1 port 60170 ssh2: ED25519 SHA256:CViePN7…
```

Consequence: if the user's ready-made command says `termux@<ip>`, it works. Report that as a
verified fact instead of "actually the user is u0_a221" — the correction confuses rather than helps.

## Effective config, because sshd_config is a decoy

`$PREFIX/etc/ssh/sshd_config` on Termux is every line commented out plus
`Include …/sshd_config.d/*.conf` (and that directory is empty). Grepping it for
`PasswordAuthentication` proves nothing. Use the parser:

```bash
sshd -T 2>/dev/null | grep -Ei '^(port|listenaddress|pubkeyauthentication|passwordauthentication|permitrootlogin|allowtcpforwarding)'
# port 8022
# listenaddress 0.0.0.0:8022
# listenaddress [::]:8022
# pubkeyauthentication yes
# passwordauthentication yes
```

`listenaddress 0.0.0.0` is the line that proves the LAN (not just loopback) can reach 8022.

## Prove the key path from the phone — before the user tests from the PC

The PC is the slowest possible test loop (user must type, screenshot, report back). Prove the
daemon-side half locally instead:

```bash
mkdir -p ~/tmp && ssh-keygen -t ed25519 -N '' -f ~/tmp/uji_key -q
cat ~/tmp/uji_key.pub >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
# test BOTH names in one go; both must print OK
timeout 20 ssh -p 8022 -i ~/tmp/uji_key -o BatchMode=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null "$(whoami)"@127.0.0.1 "echo UJIAN_A_OK; whoami" 2>&1 | tail -4
timeout 20 ssh -p 8022 -i ~/tmp/uji_key -o BatchMode=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null termux@127.0.0.1 "echo UJIAN_B_OK; whoami" 2>&1 | tail -4
```

Then **remove exactly that key and prove it is gone**:

```bash
grep -vF "$(cut -d' ' -f1,2 ~/tmp/uji_key.pub)" ~/.ssh/authorized_keys > ~/tmp/ak
cp ~/tmp/ak ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys
rm -rf ~/tmp/uji_key ~/tmp/uji_key.pub ~/tmp/ak
cat ~/.ssh/authorized_keys; wc -c ~/.ssh/authorized_keys   # back to the user's single 106-byte line
```

Report the numbers (bytes, perms, `UJIAN_A_OK`/`UJIAN_B_OK`) — that is the evidence, not "dah siap".
What this proof does **not** cover, and must be said out loud: the PC-side passphrase, the PC's
private-key file, and the actual LAN route from the PC.

`/tmp` is not writable on Android Termux (`ssh-keygen` → `Saving key failed: Permission denied`).
Keep throwaway keys in `~/tmp`.

## Reading the runit-side sshd log

`sv status sshd` → `run: sshd: (pid N) …; run: log: (pid M) …`, and the log file is
`$PREFIX/var/log/sv/sshd/current` (svlogd also keeps `@4000…` rotated files in the same dir).

Line shape — note the svlogd prefix `DATE_TIME.MICROSECONDS` and the trailing `CR`:

```
2026-11-17_15:00:37.56741 Accepted publickey for termux from 127.0.0.1 port 60170 ssh2: ED25519 SHA256:CViePN7…
```

Parse it with `tr -d '\r'` first, then `sed -E 's/^([0-9-]+)_([0-9:]+)\.[0-9]+ /\1 \2  /'`, then awk.
After that rewrite the fields are:
`$1` date, `$2` time, `$3` Accepted, `$4` publickey, `$5` for, `$6` user, `$7` from, `$8` ip,
`$9` port, `$10` number, `$11` the `SHA256:` token (if sed renamed it).

Two parsing traps that each needed a fix in this session:

1. **Field index drift.** Using `$12` after a `kunci=SHA256:` rewrite printed an empty value, then
   `kunci=kunci=SHA256:…` once the index matched but the printf also prefixed `kunci=`. Decide once:
   either rename the token in sed *or* add the label in awk — never both.
2. **`grep -c` exits 1 on zero matches**, so `kali=$(grep -c … || echo 0)` yields `0\n0` and prints a
   second stray line. Use `kali=$(grep -c … | head -1); [ -z "$kali" ] && kali=0`.

## Fingerprint → key name mapping

`ssh-keygen -lf - <<< "$line"` accepts a key on stdin, so the audit can print, per key in
`authorized_keys`: type, `SHA256:` fingerprint, and how many `Accepted publickey` log lines mention
that fingerprint. That turns "someone logged in" into "**this PC's key** logged in, N times".

Useful sample values from the session: the user's `sofia-pc` key =
`SHA256:7kwtxJDJ844h5OxI7QOL0tL6fF1UzKTI7Q8ejOobmOA`; the throwaway test key =
`SHA256:CViePN7Rk3AEOa5wR9Wa5/Nkv/H/KGqI8NJVMEZAWKI` (0 uses after cleanup, by design).

## Honesty boundaries observed here

- `PasswordAuthentication yes` still stands after installing a key. Say it plainly
  ("sesiapa di WiFi sama boleh cuba teka") and offer to switch to key-only; do not flip it silently,
  because a wrong key on the PC would then lock the user out with no fallback.
- Adding **the same public key to GitHub** is a different job from installing it on the phone: it
  needs account-level auth (`gh auth login`, or a PAT with `admin:public_key`). If `gh auth status`
  says not logged in and no `GITHUB_TOKEN`/`GH_TOKEN` exists in the env file, report it as blocked
  and hand the user the `github.com/settings/ssh/new` paste (Title = host name, Key type =
  **Authentication key**). Never imply the key was registered when it was only written to
  `authorized_keys`.
