-- T-9 fitur 024 · Peran dan basis data — jalankan sebagai superuser pada `postgres`
--
-- Mewujudkan Keputusan Gerbang 1 nomor 1 dan nomor 2:
--   satu peladen, DUA basis data, dan pemisahan lewat skema SEKALIGUS pengguna.
--
-- Empat peran, mencerminkan `src/penyimpanan/kredensial_baku.py` satu lawan satu.
-- Bila berkas itu berubah, berkas ini wajib ikut berubah — dua daftar yang
-- bercerita berbeda adalah cacat, dan yang salah justru daftar yang dibaca orang.

-- Dapat dijalankan berulang. Penyiapan yang hanya boleh dijalankan sekali
-- adalah penyiapan yang gagal pada percobaan kedua, dan percobaan kedua selalu
-- terjadi — saat memulihkan, saat menambah lingkungan, saat menjalankan uji.
--
-- `CREATE DATABASE` tidak mengenal IF NOT EXISTS, sehingga dipanggil lewat
-- \gexec yang menghasilkan perintahnya hanya bila basis datanya belum ada.

SELECT 'CREATE DATABASE smart_coaching'
 WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smart_coaching')
\gexec

SELECT 'CREATE DATABASE smart_coaching_pseudonim'
 WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smart_coaching_pseudonim')
\gexec

DO $$
DECLARE nama text;
BEGIN
  FOREACH nama IN ARRAY ARRAY['peran_penjawaban','peran_verifikasi',
                              'peran_pemanggil_llm','peran_pseudonim'] LOOP
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = nama) THEN
      EXECUTE format('CREATE ROLE %I LOGIN', nama);
    END IF;
  END LOOP;
END $$;

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
