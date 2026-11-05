# Background run-state integrity (the bugs that hang or silently lose a run)

Two distinct failure classes showed up in production of the console. Both come from more than one
writer touching `runs/<id>/run.json`.

Symptom A (hung run):

```
GET /api/agency/run/<id>   →  status: "running", waves: null, outputs: [], mtime 5 min old
GET /api/agency/guard      →  {"active": ["<id>"], ...}      # slot never released
server.log                 →  Exception in thread run-<id>:
                              json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
                              at  run = load(run_id)
```

Root cause: the POST handler did `save(run)` (plain `Path.write_text`) while the freshly spawned
worker thread called `load(run_id)` on the same `run.json`. The reader caught the file mid-write
(truncated/empty), `json.loads` raised **before** the thread's own `try/finally`, so:

1. the thread died silently,
2. the run stayed `running` forever,
3. `release_slot()` never ran → the spend guard locked out every later run,
4. the UI kept showing "EKSEKUSI 0/N" with no error.

Symptom B (lost operator input): a note posted to a *running* run (`POST /api/agency/run/{id}/note`)
returned `200` and `inbox: 1`, yet minutes later the finished `run.json` had `inbox: 0` and the
downstream agent never saw the correction. Cause: the worker thread holds its own copy of the run
dict and saves it on every output; its stale `inbox: []` overwrote the note written by the endpoint.

Never let a worker and its spawner (or an operator endpoint) touch the same JSON file without the
six fixes below.

## Fix 1 — atomic writes

```python
def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)          # readers only ever see a complete file
```

Use it for every artifact (`run.json`, `plan.json`, per-agent output). `os.replace` is atomic on the
same filesystem.

## Fix 2 — tolerant read

```python
def load(run_id: str) -> dict | None:
    f = RUNS / run_id / "run.json"
    for i in range(4):
        if not f.exists():
            return None
        try:
            return json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            time.sleep(0.05 * (i + 1))     # write in flight — retry
    return None                            # never raise into a worker thread
```

## Fix 3 — don't re-read what the spawner already has

Write the status **first**, then hand the in-memory dict to the thread:

```python
run["status"] = "running"
save(run)                                  # before spawn, not after
acquire_slot(run_id)
try:
    threading.Thread(target=_execute, args=(run_id, run), daemon=True).start()
except Exception:
    release_slot(run_id); run["status"] = "failed"; save(run); raise
```

`def _execute(run_id, preloaded=None): run = preloaded or load(run_id)`.
The old order (spawn → then `save(status=running)`) also risked overwriting a fast worker's terminal
state.

## Fix 4 — release the slot in `finally`, and reconcile orphans

```python
def _execute(run_id, preloaded=None):
    run = preloaded or load(run_id)
    if not run:
        release_slot(run_id); return
    try:
        ...
    except Exception as e:
        run["status"] = "failed"; run["error"] = scrub(f"{e}")
    finally:
        release_slot(run_id)
    save(run)
```

Even with that, a hard crash can still orphan a slot, so `guard_status()` must self-heal:

```python
for rid in list(_GUARD["active"]):
    r = load(rid)
    if not r or r.get("status") not in ("running", "synthesizing"):
        _GUARD["active"].discard(rid)
```

## Fix 5 — reconcile stale runs at startup

```python
def recover_stale(max_age_s: int = 1800) -> list[str]:
    # any run whose run.json is older than max_age_s and still running/synthesizing/planning
    # → status="failed", error="terhenti (stale) — server dimulakan semula atau thread mati"
```

Call it at import/startup with a tighter window (900 s) so a restart cleans the previous process's
casualties. It is the only way "running" ever clears for a run whose thread is gone.

## Fix 6 — operator writes must merge, not replace (symptom B)

One `RLock` per run id, an explicit append helper, and a `save()` that never shrinks lists owned by
another writer:

```python
_RUN_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()

def _lock(run_id):
    with _LOCKS_GUARD:
        return _RUN_LOCKS.setdefault(run_id, threading.RLock())

def save(run, merge=True):
    with _lock(run["id"]):
        if merge:
            disk = load(run["id"])            # load() is lock-free; RLock is re-entrant
            if disk:
                for k in ("inbox", "attachments"):   # append-only lists owned by endpoints
                    if len(disk.get(k) or []) > len(run.get(k) or []):
                        run[k] = disk[k]
        _atomic_write(... run.json ...)

def append_inbox(run_id, entry, attachments=None):
    with _lock(run_id):
        run = load(run_id)
        if not run:
            return None
        run.setdefault("inbox", []).append(entry)
        if attachments:
            run["attachments"] = (run.get("attachments") or []) + attachments
        save(run, merge=False)                # we already hold the freshest copy
        return run
```

Rule of thumb: fields written **only** by the worker (`status`, `wave`, `outputs`, `final`, `usage`)
may be replaced wholesale; fields written by **operator endpoints while the run is live** (`inbox`,
`attachments`, notes) must be merged defensively.

Then read them fresh at each wave so a mid-run note reaches the next agent:

```python
fresh = load(run_id) or {}
extra_atts = fresh.get("attachments") or run.get("attachments") or []
notes = [n.get("text") if isinstance(n, dict) else str(n) for n in (fresh.get("inbox") or [])]
run_agent(ag, persona, instruction, upstream, extra_atts, notes)
```

The agent prompt gains `NOTA TERKINI DARIPADA KETUA/PENGGUNA (ambil kira, jangan abai): - …` and an
attachment block. Verified end-to-end: note posted 2 s after start, run finished with `inbox: 1`,
and the wave-2 reviewer's output contained the note's keywords ("emoji", "pembetulan").

## Isolation behaviour worth keeping

One failing agent must not sink the run: record `{slug, status:"error", text:"RALAT: <why>", ms}` and
continue; the synthesis prompt then sees the gap and can mark the missing work. Real example:
`pricing-analyst` failed (truncated output, `finish_reason=length`) while `trend-researcher` and
`financial-analyst` succeeded; Ketua's verdict explicitly said the pricing section was unverified
and audited the missing input. Surface agent errors with a red tag, never silently drop them.

## Regression checks

- Start a run, then `GET /api/live/state` repeatedly: status must leave `running` and
  `active_agents` must drain to `[]`.
- `GET /api/agency/guard` → `active: []` after completion.
- `grep -ci traceback server.log` → `0`.
- Kill the server mid-run on purpose once: after restart the run must be `failed` (stale), not stuck
  `running`.
- **Multi-writer check**: start a run, immediately `POST /run/{id}/note`, wait for `done`, then
  assert `len(run["inbox"]) == 1` *and* grep the downstream agent's output for a word from the note.
