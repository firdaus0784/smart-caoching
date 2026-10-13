-- Fitur 039 · Tautan sumber asli — jalankan sebagai superuser pada basis data
-- `smart_coaching`, sesudah 01 s.d. 16.
--
-- Bentuk D-14 Bagian 5.1 (versi 0.22); rancangan `plan.md` fitur 039 Bagian 2.
--
-- Yang ditegakkan PELADEN:
--
--   P-5 A, KL-04    Tautan ke halaman sumber asli, dicatat saat menerima pada
--                   penerimaan dan catatan metadata korpus. Boleh kosong;
--                   bila berisi, `http` atau `https` tanpa spasi.
--
-- Tanpa hak baru: penerimaan disisipkan `peran_ingesti` dan catatan metadata
-- `peran_verifikasi`, keduanya dengan hak sisip per tabel (fitur 037, 032),
-- dan pembaca keduanya membaca per tabel. Uji katalog yang membuktikannya,
-- bukan anggapan ini.

ALTER TABLE karantina.penerimaan ADD COLUMN IF NOT EXISTS tautan text NULL;
ALTER TABLE korpus.metadata_dokumen ADD COLUMN IF NOT EXISTS tautan text NULL;

-- `coalesce`: CHECK lulus bila hasilnya NULL, dan NULL memang sah di sini.
ALTER TABLE karantina.penerimaan DROP CONSTRAINT IF EXISTS penerimaan_tautan;
ALTER TABLE karantina.penerimaan ADD CONSTRAINT penerimaan_tautan
  CHECK (tautan IS NULL OR coalesce(tautan ~ '^https?://[^[:space:]]+$', false));
ALTER TABLE korpus.metadata_dokumen DROP CONSTRAINT IF EXISTS metadata_tautan;
ALTER TABLE korpus.metadata_dokumen ADD CONSTRAINT metadata_tautan
  CHECK (tautan IS NULL OR coalesce(tautan ~ '^https?://[^[:space:]]+$', false));
