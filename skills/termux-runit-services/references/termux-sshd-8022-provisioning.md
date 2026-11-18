# SSH into the phone from a PC — Termux sshd on port 8022

Goal: the user's PC can `ssh` into Termux for real file/terminal work (not just view the web
dashboard). Everything below was probed on the Redmi/Termux device; each command is the one that
actually produced evidence.

## 0. What the default install looks like

| Fact | How to confirm |
|---|---|
| `openssh` installed, `sshd` at `$PREFIX/bin/sshd` | `command -v sshd; dpkg -s openssh \| grep -E '^(Status\|Version)'` |
| `sshd` runit service **exists but is disabled** | `sv status sshd` → `down: sshd`; `ls $PREFIX/var/service/sshd/` contains a `down` file |
| Termux default port = **8022**, bound **0.0.0.0** (LAN-reachable) | log line `Server listening on 0.0.0.0 port 8022.` |
| Account has **no password** → `password` auth is advertised but unusable | `grep '^'"$(whoami)" $PREFIX/etc/shadow` → empty |

`sshd_config` on Termux is nearly empty (`Include …/sshd_config.d/*.conf`, `AuthorizedKeysFile`,
`sftp` subsystem) — no `PasswordAuthentication no`, so OpenSSH's default `yes` applies and
password auth is offered automatically.

## 1. Enable the service (the `down` file is the whole blocker)

```bash
rm -f "$PREFIX/var/service/sshd/down"
sv up sshd
sv status sshd            # run: sshd: (pid N) Ns
```

Add persistence — the existing boot script must also bring it up:

```bash
# in ~/.termux/boot/10-*.sh, next to the other sv up lines
sv up "$PREFIX/var/service/sshd" 2>/dev/null || true
```

## 2. Verify the port WITHOUT ss/netstat

`ss -ltn` and `netstat -ltn` return nothing useful in Termux — do not conclude "closed" from them.

```bash
# (a) real TCP probe
python3 - <<'EOF'
import socket
for p in (8022, 22):
    s = socket.socket(); s.settimeout(3)
    try: s.connect(("127.0.0.1", p)); print(f"port {p}: BUKA")
    except Exception as e: print(f"port {p}: TUTUP ({e.__class__.__name__})")
    finally: s.close()
EOF

# (b) authoritative daemon log
tail -5 "$PREFIX/var/log/sv/sshd/current"
```

## 3. Prove the daemon and see which auth methods are live

```bash
ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -p 8022 "$(whoami)"@127.0.0.1 true
# → "Permission denied (publickey,password,keyboard-interactive)"
```

That refusal is a **pass**: the daemon answered and it tells you exactly which methods are enabled.
If `password` is missing from the list, password login is off in config; if the connection is
refused, the service/port is the problem, not credentials.

## 4a. Preferred: key auth (no password to share)

1. Ask the user for the PC's **public** key only (`cat ~/.ssh/id_ed25519.pub` on the PC).
2. Append it: `mkdir -p ~/.ssh && chmod 700 ~/.ssh; echo "<pubkey>" >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys`
3. Re-run the probe in §3 without `BatchMode` — must print nothing and exit 0.
4. PC side: `ssh -p 8022 <user>@<lan-ip>`.
   Never ask for, transfer, or store the PC's private key.

## 4b. Fallback: set a password — `passwd` is interactive, drive it over a pty

Termux `passwd` has **no non-interactive mode** (`passwd -d` only locks/disables). A plain
`terminal("passwd")` blocks. Correct shape: start it as a background **pty**, then submit twice.

```
terminal(command="passwd", tty/pty=true, background=true)   → session_id
process(action="submit", session_id=..., data="<pw>")
process(action="submit", session_id=..., data="<pw>")       → then process(action="poll")
```

Generate the password to a **`chmod 600` file first**, never inline in a command string that gets
echoed into the transcript:

```bash
python3 -c "import secrets,string;a=string.ascii_letters+string.digits;print(''.join(secrets.choice(a) for _ in range(14)))" \
  > ~/.hermes20/secrets/.ssh_pw.tmp && chmod 600 ~/.hermes20/secrets/.ssh_pw.tmp
```

Then record it as `user:` / `password:` / `port: 8022` / `host: <lan-ip>` in
`~/.hermes20/secrets/ssh_login.txt` (600), and point the user at the path or the mail channel —
**never paste the value into the chat**, the transcript is persisted in the session DB.

Pitfall seen live: the pty prompt produced a login banner (`Created By HTR-TECH … Welcome …`) before
the `New password:` prompt, so a fixed-order "submit twice" can race the banner. Poll the session
after starting it, wait for the actual `New password:` text, then submit.

## 5. LAN IP

`ip -4 addr` may print nothing on this device. Reliable read:

```bash
python3 -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));print(s.getsockname()[0])"
```

The DHCP address changes; re-read it instead of reusing an old one, and never hand out a
`100.x.y.z` (CGNAT) address.

## 6. Security posture to state plainly

Binding `0.0.0.0:8022` means **anyone on the same WiFi can attempt a login**. That is acceptable on
a trusted home LAN; say so, keep the password long, and prefer key auth. Do not open the port
through the public tunnel unless the user explicitly asks.
