"""Ambang kesepakatan dan kualifikasi — **satu-satunya tempat angkanya ada**.

Dimiliki D-03, bukan berkas ini. Yang ada di sini adalah salinan yang dijaga
uji: `tests/nlp/test_ambang_kesepakatan.py` membaca `docs/D03.md` sungguhan
dan membandingkannya, sehingga salinan yang menyimpang menjatuhkan gerbang
alih-alih menunggu seseorang menyadarinya.

**C-16 melarang menyetel ambang di luar prosedur kalibrasi D-07 BT-29.** Itu
alasan modul ini ada, dan alasannya perlu dibaca sebelum ada yang mengubah
satu angka pun di bawah:

> Bila tingkat penolakan validator terlalu tinggi, perbaiki pengambilan —
> jangan longgarkan validator.

Bentuk yang sama berlaku di sini. Kesepakatan antar-anotator yang tidak
mencapai ambang ditangani dengan **mempertajam pedoman dan menganotasi ulang**
(D-03 Bagian 11.1 kolom Tindakan), bukan dengan menurunkan ambangnya. Yang
kedua menghasilkan angka yang memenuhi syarat dan korpus yang tidak berubah
mutunya — lalu angka itu masuk naskah.

Menaruh seluruhnya pada satu berkas bukan kerapian. Ambang yang tertulis di
tiga tempat akan disetel di salah satunya, dan yang menyetelnya tidak akan
merasa sedang menyetel ambang: ia merasa sedang memperbaiki satu uji yang
gagal. Dengan satu tempat, perubahannya terlihat pada diff sebagai apa
adanya, dan uji terhadap D-03 menjatuhkannya.

## Dua kelompok, dan keduanya tidak boleh disamakan

| Kelompok | Menilai apa | Sumber |
|---|---|---|
| Ambang batch | Dua anotator terhadap **satu sama lain** | D-03 Bagian 11 |
| Ambang kualifikasi | Satu anotator terhadap **kunci jawaban** adjudikator | D-03 Bagian 13 |

Ambang kualifikasi F1 longgar lebih rendah daripada ambang batch, dan itu
bukan kelalaian. Keduanya mengukur hal yang berbeda terhadap pembanding yang
berbeda; menyamakannya menaikkan syarat masuk anotator atas dasar yang tidak
pernah dinyatakan siapa pun.

**Letak ambang kualifikasi adalah D-03 Bagian 13, bukan Bagian 12.**
`specs/003-perangkat-anotasi/spec.md` R-14 dan `tasks.md` C-1 menyebut Bagian
12; Bagian 12 memuat beban kerja dan jadwal. Nilainya benar pada keduanya,
rujukannya yang keliru. Dicatat di sini karena rujukan yang keliru akan
disalin pembaca berikutnya, dan pembetulan `spec.md` diajukan terpisah —
mengubah spesifikasi saat implementasi adalah hal yang `AGENTS.md` larang.
"""

from __future__ import annotations

AMBANG_KAPPA = 0.70
"""Cohen's Kappa klasifikasi, ambang minimum batch — D-03 Bagian 11.1.

Di bawah 0,70 batas kategori dianggap belum memadai: pedoman disegarkan dan
batch dianotasi ulang. Tafsirannya mengikuti Landis & Koch (1977) lewat D-11
Bagian 3.2, bukan pilihan tim.
"""

AMBANG_F1_TEPAT = 0.75
"""F1 berpasangan, batas rentang dan label sama persis — D-03 Bagian 11.2."""

AMBANG_F1_LONGGAR = 0.85
"""F1 berpasangan, rentang bertumpang tindih dan label sama — D-03 Bagian 11.2.

Lebih tinggi daripada ambang tepat karena pencocokannya lebih longgar; selisih
besar antara keduanya menandakan masalah pada aturan rentang, bukan pada
pemahaman label.
"""

AMBANG_KUALIFIKASI_F1_LONGGAR = 0.80
"""Anotator terhadap kunci jawaban, 20 dokumen — D-03 Bagian 13."""

AMBANG_KUALIFIKASI_KAPPA = 0.70
"""Kappa kategori anotator terhadap kunci jawaban — D-03 Bagian 13.

Sama nilainya dengan `AMBANG_KAPPA` dan tetap ditulis terpisah: keduanya
dimiliki bagian D-03 yang berbeda, dan menyatukannya berarti perubahan pada
salah satunya diam-diam mengubah yang lain.
"""

JUMLAH_DOKUMEN_KUALIFIKASI = 20
"""Dokumen berkunci jawaban pada uji kualifikasi — D-03 Bagian 13.

**Bukan ambang, dan tetap di sini.** Ia menentukan apakah sebuah penilaian
sah, bukan berapa nilai yang dituntut, tetapi ia angka milik D-03 dengan cara
yang sama — dan menaruhnya di tempat lain berarti ada dua tempat angka D-03
disalin.

Angka bulat **tidak ikut disapu** oleh uji "satu tempat" pada B-6. Sapuan itu
mencari nilai pecahan ambang; menyapu bilangan bulat 20 akan menandai setiap
kemunculan angka itu pada seluruh `src/`, dan pemeriksa yang menyala pada hal
yang benar akan dimatikan orang. Yang menjaganya di sini adalah uji terhadap
`docs/D03.md`, bukan sapuan.
"""
