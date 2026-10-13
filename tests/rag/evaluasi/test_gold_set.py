"""Uji bentuk *gold set* dan sidiknya — T-2 fitur 040, R-02, R-03, R-07, K-1, K-3.

Bentuknya milik D-08 Bagian 5.3, komposisinya milik D-08 Bagian 5.1. Uji
membaca keduanya dari dokumen, tidak menyalinnya: uji yang menyalin hanya
membuktikan dua salinan sama, termasuk ketika keduanya sudah menyimpang dari
pemiliknya.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.rag.evaluasi.gold_set import (
    KOMPOSISI_D08,
    GalatBerkas,
    GoldSet,
    JenisPertanyaan,
    urai,
)
from tests.rag.evaluasi.rekaan import baris, berkas, komposisi_penuh

AKAR = Path(__file__).resolve().parents[3]
D08 = (AKAR / "docs" / "D08.md").read_text(encoding="utf-8")


def _komposisi_d08() -> dict[str, int]:
    """Tabel D-08 Bagian 5.1: `| **A · …** | 100 | … |`."""
    bagian = D08.split("### 5.1 Komposisi", 1)[1].split("### 5.2", 1)[0]
    pola = re.compile(r"^\|\s*\*\*([A-Z]) · [^|]*\*\*\s*\|\s*(\d+)\s*\|")
    hasil = {}
    for b in bagian.splitlines():
        cocok = pola.match(b)
        if cocok:
            hasil[cocok.group(1)] = int(cocok.group(2))
    return hasil


def _galat(teks: str) -> GalatBerkas:
    with pytest.raises(GalatBerkas) as info:
        urai(teks)
    return info.value


def test_enam_jenis_dan_komposisi_dibaca_dari_d08() -> None:
    """D-08 Bagian 5.1 pemilik tunggal jenis dan komposisi."""
    d08 = _komposisi_d08()
    assert sum(d08.values()) == 200
    assert {j.value for j in JenisPertanyaan} == set(d08)
    assert {j.value: n for j, n in KOMPOSISI_D08.items()} == d08


@pytest.mark.parametrize(
    ("jenis", "jumlah_kunci", "sah"),
    [
        ("A", 0, False),
        ("A", 1, True),
        ("B", 0, False),
        ("B", 2, True),
        ("C", 0, True),
        ("C", 1, False),
        ("D", 0, True),
        ("D", 1, False),
        ("E", 0, False),
        ("E", 1, True),
        ("F", 1, False),
        ("F", 2, True),
    ],
)
def test_kunci_sesuai_jenis(jenis: str, jumlah_kunci: int, sah: bool) -> None:
    """R-02: C dan D tanpa kunci; A, B, E berkunci; F sedikitnya dua (M-4)."""
    kunci = [("DOK-1", f"Pasal {i + 1}") for i in range(jumlah_kunci)]
    teks = berkas(baris("q-1", jenis, kunci=kunci))
    if sah:
        assert len(urai(teks).pertanyaan) == 1
    else:
        assert "baris 1" in str(_galat(teks))


def test_kunci_kembar_ditolak() -> None:
    teks = berkas(baris("q-1", "F", kunci=[("DOK-1", "Pasal 2"), ("DOK-1", "Pasal 2")]))
    assert "kembar" in str(_galat(teks))


def test_jenis_di_luar_a_sampai_f_ditolak() -> None:
    teks = berkas({**baris("q-1"), "jenis": "G"})
    assert "baris 1" in str(_galat(teks))


def test_kategori_wajib_kecuali_jenis_d() -> None:
    assert urai(berkas(baris("q-1", "D"))).pertanyaan[0].kategori is None
    assert urai(berkas({**baris("q-1", "D"), "kategori": "K2"})).pertanyaan[0].kategori
    for jenis in "ABCEF":
        assert "kategori" in str(_galat(berkas(baris("q-1", jenis, kategori=None))))
    assert "baris 1" in str(_galat(berkas(baris("q-1", kategori="K9"))))


def test_bernomor_regulasi_wajib_tanpa_nilai_baku() -> None:
    """P-6 A: nilai baku `false` diam-diam mengeluarkan pertanyaan dari
    himpunan berambang 95%."""
    tanpa = baris("q-1")
    del tanpa["bernomor_regulasi"]
    assert "bernomor_regulasi" in str(_galat(berkas(tanpa)))
    for nilai in ("ya", 1, "true"):
        assert "bernomor_regulasi" in str(
            _galat(berkas({**baris("q-1"), "bernomor_regulasi": nilai}))
        )
    assert urai(berkas(baris("q-1", bernomor_regulasi=True))).pertanyaan[0].bernomor_regulasi


@pytest.mark.parametrize("id_", ["", "ada spasi", "x" * 65, "q/1", 7])
def test_bentuk_id(id_: object) -> None:
    assert "id" in str(_galat(berkas({**baris("q-1"), "id": id_})))


def test_id_kembar_ditolak_dengan_kedua_barisnya() -> None:
    pesan = str(_galat(berkas(baris("q-1"), baris("q-2"), baris("q-1"))))
    assert "q-1" in pesan
    assert "baris 3" in pesan
    assert "baris 1" in pesan


def test_gold_set_yang_dibentuk_langsung_pun_menolak_id_kembar() -> None:
    """Keunikan dijaga tipenya, bukan hanya pengurainya."""
    satu = urai(berkas(baris("q-1"))).pertanyaan[0]
    with pytest.raises(ValidationError, match="id kembar"):
        GoldSet(pertanyaan=(satu, satu))
    with pytest.raises(ValidationError):
        GoldSet(pertanyaan=())


def test_pertanyaan_hampa_ditolak() -> None:
    assert "pertanyaan" in str(_galat(berkas({**baris("q-1"), "pertanyaan": "   "})))


def test_bidang_asing_dan_kunci_json_kembar_ditolak() -> None:
    assert "baris 1" in str(_galat(berkas({**baris("q-1"), "jawaban": "x"})))
    mentah = berkas(baris("q-1")).rstrip("\n")[:-1] + ', "jenis": "B"}\n'
    assert "kembar" in str(_galat(mentah))


def test_baris_bukan_objek_json_ditolak_tanpa_mengutipnya() -> None:
    rahasia = "Bu Siti kepala SD Negeri 3 bertanya"
    pesan = str(_galat(berkas(baris("q-1")) + f"{rahasia}\n" + json.dumps([rahasia]) + "\n"))
    assert "baris 2" in pesan
    assert "baris 3" in pesan
    assert "Siti" not in pesan


def test_pesan_galat_tidak_memuat_teks_pertanyaan() -> None:
    """R-07, K-1: `input` pydantic tidak pernah dibawa ke pesan."""
    rahasia = "Bagaimana Pak Darmawan mengatur dana BOS SDN 2 Cikoneng?"
    salah = [
        {**baris("q-1", pertanyaan=rahasia), "jenis": rahasia},
        {**baris("q-2", pertanyaan=rahasia), "kategori": rahasia},
        {**baris("q-3", pertanyaan=rahasia), "bernomor_regulasi": rahasia},
        {**baris("q-4", pertanyaan=rahasia), "kunci": rahasia},
        {**baris("q-5", pertanyaan=rahasia), "kunci": [{"dokumen": rahasia}]},
        {**baris("q-6", pertanyaan=rahasia), "id": rahasia},
        baris("q-7", "C", pertanyaan=rahasia, kunci=[("DOK-1", "Pasal 1")]),
    ]
    pesan = str(_galat(berkas(*salah)))
    for n in range(1, 8):
        assert f"baris {n}" in pesan
    assert "Darmawan" not in pesan
    assert "Cikoneng" not in pesan


def test_berkas_hampa_ditolak() -> None:
    assert "tidak memuat" in str(_galat("\n  \n"))


def test_baris_hampa_dilewati_dan_nomor_baris_tetap() -> None:
    teks = "\n" + berkas(baris("q-1")) + "\n" + berkas({**baris("q-2"), "jenis": "G"})
    assert "baris 4" in str(_galat(teks))
    assert len(urai("\n" + berkas(baris("q-1")) + "\n").pertanyaan) == 1


def _acak(teks: str, benih: int) -> str:
    """Urutan baris, bidang, kunci, dan spasi diacak; isinya tetap."""
    acak = random.Random(benih)
    hasil = []
    for b in teks.splitlines():
        obj = json.loads(b)
        kunci = list(obj["kunci"])
        acak.shuffle(kunci)
        obj["kunci"] = kunci
        bidang = list(obj.items())
        acak.shuffle(bidang)
        hasil.append(
            json.dumps(dict(bidang), ensure_ascii=False, indent=None, separators=(" , ", " :  "))
        )
    acak.shuffle(hasil)
    return "\n".join(hasil) + "\n"


def test_sidik_tetap_terhadap_urutan_dan_spasi() -> None:
    """R-03 (M-5): sidik isi kanonik, bukan sidik berkas."""
    teks = berkas(
        baris("q-1", "F", kunci=[("DOK-1", "Pasal 2"), ("DOK-2", "Pasal 9")]),
        baris("q-2", "A", kunci=[("DOK-1", "Pasal 3")], bernomor_regulasi=True),
        baris("q-3", "D"),
        baris("q-4", "C", kategori="K4"),
    )
    sidik = urai(teks).sidik
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", sidik)
    for benih in range(5):
        assert urai(_acak(teks, benih)).sidik == sidik


@pytest.mark.parametrize(
    "ubah",
    [
        {"pertanyaan": "REKAAN pertanyaan q-1."},
        {"jenis": "B"},
        {"kategori": "K2"},
        {"kunci": [{"dokumen": "DOK-1", "bagian": "Pasal 4"}]},
        {"kunci": [{"dokumen": "DOK-9", "bagian": "Pasal 1"}]},
        {"bernomor_regulasi": True},
        {"id": "q-9"},
    ],
)
def test_sidik_berubah_terhadap_setiap_bidang_isi(ubah: dict[str, object]) -> None:
    asal = baris("q-1", kunci=[("DOK-1", "Pasal 1")])
    lain = baris("q-2", "C")
    assert urai(berkas(asal, lain)).sidik != urai(berkas({**asal, **ubah}, lain)).sidik


def test_komposisi_dan_penyimpangan_dari_d08() -> None:
    penuh = urai(berkas(*komposisi_penuh()))
    assert penuh.komposisi() == dict(KOMPOSISI_D08)
    assert penuh.penyimpangan() == {}
    kurang = GoldSet(pertanyaan=penuh.pertanyaan[1:])
    assert kurang.penyimpangan() == {JenisPertanyaan.A: (99, 100)}
    kecil = urai(berkas(baris("q-1"), baris("q-2", "D")))
    assert kecil.komposisi()[JenisPertanyaan.F] == 0
    assert kecil.penyimpangan()[JenisPertanyaan.F] == (0, 10)


def test_komposisi_kategori_dan_jumlah_bernomor() -> None:
    gold = urai(
        berkas(
            baris("q-1", kategori="K2", bernomor_regulasi=True),
            baris("q-2", kategori="K2"),
            baris("q-3", "D"),
        )
    )
    assert gold.komposisi_kategori() == {"K2": 2, "tanpa-kategori": 1}
    assert gold.jumlah_bernomor_regulasi() == 1
