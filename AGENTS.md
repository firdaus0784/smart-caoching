# AGENTS.md

Sistem Smart-Coaching Adaptif berbasis NLP untuk kepala sekolah dasar.
Penelitian Hibah UPI, siklus 2026, target TKT 3. Bahasa: Indonesia.

Spesifikasi lengkap ada di `docs/`. Baca `docs/00-INDEKS.md` untuk peta.

## Urutan prioritas

Bila instruksi bertabrakan, ikuti urutan ini. Jangan pernah membalik urutannya.

1. **Kepatuhan** — `constitution.md` pasal C-01 s.d. C-20
2. **Kebenaran** — spesifikasi fitur di `specs/`
3. **Cakupan uji** — tidak boleh turun
4. **Kecepatan** — terakhir, selalu

Jika sebuah tugas tidak dapat diselesaikan tanpa melanggar 1–3: berhenti, tulis apa yang menghalangi, tanya. Jangan cari jalan pintas.

## Alur kerja

Satu fitur = satu folder di `specs/nnn-nama/`.

```
spec.md  →  [GERBANG 1]  →  plan.md  →  [GERBANG 2]
         →  tasks.md  →  [GERBANG 3]  →  kode  →  [GERBANG 4]
```

- Jangan menulis kode sebelum `tasks.md` disetujui manusia.
- Jangan mengubah `spec.md` saat implementasi. Ajukan perubahan, tunggu.
- Satu tugas dari `tasks.md` = satu commit.
- Tulis uji lebih dulu, lalu implementasi.

## Perintah

```bash
make setup        # pasang ketergantungan
make test         # seluruh uji
make test-unit    # cepat, jalankan sebelum tiap commit
make lint         # linter + format
make check        # V-01 s.d. V-06, wajib lulus sebelum commit
make compliance   # periksa pasal C-01 s.d. C-20
```

Jalankan `make check` sebelum menyatakan tugas selesai. Bukan `make test` saja.

## Arsitektur

```
src/kamus/      enum kamus data D-14 Bagian 5; tidak mengimpor apa pun
src/api/        FastAPI, satu-satunya titik masuk, kendali peran di sini
src/nlp/        NER, klasifikasi, praproses, anonimisasi
src/rag/        pengambilan, penyusunan jawaban, validator
src/ingest/     empat kanal, penyaringan, antrean kurasi
src/llm/        pembungkus tunggal semua pemanggilan model
src/penyimpanan/ akses penyimpanan, kredensial per area
src/pengguna/    profil, prioritas manajerial, persetujuan penelitian
src/logbook/    penulis logbook tambah-saja; jalur tunggal menulis ke `logbook/`
web/            React PWA
tests/
logbook/        D-10, diisi tiap percobaan
```

Aturan arah: `api` boleh memanggil `nlp`, `rag`, `ingest`. Tidak sebaliknya.
`ingest` boleh memanggil `nlp`, satu jurusan — `nlp` tidak memanggil `ingest`.
Tepi itu ada karena pendeteksi data pribadi tinggal di `nlp` sedangkan yang
menjalankannya gerbang di `ingest`; ia dituliskan agar impornya terbaca sebagai
rancangan, bukan sebagai kebiasaan yang tidak dijelaskan dokumen mana pun.
`rag` boleh memanggil `nlp`, satu jurusan — `nlp` tidak memanggil `rag`.
Tepi kedua ini ada karena D-07 Bagian 3.3 menuntut BM25 bekerja atas hasil
praproses Bahasa Indonesia (FR-B03), dan praproses tinggal di `nlp`. Arah
sebaliknya terlarang dengan alasan yang sejajar: `nlp` yang memanggil `rag`
membuat praproses bergantung pada indeks yang praproses itu sendiri isi.
`ingest` boleh memanggil `llm`, satu jurusan. Tepi ini sudah ada sejak fitur
002 tanpa pernah dituliskan; ia ditemukan pada fitur 008 dan dicatat di sini
alih-alih dibiarkan menjadi kebiasaan tak berdokumen.
`pengguna` boleh memanggil `nlp` dan `kamus`, satu jurusan — `nlp` tidak
memanggil `pengguna`. Tepi itu ada karena dua hal yang `src/pengguna/` butuh
sudah bertempat tinggal di `nlp`: `KategoriMasalah` bagi prioritas manajerial
(FR-A03), dan pendeteksi data pribadi FR-B04 bagi bidang teks bebas (KM-03).
Arah sebaliknya terlarang dengan alasan yang sejajar dengan tepi `rag → nlp`:
`nlp` yang memanggil `pengguna` membuat praproses bergantung pada profil orang
yang teksnya sedang diproses.

`src/kamus/` boleh diimpor siapa pun dan **tidak mengimpor apa pun dari `src/`**.
Ia lapisan di bawah `src/penyimpanan/`. Isinya enum milik `docs/D14.md` Bagian
5 — bukan milik lapisan mana pun, dan itu sebabnya ia berdiri sendiri:
`IndeksTujuan` sempat ditulis dua kali karena tidak punya rumah.
Semua pemanggilan model lewat `src/llm/`. Tanpa pengecualian — ini yang mencatat versi.
Semua akses penyimpanan lewat `src/penyimpanan/`. Tanpa pengecualian — ini yang
menegakkan C-03. Ia lapisan di bawah keempatnya, bukan sejajar: `rag` membaca
korpus dan `ingest` menulis karantina, keduanya melaluinya dengan kredensial
berbeda.
Semua penulisan catatan percobaan lewat `src/logbook/`. Tanpa pengecualian —
ini yang menegakkan C-09 dan sifat tambah-saja; permukaannya sengaja tidak
menyediakan cara mengubah atau menghapus baris. Ia sudah diimpor lima lapisan
sejak fitur 002 tanpa pernah tercatat di sini, dan ketiadaannya ditemukan
pemeriksa arah pada fitur 009 — bukan oleh mata.

## Batas

Jangan lakukan hal berikut. Bila tampak perlu, berarti spesifikasinya salah — tanya.

- Menambah rute yang tidak ada di `docs/D14.md` Bagian 3
- Menambah bidang pada tanggapan `/api/v1/tanya`
- Mengubah daftar nilai enum
- Menyetel ambang RAG, kecukupan bukti, atau validator
- Memberi sistem kemampuan bertindak: pemanggilan alat, akses tulis dari `src/rag/`, pengiriman keluar
- Menempatkan konten hasil pengambilan pada posisi instruksi permintaan LLM
- Membuat tabel poin, lencana, papan peringkat, atau pertemanan
- Membangun fitur pada `docs/D01.md` Bagian 4.2 (gamifikasi, mobile native, personalisasi, peer mentoring, integrasi Dapodik)
- Menambah ketergantungan tanpa persetujuan
- Menulis data pribadi ke log
- Menyentuh `logbook/` selain menambah baris — L1, L2, L4, L7 sama terlindunginya.
  Menyunting atau menghapus baris yang sudah ada dilarang, termasuk untuk memperbaikinya
- Menulis ulang riwayat git: `rebase`, `commit --amend`, `push --force` pada branch bersama

## Gaya

Hanya yang berbeda dari kebiasaan umum:

- Indeks **karakter**, bukan token, untuk rentang anotasi
- Waktu disimpan UTC
- Enum sebagai tipe, bukan string bebas
- Pesan galat ke pengguna: bahasa Indonesia, ≤ 20 kata, tanpa istilah teknis, tanpa kode galat
- Nama tabel dan bidang: Bahasa Indonesia, sesuai `docs/D14.md` Bagian 5

## Selesai

Sebuah tugas selesai bila seluruhnya benar:

- [ ] `make check` lulus
- [ ] Uji ditulis sebelum implementasi dan menguji perilaku, bukan implementasi
- [ ] Cakupan uji tidak turun
- [ ] Tidak ada pelanggaran `constitution.md`
- [ ] Setiap berkas berubah dapat ditelusuri ke kode kebutuhan (FR-xx, NFR-xx)
- [ ] Pesan commit menyebut spec dan kode kebutuhan

Format commit:
```
feat(rag): validator sitasi VS-08

Ref: specs/008-validator/spec.md
Kebutuhan: FR-F15, VS-08
```

## Bila ragu

Bertanya lebih baik daripada menebak. Tulis pertanyaan dan berhenti.
Jangan lanjut diam-diam dengan asumsi — asumsi yang salah pada sistem ini
berakhir pada arahan keliru kepada kepala sekolah.

## Peta dokumen

| Butuh tahu | Baca |
|---|---|
| Kebutuhan berkode | `docs/D01.md` |
| Pengguna dan alur | `docs/D02.md` |
| Skema label anotasi | `docs/D03.md` |
| Keputusan arsitektur | `docs/D04.md` |
| Layar dan mikrokopi | `docs/D05.md` |
| Kanal sumber dan kurasi | `docs/D06.md` |
| RAG dan validator | `docs/D07.md` |
| Prosedur uji | `docs/D08.md` |
| Ancaman dan kendali | `docs/D13.md` |
| Rute dan kamus data | `docs/D14.md` |
