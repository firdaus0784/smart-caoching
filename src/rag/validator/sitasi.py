"""Pemeriksaan sitasi — VS-01, VS-02, VS-04, VS-06, VS-08; R-01 s.d. R-05.

Lima dari sembilan pemeriksaan D-07 Bagian 6.1. VS-03 menyusul pada fitur 020;
ia menuntut kemiripan semantik, dan itu berarti model sematan serta ambang
BT-29.

## Dua tingkat pembuangan, dan bedanya bukan gradasi keparahan

D-07 Bagian 6.2 memisahkan keduanya:

- **VS-01, VS-02** gagal ketika model menyusun klaim yang tidak tertopang —
  kekeliruan **penyusunan**. Klaimnya dibuang; jawaban lanjut bila ringkasannya
  masih terisi. Karena itu keduanya **menunjuk klaim** yang bermasalah.
- **VS-04, VS-06** gagal ketika segmen yang tidak boleh terjangkau ternyata
  terjangkau — **gerbang yang bocor**. Seluruh jawaban dibuang tanpa perbaikan,
  dan dicatat sebagai insiden kepatuhan. Karena itu keduanya **tidak menunjuk
  klaim**: menunjuknya menyesatkan ke arah perbaikan sebagian, dan perbaikan
  sebagian menghasilkan jawaban yang tampak sehat di atas gerbang yang rusak.
- **VS-08** berada di antara keduanya: klaimnya **diturunkan** menjadi bacaan
  lanjutan, bukan dibuang (KD-15), sehingga ia menunjuk klaim.

## VS-08 tidak menyentuh keputusan BT-64

`docs/D14.md` Bagian 4.1 menyatakan arti `klaim[].peringkat_kepercayaan` pada
klaim campuran adalah **keputusan BT-64, bukan keputusan pelaksana**, dan
ketiga pilihan yang mungkin mengubah apa yang dilihat kepala sekolah pada klaim
yang sama.

`periksa_peringkat_klaim` karena itu tidak membaca bidang itu sama sekali. Ia
merumuskan pelanggaran atas **seluruh segmen penopang**: sebuah klaim melanggar
bila tidak satu pun penopangnya berperingkat kuat. Pernyataan itu benar pada
ketiga pilihan BT-64.

Yang paling mudah keliru di sini bukan aturannya melainkan arahnya. D-13 Bagian
6 menyatakan T3 *"boleh menopang, tetapi klaim memerlukan segmen T1 atau T2"* —
sehingga klaim yang ditopang T1 dan T3 sekaligus adalah bentuk yang **benar**.
Validator yang menolaknya membuang jawaban sah, lalu dilonggarkan orang, dan
yang longgar bersamanya adalah VS-08.

## Rujukan yang tidak dikenal tidak pernah menyelamatkan klaim

Klaim yang menyebut id yang tidak ada di antara segmen terambil sudah gagal
VS-02. VS-08 tidak boleh menyelamatkannya dengan menganggap rujukan tak dikenal
sebagai penopang kuat — bila ia menganggapnya kuat, model yang mengarang satu
id dapat meloloskan klaim yang seluruh penopang nyatanya berperingkat lemah.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.kamus.segmen import IndeksTujuan, StatusKeberlakuan
from src.rag.validator.keluaran import KeluaranModel, SegmenRujukan
from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status


def _peta(segmen: Sequence[SegmenRujukan]) -> dict[str, SegmenRujukan]:
    return {s.id_segmen: s for s in segmen}


def periksa_dasar_klaim(keluaran: KeluaranModel) -> HasilPemeriksaan:
    """**VS-01** — setiap klaim memiliki minimal satu `id_segmen` (R-01).

    `Klaim` sudah menegakkannya sebagai tipe; pemeriksaan ini tetap ada sebab
    keluaran model tiba sebagai data, bukan sebagai objek yang sudah
    tervalidasi. Yang tidak dapat dibentuk tetap dapat **diminta**.

    Keluaran tanpa klaim sama sekali **lulus**: jawaban tanpa klaim adalah
    bentuk sah `tidak_ditemukan` (D-14 Bagian 4.1), dan penolakan yang sah
    bukan kegagalan validator.
    """
    tanpa_dasar = tuple(k.id_klaim for k in keluaran.klaim if not k.id_segmen)
    if tanpa_dasar:
        return HasilPemeriksaan(
            kode=KodePemeriksaan.VS_01,
            status=Status.GAGAL,
            alasan="klaim tanpa id_segmen — klaim tanpa dasar (D-07 VS-01)",
            id_klaim_bermasalah=tanpa_dasar,
        )
    return HasilPemeriksaan(
        kode=KodePemeriksaan.VS_01,
        status=Status.LULUS,
        alasan=f"{len(keluaran.klaim)} klaim, seluruhnya membawa id_segmen",
    )


def periksa_rujukan_nyata(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> HasilPemeriksaan:
    """**VS-02** — setiap `id_segmen` benar-benar ada di antara segmen yang
    diambil (R-02).

    Diperiksa terhadap **segmen yang diambil**, bukan terhadap daftar id pada
    klaim lain. Versi yang memeriksa kesalingcocokan antarklaim meloloskan
    model yang mengarang satu id lalu memakainya dua kali — dan kegagalan itu
    berarti "rujukan mengada-ada" pada D-07 Bagian 6.1.
    """
    dikenal = _peta(segmen).keys()
    mengarang = tuple(
        k.id_klaim for k in keluaran.klaim if any(i not in dikenal for i in k.id_segmen)
    )
    if mengarang:
        return HasilPemeriksaan(
            kode=KodePemeriksaan.VS_02,
            status=Status.GAGAL,
            alasan="klaim merujuk id_segmen yang tidak ada di antara segmen terambil — "
            "rujukan mengada-ada (D-07 VS-02)",
            id_klaim_bermasalah=mengarang,
        )
    return HasilPemeriksaan(
        kode=KodePemeriksaan.VS_02,
        status=Status.LULUS,
        alasan=f"seluruh rujukan ada di antara {len(segmen)} segmen terambil",
    )


def periksa_indeks_metadata(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> HasilPemeriksaan:
    """**VS-04** — tidak ada segmen `indeks_metadata` menjadi dasar klaim
    (R-03, C-02, KL-01).

    Keberadaan segmen metadata di antara segmen terambil **tidak** dilarang: ia
    bahan `bacaan_lanjutan`, dan D-14 Bagian 6 menetapkannya sebagai tempat
    satu-satunya bagi sumber itu. Yang dilarang adalah ia menjadi **dasar
    klaim**. Validator yang menolak keberadaannya menutup pekerjaan yang D-14
    tuntut, lalu dimatikan orang.
    """
    peta = _peta(segmen)
    melanggar = [
        i
        for k in keluaran.klaim
        for i in k.id_segmen
        if i in peta and peta[i].indeks_asal is IndeksTujuan.METADATA
    ]
    if melanggar:
        return HasilPemeriksaan(
            kode=KodePemeriksaan.VS_04,
            status=Status.GAGAL,
            alasan="segmen dari indeks_metadata dipakai sebagai dasar klaim — "
            f"pelanggaran KL-01 dan C-02, insiden kepatuhan; segmen: {sorted(set(melanggar))}",
        )
    return HasilPemeriksaan(
        kode=KodePemeriksaan.VS_04,
        status=Status.LULUS,
        alasan="seluruh dasar klaim berasal dari indeks utama",
    )


def periksa_keberlakuan(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> HasilPemeriksaan:
    """**VS-06** — tidak ada segmen dari regulasi dicabut yang dipakai (R-04,
    C-07, KL-07).

    **Hanya `dicabut`.** D-07 Bagian 4.5 menetapkan segmen berstatus `diubah`
    tetap dipakai, dengan kewajiban menampilkan penanda dan rujukan
    pengubahnya (FR-F14). Validator yang menolak keduanya membuang jawaban yang
    sah — dan penanda keberlakuan justru dibangun untuk keadaan itu.

    Ketegasan terhadap `dicabut` disengaja, dan D-07 menyebut alasannya:
    menjawab berdasarkan aturan yang sudah dicabut adalah bentuk kekeliruan
    yang paling merugikan, **karena jawabannya terdengar berdasar**.
    """
    peta = _peta(segmen)
    dicabut = [
        i
        for k in keluaran.klaim
        for i in k.id_segmen
        if i in peta and peta[i].status_keberlakuan is StatusKeberlakuan.DICABUT
    ]
    if dicabut:
        return HasilPemeriksaan(
            kode=KodePemeriksaan.VS_06,
            status=Status.GAGAL,
            alasan="segmen dari regulasi berstatus dicabut dipakai sebagai dasar klaim — "
            f"pelanggaran PR-06 dan C-07, insiden kepatuhan; segmen: {sorted(set(dicabut))}",
        )
    return HasilPemeriksaan(
        kode=KodePemeriksaan.VS_06,
        status=Status.LULUS,
        alasan="tidak ada dasar klaim dari regulasi berstatus dicabut",
    )


def periksa_peringkat_klaim(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> HasilPemeriksaan:
    """**VS-08** — tidak ada klaim bersandar tunggal pada T3 atau T4 (R-05,
    C-19, FR-F15).

    Sebuah klaim melanggar bila **tidak satu pun** penopangnya berperingkat
    kuat. Rumusan itu sengaja tidak menyentuh `klaim[].peringkat_kepercayaan`,
    yang artinya keputusan BT-64 — lihat uraian modul.

    Rujukan yang tidak dikenal **tidak** dihitung sebagai penopang kuat: ia
    sudah gagal VS-02, dan menghitungnya kuat akan membuat satu id karangan
    menyelamatkan klaim yang seluruh penopang nyatanya lemah.
    """
    peta = _peta(segmen)
    bersandar_lemah = tuple(
        klaim.id_klaim
        for klaim in keluaran.klaim
        if not any(
            i in peta and not peta[i].peringkat_kepercayaan.lemah for i in klaim.id_segmen
        )
    )
    if bersandar_lemah:
        return HasilPemeriksaan(
            kode=KodePemeriksaan.VS_08,
            status=Status.GAGAL,
            alasan="klaim bersandar tunggal pada segmen peringkat T3 atau T4 — "
            "diturunkan menjadi bacaan lanjutan (FR-F15, C-19, KD-15)",
            id_klaim_bermasalah=bersandar_lemah,
        )
    return HasilPemeriksaan(
        kode=KodePemeriksaan.VS_08,
        status=Status.LULUS,
        alasan="setiap klaim ditopang sekurangnya satu segmen T1 atau T2",
    )
