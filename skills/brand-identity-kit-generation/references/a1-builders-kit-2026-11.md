# Worked example — A1 General Builders brand kit (2026-11)

Brief: licensed general contractor in Los Angeles County (kitchens, baths, foundations, ADUs, new
builds) needs a full identity: logo (3 colourways + icon), palette, typography, guidelines PDF,
business card, truck/yard/social mockups, source files. Direction: professional, simple, strong,
elegant-masculine, credible from a bathroom to a ground-up build.

## What preceded it (and why the operator had to rebuild)

A 4-agent console run (`brand-guardian → image-prompt-engineer + document-generator → reality-checker`,
waves) finished `done` but QA scored **0/8 GAGAL**: `document-generator` died with
`RALAT: LLM gagal: respons kosong (finish=length)`, the brand-guardian document was truncated
mid-SVG (`d="M0 0 H82 L`), palette/typography were flagged `placeholder`, and no file existed at all.
Lesson: **a pipeline verdict of `done` is not a deliverable**. Read the QA table, then produce the
files yourself from code rather than rerunning the same agents with the same token budget.

## Decision set that was left open by the agents

- Palette: Charcoal `#16181A`, Bone `#F2EFE9`, Steel `#4A4F55`, Bronze `#B87333`, plus a new
  **Bronze Deep `#8A5726`** because Bronze/Bone = 3.3:1 (large text only).
  Measured: Charcoal/Bone 15.5:1 AAA · Steel/Bone 7.2:1 AAA · Bronze Deep/Bone 5.3:1 AA ·
  Bronze/Charcoal 4.7:1 AA.
- Type: Archivo Black/Bold (headline) + Inter Regular/Medium/SemiBold (body), both OFL.
- Mark "FOUNDATION MARK": square tile 200 units, chamfer 36 (18%) on top-right + bottom-left,
  bronze wedge in the top-right corner, "A1" fit to 132 units wide, cap ≈ 100.
- Lockups: `primary` = icon + "GENERAL BUILDERS"; `wordmark` = "A1 GENERAL BUILDERS" text-only;
  `stacked` for signage. The repeated "A1 A1 GENERAL BUILDERS" version was rejected as redundant.
- Naming: `INC.` only on cards/contracts; yard sign and truck read "A1 GENERAL BUILDERS".

## Page list of the guidelines PDF (9)

cover · idea & voice (positioning, voice, name rules) · logo system (primary, wordmark, icon, stacked)
· clear space/min size/don'ts · colour + contrast + print notes · typography + scale table ·
business card (both sides + production notes) · applications (truck, yard, social, apparel) ·
files index + open items + how the files were made.

## Defects the render-and-look loop caught (all fixed)

1. Monogram 100-unit cap overflowed the tile and clipped at the canvas edge → fit by width.
2. Horizontal lockup: the tile's "A1" was drawn in the same ink as the tile (invisible) and the
   wordmark ran past the right edge → separate letter colour + 1% + 18 px padding.
3. Business card front: "INC." overlapped "BUILDERS" → moved `Inc.` into the legal line.
4. Card back: corner mark clipped by the trim → scale 0.62 and lift it above the footer.
5. Truck: duplicated big "A1" text beside the tile, wordmark hidden behind the cab, wheels floating →
   rebuilt body/cab/wheel geometry, icon in the dark panel only.
6. Yard sign: same duplicate "A1" + wordmark overflowing the board; CSLB line unreadable (Steel on
   Ink) → centred fit-text, bone at 75% opacity.
7. Cover: headline drawn twice (two overlapping text calls) → single centred `fit_text` pair.
8. Social 1080²: text started at x=0 and was clipped → centred `fit_text`, icon tile 420 px.

## Output size

113 files / 20 MB: 18 logo SVGs + PDFs + 27 PNGs, palette & type PDFs, 2 card PDFs, 3 mockups,
9-page A4 PDF (595×842 pt verified), `INVENTORY.json`, `README.md` (client, English),
`LAPORAN-QA.md` (Malay, gate table + evidence), zip ≈ 9.3 MB.

## Open items handed back to the user

CSLB licence number · phone · email/domain · owner name & title · tagline decision · insurance
wording. All marked `[TBC]` inside the artwork so nothing false ships.
