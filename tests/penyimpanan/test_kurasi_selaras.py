"""Salinan nilai enum fitur 010 pada `src/penyimpanan/kurasi.py` — T-3 fitur 013.

Lapisan penyimpanan tidak mengimpor `src/ingest/` (AGENTS.md), sehingga ia
memegang salinan nilai `JenisPutusan`, `PeranKurasi`, `Pemicu`, dan
`TindakanPenarikan`. Salinan yang hanyut membuat penyimpan menolak putusan sah
atau menerima putusan kelima; uji ini yang menjaga keduanya tetap sama.
"""

from __future__ import annotations

from src.ingest.kurasi.penarikan import Pemicu, TindakanPenarikan
from src.ingest.kurasi.putusan import JenisPutusan, PeranKurasi
from src.penyimpanan import kurasi


def test_jenis_putusan_sama() -> None:
    semua = {j.value for j in JenisPutusan}
    assert kurasi._MENYETUJUI | {"tolak", "tunda"} == semua
    assert {j.value for j in JenisPutusan if j.name.endswith("SETUJUI")} == kurasi._MENYETUJUI


def test_peran_pemutus_sama() -> None:
    assert {p.value for p in PeranKurasi} == kurasi._PERAN_PEMUTUS


def test_pemicu_dan_tindakan_sama() -> None:
    assert {p.value for p in Pemicu} == kurasi._PEMICU
    assert {t.value for t in TindakanPenarikan} == kurasi._TINDAKAN
