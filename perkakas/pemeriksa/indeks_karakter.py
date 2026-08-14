"""Pemeriksa indeks rentang anotasi — C-10, D-03 Bagian 15.

C-10 berbunyi: *"Rentang anotasi memakai indeks karakter, bukan indeks
token."* D-03 Bagian 15 menyebut alasannya: **menghindari ketergantungan pada
pilihan tokenizer**. Korpus berindeks token berhenti berarti begitu
tokenizernya diganti, dan penggantian tokenizer adalah hal yang wajar terjadi.

## Mengapa pasal ini sulit dilanggar dengan mencolok

Indeks token dan indeks karakter sama-sama bilangan bulat. Rentang yang keliru
tidak menghasilkan galat apa pun — ia menunjuk kata lain, dan berkas
korpusnya tetap terbaca sempurna. Yang membedakan hanya apakah potongan
teksnya cocok.

Ketiga aturan di bawah karena itu tidak mengejar "apakah angkanya indeks
karakter" — pertanyaan yang tidak dapat dijawab AST. Ia menutup **tiga tempat
angka itu dapat berpindah makna tanpa terlihat**.

## Tiga aturan

1. **`RentangEntitas` membawa teks kanoniknya dan memeriksa potongannya.**
   Inilah yang membuat indeks token tidak dapat menyamar: indeks token yang
   dipakai sebagai indeks karakter akan memotong teks pada tempat yang salah,
   dan pemeriksaan potongan menangkapnya saat pembentukan. Menghapus
   `teks_kanonik` menghapus satu-satunya saksi.

2. **Ekspor CoNLL melaporkan rentang yang tidak sejajar token, dan melewati
   dokumennya.** Di sinilah kedua sistem indeks bertemu. Menggeser rentang ke
   batas token terdekat menghasilkan berkas pelatihan yang benar bentuknya dan
   salah isinya — dan model yang dilatih atasnya belajar batas entitas yang
   tidak pernah ditandai siapa pun. Melaporkan **sambil tetap menuliskannya**
   sama saja: laporan yang tidak mengubah apa pun.

3. **Hanya modul ekspor yang boleh melihat tokenisasi.** Pembentukan dan
   pembacaan anotasi tidak boleh mengenal token sama sekali; yang tidak
   mengenal token tidak dapat memakai indeksnya. Ekspor dikecualikan karena
   CoNLL memang berbaris per token — dan aturan 2 yang menjaga perkecualian
   itu tidak menjadi pintu.

Ketiganya bertingkat: aturan 1 menjaga bentuk yang menyimpan rentang, aturan 3
menjaga tempat indeks token dapat masuk, dan aturan 2 menjaga satu-satunya
tempat keduanya sah bertemu.

## Batas yang diakui terbuka

Ini pembacaan bentuk kode. Rentang yang dihitung keliru dari sumber lain —
misalnya berkas impor yang memang memuat indeks token — lolos pemeriksa ini
dan tertahan pemeriksaan potongan pada aturan 1 saat dibentuk. Keduanya
diperlukan; tidak satu pun cukup sendiri.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

DIREKTORI_ANOTASI = Path("src") / "nlp" / "anotasi"
BERKAS_RENTANG = DIREKTORI_ANOTASI / "rentang.py"
BERKAS_EKSPOR = DIREKTORI_ANOTASI / "ekspor.py"

NAMA_RENTANG = "RentangEntitas"
BIDANG_SAKSI = "teks_kanonik"
BIDANG_LAPORAN = "tak_sejajar_token"
PENGGAL_TOKENISASI = "praproses"


def periksa_indeks_karakter(akar: Path) -> list[Temuan]:
    """Ketiga aturan C-10 — lihat uraian modul."""
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_rentang_membawa_saksinya(akar))
    temuan.extend(_aturan_2_ekspor_melaporkan_dan_melewati(akar))
    temuan.extend(_aturan_3_hanya_ekspor_melihat_token(akar))
    return temuan


def _aturan_1_rentang_membawa_saksinya(akar: Path) -> list[Temuan]:
    """`RentangEntitas` membawa teks kanoniknya dan memeriksa potongannya."""
    berkas = akar / BERKAS_RENTANG
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul rentang anotasi tidak ditemukan — menghapus bentuk yang dijaga "
                "bukan cara sah meloloskan pemeriksa ini (C-10)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    kelas = _kelas_bernama(pohon, NAMA_RENTANG)
    if kelas is None:
        return [
            Temuan(
                berkas,
                0,
                f"{NAMA_RENTANG} tidak ditemukan — tipe yang hilang bukan tipe yang aman (C-10)",
            )
        ]

    bidang = {
        simpul.target.id
        for simpul in kelas.body
        if isinstance(simpul, ast.AnnAssign) and isinstance(simpul.target, ast.Name)
    }
    if BIDANG_SAKSI not in bidang:
        return [
            Temuan(
                berkas,
                kelas.lineno,
                f"{NAMA_RENTANG} tidak membawa {BIDANG_SAKSI} — tanpa teks kanoniknya, "
                "indeks token yang dipakai sebagai indeks karakter memotong tempat "
                "yang salah tanpa satu galat pun (C-10, D-03 Bagian 15)",
            )
        ]

    if not _memotong_teks_kanonik(kelas):
        return [
            Temuan(
                berkas,
                kelas.lineno,
                f"{NAMA_RENTANG} membawa {BIDANG_SAKSI} tetapi tidak memotongnya — "
                "saksi yang tidak pernah ditanya sama saja dengan tidak ada (C-10)",
            )
        ]
    return []


def _memotong_teks_kanonik(kelas: ast.ClassDef) -> bool:
    """Adakah `self.teks_kanonik[...]` di dalam tubuh kelas?"""
    for simpul in ast.walk(kelas):
        if not isinstance(simpul, ast.Subscript):
            continue
        sasaran = simpul.value
        if isinstance(sasaran, ast.Attribute) and sasaran.attr == BIDANG_SAKSI:
            return True
    return False


def _aturan_2_ekspor_melaporkan_dan_melewati(akar: Path) -> list[Temuan]:
    """Ekspor CoNLL melaporkan rentang tak sejajar **dan** melewati dokumennya."""
    berkas = akar / BERKAS_EKSPOR
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul ekspor anotasi tidak ditemukan — di sanalah kedua sistem "
                "indeks bertemu (C-10)",
            )
        ]

    isi = berkas.read_text(encoding="utf-8")
    pohon = ast.parse(isi)

    if BIDANG_LAPORAN not in _bidang_seluruh_kelas(pohon):
        return [
            Temuan(
                berkas,
                0,
                f"hasil ekspor tidak membawa {BIDANG_LAPORAN} — rentang yang tidak "
                "jatuh pada batas token wajib dilaporkan, bukan digeser diam-diam "
                "(C-10, D-03 Bagian 15)",
            )
        ]

    if not _melewati_dokumen_meleset(pohon):
        return [
            Temuan(
                berkas,
                0,
                "dokumen berentang tak sejajar tidak dilewati — melaporkannya sambil "
                "tetap menuliskannya adalah laporan yang tidak mengubah apa pun "
                "(C-10)",
            )
        ]
    return []


def _bidang_seluruh_kelas(pohon: ast.Module) -> set[str]:
    return {
        simpul.target.id
        for simpul in ast.walk(pohon)
        if isinstance(simpul, ast.AnnAssign) and isinstance(simpul.target, ast.Name)
    }


def _melewati_dokumen_meleset(pohon: ast.Module) -> bool:
    """Adakah `continue` pada cabang **yang sama** dengan pelaporannya?

    Bukan `continue` mana pun di dalam gelung mana pun. Rumusan longgar itu
    sempat dipakai dan **lolos pada pohon sungguhan** meski pelewatannya
    dihapus — sebab modul ekspor memuat gelung lain yang kebetulan juga
    memakai `continue`. Uji mutasi yang menemukannya, bukan mata.

    Yang dicari sekarang: nama daftar yang diteruskan ke `tak_sejajar_token`,
    lalu cabang `if` yang menambahkan ke daftar itu. Cabang itulah yang wajib
    memuat `continue` — sebab di sanalah, dan hanya di sana, dokumennya
    diputuskan ikut tertulis atau tidak.
    """
    pelapor = _nama_daftar_pelaporan(pohon)
    if pelapor is None:
        return False

    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.If):
            continue
        if not _menambahkan_ke(simpul, pelapor):
            continue
        if any(isinstance(anak, ast.Continue) for anak in ast.walk(simpul)):
            return True
    return False


def _nama_daftar_pelaporan(pohon: ast.Module) -> str | None:
    """Nama daftar yang diteruskan ke `tak_sejajar_token=`.

    Dibaca dari pemanggilannya, bukan ditebak dari nama peubah: peubah dapat
    dinamai apa saja, sedangkan kata kunci itu bagian bentuk hasilnya.
    """
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.keyword) or simpul.arg != BIDANG_LAPORAN:
            continue
        # `tuple(tak_sejajar)` memuat dua nama, dan yang pertama ditemui
        # `ast.walk` adalah `tuple` — nama fungsinya, bukan daftarnya. Posisi
        # pemanggil karena itu disingkirkan lebih dulu.
        nama_fungsi = {
            anak.func.id
            for anak in ast.walk(simpul.value)
            if isinstance(anak, ast.Call) and isinstance(anak.func, ast.Name)
        }
        for anak in ast.walk(simpul.value):
            if isinstance(anak, ast.Name) and anak.id not in nama_fungsi:
                return anak.id
    return None


def _menambahkan_ke(cabang: ast.If, nama: str) -> bool:
    """Adakah `<nama>.append(...)` di dalam cabang ini?"""
    for simpul in ast.walk(cabang):
        if not isinstance(simpul, ast.Call):
            continue
        fungsi = simpul.func
        if (
            isinstance(fungsi, ast.Attribute)
            and fungsi.attr == "append"
            and isinstance(fungsi.value, ast.Name)
            and fungsi.value.id == nama
        ):
            return True
    return False


def _aturan_3_hanya_ekspor_melihat_token(akar: Path) -> list[Temuan]:
    """Hanya modul ekspor yang boleh mengimpor praproses dari `src/nlp/anotasi/`."""
    diizinkan = (akar / BERKAS_EKSPOR).resolve()
    direktori = akar / DIREKTORI_ANOTASI
    if not direktori.is_dir():
        return []

    temuan: list[Temuan] = []
    for berkas in berkas_python(direktori):
        if berkas.resolve() == diizinkan:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if not isinstance(simpul, ast.ImportFrom):
                continue
            if simpul.module is None or PENGGAL_TOKENISASI not in simpul.module:
                continue
            temuan.append(
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"modul anotasi mengimpor {simpul.module} — pembentukan dan "
                    "pembacaan anotasi tidak boleh mengenal token sama sekali, sebab "
                    "yang tidak mengenal token tidak dapat memakai indeksnya. Hanya "
                    "ekspor CoNLL yang dikecualikan (C-10)",
                )
            )
    return temuan


def _kelas_bernama(pohon: ast.Module, nama: str) -> ast.ClassDef | None:
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ClassDef) and simpul.name == nama:
            return simpul
    return None
