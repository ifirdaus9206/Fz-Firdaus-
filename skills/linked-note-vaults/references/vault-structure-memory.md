# Vault-structure reference (experience-memory vault)

Worked structure from a delivered vault (`~/vault`, 7 folders, 15 notes, 99 links, 0 broken).

## File set that satisfies the folder scheme

```
vault/
  README.md                                  hub: rules, folder table, role index, how-to
  00-Inbox/README.md
  10-Projek/README.md
  20-Ejen/README.md                          folder index (needed as a link target)
  20-Ejen/<role>.md                          x N roles
  30-Keputusan/README.md
  30-Keputusan/YYYY-MM-DD-short-title.md     the real decision note
  40-Pelajaran/README.md
  90-Arkib/README.md
  templates/nota-ejen.md
```

Add a `README.md` to any folder that will be a link target — otherwise `[[folder/README]]` dangles.
Adding folder notes everywhere is exactly what creates the bare-`[[README]]` ambiguity: use path links
and a hub alias, and disclose it.

## Hub README skeleton

```markdown
---
tajuk: Vault Memori Panjang
aliases: [Rumah, Vault]
jenis: hab
---

# Vault Memori Panjang — Rumah

## Peraturan utama
1. Nota = pengalaman (apa berlaku, apa dicuba, apa gagal).
2. Fakta pergi ke knowledge_base/ (harga, SOP, FAQ, API).
3. Setiap nota mesti ada pautan dua hala.
4. Satu nota, satu peristiwa/keputusan.
5. Nama fail keputusan: YYYY-MM-DD-tajuk-singkat.md.

Pautan pendek ke hab: [[Rumah]]  (alias unik; [[README]] mengelirukan bila setiap folder ada README.md)
```

## Role note skeleton (≥2 links, ~6 in practice)

```markdown
---
tajuk: Ops
ejen: ops
peranan: Proses, jadual, vendor, gangguan operasi.
status: aktif
dikemas: 2026-11-05
tag: [ejen, ops]
---

Balik ke [[README]] · Folder: [[20-Ejen/README|20-Ejen]] · Projek: [[10-Projek/README|10-Projek]]
· Templat: [[templates/nota-ejen|nota-ejen]]

## Pengalaman yang membentuk kerja saya
<one concrete incident, not a job description>

## Corak yang saya pegang
- <one-line rule distilled from that incident>

## Nota berkaitan
- [[40-Pelajaran/README|40-Pelajaran]]
- [[30-Keputusan/YYYY-MM-DD-tajuk|Keputusan ...]]
```

An experience log earns its keep only if the incident is specific (what was tried, what broke, the
number/24h/five-day detail). Generic "responsible for X" text is indistinguishable from a persona blurb.

## Decision note skeleton

Frontmatter `tajuk/tarikh/ejen/projek/tag/status`, then: Konteks → Keputusan (numbered) → Sebab →
Apa yang dikorbankan → Pautan → Semak semula (a date, and the question to re-ask).

The "what was sacrificed" section is what makes a decision note trustworthy later; without it the note
reads as justification written after the fact.

## Template frontmatter (YAML-safe)

```yaml
---
tarikh: "{{date:YYYY-MM-DD}}"
ejen: 
projek: 
tag: []
status: draf
---
```

Unquoted `{{date}}` breaks YAML parsing. Leave the value quoted so a template engine can substitute.

## Delivery report shape

1. Outcome bullets (folders, files, link counts, broken = 0).
2. File list.
3. Verbatim `find <vault> -type f | sort` output in a fenced block + `wc -l`.
4. Verbatim `find <vault> -type d | sort` + folder count.
5. Full link table: source file | `[[link]]` | resolved target | ADA/TIADA.
6. Unique-target tally (`X/X targets exist; 0 broken`).
7. Two-way proof, one line per role: forward link ADA and reverse link ADA.
8. Design/deviations notes: extra READMEs, alias mitigation, what was deliberately not touched.

Language: if the user writes Malay, deliver vault prose and report in Malay; keep technical tokens
(`wikilink`, `frontmatter`, `ADA`/`TIADA`) as-is.
