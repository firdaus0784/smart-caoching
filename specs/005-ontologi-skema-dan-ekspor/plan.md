# Plan: 005-ontologi-skema-dan-ekspor

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 10 Agustus 2026, KB-032 |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026, keputusan KB-033 |
| Ketergantungan baru | **Nol paket Python** |
| Pertanyaan terbuka | **Nol** — ditetapkan D-06 Bagian 11.2, FR-E02, D-04 Bagian 7.3 |

---

## 1 · Letak modul

`AGENTS.md` tidak menyebut ontologi pada daftar arsitekturnya. Ia bahan
pengetahuan yang dipakai `src/rag/`, dan D-06 menempatkan pembangunannya di
atas bahan terkurasi.

```
src/rag/ontologi/
  skema.py     JenisRelasi, Konsep, Relasi          R-01 s.d. R-06
  hitung.py    jumlah sah dan mentah                R-07
  ekspor.py    JSON-LD                              R-08, R-09
  jejak.py     pencatatan ekspor ke logbook         R-10
```

Tanpa perubahan `AGENTS.md`: `rag` sudah ada pada daftarnya, dan ontologi
adalah bahan pengambilan.

**Tidak menulis berkas.** `src/rag` berada pada jalur penjawaban dan C-17
melarang akses tulis dari sana — pelajaran B-1 fitur 016. Ekspor mengembalikan
untainya; penulisan pekerjaan pemanggil di luar `src/`.

---

## 2 · Yang paling mudah keliru, dan bentuk yang mencegahnya

### Angka 500 yang dipenuhi konsep kosong

D-06 Bagian 11.2 menamainya langsung. Godaannya nyata: MK-06 adalah syarat
Definisi Selesai, tenggatnya bulan 8, dan menambah baris tabel jauh lebih
cepat daripada menyusun definisi.

Bentuknya: `hitung_ontologi` mengembalikan **dua angka bersama** — sah dan
mentah. Satu angka saja dapat dibaca sebagai yang lain, dan yang dibaca
adalah yang lebih besar.

Konsep tanpa definisi tetap **dapat dibentuk**: ia keadaan kerja yang wajar.
Yang tidak boleh adalah ia ikut terhitung.

### Relasi yang mewarisi rujukan konsepnya

R-04. Menghemat satu bidang terasa rapi, dan akibatnya: relasi "bertentangan
dengan" antara dua konsep yang masing-masing bersumber dokumen berbeda tidak
punya dokumen yang menyatakan pertentangannya. Klaim relasi menjadi klaim
tanpa sumber — persis yang C-01 larang pada jawaban.

### Konsep dari karantina

R-06, dan ini C-03 yang merambat. Ontologi diekspor untuk HKI dan publikasi;
dokumen yang belum diverifikasi anonimisasinya lolos ke berkas yang
dilampirkan naskah.

Bentuknya mengikuti fitur 006: bidang `sumber_terkurasi: bool` wajib tanpa
nilai bawaan, dan konsep yang bernilai `False` tidak terhitung sah.

---

## 3 · Bentuk JSON-LD

Konteksnya menamai ketujuh jenis relasi sehingga berkasnya dapat dibaca tanpa
dokumen kita. Ekspor yang menamai relasi dengan untai bebas menuntut pembacanya
menebak artinya — dan berkas ini ditujukan untuk HKI dan publikasi, dibaca
orang yang tidak punya akses ke `docs/`.

Ontologi kosong **ditolak saat diekspor**: berkas JSON-LD berisi nol simpul
terbaca seperti ekspor yang berjalan dan tidak menemukan apa-apa.

---

## 4 · Rencana uji mutasi

| Yang dimutasi | Yang wajib gagal |
|---|---|
| Konsep tanpa definisi ikut terhitung sah | Uji hitung sah |
| Hanya satu angka dikembalikan | Uji dua angka terpisah |
| Konsep dari karantina ikut terhitung | Uji C-03 merambat |
| Relasi mewarisi rujukan konsepnya | Uji bidang wajib |
| Relasi ke konsep yang tidak ada diterima | Uji penolakan |
| Ekspor memuat konsep tak sah | Uji isi ekspor |

---

## 5 · Ketergantungan

**Nol.** JSON-LD adalah JSON biasa; konteksnya untai. Menambah pustaka RDF
untuk menulis satu berkas berarti menambah permukaan V-05 demi kemudahan yang
tidak diperlukan.
