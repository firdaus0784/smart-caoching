# Plan: 015-praproses-ocr-dan-data-pribadi

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 6 Agustus 2026 |
| Status | **Lolos Gerbang 2** — 6 Agustus 2026. Kedua pertanyaan diputus (KB-018). Menunggu `tasks.md` dan Gerbang 3 |
| Ketergantungan baru | Lima, disetujui KB-017 |
| Pertanyaan yang menuntut putusan Anda | **Dua, keduanya sudah diputus** — Bagian 1 dan Bagian 6; putusannya pada Bagian 9 |

---

## 1 · Letak modul — pertanyaan pertama

`AGENTS.md` sudah memberi tempat bagi keduanya, dan pembagiannya jelas:

| Pekerjaan | Direktori menurut `AGENTS.md` |
|---|---|
| Pembacaan berkas, OCR | `src/ingest/` — "empat kanal, penyaringan, antrean kurasi" |
| Praproses, anonimisasi | `src/nlp/` — "NER, klasifikasi, praproses, anonimisasi" |

Sampai di situ tidak ada yang perlu diputuskan. **Yang perlu diputuskan adalah
arah pemanggilannya.**

Pendeteksi data pribadi berada di `src/nlp/`, tetapi yang menjalankannya adalah
gerbang di `src/ingest/`. Aturan arah pada `AGENTS.md` berbunyi: "`api` boleh
memanggil `nlp`, `rag`, `ingest`. Tidak sebaliknya." Ia **tidak menyebut**
apakah `ingest` boleh memanggil `nlp`.

Diamnya aturan bukan izin. Fitur 002 sudah sekali menemui keadaan serupa —
`src/penyimpanan/` tidak ada pada daftar arsitektur — dan jalan keluarnya
adalah menambahkannya pada `AGENTS.md` di Gerbang 2, bukan memutuskannya
diam-diam saat menulis kode.

| | Pilihan | Akibat |
|---|---|---|
| **A** | `ingest` boleh memanggil `nlp`; satu baris ditambahkan pada aturan arah `AGENTS.md` | Pendeteksi ada di tempat yang `AGENTS.md` tetapkan. Menambah satu tepi berarah pada arsitektur, dan tepi itu wajib satu jurusan — `nlp` tidak boleh memanggil `ingest` |
| **B** | Pendeteksi diletakkan di `src/ingest/`, dekat gerbang yang memakainya | Tanpa tepi baru. Tetapi `AGENTS.md` menempatkan anonimisasi di `nlp`, sehingga fitur 004 kelak menemukan pendeteksi di tempat yang tidak disebut dokumen mana pun |
| **C** | Gerbang menerima pendeteksi sebagai parameter; yang menyambungkan keduanya adalah `src/api/` | Tanpa tepi baru dan tanpa memindahkan apa pun. Tetapi `src/api/` belum ada — ia fitur 009 — sehingga sampai saat itu penyambungnya adalah uji, dan jalur sesungguhnya belum pernah dijalankan |

**Saran saya: A.** Gerbang fitur 002 sudah menerima pemeriksa pola sebagai
parameter dengan nilai bawaan, dan bentuk yang sama berlaku di sini — sehingga
A dan C sebenarnya sama dari sisi kode, dan yang membedakan hanya di mana nilai
bawaannya diimpor. Menuliskan tepi `ingest → nlp` pada `AGENTS.md` membuat
kenyataan itu terbaca, alih-alih berdiri sebagai impor yang tidak dijelaskan
dokumen mana pun.

B ditolak karena memecah anonimisasi menjadi dua tempat pada saat fitur 004
membangun sisanya.

---

## 2 · Bentuk yang menegakkan C-10

Ini bagian terpenting rencana, dan ia bukan pilihan melainkan konsekuensi.

Tiga bentuk teks yang **tidak** boleh tertukar:

| Bentuk | Milik | Indeks karakter |
|---|---|---|
| Berkas asli | `src/penyimpanan/` | — |
| **Teks kanonik** — hasil ekstraksi atau OCR | `src/ingest/` | **Rujukan tunggal.** Seluruh rentang anotasi, temuan pendeteksi, dan temuan pola adversarial menunjuk ke sini |
| Keluaran praproses — token, stem, tanpa stop-word | `src/nlp/` | **Tidak punya indeks sendiri.** Tiap token membawa rentang pada teks kanonik |

Stemming mengubah panjang kata; "menugaskan" menjadi "tugas". Token yang hanya
menyimpan stem kehilangan tempatnya, dan C-10 beserta D-03 Bagian 15 menjadi
tidak dapat ditegakkan.

Maka `Token` membawa **empat** hal: permukaan asli, stem, `mulai`, `akhir`.
Bukan tiga. Uji yang menyatakan sifat ini berbunyi: bagi setiap token,
`teks_kanonik[token.mulai:token.akhir] == token.permukaan`. Dinyatakan sebagai
sifat atas seluruh token, bukan sebagai satu kasus.

Kegunaannya juga dibatasi tegas pada uraian modulnya: keluaran praproses untuk
**pencarian**, tidak untuk menyiapkan bahan anotasi.

---

## 3 · Antarmuka, dan bagaimana OCR diuji tanpa memasang apa pun

Mengikuti ADR-12 yang sudah terbukti dua kali:

```
Pengekstrak (abstrak)          Pemeriksa data pribadi (abstrak)
  ├── PengekstrakPdf             └── PendeteksiPola   ← satu-satunya wujud
  ├── PengekstrakDocx
  ├── PengekstrakXlsx
  └── PengekstrakOcr  ←── membungkus pytesseract
```

`PengekstrakOcr` adalah **satu-satunya** tempat `pytesseract` diimpor, dengan
alasan yang sama dengan C-08 bagi `src/llm/`: ia yang mencatat versi mesin dan
versi berkas model ke `logbook/` (R-05). Impor di tempat lain akan melewati
pencatatan itu, dan pemeriksa untuk larangan ini dibangun mengikuti pola
`impor_penyedia.py` yang sudah ada.

**Uji tidak menuntut Tesseract terpasang.** Seluruh uji perilaku berjalan
terhadap pengekstrak tiruan deterministik. Satu uji terpisah — ditandai
sehingga dapat dilewati — menjalankan mesin sungguhan, dan itu satu-satunya
yang menuntut pemasangan.

Keadaan "mesin OCR tidak terpasang" pada `spec.md` diuji **tanpa** mesin
terpasang: pembungkusnya wajib gagal tegas saat penyalaan, dan itu justru
keadaan bawaan lingkungan uji.

---

## 4 · Bahan uji

Berkas PDF, DOCX, dan XLSX kecil disimpan pada `tests/bahan/`. Isinya karangan
menyerupai dokumen sekolah — **tidak ada data pribadi sungguhan**, dan nomor
yang dipakai dibuat agar tidak sah sebagai NIK sungguhan sambil tetap
mencocoki pola.

Berkas DOCX dan XLSX dibangkitkan sekali dengan `python-docx` dan `openpyxl`
lalu dikomit. Membangkitkannya tiap kali uji berjalan berarti menguji pustaka
terhadap dirinya sendiri.

PDF dikomit sebagai berkas tetap. Empat berkas: satu berlapis teks, satu
pindaian tanpa lapisan teks, satu terkunci kata sandi, satu rusak. Keempat
keadaan pada `spec.md` menuntut bahannya ada.

---

## 5 · Cara C-12 diperiksa mesin

`ketergantungan-disetujui.toml` bertambah lima nama pada `langsung`, dan pohon
`terkunci` disusun ulang dari `uv.lock` **setelah** pemasangan, lalu dicatat.
Ini satu-satunya perubahan berkas itu sejak fitur 001, dan ia keputusan manusia
— berkasnya menyatakan hal itu di kepalanya.

Bagian `[sistem]` ditambahkan (KB-017):

```toml
[sistem.tesseract]
versi = "…"          # keluaran `tesseract --version`
berkas_model = "ind.traineddata"
sidik = "sha256:…"
```

Pemeriksa R-18 diperluas membandingkannya. Bila Tesseract tidak terpasang,
pemeriksa **melapor "belum dapat diperiksa"**, bukan "lulus" — pelajaran
TA-01 diterapkan pada perkakas: laporan bersih yang tidak memeriksa apa pun
lebih berbahaya daripada tidak ada laporan.

---

## 6 · Pertanyaan kedua: apa yang diperiksa saat berkas model tidak ada

`spec.md` sudah menetapkan bahwa keberadaan `ind.traineddata` diperiksa sebagai
tugas pertama fase OCR. Yang belum ditetapkan adalah apa yang terjadi bila ia
tidak dapat diperoleh sama sekali di lingkungan penelitian.

| | Pilihan | Akibat |
|---|---|---|
| **A** | Fase OCR berhenti; `pytesseract` dicabut dari daftar; FR-B02 menjadi butir terbuka baru | Jujur, dan tiga kebutuhan lain tetap selesai. FR-B02 berprioritas W tidak terpenuhi pada siklus 2026 |
| **B** | OCR dibangun dengan model bahasa Inggris sebagai sementara | **Saya menyarankan menolak.** Dokumen berbahasa Indonesia yang di-OCR dengan model Inggris menghasilkan teks yang terbaca seperti teks — dan korpus yang rusak diam-diam lebih buruk daripada korpus yang kosong |
| **C** | Cari mesin OCR lain | Kembali ke Gerbang 2 dengan usulan ketergantungan baru; bukan keputusan yang dapat diambil sekarang tanpa bahan |

**Saran saya: A**, dan pertanyaan ini diputus **sekarang** meski keadaannya
belum tentu terjadi. Keputusan yang diambil saat tenggat sudah dekat dan
pekerjaan sudah separuh jalan hampir selalu B.

---

## 7 · Rencana uji mutasi

| Yang dimutasi | Yang wajib gagal |
|---|---|
| `Token` kehilangan `mulai`/`akhir` | Uji sifat pemetaan balik (Bagian 2) |
| Pengekstrak mengembalikan teks kosong alih-alih melempar galat pada berkas rusak | Uji R-02 dan R-06 |
| `pytesseract` diimpor dari modul kedua | Pemeriksa impor tunggal (Bagian 3) |
| Satu nama dihapus dari `ketergantungan-disetujui.toml` | R-18 pada `make check` |
| Pendeteksi menyalin nilai temuan ke pesan galat | Uji R-11 |

---

## 8 · Ketergantungan

Lima langsung, disetujui KB-017: `pypdf`, `python-docx`, `openpyxl`,
`PySastrawi`, `pytesseract`. Tiga transitif baru: `lxml`, `et-xmlfile`,
`Pillow`. Satu ketergantungan sistem: Tesseract beserta `ind.traineddata`.

Tidak ada tambahan di luar daftar itu. Bila implementasi menemukan satu pun
diperlukan, pekerjaan berhenti dan diajukan — bukan dipasang lalu dilaporkan.

---

## 9 · Keputusan Gerbang 2

Keduanya diputus pemegang gerbang pada 6 Agustus 2026, tercatat KB-018.

**1 · Pilihan A — `ingest` boleh memanggil `nlp`.** `AGENTS.md` bertambah satu
kalimat pada aturan arah, menyatakan tepi itu ada dan **satu jurusan**: `nlp`
tidak memanggil `ingest`. Pendeteksi tetap di `src/nlp/` sebagaimana `AGENTS.md`
menempatkan anonimisasi, dan gerbang di `src/ingest/` menerimanya sebagai
parameter dengan nilai bawaan — bentuk yang sama dengan pemeriksa pola pada
fitur 002.

Pilihan B ditolak karena memecah anonimisasi menjadi dua tempat justru pada saat
fitur 004 membangun sisanya. Pilihan C ditolak karena `src/api/` belum ada,
sehingga penyambungnya akan menjadi uji dan jalur sesungguhnya tidak pernah
dijalankan.

**2 · Pilihan A — fase OCR berhenti bila berkas model tidak dapat diperoleh.**
`pytesseract` dicabut dari daftar ketergantungan, dan FR-B02 menjadi butir
terbuka bagi rapat tim. Tiga kebutuhan lain tetap selesai.

Pilihan B — memakai model bahasa Inggris sebagai sementara — **ditolak tegas**.
Dokumen berbahasa Indonesia yang di-OCR dengan model Inggris menghasilkan teks
yang terbaca seperti teks, dan korpus yang rusak diam-diam lebih buruk daripada
korpus yang kosong. Keputusan ini diambil sekarang, sebelum keadaannya terjadi,
justru karena keputusan yang diambil saat tenggat dekat hampir selalu jatuh
pada B.

Sesudah ini `tasks.md` disusun dan diajukan ke Gerbang 3. Tidak ada kode
ditulis sebelum Gerbang 3 dilewati.
