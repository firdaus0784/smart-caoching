# L10 · Berkas HKI

Bahan pendaftaran Hak Kekayaan Intelektual, disusun **bertahap bersama
pengembangan** — bukan dikejar menjelang pendaftaran. Kerangkanya pada
`docs/D10.md` Bagian 10A; kebutuhannya BR-10 pada `docs/D01.md`.

Pemilik isi: **ketua peneliti**. Agen menyiapkan tempat, menunjuk sumber
bahan, dan mencatat keadaan tiap komponen apa adanya — agen **tidak**
menulis deskripsi ciptaan maupun pernyataan kepemilikan.

**Ditambah, tidak disunting.** Lihat `AGENTS.md` bagian Batas.

---

## Mengapa berkas ini dibuka terlambat, dan itu dicatat di sini

D-10 menjadwalkan komponen pertamanya **Bulan 4**. Berkas ini dibuka
**23 September 2026**, hampir tiga bulan sesudahnya.

Sebabnya bukan kelalaian menyalin jadwal. Nomor yang D-10 tetapkan baginya —
L8 — sudah dipakai artefak lain sejak fitur 001, yaitu tagihan pasal belum
dapat diperiksa. Keduanya artefak yang sah; nomornya yang berimpit. Akibatnya
**ketiadaan berkas HKI tidak terbaca dari daftar berkas `logbook/`**: tempat
yang D-10 tunjuk terlihat terisi.

Lebih jauh, temuan **TK-37** sudah pernah menutup persoalan yang sama —
"dokumentasi HKI tanpa waktu mulai" — dengan tindakan berupa jadwal bertahap
pada D-10 Bagian 10. Jadwal itu kemudian tidak menunjuk berkas mana pun,
sementara status TK-37 tetap terbaca **Selesai**. Temuan yang ditutup dengan
remedi yang belakangan tidak berlaku lagi tidak menyatakan dirinya batal.

Tercatat sebagai TK-59 pada `docs/D00.md` Bagian 7.12, diputus 23 September
2026 (KB-107). Keterlambatan ini ditulis pada berkasnya sendiri, mengikuti
cara L9 menyatakan bahwa ia dibuka **mendahului** jadwalnya.

---

## 1. Keadaan tiap komponen

Diperbarui setiap kali sebuah komponen berpindah keadaan. Baris lama tetap
berdiri; perubahan ditulis pada Bagian 3.

| # | Komponen | Tenggat D-10 | Keadaan 23 September 2026 | Pemilik |
|---|---|---|---|---|
| 1 | Deskripsi ciptaan | Bulan 4 | **Belum disusun** — bahannya ada pada D-01 Bagian 1–3 dan D-04 Bagian 2–6 | Ketua peneliti |
| 2 | Uraian kebaruan | Bulan 4 | **Belum disusun** — bahannya proposisi nilai D-01 dan kebaruan tiga aspek pada proposal | Ketua peneliti |
| 3 | Manual penggunaan sistem | Bulan 6 | **Belum dapat disusun** — D-05 menginventarisasi layar, tetapi `web/` masih nol baris | Ketua peneliti, sesudah fitur 013 |
| 4 | Dokumentasi teknis | Bulan 6 | **Bahannya sudah ada dan mutakhir** — D-04 arsitektur, D-07 spesifikasi RAG, `AGENTS.md` peta lapisan. Belum dirangkum menjadi bentuk HKI | Ketua peneliti |
| 5 | Tangkapan layar sistem berjalan | Bulan 6 | **Belum dapat diambil** — antarmuka belum ada. Lapisan HTTP berjalan dan dapat ditembak lewat `make jalan`, tetapi tangkapan layar menuntut layar | Ketua peneliti, sesudah fitur 013 |
| 6 | Daftar artefak yang didaftarkan | Bulan 7 | **Sebagian dapat disusun sekarang** — prototipe dan ontologi ada; model dan korpus belum | Ketua peneliti |
| 7 | Surat pernyataan kepemilikan | Bulan 7 | **Belum disusun** — bergantung keputusan BT-06 yang belum diambil | Ketua peneliti |

**Empat dari tujuh komponen tertahan hal yang sama**: antarmuka belum ada,
model belum dilatih, korpus belum selesai. Ketiganya tertahan masukan dari
luar, bukan oleh pekerjaan pemrograman.

---

## 2. Artefak yang sudah ada dan dapat didaftarkan

Disusun dari keadaan repositori pada 23 September 2026, bukan dari rencana.
Ia bahan bagi komponen 6, **bukan** komponen 6 itu sendiri.

| Artefak | Keadaan | Letak |
|---|---|---|
| Kode sistem | 20 dari 25 fitur lolos Gerbang 4; `make check` lulus enam gerbang | `src/`, `perkakas/` |
| Skema ontologi dan ekspor JSON-LD | Fitur 005 lolos Gerbang 4 | `src/` fitur 005 |
| Isi ontologi | **Belum** — putaran pengisian berikutnya menunggu putusan (KB-075) | — |
| Model NER dan klasifikasi | **Belum** — fitur 017 menunggu korpus teranotasi dan ET-01 | — |
| Korpus teranotasi | **Belum** — datasheet dibuka, pengumpulan tertahan ET-01 | `logbook/L9` |
| Basis pengetahuan dan indeks | Kerangka ada, isi kosong | `perkakas/basis_data/` |
| Antarmuka pengguna | **Belum** — `web/` nol baris | — |

---

## 3. Riwayat pemutakhiran

| Tanggal | Perubahan | Pemicu |
|---|---|---|
| 23 September 2026 | Berkas dibuka; keadaan ketujuh komponen dicatat apa adanya; keterlambatan pembukaan dinyatakan | TK-59, KB-107 |
