# L4 · Catatan Keputusan Berjalan

Mengikat `docs/D10.md` Bagian 6. Keputusan besar tercatat sebagai ADR pada
`docs/D04.md`. Bagian ini menampung keputusan yang muncul saat pengerjaan,
tidak cukup besar untuk menjadi ADR, tetapi memengaruhi hasil.

**Ditambah, tidak disunting.** Koreksi ditulis sebagai entri baru yang merujuk
entri lama. Menimpa entri menghapus selisih antara apa yang diketahui saat
memutuskan dan apa yang diketahui kemudian — dan selisih itu bagian dari nilai
rekaman ini. Lihat `AGENTS.md` bagian Batas.

## Bentuk entri

Setiap entri berupa judul `## KB-nnn · ringkas` diikuti tabel enam bidang
wajib: Tanggal, Konteks, Keputusan, Alternatif, Dampak, Pemutus. Kelengkapannya
ditegakkan uji, bukan kebiasaan.

<!-- Entri dimulai di bawah baris ini. -->

## KB-001 · Pemegang Gerbang 1–4 pada jalur pengembangan sistem

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Alur SDD `docs/D12.md` Bagian 3 mensyaratkan empat gerbang manusia. BT-49 (penetapan siapa memegangnya) masih terbuka, sementara fitur 001 tidak dapat dimulai tanpa pemegang gerbang. |
| Keputusan | Anggota peneliti bidang pengembangan sistem memegang Gerbang 1 s.d. 4 untuk jalur pengembangan sistem. Bersifat sementara. |
| Alternatif | Menunggu rapat tim menetapkan BT-49 — ditolak karena menghambat seluruh urutan pembangunan `docs/D12.md` Bagian 7 tanpa mengurangi risiko apa pun; keputusan sementara ini tetap dapat digantikan. |
| Dampak | Seluruh persetujuan Gerbang 1 s.d. 4 pada fitur 001 bersandar pada keputusan ini. Bila rapat tim menetapkan pemegang lain, persetujuan yang sudah diberikan ditinjau ulang, bukan otomatis batal. |
| Pemutus | Anggota peneliti bidang pengembangan sistem |

## KB-002 · Pemilihan uv sebagai pengelola paket dan pengunci versi

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | C-09 mencatat "versi kode" sebagai bukti reproduksibilitas. Tanpa pengunci versi, pohon ketergantungan mengambang dan catatan versi kode kehilangan sebagian maknanya. Kontainerisasi dikeluarkan dari cakupan fitur 001, tetapi pengunci versi tidak. |
| Keputusan | uv dipakai sebagai pengelola paket dan pengunci versi. `uv.lock` merekam pohon transitif utuh. |
| Alternatif | Poetry — setara untuk keperluan ini. pip-tools — memerlukan lebih banyak sambungan manual. Tanpa pengunci — ditolak; membuat C-09 tidak bermakna. |
| Dampak | `Makefile` menyembunyikan pilihan ini dari alur kerja, sehingga penggantian ke Poetry menyentuh satu berkas dan tidak mengubah `AGENTS.md`. Tercatat sebagai risiko RP-03 pada `specs/001-kerangka-proyek/plan.md`: uv relatif baru dan mungkin tidak dapat dipakai pada infrastruktur UPI. |
| Pemutus | Gerbang 2 fitur 001 |

## KB-003 · Pencabutan setelan mypy disallow_any_explicit

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Setelan dipasang pada tugas A-4 dengan alasan menegakkan pemisahan tipe R-06 dan ADR-13. Alasan itu keliru: setelan tersebut hanya melarang kata `Any` ditulis pada kode sendiri, dan yang menegakkan R-06 adalah `strict`. Yang ia lakukan adalah menolak `pydantic.BaseModel`, karena tanda tangan pydantic memuat `Any`. |
| Keputusan | Setelan dicabut. `strict` dipertahankan. |
| Alternatif | Daftar pengecualian per modul — ditolak; ia bertambah setiap kali model baru dibuat, dan daftar pengecualian yang bertambah adalah tempat pekerjaan bersembunyi, persis yang R-15 dirancang cegah pada `make compliance`. |
| Dampak | Tidak ada penurunan penegakan tipe: `strict` tetap menolak fungsi tanpa anotasi, generik tanpa parameter, dan pengembalian `Any`. Alasan pencabutan ditulis pada `pyproject.toml` agar tidak dipasang ulang. |
| Pemutus | Anggota teknis, tugas C-3 |
