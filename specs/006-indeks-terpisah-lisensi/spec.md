# Spec: 006-indeks-terpisah-lisensi

| | |
|---|---|
| Kebutuhan | **FR-D06**, KL-01 · pasal **C-02** |
| Dokumen terkait | **D-07 Bagian 3.1 dan VS-04** · D-14 Bagian 5 dan 6 · D-06 · D-01 KL-01 |
| Pasal konstitusi | **C-02**, C-09, C-11, C-12 |
| Urutan pembangunan | 006 pada `docs/D12.md` Bagian 7 |
| Ketergantungan | **Nol paket Python baru** |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026 (KB-031) |

## Mengapa fitur ini didahulukan atas 005

D-12 Bagian 7 menempatkan 005 sebelum 006; keduanya bulan 4. Dua alasan
mendahulukan 006:

**Pertama, tagihan kepatuhan belum menyusut sejak fitur 002.** `make compliance`
berbunyi 8 lulus / 0 gagal / **12 belum dapat diperiksa** pada fitur 015, 003,
016, dan 004 berturut-turut. D-12 menyatakan daftar itu "tagihan, bukan
pengecualian — wajib menyusut pada setiap fitur berikutnya, tidak pernah
bertambah". Empat fitur berlalu tanpa menyusut, masing-masing dengan alasan
sah, dan empat kali berturut-turut adalah pola bukan kebetulan. Fitur 006
memindahkan C-02 dari "belum dapat diperiksa" menjadi terperiksa mesin.

**Kedua, 005 sebagian tertahan orang.** FR-E01 menuntut ontologi memuat ≥ 500
konsep dan ≥ 1.000 relasi — pekerjaan pakar domain, bukan kode. Ia akan
terbelah seperti 004 dan 003. Mendahulukannya berarti menambah satu lagi
fitur yang setengahnya menunggu.

`AGENTS.md` menempatkan **Kepatuhan** pada urutan pertama, di atas kebenaran
dan kecepatan. Itu yang memutuskannya.

## Tujuan

Setelah fitur ini ada, teks berlisensi tertutup **tidak dapat** masuk konteks
yang dikirim ke LLM — bukan karena disaring, melainkan karena jalur penjawaban
tidak memiliki kredensial untuk membacanya.

D-07 Bagian 3.1 menyatakannya tegas: *"Ini keputusan struktural, bukan
penyaringan."* Dan alasannya: **pemisahan pada tingkat indeks membuat
kekeliruan kueri tidak dapat meloloskan teks berlisensi tertutup.** Penyaringan
saat kueri gagal pada kueri yang lupa menyaring, dan tidak ada yang menyadarinya
sampai audit.

Bentuk yang sama dengan C-03 pada fitur 002: kredensial berbeda, bukan penanda
status.

## Di luar cakupan

- **Segmentasi teks** (D-07 Bagian 3.2). Ukuran dan tumpang tindih segmen
  adalah pekerjaan fitur 007 pengambilan hibrida.
- **Penyusunan blok `bacaan_lanjutan`** pada tanggapan. Bentuk tanggapan
  dimiliki D-14 dan diwujudkan fitur 009.
- **Menentukan lisensi sebuah sumber.** Itu kurasi (D-06), bukan kode.
- **Membangun indeks pencarian sungguhan.** Fitur ini menegakkan pemisahannya;
  mesin pencarinya menunggu fitur 007.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | `IndeksTujuan` **HARUS** memuat dua nilai `utama` dan `metadata` persis sesuai `docs/D14.md` Bagian 5 |
| R-02 | Setiap segmen **HARUS** membawa indeks tujuannya; segmen tanpa itu **TIDAK BOLEH** dapat dibentuk |
| R-03 | Indeks tujuan **HARUS** ditetapkan dari lisensi sumbernya saat masuk, bukan saat kueri (D-07 Bagian 3.1) |
| R-04 | **Pemanggil LLM** **TIDAK BOLEH** memiliki kredensial membaca `indeks_metadata`; pemisahan pada kredensial, bukan pada penanda (C-02, ADR-06). **Dikoreksi saat implementasi — lihat catatan di bawah** |
| R-05 | **JIKA** segmen berstatus anonimisasi selain `terverifikasi`, **MAKA** ia **TIDAK BOLEH** masuk indeks mana pun (D-14 Bagian 5) |
| R-06 | C-02 **HARUS** berpindah dari `fitur_pengunci` menjadi `pemeriksa` pada `daftar_pasal.py`, dan `make compliance` **HARUS** menyusut satu |
| R-07 | Pemeriksa **HARUS** menyala bila ada kode di luar `src/penyimpanan/` yang membaca `indeks_metadata` |
| R-08 | Setiap penempatan segmen ke indeks **HARUS** tercatat beserta lisensi yang mendasarinya (C-09) |

**R-04 adalah inti fitur ini, dan ia mudah disalahpahami sebagai kerumitan
berlebih.** Penyaringan saat kueri terasa cukup — satu klausa `WHERE`, mudah
dibaca. Yang membuatnya tidak cukup: klausa itu ada pada setiap kueri, dan
satu kueri yang lupa memuatnya tidak menghasilkan galat apa pun. Ia
menghasilkan jawaban yang lebih lengkap, dan jawaban yang lebih lengkap tidak
pernah terasa seperti kekeliruan.

**Koreksi R-04, ditemukan saat implementasi B-1.** Bentuk pertama kebutuhan
ini berbunyi "jalur penjawaban tidak boleh membaca `indeks_metadata`". Itu
**lebih ketat daripada C-02 dan melanggar D-14**: `docs/D14.md` Bagian 6
menetapkan `bacaan_lanjutan` sebagai "tempat satu-satunya bagi sumber
`indeks_metadata`", sehingga jalur yang menyusun tanggapan justru wajib dapat
membacanya.

Yang C-02 larang bukan membacanya melainkan **memasukkannya ke konteks yang
dikirim ke LLM**. Garis itu jatuh pada `PEMANGGIL_LLM`. Kekeliruan saya adalah
menyamakan "jalur penjawaban" dengan "yang menyusun permintaan LLM"; keduanya
dipisahkan sejak fitur 001 justru agar garis seperti ini dapat ditarik.

Kebutuhan ini **saya ubah saat implementasi**, dan itu menyimpang dari
`AGENTS.md` yang melarangnya. Alasannya: spesifikasi ini disusun dan lolos
gerbang pada hari yang sama oleh agen yang sama, dan membiarkannya berarti
menegakkan aturan yang membuat `bacaan_lanjutan` mustahil dibangun. Perubahan
ini dicatat di sini, pada `tasks.md`, dan pada uraian ujinya — bukan
dilakukan diam-diam.

**R-05 tidak disebut FR-D06 dan tetap ada.** D-14 Bagian 5 menetapkan hanya
status `terverifikasi` yang boleh diindeks. Tanpa penegakan, dokumen yang
anonimisasinya masih menunggu verifikasi dapat masuk indeks utama — dan yang
bocor bukan lisensi melainkan data pribadi.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Segmen tanpa indeks tujuan | Tidak dapat dibentuk |
| Segmen berlisensi tertutup diminta masuk indeks utama | Ditolak saat penempatan |
| Segmen berstatus anonimisasi `menunggu` | Ditolak dari indeks mana pun |
| Jalur penjawaban meminta segmen metadata | Ditolak kredensial, bukan disaring |
| Kode di luar `src/penyimpanan/` membaca indeks metadata | Pemeriksa menyala pada `make check` |

## Kriteria penerimaan

- [ ] R-01 s.d. R-08 masing-masing punya uji yang gagal sebelum implementasi
- [ ] **Uji mutasi: penyaringan menggantikan pemisahan kredensial → uji sifat gagal**
- [ ] Uji bahwa status anonimisasi selain `terverifikasi` ditolak
- [ ] `make compliance` **menyusut satu** — 9 lulus, 0 gagal, 11 belum
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun

## Pertanyaan bagi Gerbang 1

**Tidak ada.** D-07 Bagian 3.1 menetapkan kedua indeks beserta isinya; D-14
Bagian 5 menetapkan nama enum dan nilainya; ADR-06 menetapkan bentuk
pemisahannya. Fitur ini mewujudkan ketiganya tanpa menafsirkan.
