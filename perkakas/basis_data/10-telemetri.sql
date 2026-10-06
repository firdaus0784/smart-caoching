-- Fitur 034 · Penyimpanan telemetri — jalankan sebagai superuser pada basis data
-- `smart_coaching`, sesudah 01 s.d. 09.
--
-- Bentuk tabel D-04 Bagian 7.4 dan D-14 Bagian 5.1 (versi 0.13).
--
-- Yang ditegakkan PELADEN (plan Bagian 4):
--
--   Tambah-saja     Tidak satu peran pun memegang UPDATE, DELETE, atau TRUNCATE.
--                   Peristiwa yang dapat diubah sesudah terekam tidak
--                   membuktikan apa pun tentang apa yang terjadi (R-07 fitur 012).
--   C-05            Pemilik berpola pseudonim akun; `peran_telemetri` tanpa
--                   CONNECT ke basis data pseudonim.
--   FR-J01          Dua puluh kode taksonomi D-01 Bagian 9, sama dengan
--                   `JenisPeristiwa` — dijaga uji, bukan kepercayaan.
--
-- C-04 TIDAK ditegakkan di sini: persetujuan dibaca gerbang `rekam()` pada
-- setiap peristiwa. Peladen menjaga apa yang tersimpan, bukan siapa yang boleh.

CREATE SCHEMA IF NOT EXISTS telemetri;
REVOKE ALL ON SCHEMA telemetri FROM PUBLIC;

CREATE TABLE IF NOT EXISTS telemetri.peristiwa (
  nomor          bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pseudonim      text        NOT NULL,
  jenis          text        NOT NULL,
  waktu          timestamptz NOT NULL,
  properti       jsonb       NOT NULL,
  versi_aplikasi text        NOT NULL CHECK (char_length(btrim(versi_aplikasi)) > 0),
  versi_model    text        NOT NULL CHECK (char_length(btrim(versi_model)) > 0)
);

CREATE INDEX IF NOT EXISTS peristiwa_pemilik_jenis
  ON telemetri.peristiwa (pseudonim, jenis, waktu DESC);

-- Dipasang ulang tiap kali berkas ini dijalankan — pelajaran KB-158.
ALTER TABLE telemetri.peristiwa DROP CONSTRAINT IF EXISTS peristiwa_pola_pemilik;
ALTER TABLE telemetri.peristiwa
  ADD CONSTRAINT peristiwa_pola_pemilik CHECK (pseudonim ~ '^psd_[a-z]{16}$');
ALTER TABLE telemetri.peristiwa DROP CONSTRAINT IF EXISTS peristiwa_jenis_taksonomi;
ALTER TABLE telemetri.peristiwa
  ADD CONSTRAINT peristiwa_jenis_taksonomi CHECK (jenis IN (
    'session_start',
    'session_end',
    'question_asked',
    'answer_served',
    'answer_rejected_validator',
    'injection_suspected',
    'answer_rated',
    'citation_opened',
    'discovery_served',
    'discovery_opened',
    'discovery_read_complete',
    'discovery_dismissed',
    'discovery_saved',
    'knowledge_check_started',
    'knowledge_check_completed',
    'commitment_created',
    'commitment_status_updated',
    'return_visit',
    'search_performed',
    'export_performed'
  ));

REVOKE ALL ON telemetri.peristiwa FROM PUBLIC;

GRANT USAGE ON SCHEMA telemetri TO peran_telemetri;
GRANT SELECT, INSERT ON telemetri.peristiwa TO peran_telemetri;
