# Plan: 006-indeks-terpisah-lisensi

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 10 Agustus 2026, KB-030 |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026, keputusan KB-031 |
| Ketergantungan baru | **Nol paket Python** |
| Pertanyaan terbuka | **Nol** — seluruhnya ditetapkan D-07, D-14, dan ADR-06 |

---

## 1 · Letak modul

Pemisahan indeks adalah pemisahan **akses penyimpanan**, dan `AGENTS.md`
menetapkan seluruh akses penyimpanan lewat `src/penyimpanan/`. Bentuknya
mengikuti C-03 fitur 002 yang sudah berdiri di sana.

```
src/penyimpanan/
  indeks.py       IndeksTujuan, SegmenTerindeks, penempatan   R-01 s.d. R-05, R-08
  kredensial.py   diperluas: peran tanpa akses metadata       R-04
perkakas/pemeriksa/
  pemisahan_indeks.py   pemeriksa C-02                        R-06, R-07
```

`IndeksTujuan` **tidak ditambahkan pada `Area`**. Uraian `area.py` menyatakan
menambah nilai ketiga menuntut D-14 diubah lebih dulu (AG-04), dan indeks
bukan area penyimpanan melainkan tujuan segmen. D-14 Bagian 5 sudah menamainya
`segmen_teks.indeks_tujuan` dengan nilai `utama` dan `metadata`; fitur ini
mewujudkannya, tidak menciptakannya.

---

## 2 · Yang paling mudah keliru, dan bentuk yang mencegahnya

### Penyaringan menggantikan pemisahan

Godaan terbesar fitur ini, dan ia **terasa lebih sederhana**: satu klausa
`WHERE indeks_tujuan = 'utama'` pada setiap kueri. Mudah dibaca, mudah diuji,
dan salah.

Yang membuatnya salah: klausa itu ada pada **setiap** kueri, dan satu kueri
yang lupa memuatnya tidak menghasilkan galat apa pun. Ia menghasilkan jawaban
yang lebih lengkap — dan jawaban yang lebih lengkap tidak pernah terasa seperti
kekeliruan sampai audit lisensi.

Bentuk yang mencegahnya, mengikuti ADR-06 dan C-03 fitur 002: **kredensial
jalur penjawaban tidak memuat izin baca `metadata`.** Bukan tidak boleh —
tidak bisa. Ditambah pemeriksa AST yang menyala bila ada kode di luar
`src/penyimpanan/` menyebut indeks metadata.

### Status anonimisasi yang terlewat

R-05. Penegakan lisensi mudah menyita seluruh perhatian di sini, dan
sementara itu dokumen yang anonimisasinya masih `menunggu` masuk indeks utama
tanpa satu pun pemeriksaan menyala. Yang bocor bukan lisensi melainkan data
pribadi — dan itu lebih berat.

Bentuknya: penempatan ke indeks menuntut **kedua** syarat, dan keduanya
diperiksa pada satu tempat yang sama sehingga tidak dapat dipenuhi separuh.

### Indeks tujuan yang ditetapkan belakangan

R-03. Segmen yang dibentuk tanpa indeks tujuan lalu diisi kemudian adalah
segmen yang sempat ada tanpa penjagaan. Bentuknya: bidang wajib tanpa nilai
bawaan, sama dengan `status_pra_anotasi` fitur 003.

---

## 3 · Cara C-02 menjadi terperiksa mesin

`daftar_pasal.py` memindahkan C-02 dari `fitur_pengunci="006 …"` menjadi
`pemeriksa=periksa_pemisahan_indeks`, persis seperti C-03 pada fitur 002.

Pemeriksanya menegakkan tiga hal:

| Aturan | Yang dicegah |
|---|---|
| Hanya `src/penyimpanan/` menyebut `metadata` sebagai indeks | Jalur lain membaca langsung |
| Tidak ada kredensial di luar `kredensial_baku.py` yang memberi izin baca metadata | Izin diberikan sambil lalu |
| `src/llm/` dan `src/rag/` tidak mengimpor modul indeks metadata | Teks tertutup mencapai pembungkus LLM |

**`make compliance` wajib menyusut satu** — 9 lulus, 11 belum. Bila tidak
menyusut, ada yang keliru: pemeriksa yang terdaftar tetapi tidak memeriksa apa
pun akan melapor lulus dengan cara yang sama seperti pemeriksa yang benar.

---

## 4 · Rencana uji mutasi

| Yang dimutasi | Yang wajib gagal |
|---|---|
| Kredensial penjawaban diberi izin baca metadata | Uji sifat pemisahan |
| Penempatan menyaring alih-alih menolak | Uji penolakan lisensi tertutup |
| Syarat status anonimisasi dilepas | Uji status `menunggu` ditolak |
| Pemeriksa didaftarkan tanpa memeriksa apa pun | Uji `make compliance` menyusut |
| Indeks tujuan diberi nilai bawaan | Uji bidang wajib |

---

## 5 · Ketergantungan

**Nol.** Seluruhnya tipe dan pemeriksa AST pustaka baku.
