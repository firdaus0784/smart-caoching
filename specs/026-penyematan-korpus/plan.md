# Plan: 026-penyematan-korpus

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 23 September 2026, nol pertanyaan terbuka (KB-109) |
| Status | **Menunggu Gerbang 2** |
| Kebutuhan | R-01 s.d. R-11 `spec.md`; C-02, C-03, C-09, C-12; TK-57, TK-60 |

## 1. Letak modul — diverifikasi dengan menjalankan pemeriksanya

```
src/ingest/penyematan.py                 (baru)  Jalur penyematan korpus
src/logbook/penulis.py                   (ubah)  Satu fungsi baru: tambah_versi_artefak
perkakas/basis_data/05-kolom-vektor.sql  (ubah)  Nama kolom + kolom versi
src/rag/pengambilan/vektor.py            (ubah)  Mengikuti nama kolom baru
```

`baca_arah()` dijalankan atas `AGENTS.md` hari ini, bukan dibaca kalimatnya:

```
ingest -> ['llm', 'nlp']
lapisan terbuka: ['kamus', 'llm', 'logbook', 'penyimpanan']
```

`src/ingest/` karena itu sudah boleh memanggil `llm` (penyemat), `penyimpanan`
(sambungan dan kredensial), `logbook` (pencatatan), dan `kamus` (`IndeksTujuan`).
**Nol tepi arah baru.** `AGENTS.md` tidak perlu diperbarui, dan bila ternyata
perlu, itu temuan — bukan tambahan yang dikerjakan sambil jalan.

## 2. Bentuk

```python
class HasilPenyematan(BaseModel):          # frozen, extra="forbid"
    indeks_tujuan: IndeksTujuan
    versi_indeks: str                      # dihasilkan, bukan diserahkan — K-2
    versi_penyemat: VersiPenyemat
    tersemat: int                          # baris yang ditulis
    dilewati_teks_kosong: int
    tersisa_tanpa_vektor: int              # sesudah jalan; nol berarti indeks penuh


async def sematkan_indeks(
    sambungan: SambunganAktif,
    *,
    penyemat: Penyemat,                    # R-04 — diserahkan pemanggil, wajib
    indeks_tujuan: IndeksTujuan,
    kredensial: Kredensial,
    sekarang: Callable[[], datetime],      # disuntikkan — lihat Bagian 4
) -> HasilPenyematan: ...
```

Tiga bidang hitungan, bukan satu. `tersemat` sendirian tidak dapat dibedakan
dari indeks yang sebagian segmennya dilewati karena bertext kosong, dan
pembedaan itu yang memberi tahu apakah korpusnya bermasalah atau jalurnya.

## 3. Urutan penjagaan, dan mengapa urutannya yang menentukan

| # | Penjagaan | Kebutuhan | Mengapa **sebelum** yang berikutnya |
|---|---|---|---|
| 1 | Kredensial menjangkau indeks sasaran | R-06, R-07, C-02, C-03 | Bentuk yang sama dengan `ambil_hibrida`: menyaring sesudah kueri berjalan menghasilkan daftar yang sama sambil barisnya sudah terbaca |
| 2 | Dimensi penyemat cocok dengan kolom | R-03 | Memakai ulang `pastikan_dimensi_cocok` fitur 019. Ditolak **sebelum satu baris pun ditulis**, bukan pada baris pertama yang gagal |
| 3 | Versi penyemat cocok dengan yang sudah ada pada indeks | R-09 | `SELECT DISTINCT versi_model_sematan WHERE NOT NULL`. Indeks bercampur dua model **tidak menghasilkan galat** — ia menghasilkan peringkat masuk akal yang salah |
| 4 | Baru membaca segmen ber-`vektor_sematan` NULL | R-01, R-08 | `WHERE ... IS NULL` yang membuat penjalanan ulang aman tanpa penanda apa pun |

Penjagaan 3 yang paling mudah ditulis terbalik: memeriksanya **sesudah**
menyemat akan menemukan percampuran setelah percampuran itu terjadi.

## 4. Waktu disuntikkan, tidak diambil dari jam

K-2 menetapkan versi indeks berupa cap waktu UTC. Fungsi yang memanggil
`datetime.now()` sendiri **tidak dapat diuji**: uji atas bentuk versinya akan
menghasilkan nilai berbeda tiap jalan, dan uji yang hanya memeriksa polanya
membuktikan pola, bukan nilai.

`sekarang` disuntikkan sebagai `Callable[[], datetime]`. Uji menyerahkan jam
tetap; pemanggil sungguhan menyerahkan `lambda: datetime.now(UTC)`. Bentuk
yang sama dengan `Penyemat` — pelaksana dipilih pemanggil (R-04), dan alasan
yang sejajar.

Penjagaan yang menyertainya: `datetime` tanpa zona waktu **ditolak**, KM-01.

## 5. Pencatatan L2 — bidangnya sudah ditetapkan D-10, bukan dipilih di sini

`docs/D10.md` Bagian 4 memuat dua baris yang berlaku tepat bagi fitur ini:

| Artefak | Yang dicatat |
|---|---|
| Model sematan | Nama dan versi |
| Indeks | Nomor versi, tanggal pembangunan, jumlah segmen, komposisi sumber |

`src/logbook/penulis.py` bertambah `tambah_versi_artefak`, sejajar
`tambah_percobaan` yang sudah ada bagi L1. Ia **bukan** `tambah_baris` telanjang:
`tambah_percobaan` menerima `Versi` bertipe justru agar kelima bidangnya tidak
luput karena lupa, dan alasan yang sama berlaku di sini.

Seluruh penulisan tetap lewat `src/logbook/` — C-09, tanpa pengecualian.

## 6. Penggantian nama kolom — blast radius **diukur**, bukan diperkirakan

`plan.md` fitur 019 dua kali menyatakan blast radius di bawah kenyataan
(KB-094: 3 berkas disebut, 6 tersentuh; KB-100: 1 disebut, 7 tersentuh).
Karena itu angka di bawah dihasilkan dengan menyapu repositori hari ini.

**Kolom `vektor` → `vektor_sematan`, dan kolom baru `versi_model_sematan`
(D-04 Bagian 7.2, TK-60): 4 berkas, 9 tempat.**

| Berkas | Tempat |
|---|---|
| `perkakas/basis_data/05-kolom-vektor.sql` | 2 — deklarasi pada kedua skema |
| `src/rag/pengambilan/vektor.py` | 5 — tetapan `KOLOM_VEKTOR`, dua untai SQL harfiah, dua pesan galat |
| `tests/rag/pengambilan/test_sumber_vektor.py` | 1 — daftar kolom pada INSERT |
| `tests/rag/pengambilan/test_kontrak_sumber.py` | 1 — daftar kolom pada INSERT |

### Jebakan yang ditemukan saat mengukur, dan wajib dibaca sebelum menyentuh

**(a) `"vektor"` berarti dua hal yang berbeda.** Selain nama kolom, ia nama
sumber yang `SumberVektor.nama` kembalikan, dan nama itu muncul pada **26
tempat** di tujuh berkas uji. Penggantian dengan sapuan seluruh berkas akan
merusak nama sumber, dan ujinya akan gagal pada tempat yang tidak ada
hubungannya dengan kolom. Bentuk yang sama dengan KB-088: sasaran mutasi yang
mengenai kelas yang salah.

**Cara yang dipakai:** ganti hanya pada konteks SQL, dan **nama sumber tidak
disentuh sama sekali**. Sesudahnya, sapuan `"vektor"` wajib masih menemukan 26
tempat itu utuh.

**(b) Dua untai SQL melewati tetapannya sendiri.** `vektor.py` memiliki
`KOLOM_VEKTOR`, tetapi baris 219 dan 222 menulis `vektor <=> $1::vector`
harfiah. Mengganti lewat tetapan saja akan meninggalkan keduanya menunjuk kolom
yang sudah tidak ada — dan keduanya baru gagal ketika kueri **dijalankan**,
bukan saat diimpor. Keduanya disatukan ke tetapan pada tugas yang sama.

## 7. Uji

### 7.1 Yang menuntut peladen

Seluruh jalur penyematan. `make check` sudah menuntut PostgreSQL sejak 12
September 2026, sehingga tidak ada jalur dilewati.

### 7.2 Yang tidak menuntut peladen

Bentuk `HasilPenyematan`, bentuk versi indeks, penolakan `datetime` tanpa zona,
dan penolakan penyemat yang tidak diserahkan.

### 7.3 Uji mutasi

| | Mutasi | Yang wajib menangkapnya |
|---|---|---|
| M-1 | Kredensial diperiksa sesudah baris dibaca | R-06, R-07, C-02, C-03 |
| M-2 | Dimensi dicocokkan sesudah penulisan dimulai | R-03 |
| M-3 | Versi penyemat tidak diperiksa terhadap isi indeks | **R-09** |
| M-4 | Penjalanan ulang menulis ulang vektor yang sudah ada | R-08 |
| M-5 | Segmen bertext kosong disemat menjadi vektor nol | Keadaan wajib |
| M-6 | `versi_model_sematan` tidak ditulis | R-02, TK-60 |
| M-7 | Versi indeks dikarang pemanggil, bukan dihasilkan | K-2 |
| M-8 | Baris L2 tidak ditulis | R-02, C-09 |
| M-9 | Penyemat disusun sendiri, bukan diserahkan | R-04 |
| **M-10** | **M-7 fitur 019** — versi penyemat tidak masuk keluaran | TK-57 — ia **tidak dapat dipasang** sebelum fitur ini; menyalanya adalah bukti temuannya tertutup |

Yang tidak menyala **tetap dilaporkan beserta sebabnya**. Bila sebuah mutasi
diam, yang pertama diperiksa adalah apakah mutasinya terlalu lemah (M-3 fitur
024), atau apakah di seluruh rangkaian uji hanya pernah ada satu nilai (M-8
fitur 019, KB-101).

## 8. Urutan tugas

| | Tugas | Mengapa di sini |
|---|---|---|
| T-1 | Penggantian nama kolom dan penambahan `versi_model_sematan` | **Mendahului seluruhnya.** Ia menyentuh fitur 019 yang sudah lolos Gerbang 4; menggabungkannya dengan kode baru membuat kegagalan tidak dapat ditelusuri ke perubahan yang mana — pelajaran T-2 fitur 024 dan T-1 fitur 019 |
| T-2 | `tambah_versi_artefak` pada `src/logbook/` | Tidak menyentuh basis data sama sekali, sehingga dapat berdiri sebelum jalurnya ada |
| T-3 | `HasilPenyematan` dan bentuk versi indeks | Murni bentuk; tanpa peladen |
| T-4 | `sematkan_indeks` beserta keempat penjagaan | Inti fitur |
| T-5 | R-08 dan R-09 — penjalanan ulang dan penolakan percampuran model | Dipisah dari T-4: keduanya sifat atas **dua** penjalanan, dan uji atas satu penjalanan tidak dapat menyatakannya |
| T-6 | Uji mutasi M-1 s.d. M-10, dilaporkan apa adanya | |
| T-7 | Menutup TK-57 dan TK-60; docstring `HasilSumber.versi_penyemat` diperbarui | Setengah R-06 yang dinyatakan terbuka di sana kini tertutup |

## 9. Yang menghentikan pekerjaan, bukan yang memperlambatnya

| Keadaan | Yang dilakukan |
|---|---|
| Penggantian nama kolom menuntut `SumberVektor` berubah lebih dari nama | **Berhenti.** Itu berarti abstraksinya bocor, dan perubahannya melewati Gerbang 2 tersendiri |
| `Penyemat` ternyata perlu berubah agar jalur ini bekerja | **Berhenti, catat sebagai temuan.** ADR-12 memperkirakan ini; `spec.md` menyatakannya di muka |
| Godaan menyetel ukuran kumpulan penyematan sebagai "ambang" | **Berhenti.** Ia bukan ambang RAG, tetapi bila ia disebut ambang maka C-16 berlaku. Namanya menyebut apa adanya: `SEGMEN_PER_KUMPULAN` |
| Godaan menulis vektor pengganti bagi segmen yang gagal disemat | **Berhenti.** R-05 melarangnya tegas — vektor karangan tidak menghasilkan galat, ia menghasilkan tetangga terdekat yang salah |
