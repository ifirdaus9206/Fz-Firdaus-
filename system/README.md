# system/ — 8 Modul Sistem AI

Setiap fail ialah **system prompt** untuk satu lapisan dalam aliran kerja Ketua.
Semuanya berstatus **TERISI v2.0** (27 Okt 2026) dan boleh di-import.

| # | Modul | Peranan | Bila digunakan |
|---|---|---|---|
| 1 | `agent_factory.md` | Menjana ejen baharu: acuan persona, tier, ujian lulus/gagal, daftar roster | Bila perlu ejen baharu |
| 2 | `role_generator.md` | Menukar keperluan kerja → peranan + slug + skop | Langkah 1 selepas brief |
| 3 | `workflow_generator.md` | Menyusun urutan kerja, kebergantungan, gate | Selepas peranan ditetapkan |
| 4 | `orchestrator.md` | Mengarah dan menyelaras semua ejen; pemilik papan tugasan | Sepanjang pelaksanaan |
| 5 | `qa_system.md` | Memeriksa output terhadap kriteria lulus brief | Sebelum lulus apa-apa kerja |
| 6 | `recovery_system.md` | Mengendalikan kegagalan: P1 tegur → P2 ulang → P3 turun tier → P4 bersara | Bila ejen gagal |
| 7 | `completion_system.md` | Mengesahkan kerja benar-benar siap + bukti | Sebelum lapor kepada bos |
| 8 | `memory_manager.md` | Menyimpan fakta jangka panjang, menyuling memori pendek | Setiap malam / selepas kerja besar |

## Aliran

```
brief (8 medan)
      │
      ▼
role_generator ──► workflow_generator ──► orchestrator
                                              │
                        ┌─────────────────────┼──────────────────┐
                        ▼                     ▼                  ▼
                  agent_factory           qa_system        recovery_system
                        │                     │                  │
                        └──────────► completion_system ◄─────────┘
                                            │
                                            ▼
                                    memory_manager
```

## Peraturan

1. Modul ini **arahan**, bukan kod. Jangan simpan kunci atau data.
2. Setiap modul mesti boleh dibaca sendiri tanpa modul lain.
3. Versi lama disimpan di `backups/` atau `archive/system-backup-2026-10-27/`.
4. Selepas ubah mana-mana modul, naikkan tarikh dalam baris `STATUS:`.
