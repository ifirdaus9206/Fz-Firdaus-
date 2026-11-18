# Laporan: Notifikasi "3 sessions (wake lock held)" keluar tak henti-henti

Tarikh: 2026-11-18 · Oleh: Ketua · Status: **SIAP / DIBETULKAN**

## Gejala
Notifikasi Termux `3 sessions (wake lock held)` (butang Exit / Release wakelock) muncul
berulang-ulang pada skrin telefon.

## Punca sebenar (dua bug bertindan)
1. **Fail:** `/data/data/com.termux/files/usr/var/service/hermes-gateway/run`
   Baris `wake_ctl.sh auto` diletakkan **sebelum** `exec hermes gateway run`.
   Setiap kali runsv menghidupkan semula khidmat, `termux-wake-lock` dipanggil semula.
   Android menyiarkan semula notifikasi pada SETIAP panggilan `termux-wake-lock`.
2. **Gelung restart gateway.** Gateway orphan (PID 5292) memegang `~/.hermes20/gateway.lock`.
   Anak runsv keluar dalam ~1s dengan mesej
   `✗ Another gateway instance is already running (PID 5292)` → runsv cuba lagi setiap ~2s →
   satu panggilan wake-lock setiap ~2s → notifikasi berkelip tanpa henti.

Bukti sebelum: `sv status hermes-gateway` menunjukkan PID bertukar setiap 1–3 saat.

## Pembetulan
1. `run` khidmat gateway: baris `wake_ctl.sh auto` **dibuang**. Wake-lock kini diambil sekali
   sahaja di peringkat boot / keeper (`wake_ctl.sh auto` masih ada dalam `start_all.sh` dan
   `~/.termux/boot`).
2. `run` khidmat gateway: ditambah gelung **menunggu** (maks 30 min) selagi ada gateway lain
   memegang lock, bukan keluar serta-merta. Tiada lagi gelung panas; khidmat mengambil alih
   secara terkawal bila gateway lama mati.
3. `~/hermes-console/tools/keeper.sh`: ditambah jaring keselamatan runit — `sv up` untuk
   `hermes-gateway`, `hermes-console`, `hermes-dashboard` jika terhenti (tidak pernah mematikan
   yang sedang jalan).

## Bukti selepas pembetulan
```
sv status hermes-gateway
run: hermes-gateway: (pid 31098) 72s      <-- PID sama, uptime menaik (bukan gelung)

pgrep -af "hermes gateway run"            <-- hanya satu gateway: pid 5292 (yang berkhidmat)
pgrep -af termux-wake-lock                <-- kosong: tiada lagi panggilan berulang
curl 127.0.0.1:8787/api/ping              -> 200
curl 127.0.0.1:9119/                      -> 302 (login, normal)

wake_ctl.sh status
HELD (wake-lock aktif — phone tak tidur)
auto-mode: ON
```

## Nota untuk bos
- Satu notifikasi Termux **kekal** di skrin selagi wake-lock dipegang. Itu BETUL dan perlu —
  tanpanya Android akan tidurkan Termux dan gateway mati. Yang dibetulkan ialah ia **tidak lagi
  muncul berulang-ulang**.
- Angka `3 sessions` = bilangan sesi terminal Termux yang terbuka dalam app, bukan kebocoran.
  Boleh jadi 1 dengan menutup sesi tambahan dalam app Termux.
- Jika mahu telefon boleh tidur (bateri), jalankan: `bash ~/hermes-console/tools/wake_ctl.sh off`
  — tetapi gateway berkemungkinan mati bila skrin lama padam.
