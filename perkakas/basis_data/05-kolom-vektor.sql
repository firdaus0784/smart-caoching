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

\set ON_ERROR_STOP on

\if :{?dimensi}
\else
  \warn 'GAGAL: jalankan dengan -v dimensi=<N>, misalnya -v dimensi=1024'
  -- Galat SQL, bukan `\quit`. Penjagaan ini ditulis pada T-4 dengan `\quit`,
  -- dan selama itu berkas ini **keluar dengan status 0** ketika dimensinya
  -- lupa diberikan: penyiapan yang tidak membuat satu tabel pun terbaca
  -- berhasil. Ditemukan pada T-9, dengan mencoba (KB-102).
  DO $$ BEGIN
    RAISE EXCEPTION 'dimensi wajib diberikan: jalankan dengan -v dimensi=<N>';
  END $$;
\endif

-- Ekstensinya TIDAK dipasang di sini. Ia dipasang 01b-ekstensi-vektor.sql,
-- dan berkas ini berhenti bila ekstensinya belum ada — dengan menyebut berkas
-- mana yang memasangnya, bukan dengan galat tipe `vector` tidak dikenal.
--
-- Memasangnya di dua tempat akan membuat salah satunya usang tanpa terlihat.

SELECT NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')
    AS ekstensi_belum_ada \gset

\if :ekstensi_belum_ada
  \warn 'GAGAL: ekstensi pgvector belum ada pada basis data ini.'
  \warn 'Jalankan lebih dulu: psql -d smart_coaching -f 01b-ekstensi-vektor.sql'
  -- Galat SQL, bukan `\quit` — lihat alasannya pada 01b-ekstensi-vektor.sql.
  DO $$ BEGIN
    RAISE EXCEPTION 'ekstensi pgvector belum ada pada basis data ini';
  END $$;
\endif

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
    vektor_sematan            vector(:dimensi),
    versi_model_sematan       text,
    diindeks_pada             timestamptz NOT NULL DEFAULT now()  -- KM-01: UTC
);

CREATE TABLE IF NOT EXISTS indeks_metadata.segmen_teks (
    id_segmen                 text PRIMARY KEY,
    id_dokumen                text NOT NULL,
    teks                      text NOT NULL,
    lisensi                   text NOT NULL,
    anonimisasi_terverifikasi boolean NOT NULL,
    penanda_bagian            text NOT NULL,
    vektor_sematan            vector(:dimensi),
    versi_model_sematan       text,
    diindeks_pada             timestamptz NOT NULL DEFAULT now()
);

-- `indeks_tujuan` sengaja BUKAN kolom.
--
-- Ia terbaca dari skema tempat barisnya berada, dan itu yang membuatnya dapat
-- dijaga peladen. Kolom penanda tidak dapat dijaga: hak akses PostgreSQL
-- berlaku pada skema dan tabel, tidak pada nilai baris. Bentuk yang sama
-- dengan `area_simpan` pada 04-tabel-dokumen.sql, dan alasan yang sejajar.

-- Nama kedua kolom mengikuti `docs/D04.md` Bagian 7.2, yang menetapkannya
-- sebelum proyek ini berjalan. Fitur 019 sempat menamainya `vektor` saja dan
-- tidak pernah membuat `versi_model_sematan` sama sekali — tercatat TK-60,
-- diluruskan pada T-1 fitur 026.
--
-- `versi_model_sematan` berupa kolom per baris, bukan tabel metadata
-- tersendiri: indeks yang bercampur dua model terdeteksi dengan
-- SELECT DISTINCT, dan kebenarannya tinggal bersama datanya. Tabel
-- tersendiri dapat hanyut dari baris yang digambarkannya.
--
-- Vektor boleh NULL: segmen yang sudah terindeks leksikal tetapi belum
-- disematkan adalah keadaan yang sah selama penyematan berjalan bertahap.
-- Yang TIDAK sah adalah segmen semacam itu muncul sebagai kandidat, dan yang
-- menjaganya kueri pada fitur ini — bukan batasan kolom.

-- ─────────────────────────────────────────────────────────────────────────
-- Migrasi tabel yang SUDAH ADA — T-1 fitur 026
--
-- `CREATE TABLE IF NOT EXISTS` di atas tidak menyentuh tabel yang sudah ada.
-- Pada basis data yang dibangun sebelum 23 September 2026, kolomnya masih
-- bernama `vektor` dan `versi_model_sematan` belum ada — dan berkas ini akan
-- **selesai dengan status 0 tanpa mengubah apa pun**. Bentuk kegagalan yang
-- sama dengan `\quit` pada T-9 fitur 019: penyiapan yang tidak mengerjakan
-- apa-apa terbaca berhasil.
--
-- Ketiga pernyataan di bawah aman dijalankan berulang.
-- ─────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
  s text;
BEGIN
  FOREACH s IN ARRAY ARRAY['indeks_utama', 'indeks_metadata'] LOOP
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = s AND table_name = 'segmen_teks' AND column_name = 'vektor'
    ) AND NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema = s AND table_name = 'segmen_teks' AND column_name = 'vektor_sematan'
    ) THEN
      EXECUTE format('ALTER TABLE %I.segmen_teks RENAME COLUMN vektor TO vektor_sematan', s);
    END IF;

    -- Kolom lama yang tersisa berdampingan dengan yang baru dibuang. Dua
    -- kolom yang menyimpan hal yang sama akan berbeda isinya pada hari salah
    -- satunya lupa ditulis, dan yang lupa ditulis adalah yang tidak dibaca uji.
    EXECUTE format('ALTER TABLE %I.segmen_teks DROP COLUMN IF EXISTS vektor', s);
    EXECUTE format(
      'ALTER TABLE %I.segmen_teks ADD COLUMN IF NOT EXISTS versi_model_sematan text', s
    );
  END LOOP;
END $$;
