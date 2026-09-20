-- T-4 fitur 019 · Tabel segmen terindeks beserta kolom vektor
--
-- Jalankan sebagai superuser pada `smart_coaching`, sesudah 02-skema-dan-hak.sql:
--
--     psql -d smart_coaching -v dimensi=1024 -f 05-kolom-vektor.sql
--
-- `dimensi` WAJIB diberikan. Ia sengaja tidak berbawaan: dimensi yang
-- diam-diam terpakai adalah dimensi yang tidak pernah dicocokkan dengan model
-- yang sebenarnya dipasang, dan ketidakcocokannya baru terlihat pada kueri
-- pertama di lingkungan sungguhan.
--
-- ─────────────────────────────────────────────────────────────────────────
-- Dua skema, dan pemisahannya bukan soal kerapian
--
-- `indeks_utama`    segmen yang boleh masuk konteks LLM
-- `indeks_metadata` segmen yang TIDAK boleh (C-02, FR-D06)
--
-- Keduanya sudah ada beserta hak aksesnya sejak 02-skema-dan-hak.sql:
-- `peran_pemanggil_llm` tidak diberi USAGE atas `indeks_metadata` sama sekali,
-- sehingga pemisahan C-02 ditolak peladen alih-alih disaring kueri.
--
-- Vektor karena itu cukup menjadi KOLOM pada tabel di masing-masing skema —
-- Keputusan Gerbang 1 nomor 3. Tabel vektor tersendiri tidak menambah
-- penjagaan apa pun di atas itu; ia hanya menambah satu tempat lagi yang
-- dapat hanyut dari pasangannya.
-- ─────────────────────────────────────────────────────────────────────────

\if :{?dimensi}
\else
  \echo 'GAGAL: jalankan dengan -v dimensi=<N>, misalnya -v dimensi=1024'
  \quit
\endif

CREATE EXTENSION IF NOT EXISTS vector;

-- Bidangnya mengikuti `SegmenTerindeks` pada `src/penyimpanan/indeks.py`
-- satu lawan satu. Dua daftar yang menggambarkan hal yang sama akan hanyut,
-- dan yang hanyut tidak terlihat dari salah satunya — itu sebabnya uji
-- membandingkan keduanya alih-alih memercayai keduanya.

CREATE TABLE IF NOT EXISTS indeks_utama.segmen_teks (
    id_segmen                 text PRIMARY KEY,
    id_dokumen                text NOT NULL,
    teks                      text NOT NULL,
    lisensi                   text NOT NULL,
    anonimisasi_terverifikasi boolean NOT NULL,
    penanda_bagian            text NOT NULL,
    vektor                    vector(:dimensi),
    diindeks_pada             timestamptz NOT NULL DEFAULT now()  -- KM-01: UTC
);

CREATE TABLE IF NOT EXISTS indeks_metadata.segmen_teks (
    id_segmen                 text PRIMARY KEY,
    id_dokumen                text NOT NULL,
    teks                      text NOT NULL,
    lisensi                   text NOT NULL,
    anonimisasi_terverifikasi boolean NOT NULL,
    penanda_bagian            text NOT NULL,
    vektor                    vector(:dimensi),
    diindeks_pada             timestamptz NOT NULL DEFAULT now()
);

-- `indeks_tujuan` sengaja BUKAN kolom.
--
-- Ia terbaca dari skema tempat barisnya berada, dan itu yang membuatnya dapat
-- dijaga peladen. Kolom penanda tidak dapat dijaga: hak akses PostgreSQL
-- berlaku pada skema dan tabel, tidak pada nilai baris. Bentuk yang sama
-- dengan `area_simpan` pada 04-tabel-dokumen.sql, dan alasan yang sejajar.

-- Vektor boleh NULL: segmen yang sudah terindeks leksikal tetapi belum
-- disematkan adalah keadaan yang sah selama penyematan berjalan bertahap.
-- Yang TIDAK sah adalah segmen semacam itu muncul sebagai kandidat, dan yang
-- menjaganya kueri pada fitur ini — bukan batasan kolom.
