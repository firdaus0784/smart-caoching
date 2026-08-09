"""PDF yang terbuka tetapi isinya tidak dapat diurai — bahan uji B-5.

Berbeda dari `rusak.pdf` yang gagal saat dibuka. Yang ini punya kerangka sah
sehingga pembacanya berhasil dibentuk, dan baru gagal ketika teksnya diambil.
Aliran isinya menyatakan dirinya terkompresi Flate padahal isinya bukan.
"""

from pathlib import Path

from pypdf import PdfReader

BAHAN = Path("tests/bahan")
aliran = b"bukan-data-flate-sama-sekali"
objek = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << >> /Contents 4 0 R >>",
    b"<< /Length "
    + str(len(aliran)).encode()
    + b" /Filter /FlateDecode >>\nstream\n"
    + aliran
    + b"\nendstream",
]
keluaran = bytearray(b"%PDF-1.4\n")
tempat = []
for i, isi in enumerate(objek, start=1):
    tempat.append(len(keluaran))
    keluaran += str(i).encode() + b" 0 obj\n" + isi + b"\nendobj\n"
awal = len(keluaran)
keluaran += b"xref\n0 " + str(len(objek) + 1).encode() + b"\n0000000000 65535 f \n"
for t in tempat:
    keluaran += f"{t:010d} 00000 n \n".encode()
keluaran += (
    b"trailer\n<< /Size "
    + str(len(objek) + 1).encode()
    + b" /Root 1 0 R >>\nstartxref\n"
    + str(awal).encode()
    + b"\n%%EOF\n"
)
(BAHAN / "isi-rusak.pdf").write_bytes(bytes(keluaran))
print("isi-rusak.pdf", (BAHAN / "isi-rusak.pdf").stat().st_size, "bita")

pembaca = PdfReader(BAHAN / "isi-rusak.pdf")
print("terbuka, halaman:", len(pembaca.pages))
try:
    pembaca.pages[0].extract_text()
    print("extract_text: TIDAK melempar")
except Exception as e:
    print("extract_text ->", type(e).__name__)
