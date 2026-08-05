# Spec: 014-pemeriksa-konsistensi-dokumen

| | |
|---|---|
| Kebutuhan | Tidak ada FR sistem. Melayani `docs/D00.md` Bagian 5 dan 6, prinsip AP-01 pada `docs/D04.md` |
| Dokumen terkait | D-00 Bagian 2, 5, 6, 7 · D-04 AP-01 · D-12 Bagian 5 |
| Pasal konstitusi yang menyentuh fitur ini | C-11, C-12 (sebagai perkakas, bukan sebagai sistem) |
| Urutan pembangunan | Sisipan sebelum 002; menambah satu baris pada `docs/D12.md` Bagian 7 |
| Status | Menunggu gerbang gabungan 1–3 |

## Tujuan

Setelah fitur ini ada, penyimpangan antardokumen yang selama ini hanya
tertangkap pembacaan manusia tertangkap `make check`. D-00 sudah menghasilkan
52 temuan lewat sepuluh audit manual, dan TK-45 menunjukkan batasnya: register
Bagian 2 tertinggal pada tujuh dokumen **tanpa satu pun aturan dilanggar**.
D-00 Bagian 6 mewajibkan riwayat revisi diperbarui — dan itu selalu dipenuhi.
Kewajiban memperbarui register tidak pernah dinyatakan.

Perbaikan yang benar bukan menambah imbauan melainkan menambah pemeriksaan.
Ini AP-01 diterapkan pada mekanisme kendali itu sendiri.

Manfaat terbesarnya bukan hari ini melainkan pada **AK-10** (sebelum pilot) dan
**AK-11** (sebelum naskah). Keduanya wajib, keduanya sepenuhnya manual, dan
keduanya dijalankan ketika waktu paling sempit.

## Di luar cakupan

Tegas. Batas ini yang menjaga pemeriksa tetap dipakai alih-alih dimatikan.

- **Klaim jumlah dalam prosa** — "52 temuan", "enam belas dokumen". Memeriksanya
  menuntut penafsiran kalimat, dan penafsiran yang keliru menghasilkan
  kebisingan. Ditangani manusia pada audit.
- **Kepemilikan fakta tunggal** (D-00 Bagian 3) — pertanyaan semantik, bukan
  pertanyaan bentuk.
- **Kecocokan isi antardokumen** — misalnya apakah ambang pada D-07 sama dengan
  yang dirujuk D-08. Ini pekerjaan uji tujuh pertanyaan, bukan pekerjaan mesin.
- **Rentang kode usang** seperti "C-01 s.d. C-07". Menangkapnya menuntut
  mengetahui rentang mana yang dimaksud; kekeliruannya akan menyalak pada
  kutipan sejarah yang sah.
- **Perubahan isi dokumen mana pun.** Pemeriksa melapor, tidak memperbaiki.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | **JIKA** versi pada kepala sebuah dokumen berbeda dari versi dokumen itu pada register `docs/D00.md` Bagian 2, **MAKA** `make check` **HARUS** gagal |
| R-02 | **JIKA** versi pada kepala sebuah dokumen berbeda dari versi pada baris teratas riwayat revisinya sendiri, **MAKA** `make check` **HARUS** gagal |
| R-03 | **JIKA** sebuah dokumen terdaftar pada register tetapi berkasnya tidak ada di `docs/`, **MAKA** `make check` **HARUS** gagal |
| R-04 | **JIKA** sebuah berkas ada di `docs/` tetapi tidak terdaftar pada register, **MAKA** `make check` **HARUS** gagal |
| R-05 | **JIKA** kode `TK-xx` atau `ADR-xx` dirujuk sebuah dokumen tetapi tidak memiliki definisi di mana pun, **MAKA** `make check` **HARUS** gagal |
| R-06 | Pemeriksa **HARUS** melaporkan berkas dan nomor baris setiap temuan |
| R-07 | Pemeriksa **TIDAK BOLEH** mengubah berkas mana pun |
| R-08 | **JIKA** register tidak dapat diurai dari `docs/D00.md`, **MAKA** pemeriksa **HARUS** gagal, bukan melaporkan bersih |

R-08 mengikuti pelajaran yang berulang pada fitur 001: pemeriksa yang tidak
dapat membaca bahannya lalu melaporkan bersih adalah laporan palsu, dan
laporan palsu menghentikan kewaspadaan.

## Keadaan yang wajib ditangani

**Tidak berlaku.** Fitur ini tidak memiliki antarmuka pengguna.

## Kriteria penerimaan

- [ ] R-01 s.d. R-08 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Setiap pemeriksa punya **pelanggaran buatan** yang wajib tertangkap
- [ ] Pemeriksa diuji mutasi terhadap dokumen sebenarnya: versi diubah secara buatan pada satu dokumen → `make check` gagal
- [ ] Dijalankan terhadap `docs/` yang sebenarnya → bersih
- [ ] Tidak ada ketergantungan baru (C-12)
- [ ] Cakupan tidak turun dari 98,9% (C-11)
- [ ] `docs/D12.md` Bagian 7 memuat baris fitur ini

## Pertanyaan terbuka

**Tidak ada.** Fitur ini dapat diserahkan ke agen.

Empat temuan AK-12 yang terbuka — TK-40, TK-41, TK-42, TK-44 — tidak
menyentuh fitur ini. Ketiga yang pertama menghambat fitur 002, 005, 008, dan
009; yang keempat adalah penyelarasan rumusan yang menunggu keputusan pemilik
dokumen.
