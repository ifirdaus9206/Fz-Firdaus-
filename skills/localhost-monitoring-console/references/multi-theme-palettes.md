# Multiple named themes on top of a light/dark toggle

Companion to `light-theme-full-sweep.md`. That file gets you **one** readable light theme. This
one is the follow-on request: *"tambah banyak tema — biru muda, krim, kelabu terang"*.

## Why a naive `body.theme-blue { --bg: … }` does nothing

After a full light sweep, `theme.css` is full of **hardcoded** values, not variables:

```css
body.light .panel{background:#ffffff!important}
body.light .side{background:linear-gradient(180deg,#ffffff,#f7f7f8)!important}
body.light .chip-live{background:#ffffff!important;color:#3f3f46!important}
```

Those `!important` literals beat any variable you redefine later. Redefining `--bg`/`--panel` in a
theme class changes only the few surfaces that still read the variable, so the user picks "krim"
and sees a white page with one cream border — "tak jadi".

Two options, pick by size of the sweep:

1. **Small app (< ~200 lines of light layer):** convert the light literals to `var(--panel)` etc.
   so one palette class re-colours everything.
2. **Large sweep (measured here: 69 light selectors):** leave the light layer alone and give each
   palette its **own explicit override block** for the surfaces that matter. Verbose, but it is
   additive, cannot regress the readable light theme, and takes one edit.

## Palette block shape that worked (5 palettes + dark)

```css
/* setiap tema: token + override permukaan utama */
body.theme-cream{--bg:#fdf6e3;--panel:#fffaf0;--panel2:#f7ecd7;--line:#e6d9bd;
  --ink:#3b2f1f;--dim:#8a7a5f;--acc:#b45309;--oc-text:#3b2f1f}
body.theme-blue {--bg:#eef6ff;--panel:#ffffff;--panel2:#f0f7ff;--line:#cfe3f7;
  --ink:#12314d;--dim:#5c7f9c;--acc:#1d6fd0;--oc-text:#12314d}
body.theme-grey {--bg:#f2f2f4;--panel:#ffffff;--panel2:#f4f4f6;--line:#dcdce2;
  --ink:#26262b;--dim:#71717a;--acc:#3f3f46;--oc-text:#26262b}
body.theme-mint {--bg:#effaf4;--panel:#ffffff;--panel2:#f1fbf6;--line:#cbe9db;
  --ink:#14352a;--dim:#5f8878;--acc:#0f9b63;--oc-text:#14352a}

/* satu blok berkumpulan untuk SEMUA tema — bukan 6 blok berasingan */
body.theme-cream,body.theme-blue,body.theme-grey,body.theme-mint{background:var(--bg)!important;color:var(--ink)!important}
body.theme-cream .panel,body.theme-blue .panel,body.theme-grey .panel,body.theme-mint .panel{background:var(--panel)!important;border-color:var(--line)!important}
body.theme-cream .side,body.theme-blue .side,body.theme-grey .side,body.theme-mint .side{background:var(--panel)!important}
body.theme-cream .chip-live,body.theme-blue .chip-live,body.theme-grey .chip-live,body.theme-mint .chip-live{background:var(--panel)!important;border-color:var(--line)!important;color:var(--ink2)!important}
body.theme-cream input,body.theme-blue input,body.theme-grey input,body.theme-mint input,
body.theme-cream select,body.theme-blue select,body.theme-grey select,body.theme-mint select,
body.theme-cream textarea,body.theme-blue textarea,body.theme-grey textarea,body.theme-mint textarea{background:var(--panel)!important;color:var(--ink)!important;border-color:var(--line2)!important}
```

Surfaces worth covering in every palette block: `body`, `.panel`, `.side`, `header.top`, cards
(`.card`, `.svc-row`, `.krcard`, `.avtask`), the hero (`.hero-live`), chips (`.chip-live`), the
log/report text (`pre.log`, `.bot-log`, `.bodytext`), `input/select/textarea`, and the sidebar
active item (`#side button[data-go].on`).

## Wiring: one control, one storage key

Replace the old two-state toggle with a `<select>` so six themes fit without cycling:

```html
<select class="btn" id="hud-theme" title="Tukar tema" style="padding:4px 6px">
  <option value="light">TERANG</option>
  <option value="cream">KRIM</option>
  <option value="blue">BIRU MUDA</option>
  <option value="grey">KELABU TERANG</option>
  <option value="mint">HIJAU MUDA</option>
  <option value="dark">GELAP</option>
</select>
```

```js
const THEMES = ["light","cream","blue","grey","mint","dark"];
function applyTheme(name) {
  THEMES.forEach((x) => document.body.classList.remove("theme-" + x));
  document.body.classList.remove("light");
  // semua tema cerah berkongsi kelas `light` sebagai asas lapisan terang
  if (["light","cream","blue","grey","mint"].includes(name)) document.body.classList.add("light");
  if (name !== "light") document.body.classList.add("theme-" + name);
  try { localStorage.setItem("console_theme_v3", name); } catch (_) {}
}
const t = document.getElementById("hud-theme");
if (t) {
  t.addEventListener("change", () => applyTheme(t.value));
  const saved = localStorage.getItem("console_theme_v3") || "light";
  t.value = saved; applyTheme(saved);
}
```

Key details that matter:

- **Bump the storage key** (`console_theme_v2` → `_v3`). A browser holding `"dark"` under the old
  key will otherwise override the new default on every load.
- **Light themes share the `light` class.** The palette class is additive; without `light` the
  base dark sheet wins and only the palette borders show.
- **`dark` gets no `theme-` class and no `light`** — it falls through to the base sheet.
- The `click` listener must become `change`; a `<select>` fires `click` on every option tap and
  the last value wins inconsistently.

## Verification

```bash
# 6 pilihan tema sampai ke browser
curl -s 'http://127.0.0.1:8787/?tab=pusat' | grep -o 'value="\(light\|cream\|blue\|grey\|mint\|dark\)"' | tr '\n' ' '

# lapisan tema diservis (bukan sekadar ditulis ke cakera)
curl -s 'http://127.0.0.1:8787/static/theme.css?v=16' | grep -c 'TEMA PILIHAN v15'

# versi yang diminta halaman mesti sama dengan yang diservis
curl -s 'http://127.0.0.1:8787/?tab=pusat' | grep -o 'theme.css?v=[0-9]*'
```

Bump `?v=` in `index.html` on every theme edit — the CSS may be byte-identical in size and a
user's screenshot can predate the change.

## Pitfall: SVG chart text

The org chart reads `--oc-text` / `--oc-node` etc. Every palette must set `--oc-text` (and ideally
`--oc-node`) or the chart keeps the previous theme's ink and turns into unreadable blocks — the
exact complaint that started the whole sweep.
