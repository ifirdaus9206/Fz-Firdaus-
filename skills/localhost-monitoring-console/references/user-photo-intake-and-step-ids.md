# Intake of user photos + step-id consistency

Two failure classes hit back-to-back on 2026-11-11 when the user sent phone screenshots through
Telegram and then asked *"aku ada letak dan simpan betul atau tidak"*. Both are cheap to prevent.

---

## 1. Where a "Telegram" photo actually lands

Photos the user sends in chat are **not** in the console inbox and **not** in `data/steps/`. They are
cached by the gateway:

```
~/.hermes20/cache/images/img_<hash>.jpg
```

So when the user says *"aku dah bagi imej dalam sistem"* and `GET /api/inbox` still shows only old
items, search by mtime, not by name:

```bash
find ~/.hermes20/cache/images -type f -newermt "-24 hours" -printf '%TH:%TM %8s %p\n'
```

Console uploads (`POST /api/steps`, `POST /api/inbox`) are a **different** pipeline — a user can
have done one, the other, or neither, and both answers are worth stating explicitly.

## 2. Prove the copy before deleting the source

The user asked: *"kalau sudah betul padam di Telegram, simpan di peranti sahaja"*. Order matters —
hash first, delete second, or you can destroy the only good copy:

```bash
C=~/.hermes20/cache/images; S=~/hermes-console/data/steps
sha256sum $C/img_aaaa.jpg $S/step-20261111_125919.jpg    # must be identical
ls -l     $C/img_aaaa.jpg $S/step-20261111_125919.jpg    # same byte count
rm -f     $C/img_aaaa.jpg                                # only after the hashes match
```

Then re-prove the surviving copy:

```bash
python3 -c "from PIL import Image; im=Image.open('data/steps/x.jpg'); im.verify(); print(im.size)"
curl -s -o /dev/null -w '%{http_code} %{content_type} %{size_download}b\n' \
  http://127.0.0.1:8787/api/steps/<id>/file      # want: 200 image/jpeg <same bytes>
```

### Say the limit out loud

A bot **cannot delete the user's own message** in Telegram (only its own, and only within the
deletion window). After clearing the cache, the honest sentence is:

> Salinan dalam sistem saya sudah tiada; gelembung gambar dalam Telegram anda perlu padam sendiri
> (tekan lama → Delete).

Never imply the chat bubble is gone.

## 3. Step ids: one namespace, validated the same on write *and* read

Ids written by different code paths differed:

| Writer | Example id |
|---|---|
| seed | `seed1` |
| `POST /api/steps` | `20261111_125400_db7496` |
| hand-added / imported | `perihal-20261111_125919` |

The file endpoint validated with `re.fullmatch(r"[A-Za-z0-9_]{4,40}", sid)` → every id containing a
**hyphen** returned `400 {"detail":"id tidak sah"}`. Symptom the user sees: the step exists in
`GET /api/steps` (count goes up) but the thumbnail is broken and `aid`/click does nothing. It looks
like "image corrupt", it is actually "id rejected".

Fix: allow the characters your writers emit, and keep the two regexes together:

```python
STEP_ID_RE = re.compile(r"[A-Za-z0-9_\-]{3,60}")
```

Checklist whenever a new id format is introduced anywhere in the app:

1. grep the validators: `grep -rn "fullmatch\|re.match" app.py | grep -i "id"`
2. write one id of the new shape, then `curl` **every** endpoint that takes an id
   (file, detail, delete) and require 200;
3. only then add the UI affordance.

A create-then-fetch smoke check (POST one item, GET its file, assert byte count) catches this class
before the user does — add it to the console smoke test as one line:

```
POST /api/steps → GET /api/steps/<new id>/file → expect 200 + identical size
```

## 4. Device-labelled variants without duplicating art

The same schematic guides serve any HyperOS phone; only the model name differs. Do **not** ship a
second copy of six images. Add a label parameter to the generator and post-process:

```python
label = "REDMI NOTE 15 PRO 5G"
if nama.startswith("adb-"):
    svg = svg.replace(">LANGKAH</text>", f">LANGKAH · {label}</text>")
```

Re-run `scripts/verify_svg_text_layout.py` afterwards — a longer header is exactly the kind of line
that starts overflowing the frame (`LANGKAH · REDMI NOTE 15 PRO 5G` ≈ 353 px at 21 px bold, safe
inside a 640 px box, but always measure instead of guessing).

Reading the model/IP off the user's own screenshot is legitimate evidence: a "Status" screen gave
`REDMI Note 15 Pro 5G` + IP `192.168.0.8`, which was then used to pre-fill the ADB form
(`value="192.168.0.8:"`) so the user only supplies the pairing **port** and the 6-digit code.
Never repeat IMEI/EID/MAC back into logs or docs — state that they were present and left unrecorded.
