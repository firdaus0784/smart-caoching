"""Penjalan uji kepatuhan U5 — fitur 042, R-01 s.d. R-07, D-08 Bagian 8, D-13 Bagian 8.

    python -m perkakas.kepatuhan jalankan --lingkungan <nama> --id-percobaan EXP-2026-nnn

Menjalankan UK-01 s.d. UK-15 terhadap satu lingkungan dan melaporkan
masing-masing sebagai lulus, gagal, atau belum dapat diperiksa. Aman diulang
di produksi (D-09 langkah 5): percobaan basis data berjalan di dalam transaksi
yang selalu dibatalkan, dan pemeriksaan API memakai sesi akun uji buatan
operator.
"""
