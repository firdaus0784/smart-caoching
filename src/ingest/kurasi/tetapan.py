"""Rumah tetapan kurasi — R-12, R-10, C-16, D-06 Bagian 8.3 dan Bagian 7.5.

Rumah keempat, sesudah `src/nlp/anotasi/ambang.py` (fitur 003),
`src/nlp/pelatihan/pembagian.py` (fitur 004), dan
`src/rag/pengambilan/tetapan.py` (fitur 007).

## Angka yang dikutip, dan angka yang belum ada

Seluruh tetapan di sini berasal dari **D-06**, yang menamai nilainya beserta
dasarnya. Menyalinnya bukan menyetel — ia mewujudkan keputusan yang sudah
diambil dokumen pemiliknya.

Empat angka berasal dari Bagian 8.3 (pagu dan pengereman); satu dari Bagian
7.5 (tenggat penarikan). Yang terakhir masuk ke sini alih-alih tinggal pada
`penarikan.py` karena alasan yang sama: angka yang tersebar adalah angka yang
perubahannya tidak terlihat pada satu tempat mana pun.

**Yang tidak ada di sini: ambang relevansi L4.** D-06 Bagian 6 menyerahkannya
ke BT-24, uji ingesti percobaan bulan 3, dan menuliskan nilai awal di sini
adalah menyetel ambang yang C-16 larang. Kekosongan itu yang benar, dan ia
diuji.

D-06 menyebut kedua akibat yang salah bila ia ditebak: *"Ambang terlalu longgar
membanjiri antrean kurasi; terlalu ketat membuat feed kekurangan isi dan
memicu titik kritis T5 pada D-02."*
"""

from __future__ import annotations

PAGU_KURASI_HARIAN = 15
"""Butir yang dinilai kurator per hari kerja — `docs/D06.md` Bagian 8.3.

Dasarnya ritme 20-30 menit per hari (D-06 Bagian 7.2) dan 2 menit per butir
(D-05 S-15). Ia **batas kelayakan, bukan target efisiensi**: kurator adalah
dosen yang juga mengajar.
"""

PENGALI_AMBANG_ANTREAN = 2
"""Antrean dianggap melampaui ambang bila lebih dari 2x pagu harian.

`docs/D06.md` Bagian 8.3 dan PM-01. Dinyatakan sebagai pengali, bukan sebagai
angka 30, agar ia tetap benar ketika pagu harian berubah — dan pagu harian
akan berubah bila kapasitas kurator berubah.
"""

HARI_BERTURUT_SEBELUM_PENGEREMAN = 3
"""Hari berturut-turut melampaui ambang sebelum ingesti diperlambat.

`docs/D06.md` Bagian 8.3 dan FR-I08. Angkanya berada pada kolom kendali tabel
itu — *"Tindakan bila melampaui 3 hari berturut-turut"* — bukan pada kolom
nilai, dan itu satu-satunya tempat ia tertulis.

**Tiga, bukan satu.** Pengereman pada hari pertama menurunkan frekuensi K-C
setiap kali antrean naik sehari, dan sesudah itu feed kekurangan isi. Angka
ini yang membedakan antrean yang sedang menumpuk dari antrean yang kebetulan
panjang satu hari.
"""

PAGU_TAYANG_PER_PENGGUNA = 3
"""Butir yang tayang ke satu pengguna per hari — FR-G05, D-06 Bagian 8.3.

**Berbeda dari pagu kurasi harian**, dan D-01 FR-I07 menyatakan pembedaannya
tegas: yang satu membatasi beban kurator, yang lain membatasi beban pembaca.
Menyatukannya akan membuat penambahan kapasitas kurator membanjiri pengguna.
"""

TENGGAT_PENARIKAN_HARI_KERJA = 1
"""Hari kerja untuk menarik butir yang kekeliruan isinya dilaporkan pengguna.

`docs/D06.md` Bagian 7.5 dan FR-I06. **Bukan** tenggat bagi penarikan karena
regulasi berubah — yang itu berjalan otomatis, dan tenggat padanya akan
membaca seperti izin menunda sehari.
"""
