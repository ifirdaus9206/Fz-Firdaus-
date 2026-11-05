# Python module convention for `~/.hermes20/system/*.md`

The user's current authoring format: each system file is **markdown wrapper + one fenced
python block** that is a real, importable module. Confirmed on `agent_factory` (v2.0) and
`role_generator` (v2.0) — user instruction: *"ikut code arahan python setiap satu"*.

## Shape

```
# system/<name>.md          <- markdown header: path, title, owner line, STATUS line
```python
"""<name> — one-line role."""
SYSTEM_NAME / SYSTEM_VERSION ("2.0.0") / UPSTREAM / HERMES_VERSION / LANGUAGE ("ms")
SYSTEM_PROMPT = r"""<user prompt VERBATIM>"""
<UPPER_TUPLE> ...   one tuple[str, ...] per list in the prompt
@dataclass(slots=True) class <Thing>Spec   one attr per output field
def validate_<thing>_spec(spec) -> list[str]   returns errors, [] == pass
if __name__ == "__main__": print name/version/prompt
```
```

## Content fidelity rule

The user supplies the prompt; the agent supplies only the *plumbing*. Reproduce their text
verbatim. The only edits allowed are cosmetic:

- `Langkah 1:` / `Name` / `✓ …` runs that arrive squashed on one line → split onto their own
  lines, and restore `1.` `2.` numbering / `-` bullets / one `✓` per line.
- Never reword, expand, translate, or "improve" a sentence. No fields added that the prompt
  did not list.

## Schema mapping per module (as built)

| Module | Prompt lists | Python schema |
|---|---|---|
| `agent_factory` | 12 agent fields, 7 analysis fields, 5 agent categories, 6 output dirs, 6 completion ✓ | `AGENT_SPEC_FIELDS`, `ANALYSIS_FIELDS`, `AGENT_CATEGORIES`, `PROJECT_OUTPUT_DIRS`, `COMPLETION_CHECKS`, `AgentSpec`, `validate_agent_spec`, `is_project_complete` |
| `role_generator` | 8 role fields, 5 creation steps, 4 quality standards, 3 adaptation actions | `ROLE_FIELDS`, `CREATION_STEPS`, `QUALITY_STANDARDS`, `ADAPTATION_ACTIONS`, `RoleSpec`, `validate_role_spec`, `detect_overlap` |

Design extras worth repeating: `detect_overlap()` enforces the prompt's "tidak bertindih"
standard; `is_project_complete()` enforces "6 ✓ must all be true".

## Verification transcript (real, 27 Okt)

```
COMPILE_OK
IMPORT_OK agent_factory 2.0.0
PROMPT_LEN 2027
AGENT_FIELDS 12
ERRORS_ON_EMPTY 11
COMPLETE_ALL_TRUE True
COMPLETE_MISSING_ONE False
```

role_generator: `PROMPT_LEN 811`, `ROLE_FIELDS 8 STEPS 5 QUALITY 4`,
`ERRORS_ON_OK []`, `OVERLAP [('Data Engineer', 'QA Engineer')]`.

Use `scripts/verify_prompt_module.py <file.md>` to reproduce this instead of hand-typing
`python3 -c` one-liners.

## Loader trap

```python
spec = importlib.util.spec_from_file_location("af", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)        # AttributeError: 'NoneType' object has no attribute '__dict__'
```
`@dataclass(slots=True)` inspects `sys.modules[cls.__module__]`, which is `None` when the
module was never registered. Fix: `runpy.run_path(path, run_name="af")`, or register first
(`sys.modules["af"] = mod`). `py_compile` alone passes — this trap only fires at import.
