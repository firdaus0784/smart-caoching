# Spec: [nnn-nama-fitur]

| | |
|---|---|
| Kebutuhan | FR-xx, NFR-xx (dari docs/D01.md) |
| Dokumen terkait | D-xx Bagian x |
| Pasal konstitusi yang menyentuh fitur ini | C-xx |

## Tujuan

Satu paragraf. Apa yang bisa dilakukan pengguna atau sistem setelah ini ada,
yang sebelumnya tidak bisa.

## Di luar cakupan

Sebutkan tegas. Ini yang membatasi penjelajahan agen.

- …
- …

## Kebutuhan (EARS)

Satu klaim per baris, dapat diuji. Pakai kata kunci HARUS / TIDAK BOLEH.

| ID | Kebutuhan |
|---|---|
| R-01 | **KETIKA** [pemicu], sistem **HARUS** [respons] |
| R-02 | **SELAMA** [keadaan], sistem **HARUS** [respons] |
| R-03 | **JIKA** [kondisi], **MAKA** sistem **TIDAK BOLEH** [tindakan] |
| R-04 | Sistem **HARUS** [perilaku tetap] |

Pola: KETIKA (peristiwa), SELAMA (keadaan berlangsung), JIKA-MAKA (kondisi
tak diinginkan), tanpa awalan (perilaku selalu berlaku).

## Keadaan yang wajib ditangani

Untuk fitur berantarmuka, seluruh tujuh keadaan D-05 Bagian 7.

| Keadaan | Perilaku |
|---|---|
| Memuat | |
| Kosong pertama kali | |
| Kosong karena habis | |
| Galat sistem | |
| Luring | |
| Antrean kirim | |
| Tidak ditemukan dasar | |

## Kriteria penerimaan

Dapat diperiksa mesin bila mungkin.

- [ ] R-01 s.d. R-nn punya uji yang gagal sebelum implementasi
- [ ] Pasal konstitusi terkait punya uji tersendiri
- [ ] …

## Pertanyaan terbuka

Tulis di sini alih-alih menebak. Fitur dengan pertanyaan terbuka tidak
diserahkan ke agen.

- …
