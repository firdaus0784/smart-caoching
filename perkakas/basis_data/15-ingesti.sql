-- Fitur 037 · Catatan gerbang ingesti dan peran dokumen — jalankan sebagai
-- superuser pada basis data `smart_coaching`, sesudah 01 s.d. 14.
--
-- Bentuk tabel D-14 Bagian 5.1 (versi 0.19); rancangan `plan.md` fitur 037
-- Bagian 2.
--
-- Yang ditegakkan PELADEN, bukan oleh ketiadaan metode:
--
--   P-2 A, C-03     Tiga peran dokumen, satu per kredensial kode. Ingesti
--                   menaruh dokumen di karantina tanpa dapat membacanya.
--                   Verifikator membaca karantina dan hanya dapat MENGELUARKAN
--                   dokumen darinya — tidak menyisipkan maupun mengubah, agar
--                   ia tidak dapat menyunting bahan yang sedang dinilainya.
--                   Penarikan mengeluarkan dokumen dari korpus dan tidak dapat
--                   memasukkan apa pun ke sana. Peran aplikasi lain tidak
--                   memegang USAGE atas karantina.
--   TK-84 A         Penarikan menghapus segmen dokumen dari kedua indeks tanpa
--                   dapat membaca teksnya.
--   TK-85 A         Ingesti membaca kolom `id` korpus saja, agar unggahan ulang
--                   atas dokumen yang berada di korpus ditolak di dalam
--                   pernyataan sisipnya.
--   P-1 A           Catatan karantina tambah-saja; keadaan gerbang diturunkan
--                   darinya, bukan disunting.
--   P-6 A           Pelaku berupa kode anggota tim, bukan nama orang.

-- ── Hak bawaan karantina bagi verifikator ────────────────────────────
-- `02-skema-dan-hak.sql` memberi `peran_verifikasi` SELECT, INSERT, UPDATE
-- atas setiap tabel baru di karantina. Dicabut LEBIH DULU, sebelum tabel di
-- bawah dibuat, dan berlaku pula bagi tabel karantina kelak.
ALTER DEFAULT PRIVILEGES IN SCHEMA karantina
  REVOKE INSERT, UPDATE ON TABLES FROM peran_verifikasi;

-- ── Penerimaan — satu baris per unggahan; yang terbaru berlaku ──────────
-- Ditulis `peran_ingesti` dalam pernyataan yang sama dengan teks dokumen
-- karantina dan temuannya (`src/penyimpanan/karantina.py`).
CREATE TABLE IF NOT EXISTS karantina.penerimaan (
  nomor                       bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_dokumen                  text        NOT NULL,
  judul                       text        NOT NULL,
  jenis                       text        NOT NULL,
  penerbit                    text        NOT NULL,
  tahun                       integer     NOT NULL,
  tingkat_kerahasiaan         text        NOT NULL,
  status_persetujuan_pemilik  text        NOT NULL,
  samaran                     jsonb       NOT NULL,
  id_penerima                 text        NOT NULL,
  diterima_pada               timestamptz NOT NULL DEFAULT now()  -- KM-01: UTC
);
CREATE INDEX IF NOT EXISTS penerimaan_terbaru
  ON karantina.penerimaan (id_dokumen, nomor);

-- ── Temuan pola instruksi adversarial (FR-B08) ───────────────────────
-- Atas teks SESUDAH disamarkan: kutipannya tidak membawa pengenal berpola.
CREATE TABLE IF NOT EXISTS karantina.temuan_pola (
  nomor             bigint  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nomor_penerimaan  bigint  NOT NULL REFERENCES karantina.penerimaan (nomor),
  pola              text    NOT NULL,
  mulai             integer NOT NULL,
  akhir             integer NOT NULL,
  kutipan           text    NOT NULL
);

-- ── Tinjauan manusia atas temuan ─────────────────────────────────────
-- Hanya yang merujuk penerimaan terbaru yang berlaku: unggahan ulang
-- membatalkan tinjauan lama tanpa menghapusnya.
CREATE TABLE IF NOT EXISTS karantina.tinjauan_temuan (
  nomor             bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nomor_penerimaan  bigint      NOT NULL REFERENCES karantina.penerimaan (nomor),
  id_peninjau       text        NOT NULL,
  catatan           text        NOT NULL,
  ditinjau_pada     timestamptz NOT NULL DEFAULT now()
);

-- ── Jejak area — D-04 Bagian 7.2 ─────────────────────────────────────
-- Ditulis dalam pernyataan yang sama dengan pemindahan yang dicatatnya.
-- `nomor_penerimaan` NOT NULL: dokumen yang tidak pernah diterima tidak
-- memiliki putusan.
CREATE TABLE IF NOT EXISTS karantina.jejak_area (
  id                bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_dokumen        text        NOT NULL,
  nomor_penerimaan  bigint      NOT NULL REFERENCES karantina.penerimaan (nomor),
  putusan           text        NOT NULL,
  id_pelaku         text        NOT NULL,
  dari_area         text        NOT NULL,
  ke_area           text        NOT NULL,
  alasan            text        NOT NULL,
  waktu             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS jejak_area_dokumen
  ON karantina.jejak_area (id_dokumen, id);

-- Batasan dipasang ulang tiap kali berkas dijalankan (KB-158). Daftar nilai
-- dibandingkan uji dengan `JenisSumber`, `TingkatKerahasiaan`,
-- `StatusPersetujuan`, `PutusanGerbang`, `Area`, dan jenis pendeteksi FR-B04.
ALTER TABLE karantina.penerimaan
  DROP CONSTRAINT IF EXISTS penerimaan_jenis,
  DROP CONSTRAINT IF EXISTS penerimaan_kerahasiaan,
  DROP CONSTRAINT IF EXISTS penerimaan_persetujuan,
  DROP CONSTRAINT IF EXISTS penerimaan_tahun,
  DROP CONSTRAINT IF EXISTS penerimaan_berisi,
  DROP CONSTRAINT IF EXISTS penerimaan_samaran,
  DROP CONSTRAINT IF EXISTS penerimaan_penerima;
ALTER TABLE karantina.penerimaan
  ADD CONSTRAINT penerimaan_jenis CHECK (jenis IN
    ('regulasi_resmi', 'data_resmi_agregat', 'artikel_lisensi_terbuka',
     'dokumen_sekolah', 'laporan_lembaga')),
  ADD CONSTRAINT penerimaan_kerahasiaan CHECK (tingkat_kerahasiaan IN
    ('publik', 'internal_sekolah', 'terbatas')),
  ADD CONSTRAINT penerimaan_persetujuan CHECK (status_persetujuan_pemilik IN
    ('belum_diminta', 'diberikan', 'ditolak', 'dicabut')),
  ADD CONSTRAINT penerimaan_tahun CHECK (tahun >= 1945),
  ADD CONSTRAINT penerimaan_berisi CHECK (
    char_length(btrim(id_dokumen)) > 0 AND char_length(btrim(judul)) > 0
    AND char_length(btrim(penerbit)) > 0),
  -- Keenam jenis, tidak kurang dan tidak lebih, masing-masing bilangan cacah:
  -- jumlah, bukan nilai yang disamarkan (P-5 A, KM-03).
  ADD CONSTRAINT penerimaan_samaran CHECK (
    jsonb_typeof(samaran) = 'object'
    AND samaran ?& ARRAY['nik', 'nip', 'nisn', 'nuptk', 'telepon', 'rekening']
    AND samaran - ARRAY['nik', 'nip', 'nisn', 'nuptk', 'telepon', 'rekening'] = '{}'::jsonb
    AND NOT jsonb_path_exists(samaran, '$.* ? (@.type() != "number" || @ < 0)')),
  ADD CONSTRAINT penerimaan_penerima CHECK (id_penerima ~ '^[a-z]{2,8}-[0-9]{3}$');

ALTER TABLE karantina.temuan_pola
  DROP CONSTRAINT IF EXISTS temuan_rentang,
  DROP CONSTRAINT IF EXISTS temuan_pola_berisi;
ALTER TABLE karantina.temuan_pola
  ADD CONSTRAINT temuan_rentang CHECK (mulai >= 0 AND akhir >= mulai),
  ADD CONSTRAINT temuan_pola_berisi CHECK (char_length(btrim(pola)) > 0);

ALTER TABLE karantina.tinjauan_temuan
  DROP CONSTRAINT IF EXISTS tinjauan_peninjau;
ALTER TABLE karantina.tinjauan_temuan
  ADD CONSTRAINT tinjauan_peninjau CHECK (id_peninjau ~ '^[a-z]{2,8}-[0-9]{3}$');

ALTER TABLE karantina.jejak_area
  DROP CONSTRAINT IF EXISTS jejak_putusan,
  DROP CONSTRAINT IF EXISTS jejak_area_nilai,
  DROP CONSTRAINT IF EXISTS jejak_arah,
  DROP CONSTRAINT IF EXISTS jejak_pelaku,
  DROP CONSTRAINT IF EXISTS jejak_alasan;
ALTER TABLE karantina.jejak_area
  ADD CONSTRAINT jejak_putusan CHECK (putusan IN ('setujui', 'tolak', 'cabut_persetujuan')),
  ADD CONSTRAINT jejak_area_nilai CHECK (dari_area IN ('karantina', 'korpus')
    AND ke_area IN ('karantina', 'korpus')),
  -- Arah menurut putusan: setujui satu-satunya jalan ke korpus; tolak menahan;
  -- pencabutan hanya mengeluarkan.
  ADD CONSTRAINT jejak_arah CHECK (
    (putusan = 'setujui' AND dari_area = 'karantina' AND ke_area = 'korpus')
    OR (putusan = 'tolak' AND dari_area = 'karantina' AND ke_area = 'karantina')
    OR (putusan = 'cabut_persetujuan' AND ke_area = 'karantina')),
  ADD CONSTRAINT jejak_pelaku CHECK (id_pelaku ~ '^[a-z]{2,8}-[0-9]{3}$'),
  ADD CONSTRAINT jejak_alasan CHECK (char_length(btrim(alasan)) > 0);

-- ── Hak ──────────────────────────────────────────────────────────────
REVOKE ALL ON karantina.penerimaan, karantina.temuan_pola,
  karantina.tinjauan_temuan, karantina.jejak_area FROM PUBLIC, peran_verifikasi;

-- Verifikator: membaca seluruh catatan; menulis tinjauan dan putusan;
-- mengeluarkan dokumen dari karantina, tidak menaruh maupun menyunting.
REVOKE INSERT, UPDATE ON karantina.dokumen_sumber FROM peran_verifikasi;
GRANT DELETE ON karantina.dokumen_sumber TO peran_verifikasi;
GRANT SELECT ON karantina.penerimaan, karantina.temuan_pola,
  karantina.tinjauan_temuan, karantina.jejak_area TO peran_verifikasi;
GRANT INSERT ON karantina.tinjauan_temuan, karantina.jejak_area TO peran_verifikasi;

-- Ingesti: menaruh dan mengganti teks karantina tanpa membacanya. `SELECT (id)`
-- karena `WHERE` dan `RETURNING` membaca kolom itu; `SELECT (nomor)` atas
-- penerimaan karena temuan merujuk nomor yang baru lahir. Penggantian memakai
-- `UPDATE` lalu `INSERT`, bukan `ON CONFLICT`: `excluded.isi` menuntut hak baca
-- `isi`, dan hak itu sengaja tidak diberikan.
GRANT USAGE ON SCHEMA karantina, korpus TO peran_ingesti;
GRANT INSERT ON karantina.dokumen_sumber TO peran_ingesti;
GRANT SELECT (id), UPDATE (isi, disimpan_pada) ON karantina.dokumen_sumber TO peran_ingesti;
GRANT INSERT ON karantina.penerimaan, karantina.temuan_pola TO peran_ingesti;
GRANT SELECT (nomor) ON karantina.penerimaan TO peran_ingesti;
GRANT SELECT (id) ON korpus.dokumen_sumber TO peran_ingesti;

-- Penarikan persetujuan: keluar dari korpus beserta segmennya, ke karantina.
GRANT USAGE ON SCHEMA karantina, korpus, indeks_utama, indeks_metadata
  TO peran_penarikan_dokumen;
GRANT SELECT, DELETE ON korpus.dokumen_sumber TO peran_penarikan_dokumen;
GRANT INSERT ON karantina.dokumen_sumber TO peran_penarikan_dokumen;
GRANT SELECT (nomor, id_dokumen) ON karantina.penerimaan TO peran_penarikan_dokumen;
GRANT INSERT ON karantina.jejak_area TO peran_penarikan_dokumen;
GRANT SELECT (id_dokumen), DELETE ON indeks_utama.segmen_teks, indeks_metadata.segmen_teks
  TO peran_penarikan_dokumen;
