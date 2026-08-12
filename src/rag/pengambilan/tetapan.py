"""Rumah tetapan pengambilan — R-08, C-16, D-07 Bagian 4.4.

Satu tempat bagi angka yang dimiliki D-07, dan **bukan** tempat bagi angka
yang belum dimiliki siapa pun.

## Dua jenis angka, dan hanya satu yang boleh ada di sini

C-16 berbunyi: *"Ambang tidak disetel di luar prosedur kalibrasi `docs/D07.md`
BT-29."* Yang membuat pasal itu mudah dilanggar tanpa disadari adalah bahwa
tidak semua angka pada sistem ini adalah ambang.

**Angka yang dikutip.** D-07 Bagian 4.4 sudah menetapkan nilai awal: kandidat
20 teratas per sumber, 5–8 segmen diteruskan. Menyalinnya ke sini bukan
menyetel — ia mewujudkan keputusan yang sudah diambil dokumen pemiliknya.
Syaratnya satu: asalnya tertulis, sehingga pembaca berikutnya dapat
membedakannya dari angka yang dipilih seseorang karena bekerja baik.

**Angka yang disetel.** Ambang tinggi dan menengah pada penilaian kecukupan
bukti (D-07 Bagian 4.6) **tidak** memiliki nilai pada dokumen mana pun. D-07
menyerahkannya ke BT-29, kalibrasi terhadap *gold set* BT-35 yang baru ada
bulan 4–5. Menuliskan nilai awal di sini adalah menyetel, dan cara paling
sunyi melanggar C-16 bukan mengubah angka melainkan menuliskan angka awal
yang tak pernah ditinjau: ia berjalan pada hari pertama, memberi hasil masuk
akal, dan tidak seorang pun kembali kepadanya.

**Karena itu berkas ini tidak memuat satu pun tetapan bernama ambang, dan
kekosongan itu diuji.** Ia bukan keadaan sementara yang perlu diisi.

## Rumah tetapan ketiga

`src/nlp/anotasi/ambang.py` (fitur 003) dan `src/nlp/pelatihan/pembagian.py`
(fitur 004) mendahuluinya. Alasan bentuknya sama ketiga kalinya: angka yang
tertulis di dua tempat akan berbeda di salah satunya, dan yang berbeda adalah
yang tidak diperbarui.
"""

from __future__ import annotations

JUMLAH_KANDIDAT_PER_SUMBER = 20
"""Kandidat yang diambil setiap sumber sebelum penggabungan.

`docs/D07.md` Bagian 4.4: "Kandidat BM25 — 20 teratas" dan "Kandidat vektor —
20 teratas". Sama untuk kedua sumber, karena itu satu tetapan, bukan dua.
Dua tetapan bernilai sama adalah dua tetapan yang kelak berbeda.
"""

JUMLAH_SEGMEN_DITERUSKAN_MINIMUM = 5
"""Batas bawah segmen yang diteruskan ke penyusunan jawaban.

`docs/D07.md` Bagian 4.4: "Segmen diteruskan — 5–8", dengan catatan "cukup
untuk menjawab; tidak membanjiri konteks". Batas bawah, bukan sasaran:
kandidat yang lebih sedikit diteruskan seluruhnya, tidak diisi sampai penuh.
"""

JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM = 8
"""Batas atas segmen yang diteruskan.

`docs/D07.md` Bagian 4.4, dan diulang pada Bagian 9: "Batas konteks — 5–8
segmen; segmen dipangkas bila melampaui batas" (RT-03).
"""

TETAPAN_RRF_K = 60
"""Konstanta penghalus pada *Reciprocal Rank Fusion*.

Nilai dari **Cormack dkk. 2009**, makalah yang `docs/D04.md` ADR-03 dan
`docs/D07.md` Bagian 4.4 kutip keduanya sebagai sumber metode penggabungan
peringkat. D-07 menyebut metodenya tanpa menyebut nilainya; nilai ini karena
itu dikutip dari sumber yang D-07 tunjuk, bukan dipilih.

Yang dilakukannya: skor sebuah segmen adalah jumlah `1 / (k + peringkat)` atas
seluruh sumber yang menemukannya. Nilai `k` yang besar memperkecil jarak antar
peringkat teratas, sehingga segmen yang ditemukan **dua** sumber pada peringkat
sedang mengungguli segmen yang ditemukan satu sumber pada peringkat pertama.
Itu perilaku yang ADR-03 tuju.

Ditinjau pada BT-29 bersama seluruh ambang lain, dan sampai saat itu ia tetap
nilai dari makalahnya — bukan nilai yang kami setel.
"""

JUMLAH_SUMBER_MINIMUM = 2
"""Sumber kandidat paling sedikit yang wajib berpartisipasi (R-05).

**Bukan tetapan kalibrasi.** `docs/D04.md` ADR-03 menolak dua hal secara
tegas: "Vektor saja — gagal pada nomor regulasi, justru pada kasus yang paling
menuntut ketepatan. Leksikal saja — gagal pada parafrase pengguna." Dua adalah
jumlah jenis pengambilan yang keputusan itu tuntut.

Menurunkannya menjadi satu membatalkan ADR-03; ia bukan penyetelan yang BT-29
tinjau melainkan keputusan arsitektur yang menuntut ADR baru.

Ia ada di sini, dan bukan sebagai angka telanjang pada `gabung.py`, justru
karena bahaya yang ditutupnya sunyi: penggabungan atas satu daftar
mengembalikan daftar itu — tanpa galat, dengan nama fungsi yang tetap berbunyi
hibrida.
"""
