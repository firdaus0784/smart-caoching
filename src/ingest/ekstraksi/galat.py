"""Galat ekstraksi dan pesan penggunanya — R-02, C-13, NFR-19.

Satu tipe untuk seluruh kegagalan pembacaan berkas, dengan **dua pesan yang
terpisah tegas**. Pemisahan itu bukan kerapian: dua pembaca dengan kebutuhan
berlawanan membaca hal yang sama. Pengembang perlu tahu pustaka mana yang
gagal; kepala sekolah tidak boleh melihatnya sama sekali.

**Kumpulan pesan disusun sekali di sini, bukan ditempel saat menangani
galat.** Pesan yang ditulis sambil menangani galat adalah pesan yang menyebut
nama pustaka — "PdfReadError", "PackageNotFoundError" — karena nama itu
sedang ada di tangan penulisnya. Keduanya tidak berarti apa pun bagi pembaca
yang dituju, dan keduanya masuk dengan sendirinya bila tidak ada tempat lain
yang menampung pesannya.

Empat aturan berlaku pada setiap baris `PESAN`, dan keempatnya diuji:

1. **Paling banyak 20 kata per kalimat** (C-13).
2. **Tanpa istilah teknis dan tanpa nama pustaka.** Termasuk kata "galat"
   sendiri — pengguna tidak perlu tahu bahwa yang terjadi disebut galat, ia
   perlu tahu apa yang harus dilakukannya.
3. **Menyebut tindakan berikutnya.** Pesan yang berhenti pada "tidak dapat
   dibaca" membuat pengguna mengulang tindakan yang sama.
4. **Tanpa kode galat** (`AGENTS.md`). Kode mengundang pengguna menyalinnya
   ke pencarian web, dan yang ditemukannya halaman untuk pengembang.
"""

from __future__ import annotations

PESAN: dict[str, str] = {
    "tidak_terbaca": "Berkas tidak dapat dibaca. Mohon periksa berkasnya lalu unggah ulang.",
    "terkunci": "Berkas terkunci kata sandi. Mohon unggah versi yang terbuka.",
    "tanpa_isi": "Berkas terbuka tetapi kosong. Mohon periksa isinya lalu unggah ulang.",
    "perlu_pindaian": "Berkas berupa hasil pindaian. Mohon tunggu, teksnya sedang dibaca.",
    "jenis_tidak_didukung": "Jenis berkas ini belum dapat diterima. Mohon unggah bentuk lain.",
}
"""Seluruh pesan yang mungkin sampai ke pengguna pada jalur ekstraksi.

Lima, dan jumlahnya sengaja kecil. Pesan yang terlalu rinci memaksa pengguna
menebak perbedaan antara dua keadaan yang tindakannya sama.

`perlu_pindaian` bukan pesan kegagalan melainkan pesan tunggu: dokumen
pindaian memang berlanjut ke OCR, dan pengguna yang membaca "tidak dapat
dibaca" akan mengunggah ulang berkas yang sebenarnya baik-baik saja.
"""


class GalatEkstraksi(Exception):
    """Berkas tidak dapat diurai menjadi teks.

    **Selalu dilempar, tidak pernah diganti untai kosong.** Pengekstrak yang
    mengembalikan untai kosong pada berkas bermasalah menghasilkan dokumen
    yang lolos seluruh gerbang fitur 002 tanpa satu pun berbunyi.
    """

    def __init__(self, pesan_teknis: str, pesan_pengguna: str = "") -> None:
        super().__init__(pesan_teknis)
        self.pesan_pengguna = pesan_pengguna or PESAN["tidak_terbaca"]
