"""Pencatatan percobaan model ke logbook — R-10, R-11, C-09, D-10 Bagian 3.

D-10 Bagian 3 menutup daftar bidangnya dengan satu kalimat yang menentukan
seluruh modul ini: **pencatatan seed acak dan pembagian data bersifat wajib.**
Tanpa keduanya, angka yang dilaporkan tidak dapat diulang oleh siapa pun,
termasuk oleh tim sendiri tiga bulan kemudian.

## Seed dan pembagian diambil dari lemarinya, tidak diminta terpisah

Argumen terpisah dapat diisi angka yang bukan milik pembagian yang benar-benar
dipakai — dan **catatan yang menyebut seed yang salah lebih buruk daripada
catatan tanpa seed**, sebab ia menuntun orang mengulang dengan angka yang
keliru lalu menyimpulkan hasilnya tidak dapat direproduksi.

Karena itu `catat_percobaan` menerima `LemariUji`, bukan dua bilangan. Bentuk
yang sama dengan `catat_keluaran_ocr` fitur 015 yang menolak tipe selain
`TeksPindaian`.

## Hitungan pembukaan himpunan uji ikut

KB-028 pilihan C. Angka yang dilaporkan bersama "himpunan uji dibuka empat
kali" adalah angka yang pembacanya dapat nilai sendiri — dan alasan tiap
pembukaan ikut, sebab hitungan tanpa alasan tidak membedakan evaluasi akhir
dari mengintip.

## Percobaan yang gagal wajib tercatat

D-10 menuliskannya tegas. Alasannya bukan kerapian: rangkaian percobaan gagal
adalah bukti bahwa konfigurasi akhir dipilih berdasarkan pengujian, bukan
kebetulan. Catatan yang hanya memuat keberhasilan terbaca seperti penelitian
yang tidak pernah salah — dan tidak ada penelitian seperti itu.

Percobaan gagal **wajib menyebut dugaan penyebabnya**, sesuai ketentuan bidang
`catatan` pada D-10. Baris gagal tanpa dugaan tidak menghalangi siapa pun
mengulangi jalan buntu yang sama.

Ditulis ke **L1**, bukan L2: L1 mencatat percobaan model, L2 mencatat versi
artefak. Pembedaannya menentukan berkas mana yang dibaca saat menyusun bagian
metode naskah.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.logbook.penulis import Buku, tambah_baris
from src.nlp.pelatihan.lemari_uji import LemariUji
from src.nlp.pelatihan.metrik import HasilMetrik, Nilai

STATUS_SAH = ("berhasil", "gagal", "dibatalkan")
"""Ketiga status D-10 Bagian 3, dan hanya ketiganya.

Untai bebas di sini berarti "sukses", "OK", dan "berhasil" hidup berdampingan,
lalu jumlah percobaan berhasil dihitung atas salah satunya saja.
"""


def _nilai(n: Nilai) -> dict[str, object]:
    """Satu angka beserta keadaannya.

    `terhitung` selalu ada, pada kedua keadaan — penanda yang muncul hanya
    ketika ada masalah menuntut pembacanya menyimpulkan dari ketiadaan, dan
    ketiadaan pada berkas JSONL juga berarti versi penulis yang lebih tua.
    """
    return {"terhitung": n.terhitung, "nilai": n.nilai, "alasan": n.alasan}


def _hasil(metrik: HasilMetrik | None) -> dict[str, object]:
    """Bentuk bidang `hasil` D-10 — **per kelas dan kedua rerata**.

    FR-D04 dijaga sampai ke catatannya, bukan hanya sampai ke tipenya. Catatan
    yang hanya memuat rerata membuat kelas berperforma rendah hilang justru
    pada berkas yang dibaca berbulan kemudian.
    """
    if metrik is None:
        return {"terhitung": False, "alasan": "percobaan tidak menghasilkan metrik"}
    return {
        "terhitung": True,
        "jumlah_contoh": metrik.jumlah_contoh,
        "f1_makro": _nilai(metrik.f1_makro),
        "f1_mikro": _nilai(metrik.f1_mikro),
        "per_kelas": {
            nama: {
                "presisi": _nilai(m.presisi),
                "recall": _nilai(m.recall),
                "f1": _nilai(m.f1),
                "jumlah_acuan": m.jumlah_acuan,
                "jumlah_prediksi": m.jumlah_prediksi,
            }
            for nama, m in metrik.per_kelas.items()
        },
    }


def catat_percobaan(
    akar_logbook: Path,
    *,
    id_percobaan: str,
    tujuan: str,
    tugas: str,
    model_dasar: str,
    lemari: LemariUji,
    konfigurasi: dict[str, Any],
    perangkat_keras: str,
    durasi_detik: int,
    metrik: HasilMetrik | None,
    status: str,
    catatan: str,
    versi_kode: str,
) -> None:
    """Satu baris L1 bagi satu percobaan — R-10, R-11, C-09.

    Seluruh argumen bersifat kata kunci. Empat belas bidang yang sebagian
    besar berupa untai adalah tempat penukaran posisi tidak menghasilkan galat
    apa pun — hanya `tujuan` yang tercatat sebagai `tugas`, dan tidak ada yang
    menyadarinya sampai naskah ditulis.
    """
    if status not in STATUS_SAH:
        raise ValueError(
            f"status {status!r} di luar ketiga status D-10 Bagian 3 "
            f"({', '.join(STATUS_SAH)}) — untai bebas membuat jumlah percobaan "
            "berhasil dihitung atas salah satu ejaan saja"
        )
    if status == "gagal" and not catatan.strip():
        raise ValueError(
            "percobaan gagal wajib menyebut dugaan penyebabnya (D-10 Bagian 3 "
            "bidang `catatan`) — baris gagal tanpa dugaan tidak menghalangi "
            "siapa pun mengulangi jalan buntu yang sama"
        )

    tambah_baris(
        akar_logbook,
        Buku.L1,
        {
            "id_percobaan": id_percobaan,
            "tujuan": tujuan,
            "tugas": tugas,
            "model_dasar": model_dasar,
            "versi_korpus": lemari.pembagian.versi_korpus,
            "id_pembagian_data": lemari.pembagian.id_pembagian,
            "sidik_pembagian": lemari.pembagian.sidik,
            "seed": lemari.pembagian.seed,
            "konfigurasi": konfigurasi,
            "perangkat_keras": perangkat_keras,
            "durasi_detik": durasi_detik,
            "hasil": _hasil(metrik),
            "status": status,
            "catatan": catatan,
            "versi_kode": versi_kode,
            "pembukaan_himpunan_uji": lemari.jumlah_pembukaan,
            "alasan_pembukaan": [p.alasan for p in lemari.riwayat],
        },
    )
