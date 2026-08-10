"""Daftar pasal C-01 s.d. C-20 beserta pemeriksa atau fitur penguncinya — R-15.

Daftar ini adalah yang membuat `make compliance` tidak dapat berbohong.

Setiap pasal membawa **tepat satu** dari dua hal: pemeriksa yang dapat
dijalankan, atau nama fitur yang kelak mengaktifkan pemeriksaannya. Tidak
pernah keduanya, tidak pernah tidak keduanya. Pasal yang sudah punya pemeriksa
tetapi masih membawa alasan menunggu adalah tempat menyembunyikan pekerjaan;
pasal tanpa keduanya adalah pasal yang terlupa.

Pada fitur 001 sebagian besar pasal belum dapat diperiksa mesin karena
komponen yang dijaganya belum ada. Itu keadaan yang jujur dan wajib terlihat.
`make compliance` yang melaporkan "lulus" dalam keadaan itu adalah laporan
palsu — dan laporan palsu lebih berbahaya daripada tidak ada laporan, karena
ia menghentikan kewaspadaan. Ini pelajaran TA-01 pada `docs/D00.md` Bagian
7.10, diterapkan pada perkakas alih-alih pada sistem.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan
from perkakas.pemeriksa.cakupan import periksa_cakupan
from perkakas.pemeriksa.catatan_versi import periksa_catatan_versi
from perkakas.pemeriksa.impor_ocr import periksa_impor_ocr
from perkakas.pemeriksa.impor_penyedia import periksa_impor_penyedia
from perkakas.pemeriksa.ketergantungan import periksa_ketergantungan
from perkakas.pemeriksa.logbook_tambah_saja import periksa_logbook_tambah_saja
from perkakas.pemeriksa.nama_terlarang import periksa_nama_terlarang
from perkakas.pemeriksa.pemisahan_indeks import periksa_pemisahan_indeks
from perkakas.pemeriksa.pemisahan_instruksi import periksa_pemisahan_instruksi
from perkakas.pemeriksa.pemisahan_penyimpanan import periksa_pemisahan_penyimpanan
from perkakas.pemeriksa.tanpa_kemampuan_bertindak import periksa_tanpa_kemampuan_bertindak

Pemeriksa = Callable[[Path], list[Temuan]]


def _c09(akar: Path) -> list[Temuan]:
    """C-09 diperiksa dari tiga sisi.

    Kelengkapan jejak versi pada catatan yang sudah ada, keutuhan mesin
    pencatatnya, dan — sejak fitur 015 — ketunggalan tempat pemanggilan mesin
    OCR. Catatan yang lengkap di atas penulis yang dapat menimpa bukan jaminan
    apa pun, dan begitu pula catatan yang lengkap atas keluaran yang sebagian
    dihasilkan di luar jangkauan pencatatnya.
    """
    return [
        *periksa_catatan_versi(akar),
        *periksa_logbook_tambah_saja(akar),
        *periksa_impor_ocr(akar),
    ]


@dataclass(frozen=True)
class Pasal:
    kode: str
    ringkas: str
    pemeriksa: Pemeriksa | None = None
    fitur_pengunci: str | None = None


DAFTAR_PASAL: tuple[Pasal, ...] = (
    Pasal(
        "C-01",
        "klaim manajerial tidak tayang tanpa sitasi terverifikasi",
        fitur_pengunci="008 validator sitasi",
    ),
    Pasal(
        "C-02",
        "segmen berlisensi tertutup tidak masuk konteks LLM",
        pemeriksa=periksa_pemisahan_indeks,
    ),
    Pasal(
        "C-03",
        "layanan RAG dan pelatihan tanpa akses area karantina",
        pemeriksa=periksa_pemisahan_penyimpanan,
    ),
    Pasal(
        "C-04",
        "telemetri tidak merekam tanpa persetujuan aktif",
        fitur_pengunci="012 telemetri",
    ),
    Pasal(
        "C-05",
        "kunci pseudonim terpisah dari data perilaku",
        fitur_pengunci="012 telemetri",
    ),
    Pasal(
        "C-06",
        "butir pengetahuan tidak tayang tanpa persetujuan kurator",
        fitur_pengunci="010 pipeline pengetahuan dan gerbang kurasi",
    ),
    Pasal(
        "C-07",
        "sistem tidak menjawab berdasarkan regulasi dicabut",
        fitur_pengunci="010 pipeline pengetahuan dan gerbang kurasi",
    ),
    Pasal(
        "C-08",
        "seluruh pemanggilan model lewat src/llm/",
        pemeriksa=periksa_impor_penyedia,
    ),
    Pasal(
        "C-09",
        "setiap keluaran eksperimen mencatat lima bidang versi ke logbook/",
        pemeriksa=_c09,
    ),
    Pasal(
        "C-10",
        "rentang anotasi memakai indeks karakter, bukan token",
        fitur_pengunci="003 perangkat anotasi",
    ),
    Pasal(
        "C-11",
        "cakupan uji pada modul inti tidak turun",
        pemeriksa=periksa_cakupan,
    ),
    Pasal(
        "C-12",
        "tidak ada ketergantungan baru tanpa persetujuan",
        pemeriksa=periksa_ketergantungan,
    ),
    Pasal(
        "C-13",
        "bahasa antarmuka: kalimat <= 20 kata, tanpa singkatan tak diuraikan",
        fitur_pengunci="013 penyempurnaan antarmuka",
    ),
    Pasal(
        "C-14",
        "fitur D-01 Bagian 4.2 tidak dibangun, termasuk kerangka kosong",
        fitur_pengunci="010 s.d. 013; sebagian dapat diperiksa lebih awal",
    ),
    Pasal(
        "C-15",
        "tanpa tabel poin, lencana, papan peringkat, pertemanan",
        pemeriksa=periksa_nama_terlarang,
    ),
    Pasal(
        "C-16",
        "ambang tidak disetel di luar prosedur kalibrasi BT-29",
        fitur_pengunci="007 pengambilan hibrida dan kalibrasi ambang",
    ),
    Pasal(
        "C-17",
        "sistem tanpa kemampuan bertindak",
        pemeriksa=periksa_tanpa_kemampuan_bertindak,
    ),
    Pasal(
        "C-18",
        "konten terambil tidak pernah pada posisi instruksi",
        # Diperiksa dari dua sisi sejak D-5: bentuk kode (konstruksi Instruksi
        # terkunci satu modul) dan perilaku sebenarnya (penanda dijalankan
        # melalui pembangun muatan, ambang nol). Sisi kedua diperlukan karena
        # C-18 dapat dilanggar tanpa mengubah satu pun bentuk yang terbaca AST.
        pemeriksa=periksa_pemisahan_instruksi,
    ),
    Pasal(
        "C-19",
        "klaim tidak bersandar tunggal pada segmen T3 atau T4",
        fitur_pengunci="008 validator sitasi",
    ),
    Pasal(
        "C-20",
        "bentuk tanggapan dan daftar rute mengikuti D-14",
        fitur_pengunci="009 penyusunan jawaban dan rute /api/v1/tanya",
    ),
)
