# Tasks: 001-kerangka-proyek

Ditinjau manusia sebelum kode ditulis. Satu tugas = satu commit.

Tugas atomik: dapat diselesaikan dan diuji sendiri, tidak menggantung.

| | |
|---|---|
| Spec | `spec.md` (lolos Gerbang 1) |
| Plan | `plan.md` (lolos Gerbang 2) |
| Status | Menunggu Gerbang 3 |
| Jumlah tugas | **34** — melampaui ambang ±30; lihat catatan pada bagian Urutan |

## Kewajiban dari Gerbang 2

| Kode | Kewajiban | Tugas |
|---|---|---|
| G2-1 | Sikap menolak ketergantungan yang dapat digantikan pustaka baku dipertahankan | berlaku terus, bukan tugas |
| G2-2 | uv dicatat sebagai keputusan berjalan L4 | E-4 |
| G2-3 | Kelima paket beserta versi terkunci dicatat sebagai titik nol R-18 | E-5 |
| G2-4 | BT-14 dinaikkan menjadi **ADR-12** pada D-04, beserta alternatif ditolak dan RP-04 | E-2 |
| G2-5 | Permintaan terstruktur dan pembatasan konstruksi `Instruksi` menjadi **ADR-13** | E-2 |
| G2-6 | Larangan RP-05 ditulis pada bagian Batas `AGENTS.md` | A-7 |
| G2-7 | Tiga belas pasal belum-dapat-diperiksa disalin ke `logbook/` sebagai tagihan | E-6 |

---

## Daftar periksa Gerbang 4

**Ditulis sebelum implementasi dimulai**, memenuhi syarat (a) pada KM-002.
Fitur 001 diverifikasi manusia terhadap daftar ini karena `make check` dan
`make compliance` adalah luarannya sendiri (KM-002). Pengecualian berlaku
**hanya** untuk fitur 001.

### Luaran yang wajib ada dan berfungsi — syarat (c) KM-002

- [ ] G4-01 · `make setup` berhasil pada lingkungan bersih
- [ ] G4-02 · `make check` ada dan **gagal** ketika V-01 s.d. V-06 dilanggar secara buatan — dibuktikan satu per satu, bukan sekaligus
- [ ] G4-03 · `make compliance` ada, menampilkan **kedua puluh** pasal tepat sekali
- [ ] G4-04 · `make compliance` gagal ketika satu pasal dihapus dari daftar
- [ ] G4-05 · `make compliance` gagal ketika keluarannya kosong (R-16)
- [ ] G4-06 · Tujuh pasal berstatus `LULUS`; tiga belas berstatus `BELUM-DAPAT-DIPERIKSA` dan **masing-masing menyebut fitur penguncinya**

### Kendali yang menjadi alasan fitur ini ada

- [ ] G4-07 · Uji penanda C-18 lulus pada **ambang nol**: untai unik dari `Data.teks` tidak muncul pada bidang instruksi permintaan
- [ ] G4-08 · Uji C-18 dengan muatan bergaya serangan `docs/D13.md` Bagian 1 lulus
- [ ] G4-09 · Tanda tangan `pembungkus.panggil` dan `AdaptorDasar` **tidak memuat** parameter alat, pendaftaran fungsi, atau keluaran yang dapat dieksekusi (C-17)
- [ ] G4-10 · Pemeriksa AST menggagalkan impor pustaka penyedia di luar `src/llm/` (C-08)
- [ ] G4-11 · Pemeriksa AST menggagalkan konstruksi `Instruksi` di luar `src/llm/instruksi.py` (ADR-13)
- [ ] G4-12 · Pemanggilan tanpa salah satu dari lima bidang versi ditolak; bidang belum berlaku berisi `belum-berlaku`, bukan kosong (C-09, R-12)

### Mutu dan kejujuran uji

- [ ] G4-13 · R-01 s.d. R-18 masing-masing punya uji yang lulus
- [ ] G4-14 · Setiap uji **pernah gagal** sebelum implementasinya — dibuktikan dari riwayat commit, bukan pernyataan
- [ ] G4-15 · **Tidak ada pemanggilan jaringan** selama seluruh rangkaian uji
- [ ] G4-16 · Cakupan modul inti tercatat sebagai penanda dasar bagi C-11

### Rekaman yang tidak boleh ditunda

- [ ] G4-17 · KM-001 dan keputusan uv tercatat pada `logbook/L4`
- [ ] G4-18 · KM-002 tercatat pada `logbook/L7` beserta alasan dan pemberi izin
- [ ] G4-19 · Titik nol R-18 — kelima paket dan versi terkuncinya — tercatat pada `logbook/L2`
- [ ] G4-20 · Daftar tiga belas pasal tersalin ke `logbook/` sebagai tagihan yang dapat dilacak penyusutannya
- [ ] G4-21 · ADR-12 dan ADR-13 ada pada `docs/D04.md`
- [ ] G4-22 · TK-39 diterapkan: `docs/D14.md` naik ke 0.2, tercatat pada `docs/D00.md` Bagian 7
- [ ] G4-23 · `docs/D12.md` Bagian 7 diperbarui; temuan AK-12 tercatat
- [ ] G4-24 · `AGENTS.md` bagian Batas memuat larangan RP-05
- [ ] G4-25 · Setiap berkas berubah dapat ditelusuri ke kode kebutuhan

---

## Fase A · Perancah dan lapisan tata kelola

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | Struktur direktori `src/`, `tests/`, `perkakas/`, `logbook/`, `docs/`, `specs/_template/`; `.gitignore` | Uji struktur: direktori wajib ada | R-01, R-02 | [ ] |
| A-2 | Salin `AGENTS.md`, `CLAUDE.md`, `constitution.md` ke akar; salin ketiga templat ke `specs/_template/` | Uji: berkas ada; `constitution.md` memuat C-01 s.d. C-20 tepat sekali | R-01, R-02 | [ ] |
| A-3 | Salin `00-INDEKS.md` dan `D00.md` s.d. `D14.md` ke `docs/` | Uji: keenam belas berkas ada dengan nama pendek | R-01 | [ ] |
| A-4 | `pyproject.toml`: Python 3.12, lima ketergantungan disetujui, konfigurasi ruff/mypy/pytest | Uji: ketergantungan langsung **tepat sama** dengan daftar disetujui — lebih maupun kurang menggagalkan | R-18 | [ ] |
| A-5 | Kunci versi: `uv.lock` + `ketergantungan-disetujui.toml` sebagai titik nol | Uji: himpunan paket pada lock dan daftar disetujui identik | R-18 | [ ] |
| A-6 | `Makefile`: enam sasaran `setup`, `test`, `test-unit`, `lint`, `check`, `compliance` — kerangka, isi diisi Fase B | Uji: keenam sasaran ada dan dapat dipanggil | R-14 | [ ] |
| A-7 | Tambahkan larangan RP-05 ke bagian Batas `AGENTS.md`: penyuntingan `logbook/` selain menambah baris, dan penulisan ulang riwayat git | Uji: kedua larangan ada pada bagian Batas | G2-6 | [ ] |

## Fase B · Gerbang mutu — dibangun sebelum yang dijaganya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | Inti pemeriksa AST: pemuatan berkas, penelusuran impor dan konstruksi, pelaporan berposisi | Uji: pohon contoh menghasilkan daftar impor yang benar | prasyarat R-04, R-13 | [ ] |
| B-2 | Aturan: impor pustaka penyedia model di luar `src/llm/` | Uji: berkas contoh di luar `src/llm/` mengimpor pustaka penyedia → gagal | R-04, C-08 | [ ] |
| B-3 | Pemeriksa penanda placeholder pada `AGENTS.md` | Uji: berkas dengan penanda → gagal; tanpa penanda → lulus | R-03 | [ ] |
| B-4 | Isi bagian "Perintah" `AGENTS.md` dengan perintah nyata; hapus penanda placeholder | Uji: pemeriksa B-3 terhadap `AGENTS.md` nyata → lulus | R-03 | [ ] |
| B-5 | Pemeriksa ketergantungan: `uv.lock` dibanding `ketergantungan-disetujui.toml` | Uji: paket disisipkan ke lock tanpa masuk daftar → gagal | R-18, C-12 | [ ] |
| B-6 | Penanda cakupan dan pemeriksa penurunan | Uji: penanda diturunkan secara buatan → gagal | R-17, C-11 | [ ] |
| B-7 | Pemeriksa nama terlarang pada `src/`: poin, lencana, papan peringkat, pertemanan | Uji: berkas contoh bernama `lencana` → gagal | C-15 | [ ] |
| B-8 | Daftar pasal C-01 s.d. C-20 beserta status dan fitur pengunci | Uji: tepat 20 entri, tanpa duplikat; setiap `BELUM` menyebut fitur | R-15 | [ ] |
| B-9 | Pelaksana `make compliance`: tiga keadaan; gagal bila ada `GAGAL`, bila ada pasal tanpa entri, dan bila keluaran kosong | Uji: pasal dihapus → gagal. Uji: keluaran kosong → gagal | R-15, R-16 | [ ] |
| B-10 | `make check` menjalankan V-01 s.d. V-06 | Uji: setiap V dilanggar buatan satu per satu → `make check` gagal | R-14 | [ ] |

## Fase C · Penulis logbook

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Penulis tambah-saja untuk `L1-percobaan.jsonl` dan `L2-versi-artefak.jsonl` | Uji: penambahan menambah satu baris; permukaan modul tidak memuat fungsi ubah atau hapus | R-11, R-13 | [ ] |
| C-2 | Aturan AST: pembukaan berkas `logbook/` dengan mode tulis atau potong di luar `src/logbook/` | Uji: berkas contoh membuka `logbook/` dengan mode `w` → gagal | R-13 | [ ] |
| C-3 | Lima bidang versi wajib; bidang belum berlaku diisi `belum-berlaku` | Uji: bidang kosong ditolak; `belum-berlaku` diterima; bidang hilang ditolak | R-11, R-12, C-09 | [ ] |
| C-4 | Berkas `L4-keputusan.md` dan `L7-alat-bantu-ai.md` beserta bentuk entrinya | Uji: bentuk entri sesuai `docs/D10.md` Bagian 6 dan Bagian 9 | R-11 | [ ] |

## Fase D · Pembungkus model

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| D-1 | Tipe: `Peringkat`, `IndeksTujuan`, `Instruksi`, `Data`, `Konfigurasi`, `Tanggapan` | Uji: `Data` menolak peringkat di luar T1–T4; enum bertipe, bukan untai bebas | R-06 | [ ] |
| D-2 | Konstruksi `Instruksi` dibatasi pada `src/llm/instruksi.py` + aturan AST penegaknya | Uji: konstruksi `Instruksi` di berkas lain → pemeriksa gagal | R-06, ADR-13 | [ ] |
| D-3 | `AdaptorDasar`: antarmuka abstrak tanpa parameter alat | Uji: telaah tanda tangan — tidak ada parameter alat, pendaftaran fungsi, atau keluaran dapat dieksekusi | R-08, C-17 | [ ] |
| D-4 | Adaptor tiruan deterministik | Uji: masukan sama menghasilkan keluaran sama; tidak ada soket jaringan terbuka | R-10 | [ ] |
| D-5 | Pembangun permintaan terstruktur: `instruksi` dan `data` menempati bidang berbeda, tanpa penggabungan menjadi untai | **Uji penanda, ambang nol:** untai unik pada `Data.teks` tidak muncul pada bidang instruksi. Ditambah muatan bergaya serangan `docs/D13.md` Bagian 1 | R-07, C-18 | [ ] |
| D-6 | `pembungkus.panggil`: mencatat nama dan versi model, konfigurasi, waktu, biaya; menulis baris L1 | Uji: satu pemanggilan menghasilkan tepat satu baris L1 lengkap | R-05, C-08, C-09 | [ ] |
| D-7 | Galat `LAYANAN_MODEL_GAGAL` berbentuk `docs/D14.md` Bagian 4.2 | Uji: `pesan_pengguna` ≤ 20 kata, tanpa nama penyedia, kode HTTP, maupun jejak tumpukan; sebab asli hanya ke log operasional | R-09, C-13 | [ ] |

## Fase E · Penerapan keputusan pada dokumen dan rekaman

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| E-1 | TK-39: tambahkan `catatan_keberlakuan` ke `docs/D14.md` Bagian 4.1 dan tabel aturan bidangnya; naikkan D-14 ke 0.2; catat TK-39 pada `docs/D00.md` Bagian 7 dan riwayat revisi | Uji: bidang ada pada contoh dan tabel; D-00 memuat TK-39 | KM-003 | [ ] |
| E-2 | **ADR-12** (antarmuka abstrak, adaptor tiruan, alternatif ditolak, RP-04 sebagai konsekuensi) dan **ADR-13** (permintaan terstruktur, pembatasan konstruksi `Instruksi`) pada `docs/D04.md`; naikkan versi D-04 | Uji: kedua ADR ada dan memuat keempat bagian format D-04 Bagian 8 | G2-4, G2-5 | [ ] |
| E-3 | Perbarui `docs/D12.md` Bagian 7 — penugasan pasal per fitur usang karena ditulis sebelum D-13 ada; catat sebagai temuan AK-12 | Uji: baris fitur 001 memuat C-17 dan C-18; temuan tercatat | G1-2 | [ ] |
| E-4 | `logbook/L4`: KM-001 pemegang Gerbang 1–4 sementara (BT-49 tetap terbuka), dan keputusan memakai uv | Uji: kedua entri memuat ketujuh bidang D-10 Bagian 6 | KM-001, G2-2 | [ ] |
| E-5 | `logbook/L2` dan `L7`: titik nol R-18 (lima paket + versi terkunci); KM-002 beserta alasan dan pemberi izin | Uji: kelima paket tercatat dengan versi; entri L7 memuat pemberi izin | G2-3, KM-002 | [ ] |
| E-6 | Salin daftar tiga belas pasal belum-dapat-diperiksa ke `logbook/` sebagai tagihan, masing-masing dengan fitur penguncinya | Uji: tiga belas entri; setiap entri menyebut fitur | G2-7 | [ ] |

---

## Urutan

**Aturan pokok: gerbang kepatuhan dibangun sebelum hal yang dijaganya.**
Ini penerapan keputusan G1-4, dan alasannya sama dengan alasan `docs/D12.md`
menempatkan fitur 008 sebelum 009.

```
A (perancah)  →  B (gerbang mutu)  →  C (logbook)  →  D (pembungkus)  →  E (rekaman)
                      ▲                                    │
                      └──── D ditulis di bawah pengawasan ─┘
```

| Kendala | Alasan |
|---|---|
| **B mendahului C dan D** | Syarat mutlak dari G1-4. R-14 s.d. R-18 berjalan sebelum R-04 s.d. R-13 ditulis |
| **A-4, A-5 mendahului B-5** | Pemeriksa ketergantungan memerlukan lock dan daftar disetujui sebagai pembanding |
| **A-6 mendahului B-3** | `make check` harus punya kerangka sebelum pemeriksa dipasang ke dalamnya |
| **B-3 mendahului B-4** | Pemeriksa placeholder ditulis lebih dulu, baru placeholder dihapus — sehingga uji pernah gagal sebelum lulus |
| **B-1 mendahului B-2, C-2, D-2** | Ketiganya memakai inti pemeriksa AST yang sama |
| **C mendahului D** | Pembungkus menulis catatan versinya ke `logbook/`; R-05 bertemu R-11 |
| **D-1, D-2, D-3 mendahului D-5** | Permintaan terstruktur memerlukan tipe dan antarmuka adaptor lebih dulu |
| **A-5 mendahului E-5** | Titik nol R-18 hanya dapat dicatat setelah lock ada |

**Satu kejanggalan urutan yang disengaja.** Titik nol R-18 (G2-3) idealnya
dicatat pada A-5 ketika lock dibuat, tetapi penulis `logbook/` baru ada pada C-1.
Menuliskannya manual di A-5 lalu menimpanya di E-5 melanggar sifat tambah-saja.
Karena itu ia dicatat sekali di E-5, dan A-5 hanya menghasilkan berkas lock —
yang isinya tidak berubah di antara keduanya, sehingga tidak ada informasi hilang.

### Catatan jumlah tugas — memerlukan putusan Gerbang 3

Gerbang 1 menetapkan: bila tugas atomik melampaui ±30, fitur ditinjau ulang di
Gerbang 3. **Jumlahnya 34.**

Selisihnya dapat ditelusuri dan bukan pembengkakan cakupan: perkiraan ±29 pada
`plan.md` disusun **sebelum** Gerbang 2 menambahkan lima kewajiban rekaman
(ADR-12, ADR-13, L4 uv, titik nol R-18, tagihan tiga belas pasal). Kelimanya
seluruhnya berada di Fase E, dan Fase E sudah dimampatkan dari sembilan tugas
menjadi enam.

Yang perlu diketahui saat memutuskan: **alasan "jangan dipecah" pada Gerbang 1
tidak berlaku bagi Fase E.** Alasan itu adalah pembungkus tidak boleh lahir tanpa
penjaganya — hubungan antara B dan D. Fase E berisi dokumen dan rekaman, tidak
menjaga apa pun dan tidak dijaga apa pun.

Meski begitu saya menyarankan **tetap satu fitur**. Fase E adalah rekaman
keputusan yang diambil *selama* fitur ini; memindahkannya ke unit terpisah
menghidupkan kembali persis kegagalan yang diperingatkan `docs/D10.md` Bagian 1 —
catatan yang disusun belakangan, dari ingatan. Tiga puluh empat berbanding tiga
puluh adalah harga yang lebih murah daripada itu.

---

## Verifikasi akhir

- [ ] `make check` lulus
- [ ] `make compliance` lulus — dengan tiga belas pasal terdaftar sebagai belum dapat diperiksa, bukan disembunyikan
- [ ] Seluruh kebutuhan R-01 s.d. R-18 punya uji yang lulus
- [ ] Cakupan tidak turun
- [ ] Catatan percobaan ditambahkan ke `logbook/` bila menyentuh model — pada fitur ini: baris L1 dari adaptor tiruan, dan L2 titik nol ketergantungan
- [ ] **Daftar periksa Gerbang 4 (G4-01 s.d. G4-25) diperiksa manusia** — pengecualian KM-002, berlaku hanya untuk fitur 001
