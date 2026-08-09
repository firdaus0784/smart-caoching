"""Bahan uji PDF — ditulis tangan agar isinya persis diketahui.

Empat berkas untuk empat keadaan pada spec.md. PDF berlapis teks disusun
sebagai sintaks PDF mentah, bukan dibangkitkan pustaka: bahan uji yang
dibangkitkan pustaka yang sama dengan yang diuji berarti menguji pustaka
terhadap dirinya sendiri.
"""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

BAHAN = Path("tests/bahan")
BARIS = [
    "Notulen Rapat Pleno Semester Ganjil",
    "SDN Sukamaju, Kecamatan Sumedang Selatan",
    "Kepala sekolah menugaskan wakil kurikulum menyusun jadwal supervisi.",
]


def _pdf(isi_aliran: bytes, dengan_font: bool) -> bytes:
    objek: list[bytes] = []
    objek.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objek.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    sumber = b"<< /Font << /F1 5 0 R >> >>" if dengan_font else b"<< >>"
    objek.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources "
        + sumber
        + b" /Contents 4 0 R >>"
    )
    objek.append(
        b"<< /Length "
        + str(len(isi_aliran)).encode()
        + b" >>\nstream\n"
        + isi_aliran
        + b"\nendstream"
    )
    if dengan_font:
        objek.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    keluaran = bytearray(b"%PDF-1.4\n")
    tempat: list[int] = []
    for i, isi in enumerate(objek, start=1):
        tempat.append(len(keluaran))
        keluaran += str(i).encode() + b" 0 obj\n" + isi + b"\nendobj\n"
    awal_xref = len(keluaran)
    keluaran += b"xref\n0 " + str(len(objek) + 1).encode() + b"\n0000000000 65535 f \n"
    for t in tempat:
        keluaran += f"{t:010d} 00000 n \n".encode()
    keluaran += (
        b"trailer\n<< /Size "
        + str(len(objek) + 1).encode()
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(awal_xref).encode()
        + b"\n%%EOF\n"
    )
    return bytes(keluaran)


teks = b"BT /F1 12 Tf 50 780 Td 16 TL\n"
for baris in BARIS:
    teks += b"(" + baris.encode("latin-1") + b") Tj T*\n"
teks += b"ET\n"

(BAHAN / "berlapis-teks.pdf").write_bytes(_pdf(teks, dengan_font=True))
(BAHAN / "pindaian-tanpa-teks.pdf").write_bytes(
    _pdf(b"0.9 0.9 0.9 rg 50 700 495 100 re f\n", dengan_font=False)
)

penulis = PdfWriter()
penulis.append(PdfReader(BAHAN / "berlapis-teks.pdf"))
penulis.encrypt("rahasia-uji")
with (BAHAN / "terkunci.pdf").open("wb") as berkas:
    penulis.write(berkas)

utuh = (BAHAN / "berlapis-teks.pdf").read_bytes()
(BAHAN / "rusak.pdf").write_bytes(utuh[: len(utuh) // 2])
(BAHAN / "kosong.pdf").write_bytes(b"")

for nama in sorted(p.name for p in BAHAN.iterdir()):
    print(nama, (BAHAN / nama).stat().st_size)
