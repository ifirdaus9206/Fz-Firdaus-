# Reconciling a Ketua verdict with the run archive (and handing the run to chat)

A finished run leaves `runs/<id>/{run.json, plan.json, out_<slug>.md, final.md}`. `final.md` is the
Ketua synthesis — the thing the user reads and quotes. It is **generated from truncated inputs**, so
it can be confidently wrong. Treat it as a claim to audit, never as the record.

## 1. Why the verdict lies (measured, 2026-11)

`agency_runner.py`:

| Line | Slice | Effect |
|---|---|---|
| 422 | `(u.get('text') or '')[:7000]` | upstream agent output cut before the next agent sees it |
| 491 | `(o.get("text") or "")[:9000]` | agent output cut before the synthesis sees it |

A 3-agent brand run produced:

| Agent | Stored length | Real ending | Ketua said |
|---|---|---|---|
| brand-guardian | 8,298 | `STATUS: NEEDS_WORK` + `SERAHAN:` | "terpotong pada §7" (it saw the 7k slice) |
| whimsy-injector | 11,215 | §7 complete + `STATUS: DONE` | "terputus pada §5 selepas 'nampak '" |
| image-prompt-engineer | 14,400 | §8 complete + `STATUS: DONE`, BB-01…BB-18 | "terputus mid BB-02, BB-03–BB-18 tiada" |

Two QA gates (`qa_system`, `prompt_consistency_system`) were failed on that basis. Both were fine.

## 2. Forensic check — 30 seconds, no guessing

```python
import json, os
base = os.path.expanduser("~/hermes-console/runs/<id>")
run = json.load(open(os.path.join(base, "run.json")))
for o in run["outputs"]:
    t = o["text"]
    print(o["slug"], len(t), "| 9000-tail:", repr(t[8940:9000]), "| 7000-tail:", repr(t[6940:7000]))
```

If a tail ends exactly where the verdict says the text stopped (`"(nampak "`, `"| **BB-02** Buzz
Terbang | \`flat vector "`), the truncation is the runner's, not the agent's. Also compare
`len(o["text"])` with `len(open(out_<slug>.md).read())` — they should match; a short `out_*.md` is a
genuine truncation.

Then re-derive the gate table: which gates failed *only* because of the slice (→ LULUS), which fail on
real missing content (→ keep GAGAL). The overall status can stay `NEEDS_WORK` while the reasons change
completely — say that explicitly instead of quietly reusing the old verdict.

## 3. Fix at the source (applied — `agency_runner.py`, 2026-11-04)

Never slice silently. Raise the caps **and** make any residual cut self-announcing, so synthesis can
no longer mistake a data-transfer limit for an incomplete agent:

```python
MAX_TOKENS = 3200
TIMEOUT = 240

# dulu 7000 (ejen→ejen) / 9000 (ejen→Ketua): output panjang dipotong SENYAP
MAX_UPSTREAM_CHARS = 24000
MAX_SYNTH_CHARS = 24000


def clip(text: str, cap: int, label: str = "teks") -> str:
    """Potong pada `cap`, TAPI tandakan dengan jelas bila dipotong."""
    t = text or ""
    if len(t) <= cap:
        return t
    return (t[:cap]
            + f"\n\n[NOTA SISTEM: {label} dipotong pada {cap} daripada {len(t)} aksara "
              f"kerana had konteks. Ini had pemindahan data, BUKAN kerja ejen yang tidak "
              f"lengkap — jangan simpulkan 'output terputus' daripada nota ini.]")
```

Wire it in both places instead of the slices: `run_agent()`'s upstream block
(`clip(u.get('text') or '', MAX_UPSTREAM_CHARS, 'output ' + u['slug'])`) and `synthesize()`'s
per-output block (`body = clip(o.get("text") or "", MAX_SYNTH_CHARS, "output " + o["slug"])`).

Verify the change **without** spending a run:

```bash
cd ~/hermes-console && python -c "
import agency_runner as a
print(a.MAX_UPSTREAM_CHARS, a.MAX_SYNTH_CHARS)
print('lulus penuh:', len(a.clip('x'*14400, a.MAX_SYNTH_CHARS)) == 14400)
o=a.clip('y'*30000, a.MAX_UPSTREAM_CHARS); print('penanda:', 'NOTA SISTEM' in o)"
grep -n "MAX_UPSTREAM_CHARS\|MAX_SYNTH_CHARS\|\[:7000\]\|\[:9000\]" agency_runner.py   # no slices left
```

Then **restart the instance** — Python reads the module at boot, so an edited runner has no effect
until 8787 is cycled (leave 8790/trading alone):

```bash
python tools/stop_server.py --port 8787 && sleep 1 && bash tools/start_all.sh
curl -s http://127.0.0.1:8787/api/ping     # {"ok":true,...}
```

Record the numbers in the project README ("Had teks antara ejen") so the next session does not
re-diagnose the same false QA failures. Confirm end-to-end on the next real run: `final.md` must not
claim "terpotong" where `out_<slug>.md` is complete.

Note the remaining independent truncation risk: the per-agent `max_tokens=3200` can cut an agent's own
prose mid-sentence. That *is* a real truncation — check `finish_reason`, and raise to ~4096 before
blaming the agent.

## 4. Handoff package (one format per folder)

```
runs/<id>/PAKEJ/
  00_BACA_DULU.md            # what the run was, status, fail→reader matrix, real gaps, work order
  01_PELAN_KETUA.md          # plan.json rendered as markdown (faham, andaian, ejen table, langkah, risiko, kos)
  02_<AGENT>.md …            # out_<slug>.md copied verbatim, numbered in execution order
  NN_KEPUTUSAN_KETUA.md      # final.md verbatim, unedited
  NN_SEMAKAN_BUKTI.md        # reconciliation: false claims + evidence + corrected gate table
```

Rules that made it usable on a phone:

- **Numbered filenames** carry the reading order; the matrix in `00_BACA_DULU.md` says who reads what.
- **Never edit `final.md`** in the package — the correction lives in its own file so the user can see
  both the verdict and the rebuttal.
- Chat body = the verdict + the correction summary + the real gap list; the full documents ride as
  `MEDIA:` attachments. Do not paste 40 KB of agent prose into chat.
- End with 3–4 numbered options (fix the runner / close the real gaps / re-run / dump full text in
  chat) — this user answers by number.
- `plan.json` → markdown needs the `usage` block too (prompt/completion/total/cost); cost is part of
  the record of what the run consumed.

## 5. Closing a run on request (\"setop dan padam kerja ini\")

When the client goes quiet and the user says stop and delete:

1. **Prove nothing is running** before deleting: `ps -ef | grep -E \"agency|runner\" | grep -v grep`
   → expect nothing (a finished run has no process; the artifact is just files).
2. **Find every reference first** with ripgrep, not `grep -rl` — `grep -rl <id> ~/.hermes20` hit the
   180 s tool timeout on this device; `search_files(pattern=<id>, path=~/hermes-console)` returned the
   4 hits instantly. References usually live only inside `runs/<id>/` (a console run is a directory
   entry, not a DB row, so deleting the folder removes it from the archive list).
3. `rm -rf runs/<id>` → verify with `ls -d` (expect \"no such file\") and re-list `runs/` to show the
   new archive tail.
4. **Say what cannot be deleted:** the copies already sent as `MEDIA:` stay in the Telegram chat
   history; the machine copy is gone. One honest line beats implying a full retraction.
5. Record the reason for closure in the reply (e.g. \"pelanggan tak beri maklumat lanjut\") and offer
   numbered follow-ups (close for good / still fix the bug / prune old runs / keep reusable assets).
