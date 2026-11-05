# Is that IP this phone, or the other phone? (unrooted Termux)

**Read this first whenever the user pastes an IP / IPv6 / MAC and asks "tambah peranti" or
"test boleh atau tak".** A ping that answers is not evidence: this phone answering its own
address looks identical to a successful pairing.

Two pitfalls this session burned time on:

- **`pkill -f "<pattern>"` kills the shell that runs it** when the pattern is inside the invoking
  command — `pkill -f "http.server 9123"` ended the whole command with SIGTERM (exit `-15`),
  silently dropping the rest of the script. Kill via the `process` tool session id, a pidfile, or
  `pkill -f "[h]ttp.server 9123"`. Do not put the pattern you are about to kill in your own
  command line.
- **A background `python3 -m http.server … &` inside a foreground tool call may never start.**
  Use `terminal(background=true)` and then `curl` in a separate call.

Session evidence, 2026-11-03. User pasted what they believed were a second phone's details —
MAC `40:08:77:64:9a:92`, `192.168.0.41`, link-local `fe80::8c66:8ff:fe4f:cf2a`, plus two
`2001:e68:...` global addresses — and asked "test dan simpan".

## What actually happened

`ping 192.168.0.41` answered in **0.088 ms** and `ping6 fe80::8c66:8ff:fe4f:cf2a%wlan0`
answered in **0.094 ms**. Both looked like a win. They were not: `ifconfig wlan0` on the device
running Termux shows `inet 192.168.0.41/24`. The address *was this phone*.

## The decisive test (no root needed)

A TCP listener can prove identity because a remote host cannot be served by a local process:

```bash
# 1. start a listener on every interface (use terminal(background=true), not `&`)
python3 -m http.server 9123 --bind 0.0.0.0

# 2. hit both addresses
curl -s -m3 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9123/   # 404
curl -s -m3 -o /dev/null -w '%{http_code}\n' http://192.168.0.41:9123/ # 404  <-- same server

# 3. read the access log
#   127.0.0.1 - - [..] "GET / HTTP/1.1" 404 -
#   192.168.0.41 - - [..] "GET / HTTP/1.1" 404 -      <-- target logged as CLIENT of our own process
```

`<ip>` logged as a client of the process we just started ⇒ `<ip>` is this device. If it were a
separate phone, the request could not have reached this listener at all.

Ping RTT is a weaker but free signal: ~0.1 ms and TTL 64 = yourself; a real Wi-Fi peer is
typically 1–10 ms.

## What cannot be verified without root

```bash
cat /proc/net/arp     # Permission denied
ip neigh              # Cannot bind netlink socket: Permission denied
```

So a MAC address the user supplies **cannot** be confirmed from Termux. Do not stamp it
"disahkan"; say it is unverifiable here and use IP:port + 6-digit pairing code as the real proof.

## Finding the other phone when only a MAC is known

```bash
seq 1 254 | xargs -P 32 -I{} sh -c 'ping -c1 -W1 192.168.0.{} >/dev/null 2>&1 && echo 192.168.0.{}' \
  | sort -t. -k4 -n
# -> .1 (router), .12, .41 (this phone), .220, .237
```

Then probe ADB ports on each live host:

```bash
for p in 5555 5037; do
  timeout 2 bash -c "</dev/tcp/<ip>/$p" >/dev/null 2>&1 && echo "$p BUKA" || echo "$p tutup"
done
```

All closed ⇒ wireless debugging is off on those devices and no pairing is possible yet.

## Reporting shape that worked

Say it plainly, with the table of evidence, then the single physical step the user must do:

> `192.168.0.41` dan `fe80::...` itu ialah telefon ini sendiri, bukan telefon isteri.
> Untuk tambah telefon dia: Seting → Perihal telefon → ketik "Nombor binaan" 7× →
> Pilihan pembangun → Nyahpepijat wayarles → "Pasangkan peranti dengan kod" →
> hantar IP:port + kod 6 digit.

The user asked "boleh atau tak"; the honest answer was "belum" plus the one step that makes it
possible. Counting a self-ping as success would have been the failure mode here.
