# Spec: 019-sumber-vektor-dan-kalibrasi

| | |
|---|---|
| Kebutuhan | ADR-03 sisi semantik, ADR-05, ADR-12; BT-29, BT-30; C-02, C-12, C-16 |
| Dokumen terkait | D-04 ADR-03 dan ADR-05, D-07 Bagian 4.4 dan 4.6, D-08 Bagian 5, D-11 Bagian 3.4 |
| Status | **Menunggu Gerbang 1** |

## Tujuan

ADR-03 memutuskan pengambilan **hibrida**: leksikal dan semantik, lalu
diperingkat ulang. Sisi leksikalnya selesai pada fitur 007 — BM25 beserta
penggabungan Reciprocal Rank Fusion. **Sisi semantiknya belum ada sama
sekali**, sehingga `ambil_hibrida` hari ini berjalan dengan satu sumber dan
gagal tepat pada hal yang ADR-03 sebut sebagai alasannya: parafrase pengguna.

Fitur ini menambahkan sumber vektor, pemeringkat ulang, dan — bila bahannya
tersedia — kalibrasi ambang BT-29.

## Bentuk yang sudah disiapkan fitur 007, dan mengapa itu penting

`SumberKandidat` sudah berupa antarmuka abstrak, dan `ambil_hibrida` sudah
menerima **urutan** sumber. Menambahkan sisi semantik karena itu **tidak
mengubah `ambil_hibrida` sama sekali** — ia satu pelaksana baru pada kontrak
yang sudah ada.

Itu ukuran keberhasilan fitur ini, bukan sekadar harapannya. Bila
`ambil_hibrida` ternyata perlu diubah, kontraknya yang salah — dan perubahan
itu melewati Gerbang 2 tersendiri, bukan dikerjakan sambil jalan.

## Apa yang dapat dibangun, dan apa yang tidak — dinyatakan di muka

Fitur ini **tidak dapat diselesaikan seluruhnya** pada siklus pengerjaan saat
ini, dan menyatakannya sekarang lebih murah daripada menemukannya di tengah.

| Bagian | Keadaan | Yang menghalangi |
|---|---|---|
| Sumber vektor beserta penyimpanan `pgvector` | **dapat dibangun** | — |
| Antarmuka penyemat beserta pelaksana tiruan deterministik | **dapat dibangun** | — |
| Pemeringkat ulang beserta jalur mundurnya | **dapat dibangun** | — |
| Penyemat sungguhan `intfloat/multilingual-e5-large-instruct` | **tertahan** | Bobot model tidak terjangkau dari lingkungan agen — permintaan ke HuggingFace ditolak proksi organisasi (403). Pengunduhan dilakukan pada mesin penelitian |
| Kalibrasi ambang BT-29 | **tertahan** | Menuntut *gold set* D-08 Bagian 5 yang **dibekukan sebelum kalibrasi**. Gold set belum disusun |

Pembagian ini bukan penundaan yang menumpuk utang: bagian yang dapat dibangun
adalah bagian yang membuat sisanya murah pada hari bahannya ada.

## Di luar cakupan

Disebutkan tegas beserta sebabnya. Yang tidak disebut sebabnya akan dikerjakan
seseorang karena mengira ia terlupa.

- **Melatih atau menyetel model penyemat.** Model praterlatih dipakai apa
  adanya; pelatihan adalah fitur 017 dan menuntut korpus teranotasi.
- **Menyetel ambang di luar prosedur BT-29.** C-16 melarangnya, dan larangan
  itu berlaku terutama pada fitur ini — di sinilah godaannya paling besar,
  sebab ambang yang "kelihatan masuk akal" akan membuat sistem menjawab.
- **Menyusun gold set.** Ia milik D-08, disusun tim substansi dari survei 50
  kepala sekolah, dan dibekukan sebelum kalibrasi. Agen yang menyusunnya
  menguji dirinya sendiri.
- **Mengubah `ambil_hibrida`.** Lihat bagian di atas.

## Kebutuhan (EARS)

**R-01.** Sistem WAJIB menyediakan `SumberVektor` yang memenuhi kontrak
`SumberKandidat` tanpa satu pun perubahan pada `ambil_hibrida`.

**R-02.** Penyematan WAJIB berada di balik antarmuka abstrak dengan pelaksana
tiruan deterministik, mengikuti ADR-12. Pelaksana sungguhan dipilih pemanggil.

**R-03.** KETIKA sumber vektor mencari, ia WAJIB memeriksa `indeks_tujuan`
terhadap kredensial **sebelum** kueri dijalankan — bentuk yang sama dengan
sumber BM25, sebab C-02 menolak penyaringan saat kueri.

**R-04.** Vektor segmen `indeks_metadata` WAJIB disimpan terpisah dari vektor
segmen `indeks_utama`, pada tingkat yang ditolak peladen — bukan pada kolom
penanda.

**R-05.** JIKA model pemeringkat ulang untuk Bahasa Indonesia tidak tersedia,
MAKA tahap 5 WAJIB memakai urutan hasil penggabungan apa adanya, dan
ketiadaannya WAJIB tercatat pada keluaran — bukan didiamkan (BT-30).

**R-06.** Penyemat WAJIB mencatat nama dan versi model pada setiap keluaran
yang dipakai membentuk indeks, mengikuti C-09.

**R-07.** SELAMA kalibrasi BT-29 belum dijalankan, sistem WAJIB **tetap
menolak** membentuk `AmbangKecukupan` — C-16 berlaku tanpa pengecualian, dan
ketiadaan ambang adalah keadaan yang benar, bukan cacat yang perlu ditambal.

**R-08.** Dimensi vektor dan ukuran jarak WAJIB dinyatakan satu tempat, dan
ketidakcocokan antara dimensi model dan dimensi kolom WAJIB tertangkap saat
penyusunan — bukan saat kueri pertama.

## Keadaan yang wajib ditangani

| Keadaan | Yang wajib terjadi |
|---|---|
| Model penyemat belum dipasang | Galat yang menyebut keadaannya; sistem tidak jatuh ke pencarian leksikal diam-diam |
| Dimensi vektor tidak cocok dengan kolom | Ditolak saat penyusunan |
| Segmen belum memiliki vektor | Tidak muncul sebagai kandidat; jumlahnya dilaporkan |
| Kredensial tidak menjangkau indeks | Sumber tidak dijalankan sama sekali |
| Pemeringkat ulang tidak tersedia | Urutan penggabungan dipakai, dan ketiadaannya tercatat |

## Pertanyaan yang wajib dijawab Gerbang 1

1. **`SumberKandidat.cari` menjadi asinkron?** Sumber vektor menanyakan
   `pgvector` lewat `asyncpg`, sedangkan `cari` hari ini sinkron. Ini
   **bentuk kekeliruan yang sama persis** dengan yang menghentikan T-3 fitur
   024, dan Gerbang 2 sudah memutuskannya untuk `PenyimpanDasar` (KB-085).
   Keputusan yang sama belum diambil untuk kontrak ini, dan mengambilnya
   diam-diam karena "sudah pernah diputuskan pada kontrak lain" adalah cara
   keputusan menyebar tanpa dicatat.

2. **Fitur ini dipecah dua atau tidak?** Bagian yang dapat dibangun dan bagian
   yang tertahan gold set berbeda tenggat berbulan-bulan. Satu fitur yang
   separuhnya menunggu akan tercatat "belum selesai" sepanjang itu, dan
   ketidakselesaiannya akan berhenti bermakna. **Pemecahan menuntut baris baru
   pada `docs/D12.md` Bagian 7**, dan itu keputusan tim.

3. **Vektor `indeks_metadata` disimpan di mana?** R-04 menuntut keterpisahan
   yang ditolak peladen. Fitur 024 sudah menyediakan skema `indeks_utama` dan
   `indeks_metadata` beserta hak aksesnya — pertanyaannya apakah kolom vektor
   cukup ditambahkan di sana, atau perlu tabel tersendiri. **Menentukan bentuk
   migrasi, dan tidak boleh diputuskan saat menulis kode.**

4. **Siapa menjalankan pengunduhan bobot model, dan hasilnya dipatok di mana?**
   Lingkungan agen tidak dapat menjangkau HuggingFace. Versi bobot yang dipakai
   wajib tercatat (C-09), dan pencatatan itu tidak dapat dilakukan oleh yang
   tidak mengunduhnya.

## Ketertelusuran

| Kebutuhan | Diwujudkan |
|---|---|
| ADR-03 sisi semantik | R-01, R-02 |
| ADR-12 | R-02 |
| C-02, FR-D06 | R-03, R-04 |
| BT-30 | R-05 |
| C-09 | R-06 |
| C-16, BT-29 | R-07 |
| ADR-05 `pgvector` | R-04, R-08 |
| C-12 | Nol ketergantungan baru — `torch`, `transformers`, `sentence-transformers`, dan `pgvector` sudah pada berkas persetujuan (KB-083) |
