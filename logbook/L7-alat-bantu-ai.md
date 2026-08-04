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
