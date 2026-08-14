"""Pengambilan leksikal BM25 — R-09, R-13, ADR-03, D-07 Bagian 3.3 dan 4.4.

Sisi leksikal ADR-03. Alasan keberadaannya tertulis pada ADR-03 sendiri:
*"Pertanyaan manajerial sering memuat istilah regulasi yang harus cocok persis
('Permendikbudristek Nomor 21 Tahun 2022')"*, dan pencarian vektor *"gagal pada
nomor regulasi, justru pada kasus yang paling menuntut ketepatan"*.

## Mencocokkan `stem`, bukan `permukaan`

D-07 Bagian 3.3: BM25 *"dengan penanganan morfologi Bahasa Indonesia sesuai
modul praproses (FR-B03)"*. `Token` fitur 015 membawa keduanya, dan
`stemming.py` sudah menyatakan pembagiannya: *"`permukaan` untuk menunjuk,
`stem` untuk mencari."*

Versi yang mencocokkan permukaan bekerja pada sebagian besar kasus — "sekolah"
tetap "sekolah" — dan gagal justru pada kata berimbuhan yang menjadi inti
pertanyaan manajerial: "menugaskan", "penugasan", "ditugaskan", ketiganya
berstem `tugas`. **Kegagalannya berupa hasil yang sepi, bukan galat**, dan
hasil yang sepi terbaca sebagai korpus yang tidak memuat jawabannya.

Impor `src/rag/` → `src/nlp/` disahkan pada KB-034 pertanyaan 4 dan tertulis
pada `AGENTS.md`.

## Satu indeks melayani satu indeks tujuan

Penjagaan yang menopang C-02. Kredensial diperiksa terhadap `indeks_tujuan`
sumber sebelum sumber dijalankan (`hibrida.py`); sumber yang mengaku `utama`
tetapi memuat segmen `metadata` meloloskan keduanya, dan pemeriksaan
kredensialnya menjadi tidak berarti apa pun.

## Kueri kosong dan kueri tanpa kata kunci adalah dua hal berbeda

Kueri kosong adalah pemanggilan yang keliru — ditolak. Kueri yang seluruh
katanya kata fungsi ("apa yang di sana") adalah pertanyaan sungguhan yang tidak
memuat kata kunci; ia berakhir pada hasil kosong, lalu pada balasan
tidak-ditemukan (FR-F04). Menyamakan keduanya menampilkan pesan galat kepada
pengguna yang bertanya dengan wajar, dan pengguna itu menyimpulkan sistemnya
rusak.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence

from src.kamus.segmen import IndeksTujuan
from src.nlp.praproses.stemming import stemkan, tanpa_stop_word
from src.nlp.praproses.tokenisasi import tokenkan
from src.penyimpanan.indeks import SegmenTerindeks
from src.rag.pengambilan.kandidat import HasilSumber, Kandidat, SumberKandidat, urutkan_kandidat
from src.rag.pengambilan.tetapan import BM25_B, BM25_K1


def _stem_dari(teks: str) -> list[str]:
    """Teks → daftar stem, lewat jalur praproses fitur 015.

    Stop-word dibuang **sebagai token**, bukan dipotong dari teks — bentuk yang
    `stemming.py` tetapkan agar rentang karakter yang tersisa tetap sah.
    """
    return [t.stem for t in tanpa_stop_word(stemkan(tokenkan(teks)))]


class IndeksLeksikal:
    """Indeks BM25 atas satu indeks tujuan.

    Beku setelah dibangun: `bangun_indeks` adalah satu-satunya pintunya, dan
    tidak ada metode yang menambah segmen. Indeks yang dapat ditambahi saat
    jalan adalah indeks yang versinya berbohong — D-07 Bagian 3.3 menetapkan
    pengindeksan ulang bersifat atomik, "indeks lama tetap melayani sampai
    indeks baru siap sepenuhnya".
    """

    def __init__(
        self,
        *,
        versi: str,
        indeks_tujuan: IndeksTujuan,
        stem_per_segmen: Mapping[str, Sequence[str]],
    ) -> None:
        self.versi = versi
        self.indeks_tujuan = indeks_tujuan
        self._stem = {id_segmen: tuple(stem) for id_segmen, stem in stem_per_segmen.items()}
        self._panjang = {id_segmen: len(stem) for id_segmen, stem in self._stem.items()}
        jumlah_kata = sum(self._panjang.values())
        self._panjang_rerata = jumlah_kata / len(self._stem) if self._stem else 0.0
        self._memuat: dict[str, set[str]] = {}
        for id_segmen, stem in self._stem.items():
            for kata in set(stem):
                self._memuat.setdefault(kata, set()).add(id_segmen)

    @property
    def jumlah_segmen(self) -> int:
        return len(self._stem)

    def _idf(self, kata: str) -> float:
        """IDF ragam Lucene — selalu positif.

        `ln(1 + (N - n + 0,5) / (n + 0,5))`. Bentuk klasik tanpa `1 +` menjadi
        **negatif** untuk kata yang muncul pada lebih dari separuh segmen, dan
        skor negatif membuat segmen yang memuat kata kueri terurut di bawah
        segmen yang tidak memuatnya sama sekali.
        """
        n = len(self._memuat.get(kata, ()))
        return math.log(1 + (self.jumlah_segmen - n + 0.5) / (n + 0.5))

    def skor(self, kata_kueri: Sequence[str]) -> dict[str, float]:
        """Skor BM25 setiap segmen yang memuat sekurangnya satu kata kueri."""
        hasil: dict[str, float] = {}
        for kata in kata_kueri:
            pemuat = self._memuat.get(kata)
            if not pemuat:
                continue
            idf = self._idf(kata)
            for id_segmen in pemuat:
                frekuensi = self._stem[id_segmen].count(kata)
                panjang_nisbi = self._panjang[id_segmen] / self._panjang_rerata
                penyebut = frekuensi + BM25_K1 * (1 - BM25_B + BM25_B * panjang_nisbi)
                hasil[id_segmen] = hasil.get(id_segmen, 0.0) + idf * (
                    frekuensi * (BM25_K1 + 1) / penyebut
                )
        return hasil


def bangun_indeks(
    segmen: Iterable[SegmenTerindeks],
    *,
    versi: str,
    indeks_tujuan: IndeksTujuan,
) -> IndeksLeksikal:
    """Bangun indeks leksikal dari segmen yang sudah terindeks.

    `indeks_tujuan` diminta terpisah, bukan disimpulkan dari segmennya. Indeks
    kosong tetap memiliki indeks tujuan yang jelas — dan korpus kosong adalah
    keadaan sistem ini hari ini.
    """
    stem_per_segmen: dict[str, list[str]] = {}
    for satu in segmen:
        if satu.indeks_tujuan is not indeks_tujuan:
            raise ValueError(
                f"segmen {satu.id_segmen} berada pada indeks tujuan "
                f"{satu.indeks_tujuan.value}, sedangkan indeks ini melayani "
                f"{indeks_tujuan.value} — satu indeks melayani satu indeks tujuan, "
                "sebab kredensial diperiksa terhadap indeks tujuan sumbernya (C-02)"
            )
        if satu.id_segmen in stem_per_segmen:
            raise ValueError(f"id_segmen kembar pada indeks: {satu.id_segmen}")
        stem_per_segmen[satu.id_segmen] = _stem_dari(satu.teks)
    return IndeksLeksikal(versi=versi, indeks_tujuan=indeks_tujuan, stem_per_segmen=stem_per_segmen)


class SumberBM25(SumberKandidat):
    """Sisi leksikal ADR-03."""

    def __init__(self, indeks: IndeksLeksikal) -> None:
        self._indeks = indeks

    @property
    def nama(self) -> str:
        return "bm25"

    @property
    def indeks_tujuan(self) -> IndeksTujuan:
        return self._indeks.indeks_tujuan

    @property
    def versi_indeks(self) -> str:
        return self._indeks.versi

    def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        if not kueri.strip():
            raise ValueError("kueri kosong tidak dapat dicari")
        kata = _stem_dari(kueri)
        skor = self._indeks.skor(kata) if kata else {}
        peringkat = urutkan_kandidat(
            Kandidat(id_segmen=id_segmen, skor=nilai) for id_segmen, nilai in skor.items()
        )
        return HasilSumber(
            nama_sumber=self.nama,
            versi_indeks=self._indeks.versi,
            peringkat=peringkat[:batas],
        )
