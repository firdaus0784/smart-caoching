-- T-9 fitur 024 · Peran dan basis data — jalankan sebagai superuser pada `postgres`
--
-- Mewujudkan Keputusan Gerbang 1 nomor 1 dan nomor 2:
--   satu peladen, DUA basis data, dan pemisahan lewat skema SEKALIGUS pengguna.
--
-- Peran yang berpasangan dengan `src/penyimpanan/kredensial_baku.py` mencerminkannya
-- satu lawan satu; `peran_riwayat`, `peran_autentikasi`, `peran_pengelola_akun`,
-- `peran_pengguna`, `peran_kurasi`, `peran_penayangan`, `peran_pengisi_antrean`,
-- `peran_telemetri`, `peran_pembaca_sumber`, `peran_koleksi`, `peran_ingesti`, dan
-- `peran_penarikan_dokumen` dipakai lewat
-- tetapan namanya pada modul penyimpannya sendiri.
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
                              'peran_pemanggil_llm','peran_pseudonim',
                              'peran_penyematan','peran_riwayat',
                              'peran_autentikasi','peran_pengelola_akun',
                              'peran_pengguna','peran_kurasi',
                              'peran_penayangan','peran_pengisi_antrean',
                              'peran_telemetri','peran_penarikan',
                              'peran_penarikan_pseudonim','peran_analitik',
                              'peran_penilaian','peran_pembaca_sumber',
                              'peran_koleksi','peran_ingesti',
                              'peran_penarikan_dokumen'] LOOP
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
  TO peran_penjawaban, peran_verifikasi, peran_pemanggil_llm, peran_penyematan,
     peran_riwayat, peran_autentikasi, peran_pengelola_akun, peran_pengguna,
     peran_kurasi, peran_penayangan, peran_pengisi_antrean, peran_telemetri,
     peran_penarikan, peran_analitik, peran_penilaian, peran_pembaca_sumber,
     peran_koleksi, peran_ingesti, peran_penarikan_dokumen;

-- `peran_penyematan` (fitur 026, TK-63) sengaja TIDAK diberi CONNECT ke basis
-- data pseudonim. Jalur penyematan tidak membutuhkannya, dan C-05 menuntut
-- kunci pseudonim tidak terjangkau dari layanan aplikasi mana pun.
--
-- `peran_riwayat` (fitur 028) sama: riwayat menyimpan pemilik berupa
-- pseudonim, dan penulisnya tidak membutuhkan pemetaan ke identitas (C-05).
--
-- `peran_autentikasi` dan `peran_pengelola_akun` (fitur 029) sama pula.
-- Akun berpseudonim (P-1 A) berarti layanan aplikasi tidak pernah perlu tahu
-- siapa orangnya — hanya akunnya. Perkakas tim pun tidak: pasangan pseudonim
-- dengan orang sungguhan diisi peneliti di luar layanan (KA-03, NFR-08).
--
-- `peran_pengguna` (fitur 030) sama: profil, prioritas, dan persetujuan
-- dimiliki pseudonim akun, dan penulisnya tidak membutuhkan pemetaan ke orang.
--
-- `peran_kurasi`, `peran_penayangan`, dan `peran_pengisi_antrean` (fitur 013)
-- sama: jejak kurasi membawa pseudonim kurator dari sesi, bukan orangnya.
--
-- `peran_telemetri` (fitur 034) sama: peristiwa penelitian dimiliki pseudonim,
-- dan perekamnya tidak membutuhkan pemetaan ke orang (C-05, FR-J02).
--
-- `peran_penilaian` (fitur 036) sama: penilaian dimiliki pseudonim lewat
-- percakapannya, dan aduan yang ditulisnya tidak membawa pseudonim sama sekali.
--
-- `peran_pembaca_sumber` dan `peran_koleksi` (fitur 032) sama: pembaca sumber
-- tidak menyentuh data peserta sama sekali, dan koleksi dimiliki pseudonim akun.
--
-- `peran_ingesti` dan `peran_penarikan_dokumen` (fitur 037) sama: keduanya
-- menangani dokumen sumber, bukan data peserta, dan pelakunya kode anggota tim.

GRANT CONNECT ON DATABASE smart_coaching_pseudonim
  TO peran_pseudonim, peran_penarikan_pseudonim;
