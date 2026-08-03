"""Pemeriksa V-03, V-05, dan V-06 — R-14, `docs/D12.md` Bagian 5.

V-01, V-02, dan V-04 memakai pemeriksa yang sudah ada pada tugas sebelumnya.
Tiga sisanya berada di sini.

**V-03 ketertelusuran dan keselarasan dokumen.** Setiap modul wajib menyebut
kode kebutuhan yang diwujudkannya. Ini penerapan butir "setiap berkas berubah
dapat ditelusuri ke kode kebutuhan" pada daftar Selesai `AGENTS.md`, digeser
dari pemeriksaan mata menjadi pemeriksaan mesin.

**V-05 pemindaian keamanan statis.** Dikerjakan dengan `ast` pustaka baku, dan
sengaja sempit: hanya pola yang tidak punya alasan sah muncul pada sistem ini.
Pemindai luas akan menghasilkan kebisingan, dan pemeriksa yang berisik akan
dimatikan.

**V-06 rahasia, kunci, dan data pribadi.** NFR-07 dan FR-B04 melarang data
pribadi menyentuh korpus; ia sama sekali tidak punya urusan berada di dalam
kode.

Batas yang diakui terbuka: seluruhnya membaca bentuk kode dan untai harfiah.
Rahasia yang disusun saat jalan tidak terbaca. Sama seperti RP-01, ia tidak
diklaim tertutup.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

DIPERIKSA = ("src", "perkakas")

POLA_KEBUTUHAN = re.compile(
    r"\b(?:R|FR|NFR|MK|KL|RE|VS|KD|AN|UK|G\d)-[A-Z]?\d+|\bC-\d{2}\b|\bADR-\d+\b"
)

# V-05 — pemanggilan bawaan yang tidak punya alasan sah pada sistem ini.
BAWAAN_TERLARANG = {
    "eval": "menjalankan untai sebagai kode",
    "exec": "menjalankan untai sebagai kode",
    "compile": "menyusun kode saat jalan",
}

# Dicocokkan pada **jalur bertitik penuh**, bukan pada nama atributnya saja.
# Mencocokkan nama atribut menghasilkan kebisingan yang membatalkan gunanya:
# `re.compile` dan `json.loads` sah dan lazim, sedangkan `pickle.loads` dan
# `os.system` tidak. Pemeriksa versi pertama menyalak pada keduanya, dan
# `make check` sendiri yang menangkapnya.
BERTITIK_TERLARANG = {
    "pickle.loads": "memuat objek Python sembarang dari untai byte",
    "dill.loads": "memuat objek Python sembarang dari untai byte",
    "marshal.loads": "memuat objek Python sembarang dari untai byte",
    "os.system": "menjalankan perintah cangkang",
    "os.popen": "menjalankan perintah cangkang",
    "yaml.load": "pemuatan YAML tanpa pembatasan tipe",
    "yaml.unsafe_load": "pemuatan YAML tanpa pembatasan tipe",
}

# V-06 — pola rahasia dan data pribadi pada untai harfiah.
POLA_RAHASIA = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "kunci privat"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"), "kunci penyedia model"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}"), "token GitHub"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "kunci akses AWS"),
    (re.compile(r"(?<!\d)\d{16}(?!\d)"), "deret enam belas digit menyerupai NIK"),
    (re.compile(r"(?<!\d)\d{18}(?!\d)"), "deret delapan belas digit menyerupai NIP"),
)

NAMA_SANDI = re.compile(r"^(password|sandi|kata_sandi|secret|token|api_key)$", re.IGNORECASE)


def _jalur_panggilan(simpul: ast.Call) -> str:
    """Jalur bertitik selengkap yang terbaca: `re.compile`, `pickle.loads`, `eval`."""
    fungsi = simpul.func
    bagian: list[str] = []
    while isinstance(fungsi, ast.Attribute):
        bagian.append(fungsi.attr)
        fungsi = fungsi.value
    if isinstance(fungsi, ast.Name):
        bagian.append(fungsi.id)
    else:
        return ""
    return ".".join(reversed(bagian))


def _cabang(akar: Path) -> list[Path]:
    return [akar / d for d in DIPERIKSA if (akar / d).is_dir()]


def periksa_ketertelusuran(akar: Path) -> list[Temuan]:
    """V-03 — setiap modul menyebut kode kebutuhan yang diwujudkannya."""
    temuan: list[Temuan] = []
    for cabang in _cabang(akar):
        for berkas in berkas_python(cabang):
            isi = berkas.read_text(encoding="utf-8")
            if berkas.name == "__init__.py" and not isi.strip():
                continue
            pohon = ast.parse(isi, filename=str(berkas))
            uraian = ast.get_docstring(pohon)
            if not uraian:
                temuan.append(
                    Temuan(
                        berkas,
                        1,
                        "modul tanpa uraian — V-03 mensyaratkan setiap berkas "
                        "dapat ditelusuri ke kode kebutuhan",
                    )
                )
            elif not POLA_KEBUTUHAN.search(uraian):
                temuan.append(
                    Temuan(
                        berkas,
                        1,
                        "uraian modul tidak menyebut satu pun kode kebutuhan "
                        "(R-xx, FR-xx, NFR-xx, C-xx, ADR-xx)",
                    )
                )
    return temuan


def periksa_keamanan_statis(akar: Path) -> list[Temuan]:
    """V-05 — pola yang tidak punya alasan sah pada sistem ini."""
    temuan: list[Temuan] = []
    for cabang in _cabang(akar):
        for berkas in berkas_python(cabang):
            pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
            for simpul in ast.walk(pohon):
                if not isinstance(simpul, ast.Call):
                    continue
                jalur = _jalur_panggilan(simpul)
                sebab = BERTITIK_TERLARANG.get(jalur) or (
                    BAWAAN_TERLARANG.get(jalur) if "." not in jalur else None
                )
                if sebab:
                    temuan.append(Temuan(berkas, simpul.lineno, f"{jalur}(): {sebab}"))
                for kata in simpul.keywords:
                    if (
                        kata.arg == "shell"
                        and isinstance(kata.value, ast.Constant)
                        and kata.value.value is True
                    ):
                        temuan.append(
                            Temuan(
                                berkas,
                                simpul.lineno,
                                "shell=True membuka penyuntikan perintah cangkang",
                            )
                        )
    return temuan


def periksa_rahasia(akar: Path) -> list[Temuan]:
    """V-06 — rahasia, kunci, dan data pribadi pada untai harfiah."""
    temuan: list[Temuan] = []
    for cabang in _cabang(akar):
        for berkas in berkas_python(cabang):
            pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
            for simpul in ast.walk(pohon):
                if isinstance(simpul, ast.Constant) and isinstance(simpul.value, str):
                    for pola, sebutan in POLA_RAHASIA:
                        if pola.search(simpul.value):
                            temuan.append(Temuan(berkas, simpul.lineno, sebutan))
                            break
                elif isinstance(simpul, ast.Assign):
                    for sasaran in simpul.targets:
                        if (
                            isinstance(sasaran, ast.Name)
                            and NAMA_SANDI.match(sasaran.id)
                            and isinstance(simpul.value, ast.Constant)
                            and isinstance(simpul.value.value, str)
                            and simpul.value.value
                        ):
                            temuan.append(
                                Temuan(
                                    berkas,
                                    simpul.lineno,
                                    f"{sasaran.id} diberi nilai harfiah di dalam kode",
                                )
                            )
    return temuan
