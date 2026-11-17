---
name: social-commerce-content-kit
description: Build Shopee/TikTok product video content kits.
version: 1.0.0
author: Ketua (Hermes Agent)
license: MIT
platforms: [linux, macos, android]
metadata:
  hermes:
    tags: [ecommerce, shopee, tiktok, content, video, copywriting, ffmpeg]
    related_skills: [brand-identity-kit-generation, device-storage-handoff]
---

# Social-Commerce Content Kit

Turn ONE product into a shippable content pack: **2 storyboard images → Google Flow prompts → 16s vertical video → copy + hashtags for Shopee, TikTok, Facebook, Instagram, YouTube.**

## When to use

- User wants to market/sell a product on Shopee, TikTok Shop, FB, IG, YouTube.
- User asks for "video 16s", "imej 1 sambung imej 2", "ayat tarik pelanggan", "hashtag semua platform".
- Recurring for this user: he builds *many* videos, so the pack must be repeatable per product, not hand-crafted.

## STEP 0 — Capability audit BEFORE promising anything (non-negotiable)

Run `scripts/audit_capabilities.sh` first. Print the result as a table in the reply. Never promise an artifact you have not proven you can produce.

| Need | Probe |
|---|---|
| Video assembly | `command -v ffmpeg` |
| Image composition | `python3 -c "import PIL"` |
| SVG → PNG | `command -v rsvg-convert` / `magick` |
| AI image generation | keys in `.env` (`OPENAI/GEMINI/FAL/REPLICATE/STABILITY`) + ComfyUI |
| Browser / platform login | `command -v chromium/google-chrome/playwright` |

Then state plainly, in the user's language, what is possible and what is not. Typical honest split on a phone/Termux box with no image API:
- CAN: 1080×1920 graphics via Pillow/SVG, frame extraction from the user's reference video, ffmpeg 16s 9:16 render, all copy/hashtags, Flow prompts.
- CANNOT: log into Shopee Seller Centre or Google Flow for the user, generate photoreal AI images, harvest live best-seller data.

## STEP 1 — Get product data (do not pretend to scrape)

Shopee web is an SPA behind anti-bot: `GET /search?keyword=` returns only an HTML shell (~200 KB, no product objects) and `/api/v4/search/search_items` returns **403**. Do not build a plan that depends on harvesting Shopee.

**Product links the user shares are also unreadable.** Verified 2026-11: a shortlink (`s.shopee.com.my/XXXX`) redirects (HTTP 200) to `shopee.com.my/<shop>/<shopid>/<itemid>` — so you CAN extract the numeric `shopid`/`itemid` — but every content path is walled:

| Probe | Result |
|---|---|
| product page (mobile UA, cookies) | 294 KB shell, no `og:title`, no JSON-LD, no `__INITIAL_STATE__` |
| `api/v4/pdp/get_pc` | `{"error":90309999,"redirect_to_error_page":true}` |
| `api/v4/product/get` | `{"error":"error_not_found"}` |
| `r.jina.ai` proxy | redirects to `/verify/traffic/error` (CAPTCHA wall) |

So: confirm the item id, then **immediately ask for a screenshot of the listing** (name + price visible). Do not spend several turns scraping, and never invent a product name/price/benefit list to keep momentum — a kit built on guessed facts is worthless and gets the user's listing pulled. Say plainly: "pautan berjaya dibuka, isi produk disekat robot".

Legitimate sources, in order:
1. **Screenshot of the product page / listing** (name, price, main image) — fastest real data.
1. **Seller Centre → Analytics → best-selling products** (own shop, exact) — ask for screenshot/CSV export.
2. **User-supplied product links** (Share → Copy Link) — 3–5, best starting point.
3. **One reference video with high views** — copy the *style* (hook, tempo, on-screen text), never the file.

## STEP 2 — Two images (storyboard frames)

- Imej 1 = **HOOK (0–3s)**: product large, big text, clean background, 1080×1920.
- Imej 2 = **RESULT/CTA (8–16s)**: different angle or in-use shot, price + call to action.
- Safe-zone: keep text out of top ~250 px and bottom ~320 px (TikTok/Reels UI).
- No AI image model? Compose in Pillow/rsvg (gradient + product cut-out + big Malay text + badge). Say honestly these are *designed graphics*, not photoreal — Flow animates them.

## STEP 3 — Google Flow prompts (image 1 → image 2 continuity)

Write **two** prompts plus an explicit continuity clause. See `references/flow-image-to-video.md` for the template. Requirements:
- Clip A 8s, Clip B 8s → 16s total.
- Same subject, same lighting, same background between clips; name the motion that carries across the cut ("kamera push-in berterusan", "produk bergerak kanan ke tengah").
- No text rendered by the model — overlay text in ffmpeg instead (models garble Malay).

## STEP 4 — Copy + hashtags per platform

One folder per product with `shopee.md`, `tiktok.md`, `fb.md`, `ig.md`, `youtube.md`, `hashtag-master.md`. Specs and compliance in `references/platform-rules-my.md`.

Shape that works: hook 3 detik (masalah/soalan) → 3 manfaat konkrit → harga/nilai → CTA lembut. Malay, bahasa pasar, no hype Bahasa buku.

## STEP 5 — Assemble 16s video

Two modes. Pick by what exists, and say which one you used.

**A. Flow clips exist** — `ffmpeg` concat of the two clips → 1080×1920, one audio track, text overlays.

**B. No Flow clips (phone/Termux, no image API)** — render a *proof-quality* 16s animatic from the two Pillow frames. Verified working command, full recipe in `references/phone-render-pipeline.md`:
```bash
ffmpeg -y -loop 1 -t 8.25 -i imej-1.png -loop 1 -t 8.25 -i imej-2.png \
 -filter_complex "[0:v]scale=1080:1920,fps=24,format=yuv420p[v0];\
[1:v]scale=1080:1920,fps=24,format=yuv420p[v1];\
[v0][v1]xfade=transition=fade:duration=0.5:offset=7.75[v]" \
 -map "[v]" -c:v libx264 -preset veryfast -crf 24 -movflags +faststart out.mp4
```
Measured on a Redmi/Termux phone: **~14 s** per render, output ~284 KB. Duration math: `durA + durB − fade` → `8.25 + 8.25 − 0.5 = 16.000`.

- **Never use `zoompan` here.** `zoompan` on 1080×1920 hangs past a 240 s timeout on phone hardware; the killed run leaves an unplayable mp4 (`moov atom not found`).
- Always verify with `ffprobe` and write `05-VIDEO/semakan.txt` (duration, width/height, r_frame_rate) as evidence.
- If Flow clips are missing, deliver images + prompts + shot list and say the render is blocked on the user's Flow step.

A ready generator lives for this user at `~/shopee-video-factory/scripts/kit.py` (`--data product.json --out DIR`; schema in `templates/product.json`). It writes 2 images, the 6 copy files, the Flow prompts, the 16s video and `semakan.txt` in one pass — extend it instead of hand-writing a new pipeline.

## STEP 6 — Handoff

Folder convention (user demands one format per folder, plus a plain-Malay doc):
```
01-RISET/  02-IMEJ/  03-PROMPT/  04-TEKS/<produk>/  05-VIDEO/  06-SERAHAN/
```
`06-SERAHAN/BACA-DULU.md` must contain a recipient matrix (which file goes to which platform) and paste instructions. Copy to device storage with the project's verified one-way export script; never leave deliverables only in chat.

## Pitfalls

1. **Order matters: Shopee listing ready BEFORE the video.** Traffic to an empty listing raises bounce and tanks shop ranking. Say this to the user explicitly.
2. **Cosmetics = regulated.** Product must be NPRA/KKM-notified; keep the supplier's notification certificate. Never write medical claims ("hilang jerawat dalam 3 hari") — gets listings pulled.
3. **TikTok link policy.** Don't put "klik link Shopee" in video/caption; keep the Shopee link in bio.
4. **TikTok Shop "cannot sell" checklist** (tell the user to check Seller Center → Account Health): business verification/SSM, beauty category requiring NPRA docs, account restricted for policy breach, shop not linked, missing stock/pickup address.
5. **Don't repeat vendor myths about free storage** ("700 GB free in Termux"). Verify from the device with `df -h` / `du -sh`; report the real numbers.
6. **Fashion/beauty beat gadgets for impulse sales** (price, 3-second decision, visual proof, repeat purchase). Recommend ONE sub-niche first, prove the template, then scale.
7. **`/tmp` is not writable in Termux** — write test/scratch files to `$TMPDIR` or `$HOME/.scratch`, not `/tmp`.
8. **Pillow `fill=(r,g,b,alpha)` on an RGB canvas ignores alpha and paints solid white.** On a dark card that means a blinding white box. Use an explicit dark RGB fill (e.g. `(24,18,44)`) plus a coloured `outline=` instead.
9. **Check the rendered image before shipping.** Load it with vision and confirm no text is clipped or overlapping (price font at 132–150 px easily collides with the note line below it). Text-overflow bugs are invisible in code review but obvious in the picture.
10. **A "proven pipeline" must be run, not assumed.** Build the generator, run it on deliberately dummy data (`{slug:"ujian", badge:"UJIAN PIPELINE"}`), show the user the real output, and keep test artefacts in `07-UJIAN/` — then swap in the real product data. This lets you deliver value in the same turn a data source is blocked.

## Reply style for this user

- Plain Malay, no jargon, short tables.
- One question at a time; numbered 3–4 options at the end, he answers by number.
- Show proof (real numbers, exit codes, file paths), never "dah siap" without evidence.
