# Spec: 005-ontologi-skema-dan-ekspor

| | |
|---|---|
| Kebutuhan | **FR-E02, FR-E03, FR-E05** · FR-E01 dan FR-E04 dipisahkan ke fitur 018 |
| Dokumen terkait | **D-06 Bagian 11** · D-04 Bagian 7.3 · D-01 Modul E, MK-06 · D-08 Bagian 4.4 |
| Pasal konstitusi | C-03, C-09, C-11, C-12 |
| Urutan pembangunan | 005 pada `docs/D12.md` Bagian 7 |
| Ketergantungan | **Nol paket Python baru** |
| Status | Menunggu Gerbang 1 |

## Mengapa fitur ini dipisah

FR-E01 menuntut ontologi memuat **≥ 500 konsep dan ≥ 1.000 relasi**. Itu
pekerjaan pakar domain di atas bahan terkurasi, bukan kode — dan bahan
terkuranya sendiri belum ada, sebab kurasi menunggu fitur 010.

D-06 Bagian 11.1 menamai kekosongan yang sesungguhnya, dan bukan jumlahnya:

> Yang tidak pernah ada: **cara mengerjakannya, dan pemeriksaan apakah ia
> dapat dikerjakan**. Ini pola TK-29 dan TK-41 yang berulang untuk ketiga
> kalinya — perilaku diwajibkan, target ditetapkan, tanpa ada yang menghitung
> bebannya.

Yang dapat dikerjakan sekarang adalah **aturan yang membuat angka 500 berarti
sesuatu**. D-06 Bagian 11.2 menuliskannya, dan tanpa penegakannya target itu
dapat dipenuhi dengan konsep yang tidak berguna.

| | Bagian | Menunggu orang? |
|---|---|---|
| **1** | Skema konsep dan relasi, aturan hitung sah, ekspor JSON-LD | **Tidak** |
| **2** | Mengisi 500 konsep dan 1.000 relasi; antarmuka graf | **Ya** |

Bagian 2 diusulkan menjadi **fitur 018**.

## Tujuan

Setelah fitur ini ada, **angka MK-06 tidak dapat dipenuhi dengan konsep
kosong.** Konsep tanpa definisi tidak terhitung; konsep tanpa dokumen sumber
tidak terhitung; relasi berjenis di luar tujuh jenis FR-E02 tidak terbentuk.

D-06 Bagian 11.2 menyatakan alasannya dalam satu kalimat: *"Tanpa aturan ini,
target 500 dapat dipenuhi dengan konsep yang tidak berguna, dan angka MK-06
menjadi angka tanpa isi."*

## Di luar cakupan

- **Mengisi ontologinya.** Pekerjaan pakar domain (fitur 018).
- **Antarmuka graf** (FR-E04, prioritas S). Menunggu layar D-05.
- **Pemeriksaan duplikat.** D-06 Bagian 11.2 menyatakannya **pekerjaan
  manusia** pada audit graf D-08 Bagian 4.4. Menebaknya dengan kesamaan untai
  akan menyatukan dua konsep yang definisinya kebetulan mirip.
- **Menetapkan target 500/1.000.** Dimiliki MK-06.
- **Ekspor OWL/RDF penuh.** D-01 Bagian 12.2 memilih JSON-LD sebagai bentuk
  utama; OWL menyusul bila penerbit menuntutnya.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | `JenisRelasi` **HARUS** memuat tujuh jenis FR-E02 persis, sebagai tipe |
| R-02 | Konsep **HARUS** membawa label, definisi, dan sekurang-kurangnya satu dokumen sumber (FR-E03, D-06 Bagian 11.2) |
| R-03 | **JIKA** definisi konsep kosong, **MAKA** konsep itu **TIDAK BOLEH** terhitung sah |
| R-04 | Relasi **HARUS** membawa dokumen rujukannya sendiri, bukan mewarisi dari konsepnya |
| R-05 | Relasi **TIDAK BOLEH** menunjuk konsep yang tidak ada |
| R-06 | Konsep yang bersumber dari bahan **karantina** **TIDAK BOLEH** terhitung sah (C-03) |
| R-07 | Penghitungan **HARUS** melaporkan jumlah sah **dan** jumlah mentah secara terpisah |
| R-08 | Ekspor **HARUS** berbentuk JSON-LD sah dengan konteks yang menamai ketujuh jenis relasi (FR-E05) |
| R-09 | Ekspor **HARUS** memuat hanya konsep dan relasi yang sah |
| R-10 | Setiap ekspor **HARUS** tercatat beserta jumlah sah dan mentahnya (C-09) |

**R-07 adalah kebutuhan terpenting fitur ini, dan ia tentang cara melapor
bukan cara menghitung.** Laporan yang hanya menyebut "512 konsep" tidak dapat
dibedakan antara 512 konsep berdefinisi dan 512 baris tabel. Melaporkan
keduanya membuat selisihnya terbaca — dan selisih itulah yang memberi tahu
berapa banyak pekerjaan yang tersisa.

Bentuk yang sama dengan `terperiksa` pada pemeriksa ketergantungan sistem
fitur 015, `terhitung` pada kesepakatan fitur 003, dan `bendera_terkumpul`
fitur 016.

**R-06 adalah C-03 yang merambat ke tempat yang tidak terduga.** Konsep yang
diturunkan dari dokumen karantina membawa isinya ke ontologi — dan ontologi
diekspor untuk HKI dan publikasi. Dokumen yang belum diverifikasi anonimisasinya
lolos ke berkas yang dilampirkan naskah.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Konsep tanpa definisi | Terbentuk, **tidak terhitung sah**, dan dilaporkan |
| Konsep tanpa dokumen sumber | Tidak dapat dibentuk |
| Relasi menunjuk konsep yang tidak ada | Ditolak |
| Relasi tanpa dokumen rujukan | Tidak dapat dibentuk |
| Konsep bersumber dari karantina | Tidak terhitung sah |
| Jenis relasi di luar tujuh | Tidak dapat dibentuk |
| Ontologi kosong saat diekspor | Ditolak; ekspor kosong terbaca seperti ekspor yang gagal diam |

Baris pertama sengaja **terbentuk tetapi tidak terhitung**, bukan ditolak.
Konsep yang masih disusun definisinya adalah keadaan kerja yang wajar; yang
tidak boleh adalah ia ikut terhitung pada angka MK-06.

## Kriteria penerimaan

- [ ] R-01 s.d. R-10 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa konsep tanpa definisi tidak terhitung (R-03)
- [ ] Uji bahwa konsep dari karantina tidak terhitung (R-06)
- [ ] **Uji bahwa jumlah sah dan mentah dilaporkan terpisah** (R-07)
- [ ] Uji bahwa JSON-LD hasil ekspor dapat diurai dan memuat konteksnya
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun
- [ ] `make compliance` tidak berubah — 9 lulus, 0 gagal, 11 belum

## Pertanyaan bagi Gerbang 1

**Tidak ada.** D-06 Bagian 11.2 menetapkan aturan hitungnya, FR-E02 menetapkan
ketujuh jenis relasi, D-04 Bagian 7.3 menetapkan bidangnya, dan D-01 Bagian
12.2 memilih JSON-LD. Fitur ini mewujudkan keempatnya tanpa menafsirkan.
