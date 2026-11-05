---
name: project-restructuring
description: Restructure/merge project dirs, legacy migration, verify.
category: software-development
tags: [restructuring, migration, reorganization, legacy, merge, verification]
---

# Project Restructuring & Migration

Use when: reorganizing a codebase/project directory structure, merging legacy folders into a new schema, migrating content between folder hierarchies, or consolidating duplicated structures.

## Trigger Conditions
- User asks to "restructure", "reorganize", "merge old and new structure", "migrate folders"
- Legacy project exists alongside new target structure
- Need to preserve history while adopting new architecture
- Multiple folder categories need mapping (agents, skills, workflows, knowledge, etc.)

## Workflow

### 1. Backup First
```bash
cp -r /path/to/project /path/to/project_backup
```
Always create a full backup before any destructive reorganization.

### 2. Analyze Both Structures
- List all directories and files in legacy structure
- List target structure (from user spec or best practices)
- Create mapping document: legacy folder to new folder(s)

### 3. Plan with Todo List
Use `todo` tool to track phases:
- Backup
- Create new directories
- Merge each category (identity, agents, skills, workflows, knowledge, logs, config, etc.)
- Migrate standalone files (memory, projects, tasks, system, tools)
- Create missing configs/docs
- Verify

### 4. Merge Strategy per Category

#### Identity/Config (files)
- Read all legacy files
- Write new consolidated files incorporating legacy content
- Archive legacy originals to `legacy/` subfolder

#### Agents/Skills/Workflows (folders with subfolders)
- Map N legacy items to M new categories
- Create new category folders with README.md documenting merged content
- Write registry.json mapping legacy to new
- Move legacy folders to `legacy/`

#### Knowledge/Logs (content folders)
- Move content to new locations
- Preserve file names and internal structure
- Remove empty source directories

#### Standalone root folders (memory, projects, tasks, system, tools)
- Move to appropriate new parent (knowledge/, logs/, config/, src/)
- Update any references

### 5. Create Missing Infrastructure
- Config files (agent.json, models.json, routing.json, permissions.json, capabilities.json)
- Database schema
- Deployment (Dockerfile, docker-compose.yml, deploy.yaml)
- Documentation (architecture.md, api.md, installation.md, operations.md)
- Root files (README.md, CHANGELOG.md, LICENSE)

### 6. Verification
Run automated checks:
- All JSON files valid
- All required directories exist
- All required files exist
- Legacy backups present
- Migrated content accessible at new paths

## Pitfalls
- **Forgetting backup** -- irreversible data loss risk
- **Incomplete mapping** -- legacy content lost in gaps between categories
- **Breaking references** -- paths in configs/code still point to old locations
- **Missing registry updates** -- agents/skills/workflows not discoverable
- **Empty folders left behind** -- cleanup with `rmdir` after migration
- **Overwriting new files** -- create new files first, then migrate content

## Verification Script Pattern
```python
# Check JSON validity, required paths, legacy backups, migrations
# Exit 0 = pass, Exit 1 = fail with details
```

## Example Mapping (ANIS Legacy to New)

| Legacy | New | Notes |
|--------|-----|-------|
| identity/{SOUL,identity,mission,principles,authority}.md | identity/{agent_identity,role,mission,principles}.md | Consolidated |
| agents/{10 folders} | agents/{orchestrator,researcher,architect,developer,reviewer}/ | 10 to 5 merge |
| skills/{ai,coding,business,trading,website,automation} | skills/{research,coding,analysis,database,automation}/ | 6 to 5 merge |
| workflows/{6 folders} | workflows/{planning,research,development,testing,deployment}/ | 6 to 5 merge |
| memory/* | knowledge/memory/ | Relocated |
| projects/* | knowledge/projects/ | Relocated |
| tasks/* | logs/tasks/ | Relocated |
| system/* | config/system/ | Relocated |
| tools/* | src/tools/ | Relocated |

## Related Skills
- `plan` -- for writing the restructuring plan
- `simplify-code` -- for cleaning up after restructuring
- `systematic-debugging` -- if restructuring breaks things

## Support Files
- `references/verify_restructure.py` -- Automated verification script for restructuring
- `references/anis_mapping.md` -- ANIS legacy-to-new mapping reference