"""Penulis logbook tambah-saja — R-11, R-13, C-09, `docs/D10.md`.

`docs/D10.md` Bagian 1 menyatakan aturan pokoknya dalam satu kalimat: dicatat
saat terjadi, bukan saat dibutuhkan. Modul ini adalah jalur satu-satunya bagi
kode untuk menulis ke `logbook/`.

**Permukaan modul tidak menyediakan cara mengubah atau menghapus baris.**
Larangan pada `AGENTS.md` bagian Batas bersifat prosedural bagi manusia; bagi
kode ia ditegakkan dengan cara yang lebih tegas — yang tidak disediakan tidak
dapat dipanggil karena lupa. Koreksi atas catatan yang keliru ditulis sebagai
baris baru, bukan menimpa baris lama, sehingga selisih antara apa yang dicatat
mula-mula dan apa yang diketahui kemudian tetap terbaca.

Bentuk JSONL dipilih untuk L1 dan L2 karena keduanya ditulis kode dan dibaca
mesin saat menyusun bagian metode naskah. L4 s.d. L7 ditulis manusia dan
berbentuk Markdown; keduanya tidak melewati modul ini.

Batas yang diakui terbuka (RP-05): sifat tambah-saja ditegakkan pada
permukaan modul dan pada pemeriksa AST R-13, tetapi tidak terhadap
penyuntingan berkas langsung maupun penulisan ulang riwayat git. Kendali
terhadap keduanya bersifat prosedural dan tertulis pada `AGENTS.md`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Final

BENTUK_WAKTU: Final = "dicatat_pada"


class Buku(Enum):
    """Berkas logbook yang ditulis kode. L4 s.d. L7 ditulis manusia."""

    L1 = "L1-percobaan.jsonl"
    L2 = "L2-versi-artefak.jsonl"


def tambah_baris(akar_logbook: Path, buku: Buku, catatan: dict[str, object]) -> None:
    """Tambahkan satu catatan. Tidak ada operasi lain yang disediakan.

    Stempel waktu UTC ditambahkan otomatis, sesuai KM-01 pada `docs/D14.md`.
    """
    if not catatan:
        raise ValueError(
            "catatan kosong tidak membawa informasi — rekaman penelitian tidak menerima baris hampa"
        )

    akar_logbook.mkdir(parents=True, exist_ok=True)
    berkas = akar_logbook / buku.value

    lengkap = {**catatan, BENTUK_WAKTU: datetime.now(UTC).isoformat()}
    baris = json.dumps(lengkap, ensure_ascii=False, sort_keys=True)

    # Mode "a" saja. Tidak ada cabang yang membuka berkas dengan mode menimpa.
    with berkas.open("a", encoding="utf-8") as arsip:
        arsip.write(baris + "\n")
