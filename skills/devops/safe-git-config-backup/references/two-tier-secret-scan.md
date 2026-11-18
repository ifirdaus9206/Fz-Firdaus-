# Dua peringkat imbasan rahsia (menggantikan tiga tier)

Kes terukur: cron `Sandaran malam` gagal `exit 3` beberapa malam, HEAD beku. Dua fail ditandakan,
**kedua-duanya palsu**:

1. `docs/INSIDEN-*.md` — contoh sengaja: `GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx` (16 `x`).
2. `skills/devops/safe-git-config-backup/SKILL.md` — prosa + `AKIA<16-17-aksara>`.

Punca: satu lapis `ASSIGN_RE` (kata kunci + `[:=]` + 12+ aksara) dipindai pada **semua** fail,
jadi dokumentasi sah yang memetik contoh kelihatan seperti kredential.

## Reka bentuk

Dua paksi berasingan, bukan tiga tahap keterukan:

| | Corak | Fail |
|---|---|---|
| PERINGKAT 1 | bentuk kredential keras | **semua**, termasuk `*.md` dan `docs/` |
| PERINGKAT 2 | `nama=nilai` sensitif | hanya **bukan-dokumentasi**, + tapisan nilai |

Peringkat 1 tiada pengecualian. Peringkat 2 dikecualikan pada `*.md`, `docs/`, `references/`,
`templates/`, `*.example|*.sample|*.dist`.

```bash
# PERINGKAT 1: corak keras (AKIA berasingan, lihat di bawah)
HARD_RE='(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})'
# AKIA dipadankan TAMAK supaya akhiran boleh diperiksa
AKIA_RE='AKIA[0-9A-Z]{16,}'

# PERINGKAT 2
ASSIGN_RE="(password|passwd|secret|token|api[_-]?key|app_password|client_secret)[\"']?[[:space:]]*[:=][[:space:]]*[\"']?[^\"'[:space:]]+"

IS_DOC() {
  case "$1" in
    *.md|docs/*|*/docs/*|references/*|*/references/*|templates/*|*/templates/*|*.example|*.sample|*.dist)
      return 0 ;;
  esac
  return 1
}

# 0 = rahsia sebenar (blok), 1 = abaikan
REAL_VALUE() {
  local v="$1" first rest
  v="${v%$'\r'}"
  while [ "${#v}" -gt 0 ]; do
    case "${v: -1}" in
      '"'|"'"|','|';'|')'|']'|'}') v="${v%?}" ;;
      *) break ;;
    esac
  done
  [ "${#v}" -ge 12 ] || return 1
  case "$v" in '<'*|'$('*|'${'*) return 1 ;; esac
  case "$v" in
    *REDACTED*|*DIMASK*|*PLACEHOLDER*|*CHANGEME*|*YOUR_*|*example*|*contoh*) return 1 ;;
  esac
  first="${v:0:1}"
  rest="${v//"$first"/}"          # satu aksara berulang: xxxx, ****
  [ -z "$rest" ] && return 1
  return 0
}
```

Gelung utama (baris **ditambah** sahaja, buang `+++` header dan `+` depan):

```bash
added="$(git diff --cached -U0 -- "$f" | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^+//')"

tier=""
if   printf '%s\n' "$added" | grep -qE "$HARD_RE"; then tier=1
elif printf '%s\n' "$added" | grep -oE "$AKIA_RE" | grep -qvE 'EXAMPLE$'; then tier=1
elif printf '%s\n' "$added" | grep -qE "$AKIA_RE"; then
  LOG_MSG "ABAIKAN (pseudo-kelayakan AWS EXAMPLE): $f"      # log sahaja, bukan bypass senyap
elif ! IS_DOC "$f"; then
  while IFS= read -r line; do
    vals="$(printf '%s\n' "$line" | grep -oiE "$ASSIGN_RE" \
      | sed -E "s/^[^:=]*[:=][[:space:]]*[\"']?//")"
    while IFS= read -r val; do
      [ -n "$val" ] && REAL_VALUE "$val" && { tier=2; break; }
    done <<< "$vals"
    [ -n "$tier" ] && break
  done <<< "$added"
fi
[ -n "$tier" ] && HIT_FILES="${HIT_FILES}${f} (peringkat ${tier})"$'\n'
```

## Mengapa `AKIA…EXAMPLE` dikecualikan (bukan pelonggaran)

AWS menetapkan pseudo-kelayakan dalam **dokumentasi** sentiasa berakhir `EXAMPLE`
(`AKIA<16-17-aksara>`) dan tidak memberi akses. Padanan tamak (`{16,}`) perlu kerana
`{16}` tepat memotong token kepada `AKIAIOSFODNN7EXAMPL` — yang **tidak** berakhir `EXAMPLE`,
jadi semakan akhiran akan gagal. Kunci sebenar (16–20 aksara, bukan `EXAMPLE`) tetap `exit 3` —
disahkan dalam matriks.

## Keputusan ujian sebenar (matriks 25 kes, semua lulus)

Blok: `sk-`, `ghp_`, `github_pat_`, `AIza`, `AKIA` sebenar, `xoxb-`, `-----BEGIN RSA PRIVATE
KEY-----`, JWT tiga bahagian, `sk-` dalam `.md`, `ghp_` dalam `docs/`, `db_password=`,
`app_password: "…"` (petikan), `{"client_secret": "…"}`, `export API_KEY=…`.

Abaikan: `AKIA…EXAMPLE`, `api_key=<…>`, `password=${…}`, `secret=****…`, `token=REDACTED-…`,
`passwd=abc123` (pendek), `api_key=YOUR_KEY_HERE_1234`, `client_secret=contoh-…`,
`app_password=example-…`, `password=<nilai>` dalam `.md`, `token=…` dalam `references/`.

Ujian pada repo sebenar: (a) dua fail FP → `exit 0` senyap + commit; (b) `sk-…` dalam
`ujian-kunci.md` → `exit 3`, HEAD tidak berubah (membuktikan `.md` **tidak** dikecualikan buta);
(c) `db_password=Qz7TmLp2RvXk9Wn4` dalam `.conf` → `exit 3`; (d) `api_key=xxxxxxxxxxxxxxxx`
dalam `.env` bukan-dok → `exit 0` (diabaikan, ter-commit → perlu commit pembetulan); (e) selepas
pembersihan `git status --short` kosong + `exit=0` tanpa stdout.

## Perangkap

- **Jangan buang peringkat 1 untuk fail dokumentasi.** `.md` mesti kekal dipindai; hanya
  peringkat 2 yang doc-aware.
- **`HIT_FILES` mesti membawa tag peringkat** (`(peringkat 1)`) — tanpa itu, laporan tidak dapat
  membezakan kunci sebenar daripada nilai tugasan.
- **Baris prosa boleh memadankan `sk-`:** `delegate_task-<28-aksara>.md` = `sk-` + 21
  aksara. Jangan longgarkan `sk-` untuk itu.
- **`BARE_RE` (baris token bogel) dibuang** — ia menembak blok hash/signatur dalam docs, dan
  bentuk kunci sebenar sudah ditangkap peringkat 1. Jika dikekalkan, jangan sekali-kali
  membenarkannya pada `*.md`.
- Selepas ubah skrip: `bash -n`, kemudian `grep -c 'PERINGKAT 1'` sebagai bukti struktur, kemudian
  matriks, kemudian repo sebenar (a)–(e).
