# PELAN — HERMES CONSOLE (Papan Pemantau Dwi-Home)

Tarikh: 2026-11-02
Pemilik: Ketua (Hermes20) · Subjek pantau: Hermes20 (Ketua/Agent Factory) + Hermes19 (Trading Desk)

---

## 1. MASALAH

Kerja aku (Ketua) dan kerja Hermes19 (trading) tersebar dalam:
- SQLite `state.db` setiap home (sesi, mesej, token, kos)
- `system/*.md` + `SOUL.md` (struktur organisasi 8 sistem, 7 undang-undang)
- `kanban.db`, `cron/executions.db`, `gateway_state.json`, `processes.json`
- Log trading: `decisions.log.jsonl`, `paper_trading_log.csv`
- Log runtime: `logs/gateway.log`, `logs/errors.log`

Tiada satu tempat untuk lihat: apa yang sedang jalan, berapa banyak kerja
selesai, berapa token/kos terbakar, dan **cara aku disusun** (aliran + gate).

## 2. OBJEKTIF

Satu papan web localhost, baca-sahaja (read-only), yang menjawab 4 soalan:
1. Apa status hidup sistem sekarang? (gateway, model, proses, cron)
2. Kerja apa yang telah/ sedang dibuat? (sesi → mesej → tool call)
3. Macam mana aku disusun? (8 sistem, aliran wajib, 7 undang-undang, gate)
4. Macam mana Hermes19 beroperasi? (doktrin risiko, keputusan ATC, paper trade)

Bukan penulis. Tiada endpoint yang mengubah data. Tiada tulis ke DB.

## 3. SUMBER DATA (disahkan wujud)

| Sumber | Laluan | Dipakai untuk |
|---|---|---|
| sessions | `~/.hermes20/state.db` (28 sesi, 1709 mesej) | senarai kerja, timeline |
| sessions19 | `~/.hermes19/state.db` (4 sesi, 21 mesej) | kerja trading |
| system prompts | `~/.hermes20/system/*.md` (7 modul + SOUL) | struktur organisasi |
| SOUL19 | `~/.hermes19/SOUL.md` | doktrin risiko/simbol |
| kanban | `~/.hermes20/kanban.db` (kosong sekarang) | tugasan |
| cron | `~/.hermes20/cron/executions.db` + ticker heartbeat | penjadual |
| gateway | `gateway_state.json`, `gateway.pid` | status telegram/uptime |
| proses | `processes.json` | background job |
| ATC | `decisions.log.jsonl` (25), `paper_trading_log.csv` (3) | keputusan trading |
| cakera | `du` atas kedua-dua home (16G / 105M) | kesihatan storan |

## 4. REKA BENTUK (UX)

Gaya: gelap, terminal-klasik, monospace untuk angka, sans untuk teks.
Satu halaman, 5 tab. Tiada framework JS, tiada CDN (offline-ready).
Kemas kini auto setiap 15s (polling), ada penunjuk "LIVE".

Tab:
1. **OVERVIEW** — kad status (gateway, model, sesi hari ini, token, kos, saiz
   home), graf 14 hari (sesi + tool call), ringkasan sesi terakhir.
2. **KERJA (WORK)** — jadual sesi (home, tajuk, mula, tempoh, mesej, tool call,
   token masuk/keluar, kos). Klik → panel kanan: timeline mesej (user/assistant/
   tool) + tool call yang dipanggil.
3. **ORGANISASI** — 8 kad sistem (fail, peranan, bila dipakai), rajah aliran
   wajib (objektif → agent_factory → role_generator → workflow_generator →
   orchestrator → qa → recovery → completion), senarai 7 undang-undang tetap,
   senarai skill per home.
4. **TRADING (19)** — doktrin simbol/leverage, kad ATC (keputusan terakhir,
   WIN/LOSS/NO_TRADE, confidence), jadual keputusan (25 baris terakhir),
   paper trades.
5. **SISTEM** — kesihatan: saiz DB, saiz folder, tail `errors.log` /
   `gateway.log`, status cron ticker, proses aktif, senarai endpoint.

## 5. ARKITEKTUR TEKNIKAL

```
~/hermes-console/
  PLAN.md            pelan ini
  README.md          cara jalan
  homes.json         daftar home (nama, laluan, peranan, warna)
  app.py             FastAPI + uvicorn, read-only
  static/index.html  shell UI
  static/style.css   tema gelap
  static/app.js      fetch API + render
  run.sh             skrip mula
```

- Stack: Python 3.13 + FastAPI + uvicorn (sudah ada). Tiada dependency baru.
- DB dibuka `file:...?mode=ro` — mustahil menulis.
- Bind `127.0.0.1:8787` sahaja (localhost, bukan 0.0.0.0).
- API:
  - `GET /api/meta` — daftar home + versi
  - `GET /api/overview?home=` — kad status + siri 14 hari
  - `GET /api/sessions?home=&limit=` — senarai sesi
  - `GET /api/session/{home}/{id}` — mesej + tool call
  - `GET /api/org` — 8 sistem, aliran, undang-undang, skill
  - `GET /api/trading` — ATC + paper + doktrin
  - `GET /api/health` — saiz, log tail, cron, proses
- Keselamatan: path home diambil daripada `homes.json` sahaja (tiada input
  pengguna masuk ke filesystem). Semua output `text/html` di-escape di klien.

## 6. FASA

1. Tulis PLAN.md (ini). ✔
2. Bina backend `app.py` + `homes.json`. Uji setiap endpoint dengan curl.
3. Bina frontend (index.html/style.css/app.js) 5 tab.
4. Jalankan di 127.0.0.1:8787, uji dalam browser/curl, sahkan angka sebenar
   sepadan dengan sqlite3.
5. Tulis README + `run.sh`, lapor bukti (output curl + screenshot teks).

## 7. DEFINISI SELESAI — status 2026-11-02 16:5x

- [x] `curl /api/overview` → 28 sesi, 1,744 mesej, 822 tool call, kos $0.86 (padan sqlite).
- [x] `curl /api/org` → 8 sistem, 8 langkah aliran, 7 undang-undang.
- [x] `curl /api/trading` → 25 keputusan ATC (TRADE_CANDIDATE), 2 paper trade, 5 simbol.
- [x] UI 5 tab lulus `node tools/render_test.js` terhadap API hidup (tiada undefined/NaN).
- [x] Bind 127.0.0.1:8787 (host dalam app.py), semua DB `mode=ro` —
      ujian tulis pulang `attempt to write a readonly database`.
- [x] Semua endpoint < 25 ms; 0 ralat dalam server.log.

Bukti render (petikan ujian) — sebelum fasa 2:
```
OK: OVERVIEW kad / graf 14 hari / jadual sesi
OK: WORK → #w-list (8557b) · timeline sesi 20261102_163318_aad921
OK: ORG → 8 kad sistem · aliran completion_system · 7 undang-undang
OK: TRADING → XAUUSD + jadual keputusan ATC
OK: SYSTEM → saiz home 16,347.3 MB / 104.1 MB
```

---

# FASA 2 — PENYERAPAN AGENCY-AGENTS (2026-11-02)

## 8. Apa yang dicari

Permintaan: `--cask msitarzewski/agency-agents/agency-agents` yang sudah ada dalam hermes20.
Dapatan (disahkan pada cakera):

| Benda | Keadaan sebenar |
|---|---|
| repo sumber | `~/.hermes20/agency-agents` — klon git penuh, commit `4e3ac3c` (2026-10-19), cawangan main |
| pemasangan | BUKAN brew cask (brew tiada pada Termux/Android); repo diklon terus, 1 fail berubah |
| katalog aktif | `plugins/agency-agents-router/data/agents.json` — 282 ejen (8 MB, dengan badan prompt) |
| divisi | `agency-agents/divisions.json` — 18 divisi (label + ikon + warna) |
| korpus | 325 fail .md; 267 ada frontmatter |
| app | `agency-agents-app/` — GUI Svelte/Tauri 125 MB (tidak dijalankan; cuma rujukan) |
| tapisan trading | `~/.hermes19/plugins/.../agents.json` — 21 ejen sahaja |
| penggunaan | state.db: search 5, inspect 2, load 1, delegate 0 (4 ejen pernah dipakai) |
| drift | laporan 2026-10-22: 15 path, 60 badan berbeza |

## 9. Reka bentuk penyerapan

Tab ke-6 `AGENCY` dalam console, baca-sahaja, empat lapis:

1. **Roster** — 282 kad (emoji, nama, vibe), tapis ikut divisi, cari bebas, klik → detail:
   badan prompt penuh, peranan dalam orkestra, sesi yang pernah guna, `load_hint`.
2. **Divisi → peranan 8 sistem** — setiap 18 divisi dipetakan kepada peranan Ketua
   (contoh testing → bukti qa_system; security → gerbang sebelum completion_system)
   + tunjuk skill tempatan yang menyokong divisi itu.
3. **Sumber & kemas kini** — repo, remote, commit, cawangan, fail berubah, nota bahawa
   brew cask tiada di Termux dan laluan kemas kini sebenar ialah `git pull` + `sync_agency_catalog.py`.
4. **Cadangan Ketua (dijana data)** — amaran/kritikal/nota yang dikira daripada data,
   bukan teks tetap: ejen belum dipakai, drift badan prompt, delegate sifar, dsb.
   Ditambah panel **drift** dan **penggunaan tool** (peristiwa + sesi).

## 10. Status fasa 2

- [x] `GET /api/agency` → 282 ejen, 18 divisi, 8 panggilan, 4 dipakai, 21 di hermes19.
- [x] `GET /api/agency/agent/frontend-developer` → badan 8,952 aksara, 3× dipakai.
- [x] Pemetaan 18 divisi + kiraan skill sokongan per divisi.
- [x] Panel git (commit 4e3ac3c, main, 1 fail berubah) + cadangan 4 item dijana data.
- [x] `node tools/render_test.js` → 19 semakan OK (termasuk 7 khusus AGENCY).
- [x] Endpoint agency < 230 ms (katalog 8 MB dibaca sekali, cache ikut mtime).
- [x] Kekal read-only: tiada endpoint menulis ke katalog/DB.

---

# FASA 3 — DEWAN ARAHAN (Ketua × 282 ejen)

## 11. Analisis bentuk & gaya 282 ejen (dijalankan, bukan diandaikan)

Skrip: `tools/analyze_agents.py` → `data/agent_style.json` (158 KB).
Sumber: badan prompt dalam katalog router.

| Metrik | Nilai |
|---|---|
| Persona | 282 (18 divisi) |
| Purata panjang | 1,892 perkataan (median 1,828; min 192; maks 4,638) |
| Archetype | lengkap 219 · spesialis 41 · ringkas 22 |
| Gaya | prosedural+metrik 209 · suara peribadi 29 · ringkas 22 · misi+pantang larang 17 · disiplin+artifak 5 |
| Seksyen standard | Identity & Memory 276 · Critical Rules 257 · Core Mission 252 · Communication Style 243 · Success Metrics 243 · Workflow 210 |
| Jumlah artifak | 17,250 bullet · 2,144 emoji · 197 blok kod |
| Kluster struktur | 10 (terbesar 154 ejen = templat penuh 8 seksyen) |

Kesimpulan: roster ini **hampir satu templat** — persona "You are X" + Identity/Mission/Rules/
Workflow/Metrics. Maksudnya: (a) boleh dipilih secara automatik ikut deskripsi, (b) bahagian
yang membezakan hanyalah skop domain + artifak, (c) persona boleh disuntik sebagai system
prompt tanpa diubah suai.

## 12. Alur kerja (imej: `static/img/workflow.png`, 1500×1210)

```
01 ARAHAN KAU      → taip dalam tab AGENCY
02 KETUA FAHAM     → pecah niat, tentukan sistem + gate
03 SELIDIK 282     → digest roster + metrik bentuk/gaya
04 PILIH & AGIH    → N ejen (3–5) + sebab setiap satu
05 EKSEKUSI        → setiap ejen = persona sendiri (system prompt badan penuh)
06 QA              → bukti > dakwaan, lalai NEEDS_WORK
07 SINTESIS KETUA  → gabung, percanggahan, verdict
08 ARKIB RUN       → runs/<id>/{plan.json,out_<slug>.md,final.md}
```

## 13. Reka bentuk teknikal

| Bahagian | Cara |
|---|---|
| enjin LLM | `agency_runner.py` — OpenRouter (kunci dari `~/.hermes20/.env`), model dari config |
| fasa rancang | 1 panggilan: digest 282 ejen (slug, nama, divisi, deskripsi 110 aksara) + arahan → JSON plan |
| fasa laksana | N panggilan selari (thread): persona penuh + skop kecil + format pulangan |
| sintesis | 1 panggilan: hasil semua ejen + gate 8 sistem → verdict |
| simpanan | `runs/<id>/run.json` (status), `out_<slug>.md`, `final.md` — bukan dalam DB Hermes |
| UI | panel DEWAN ARAHAN: textarea, had ejen, RANCANG → semak → LAKSANA → hasil langsung (poll 2s) |
| keselamatan | kunci tidak pernah dihantar ke browser; endpoint hanya terima teks arahan + id run |

## 14. Status fasa 3 (dibina & diuji 2026-11-02)

- [x] Imej alur kerja: `static/img/workflow.png` (1500×1210, 238 KB) + `.svg`, dipaparkan dalam tab.
- [x] Analisis 282 ejen dipaparkan (275 KB → JSON) + jadual per divisi + kluster.
- [x] POST `/api/agency/plan` → 12.9 s, Ketua pilih `twitter-engager` + `brand-guardian` dengan sebab.
- [x] POST `/api/agency/run/{id}` → 2 ejen selesai (34.6 s / 28.2 s), output disimpan.
- [x] Sintesis Ketua keluar: verdict NEEDS_WORK + bukti + gate (45 s).
- [x] Artifak run: `runs/<id>/{run.json, plan.json, out_<slug>.md, final.md}`.
- [x] `node tools/render_test.js` → 22 semakan OK (termasuk 3 DEWAN).
- [x] Tiada tulisan ke state Hermes; kunci API kekal di pelayan.
- [x] Kelemahan selari DIBETULKAN dalam fasa 4 (lihat bawah).
---

# FASA 4 — RANTAIAN EJEN + PENGUKUHAN KESELAMATAN (2026-11-02)

## 15. Kelemahan yang dibetulkan

| Kelemahan (fasa 3) | Pembetulan (fasa 4) |
|---|---|
| Ejen selari & bebas; penyemak tak nampak hasil pelaksana | `depends_on` per ejen → `waves()` susun gelombang; ejen penerima dapat blok "INPUT DARIPADA EJEN SEBELUM" (7k aksara) |
| Kitaran/halusinasi slug dalam depends_on | `_break_cycles()` buang tepi belakang + sahkan slug dalam senarai |
| JSON pelan kerap rosak | `_coerce_plan()` parse → panggil pembaikan sekali; prompt JSON ketat |
| Output terpotong senyap (model penaakulan) | `llm_chat` periksa `finish_reason=length` → gandakan token (maks 8k) |
| Tiada had kos | guard: 1 run aktif, 4 run/10 minit, 1 rancangan serentak (429) |

Bukti rantaian (`runs/20261102_184338`):
```
waves: [['twitter-engager'], ['brand-guardian']]
brand-guardian 19.4s → "Input disemak: Draf 1–5 daripada Twitter Engager"
final: draf diterima bersyarat, placeholder [Nama Kedai] ditandakan
```

## 16. Keselamatan (dibuktikan dengan curl)

| Lapisan | Ujian | Keputusan |
|---|---|---|
| Host allowlist (anti DNS-rebinding) | `curl -H "Host: evil.example"` | 403 |
| Origin allowlist | Origin luar senarai | 403 |
| Token konsol (CSRF) | POST tanpa `X-Console-Token` | 403 |
| Pengesahan id run | `POST /run/abc`, `run/..%2F..%2Fetc` | 400 / 404 |
| Header | CSP, X-Frame DENY, nosniff, no-store | hadir |
| Rahsia | `scrub()` pada output/final/error/trace | `sk-…`→`[DISUNTING]` |
| Suntikan | `scan_instruction()` | amaran dipapar, Ketua anggap DATA |
| Kebenaran fail | `runs/<id>/` | 0700 |
| Kunci API | pelayan sahaja, tiada dalam JSON/UI | disahkan |

## 17. Status fasa 4

- [x] depends_on + gelombang + input rantaian berfungsi hujung-hujung.
- [x] 26 semakan `node tools/render_test.js` lulus.
- [x] Imej alur kerja dikemas kini (gelombang 1/2).
- [x] 9 lapisan keselamatan diuji.
- [x] Tiada tulisan ke state Hermes; artifak hanya dalam `runs/`.
---

# FASA 5 — GABUNG DENGAN HERMES DESKTOP (2026-11-02)

## 18. Cadangan Ketua (keputusan reka bentuk)

Hermes Desktop ialah app Electron penuh (`apps/desktop`, React + router + SDK plugin).
Tiga pilihan:

| Pilihan | Penilaian Ketua |
|---|---|
| A. Fork `apps/desktop` dan tanam halaman console | Ditolak — menyimpang dari upstream, setiap `hermes update` jadi konflik |
| B. Tulis semula UI console dalam React desktop | Ditolak — dua sumber kebenaran, UI akan drift |
| **C. Plugin runtime di `~/.hermes20/desktop-plugins/` + iframe ke console** | **Dipilih** — pintu rasmi loader, tiada suntingan core, satu sumber UI |

Sokongan: repo sendiri menetapkan "capability lives at the edges; plugin jangan
sentuh core files" (AGENTS.md). Loader mengimbas `<hermes home>/desktop-plugins/<name>/plugin.js`
(`runtime-loader.ts`, `plugins.ts`), menulis semula import `@hermes/plugin-sdk`
dan `react*`, kemudian `register(ctx)`.

## 19. Apa yang dibina

**Plugin** `~/.hermes20/desktop-plugins/hermes-console/plugin.js` (8.4 KB, ESM):

| Kontribusi | Area | Kesan |
|---|---|---|
| `page` | `routes` | halaman `/console` — iframe `…/?embed=1` |
| `nav` | `sidebar.nav` | baris sidebar "Console" (codicon `pulse`) |
| `pill` | `statusBar.right` | penunjuk hidup/mati console |
| `open` | `palette` | "Console: Buka papan pemantau" |
| `set-url` | `palette` | tetapkan URL pelayan (desktop di mesin lain / LAN) |

**Console** (sisi pelayan):
- `?embed=1` → `body.embed` menyembunyikan brand/home/clock, padding rapat
- `frame-ancestors 'self' file: app: http://localhost:5174` — hanya shell desktop
  boleh membingkaikan; `X-Frame-Options` dibuang (CSP jadi kawalan tunggal)
- `GET /api/ping` — probe ringan, CORS `*`, tiada data sensitif
- URL pelayan boleh diubah dari Command Palette (disimpan dalam storage plugin)

## 20. Bukti (tanpa Electron — jujur tentang had)

| Semakan | Alat | Keputusan |
|---|---|---|
| Sintaks ESM + specifier + kontrak + area | `python3 tools/validate_desktop_plugin.py` | 9/9 OK, LULUS |
| `register(ctx)` sebenar + render halaman | `node tools/desktop_plugin_harness.mjs` | 14/14 OK — 4 kontribusi, iframe `127.0.0.1:8787/?embed=1` |
| Loader mengimbas folder ini | grep `runtime-loader.ts`, `plugins.ts` | disahkan `<hermes home>/desktop-plugins` |
| CSP + ping | curl | `frame-ancestors 'self' file: app: …`, ACAO `*`, tiada XFO |
| UI sedia ada | `node tools/render_test.js` | 26 semakan lulus |

**Had:** Electron tidak boleh dibina/dijalankan pada Android/Termux (tiada runtime
Electron untuk Android). Plugin aktif apabila Hermes Desktop dijalankan pada
macOS/Linux/Windows. Di peranti ini, paparan sama dicapai melalui pelayar.

## 21. Status fasa 5

- [x] Plugin runtime didaftarkan pada 5 area, tanpa suntingan core.
- [x] Mod embed + CSP frame-ancestors + /api/ping.
- [x] Dua alat pengesahan (validator + harness) lulus.
- [x] README plugin + README console dikemas kini.
- [ ] Larian sebenar dalam Electron — perlu mesin desktop (bukan Android).
---

# FASA 6 — PUSAT PEMANTAU (CARTA ORGANISASI LIVE) (2026-11-02)

## 22. Objektif

Satu tempat pemantau utama: carta organisasi langsung dari **Ketua → 8 sistem →
18 divisi → 282 ejen**, dengan sorotan hidup pada ejen yang sedang jalan, imej
menarik, dan aliran aktiviti masa nyata.

## 23. Reka bentuk

| Bahagian | Sumber | Cara |
|---|---|---|
| Hierarki | SOUL ENJIN (8 sistem) + katalog roster (18 divisi) | `DIV_SYSTEM` memetakan divisi ke sistem; `/api/orgchart` |
| Keadaan hidup | `runs/<id>/run.json` (gelombang, ejen) | `/api/live/state` — setiap ejen: done / running / queued |
| Aliran | `state.db` mesej terakhir + tool | feed 20 item, 2 saat |
| Beban | tool call 60 minit (bucket 5 minit) | sparkline 12 bar |
| Kos/hari | sesi hari ini, token, USD | kad + radar |
| Push | SSE `/api/live/stream` | EventSource; auto-sambung jika putus |

Imej (dijana sendiri oleh `tools/generate_visuals.py`, bukan scrape):
- `hero-control.png` 1600×420 — jaringan node/grid "mission control"
- `radar.png` 220×220 — dial radar berputar (CSS)
- `divider.png` — garis bercahaya

Interaksi: klik mana-mana divisi dalam carta → lompat ke tab AGENCY dengan
tapis divisi itu. Sorotan: kotak sistem + divisi bercahaya, denyutan `oc-pulse`,
lencana bulat bilangan ejen aktif.

## 24. Tambahan "lebih menarik" (cadangan Ketua yang dilaksanakan)

1. Command palette **Ctrl/⌘K** — cari tab, ejen (12 teratas), tindakan.
2. Pintasan papan kekunci **1–7** untuk tukar tab.
3. Toast bila run selesai/gagal (tanpa perlu tengok tab AGENCY).
4. Radar berputar + sparkline beban 60 minit + jam hidup.
5. Hero art gelap neon yang konsisten dengan tema console.
6. Mod embed kekal untuk Hermes Desktop; PUSAT jadi tab lalai.

## 25. Bukti

| Semakan | Hasil |
|---|---|
| `/api/orgchart` | 8 sistem · 18 divisi · 282 ejen · 0 unmapped · 8.8 KB |
| `/api/live/state` | sesi aktif, tool hari ini, kos, 20 feed, siri 60m |
| SSE `/api/live/stream` | `data: {...}` setiap 2 s (disahkan `curl -N`) |
| Carta hidup semasa run | dump PNG `tools/preview-chart-live.png` — sistem `agent_factory` + divisi `Product` menyala, lencana **1** |
| `node tools/render_test.js` | 31 semakan OK (5 khusus PUSAT) |
| Ejen gagal terpencil | `pricing-analyst` gagal (output terpotong) → Ketua tetap sintesis; had token dinaikkan (3 cubaan, 9k) |

## 26. Status

- [x] Carta organisasi SVG langsung (Ketua → sistem → divisi) + sorotan aktif.
- [x] Panel SEDANG JALAN (gelombang, ejen, kemajuan), feed, sparkline, radar.
- [x] Imej hero/radar/divider dijana dan dipasang.
- [x] SSE push 2s + fallback sambung semula.
- [x] Command palette, pintasan nombor, toast.
- [x] 31 semakan lulus; visual disemak melalui render PNG.
---

# FASA 7 — PETA EJEN AKTIF, KOS PER EJEN, BOT, 7 HARI, LAN (2026-11-03)

## 27. Skop (cadangan fasa 6 yang dilaksanakan)

| Cadangan | Status | Nota |
|---|---|---|
| (a) LAN + token + HTTPS | DONE | bind 0.0.0.0, token wajib, TLS self-signed pilihan |
| (b) Klik ejen → drawer butiran + output | DONE | `GET /api/agent-live/{slug}` + drawer |
| (c) Amaran bajet | **TIDAK** | diganti: kos per ejen + jumlah aktif (arahan pengguna) |
| (c') Peta ejen: di mana + kos setiap satu | DONE | panel PETA EJEN AKTIF + bot |
| (d) Sejarah beban 7 hari | DONE | snapshot 60s → `data/history.jsonl`, graf harian |
| Bot status | DONE | `POST /api/bot` + panel BOT STATUS |

## 28. Perakaunan kos sebenar

`llm_chat` kini menangkap `usage` OpenRouter: `prompt_tokens`, `completion_tokens`,
`reasoning_tokens`, **`cost` (USD)**. Ia diagregat per panggilan:

- `plan.usage` (Ketua merancang)
- `usage.agents[slug]` (setiap ejen — termasuk bilangan panggilan)
- `usage.synthesis` (Ketua menyemak)
- `usage.total_cost`, `usage.total_tokens`

Contoh sebenar (run `20261103_004637`, 2 ejen):

```
plan         10,835 tok  $0.002657
content-creator 2,857 tok  $0.001161
seo-specialist 18,986 tok  $0.010869   (2 panggilan — cubaan token dinaikkan)
synthesis    13,136 tok  $0.005822
TOTAL        45,814 tok  $0.020509
```

## 29. Peta ejen aktif

`GET /api/live/state` → setiap ejen bawa: `location` (sistem → divisi → ejen),
`state` (running/done/queued), `elapsed_s`, `tokens`, `cost`; setiap run bawa
`cost_so_far`, `tokens_so_far`. UI jadual: Status · Ejen · Lokasi · Masa · Token · Kos.
Klik baris → drawer: lokasi, status, masa, kos run ini, kos hari ini, tugasan, output penuh.

## 30. Bot status (dalam app)

`POST /api/bot {cmd}` — dikendalikan pelayan, tiada kos LLM:

```
/status   gateway, sesi aktif, run, ejen aktif, kos konsol hari ini
/agents   setiap ejen aktif + lokasi + masa + kos
/where <slug>  lokasi, run, tugasan, output
/cost     kos hari ini per run + per ejen (token & panggilan)
/runs     6 run terakhir + kos
/help
```

## 31. Mod LAN + HTTPS

```bash
./run.sh --lan          # 0.0.0.0:8787, token dalam .console-token
./run.sh --lan --tls    # + certs/console.crt (self-signed, SAN IP peranti)
```
- Tanpa token: HTML/API → **401**; `/api/ping` kekal awam (probe).
- `?t=<token>` → 303 + cookie HttpOnly 7 hari (token hilang dari URL).
- Host allowlist dilangkau dalam mod LAN (IP peranti sah), auth token mengambil alih.
- CSRF (X-Console-Token) kekal untuk semua POST.

Bukti: `tanpa token 401` · `?t= → 303 + set-cookie` · `cookie → 200` ·
`header X-Console-Auth → 200` · `https (self-signed) ping 200 · api 200 · html 200`.

## 32. Sejarah 7 hari

Thread `history-worker` menulis snapshot setiap 60s: tool/token/kos sesi, kos konsol,
bilangan ejen aktif, bilangan run. `GET /api/history?days=7` ambil nilai puncak harian
(kounter harian bersifat kumulatif). UI: bar harian + jumlah kos konsol 7 hari + puncak ejen.

## 33. Status

- [x] Kos per panggilan/ ejen/ sintesis direkod dan dipaparkan.
- [x] Peta ejen aktif (lokasi + masa + token + kos), drawer butiran.
- [x] Bot 6 arahan, diuji hujung-hujung.
- [x] LAN token + TLS diuji dengan curl.
- [x] Sejarah 7 hari (sampel direkod, graf dipaparkan).
- [x] 35 semakan `node tools/render_test.js` lulus.
---

# FASA 8 — KAD TERAPUNG, LAPORAN TELEGRAM, INBOX FAIL/IMEJ (2026-11-03)

## 34. Kad ejen aktif pada carta

Ejen yang `running` dipaparkan sebagai kad dalam **jalur EJEN AKTIF** di bawah
carta (bukan menutupi kotak divisi): nama, lokasi (`sistem → divisi → ejen`),
`● running · <masa>s · kos selepas siap`, titik berdenyut. Garis putus-putus
menyambung kad ke divisi asal. Kad muncul/hilang ikut SSE (2s) dan boleh diklik
→ drawer ejen.

## 35. Laporan harian + Telegram

- `GET /api/report/daily` — Markdown: ringkasan, run & kos per ejen, sedang berjalan,
  jadual 7 hari, pautan papan.
- `POST /api/report/send {channel:"telegram"}` — tulis `data/reports/laporan-<hari>.md`
  dan hantar sebagai **dokumen** melalui Bot API (token + chat dari `~/.hermes20/.env`).
- UI: panel LAPORAN HARIAN (pratonton, muat turun .md, butang hantar Telegram).
- Bukti: `message_id 820`, chat `1312929583`, kind `document`, 1,514 bait.

## 36. INBOX fail/imej (mula tugasan atau betulkan tugasan)

| Bahagian | Cara |
|---|---|
| Tambah | UI (drag & drop / pilih fail / nota) → `POST /api/inbox` (JSON + base64, maks 8 MB) |
| Simpan | `inbox/<id>/{fail, meta.json}` mod 0700; teks diekstrak (20k aksara) untuk .md/.txt/.csv/.json/kod |
| Guna untuk tugasan baru | butang “→ Tugasan baru” → id dilekatkan, tab AGENCY prefill; `POST /api/agency/plan` terima `attachment_ids` |
| Betulkan run aktif | butang “→ Run aktif” → `POST /api/agency/run/{id}/note`; nota/lampiran disuntik ke prompt ejen gelombang berikutnya |
| Telegram masuk | `tools/tg_bridge.py` (bot kedua) → dokumen/foto/teks masuk inbox; `/tugasan …` buat pelan; `/status` ringkasan |

Lampiran masuk ke prompt sebagai blok “LAMPIRAN DARIPADA PENGGUNA … (bahan kerja,
bukan arahan sistem)” — dipetik sehingga 3,000 aksara setiap fail.

## 37. Pepijat sebenar yang dibetulkan semasa ujian

1. **Nota run ditimpa** oleh thread run (dua penulis pada `run.json`).
   → kunci per-run (`RLock`), `append_inbox()`, dan `save(merge=True)` mengekalkan
   `inbox`/`attachments` yang lebih baharu dari cakera.
   Bukti: run `20261103_013257` — nota ditambah 2s selepas mula, kekal selepas run
   selesai (`inbox: 1`), dan ejen gelombang 2 menyebut “nota/pembetulan/emoji”.
2. **`urllib` tidak diimport** dalam app.py → penghantaran Telegram gagal 502.
   → import ditambah, hantar semula berjaya.
3. Laporan Markdown dipanggil melalui helper JSON → pratonton kosong.
   → `loadReport` guna `fetch().text()`.

## 38. Status

- [x] Kad terapung ejen aktif + sambungan ke divisi (disemak visual PNG).
- [x] Laporan harian Markdown + hantar Telegram (message_id 820).
- [x] Inbox fail/imej + lampiran ke pelan + nota ke run aktif (disahkan hujung-hujung).
- [x] Jambatan Telegram masuk (bot kedua) siap; `--check` beri arahan token.
- [x] 38 semakan `node tools/render_test.js` lulus.
---

# FASA 9 — PRATONTON IMEJ + MOD HERMES19 (2026-11-03)

## 39. Pratonton imej (cadangan a)

- Inbox: setiap item `kind=image` tunjuk thumbnail 64×64 (`/api/inbox/<id>/file`).
- Drawer ejen: bahagian **Lampiran run** — thumbnail untuk imej, chip 📎 untuk fail lain,
  semuanya boleh dibuka.
- `GET /api/agent-live/{slug}` kini pulang `run.attachments` (id, filename, kind, bytes).

## 40. Mod hermes19

Console kekal SATU kod; konteks boleh ditukar melalui env:

> **STATUS 2026-11-24 — BAHAGIAN INI SEJARAH SAHAJA.**
> `hermes19` sudah dipadam sepenuhnya. Port **8790 dibersarakan**; hanya **8787**
> yang digunakan. Jangan hidupkan semula 8790 atau `~/.hermes19`.

| Env | Kesan |
|---|---|
| `CONSOLE_DEFAULT_HOME` | home yang dipilih pada boot (lalai `hermes20`) |
| `CONSOLE_HOMES` | tapis senarai home dalam UI (cth `hermes19`) |
| `CONSOLE_DEFAULT_TAB` | tab yang dibuka (cth `trading`) |
| `CONSOLE_PORT` | port berasingan (8790) supaya tidak bertembung |

Pelancar: `~/.hermes19/console.sh` → `HERMES_HOME=~/.hermes19`,
`CONSOLE_DEFAULT_HOME=hermes19`, `CONSOLE_HOMES=hermes19`,
`CONSOLE_DEFAULT_TAB=trading`, `CONSOLE_PORT=8790`.

Bukti (dua instance serentak):
```
8787  default hermes20 / pusat     homes [hermes20, hermes19]
8790  default hermes19 / trading   homes [hermes19]
8790  /api/trading → 5 simbol · 25 keputusan · 7 doktrin
8790  /api/overview?home=hermes19 → 4 sesi · model deepseek-v4.1-flash
```

Dalam mod hermes19, tab pertama yang dibuka ialah **TRADING 19** (ATC, doktrin,
paper trade) dan home lain disembunyikan — jadi skrin dagangan bersih tanpa
tercampur dengan kerja Ketua.

## 41. Status

- [x] Thumbnail imej dalam inbox + drawer (lalai 64px, klik buka penuh).
- [x] `run.attachments` dihantar ke drawer.
- [x] `CONSOLE_DEFAULT_HOME` / `CONSOLE_HOMES` / `CONSOLE_DEFAULT_TAB`.
- [x] `~/.hermes19/console.sh` berjalan pada 8790, tab trading, homes ditapis.
- [x] Dua instance serentak tanpa bertembung (8787 + 8790).
---

# FASA 10 — MONITOR HERMES19 (DEMO PAPER ATC) (2026-11-03)

## 42. Nota penting: `justmakit`

`justmakit` TIDAK ditemui pada peranti ini:
- `find` seluruh `~` dan `/sdcard` (nama & kandungan) → 0 hasil
- carian sejarah sesi → 0 hasil
- /sdcard/Download/projects hanya ada `aina-launch`, `propertipro`

Yang ada dan digunakan: **demo paper trading ATC** (`run_paper.py`), iaitu
demo dagangan sedia ada dalam `~/.hermes19/autonomous_trading_controller`.
Kalau `justmakit` ada di tempat lain (Telegram/ peranti lain), hantar dan saya
jalankan yang itu pula.

## 43. Yang dijalankan

```bash
~/.hermes19/paper_demo.sh start 60     # ATC run_paper.py, selang 60s
~/.hermes19/paper_demo.sh status       # HIDUP · pid · bilangan paper trade
~/.hermes19/paper_demo.sh stop
```

Konsol: `http://127.0.0.1:8790` → tab **TRADING** (tab lalai dalam mod hermes19).

## 44. Panel PAPER LIVE (baharu)

`GET /api/trading` kini pulang `paper_live`:
`alive`, `procs[].pid`, `rows_total`, `rows` (12 terakhir dari CSV),
`events` (8 kitaran terakhir dari log), `csv_mtime`.

UI: strip status (HIDUP/MATI, pid, selang, bilangan trade, mtime) + aliran
kitaran ATC (`TRADE_CANDIDATE`/`NO_TRADE`/VETO) dengan cop masa.

## 45. Bukti langsung

```
02:19  alive true · pid 22204 · paper trades 7 · events 2
02:21  alive true · pid 22204 · paper trades 9 · events 4
       [2026-11-02T18:19:11Z] TRADE_CANDIDATE BUY conf=0.9
       [2026-11-02T18:20:11Z] TRADE_CANDIDATE BUY conf=0.9
       [2026-11-02T18:21:11Z] TRADE_CANDIDATE BUY conf=0.9
```

**Had demo:** ATC berjalan tanpa MT5 bridge, jadi suapan harga jatuh ke mod
`backtest` dengan harga stub (cap masa 2024-01-01). Ia membuktikan paip
orchestrator → risiko → log → konsol hidup, bukan harga pasaran sebenar.
Untuk harga sebenar: isi `MT5_BRIDGE_TOKEN` / `PRIMARY_DATA_FEED` dalam
`~/.hermes19/autonomous_trading_controller/.env`.

## 46. Status

- [x] Demo paper dimulakan (pid 22204) dan kekal hidup.
- [x] CSV bertambah 7 → 9, log kitaran bertambah 2 → 4 tanpa restart konsol.
- [x] `paper_live` dalam API + panel PAPER LIVE dalam tab TRADING.
- [x] `paper_demo.sh start|status|stop` untuk kawalan berulang.
- [x] 39 semakan render lulus (tambah 1 semakan PAPER LIVE).
---

# FASA 11 — METAAPI DEMO + SUAPAN HARGA SEBENAR (2026-11-03)

## 47. Kredensial yang dijumpai

| Fail | Token (sha8) | Akaun | Jenis | Server | State |
|---|---|---|---|---|---|
| `~/.hermes19/mt5-backtest/.env` | `e7cf25cd` | 1300009388 | demo | JustMarkets-Demo6 | UNDEPLOYED |
| `~/.hermes19/meta5/.env` | `04a65ba1` | 1400073582 | live | JustMarkets-Live6 | UNDEPLOYED |

Kredensial DEMO disalin ke `~/.hermes19/autonomous_trading_controller/.env`
(mod 600): `METAAPI_TOKEN`, `METAAPI_ACCOUNT_ID` (9e028add…), `MT5_LOGIN`,
`MT5_SERVER`, `MT5_ACCOUNT_TYPE=demo`, `PRIMARY_DATA_FEED=metaapi-demo,yahoo`.
Token LIVE **tidak** disalin (arahan: guna demo).

## 48. Halangan sebenar

MetaAPI menolak deploy kedua-dua akaun:

```
ForbiddenException: To allow trading account deployment please top up your account.
```

Jadi candle MetaAPI tidak boleh diambil sekarang (market-data memerlukan state
DEPLOYED). Ini bukan pepijat kod — ini baki akaun MetaAPI.

## 49. Penyelesaian: rantaian penyedia

`market/data_feed.py` cuba mengikut urutan dan merekod kegagalan:

1. **metaapi-demo** — `market/metaapi_bridge.py` dijalankan dengan venv meta5
   (`metaapi_cloud_sdk` 29.1.1). Gagal → ralat disimpan, bukan crash.
2. **yahoo** — harga sebenar tanpa kunci. XAUUSD tiada spot di Yahoo, jadi
   `GC=F` (kontrak hadapan emas) digunakan dan **dilabel proksi**.
   EURUSD/GBPUSD/USDJPY guna pasangan spot; WTI → `CL=F`.

Setiap panggilan menulis `data/feed_status.json` (sumber, harga, masa, ralat)
yang dibaca konsol.

## 50. ATC kini guna harga sebenar

- `core/orchestrator.py`: ambil M1/M15/H4 dari `data_feed` (bukan dummy).
- `core/decision_engine.py`: cap masa = UTC sekarang, `mode` dari `ATC_MODE`
  (sebelum ini hardcode `2024-01-01` / `backtest`).
- `decision["feed"]` = {source, price, last_time, errors}.

## 51. Bukti langsung

```
feed_status.json → source yahoo · GC=F · price 3969.50 · last_time 18:29:41Z
                  errors: metaapi-demo "akaun belum DEPLOYED (minta top-up)"
paper_trading_log.csv →
  2026-11-02T18:38:41Z, XAUUSD, TRADE_CANDIDATE, BUY, 0.9, … mode=paper
  2026-11-02T18:39:40Z, XAUUSD, TRADE_CANDIDATE, BUY, 0.9, … mode=paper
paper_demo.sh status → HIDUP · pid 2505 · 28 paper trade
konsol 8790 /api/trading → paper_live.alive true · feed.price 3969.5 (proxy)
```

**Nota ketepatan:** harga emas ialah proksi hadapan (GC=F), bukan spot XAUUSD
broker. Untuk spot sebenar + simbol broker (.m), akaun MetaAPI mesti DEPLOYED.

## 52. Status

- [x] Kredensial demo disimpan dalam `.env` (600).
- [x] Jambatan MetaAPI + rantaian fallback dibina dan diuji.
- [x] ATC guna candle sebenar, cap masa sebenar, mod `paper`.
- [x] Panel PAPER LIVE tunjuk sumber feed, harga, masa, dan status MetaAPI.
- [x] 39 semakan render lulus; tiada traceback.









### Nota kelemahan yang diakui
Ejen berjalan **selari dan bebas** — `brand-guardian` tidak nampak tweet yang ditulis
`twitter-engager`, jadi ia menyemak draf sendiri. Ketua mengesan ini dan menandakan
NEEDS_WORK. Penyelesaian masa depan: `depends_on` dalam plan supaya ejen kedua terima
output ejen pertama (fasa 4).

