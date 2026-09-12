-- T-9 fitur 024 · Peran dan basis data — jalankan sebagai superuser pada `postgres`
--
-- Mewujudkan Keputusan Gerbang 1 nomor 1 dan nomor 2:
--   satu peladen, DUA basis data, dan pemisahan lewat skema SEKALIGUS pengguna.
--
-- Empat peran, mencerminkan `src/penyimpanan/kredensial_baku.py` satu lawan satu.
-- Bila berkas itu berubah, berkas ini wajib ikut berubah — dua daftar yang
-- bercerita berbeda adalah cacat, dan yang salah justru daftar yang dibaca orang.

CREATE DATABASE smart_coaching;
CREATE DATABASE smart_coaching_pseudonim;

CREATE ROLE peran_penjawaban    LOGIN;
CREATE ROLE peran_verifikasi    LOGIN;
CREATE ROLE peran_pemanggil_llm LOGIN;
CREATE ROLE peran_pseudonim     LOGIN;

-- ─────────────────────────────────────────────────────────────────────────
-- BARIS YANG PALING MUDAH TERLUPA, DAN TANPANYA SELURUH BERKAS INI SIA-SIA
--
-- PostgreSQL memberi hak CONNECT kepada PUBLIC pada SETIAP basis data baru.
-- Tanpa REVOKE di bawah, `peran_penjawaban` dapat menyambung ke basis data
-- pseudonim dan C-05 runtuh — sementara daftar basis data, daftar peran,
-- daftar skema, dan hak tabel seluruhnya terbaca benar.
--
-- Diverifikasi pada peladen sungguhan, bukan disimpulkan dari dokumentasi
-- (KB-082).
-- ─────────────────────────────────────────────────────────────────────────

REVOKE CONNECT ON DATABASE smart_coaching            FROM PUBLIC;
REVOKE CONNECT ON DATABASE smart_coaching_pseudonim  FROM PUBLIC;

GRANT CONNECT ON DATABASE smart_coaching
  TO peran_penjawaban, peran_verifikasi, peran_pemanggil_llm;

GRANT CONNECT ON DATABASE smart_coaching_pseudonim
  TO peran_pseudonim;
