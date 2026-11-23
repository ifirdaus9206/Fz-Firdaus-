# "Menunggu jaringan" — the message never left the phone (client-side, not the bot)

Worked case: the owner insists *"dah hantar di telegram dia tulis menunggu jaringan"* and concludes
the bot is broken. The gateway had been restarted minutes earlier and was healthy.
**`menunggu jaringan` / "waiting for network" is drawn by the Telegram *client***: the message has
not been accepted by Telegram's servers at all, so there is nothing for the bot to receive.

## Triage order that separates the three failure directions

```bash
# 1. token + bot identity (read-only, never print the token)
curl -s "https://api.telegram.org/bot$TOKEN/getMe" | jq '.ok,.result.username'
# 2. is anything queued for the bot?
curl -s "https://api.telegram.org/bot$TOKEN/getWebhookInfo" \
  | jq '.result|{url,pending_update_count,last_error_message}'
# 3. what does the gateway itself say?
grep -n "inbound message" logs/gateway.log | tail -5
grep -nE "Connected to Telegram|UNCLEAN|connection failed" logs/gateway.log | tail -10
# 4. can this device reach the Bot API at all? (10 tries, count failures)
for i in $(seq 1 10); do curl -s -o /dev/null -m 6 -w "%{http_code} " https://api.telegram.org/; done
```

| Result | Meaning |
|---|---|
| `pending_update_count: 0`, `getUpdates?offset=-1` empty, and **no** new `inbound message` line | Nothing reached Telegram → **client/network on the phone**, not the bot. Do not present a gateway restart as the cure |
| `pending_update_count` growing while the gateway says connected | The poller is dead/stuck — restart it and re-check |
| `409 Conflict` from a manual `getUpdates` | A **second** poller exists (orphan gateway or another host) |
| Bot API ~9/10 OK from Termux while the Telegram app shows "waiting for network" | Bot path works; the *app's* MTProto route is stuck → toggle airplane mode / switch Wi-Fi↔data / force-stop the app |

`getUpdates?offset=-1` is only meaningful in one direction: an **empty queue while the gateway is
running** means the poller already drained it (or nothing arrived); it does **not** prove the bot is
blind. A `409` is the only positive proof that something else is polling.

## What to do (and what not to claim)

- Prove outbound separately: `hermes send -t telegram "…"` → `Sent to telegram home channel`. That
  proves token + allowlist + network **out**, never inbound.
- If the queue is empty and there is no inbound line, say plainly: *"mesej belum sampai ke pelayan
  Telegram — masalah di aplikasi/rangkaian telefon, bukan gerbang."* Then give **one** phone step
  (airplane-mode toggle, or Wi-Fi↔data switch) and wait for "siap".
- A restart of a healthy gateway is allowed, but report it as "gerbang dihidupkan semula sebagai
  langkah bersih" and keep the real finding in front.
- Fallback-IP noise (`Primary api.telegram.org connection failed … sticky fallback 149.154.166.110`)
  is normal on this device. Verify the fallback is reachable before blaming it:
  `curl -s -o /dev/null -w "%{http_code}" --resolve api.telegram.org:443:149.154.166.110 https://api.telegram.org/`
  → `302` means it is fine.
