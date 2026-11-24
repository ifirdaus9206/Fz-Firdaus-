# Worked case — "kau ada baca mesej Aina dan Irfan?"

**Question asked (2026-11-25):** *"Sebelum aku bagi jawapan. Tadi kau ada baca mesej aina dan
Irfan aku tegak ada jalan tadi"* — the owner believed two other people had messaged the bot.

**Answer given:** no. Neither name appeared as a sender, and the evidence took four commands.

## Evidence collected (all read-only)

```bash
cd ~/.hermes20
grep -o 'chat=[0-9-]*' logs/gateway.log | sort -u     # → chat=1312929583   (one only)
grep -o 'user=[^ ]*'  logs/gateway.log | sort -u     # → user=firdaus      (one only)
grep -c 'inbound message' logs/gateway.log           # → 296
grep -ril 'irfan' --include='*.md' --include='*.json' --include='*.yaml' .
```

| Check | Result |
|---|---|
| distinct chats in `gateway.log` | **1** (`1312929583`) |
| distinct users | **1** (`firdaus`) |
| inbound messages counted | **296** — all from that one chat |
| `channel_directory.json` | only `firdaus ismail` + its own topics |
| `session_search "Irfan"` | **0 sessions** |
| `grep -ril irfan` across the home | **0 files** |
| `grep -ril aina` | only old project/archive paths, never a chat |

## The name that looked like a person

"Aina" existed in three places, none of them a sender:

1. `TELEGRAM_HOME_CHANNEL_NAME=Aina` in `.env`, whose `TELEGRAM_HOME_CHANNEL` id is
   `1312929583` — i.e. **the owner's own DM with this bot**. The bot's display name is "Aina".
2. `~/.AINA` — a retired home directory, deleted in an earlier pass.
3. `arkib-ketua/projek-ultimate-aina/` — an archived project named after the same persona.

So the owner was remembering the bot's own label and an old project folder, not a conversation.

## Extra check worth doing when a second bot is suspected

```bash
for p in ~/.hermes20/profiles/*/; do
  printf '%-28s telegram_env=%s\n' "$p" "$(grep -c TELEGRAM "$p/.env" 2>/dev/null)"
done
sv status hermes-gateway
```

Six profiles carried `TELEGRAM*` keys but **no gateway was running for them** — one token, one bot,
one inbound stream. Keys present ≠ bot live; only `sv status` plus an `inbound message` line proves a
second bot is receiving anything.

## Reporting shape that landed well

1. Lead with the verdict in one line: "Tidak — sebab tiada mesej sedemikian sampai kepada aku."
2. Evidence table (check · result) with the raw counts.
3. A short "jadi 'Aina' itu apa?" section mapping each name to what it actually is.
4. The limits stated plainly: other platforms (WhatsApp/SMS) and other bot tokens are invisible
   here; a forwarded message is the only way in.
5. Close with numbered options (forward the message / continue the pending setup / check whether a
   second bot should be enabled / stop).

Never answer this class of question from memory or from the current conversation alone — a wrong
"ya, saya baca" destroys trust faster than any outage.
