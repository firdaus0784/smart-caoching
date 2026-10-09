-- Fitur 032 · Catatan korpus, pembaca sumber, dan koleksi — jalankan sebagai
-- superuser pada basis data `smart_coaching`, sesudah 01 s.d. 13.
--
-- Bentuk tabel D-14 Bagian 5.1 (versi 0.18); rancangan `plan.md` fitur 032
-- Bagian 2.
--
-- Yang ditegakkan PELADEN, bukan oleh ketiadaan metode:
--
--   P-2 A, C-03     `peran_pembaca_sumber` membaca `id` dokumen korpus tetapi
--                   tidak `isi`-nya — teks dokumen utuh — dan tidak memegang
--                   USAGE atas karantina. Ia menampilkan bagian yang dirujuk,
--                   bukan dokumen.
--   C-02            Pembaca yang sama tidak memegang USAGE atas
--                   `indeks_metadata`: segmen berlisensi tertutup tidak dapat
--                   dikirimnya, sekalipun kodenya keliru.
--   R-05, C-17      Pembaca tidak menulis apa pun.
--   R-03, C-14      `peran_penayangan` tidak memegang hak apa pun atas
--                   `penemuan.koleksi`: pemilihan beranda tidak dapat membaca
--                   koleksi, sehingga koleksi tidak dapat menjadi sinyal
--                   personalisasi.
--   Tambah-saja     Catatan metadata dan status korpus tidak dapat diubah
--                   maupun dihapus peran aplikasi; yang terbaru berlaku.
--   NFR-09          Hanya `peran_penarikan` yang menghapus koleksi orang lain.

-- ── Catatan metadata asal dokumen — TK-82 A ──────────────────────────
-- Ditulis gerbang ingesti dalam pernyataan yang sama dengan pemindahan
-- dokumen ke korpus (`src/penyimpanan/postgres.py`).
CREATE TABLE IF NOT EXISTS korpus.metadata_dokumen (
  nomor                bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_dokumen           text        NOT NULL,
  judul                text        NOT NULL,
  jenis                text        NOT NULL,
  penerbit             text        NOT NULL,
  tahun                integer     NOT NULL,
  tingkat_kerahasiaan  text        NOT NULL,
  dicatat_pada         timestamptz NOT NULL DEFAULT now()  -- KM-01: UTC
);
CREATE INDEX IF NOT EXISTS metadata_dokumen_terbaru
  ON korpus.metadata_dokumen (id_dokumen, nomor);

-- ── Catatan status keberlakuan — TK-81 A ─────────────────────────────
-- Ditulis perintah `status` perkakas kurasi dalam pernyataan yang sama dengan
-- salinan status kandidat dan butir tayang (`src/penyimpanan/kurasi.py`).
-- Tanpa catatan berarti status belum diketahui, BUKAN `berlaku`.
CREATE TABLE IF NOT EXISTS korpus.status_dokumen (
  nomor              bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_dokumen         text        NOT NULL,
  status             text        NOT NULL,
  rujukan_pengganti  text        NULL,
  dicatat_pada       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS status_dokumen_terbaru
  ON korpus.status_dokumen (id_dokumen, nomor);

-- ── Koleksi — FR-G06 ─────────────────────────────────────────────────
-- Bukan tambah-saja: peserta mengeluarkan butirnya sendiri, dan menyimpan
-- ulang mengganti catatan.
CREATE TABLE IF NOT EXISTS penemuan.koleksi (
  id_pengguna    text        NOT NULL,
  id_butir       text        NOT NULL,
  catatan        text        NULL,
  disimpan_pada  timestamptz NOT NULL,
  PRIMARY KEY (id_pengguna, id_butir)
);

-- Batasan dipasang ulang tiap kali berkas dijalankan (KB-158). Daftar nilai
-- dibandingkan uji dengan `JenisSumber`, `TingkatKerahasiaan`, dan
-- `StatusKeberlakuan`: nilai baru pada enum menjatuhkan uji, bukan penulisan
-- di lapangan.
ALTER TABLE korpus.metadata_dokumen
  DROP CONSTRAINT IF EXISTS metadata_jenis,
  DROP CONSTRAINT IF EXISTS metadata_kerahasiaan,
  DROP CONSTRAINT IF EXISTS metadata_tahun,
  DROP CONSTRAINT IF EXISTS metadata_berisi;
ALTER TABLE korpus.metadata_dokumen
  ADD CONSTRAINT metadata_jenis CHECK (jenis IN
    ('regulasi_resmi', 'data_resmi_agregat', 'artikel_lisensi_terbuka',
     'dokumen_sekolah', 'laporan_lembaga')),
  ADD CONSTRAINT metadata_kerahasiaan CHECK (tingkat_kerahasiaan IN
    ('publik', 'internal_sekolah', 'terbatas')),
  ADD CONSTRAINT metadata_tahun CHECK (tahun >= 1945),
  ADD CONSTRAINT metadata_berisi CHECK (
    char_length(btrim(id_dokumen)) > 0 AND char_length(btrim(judul)) > 0
    AND char_length(btrim(penerbit)) > 0);

ALTER TABLE korpus.status_dokumen
  DROP CONSTRAINT IF EXISTS status_dokumen_status,
  DROP CONSTRAINT IF EXISTS status_dokumen_pengganti,
  DROP CONSTRAINT IF EXISTS status_dokumen_berisi;
ALTER TABLE korpus.status_dokumen
  ADD CONSTRAINT status_dokumen_status CHECK (status IN ('berlaku', 'diubah', 'dicabut')),
  -- `coalesce`: CHECK lulus bila hasilnya NULL.
  ADD CONSTRAINT status_dokumen_pengganti CHECK (
    rujukan_pengganti IS NULL
    OR (status <> 'berlaku' AND coalesce(char_length(btrim(rujukan_pengganti)), 0) > 0)),
  ADD CONSTRAINT status_dokumen_berisi CHECK (char_length(btrim(id_dokumen)) > 0);

ALTER TABLE penemuan.koleksi
  DROP CONSTRAINT IF EXISTS koleksi_pola_pemilik,
  DROP CONSTRAINT IF EXISTS koleksi_catatan_berisi;
ALTER TABLE penemuan.koleksi
  ADD CONSTRAINT koleksi_pola_pemilik CHECK (id_pengguna ~ '^psd_[a-z]{16}$'),
  ADD CONSTRAINT koleksi_catatan_berisi CHECK (
    catatan IS NULL OR char_length(btrim(catatan)) > 0);

-- ── Hak ──────────────────────────────────────────────────────────────
REVOKE ALL ON korpus.metadata_dokumen, korpus.status_dokumen, penemuan.koleksi
  FROM PUBLIC;

-- Hak bawaan skema korpus (02-skema-dan-hak.sql) memberi `peran_verifikasi`
-- SELECT, INSERT, UPDATE atas setiap tabel baru di sana. Catatan tambah-saja
-- tidak diubah siapa pun, dan status bukan pekerjaan verifikator.
REVOKE UPDATE ON korpus.metadata_dokumen, korpus.status_dokumen FROM peran_verifikasi;
REVOKE INSERT ON korpus.status_dokumen FROM peran_verifikasi;
-- `peran_penjawaban` dan `peran_pemanggil_llm` tetap memegang SELECT bawaan:
-- jalur penjawab kelak membaca status (C-07) dan metadata (penyusun sitasi).

-- Perkakas kurasi: mencatat status, tanpa membaca korpus.
GRANT USAGE ON SCHEMA korpus TO peran_pengisi_antrean;
GRANT INSERT ON korpus.status_dokumen TO peran_pengisi_antrean;

-- Pembaca sumber: hanya yang tampil pada S-10.
GRANT USAGE ON SCHEMA korpus, indeks_utama TO peran_pembaca_sumber;
GRANT SELECT (id) ON korpus.dokumen_sumber TO peran_pembaca_sumber;
GRANT SELECT ON korpus.metadata_dokumen, korpus.status_dokumen TO peran_pembaca_sumber;
GRANT SELECT (id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian)
  ON indeks_utama.segmen_teks TO peran_pembaca_sumber;

-- Koleksi: tabelnya saja. Kelayakan butir dibaca penayang.
GRANT USAGE ON SCHEMA penemuan TO peran_koleksi;
GRANT SELECT, INSERT, DELETE ON penemuan.koleksi TO peran_koleksi;
GRANT UPDATE (catatan, disimpan_pada) ON penemuan.koleksi TO peran_koleksi;

-- Penarikan data (NFR-09): kolom pemilik saja, lalu hapus.
GRANT SELECT (id_pengguna) ON penemuan.koleksi TO peran_penarikan;
GRANT DELETE ON penemuan.koleksi TO peran_penarikan;
