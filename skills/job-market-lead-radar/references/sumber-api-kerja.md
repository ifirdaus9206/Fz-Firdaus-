# Sumber API kerja — peta medan, probe, dan peraturan skor

Disemak 2026-11-05 dari Termux (Android, tiada root). Semak semula dengan probe di bawah sebelum
percaya; laman tukar tanpa notis.

## Probe pantas (jalankan dulu, jangan bina atas andaian)

```bash
T=$PREFIX/tmp            # JANGAN guna /tmp di Termux — tak boleh tulis
curl -s -o /dev/null -w "freelancer %{http_code}\n" \
  "https://www.freelancer.com/api/projects/0.1/projects/active/?query=python&limit=3"
curl -s -o /dev/null -w "remoteok %{http_code}\n" -A "Mozilla/5.0" "https://remoteok.com/api"
curl -s -o /dev/null -w "wwr %{http_code}\n" \
  "https://weworkremotely.com/categories/remote-programming-jobs.rss"
curl -s -o /dev/null -w "jobstreet %{http_code}\n" -A "Mozilla/5.0" \
  "https://my.jobstreet.com/jobs?keywords=flutter"
```

Keputusan sebenar 2026-11-05: freelancer 200, remoteok 200 (648 KB), wwr 200, jobstreet **403**
(Cloudflare "Just a moment..."). Freelancer boleh dipanggil tanpa akaun/token.

## Freelancer.com — struktur respons

`GET /api/projects/0.1/projects/active/?query=<kw>&limit=20&full_description=true&sort=time_updated`

```
status: "success"
result.projects[]:
  id                  int          -> dedupe key "fl-<id>"
  title               str
  seo_url             str          -> pautan = https://www.freelancer.com/projects/<seo_url>
  preview_description str          (full_description=true -> ada description penuh)
  type                "fixed" | "hourly"
  budget.minimum / budget.maximum  float, dalam mata wang projek
  currency.code       "USD" | "INR" | "EUR" ...
  currency.exchange_rate  float    -> KALI ini untuk dapatkan bajet_usd
  bid_stats.bid_count int          -> saingan sedia ada
  time_updated        epoch saat
  language            "en" | ...
result.total_count / result.users
```

`budget.minimum/maximum` **bukan USD** secara lalai. Ini punca utama laporan penuh dengan kerja INR
yang nampak besar: `bajet_usd = maximum * currency.exchange_rate`.

## RemoteOK — struktur

`GET https://remoteok.com/api` → array JSON; `[0]` ialah notis lesen (tiada `position`), jadi tapis
`if isinstance(x, dict) and x.get("position")`.

Medan berguna: `position`, `company`, `tags[]`, `url`, `description` (HTML), `salary_min`,
`salary_max`, `epoch`, `slug`. Ini kerja **sepenuh masa jauh**, bukan projek pendek.

## We Work Remotely — RSS

`https://weworkremotely.com/categories/remote-programming-jobs.rss` → parse `xml.etree.ElementTree`,
`item/title`, `item/link`, `item/description` (HTML), `item/pubDate`
(`%a, %d %b %Y %H:%M:%S %z`). Juga sepenuh masa.

## Peraturan skor yang menghasilkan senarai berguna

Asas 0, tambah:

| Syarat | Mata |
|---|---|
| kata kunci di tajuk | +8 |
| setiap kata kunci padan (maks 3) | +6 |
| bajet USD dalam julat | +6 |
| bidaan ≤ 10 | +6 |
| bidaan > 60 | −6 |
| dihantar ≤ 6 jam | +6 |
| 6–24 jam | +3 |

Pintu masuk (gate) sebelum skor:
- tiada kata kunci langsung → buang (`tiada_kata_kunci`)
- kata kunci hanya di penerangan DAN jumlah padanan < 2 → buang (`padanan_lemah`)
- `bajet_usd` < `bajet_min` → buang (`bajet_rendah`)
- lebih 7 hari → buang (`terlalu_lama`)
- ada perkataan dalam `tolak_kata` → buang

## Konfigurasi YAML

```yaml
kata_kunci: [python, automation, chatbot, scraping, flutter]
tolak_kata: [adult, casino]
bajet_min: 30
bajet_max: 5000
maks_kerja: 8
skor_min: 6
simpan_hari: 14
sumber:
  freelancer: true
  remoteok: true
  weworkremotely: true
```

Baca dengan `yaml.safe_load`, kemudian `cfg.update(data)` di atas nilai lalai. Parser buatan sendiri
gagal senyap pada komen sebaris dan item `- `, dan kegagalan itu muncul sebagai "0 kerja" tanpa
ralat — bukan sebagai traceback.

## PROFIL.md — 5 medan yang mesti ditanya, jangan direka

1. Nama untuk klien panggil
2. Bidang utama + tahun pengalaman
3. 5 kemahiran paling kuat
4. 3 projek lepas (masalah → apa dibuat → hasil)
5. Kadar minimum (harian atau per projek, USD)

Draf proposal: ≤120 patah perkataan, satu masalah klien + satu penyelesaian + satu soalan di hujung,
Bahasa Inggeris, tiada pujian berlebihan, tiada janji harga sebelum skop jelas.
