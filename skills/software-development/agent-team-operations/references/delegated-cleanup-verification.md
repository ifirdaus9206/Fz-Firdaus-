# Verifying a delegated cleanup / "make it tidy" job

Companion to `references/interrupted-delegation-recovery.md`. That file covers a child that dies
mid-job. This one covers a child that **finishes, reports PASS, and is still wrong** — the normal
failure mode of cleanup work.

Observed 2026-11-06 (`deleg_266e0a92` + `deleg_8fd90c1b`, home `~/.hermes20`): a nightly-git-backup
build was declared complete with "0 secret files tracked", and it was telling the truth about
secrets while 15 derived files were still committed and one runtime database kept producing a
binary diff on every "silent" run.

## What PASS missed

| Claim in the child report | What the index actually held |
|---|---|
| "repo bersih" | `bin/tirith` (33 MB binary), `cron/executions.db`, 4× `agents.json.bak-*`, 7 curator archives |
| "senyap bila tiada perubahan" | `verification_evidence.db` changed size each run → a commit every night |
| "pengawal rahsia diuji" | true — but the probe file had been written *outside* the repo, so the test proved nothing |

Three different classes of wrong, all inside a confident summary. The rule "no pass without
evidence" applies to children exactly as it applies to agents on the roster.

## Lead-side sweep (run this yourself, always)

```bash
cd <repo-or-artefact-root>
git status --short                      # must be empty
git ls-files | wc -l                    # compare with the pre-job count
git ls-files | grep -E '<every pattern you asked to be removed>' || echo '(tiada)'
git ls-tree -r -l HEAD | sort -k4 -nr | head -10     # real large blobs still committed
git log -1 --stat --oneline             # what the last "silent" run actually committed
```

Then **run the automation twice in a row** and compare `git rev-parse HEAD`. A runtime DB that
churns only shows up on the second run. `out=$(bash script.sh); echo "exit=$? stdout=[$out]"`
proves silence better than reading the log.

Probe files must live inside the repo root. `~/probe.txt` is outside `~/.hermes20` and stages
nothing — the child's "guard tested" claim then means nothing.

## What to do with the leftovers

Dispatch a **narrow** second child, not a repeat of the broad brief:

- one pattern class per instruction (`bin/*`, `*.db`, `*.bak-*`, `skills/.curator_backups/`);
- reversible command only: `git rm --cached`, never `rm`;
- the exact verification lines it must paste back;
- an explicit note that the nightly script must still be silent afterwards.

The lead re-verifies and signs the verdict. Taking the pen here would break the "lead does not
execute" rule that this owner specifically checks.

## Children cannot answer approval prompts

A child that hits a command requiring interactive confirmation gets a refusal mid-run and the
rest of its brief is silently skipped — that is how the cleanup child stopped before its final
step. Write briefs so that no step can require approval:

- `git rm --cached` (index only) instead of `rm` (filesystem);
- no `sudo`, no package installs, no `git push` to a remote that does not exist yet;
- no history rewrite (`filter-branch`, `filter-repo`) — surface it as a decision for the owner;
- no mass delete, no `git clean`.

If a step genuinely needs approval, the lead runs it in the foreground with the owner present and
reports the result — it does not get pushed into a background child.
