"""Uji jalur penjawaban — B-1 fitur 021, R-05 s.d. R-12.

## Yang diuji bukan bahwa jalur menghasilkan jawaban

Yang diuji: jalur **tidak dapat** memanggil model ketika buktinya tidak cukup,
**tidak dapat** mengambil atas pertanyaan di luar domain, dan **tidak dapat**
menayangkan keluaran yang ditahan validator.

## Dua di antaranya diuji sebagai ketiadaan panggilan

"Bukti tidak cukup lalu berhenti" lulus juga pada implementasi yang memanggil
model lalu membuang hasilnya — nilai kembaliannya sama persis. Yang membedakan
hanya apakah panggilannya terjadi, dan itu biaya, jejak `logbook/`, serta satu
kesempatan bagi C-18 untuk dilanggar. Adaptor dan sumber tiruan di bawah karena
itu **menghitung**, bukan sekadar menjawab.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.api.tanya import AlasanBerhenti, BahanSegmen, HasilTanya, Jalur, baca_keluaran
from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan
from src.llm.adaptor.dasar import AdaptorDasar, Permintaan
from src.llm.pembungkus import Pembungkus
from src.llm.tipe import Konfigurasi
from src.llm.tipe import Tanggapan as TanggapanModel
from src.logbook.versi import Versi as VersiLogbook
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial
from src.rag.jawaban.tanggapan import StatusDasar, Versi
from src.rag.pengambilan.kandidat import HasilSumber, Kandidat, SumberKandidat
from src.rag.pengambilan.kecukupan import AmbangKecukupan, CatatanKalibrasi, PenilaianKecukupan
from src.rag.validator.keluaran import SegmenRujukan

# ------------------------------------------------------------------- tiruan


class SumberTiruan(SumberKandidat):
    """Menghitung pencariannya. Jalur yang mengambil atas pertanyaan di luar
    domain hanya terlihat dari sini."""

    def __init__(self, nama: str, hasil: tuple[Kandidat, ...]) -> None:
        self._nama = nama
        self._hasil = hasil
        self.jumlah_cari = 0

    @property
    def nama(self) -> str:
        return self._nama

    @property
    def indeks_tujuan(self) -> IndeksTujuan:
        return IndeksTujuan.UTAMA

    @property
    def versi_indeks(self) -> str:
        return "uji-1"

    def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        self.jumlah_cari += 1
        return HasilSumber(
            nama_sumber=self.nama,
            versi_indeks=self.versi_indeks,
            peringkat=self._hasil[:batas],
        )


class AdaptorTerhitung(AdaptorDasar):
    """Menghitung pengirimannya dan menyimpan permintaan terakhir."""

    def __init__(self, teks: str) -> None:
        self._teks = teks
        self.jumlah_kirim = 0
        self.terakhir: Permintaan | None = None

    def kirim(self, permintaan: Permintaan) -> TanggapanModel:
        self.jumlah_kirim += 1
        self.terakhir = permintaan
        saat = datetime(2026, 8, 13, 3, 0, tzinfo=UTC)
        return TanggapanModel(
            teks=self._teks,
            versi_model="tiruan-1",
            waktu_mulai=saat,
            waktu_selesai=saat,
            biaya=0.0,
            id_jejak="jejak-1",
        )


KELUARAN_SAH = json.dumps(
    {
        "ringkasan_tindakan": ["Susun jadwal supervisi bulanan."],
        "penjelasan": "Supervisi rutin menjaga mutu pembelajaran.",
        "klaim": [
            {
                "id_klaim": "K1",
                "teks": "Supervisi akademik dijadwalkan setiap bulan.",
                "id_segmen": ["S1"],
            }
        ],
        "catatan_keberlakuan": "",
    }
)

KELUARAN_TANPA_SITASI = json.dumps(
    {
        "ringkasan_tindakan": ["Susun jadwal supervisi bulanan."],
        "penjelasan": "Supervisi rutin menjaga mutu pembelajaran.",
        "klaim": [
            {
                "id_klaim": "K1",
                "teks": "Supervisi akademik dijadwalkan setiap bulan.",
                "id_segmen": ["S9"],
            }
        ],
        "catatan_keberlakuan": "",
    }
)


def _bahan(
    id_segmen: str = "S1",
    *,
    indeks: IndeksTujuan = IndeksTujuan.UTAMA,
    peringkat: Peringkat = Peringkat.T1,
) -> BahanSegmen:
    return BahanSegmen(
        rujukan=SegmenRujukan(
            id_segmen=id_segmen,
            peringkat_kepercayaan=peringkat,
            indeks_asal=indeks,
            status_keberlakuan=StatusKeberlakuan.BERLAKU,
            tautan="https://contoh.id/sumber",
        ),
        teks="Kepala sekolah menyusun jadwal supervisi akademik tiap bulan.",
    )


def _penilai() -> PenilaianKecukupan:
    return PenilaianKecukupan(
        AmbangKecukupan(
            # Ambang uji dipilih **terhadap keluaran RRF**, bukan terhadap
            # skor BM25. Penggabungan menghasilkan `Σ 1/(k+peringkat)` dengan
            # k=60: satu sumber pada peringkat 1 menyumbang 0,0164 dan dua
            # sumber menyumbang 0,0328. Ambang yang disalin dari intuisi skor
            # kemiripan (0,2 atau 0,4) menolak **seluruh** segmen — dan itu
            # persis temuan SEA-BED yang membuat kecukupan bukti dibuat
            # berbasis peringkat sejak fitur 007.
            menengah=0.02,
            tinggi=0.03,
            kalibrasi=CatatanKalibrasi(
                tanggal=date(2026, 8, 13),
                gold_set="uji-021-v1",
                jumlah_pertanyaan=10,
                pemutus="uji",
                prosedur="Ambang uji; kalibrasi sungguhan mengikuti BT-29.",
            ),
        )
    )


def _jalur(
    tmp_path: Path,
    *,
    teks_model: str = KELUARAN_SAH,
    kandidat: tuple[Kandidat, ...] = (Kandidat(id_segmen="S1", skor=0.9),),
    kandidat_kedua: tuple[Kandidat, ...] | None = None,
) -> tuple[Jalur, tuple[SumberTiruan, ...], AdaptorTerhitung]:
    # **Dua sumber, bukan satu.** ADR-03 menolak pengambilan leksikal saja
    # maupun vektor saja, dan `gabung_peringkat` menegakkannya. Jalur ini
    # mewarisi tuntutan itu apa adanya — sisi vektornya menyusul pada fitur
    # 019 dan tidak mengubah urutan tahap mana pun.
    sumber = (
        SumberTiruan("leksikal", kandidat),
        SumberTiruan("vektor", kandidat if kandidat_kedua is None else kandidat_kedua),
    )
    adaptor = AdaptorTerhitung(teks_model)
    pembungkus = Pembungkus(
        adaptor,
        tmp_path,
        VersiLogbook(
            versi_kode="uji",
            versi_model="tiruan-1",
            versi_indeks="uji-1",
            versi_skema_anotasi="belum-berlaku",
            pembagian_data="belum-berlaku",
        ),
    )
    jalur = Jalur(
        sumber=list(sumber),
        penilai=_penilai(),
        pembungkus=pembungkus,
        konfigurasi=Konfigurasi(
            nama_model="tiruan", versi_model="tiruan-1", suhu=0.0, batas_token=512
        ),
    )
    return jalur, sumber, adaptor


VERSI = Versi(model="tiruan-1", indeks="uji-1", kode="uji-1")
KREDENSIAL = Kredensial(
    nama="penjawaban",
    baca=frozenset({Area.KORPUS}),
    tulis=frozenset(),
    indeks=frozenset({IndeksTujuan.UTAMA}),
)


def _jawab(jalur: Jalur, pertanyaan: str, **ganti: object) -> HasilTanya:
    argumen: dict[str, object] = {
        "kredensial": KREDENSIAL,
        "bahan": {"S1": _bahan()},
        "segmen_resmi": frozenset({"S1"}),
        "id_pesan": "PSN-1",
        "versi": VERSI,
    }
    argumen.update(ganti)
    return jalur.jawab(pertanyaan, **argumen)  # type: ignore[arg-type]


# ------------------------------------------------- R-07 · di luar domain lebih dulu


def test_di_luar_domain_berhenti_sebelum_pengambilan(tmp_path: Path) -> None:
    """**Uji urutan, bukan uji nilai kembalian.**

    Pertanyaan di luar domain yang tetap diambilkan membakar pencarian dan,
    lebih buruk, dapat menemukan segmen yang membuatnya terlihat dapat dijawab.
    """
    jalur, sumber, adaptor = _jalur(tmp_path)
    hasil = _jawab(jalur, "Saya terdakwa dalam perkara pidana, apa hak saya?")
    assert hasil.alasan_berhenti is AlasanBerhenti.DI_LUAR_DOMAIN
    assert sum(s.jumlah_cari for s in sumber) == 0
    assert adaptor.jumlah_kirim == 0


def test_di_luar_domain_berbentuk_jawaban_bukan_galat(tmp_path: Path) -> None:
    """D-14 Bagian 4.1: keseragaman bentuk yang membuat layar D-05
    menampilkannya sebagai jawaban sah."""
    jalur, _, _ = _jalur(tmp_path)
    hasil = _jawab(jalur, "Saya pasien rumah sakit, obat apa yang cocok bagi saya?")
    assert hasil.tanggapan.status_dasar is StatusDasar.DI_LUAR_DOMAIN
    assert hasil.tanggapan.penjelasan


# ------------------------------------------- R-08 · bukti kurang, tanpa model


def test_bukti_tidak_cukup_tidak_memanggil_model(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**

    Diuji sebagai **ketiadaan panggilan**. Implementasi yang memanggil model
    lalu membuang hasilnya mengembalikan nilai yang sama persis; yang
    membedakan hanya apakah panggilannya terjadi.
    """
    # Segmen yang hanya ditemukan **satu** sumber menyumbang 1/61 = 0,0164,
    # di bawah ambang menengah 0,02. Itu keadaan yang nyata, bukan angka yang
    # dipaksakan: segmen yang hanya muncul pada satu pengambil memang bukti
    # yang lebih lemah, dan itu sebabnya RRF menjumlahkan.
    jalur, sumber, adaptor = _jalur(tmp_path, kandidat_kedua=())
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.alasan_berhenti is AlasanBerhenti.BUKTI_TIDAK_CUKUP
    assert sum(s.jumlah_cari for s in sumber) == 2
    assert adaptor.jumlah_kirim == 0


def test_tanpa_segmen_sama_sekali_juga_tidak_memanggil_model(tmp_path: Path) -> None:
    jalur, _, adaptor = _jalur(tmp_path, kandidat=())
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.alasan_berhenti is AlasanBerhenti.BUKTI_TIDAK_CUKUP
    assert adaptor.jumlah_kirim == 0


# ------------------------------------------------------------ R-09 · C-19


def test_keluaran_yang_ditahan_validator_tidak_menjadi_tanggapan(tmp_path: Path) -> None:
    """C-19. Klaim yang menunjuk segmen yang tidak diambil gagal VS-01, dan
    jawaban yang ditahan tidak boleh punya jalan menuju layar."""
    jalur, _, _ = _jalur(tmp_path, teks_model=KELUARAN_TANPA_SITASI)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.alasan_berhenti is AlasanBerhenti.DITAHAN_VALIDATOR
    assert hasil.tanggapan.status_dasar is StatusDasar.TIDAK_DITEMUKAN
    assert hasil.tanggapan.klaim == ()
    assert hasil.tanggapan.ringkasan_tindakan == ()


def test_jawaban_sah_pun_berhenti_karena_pemeriksaan_belum_dapat_dijalankan(
    tmp_path: Path,
) -> None:
    """**Temuan fitur ini, dan ia wajib terbaca sebagai temuan.**

    Bukti cukup, keluaran sah, seluruh pemeriksaan yang dapat dijalankan lulus
    — dan jalur tetap berhenti. VS-03, VS-05, dan VS-07 berstatus
    `BELUM_DAPAT_DIPERIKSA` sampai fitur 020 ada, dan status itu
    **menghalangi**, sama seperti gagal.

    Itu perilaku yang benar: pemeriksaan yang belum berjalan tidak boleh
    terbaca sebagai lulus (fitur 008). Yang tidak boleh adalah ia terhitung
    sebagai penahanan validator — pemiliknya berbeda, dan laporan yang
    menyamakannya akan membuat seseorang melonggarkan validator dengan angka
    yang benar. C-16 melarangnya justru untuk keadaan seperti ini.
    """
    jalur, _, adaptor = _jalur(tmp_path)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.alasan_berhenti is AlasanBerhenti.MENUNGGU_PEMERIKSAAN_MODEL
    assert adaptor.jumlah_kirim == 1
    assert {k.value for k in hasil.menunggu_model} == {"VS-03", "VS-05", "VS-07"}


def test_penahanan_sungguhan_tidak_tertukar_dengan_yang_menunggu_model(
    tmp_path: Path,
) -> None:
    """Klaim yang menunjuk segmen tak terambil gagal VS-01 — satu pemeriksaan
    yang menghalangi di luar ketiga yang menunggu model. Perbaikannya
    pengambilan, dan alasannya wajib menyebutkan itu."""
    jalur, _, _ = _jalur(tmp_path, teks_model=KELUARAN_TANPA_SITASI)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.alasan_berhenti is AlasanBerhenti.DITAHAN_VALIDATOR


# --------------------------------------------- keluaran tidak terbaca · alasan ke-4


@pytest.mark.parametrize(
    "teks",
    ["bukan json sama sekali", "[1, 2, 3]", '{"ringkasan_tindakan": "bukan daftar"}'],
)
def test_keluaran_tidak_terbaca_menjadi_alasan_tersendiri(tmp_path: Path, teks: str) -> None:
    """Bukan bukti yang kurang dan bukan penahanan validator — validator tidak
    pernah sempat berjalan. Yang memperbaikinya instruksi atau model."""
    jalur, _, _ = _jalur(tmp_path, teks_model=teks)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.alasan_berhenti is AlasanBerhenti.KELUARAN_TIDAK_TERBACA


def test_keluaran_tidak_terbaca_tidak_melempar_galat(tmp_path: Path) -> None:
    """Galat mengundang pemanggil membungkusnya dengan `try`, dan pada akhirnya
    seseorang menuliskan `except: pass` di sekeliling seluruh jalur."""
    jalur, _, _ = _jalur(tmp_path, teks_model="{{{")
    assert _jawab(jalur, "Bagaimana menyusun jadwal supervisi?") is not None


def test_baca_keluaran_mengembalikan_none_bukan_melempar() -> None:
    assert baca_keluaran("bukan json") is None
    assert baca_keluaran("null") is None
    assert baca_keluaran(json.dumps({"bidang_asing": 1})) is None


def test_lima_alasan_berhenti_dengan_pemilik_perbaikan_berbeda() -> None:
    """Lima pemilik perbaikan: tidak ada, kurasi, instruksi/model, pengambilan,
    fitur 020. Menyamakan dua di antaranya membuat perbaikannya tidak dapat
    dibedakan pada laporan mana pun."""
    assert {a.value for a in AlasanBerhenti} == {
        "di_luar_domain",
        "bukti_tidak_cukup",
        "keluaran_tidak_terbaca",
        "ditahan_validator",
        "menunggu_pemeriksaan_model",
    }


# ------------------------------------------------------- R-11, C-02, C-18


def test_segmen_metadata_tidak_pernah_menjadi_data(tmp_path: Path) -> None:
    """Lapisan kedua C-02. D-07 Bagian 7: sumber `indeks_metadata` tidak
    dipakai menyusun jawaban; ia hanya muncul sebagai `bacaan_lanjutan`."""
    jalur, _, adaptor = _jalur(
        tmp_path,
        kandidat=(Kandidat(id_segmen="S1", skor=0.9), Kandidat(id_segmen="S2", skor=0.8)),
    )
    _jawab(
        jalur,
        "Bagaimana menyusun jadwal supervisi akademik?",
        bahan={"S1": _bahan(), "S2": _bahan("S2", indeks=IndeksTujuan.METADATA)},
        segmen_resmi=frozenset({"S1"}),
    )
    assert adaptor.terakhir is not None
    assert [d.id_segmen for d in adaptor.terakhir.data] == ["S1"]


def test_teks_segmen_tidak_pernah_masuk_posisi_instruksi(tmp_path: Path) -> None:
    """C-18. Diuji atas `Permintaan` sungguhan: bila permintaan berupa satu
    untai, pemeriksaan ini berubah menjadi pemeriksaan mata."""
    jalur, _, adaptor = _jalur(tmp_path)
    _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert adaptor.terakhir is not None
    assert "jadwal supervisi akademik tiap bulan" not in adaptor.terakhir.instruksi.teks
    assert any("jadwal supervisi akademik tiap bulan" in d.teks for d in adaptor.terakhir.data)


def test_segmen_tanpa_bahan_dilewati_bukan_dikosongkan(tmp_path: Path) -> None:
    """Bahan kosong menghasilkan `Data` bertekst kosong yang tetap dihitung
    model sebagai segmen pendukung, dan klaim yang bersandar padanya lolos
    VS-01."""
    jalur, _, adaptor = _jalur(
        tmp_path,
        kandidat=(Kandidat(id_segmen="S1", skor=0.9), Kandidat(id_segmen="S7", skor=0.8)),
    )
    _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert adaptor.terakhir is not None
    assert [d.id_segmen for d in adaptor.terakhir.data] == ["S1"]


# --------------------------------------------------------- R-12 · utang terlihat


def test_pemeriksaan_menunggu_model_ikut_pada_hasil(tmp_path: Path) -> None:
    """FR-F16. Daftarnya dibaca dari pemiliknya di `src/rag/validator/`, bukan
    ditulis ulang pada jalur — daftar kedua akan tertinggal pada hari fitur 020
    memindahkan satu kode keluar darinya, dan yang tertinggal adalah yang
    menyatakan utang sudah lunas."""
    jalur, _, _ = _jalur(tmp_path)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert {k.value for k in hasil.menunggu_model} == {"VS-03", "VS-05", "VS-07"}


def test_menunggu_model_ikut_juga_ketika_ditahan(tmp_path: Path) -> None:
    """Utang tidak lunas karena jawabannya ditahan."""
    jalur, _, _ = _jalur(tmp_path, teks_model=KELUARAN_TANPA_SITASI)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")
    assert hasil.menunggu_model


# ------------------------------------------------------------- R-10 · C-17


def test_jalur_tanpa_parameter_alat() -> None:
    """C-17 diwujudkan sebagai **ketiadaan**. Kemampuan yang tidak dapat
    dinyatakan tidak dapat dipakai."""
    terlarang = {"alat", "tool", "fungsi", "kirim_keluar", "webhook", "tulis"}
    permukaan = {n for n in dir(Jalur) if not n.startswith("_")}
    assert not (permukaan & terlarang)
    naskah = Path("src/api/tanya.py").read_text(encoding="utf-8")
    assert "requests" not in naskah
    assert "open(" not in naskah


# --------------------------------------------------------------- R-06 · bentuk


def test_hasil_tanya_beku_dan_tanpa_bidang_tambahan() -> None:
    """Bidang tambahan pada hasil jalur adalah tempat penilaian berpindah ke
    pemanggil, dan pemanggil tidak terikat konstitusi."""
    with pytest.raises(ValidationError):
        HasilTanya(
            tanggapan=__import__(
                "src.rag.jawaban.tanggapan", fromlist=["Tanggapan"]
            ).Tanggapan.tolak_domain(id_pesan="P", versi=VERSI),
            skor_keyakinan=0.9,  # type: ignore[call-arg]
        )


def test_pertanyaan_kosong_ditolak(tmp_path: Path) -> None:
    """Kueri kosong **bukan** di luar domain: ia pemanggilan yang keliru, dan
    menyamakannya membuat pengguna yang menekan kirim tanpa mengetik menerima
    keterangan cakupan yang tidak relevan."""
    jalur, _, _ = _jalur(tmp_path)
    with pytest.raises(ValueError):
        _jawab(jalur, "   ")


# ------------------------------------------ jalur sukses, sebagaimana fitur 020 kelak


def test_jalur_menyusun_tanggapan_ketika_kesembilan_pemeriksaan_lulus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Satu-satunya jalan menguji cabang sukses hari ini — dan yang digantikan
    **hanya** yang fitur 020 akan sediakan.

    VS-03, VS-05, dan VS-07 berstatus `BELUM_DAPAT_DIPERIKSA` sampai fitur 020
    ada, sehingga `validasi()` sungguhan tidak pernah mengembalikan
    `JawabanTervalidasi`. Yang diganti di sini adalah **isi ketiga pemeriksaan
    itu saja**; `validasi()` tetap berjalan apa adanya dan tetap yang membentuk
    `JawabanTervalidasi`.

    Dua hal sengaja **tidak** dilakukan: `JawabanTervalidasi` tidak dibentuk
    langsung di uji, dan `Jalur` tidak diberi validator yang dapat disuntikkan.
    Keduanya akan menguji cabangnya sambil membatalkan justru yang membuat
    cabang itu aman — C-19 berdiri pada kenyataan bahwa `susun()` tidak
    menerima apa pun selain keluaran validator.

    Uji ini **dihapus ketika fitur 020 mendarat**, digantikan jalur sungguhan.
    """
    from src.rag.validator import validator as modul_validator
    from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status

    def lulus_seluruhnya(
        keluaran: object, *, segmen: object
    ) -> dict[KodePemeriksaan, HasilPemeriksaan]:
        return {
            kode: HasilPemeriksaan(
                kode=kode, status=Status.LULUS, alasan="disediakan fitur 020 pada uji ini"
            )
            for kode in (KodePemeriksaan.VS_03, KodePemeriksaan.VS_05, KodePemeriksaan.VS_07)
        }

    monkeypatch.setattr(modul_validator, "pemeriksaan_menunggu_model", lulus_seluruhnya)

    jalur, _, adaptor = _jalur(tmp_path)
    hasil = _jawab(jalur, "Bagaimana menyusun jadwal supervisi akademik?")

    assert hasil.alasan_berhenti is None
    assert adaptor.jumlah_kirim == 1
    assert hasil.tanggapan.ringkasan_tindakan == ("Susun jadwal supervisi bulanan.",)
    assert [k.id_segmen for k in hasil.tanggapan.klaim] == [("S1",)]
    assert hasil.tanggapan.penafian
