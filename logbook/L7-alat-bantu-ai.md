# L7 · Catatan Penggunaan Alat Bantu AI

Mengikat ET-10 pada `docs/D01.md`, `docs/D10.md` Bagian 9, dan `docs/D12.md`
Bagian 8. Sebagian besar jurnal terindeks kini mensyaratkan pengungkapan ini,
dan menyusunnya di akhir menghasilkan pernyataan yang tidak akurat.

Tiga hal yang wajib tercatat dan paling mudah terlewat:

- **Pra-anotasi otomatis** (FR-C10, BT-13) — ia menimbulkan risiko *automation
  bias* pada anotator, dan itu memengaruhi tafsir angka kesepakatan yang
  dilaporkan
- **Gerbang yang dilewati dengan pengecualian** beserta alasan dan pemberi
  izinnya (`docs/D12.md` Bagian 8)
- **Cacat yang berasal dari kode hasil agen**, untuk pelaporan jujur

Pembedaan yang perlu dijaga: LLM pada jalur penjawaban (ADR-02) adalah
**objek penelitian**, bukan alat bantu penulisan. Keduanya tetap dicatat,
tetapi tidak boleh tertukar dalam naskah.

**Ditambah, tidak disunting.** Lihat `AGENTS.md` bagian Batas.

## Bentuk entri

Setiap entri berupa judul `## AI-nnn · ringkas` diikuti tabel lima bidang
wajib: Tanggal, Jenis penggunaan, Uraian, Verifikasi manusia, Pemberi izin.
Bidang Pemberi izin diisi `tidak berlaku` bila entri bukan pengecualian
gerbang — dikosongkan bukan pilihan yang sah.

<!-- Entri dimulai di bawah baris ini. -->

## AI-001 · Pengecualian Gerbang 4 untuk fitur 001

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Jenis penggunaan | Gerbang yang dilewati dengan pengecualian (`docs/D12.md` Bagian 8) |
| Uraian | Daftar Selesai `AGENTS.md` mensyaratkan `make check` lulus. Fitur 001 justru yang membuat `make check`, sehingga ia tidak dapat diverifikasi oleh keluarannya sendiri. Gerbang 4 fitur 001 dijalankan manusia terhadap daftar periksa eksplisit G4-01 s.d. G4-25 pada `tasks.md`, ditulis **sebelum** implementasi dimulai. Berlaku hanya untuk fitur 001, bukan "sampai infrastruktur siap". `make check` dan `make compliance` yang berfungsi adalah bagian luaran fitur ini; bila belum ada di akhir, fitur belum selesai. |
| Verifikasi manusia | Pemegang Gerbang 1–4 memeriksa G4-01 s.d. G4-25 secara langsung. G4-02, G4-07, dan G4-14 disyaratkan dibuktikan, bukan dinyatakan. |
| Pemberi izin | Pemegang Gerbang 1–4 (KB-001), pada Gerbang 3 fitur 001 |

## AI-002 · Penggunaan agen pada pembangunan fitur 001

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Jenis penggunaan | Penggunaan pada proses penelitian — pembangunan perangkat lunak |
| Uraian | Seluruh kode fitur 001 disusun agen mengikuti alur SDD `docs/D12.md`: `spec.md`, `plan.md`, dan `tasks.md` ditinjau manusia berturut-turut sebelum kode ditulis. Satu tugas satu commit, uji ditulis lebih dulu. Perkiraan porsi kode yang dihasilkan agen pada fitur ini: seluruhnya, dengan spesifikasi dan keputusan gerbang berasal dari manusia. Cacat yang berasal dari kode hasil agen dicatat pada uraian commit masing-masing; enam di antaranya ditemukan oleh gerbang dan uji yang dibangun agen itu sendiri pada tugas sebelumnya. |
| Verifikasi manusia | Empat gerbang `docs/D12.md` Bagian 3, ditambah daftar periksa G4-01 s.d. G4-25. Bukti kegagalan uji sebelum implementasi tersimpan pada badan pesan commit, sehingga dapat diperiksa dari riwayat git. |
| Pemberi izin | tidak berlaku |
