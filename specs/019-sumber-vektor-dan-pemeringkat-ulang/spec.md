# Spec: 019-sumber-vektor-dan-pemeringkat-ulang

| | |
|---|---|
| Kebutuhan | ADR-03 sisi semantik, ADR-05, ADR-12; BT-30; C-02, C-09, C-12 |
| Dokumen terkait | D-04 ADR-03 dan ADR-05, D-07 Bagian 4.4 dan 4.6, D-08 Bagian 5, D-11 Bagian 3.4 |
| Status | **Gerbang 1 lolos** — 20 September 2026, nol pertanyaan terbuka. Menunggu Gerbang 2 |

## Tujuan

ADR-03 memutuskan pengambilan **hibrida**: leksikal dan semantik, lalu
diperingkat ulang. Sisi leksikalnya selesai pada fitur 007 — BM25 beserta
penggabungan Reciprocal Rank Fusion. **Sisi semantiknya belum ada sama
sekali**, sehingga `ambil_hibrida` hari ini berjalan dengan satu sumber dan
gagal tepat pada hal yang ADR-03 sebut sebagai alasannya: parafrase pengguna.

Fitur ini menambahkan **sumber vektor dan pemeringkat ulang**. Kalibrasi
ambang BT-29 dipecah menjadi fitur **025** atas keputusan Gerbang 1 — lihat
Keputusan Gerbang 1 nomor 2.

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

Pembagian ini bukan penundaan yang menumpuk utang: bagian yang dapat dibangun
adalah bagian yang membuat sisanya murah pada hari bahannya ada.

## Di luar cakupan

Disebutkan tegas beserta sebabnya. Yang tidak disebut sebabnya akan dikerjakan
seseorang karena mengira ia terlupa.

- **Melatih atau menyetel model penyemat.** Model praterlatih dipakai apa
  adanya; pelatihan adalah fitur 017 dan menuntut korpus teranotasi.
- **Kalibrasi ambang.** Seluruhnya milik fitur 025. C-16 melarang ambang
  disetel di luar prosedur BT-29, dan larangan itu berlaku terutama di sekitar
  fitur ini — sumber vektor yang sudah berjalan membuat ambang yang "kelihatan
  masuk akal" terasa satu langkah lagi dari sistem yang menjawab.
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

**R-07.** Fitur ini TIDAK BOLEH membentuk `AmbangKecukupan` maupun menyentuh
nilai ambang mana pun. Selesainya sumber vektor **tidak** mengubah keadaan
C-16: ketiadaan ambang tetap keadaan yang benar sampai fitur 025 dijalankan.

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

## Keputusan Gerbang 1

Diputus pemegang Gerbang 1–4 pada 20 September 2026. Dicatat pula pada KB-091.

**1 · `SumberKandidat.cari` menjadi asinkron.** Alasannya sejajar dengan
KB-085: sumber vektor menanyakan `pgvector` lewat `asyncpg`, dan jembatan
sinkron memaksa jalur asinkron → sinkron → asinkron yang memblokir gelung
peristiwanya sendiri. Keputusannya diambil **tersendiri** meski bentuknya sama
dengan `PenyimpanDasar`, sebab keputusan yang menyebar tanpa dicatat bukan
keputusan.

Ia mengubah kontrak yang `bm25.py`, `hibrida.py`, dan setiap pemanggilnya
pakai. Bila abstraksinya ternyata tidak pas sesudah sumber nyata pertama
menguji — sebagaimana ADR-12 perkirakan dan sebagaimana benar-benar terjadi
pada fitur 024 — penyesuaiannya melewati Gerbang 2 tersendiri.

**2 · Fitur dipecah dua.** **019** memuat sumber vektor dan pemeringkat ulang;
**025** memuat kalibrasi ambang BT-29. Sebabnya bukan besarnya melainkan **apa
yang menghalangi masing-masing**: 019 tertahan bobot model yang diunduh di
mesin penelitian, 025 tertahan gold set D-08 yang belum disusun — dua
penghalang berbeda dengan tenggat berbeda berbulan-bulan. `docs/D12.md`
Bagian 7 dan register D-00 sudah menyesuaikan; jumlah fitur menjadi 25.

**Pertanyaan nomor 4 pindah ke fitur 025.** Siapa mengunduh bobot dan di mana
versinya dipatok adalah pertanyaan yang hanya berlaku ketika penyemat
sungguhan dipakai, dan itu terjadi pada fitur 025.

**3 · Vektor disimpan sebagai kolom pada tabel di skema yang sudah ada.**
Bukan tabel tersendiri. Fitur 024 sudah menegakkan C-02 pada tingkat skema —
`peran_pemanggil_llm` tidak diberi `USAGE` atas `indeks_metadata` sama sekali,
sehingga pemisahannya ditolak peladen. Tabel tersendiri **tidak menambah
penjagaan apa pun** di atas itu; ia hanya menambah satu tempat lagi yang dapat
hanyut dari pasangannya.

R-04 karena itu terpenuhi oleh letak tabelnya, bukan oleh bentuk tabelnya —
dan letak itu sudah ada beserta hak aksesnya yang terbukti pada sepuluh arah
uji T-9 fitur 024.

## Ketertelusuran

| Kebutuhan | Diwujudkan |
|---|---|
| ADR-03 sisi semantik | R-01, R-02 |
| ADR-12 | R-02 |
| C-02, FR-D06 | R-03, R-04 |
| BT-30 | R-05 |
| C-09 | R-06 |
| C-16 | R-07 — lewat larangan, bukan lewat pembentukan |
| ADR-05 `pgvector` | R-04, R-08 |
| C-12 | Nol ketergantungan baru — `torch`, `transformers`, `sentence-transformers`, dan `pgvector` sudah pada berkas persetujuan (KB-083) |
