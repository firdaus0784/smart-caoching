"""Kendali peran — R-01 s.d. R-04, `docs/D14.md` Bagian 3, AG-02.

`AGENTS.md` menempatkan kendali peran di `src/api/`: *"FastAPI, satu-satunya
titik masuk, kendali peran di sini."* Modul ini adalah "di sini", dan ia
sengaja berdiri **tanpa kerangka web** — lihat `specs/021-rute-tanya/plan.md`
Bagian 2.

## Mengapa `Peran` tidak tinggal di `src/kamus/`

`src/kamus/` adalah rumah enum `docs/D14.md` **Bagian 5** — kamus data.
`Peran` berasal dari **Bagian 3** — peta rute. Menempatkannya di sana
melebarkan piagam modul itu diam-diam dari "kamus data" menjadi "enum apa pun
milik D-14", dan pelebaran yang tidak diputuskan tidak punya batas berikutnya.
Keputusan Gerbang 1, KB-052.

## Tabelnya ditulis penuh, termasuk rute yang belum dibangun

Seluruh rute D-14 Bagian 3 ada di sini, juga yang fiturnya belum ada. Tabel
yang diisi separuh adalah tabel yang lubangnya tidak terlihat — dan lubang pada
tabel peran berarti rute yang, pada hari ia dibangun, **terbuka bagi siapa
saja** karena tidak ada baris yang menolaknya.

Ujinya membaca D-14 sungguhan dan membandingkan dua arah: rute dokumen yang
tidak ada di sini, dan rute di sini yang tidak ada pada dokumen. Yang kedua
menegakkan AG-02 — larangan menambah rute yang tidak ada pada D-14 Bagian 3.

## Yang dicocokkan adalah **pola jalur**, bukan jalur permintaan

`/api/v1/butir/{id}` disimpan apa adanya. `boleh()` tidak mencocokkan
`/api/v1/butir/BTR-001` terhadapnya, dan itu disengaja: mencocokkan jalur
permintaan menuntut penerjemah pola tersendiri, dan penerjemah kedua yang
berselisih dengan penerjemah kerangka web adalah keadaan yang lebih buruk
daripada tidak punya. Adaptor HTTP mengetahui pola rutenya sendiri dan
menyerahkannya ke sini.

## Rute tak dikenal ditolak, bukan diloloskan

Salah ketik pada penangan yang diloloskan menjadi pintu terbuka yang tidak
tercatat di mana pun. Ditolak, ia menjadi galat yang terlihat pada uji pertama.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Peran(Enum):
    """Keenam peran `docs/D14.md` Bagian 3.

    `VERIFIKATOR` ditambahkan pada Gerbang 2 fitur 002 (KB-011): FR-B05
    mewajibkan verifikasi anonimisasi oleh manusia dan ADR-06 menuntut area
    karantina dijaga kredensial terpisah, sehingga ia satu-satunya peran yang
    kredensialnya menjangkau karantina.
    """

    PENGGUNA = "pengguna"
    KURATOR = "kurator"
    ANOTATOR = "anotator"
    PENELITI = "peneliti"
    VERIFIKATOR = "verifikator"
    ADMIN = "admin"


PENJAGA_PUBLIK = "publik"
"""Rute yang dipanggil sebelum pengguna memiliki peran.

Menuntut peran pada rute masuk mengunci pintu dari dalam.
"""

PENJAGA_SEMUA = "semua"
"""Terbuka bagi keenam peran. Peran yang tidak dapat keluar adalah sesi yang
hanya dapat berakhir dengan kedaluwarsa."""

_PENJAGA_TERBUKA = frozenset({PENJAGA_PUBLIK, PENJAGA_SEMUA})


class Rute(BaseModel):
    """Satu baris peta rute D-14 Bagian 3.

    Beku: tabel peran yang dapat diubah saat jalan adalah tabel yang dapat
    dilonggarkan oleh kode mana pun yang kebetulan mengimpornya.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metode: str = Field(min_length=3)
    jalur: str = Field(min_length=1)
    penjaga_tertulis: str = Field(min_length=1)
    """Kolom peran D-14 apa adanya — nama peran, `publik`, atau `semua`.

    Sengaja tanpa nilai bawaan. Penjaga berbawaan membuat rute yang lupa diberi
    peran terbentuk sebagai rute yang sudah berpenjaga, dan tidak satu uji
    perilaku pun gagal karenanya — penjaganya memang ada, hanya saja tidak
    seorang pun memilihnya. Bentuk yang sama dengan aturan 2 pemeriksa C-06.
    """
    kebutuhan: str = ""
    """Kode kebutuhan yang menuntut rute ini, dari kolom terakhir D-14."""


PETA_RUTE: tuple[Rute, ...] = (
    # --- D-14 Bagian 3.1 · Akun dan Profil
    Rute(metode="POST", jalur="/api/v1/auth/masuk", penjaga_tertulis="publik", kebutuhan="FR-A01"),
    Rute(metode="POST", jalur="/api/v1/auth/keluar", penjaga_tertulis="semua"),
    Rute(
        metode="GET", jalur="/api/v1/saya/profil", penjaga_tertulis="pengguna", kebutuhan="FR-A02"
    ),
    Rute(
        metode="PUT",
        jalur="/api/v1/saya/profil",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-A02, FR-A06",
    ),
    Rute(
        metode="PUT",
        jalur="/api/v1/saya/prioritas",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-A03",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/saya/persetujuan",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-A05",
    ),
    Rute(
        metode="DELETE", jalur="/api/v1/saya/data", penjaga_tertulis="pengguna", kebutuhan="NFR-09"
    ),
    # --- D-14 Bagian 3.2 · Tanya Jawab
    Rute(
        metode="POST",
        jalur="/api/v1/tanya",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-F01 s.d. FR-F17",
    ),
    Rute(metode="GET", jalur="/api/v1/percakapan", penjaga_tertulis="pengguna", kebutuhan="FR-F09"),
    Rute(
        metode="GET",
        jalur="/api/v1/percakapan/{id}",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-F09",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/pesan/{id}/penilaian",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-F07",
    ),
    Rute(
        metode="GET", jalur="/api/v1/sumber/{id}", penjaga_tertulis="pengguna", kebutuhan="FR-F11"
    ),
    # --- D-14 Bagian 3.3 · Penemuan dan Penerapan
    Rute(
        metode="GET",
        jalur="/api/v1/beranda",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-G01, FR-G05",
    ),
    Rute(metode="GET", jalur="/api/v1/butir/{id}", penjaga_tertulis="pengguna", kebutuhan="FR-G02"),
    Rute(
        metode="POST",
        jalur="/api/v1/butir/{id}/simpan",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-G06",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/butir/{id}/tolak",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-G07",
    ),
    Rute(
        metode="GET",
        jalur="/api/v1/butir/{id}/pemeriksaan",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-H01",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/pemeriksaan/{id}/jawab",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-H02",
    ),
    Rute(metode="POST", jalur="/api/v1/komitmen", penjaga_tertulis="pengguna", kebutuhan="FR-H03"),
    Rute(metode="GET", jalur="/api/v1/komitmen", penjaga_tertulis="pengguna", kebutuhan="FR-H04"),
    Rute(
        metode="PATCH",
        jalur="/api/v1/komitmen/{id}",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-H04",
    ),
    Rute(metode="GET", jalur="/api/v1/jurnal", penjaga_tertulis="pengguna", kebutuhan="FR-H06"),
    Rute(
        metode="POST",
        jalur="/api/v1/jurnal/ekspor",
        penjaga_tertulis="pengguna",
        kebutuhan="FR-H07",
    ),
    # --- D-14 Bagian 3.4 · Kurasi dan Penelitian
    Rute(
        metode="GET",
        jalur="/api/v1/kurasi/antrean",
        penjaga_tertulis="kurator",
        kebutuhan="FR-I01",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/kurasi/{id}/putusan",
        penjaga_tertulis="kurator",
        kebutuhan="FR-I02",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/kurasi/{id}/tarik",
        penjaga_tertulis="kurator",
        kebutuhan="FR-I06",
    ),
    Rute(
        metode="GET", jalur="/api/v1/kurasi/aduan", penjaga_tertulis="kurator", kebutuhan="FR-I04"
    ),
    Rute(
        metode="GET",
        jalur="/api/v1/analitik/ringkas",
        penjaga_tertulis="peneliti",
        kebutuhan="FR-J04",
    ),
    Rute(
        metode="POST",
        jalur="/api/v1/analitik/ekspor",
        penjaga_tertulis="peneliti",
        kebutuhan="FR-J03",
    ),
)
"""Seluruh rute D-14 Bagian 3 — lihat uraian modul mengapa penuh, bukan
sebagian."""

_INDEKS: dict[tuple[str, str], Rute] = {(r.metode, r.jalur): r for r in PETA_RUTE}


def boleh(peran: Peran, metode: str, pola_jalur: str) -> bool:
    """Bolehkah `peran` memanggil rute ini? — R-02.

    `pola_jalur` adalah **pola** D-14, bukan jalur permintaan; lihat uraian
    modul. Rute yang tidak dikenal ditolak.
    """
    rute = _INDEKS.get((metode, pola_jalur))
    if rute is None:
        return False
    if rute.penjaga_tertulis in _PENJAGA_TERBUKA:
        return True
    return peran.value == rute.penjaga_tertulis
