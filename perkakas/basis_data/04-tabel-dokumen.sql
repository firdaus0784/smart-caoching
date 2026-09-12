-- T-3 fitur 024 · Tabel dokumen — jalankan sebagai superuser pada `smart_coaching`,
-- sesudah 02-skema-dan-hak.sql.
--
-- Satu tabel per area, bukan satu tabel dengan kolom `area_simpan`.
--
-- D-14 Bagian 5.1 menyebut `dokumen_sumber.area_simpan` bernilai `karantina`
-- atau `korpus`, dan ADR-06 menegaskan **kredensial berbeda, bukan sekadar
-- penanda**. Kolom penanda pada satu tabel tidak dapat dijaga peladen: hak
-- akses PostgreSQL berlaku pada tabel dan skema, bukan pada nilai baris.
--
-- Memisahkan tabel per skema membuat `area_simpan` **terbaca dari tempatnya**
-- alih-alih dari isinya, dan itu yang membuat C-03 ditolak peladen.
--
-- Kolom `isi` berbentuk JSONB mengikuti bentuk yang `PenyimpanTiruan` terima.
--
-- `IF NOT EXISTS` agar berkas ini dapat dijalankan berulang. Penyiapan yang
-- hanya boleh dijalankan sekali adalah penyiapan yang gagal pada percobaan
-- kedua, dan percobaan kedua selalu terjadi.

CREATE TABLE IF NOT EXISTS karantina.dokumen_sumber (
    id          text PRIMARY KEY,
    isi         jsonb NOT NULL,
    disimpan_pada timestamptz NOT NULL DEFAULT now()  -- KM-01: seluruh waktu UTC
);

CREATE TABLE IF NOT EXISTS korpus.dokumen_sumber (
    id          text PRIMARY KEY,
    isi         jsonb NOT NULL,
    disimpan_pada timestamptz NOT NULL DEFAULT now()
);
