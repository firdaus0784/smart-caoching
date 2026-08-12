# Plan: 007-pengambilan-hibrida

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 12 Agustus 2026, KB-034 |
| Status | **Lolos Gerbang 4** — 12 Agustus 2026 (KB-035) |
| Ketergantungan baru | **Nol paket Python** |
| Pertanyaan terbuka | **Nol** — keempatnya dijawab pada KB-034 |

---

## 1 · Jawaban atas keempat pertanyaan

| | Pertanyaan | Putusan |
|---|---|---|
| 1 | `penanda_bagian` wajib pada `SegmenTerindeks` | **A** — ditambahkan sekarang, wajib |
| 2 | Konstanta *k* pada RRF | **A** — 60, dari Cormack dkk. 2009, pada rumah tetapan |
| 3 | Bentuk sumber vektor sebelum modelnya ada | **A** — antarmuka + tiruan deterministik pada `tests/` |
| 4 | Tepi `rag → nlp` pada `AGENTS.md` | **Ditambahkan**, satu jurusan, dengan alasannya |

---

## 2 · Letak modul

```
src/rag/pengambilan/
  tetapan.py     angka D-07 Bagian 4.4 dan konstanta RRF      R-08
  kandidat.py    Kandidat, SumberKandidat (abstrak)           R-01, R-02, R-03
  bm25.py        IndeksLeksikal, skor BM25 atas stem          R-09, R-10, R-13
  gabung.py      Reciprocal Rank Fusion                       R-04, R-05, R-06
  kecukupan.py   AmbangKecukupan, penilaian                   R-11, R-12
  hibrida.py     penyusun: kredensial → sumber → gabung → k   R-07, R-14
src/penyimpanan/
  indeks.py      diperluas: penanda_bagian wajib              R-10
perkakas/pemeriksa/
  ambang.py      pemeriksa C-16                               R-08, R-11
tests/rag/pengambilan/
  sumber_tiruan.py  pelaksana deterministik, berdiri untuk vektor
```

**`tetapan.py` masuk `RUMAH_TETAPAN`.** Berkas itu sudah dipakai dua kali —
`src/nlp/anotasi/ambang.py` (fitur 003) dan `src/nlp/pelatihan/pembagian.py`
(fitur 004) — dan alasannya sama ketiga kalinya: penyapuan angka pada satu
fitur akan menandai rumah tetapan fitur lain. Yang berubah kali ini: pemeriksa
C-16 menjadikan daftar itu **aturan**, bukan hanya daftar putih uji.

### Mengapa `src/rag/pengambilan/`, bukan `src/penyimpanan/`

Pemisahan indeks (fitur 006) adalah akses penyimpanan; pengambilan bukan. BM25
adalah perhitungan atas isi segmen, dan menaruhnya di `src/penyimpanan/` akan
membuat lapisan penyimpanan mengetahui cara mencari — persis pembalikan yang
`AGENTS.md` cegah dengan menyatakan penyimpanan sebagai "lapisan di bawah
keempatnya".

Yang tetap tinggal di `src/penyimpanan/`: `penanda_bagian`, sebab ia bidang
`segmen_teks` pada D-14 Bagian 5, bukan bidang hasil pengambilan.

---

## 3 · Tepi `rag → nlp`, dan mengapa ia ditulis

`AGENTS.md` bagian **Arsitektur** bertambah satu kalimat:

> `rag` boleh memanggil `nlp`, satu jurusan — `nlp` tidak memanggil `rag`.

Alasannya tidak baru; ia sudah tertulis pada fitur 015 dua hari lalu, hanya
belum di tempat yang membacanya:

> Kegunaan keluaran modul ini dibatasi tegas: **untuk pencarian**, bukan untuk
> menyiapkan bahan anotasi. — `src/nlp/praproses/stemming.py`

D-07 Bagian 3.3 menuntutnya secara langsung: *"BM25 pada teks tersegmentasi,
dengan penanganan morfologi Bahasa Indonesia sesuai modul praproses
(FR-B03)."*

Arah sebaliknya tetap terlarang, dan sebabnya sejajar dengan tepi
`ingest → nlp` yang sudah ada: `nlp` yang memanggil `rag` akan membuat
praproses bergantung pada indeks yang praproses itu sendiri isi.

**Alternatif yang ditolak:** menyalin tokenisasi dan stemming ke `src/rag/`.
Dua salinan akan berbeda ketika daftar stop-word berubah, dan `stemming.py`
sudah memuat penyaringan yang tidak lazim — `KATA_DILINDUNGI` memuat "kepala"
dan "sekolah" justru karena daftar Sastrawi membuang keduanya. Salinan yang
tertinggal satu kata itu menghasilkan pencarian yang sepi, bukan galat.

---

## 4 · Yang paling mudah keliru, dan bentuk yang mencegahnya

### 4.1 Hibrida yang sebenarnya satu sumber

Bahaya utama, dan ia **tidak menghasilkan satu galat pun**. RRF atas satu
daftar mengembalikan daftar itu — urutan yang sama, nama fungsi yang tetap
berbunyi `gabung_peringkat`, uji yang tetap hijau.

Bentuk yang mencegahnya: `gabung_peringkat` menolak kurang dari dua sumber
(R-05), dan setiap hasil membawa `penyumbang` (R-06). Keduanya bersama, sebab
masing-masing sendirian bocor: penolakan sendirian dapat dipuaskan pelaksana
kosong (pertanyaan 3 pilihan B), dan penyumbang sendirian hanya melaporkan
tanpa menahan.

### 4.2 Ambang bawaan yang "sementara"

C-16 melarang menyetel ambang di luar BT-29. Cara paling sunyi melanggarnya
bukan menyetel angka melainkan **menuliskan angka awal yang tak pernah
ditinjau** — ia berjalan hari pertama, memberi hasil masuk akal, dan tidak
seorang pun kembali kepadanya.

Bentuk yang mencegahnya: `AmbangKecukupan` **tidak dapat dibentuk tanpa**
`CatatanKalibrasi` yang menyebut tanggal, *gold set*, dan pemutusnya (R-12).
Bukan gagal saat dijalankan — tidak dapat disusun sama sekali. Pola
`Kredensial` fitur 002: "parameter berbawaan `None` akan berubah menjadi
'tanpa kredensial berarti tanpa batas'".

`PenilaianKecukupan` karena itu menuntut `AmbangKecukupan` tepat sesudah
`self`, mengikuti `PenyimpanDasar` — "menempatkannya di akhir daftar parameter
membuatnya terbaca sebagai renungan belakangan".

### 4.3 BM25 atas permukaan, bukan stem

`Token` membawa keduanya. Mencocokkan atas `permukaan` akan bekerja pada
sebagian besar uji — "sekolah" tetap "sekolah" — dan gagal justru pada kata
berimbuhan yang menjadi inti pertanyaan manajerial: "menugaskan", "penugasan",
"ditugaskan". Kegagalannya berupa hasil yang sepi, bukan galat.

Uji yang menutupnya memakai pasangan kata yang **berbeda permukaan dan sama
stem**, sehingga versi yang mencocokkan permukaan mengembalikan nol.

### 4.4 Seri yang diputus urutan sisipan

Dua segmen berskor identik lazim pada korpus kecil. Urutan sisipan bergantung
pada urutan pembacaan berkas, dan hasil yang berubah karena urutan berkas
adalah hasil yang tidak dapat diulang — R-02 gugur tanpa terlihat.

Diputus `id_segmen` menaik, dan itu dinyatakan pada uraiannya.

### 4.5 Kredensial yang diperiksa sesudah pencarian

Menyaring hasil setelah pencarian berjalan adalah penyaringan saat kueri yang
C-02 tolak — bentuk yang sama yang fitur 006 tutup. Kredensial diperiksa
**sebelum** sumber dijalankan: indeks yang tidak dijangkau tidak dicari sama
sekali.

---

## 5 · Pemeriksa C-16

C-16 kini `fitur_pengunci="007 pengambilan hibrida dan kalibrasi ambang"`.
Sesudah fitur ini ia menjadi `pemeriksa=periksa_ambang`, dengan tiga aturan:

1. **Angka ambang hanya pada rumah tetapan.** Berkas di luar `RUMAH_TETAPAN`
   yang menugaskan bilangan pecahan ke nama beryawalan `AMBANG_` atau
   berakhiran `_AMBANG` adalah temuan.
2. **`AmbangKecukupan` tidak memiliki nilai bawaan di mana pun pada `src/`.**
   Nilai tinggi dan menengah belum ada, dan kekosongan itu yang benar — bukan
   keadaan sementara yang perlu diisi.
3. **Rumah tetapan menyebut sumbernya.** Setiap tetapan pada rumah tetapan
   wajib memiliki uraian yang menyebut dokumen atau makalah asalnya. Angka
   tanpa asal adalah angka yang disetel seseorang.

Aturan 3 adalah yang membuat jawaban pertanyaan 2 dapat ditegakkan. Menyalin
60 dari Cormack dkk. 2009 sah; menuliskan 60 tanpa menyebut dari mana tidak.

**Pemeriksanya diuji terhadap pohon yang sengaja dirusak**, bukan hanya
terhadap pohon bersih — pelajaran fitur 006: pemeriksa yang terdaftar tetapi
tidak memeriksa apa pun melapor LULUS dengan cara yang persis sama dengan
pemeriksa yang benar.

---

## 6 · Rencana uji mutasi

Dijalankan pada Gerbang 4, hasilnya dilaporkan apa adanya.

| | Mutasi | Uji yang harus menyala |
|---|---|---|
| M-1 | `gabung_peringkat` menerima satu sumber | R-05 |
| M-2 | RRF memakai `1/peringkat`, bukan `1/(k + peringkat)` | contoh hitung tangan |
| M-3 | BM25 mencocokkan `permukaan`, bukan `stem` | pasangan sama-stem beda-permukaan |
| M-4 | Seri diputus urutan sisipan | uji pengulangan pada masukan teracak |
| M-5 | Kredensial diperiksa sesudah pencarian, bukan sebelum | C-02, `PEMANGGIL_LLM` |
| M-6 | `penanda_bagian` diberi nilai bawaan `""` | R-10 |
| M-7 | `AmbangKecukupan` diberi nilai bawaan | R-11 |
| M-8 | `penyumbang` diisi hanya sumber berperingkat terbaik | R-06 |

---

## 7 · Ketergantungan

**Nol paket baru.** BM25 adalah rumus; RRF adalah rumus. Praproses sudah ada
sejak fitur 015. `math` dan `collections` ada pada pustaka baku.

Yang **akan** menuntut ketergantungan adalah fitur 019 — model sematan dan
pgvector — dan itu sebabnya ia dipisah, bukan sebabnya ia ditunda.

---

## 8 · Yang berpindah ke fitur 019

| | Menunggu |
|---|---|
| Sumber kandidat vektor | Model sematan (C-12) + pgvector (ADR-05, D-09) |
| Pemeringkat ulang lintas-enkoder | Sama; D-07 menyebutnya "bila tersedia" |
| Nilai ambang tinggi dan menengah | BT-29 atas *gold set* BT-35, bulan 4–5 |
| Penguatan kategori | BT-29; menuntut klasifikasi K1–K8 fitur 017 |

Fitur 019 **tidak dapat dimulai sebelum bulan 4–5**, dan itu bukan perkiraan
melainkan pembacaan D-08 Bagian 6: *gold set* dibekukan sebelum kalibrasi.
