"""Penghasil `ekspor-label-studio-1.23.json` — bahan fitur 016.

Berkas ekspor pada folder ini **bukan hasil tebakan dari dokumentasi**. Ia
dihasilkan skrip ini terhadap Label Studio 1.23.0 yang benar-benar berjalan,
dengan dua akun anotator yang berbeda. Alasannya tercatat pada KB-021: dua
kali pada fitur 015 bentuk yang ditebak terbukti berbeda dari kenyataannya,
dan keduanya baru ketahuan ketika bahan uji sungguhan dibuat.

Skrip ini **tidak dijalankan oleh `make test`.** Ia tidak mengimpor apa pun
dari `src/`, tidak dijalankan pemeriksa mana pun, dan menuntut satu layanan
Label Studio yang tidak dipasang lingkungan pengembangan. Ia ada di sini agar
berkas ekspornya dapat dibuat ulang ketika versi Label Studio naik — bahan uji
yang tidak dapat dibuat ulang adalah bahan uji yang kelak dipercayai tanpa
seorang pun tahu asalnya.

Cara memakainya::

    LS_TOKEN_1=<token akun pertama> LS_TOKEN_2=<token akun kedua> \\
        python tests/bahan/buat_ekspor_label_studio.py

Kedua akun wajib berbeda. Bila keduanya sama, berkas hasilnya tetap terbentuk
tetapi `completed_by` bernilai sama pada seluruh anotasi — dan bahan uji
seperti itu tidak menguji pemisahan anotator sama sekali, justru hal yang
paling dituntut D-03 Bagian 11.

Bentuk isinya disengaja:

- **Tugas pertama dianotasi dua akun** dengan batas rentang yang sedikit
  berbeda dan kategori yang berbeda — bahan bagi F1 longgar dan Kappa.
- **Tugas kedua dianotasi satu akun saja** — bahan bagi keadaan "hanya satu
  anotator" pada `spec.md` fitur 003, yang wajib dilaporkan sebagai kurang
  bahan, bukan sebagai kesepakatan sempurna.

Tidak ada data pribadi. Kedua kalimatnya disusun sebagai contoh.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any

DASAR = os.environ.get("LS_DASAR", "http://localhost:8080/api")
KELUARAN = Path(__file__).resolve().parent / "ekspor-label-studio-1.23.json"

KONFIG = """<View>
  <Labels name="entitas" toName="teks">
    <Label value="REGULASI"/><Label value="PROGRAM"/><Label value="ANGGARAN"/>
    <Label value="JABATAN_PERAN"/><Label value="INDIKATOR_MUTU"/>
    <Label value="TENGGAT_WAKTU"/><Label value="INSTANSI"/><Label value="DOKUMEN"/>
  </Labels>
  <Text name="teks" value="$teks"/>
  <Choices name="kategori" toName="teks" choice="single">
    <Choice value="K1"/><Choice value="K2"/><Choice value="K3"/><Choice value="K4"/>
    <Choice value="K5"/><Choice value="K6"/><Choice value="K7"/><Choice value="K8"/>
  </Choices>
</View>"""

DOKUMEN = (
    "Kepala sekolah menyusun RKAS tahun anggaran 2026 bersama komite sekolah.",
    "Permendikdasmen Nomor 12 Tahun 2025 mengatur supervisi akademik di SD.",
)


def panggil(
    jalur: str, token: str, data: Any = None, mentah: bool = False
) -> Any:  # noqa: ANN401 — bentuk tanggapan Label Studio, bukan tipe kita
    permintaan = urllib.request.Request(
        f"{DASAR}{jalur}",
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(permintaan) as tanggapan:  # noqa: S310 — alamat lokal
        isi = tanggapan.read()
    if mentah:
        return isi
    return json.loads(isi) if isi else None


def anotasi(
    id_tugas: int,
    rentang: tuple[tuple[int, int, str, str], ...],
    kategori: str,
    token: str,
) -> Any:  # noqa: ANN401
    hasil: list[dict[str, Any]] = [
        {
            "from_name": "entitas",
            "to_name": "teks",
            "type": "labels",
            "value": {"start": mulai, "end": akhir, "text": teks, "labels": [label]},
        }
        for mulai, akhir, teks, label in rentang
    ]
    hasil.append(
        {
            "from_name": "kategori",
            "to_name": "teks",
            "type": "choices",
            "value": {"choices": [kategori]},
        }
    )
    return panggil(
        f"/tasks/{id_tugas}/annotations/", token, {"result": hasil, "was_cancelled": False}
    )


def main() -> int:
    token1 = os.environ.get("LS_TOKEN_1", "")
    token2 = os.environ.get("LS_TOKEN_2", "")
    if not token1 or not token2:
        print("LS_TOKEN_1 dan LS_TOKEN_2 wajib diisi — lihat uraian modul", file=sys.stderr)
        return 2
    if token1 == token2:
        print(
            "kedua token sama — berkas hasilnya tidak akan menguji pemisahan anotator",
            file=sys.stderr,
        )
        return 2

    proyek = panggil(
        "/projects/",
        token1,
        {
            "title": "Uji Skema D-03 dua anotator — bahan fitur 016",
            "label_config": KONFIG,
            "description": "Proyek contoh penghasil berkas ekspor. Bukan data sungguhan.",
        },
    )
    pid = proyek["id"]
    panggil(f"/projects/{pid}/import", token1, [{"teks": t} for t in DOKUMEN])
    daftar = panggil(f"/tasks/?project={pid}&page_size=100", token1)
    tugas = sorted(t["id"] for t in daftar["tasks"])

    anotasi(
        tugas[0],
        ((24, 28, "RKAS", "DOKUMEN"), (0, 14, "Kepala sekolah", "JABATAN_PERAN")),
        "K5",
        token1,
    )
    anotasi(
        tugas[1],
        ((0, 33, "Permendikdasmen Nomor 12 Tahun 2025", "REGULASI"),),
        "K1",
        token1,
    )
    anotasi(
        tugas[0],
        ((24, 34, "RKAS tahun", "DOKUMEN"), (0, 14, "Kepala sekolah", "JABATAN_PERAN")),
        "K8",
        token2,
    )

    mentah = panggil(f"/projects/{pid}/export?exportType=JSON", token1, mentah=True)
    muat = json.loads(mentah)
    KELUARAN.write_text(json.dumps(muat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    penganotasi = [a["completed_by"] for t in muat for a in t["annotations"]]
    print(f"{KELUARAN.name}: {len(muat)} tugas, completed_by={penganotasi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
