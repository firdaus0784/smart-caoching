"""Sumber kandidat tiruan yang deterministik — B-1 fitur 007, ADR-12.

**Ia berdiri untuk sumber vektor yang belum dapat dibangun.** Model sematan
menuntut ketergantungan baru (C-12) dan pgvector menuntut penyebaran D-09;
keduanya fitur 019. Sampai saat itu, penggabungan peringkat tetap perlu sumber
kedua untuk dapat diuji sama sekali.

**Tiruannya tinggal di `tests/`, bukan di `src/`.** Itu bukan kerapian
melainkan penegakan R-05. Pelaksana kosong pada `src/` yang mengembalikan
daftar kosong akan **memenuhi** syarat dua sumber tanpa mencari apa pun —
persis kegagalan yang syarat itu ada untuk menutup. Ia ditolak pada KB-034
pertanyaan 3.

Mengikuti ADR-12, yang sudah terbukti pada fitur 002 (`PenyimpanTiruan`) dan
fitur 015.

`_dipanggil` merekam apakah `cari` pernah dijalankan. Ia yang membuat uji C-1
dapat menyatakan hal yang lebih kuat daripada "hasilnya kosong": **sumber pada
indeks yang tidak dijangkau kredensial tidak dijalankan sama sekali.** Hasil
kosong dapat berarti pencarian yang berjalan lalu disaring, dan penyaringan
sesudah pencarian adalah bentuk yang C-02 tolak.
"""

from __future__ import annotations

from src.penyimpanan.indeks import IndeksTujuan
from src.rag.pengambilan.kandidat import HasilSumber, Kandidat, SumberKandidat, urutkan_kandidat


class SumberTiruan(SumberKandidat):
    """Sumber yang mengembalikan skor yang sudah ditetapkan pemanggilnya."""

    def __init__(
        self,
        nama: str,
        skor: dict[str, float],
        *,
        indeks_tujuan: IndeksTujuan = IndeksTujuan.UTAMA,
        versi_indeks: str = "tiruan-1",
    ) -> None:
        self._nama = nama
        self._skor = dict(skor)
        self._indeks_tujuan = indeks_tujuan
        self._versi_indeks = versi_indeks
        self.dipanggil = 0

    @property
    def nama(self) -> str:
        return self._nama

    @property
    def indeks_tujuan(self) -> IndeksTujuan:
        return self._indeks_tujuan

    @property
    def versi_indeks(self) -> str:
        return self._versi_indeks

    def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        self.dipanggil += 1
        kandidat = urutkan_kandidat(
            Kandidat(id_segmen=id_segmen, skor=skor) for id_segmen, skor in self._skor.items()
        )
        return HasilSumber(
            nama_sumber=self._nama,
            versi_indeks=self._versi_indeks,
            peringkat=kandidat[:batas],
        )
