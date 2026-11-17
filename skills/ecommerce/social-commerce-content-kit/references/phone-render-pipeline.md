# Phone render pipeline (no AI image API, no Flow clips)

Verified 2026-11-12 on a Redmi Note 15 Pro 5G / Termux (ffmpeg 8.1.2, Pillow 12.3.0).
Produces a shippable animatic from two Pillow frames: 16.000 s, 1080×1920, 24 fps, ~284 KB, ~14 s render.

## 1. Frame spec (Pillow)

Canvas 1080×1920, vertical gradient (dark navy → dark purple). Fonts that exist in Termux:

```
/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans-Bold.ttf
/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf
```

Layout that survives TikTok/Reels UI chrome — keep all text inside y≈120…1600:

| Zone | Content | Sizes |
|---|---|---|
| badge chip | rounded rect, `UJIAN PIPELINE` / `BEST SELLER` | 44 bold |
| hook | 2–3 wrapped lines, white | 100 bold |
| subhook | 1–3 wrapped lines, gold `(255,214,102)` | 54 regular |
| photo | optional product cut-out, centred, `thumbnail()` keeping aspect | — |
| price card | rounded rect y=H−620…H−320, dark fill + gold 6 px outline | 132 bold |
| note + shop | y=H−420 / H−250 / H−180 | 42–52 |

Frame 2 mirrors this with a green-tinted gradient, `KENAPA PILIH INI?` at 82 bold, up to 5 benefit bullets (54 regular, 34 px gap), and a solid gold CTA card at the bottom.

Rules learned the hard way:
- `fill=(r,g,b,a)` on an **RGB** image renders solid — use a dark RGB fill plus `outline=` for card borders.
- Price at 132–150 px collides with the note line: reserve ≥180 px between the price baseline and the note.
- Wrap text with `draw.textlength()` per word; never rely on a fixed character count.
- Long hooks (≥3 lines) push the photo area down — clamp wrapped lines with `[:3]`.

## 2. Video command

```bash
ffmpeg -y -loop 1 -t 8.25 -i imej-1.png -loop 1 -t 8.25 -i imej-2.png \
 -filter_complex "[0:v]scale=1080:1920,fps=24,format=yuv420p[v0];\
[1:v]scale=1080:1920,fps=24,format=yuv420p[v1];\
[v0][v1]xfade=transition=fade:duration=0.5:offset=7.75[v]" \
 -map "[v]" -c:v libx264 -preset veryfast -crf 24 -movflags +faststart out.mp4
```

- Output duration = `durA + durB − fade`. For 16 s: `8.25 + 8.25 − 0.5 = 16.0`; `offset = durA − fade = 7.75`.
- `-preset veryfast -crf 24` is the speed/quality sweet spot on phone CPUs.
- **Do not use `zoompan`.** It blew past a 240 s foreground timeout on 1080×1920; the killed process left `moov atom not found` on the mp4. If you do kill a render, `rm` the partial file before retrying and re-check with `ffprobe`.
- 24 fps keeps the frame count at 384 (vs 480 at 30 fps) — noticeably faster, no visible loss for a two-still animatic.

## 3. Evidence

```bash
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate \
  -of default=nw=1 out.mp4 | tee semakan.txt
```
Expect `duration=16.000000`, `width=1080`, `height=1920`, `r_frame_rate=24/1`. Quote these in the reply — that is the proof that beats "dah siap".

## 4. Order of work when product data is blocked

1. Build/extend the generator on dummy data and run it end-to-end.
2. Render and *look* at both frames (vision check: clipping, overlap).
3. Show the user the real animatic + image as preview.
4. State the blocker with the exact HTTP/API evidence.
5. Ask for the minimum: name + price + main image (screenshot is the fastest single action).
