# Cari kerja daripada e-mel (Freelancer.com notifications)

Trigger: *"untuk kerja kau cari di e-mel saya di freelance"* — the deliverable is a **ranked list of
open projects pulled out of notification emails**, not a summary of the emails.

## Where the data lives

Freelancer.com sends one digest per day:

```
Subjek: Firdaus, these <skill>, <skill>, ... projects and contests might interest you
Dari:   Freelancer <noreply@notifications.freelancer.com>
Badan:  ========\nProjects\n========\n
        <Tajuk projek>
        Budget: $765 - $1530 USD
        Skills: Article Writing, Blog Writing, ...
        Description:
        <satu baris panjang, dipotong ...>
        /projects/seo-writing/Teen-Patti-SEO-Content-Writer.html?utm_campaign=...
```

Every project block repeats that shape, so one digest yields 12–25 projects. Ten digests gave this
user 141 unique projects.

## Recipe

1. Read every `*.md` in the category folders, normalise CRLF first.
2. Keep only files whose `dari:` contains `freelancer`.
3. Split the body on the `Projects` heading, then regex each block:

```python
pola = re.compile(
    r"\n([^\n]{5,120})\nBudget: ([^\n]*)\n(?:Skills: ([^\n]*)\n)?"
    r"(?:Description:[^\n]*\n(.*?)\n)?(/(?:projects|contest)/[^\s?]+)",
    re.S,
)
# group(1)=tajuk 2=bajet 3=skil 4=description 5=pautan  ← pautan is group FIVE
```

4. Dedupe on the link path (digests overlap; the same project reappears for days).
5. Sort by the top of the budget range (`\$ ?([\d,]+)`), descending.
6. Write a table + per-project detail section, each row carrying the date and the source `.md` so a
   lead can be traced back to its email.

Working code for this account: `~/vault/email-inbox/kerja.py` →
`~/vault/email-inbox/2-KERJA/SENARAI-KERJA.md` (141 projek). Regenerate it from inside `auto.sh`, so
the list refreshes whenever new mail is filed.

## Traps hit while building it

- **Group numbering.** Adding the optional `Description` group shifted the link from group 4 to
  group 5; using 4 produced markdown links like `https://www.freelancer.comI'm looking for a
  designer…`. Count the groups before building the URL.
- **`\S+` swallows too much / too little.** Forbid `?` and whitespace in the link group
  (`[^\s?]+`) so UTM junk is trimmed and the description can't bleed in.
- **CRLF.** Re-reading the saved `.md` without normalising made `\n`-anchored patterns match the
  wrong spans.
- **Pick the right folder.** These digests classify as `2-KERJA` (rule keyword/domain), but the same
  sender can also land in `0-LAIN` when the log predates the label — dedupe across all four folders.

## Reporting

Show the top handful that match the user's own skills first (this user: graphic design, branding,
social media, logo, digital marketing), each with budget + direct link, then the file path and the
total count. Numbered options at the end (dedupe, re-rank by skill, open the list, filter by budget).
When the user says they will change their Freelancer profile, note that new digests simply arrive as
new `2-KERJA` files and the list rebuilds itself — no code change needed.
