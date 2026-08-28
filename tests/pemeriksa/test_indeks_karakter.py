"""Uji pemeriksa indeks rentang anotasi — C-10, D-03 Bagian 15.

Diuji terhadap **pohon yang sengaja dirusak**, masing-masing aturan terpisah.
Pemeriksa yang hanya dijalankan atas pohon yang sehat membuktikan ia tidak
mengeluh; ia tidak membuktikan ia menemukan apa pun (TA-01).
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.indeks_karakter import (
    BERKAS_EKSPOR,
    BERKAS_RENTANG,
    DIREKTORI_ANOTASI,
    periksa_indeks_karakter,
)

AKAR = Path(__file__).resolve().parents[2]

RENTANG_BERSIH = '''"""Rentang tiruan."""

from pydantic import BaseModel, model_validator


class RentangEntitas(BaseModel):
    teks_kanonik: str
    mulai: int
    akhir: int

    @model_validator(mode="after")
    def _cocok(self) -> "RentangEntitas":
        potongan = self.teks_kanonik[self.mulai : self.akhir]
        if not potongan:
            raise ValueError("rentang kosong")
        return self
'''

EKSPOR_BERSIH = '''"""Ekspor tiruan."""

from dataclasses import dataclass

from src.nlp.praproses.tokenisasi import tokenkan


@dataclass
class HasilEksporConll:
    baris: tuple[str, ...]
    tak_sejajar_token: tuple[str, ...]


def ekspor_conll(dokumen_semua: list) -> HasilEksporConll:
    baris: list[str] = []
    tak_sejajar: list[str] = []
    for dokumen in dokumen_semua:
        token = tokenkan(dokumen.teks)
        tepi = {t.mulai for t in token}
        if any(r.mulai not in tepi for r in dokumen.rentang):
            tak_sejajar.append(dokumen.id_dokumen)
            continue
        baris.append("x")
    return HasilEksporConll(baris=tuple(baris), tak_sejajar_token=tuple(tak_sejajar))
'''

MODUL_ANOTASI = '''"""Modul anotasi tiruan yang tidak mengenal token."""


def kumpulkan() -> None:
    return None
'''


def _pohon(
    tmp_path: Path,
    *,
    rentang: str = RENTANG_BERSIH,
    ekspor: str = EKSPOR_BERSIH,
    modul: str = MODUL_ANOTASI,
) -> Path:
    akar = tmp_path / "pohon"
    (akar / DIREKTORI_ANOTASI).mkdir(parents=True)
    (akar / BERKAS_RENTANG).write_text(rentang, encoding="utf-8")
    (akar / BERKAS_EKSPOR).write_text(ekspor, encoding="utf-8")
    (akar / DIREKTORI_ANOTASI / "batch.py").write_text(modul, encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_indeks_karakter(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    """Pernyataan yang **paling lemah** pada berkas ini; uji lain di bawahnya
    yang membuatnya berarti."""
    assert periksa_indeks_karakter(AKAR) == []


# ------------------------------------------------------------------- aturan 1


def test_rentang_tanpa_teks_kanonik_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1.** Tanpa teks kanoniknya, indeks token yang dipakai sebagai
    indeks karakter memotong tempat yang salah tanpa satu galat pun — sebab
    keduanya sama-sama bilangan bulat."""
    rusak = RENTANG_BERSIH.replace("    teks_kanonik: str\n", "")
    temuan = periksa_indeks_karakter(_pohon(tmp_path, rentang=rusak))
    assert temuan
    assert "teks_kanonik" in str(temuan[0])


def test_teks_kanonik_yang_tidak_pernah_dipotong_ditemukan(tmp_path: Path) -> None:
    """Saksi yang tidak pernah ditanya sama saja dengan tidak ada.

    Bentuk ini yang paling mungkin terjadi: bidangnya dipertahankan agar
    pemeriksa lulus, sementara pemeriksaan potongannya dihapus karena dianggap
    memperlambat.
    """
    rusak = RENTANG_BERSIH.replace(
        "        potongan = self.teks_kanonik[self.mulai : self.akhir]\n"
        "        if not potongan:\n"
        '            raise ValueError("rentang kosong")\n',
        "        pass\n",
    )
    temuan = periksa_indeks_karakter(_pohon(tmp_path, rentang=rusak))
    assert temuan
    assert "tidak memotongnya" in str(temuan[0])


def test_memotong_sesuatu_yang_lain_tidak_dihitung(tmp_path: Path) -> None:
    """Memotong untai **mana pun** tidak cukup — yang mengikat adalah memotong
    teks kanoniknya.

    Bentuk ini terjadi ketika seseorang memindahkan pemeriksaan ke potongan
    yang sudah tersimpan: `teks_rentang` dipotong ulang, dan yang dibandingkan
    adalah salinan dengan dirinya sendiri.
    """
    rusak = RENTANG_BERSIH.replace(
        "        potongan = self.teks_kanonik[self.mulai : self.akhir]",
        "        potongan = self.teks_rentang[0:1]",
    )
    temuan = periksa_indeks_karakter(_pohon(tmp_path, rentang=rusak))
    assert temuan
    assert "tidak memotongnya" in str(temuan[0])


def test_pohon_tanpa_direktori_anotasi(tmp_path: Path) -> None:
    """Aturan 3 diam ketika direktorinya tidak ada — bukan karena longgar,
    melainkan karena aturan 1 dan 2 sudah melaporkan berkasnya hilang.

    Dua aturan yang melaporkan hal yang sama membuat pembaca menghitung dua
    kekeliruan padahal hanya ada satu.
    """
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    temuan = periksa_indeks_karakter(akar)
    assert len(temuan) == 2
    assert all("tidak ditemukan" in str(t) for t in temuan)


def test_tipe_rentang_yang_dihapus_ditemukan(tmp_path: Path) -> None:
    rusak = RENTANG_BERSIH.replace("class RentangEntitas(BaseModel):", "class Lain(BaseModel):")
    assert periksa_indeks_karakter(_pohon(tmp_path, rentang=rusak))


def test_berkas_rentang_yang_hilang_ditemukan(tmp_path: Path) -> None:
    akar = _pohon(tmp_path)
    (akar / BERKAS_RENTANG).unlink()
    temuan = periksa_indeks_karakter(akar)
    assert temuan
    assert "tidak ditemukan" in str(temuan[0])


# ------------------------------------------------------------------- aturan 2


def test_ekspor_tanpa_laporan_ketaksejajaran_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2.** Di sinilah kedua sistem indeks bertemu.

    Menggeser rentang ke batas token terdekat menghasilkan berkas pelatihan
    yang benar bentuknya dan salah isinya — dan model yang dilatih atasnya
    belajar batas entitas yang tidak pernah ditandai siapa pun.
    """
    rusak = EKSPOR_BERSIH.replace("    tak_sejajar_token: tuple[str, ...]\n", "")
    rusak = rusak.replace(", tak_sejajar_token=tuple(tak_sejajar)", "")
    temuan = periksa_indeks_karakter(_pohon(tmp_path, ekspor=rusak))
    assert temuan
    assert "tak_sejajar_token" in str(temuan[0])


def test_ekspor_yang_melaporkan_tetapi_tetap_menulis_ditemukan(tmp_path: Path) -> None:
    """**Bentuk yang paling halus.** Laporan yang tidak mengubah apa pun tetap
    terbaca sebagai kendali yang bekerja — dan berkasnya tetap salah."""
    rusak = EKSPOR_BERSIH.replace(
        "            tak_sejajar.append(dokumen.id_dokumen)\n            continue\n",
        "            tak_sejajar.append(dokumen.id_dokumen)\n",
    )
    temuan = periksa_indeks_karakter(_pohon(tmp_path, ekspor=rusak))
    assert temuan
    assert "tidak dilewati" in str(temuan[0])


def test_continue_pada_gelung_lain_tidak_menutupi_pelewatan_yang_hilang(
    tmp_path: Path,
) -> None:
    """**Uji yang menutup kelemahan pemeriksa ini sendiri.**

    Rumusan pertama aturan 2 mencari `continue` mana pun di dalam gelung mana
    pun, dan **lolos pada pohon sungguhan** meski pelewatannya dihapus — sebab
    modul ekspor memuat gelung lain yang kebetulan memakai `continue`. Uji
    mutasi yang menemukannya, bukan mata.

    Pohon di bawah meniru keadaan itu: pelewatannya dihapus, tetapi sebuah
    gelung lain tetap memakai `continue`.
    """
    rusak = EKSPOR_BERSIH.replace(
        "            tak_sejajar.append(dokumen.id_dokumen)\n            continue\n",
        "            tak_sejajar.append(dokumen.id_dokumen)\n",
    )
    rusak += """

def bersihkan(nama_semua: list) -> list:
    hasil = []
    for nama in nama_semua:
        if not nama:
            continue
        hasil.append(nama)
    return hasil
"""
    temuan = periksa_indeks_karakter(_pohon(tmp_path, ekspor=rusak))
    assert temuan
    assert "tidak dilewati" in str(temuan[0])


def test_daftar_pelaporan_dibaca_dari_kata_kunci_bukan_dari_nama_peubah(
    tmp_path: Path,
) -> None:
    """Peubahnya boleh dinamai apa saja; yang mengikat adalah kata kunci hasil.

    Diuji dengan menamainya berbeda dari kelaziman — pemeriksa yang menebak
    dari nama peubah akan gagal di sini.
    """
    import re

    # Hanya peubahnya yang diganti; kata kunci `tak_sejajar_token` dibiarkan,
    # sebab yang diuji justru bahwa keduanya boleh berbeda.
    lain = re.sub(r"\btak_sejajar\b", "meleset_semua", EKSPOR_BERSIH)
    assert "tak_sejajar_token" in lain
    assert "meleset_semua" in lain
    assert periksa_indeks_karakter(_pohon(tmp_path, ekspor=lain)) == []


def test_pembungkus_tuple_tidak_terbaca_sebagai_nama_daftar(tmp_path: Path) -> None:
    """`tuple(tak_sejajar)` memuat dua nama, dan yang pertama ditemui penelusur
    pohon adalah `tuple` — nama fungsinya.

    Cacat ini ada pada rumusan pertama dan membuat pemeriksa melaporkan temuan
    palsu pada pohon yang sehat. Pemeriksa yang berteriak pada pohon bersih
    akan dimatikan orang.
    """
    assert periksa_indeks_karakter(_pohon(tmp_path)) == []


def test_bidang_laporan_yang_ada_tetapi_tidak_pernah_diisi_ditemukan(
    tmp_path: Path,
) -> None:
    """Bidang laporan yang dideklarasikan tetapi tidak pernah diisi.

    Bentuk ini memuaskan pemeriksaan bidang pada aturan 2 sambil tidak
    melaporkan apa pun — laporan yang selalu kosong terbaca sebagai “tidak ada
    yang meleset”, dan itu kebalikan dari maksudnya.
    """
    rusak = EKSPOR_BERSIH.replace(
        ", tak_sejajar_token=tuple(tak_sejajar)", ", tak_sejajar_token=()"
    )
    temuan = periksa_indeks_karakter(_pohon(tmp_path, ekspor=rusak))
    assert temuan
    assert "tidak dilewati" in str(temuan[0])


def test_berkas_ekspor_yang_hilang_ditemukan(tmp_path: Path) -> None:
    akar = _pohon(tmp_path)
    (akar / BERKAS_EKSPOR).unlink()
    assert periksa_indeks_karakter(akar)


# ------------------------------------------------------------------- aturan 3


def test_modul_anotasi_yang_mengimpor_tokenisasi_ditemukan(tmp_path: Path) -> None:
    """**Aturan 3.** Yang tidak mengenal token tidak dapat memakai indeksnya."""
    rusak = "from src.nlp.praproses.tokenisasi import tokenkan\n\n" + MODUL_ANOTASI
    temuan = periksa_indeks_karakter(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert "mengimpor" in str(temuan[0])


def test_ekspor_boleh_mengimpor_tokenisasi(tmp_path: Path) -> None:
    """Perkecualiannya nyata dan beralasan: CoNLL memang berbaris per token.

    Aturan 2 yang menjaga perkecualian ini tidak menjadi pintu — dan itulah
    sebabnya keduanya dipasangkan.
    """
    assert periksa_indeks_karakter(_pohon(tmp_path)) == []


def test_ketiga_aturan_menyala_terpisah(tmp_path: Path) -> None:
    """Pohon yang ketiganya rusak menghasilkan temuan dari ketiga aturan,
    bukan satu temuan gabungan — sebab yang rusak menentukan seberapa jauh
    indeks token dapat berjalan sebelum tertahan."""
    rusak_rentang = RENTANG_BERSIH.replace("    teks_kanonik: str\n", "")
    rusak_ekspor = EKSPOR_BERSIH.replace("    tak_sejajar_token: tuple[str, ...]\n", "")
    rusak_modul = "from src.nlp.praproses.token import Token\n\n" + MODUL_ANOTASI
    temuan = periksa_indeks_karakter(
        _pohon(tmp_path, rentang=rusak_rentang, ekspor=rusak_ekspor, modul=rusak_modul)
    )
    assert len(temuan) == 3


# ---------------------------------------------------------------- pendaftaran


def test_c10_terdaftar_dengan_pemeriksa_bukan_fitur_pengunci() -> None:
    """C-10 berpindah dari `fitur_pengunci="003 perangkat anotasi"` menjadi
    `pemeriksa=`. Kodenya sudah ada sejak fitur 003; yang kurang pemeriksanya."""
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-10")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None


def test_dua_pasal_tersisa_dan_keduanya_menunggu_layar() -> None:
    """Uji ini semula berbunyi "tiga pasal tersisa" dan menyatakan bahwa
    sesudah C-10 **tidak ada lagi pasal yang dapat berpindah** tanpa `web/`
    atau tanpa model yang belum ada. Pernyataan itu **keliru**, dan
    kekeliruannya bertahan tiga fitur.

    C-14 dapat berpindah, dan alasan tunggunya sudah kedaluwarsa sejak fitur
    012 lolos Gerbang 4 — ketiadaan personalisasi baru bermakna sesudah fitur
    010, 011, dan 012 ada. Yang menyembunyikannya bukan kerumitan melainkan
    bentuk pencatatannya: alasan tunggu C-14 tertulis sebagai untai bebas
    ``"010 s.d. 013; sebagian dapat diperiksa lebih awal"``, dan untai bebas
    tidak dapat kedaluwarsa dengan sendirinya. Ia menyebut syaratnya sendiri
    dan tidak ada yang memeriksa apakah syarat itu sudah terpenuhi.

    Diganti, bukan dihapus. Yang tetap berlaku: kedua pasal yang **memang**
    tersisa sungguh menunggu sesuatu yang belum ada.
    """
    belum = {p.kode for p in DAFTAR_PASAL if p.pemeriksa is None}
    assert belum == {"C-01", "C-13"}
