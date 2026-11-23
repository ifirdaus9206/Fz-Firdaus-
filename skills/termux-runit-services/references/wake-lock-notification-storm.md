# Notifikasi "N sessions (wake lock held)" berulang tanpa henti

Keluhan yang diterima: *"termux wake-lock tak henti buka"* — notifikasi muncul semula berulang
kali, bukan sekali. Ini BUKAN tanda lock dilepaskan; ia tanda `termux-wake-lock` DIPANGGIL
berulang. Android memaparkan semula notifikasi pada setiap panggilan.

## Punca yang disahkan pada peranti ini (2026-11)

`~/.hermes20/scripts/keeper.sh` — penjaga yang berjalan dalam gelung `while true; sleep 60`
melakukan ini setiap kitaran:

```bash
if [ -f "$FLAG" ]; then
  termux-wake-lock >/dev/null 2>&1 || true   # ← SETIAP 60s = notifikasi setiap 60s
  touch "$HOME/.hermes20/.wake_held"
fi
```

Ia "betul" dari segi niat (lock sentiasa dipegang) tetapi salah dari segi Android: satu panggilan
sehari cukup. Lock dipegang oleh **proses app Termux**; kalau app itu mati, keeper (anak proses
app) juga mati — jadi acquire semula setiap kitaran tidak menambah keselamatan, hanya notifikasi.

## Pembaikan

```bash
HELD="$HOME/.hermes20/.wake_held"
...
if [ -f "$FLAG" ] && [ ! -f "$HELD" ]; then
  termux-wake-lock >/dev/null 2>&1 || true
  touch "$HELD"
  say "wake-lock: dipegang SEKALI (bukan setiap kitaran)"
fi
```

Satu pemanggilan setiap kali keeper bermula (boot / `sv restart hermes-keeper`). Hanya
`wake_ctl.sh off` yang membuang `$HELD` dan melepaskan lock.

## Cara membuktikan tanpa men-spam bos

Tiga percubaan pertama gagal kerana instrumentasi, bukan kerana kod — jangan ulang:

1. **Stub dalam `PATH` tidak berkesan** untuk keeper ini: skrip menulis semula PATH
   (`export PATH=$PREFIX/bin:$HOME/.local/bin:$PATH`), jadi `$PREFIX/bin/termux-wake-lock`
   yang sebenar dipanggil dan stub di hadapan PATH diabaikan. (Untuk `hermes-console/tools/keeper.sh`
   stub BERKESAN, kerana skrip itu tidak menulis semula PATH.)
2. **`sed ... -e 's|...|echo WAKE >> $T/calls|'`** dalam petikan tunggal menulis `$T` secara
   literal → dalam salinan ujian `$T` kosong → tulisan ke `/calls` gagal senyap → kiraan 0.
   Guna petikan berganda untuk bahagian yang perlu diinterpolasi, atau tanam laluan sebenar.
3. **Membuang `$HELD` pada skrip hidup** memanggil `termux-wake-lock` sebenar → satu notifikasi
   sebenar kepada bos. Elakkan; guna salinan ber-instrument.

Resipi yang lulus (salinan ber-instrument, tiada kesan sampingan):

```bash
T=$(mktemp -d "$PREFIX/tmp/hermes-verify-XXXXXX"); : > "$T/flag"; : > "$T/calls"
sed -e "s#^LOG=.*#LOG=\"$T/k.log\"#" -e "s#^FLAG=.*#FLAG=\"$T/flag\"#" \
    -e "s#^HELD=.*#HELD=\"$T/held\"#" \
    -e "s|termux-wake-lock >/dev/null 2>&1 \|\| true|echo WAKE >> $T/calls|" \
    "$HOME/.hermes20/scripts/keeper.sh" > "$T/k.sh"
bash -n "$T/k.sh"
timeout 8 bash "$T/k.sh"; timeout 8 bash "$T/k.sh"; timeout 70 bash "$T/k.sh"
wc -l < "$T/calls"     # mesti 1, bukan 3
rm -rf "$T"
```

Bukti alternatif yang lebih murah: keeper hanya menulis ke `keeper.log` bila ia bertindak, jadi
`grep -c 'dipegang SEKALI' keeper.log` mesti bertambah 1 selepas kitaran pertama dan **0**
selepas itu.

## Panggilan wake-lock yang lain — semak semua, bukan satu

- `$PREFIX/var/service/*/run` — dahulu `wake_ctl.sh auto` ada dalam `run` gateway; setiap
  restart runsv = satu notifikasi. Kekalkan ia di luar `run`.
- `~/hermes-console/tools/keeper.sh` (cron `*/5 * * * *` melalui `console_keeper.sh`) — memanggil
  `termux-wake-lock` hanya jika konsol mati ATAU `$WL_STATE` tiada, jadi ia senyap semasa sihat;
  sahkan dengan stub PATH (berkesan untuk skrip ini) bahawa kiraan = 0.
- `~/.hermes20/scripts/fix_gateway_once.sh` — one-shot, tetapi pastikan kerjanya benar-benar
  `completed`/`enabled=false` dalam `cronjob list`; job berulang yang menyebut wake-lock akan
  menghidupkan semula ribut.
