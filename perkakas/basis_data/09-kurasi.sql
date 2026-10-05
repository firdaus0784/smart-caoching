-- Fitur 013 · Kurasi dan penemuan harian — jalankan sebagai superuser pada basis
-- data `smart_coaching`, sesudah 01 s.d. 08.
--
-- Nama tabel dan kolom mengikuti D-14 Bagian 4.6, 4.7, dan 5.1 (versi 0.12) dan
-- D-04 Bagian 7.3 (versi 0.12), yang ditulis lebih dulu pada T-1.
--
-- Yang ditegakkan PELADEN (plan Bagian 2.2):
--
--   C-06            Butir tayang hanya dapat merujuk putusan yang MENYETUJUI
--                   butir itu sendiri — kunci asing gabungan atas
--                   (nomor, id_butir, menyetujui). Peran yang menayangkan tidak
--                   dapat membaca antrean maupun menulis butir tayang.
--   FR-I07          Kandidat hanya ditambahkan perkakas tim, sesudah penyaringan
--                   L1–L3. Layar kurator tidak dapat menambahkannya.
--   C-07            Salinan status regulasi hanya diperbarui perkakas tim (K-4).
--   Empat putusan   `jenis` memuat empat nilai D-06 Bagian 7.3; penarikan dicatat
--                   pada tabelnya sendiri, bukan sebagai putusan kelima.
--   C-05            Pemutus dan pemilik berupa pseudonim akun, bukan nama akun.
--   K-2             Satu butir tayang sekali bagi orang yang sama.
--   Tanpa hapus     Tidak satu peran pun memegang DELETE atau TRUNCATE.
--   C-03            Tidak satu pun dari ketiga peran menjangkau karantina atau
--                   korpus; metadata sumber disalin ke kandidat (K-3).

CREATE SCHEMA IF NOT EXISTS kurasi;
CREATE SCHEMA IF NOT EXISTS penemuan;
REVOKE ALL ON SCHEMA kurasi, penemuan FROM PUBLIC;

CREATE TABLE IF NOT EXISTS kurasi.kandidat (
  id_butir           text        PRIMARY KEY CHECK (char_length(btrim(id_butir)) > 0),
  butir              jsonb       NOT NULL,
  sumber             jsonb       NOT NULL,
  id_dokumen_sumber  text        NOT NULL CHECK (char_length(btrim(id_dokumen_sumber)) > 0),
  kategori           text        NOT NULL
                     CHECK (kategori IN ('K1','K2','K3','K4','K5','K6','K7','K8')),
  status_keberlakuan text        CHECK (status_keberlakuan IN ('berlaku', 'diubah', 'dicabut')),
  masuk_pada         timestamptz NOT NULL,
  kembali_pada       date
);

CREATE INDEX IF NOT EXISTS kandidat_per_dokumen ON kurasi.kandidat (id_dokumen_sumber);

CREATE TABLE IF NOT EXISTS kurasi.putusan (
  nomor             bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_butir          text        NOT NULL REFERENCES kurasi.kandidat (id_butir),
  jenis             text        NOT NULL
                    CHECK (jenis IN ('setujui', 'sunting_lalu_setujui', 'tolak', 'tunda')),
  menyetujui        boolean     GENERATED ALWAYS AS
                    (jenis IN ('setujui', 'sunting_lalu_setujui')) STORED,
  peran             text        NOT NULL CHECK (peran IN ('kurator', 'kurator_pengganti')),
  pseudonim_kurator text        NOT NULL,
  alasan            text        NOT NULL CHECK (char_length(btrim(alasan)) > 0),
  waktu             timestamptz NOT NULL,
  UNIQUE (nomor, id_butir, menyetujui)
);

-- Satu putusan akhir per butir. Tunda boleh berulang; setujui, sunting, dan
-- tolak mengakhiri antrean butir itu.
CREATE UNIQUE INDEX IF NOT EXISTS putusan_akhir_tunggal
  ON kurasi.putusan (id_butir) WHERE jenis <> 'tunda';

CREATE TABLE IF NOT EXISTS kurasi.butir_tayang (
  id_butir            text        PRIMARY KEY REFERENCES kurasi.kandidat (id_butir),
  butir               jsonb       NOT NULL,
  sumber              jsonb       NOT NULL,
  id_dokumen_sumber   text        NOT NULL,
  kategori            text        NOT NULL
                      CHECK (kategori IN ('K1','K2','K3','K4','K5','K6','K7','K8')),
  status_keberlakuan  text        CHECK (status_keberlakuan IN ('berlaku', 'diubah', 'dicabut')),
  nomor_putusan       bigint      NOT NULL UNIQUE,
  menyetujui          boolean     NOT NULL DEFAULT true CHECK (menyetujui),
  tayang_pada         timestamptz NOT NULL,
  ditarik_pada        timestamptz,
  alasan_tarik        text,
  perlu_tinjauan_pada timestamptz,
  FOREIGN KEY (nomor_putusan, id_butir, menyetujui)
    REFERENCES kurasi.putusan (nomor, id_butir, menyetujui),
  CHECK ((ditarik_pada IS NULL) = (alasan_tarik IS NULL))
);

CREATE INDEX IF NOT EXISTS butir_tayang_per_dokumen ON kurasi.butir_tayang (id_dokumen_sumber);

CREATE TABLE IF NOT EXISTS kurasi.penarikan (
  nomor             bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_butir          text        NOT NULL REFERENCES kurasi.butir_tayang (id_butir),
  pemicu            text        NOT NULL CHECK (pemicu IN ('regulasi_sumber_berubah',
                                                       'kekeliruan_isi_dilaporkan',
                                                       'data_sumber_diperbarui')),
  tindakan          text        NOT NULL CHECK (tindakan IN ('ditarik', 'ditandai_perlu_tinjauan')),
  peran             text        CHECK (peran IN ('kurator', 'kurator_pengganti')),
  pseudonim_kurator text,
  alasan            text        NOT NULL CHECK (char_length(btrim(alasan)) > 0),
  waktu             timestamptz NOT NULL,
  CHECK ((peran IS NULL) = (pseudonim_kurator IS NULL)),
  -- Tanpa pemutus berarti penarikan otomatis oleh perkakas — hanya bagi
  -- regulasi yang berubah (D-06 Bagian 7.5, K-4).
  CHECK (peran IS NOT NULL OR pemicu = 'regulasi_sumber_berubah')
);

CREATE TABLE IF NOT EXISTS penemuan.tayang_harian (
  id_pengguna      text        NOT NULL,
  tanggal          date        NOT NULL,   -- tanggal WIB (P-4), bukan UTC
  id_butir         text        NOT NULL REFERENCES kurasi.butir_tayang (id_butir),
  urutan           smallint    NOT NULL CHECK (urutan > 0),
  ditayangkan_pada timestamptz NOT NULL,
  PRIMARY KEY (id_pengguna, id_butir)
);

CREATE INDEX IF NOT EXISTS tayang_harian_per_tanggal
  ON penemuan.tayang_harian (id_pengguna, tanggal);

CREATE TABLE IF NOT EXISTS penemuan.belum_relevan (
  nomor       bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_pengguna text        NOT NULL,
  id_butir    text        NOT NULL REFERENCES kurasi.butir_tayang (id_butir),
  alasan      text        NOT NULL CHECK (char_length(btrim(alasan)) > 0),
  waktu       timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS belum_relevan_per_pengguna
  ON penemuan.belum_relevan (id_pengguna);

-- Pola pseudonim dipasang ulang tiap kali berkas ini dijalankan — pelajaran
-- KB-158: batasan di dalam CREATE TABLE tidak sampai ke tabel yang sudah ada.
ALTER TABLE kurasi.putusan DROP CONSTRAINT IF EXISTS putusan_pola_pemutus;
ALTER TABLE kurasi.putusan
  ADD CONSTRAINT putusan_pola_pemutus CHECK (pseudonim_kurator ~ '^psd_[a-z]{16}$');
ALTER TABLE kurasi.penarikan DROP CONSTRAINT IF EXISTS penarikan_pola_pemutus;
ALTER TABLE kurasi.penarikan
  ADD CONSTRAINT penarikan_pola_pemutus CHECK (pseudonim_kurator ~ '^psd_[a-z]{16}$');
ALTER TABLE penemuan.tayang_harian DROP CONSTRAINT IF EXISTS tayang_pola_pemilik;
ALTER TABLE penemuan.tayang_harian
  ADD CONSTRAINT tayang_pola_pemilik CHECK (id_pengguna ~ '^psd_[a-z]{16}$');
ALTER TABLE penemuan.belum_relevan DROP CONSTRAINT IF EXISTS belum_relevan_pola_pemilik;
ALTER TABLE penemuan.belum_relevan
  ADD CONSTRAINT belum_relevan_pola_pemilik CHECK (id_pengguna ~ '^psd_[a-z]{16}$');

REVOKE ALL ON kurasi.kandidat, kurasi.putusan, kurasi.butir_tayang, kurasi.penarikan,
              penemuan.tayang_harian, penemuan.belum_relevan
  FROM PUBLIC;

-- Perkakas tim: mengisi antrean, memperbarui status regulasi, menarik otomatis.
GRANT USAGE ON SCHEMA kurasi TO peran_pengisi_antrean;
GRANT SELECT, INSERT ON kurasi.kandidat TO peran_pengisi_antrean;
GRANT UPDATE (status_keberlakuan) ON kurasi.kandidat TO peran_pengisi_antrean;
GRANT SELECT ON kurasi.butir_tayang TO peran_pengisi_antrean;
GRANT UPDATE (status_keberlakuan, ditarik_pada, alasan_tarik)
  ON kurasi.butir_tayang TO peran_pengisi_antrean;
GRANT INSERT ON kurasi.penarikan TO peran_pengisi_antrean;

-- Rute kurator: memutus, menayangkan, menarik.
GRANT USAGE ON SCHEMA kurasi TO peran_kurasi;
GRANT SELECT ON kurasi.kandidat TO peran_kurasi;
GRANT UPDATE (kembali_pada) ON kurasi.kandidat TO peran_kurasi;
GRANT SELECT, INSERT ON kurasi.putusan TO peran_kurasi;
GRANT SELECT, INSERT ON kurasi.butir_tayang TO peran_kurasi;
GRANT UPDATE (ditarik_pada, alasan_tarik, perlu_tinjauan_pada)
  ON kurasi.butir_tayang TO peran_kurasi;
GRANT SELECT, INSERT ON kurasi.penarikan TO peran_kurasi;

-- Rute pengguna: membaca butir tayang saja, mencatat butir hari ini.
GRANT USAGE ON SCHEMA kurasi, penemuan TO peran_penayangan;
GRANT SELECT ON kurasi.butir_tayang TO peran_penayangan;
GRANT SELECT, INSERT ON penemuan.tayang_harian, penemuan.belum_relevan TO peran_penayangan;
