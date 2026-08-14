"""Tiga kredensial baku — R-01, R-01a, R-01b, C-03, C-05, C-17, KD-10.

Di sinilah C-03 benar-benar diwujudkan. `kredensial.py` membangun mekanismenya;
berkas ini menetapkan isinya, dan isinya yang menentukan apakah jalur
penjawaban dapat membaca karantina.

Ketiganya **tetapan, bukan fungsi pembangun**. Fungsi yang menerima parameter
dapat dipanggil dengan parameter lain, dan pemisahan yang dapat dibentuk ulang
dengan isi berbeda bukan pemisahan.

Pembagiannya mengikuti D-13 KD-10, yang menyebut tiga jalur dengan hak berbeda
— bukan dua. Peran `verifikator` pada `docs/D14.md` Bagian 3 adalah satu-satunya
yang kredensialnya menjangkau karantina.
"""

from __future__ import annotations

from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial

PENJAWABAN = Kredensial(
    nama="penjawaban",
    baca=frozenset({Area.KORPUS}),
    tulis=frozenset(),
    indeks=frozenset({IndeksTujuan.UTAMA, IndeksTujuan.METADATA}),
)
"""Jalur penjawaban: membaca korpus, tidak menulis apa pun.

Himpunan tulis yang kosong juga bagian C-17 — tanpa akses tulis dari jalur
penjawaban. Yang menulis adalah ingesti dan verifikasi.

**Ia menjangkau kedua indeks, dan itu bukan kelonggaran.** `docs/D14.md`
Bagian 6 menetapkan `bacaan_lanjutan` sebagai "tempat satu-satunya bagi sumber
`indeks_metadata`", sehingga jalur yang menyusun tanggapan wajib dapat
membacanya. Yang C-02 larang bukan membacanya melainkan **memasukkannya ke
konteks yang dikirim ke LLM** — dan itu dijaga `PEMANGGIL_LLM` di bawah.
"""

VERIFIKASI = Kredensial(
    nama="verifikasi",
    baca=frozenset({Area.KARANTINA, Area.KORPUS}),
    tulis=frozenset({Area.KORPUS}),
    indeks=frozenset({IndeksTujuan.UTAMA, IndeksTujuan.METADATA}),
)
"""Jalur verifikasi: satu-satunya yang menjangkau karantina.

Ia menulis ke korpus karena memindahkan dokumen ke sana adalah pekerjaannya
(R-04). Ia tidak menulis ke karantina: yang menaruh dokumen di sana adalah
ingesti, dan memisahkan keduanya menjaga verifikator tidak dapat menyunting
bahan yang sedang dinilainya.
"""

PEMANGGIL_LLM = Kredensial(
    nama="pemanggil_llm",
    baca=frozenset({Area.KORPUS}),
    tulis=frozenset(),
    indeks=frozenset({IndeksTujuan.UTAMA}),
)
"""Pemanggil model: membaca korpus dan **hanya indeks utama**.

**Di sinilah C-02 diwujudkan.** Konteks yang dikirim ke LLM disusun oleh jalur
ini, dan jalur ini tidak memiliki kredensial membaca `indeks_metadata` — bukan
tidak boleh, melainkan tidak bisa. Satu kueri yang lupa menyaring tidak dapat
meloloskan teks berlisensi tertutup, sebab yang lupa menyaring pun tetap tidak
menjangkaunya.

Tidak menulis, tidak menjangkau karantina.

KD-10 dan NFR-21 menyebut ketiganya bersamaan. Larangan menjangkau kunci
pemetaan pseudonim (C-05) dipenuhi karena kunci itu tidak berada pada area mana
pun di sini — ia basis data terpisah (ADR-07, KA-03).
"""

SELURUH_KREDENSIAL: tuple[Kredensial, ...] = (PENJAWABAN, VERIFIKASI, PEMANGGIL_LLM)
"""Dipakai uji untuk menyatakan sifat seluruh daftar. Kredensial keempat yang
ditambahkan kelak wajib masuk ke sini, dan uji yang memeriksa daftar ini akan
menangkapnya bila ia kelebihan kemampuan."""
