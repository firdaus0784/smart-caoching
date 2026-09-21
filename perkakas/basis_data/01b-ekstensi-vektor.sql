-- T-9 fitur 019 · Pemasangan ekstensi pgvector
--
-- Jalankan sebagai superuser pada `smart_coaching`, sesudah 01 membuat basis
-- datanya dan sebelum 05 memakai tipenya:
--
--     psql -d smart_coaching -v ON_ERROR_STOP=1 -f 01b-ekstensi-vektor.sql
--
-- Bernomor `01b` karena ia disisipkan sesudah urutan 01-05 sudah ada. Nomornya
-- menyatakan tempatnya pada urutan jalan, bukan urutan ia ditulis.
--
-- ─────────────────────────────────────────────────────────────────────────
-- Batas yang berkas ini tandai — T-9, sejajar T-9 fitur 024
--
--     Menulis kueri vektornya adalah KODE.
--     Memasang ekstensinya adalah OPERASI.
--
-- `src/rag/pengambilan/vektor.py` menulis `<=>`, `vector(N)`, dan `ORDER BY`
-- jaraknya. Tidak satu baris pun di sana dapat memasang ekstensinya, dan itu
-- bukan kekurangan: `CREATE EXTENSION` menuntut superuser, dan layanan
-- penjawaban tidak boleh memilikinya (C-03, C-17).
--
-- Yang lebih mudah terlupa: `CREATE EXTENSION` sendiri **tidak memasang apa
-- pun**. Ia hanya mendaftarkan ke basis data sesuatu yang sudah ada sebagai
-- berkas pada mesin peladen. Bila paketnya belum dipasang, PostgreSQL
-- menjawab "could not open extension control file" — pesan yang menyebut
-- berkas, bukan menyebut paket, dan yang membacanya mencari di tempat yang
-- salah. Karena itu berkas ini memeriksa lebih dulu dan menjawab dengan
-- perintah pemasangannya.
-- ─────────────────────────────────────────────────────────────────────────

\set ON_ERROR_STOP on

SELECT NOT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'vector')
    AS paket_belum_dipasang \gset

\if :paket_belum_dipasang
  \warn 'GAGAL: paket pgvector belum terpasang pada MESIN peladen.'
  \warn 'CREATE EXTENSION hanya mendaftarkan yang sudah ada; ia tidak mengunduh apa pun.'
  \warn 'Debian/Ubuntu : apt-get install postgresql-16-pgvector'
  \warn 'RHEL/Rocky    : dnf install pgvector_16'
  \warn 'macOS/Homebrew: brew install pgvector'
  \warn 'Dari sumber   : git clone https://github.com/pgvector/pgvector && make && make install'
  \warn 'Sesudah itu jalankan berkas ini lagi. Versi yang disetujui tercatat pada'
  \warn 'ketergantungan-disetujui.toml bagian [sistem.pgvector]; menggantinya tunduk C-12.'
  -- Galat SQL, bukan `\quit`. `\quit` keluar dengan status **0** dan
  -- argumennya diabaikan diam-diam — penyiapan yang gagal akan terbaca
  -- berhasil, dan laporan palsu lebih berbahaya daripada tidak ada laporan.
  -- Ditemukan dengan mencoba, bukan dengan membaca (KB-102).
  DO $$ BEGIN
    RAISE EXCEPTION 'paket pgvector belum terpasang pada mesin peladen';
  END $$;
\endif

CREATE EXTENSION IF NOT EXISTS vector;

-- Versi yang benar-benar terpasang, dicetak agar tercatat pada keluaran
-- penyiapan. C-09 menuntut versi tercatat bagi model; alasan yang sejajar
-- berlaku bagi ekstensi yang menentukan bentuk indeks — percobaan yang
-- diulang di atas versi lain adalah percobaan lain.
SELECT extversion AS versi_pgvector_terpasang FROM pg_extension WHERE extname = 'vector';
