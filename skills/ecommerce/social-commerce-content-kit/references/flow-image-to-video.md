# Google Flow / Veo — image-to-video with continuity (2 clips → 16s)

The user builds in Google Flow himself. Our job is to hand him: **Imej 1**, **Imej 2**, and two prompts whose cut is invisible.

## Frame design (before prompting)
- Both frames: 1080×1920, same lighting direction, same background surface, same colour grade.
- Imej 1 = hook: product centred, hero angle, big text top-third.
- Imej 2 = result/CTA: 30–45° angle change or in-use hand, product still same spot in frame.
- Leave text OUT of the frames if the model will animate them — models garble Malay text. Overlay text later in ffmpeg, or bake text in only if the frame is shown as a still.

## Prompt A (0–8s) — template
```
Subject: <product, exact shape/colour/material>
Start frame: <describe Imej 1 precisely — what is where>
Camera: slow push-in, 9:16 vertical, handheld-steady
Motion: <one primary motion only, e.g. product rotates 15° clockwise; light sweep left→right>
Lighting: soft window light from left, warm 5600K, gentle shadow under product
Mood: clean, premium, calm
End state: product slightly larger in frame, still centred, light sweep finished
Duration: 8 seconds · no on-screen text · no hands · no logo changes
```

## Prompt B (8–16s) — template, MUST start where A ended
```
Continue seamlessly from the last frame of Clip A.
Same product, same background, same lighting direction, same colour grade.
Start frame: <describe the exact end state of Clip A>
Camera: continue the same push-in, then settle
Motion: <secondary motion — e.g. hand enters from right, picks product, slight tilt>
Reveal: <price tag / bundle / result — keep it physical, not text>
End state: product presented toward camera, held/centred, ready for CTA text overlay
Duration: 8 seconds · no on-screen text · no logo changes
```

## Continuity checklist (why cuts show)
- [ ] Same background described with the same words in both prompts.
- [ ] Same light direction word ("from left") in both.
- [ ] Clip B prompt opens with "Continue seamlessly from the last frame of Clip A" + the literal end state.
- [ ] Only ONE motion per clip; two motions = morphing artefacts.
- [ ] No new objects introduced in B that were not visible in A.
- [ ] Text, price, hashtags → ffmpeg overlay, never generated.

## If the cut still jumps
1. Regenerate Clip B from Imej 2 *plus* the final frame of Clip A as an extra reference, if Flow allows.
2. Otherwise cover the cut: a 4-frame whip/zoom + whoosh at 8s hides most discontinuities.
3. Last resort: ffmpeg `xfade` with a 0.2s dissolve between A and B.

## Assembly (ffmpeg, 16s total)
```bash
printf "file 'a.mp4'\nfile 'b.mp4'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -shortest out-16s.mp4
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 out-16s.mp4
```
Text overlay (hook 0–3s, CTA 12–16s) with `drawtext`; keep inside the safe zone.
