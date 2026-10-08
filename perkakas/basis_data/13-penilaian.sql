-- Fitur 036 · Penilaian jawaban dan aduan kurator — jalankan sebagai superuser
-- pada basis data `smart_coaching`, sesudah 01 s.d. 12.
--
-- Bentuk tabel D-14 Bagian 5.1 (versi 0.17); rancangan `plan.md` fitur 036
-- Bagian 2.
--
-- Yang ditegakkan PELADEN, bukan oleh ketiadaan metode:
--
--   C-07            `peran_riwayat` MENAMBAH `riwayat.pesan` tetapi tidak dapat
--                   membacanya: rute riwayat tidak dapat menayangkan ulang
--                   jawaban lama, sekalipun kodenya keliru (TK-69, P-1 A).
--   R-06, P-2 B     Aduan adalah SALINAN yang lahir saat peserta mencentang.
--                   `peran_kurasi` tidak memegang USAGE atas skema `riwayat`,
--                   dan tidak membaca `aduan.nomor_penilaian` — tautan satu-
--                   satunya ke penilaian, pesan, dan pemiliknya.
--   Tambah-saja     Tidak satu peran aplikasi pun mengubah maupun menghapus
--                   kelima tabel. Penilaian yang diganti tetap tercatat; aduan
--                   yang gugur ditandai pada tabel tersendiri, bukan diubah.
--   NFR-09          Hanya `peran_penarikan` yang menghapus, per pemilik.

CREATE TABLE IF NOT EXISTS riwayat.pesan (
  id_pesan       text        PRIMARY KEY,
  id_percakapan  uuid        NOT NULL REFERENCES riwayat.percakapan (id_percakapan),
  tanggapan      jsonb       NOT NULL,
  waktu          timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS riwayat.penilaian (
  nomor             bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_pesan          text        NOT NULL REFERENCES riwayat.pesan (id_pesan),
  nilai             text        NOT NULL,
  alasan            text        NULL,
  kirim_ke_kurator  boolean     NOT NULL,
  waktu             timestamptz NOT NULL
);

-- Penilaian terakhir per pesan dibaca berurutan nomor.
CREATE INDEX IF NOT EXISTS penilaian_pesan_nomor ON riwayat.penilaian (id_pesan, nomor);

CREATE TABLE IF NOT EXISTS kurasi.aduan (
  nomor            bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  nomor_penilaian  bigint      NOT NULL UNIQUE REFERENCES riwayat.penilaian (nomor),
  pertanyaan       text        NOT NULL,
  tanggapan        jsonb       NOT NULL,
  alasan           text        NULL,
  diadukan_pada    timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS kurasi.aduan_digantikan (
  nomor_aduan  bigint      PRIMARY KEY REFERENCES kurasi.aduan (nomor),
  waktu        timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS kurasi.tindak_lanjut_aduan (
  nomor_aduan        bigint      PRIMARY KEY REFERENCES kurasi.aduan (nomor),
  tindak_lanjut      text        NOT NULL,
  catatan            text        NOT NULL,
  peran              text        NOT NULL,
  pseudonim_kurator  text        NOT NULL,
  waktu              timestamptz NOT NULL
);

-- Dipasang ulang tiap kali berkas dijalankan (KB-158).
ALTER TABLE riwayat.pesan
  DROP CONSTRAINT IF EXISTS pesan_id_isi,
  DROP CONSTRAINT IF EXISTS pesan_tanggapan_sendiri,
  DROP CONSTRAINT IF EXISTS pesan_tanpa_keyakinan;
ALTER TABLE riwayat.pesan
  ADD CONSTRAINT pesan_id_isi CHECK (char_length(id_pesan) > 0),
  -- Tanggapan yang tercatat milik pesan ini, bukan salinan pesan lain.
  ADD CONSTRAINT pesan_tanggapan_sendiri
    CHECK (jsonb_typeof(tanggapan) = 'object' AND tanggapan ->> 'id_pesan' = id_pesan),
  -- FR-F06: tingkat keyakinan tidak pernah menjadi angka yang tersimpan.
  ADD CONSTRAINT pesan_tanpa_keyakinan CHECK (NOT tanggapan ? 'tingkat_keyakinan');

ALTER TABLE riwayat.penilaian
  DROP CONSTRAINT IF EXISTS penilaian_nilai,
  DROP CONSTRAINT IF EXISTS penilaian_kirim_hanya_keliru,
  DROP CONSTRAINT IF EXISTS penilaian_alasan_berisi;
ALTER TABLE riwayat.penilaian
  ADD CONSTRAINT penilaian_nilai CHECK (nilai IN ('membantu', 'tidak_membantu', 'keliru')),
  ADD CONSTRAINT penilaian_kirim_hanya_keliru CHECK (NOT kirim_ke_kurator OR nilai = 'keliru'),
  ADD CONSTRAINT penilaian_alasan_berisi CHECK (alasan IS NULL OR char_length(btrim(alasan)) > 0);

ALTER TABLE kurasi.aduan
  DROP CONSTRAINT IF EXISTS aduan_pertanyaan_isi,
  DROP CONSTRAINT IF EXISTS aduan_tanpa_id_pesan,
  DROP CONSTRAINT IF EXISTS aduan_alasan_berisi;
ALTER TABLE kurasi.aduan
  ADD CONSTRAINT aduan_pertanyaan_isi CHECK (char_length(btrim(pertanyaan)) > 0),
  -- R-06: `id_pesan` ikut pada `answer_rated`; salinan yang memuatnya dapat
  -- ditautkan ke pseudonim oleh pemegang ekspor analitik.
  ADD CONSTRAINT aduan_tanpa_id_pesan
    CHECK (jsonb_typeof(tanggapan) = 'object' AND NOT tanggapan ? 'id_pesan'),
  ADD CONSTRAINT aduan_alasan_berisi CHECK (alasan IS NULL OR char_length(btrim(alasan)) > 0);

ALTER TABLE kurasi.tindak_lanjut_aduan
  DROP CONSTRAINT IF EXISTS tindak_lanjut_nilai,
  DROP CONSTRAINT IF EXISTS tindak_lanjut_catatan_isi,
  DROP CONSTRAINT IF EXISTS tindak_lanjut_peran,
  DROP CONSTRAINT IF EXISTS tindak_lanjut_pola_kurator;
ALTER TABLE kurasi.tindak_lanjut_aduan
  ADD CONSTRAINT tindak_lanjut_nilai CHECK (tindak_lanjut IN
    ('sumber_diajukan', 'butir_ditarik', 'jawaban_sesuai_dasar', 'di_luar_cakupan')),
  ADD CONSTRAINT tindak_lanjut_catatan_isi CHECK (char_length(btrim(catatan)) > 0),
  ADD CONSTRAINT tindak_lanjut_peran CHECK (peran IN ('kurator', 'kurator_pengganti')),
  ADD CONSTRAINT tindak_lanjut_pola_kurator CHECK (pseudonim_kurator ~ '^psd_[a-z]{16}$');

REVOKE ALL ON riwayat.pesan, riwayat.penilaian,
  kurasi.aduan, kurasi.aduan_digantikan, kurasi.tindak_lanjut_aduan FROM PUBLIC;

-- Penulis riwayat: menambah tanggapan dalam pernyataan yang sama dengan
-- giliran. Tanpa SELECT — lihat C-07 di atas.
GRANT INSERT ON riwayat.pesan TO peran_riwayat;

-- Penilai: memeriksa pemilik, menyalin pertanyaan dan tanggapan ke aduan bila
-- dikirim, dan menggugurkan aduan terdahulu atas pesan yang sama.
GRANT USAGE ON SCHEMA riwayat, kurasi TO peran_penilaian;
GRANT SELECT (id_percakapan, pemilik) ON riwayat.percakapan TO peran_penilaian;
GRANT SELECT (id_pesan, pertanyaan) ON riwayat.giliran TO peran_penilaian;
GRANT SELECT (id_pesan, id_percakapan, tanggapan) ON riwayat.pesan TO peran_penilaian;
GRANT SELECT (nomor, id_pesan) ON riwayat.penilaian TO peran_penilaian;
GRANT INSERT ON riwayat.penilaian TO peran_penilaian;
GRANT SELECT (nomor, nomor_penilaian) ON kurasi.aduan TO peran_penilaian;
GRANT INSERT ON kurasi.aduan, kurasi.aduan_digantikan TO peran_penilaian;

-- Kurator: salinan aduan tanpa tautannya, penanda gugur, dan tindak lanjut.
GRANT SELECT (nomor, pertanyaan, tanggapan, alasan, diadukan_pada) ON kurasi.aduan TO peran_kurasi;
GRANT SELECT ON kurasi.aduan_digantikan TO peran_kurasi;
GRANT SELECT, INSERT ON kurasi.tindak_lanjut_aduan TO peran_kurasi;

-- Penarikan data (NFR-09): kolom penaut saja, lalu hapus.
GRANT USAGE ON SCHEMA kurasi TO peran_penarikan;
GRANT SELECT (id_pesan, id_percakapan) ON riwayat.pesan TO peran_penarikan;
GRANT SELECT (nomor, id_pesan) ON riwayat.penilaian TO peran_penarikan;
GRANT SELECT (nomor, nomor_penilaian) ON kurasi.aduan TO peran_penarikan;
GRANT SELECT (nomor_aduan) ON kurasi.aduan_digantikan, kurasi.tindak_lanjut_aduan TO peran_penarikan;
GRANT DELETE ON riwayat.pesan, riwayat.penilaian,
  kurasi.aduan, kurasi.aduan_digantikan, kurasi.tindak_lanjut_aduan
  TO peran_penarikan;
