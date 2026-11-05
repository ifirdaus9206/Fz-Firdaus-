# Common Identity File Patterns

This reference file contains patterns and examples for extracting information from identity documents.

## SOUL.md Pattern
Typical SOUL.md files contain:
```
You are Hermes Agent, an intelligent AI assistant created by Nous Research. You are helpful, knowledgeable, and direct. You assist users with a wide range of tasks including answering questions, writing and editing code, analyzing information, creative work, and executing actions via your tools. You communicate clearly, admit uncertainty when appropriate, and prioritize being genuinely useful over being verbose unless otherwise directed below. Be targeted and efficient in your exploration and investigations.
```

Extractable information:
- Agent identity statement
- Core capabilities and preferences
- Communication style hints (concise vs verbose)

## Identity Files Pattern (identity-full.md, ain-identity.md, etc.)
Common structure in identity files:

### YAML Frontmatter
```
---
id: Sofia
name: AINA
title: GLOBAL AI AGENT CHIEF ARCHITECT & MASTER STRATEGIST
description: Teragih berbilang pakar — gabungan 30 kepakaran elit beroperasi secara serentak untuk menyelesaikan tugas Bos Firdaus.
category: identity
created_at: 2026-08-28T09:00:00Z
version: 2.0.0
---
```

Extractable from frontmatter:
- `id`: Unique identifier
- `name`: Display name
- `title`: Professional role/title
- `description`: Summary of expertise/purpose
- `created_at`: When identity was established
- `version`: Identity document version

### Content Sections
Look for these common sections:
- **IDENTITI TERAS**: Core identity statements
- **SENARAI 30 PAKAR SERENTAK**: List of expertise areas
- **TERAS KEPUPAYAAN OPERASI**: Technical domains and standards
- **PROTOKOL EKSEKUSI**: Execution protocols and rules
- **MASTER COMMAND SYSTEM**: Available commands/capabilities

## Language Detection Patterns
To detect preferred language:
- Check if content is primarily in Bahasa Malaysia/Melayu
- Look for language markers in frontmatter or content
- Check for mixed language patterns
- Default to English if unclear

## Role-Based Communication Adaptation
Based on extracted titles/roles:
- **Chief Architect/Strategist**: Prefer strategic overview first, then technical details
- **Engineer/Developer**: May prefer technical depth and implementation details
- **Executive/Leader**: Focus on business impact, ROI, strategic alignment
- **Researcher/Analyst**: Value data, sources, methodology, and thoroughness

## Communication Preference Indicators
Look for explicit statements like:
- "be concise"
- "provide technical depth"
- "use formal language"
- "respond in [language]"
- "avoid jargon"
- "include examples"