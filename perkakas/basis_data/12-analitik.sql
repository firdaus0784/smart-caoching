-- Fitur 035 · Analitik penelitian — jalankan sebagai superuser pada basis data
-- `smart_coaching`, sesudah 01 s.d. 11.
--
-- Bentuk tabel D-14 Bagian 5.1 (versi 0.16); rancangan `plan.md` fitur 035
-- Bagian 2.
--
-- Yang ditegakkan PELADEN:
--
--   C-05            `peran_analitik` membaca peristiwa saja — tanpa akun,
--                   profil, riwayat, maupun basis data pseudonim. Pemegang
--                   ekspor tidak dapat menautkan pseudonim ke akun.
--   Tambah-saja     Catatan ekspor tidak dapat diubah maupun dihapus siapa pun:
--                   ia jejak ke mana data pergi.
--   P-4 fitur 035   `peran_penarikan` membaca rentang ekspor dan waktu
--                   peristiwa, agar perkakas penarikan dapat menyebut ekspor
--                   yang mungkin memuat data peserta yang menarik datanya.

CREATE TABLE IF NOT EXISTS telemetri.ekspor (
  nomor                  bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  peneliti               text        NOT NULL,
  diekspor_pada          timestamptz NOT NULL,
  dari                   date        NOT NULL,
  sampai                 date        NOT NULL,
  termasuk_pengembangan  boolean     NOT NULL,
  jumlah_baris           integer     NOT NULL
);

-- Dipasang ulang tiap kali berkas dijalankan (KB-158).
ALTER TABLE telemetri.ekspor
  DROP CONSTRAINT IF EXISTS ekspor_pola_peneliti,
  DROP CONSTRAINT IF EXISTS ekspor_rentang,
  DROP CONSTRAINT IF EXISTS ekspor_jumlah;
ALTER TABLE telemetri.ekspor
  ADD CONSTRAINT ekspor_pola_peneliti CHECK (peneliti ~ '^psd_[a-z]{16}$'),
  ADD CONSTRAINT ekspor_rentang CHECK (dari <= sampai),
  ADD CONSTRAINT ekspor_jumlah CHECK (jumlah_baris >= 0);

REVOKE ALL ON telemetri.ekspor FROM PUBLIC;

GRANT USAGE ON SCHEMA telemetri TO peran_analitik;
GRANT SELECT ON telemetri.peristiwa TO peran_analitik;
GRANT SELECT, INSERT ON telemetri.ekspor TO peran_analitik;

GRANT SELECT (waktu) ON telemetri.peristiwa TO peran_penarikan;
GRANT SELECT (nomor, diekspor_pada, dari, sampai) ON telemetri.ekspor TO peran_penarikan;
