# Plan: 016-pembacaan-ekspor-label-studio

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 10 Agustus 2026, keputusan KB-025 |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026, keputusan KB-027 |
| Ketergantungan baru | **Nol paket Python** |
| Keputusan Gerbang 1 | **Pilihan A dengan bentuk teknis B** — Bagian 5 |

---

## 1 · Letak modul

Tanpa perubahan `AGENTS.md`. Seluruhnya di bawah `src/nlp/anotasi/`, tempat
fitur 003 sudah berdiri.

```
src/nlp/anotasi/
  impor_ls.py     pembacaan ekspor Label Studio    R-01 s.d. R-08
  ekspor.py       JSONL dan CoNLL                  R-09 s.d. R-12
  jejak_impor.py  pencatatan impor ke logbook      R-14
perkakas/pemeriksa/
  ketergantungan_sistem.py  diperluas              R-13
```

`impor_ls.py` **tidak mengimpor apa pun dari Label Studio.** KB-020 menetapkan
ia layanan terpisah; yang dibaca hanyalah berkas JSON biasa.

---

## 2 · Yang paling mudah keliru, dan bentuk yang mencegahnya

### Bentuk ekspor yang berubah, diurai sebagian

Label Studio dapat naik versi tanpa kita. Penguraian yang toleran menghasilkan
korpus yang **sebagian bidangnya hilang tanpa satu galat pun** — dan bidang
yang hilang paling mungkin bidang yang jarang terisi, yaitu bendera.

Bentuk yang mencegahnya: setiap kunci yang dipakai diambil dengan indeks,
bukan `.get()` bernilai bawaan. Kunci yang hilang menaikkan `GalatBentukEkspor`
yang menyebut kunci dan letaknya. Satu titik masuk, satu tipe galat.

### Korpus yang terbaca bersih karena instrumennya tidak ada

R-06, dan ini pelajaran TA-01 pada bentuknya yang paling mahal. `bocor_pii`
adalah bendera yang menyatakan data pribadi lolos anonimisasi; korpus tanpa
bendera karena proyeknya **tidak dapat** mengumpulkannya terbaca persis seperti
korpus bersih.

Bentuknya mengikuti `HasilSistem` fitur 015 dan `HasilKualifikasi` fitur 003:
`HasilImpor` membawa `bendera_terkumpul: bool` di samping dokumennya, dan
ekspor JSONL menuliskan **`null`, bukan `[]`**, ketika benderanya tidak
terkumpul. `[]` berarti "diperiksa, tidak ada"; `null` berarti "tidak
diperiksa".

### Id pengguna Label Studio masuk korpus

R-07. `completed_by` adalah bilangan bulat internal Label Studio; D-03 Bagian
15 menuntut **kode anonim**. Pemetaan id ke kode diberikan pemanggil sebagai
tabel; id yang tidak ada pada tabel **menggagalkan impor**, tidak dipakai apa
adanya. Id mentah yang lolos ke korpus adalah pengenal yang bertahan pada
berkas yang dilampirkan naskah.

### Rentang yang bergeser saat ekspor CoNLL

R-10. CoNLL berbaris per token; anotasi kita berindeks karakter. Pemetaannya
memakai `Token.mulai` dan `Token.akhir` dari fitur 015 — keduanya sudah
berindeks karakter, sehingga pemetaannya pencocokan tepat, bukan perkiraan.

Rentang yang **tidak jatuh pada batas token** dilaporkan sebagai temuan dan
dokumennya dilewati. Menggesernya ke batas terdekat menghasilkan berkas
pelatihan yang benar bentuknya dan salah isinya.

---

## 3 · Bentuk konfigurasi Label Studio yang dituntut

Ditetapkan di sini (Gerbang 1 pilihan A) supaya tim punya satu hal pasti
untuk disalin:

```xml
<Choices name="bendera" toName="teks" choice="multiple">
  <Choice value="perlu_adjudikasi"/><Choice value="ocr_rusak"/>
  <Choice value="anonimisasi_berlebih"/><Choice value="bocor_pii"/>
</Choices>
```

`impor_ls` **tidak membaca konfigurasi proyek** — ekspor tidak membawanya.
Pemanggil menyatakan keadaannya lewat satu parameter, dan pernyataan itu ikut
tercatat ke `logbook/`. Itu bentuk teknis B pada `spec.md`.

---

## 4 · Cara diuji

**Terhadap berkas sungguhan pada `tests/bahan/`.** Bentuk yang disusun uji
akan menyerupai dugaan penulisnya, dan itu kekeliruan yang KB-021 tolak dengan
dua contoh.

Bentuk yang berubah diuji dengan **merusak salinan berkas sungguhan** —
menghapus satu kunci, mengubah satu tipe — bukan dengan menyusun bentuk rusak
dari nol.

---

## 5 · Keputusan Gerbang 1

**Pilihan A dengan bentuk teknis B** — diputus 10 Agustus 2026, KB-025.

Nama kendali dan keempat nilainya ditetapkan kode (Bagian 3). Keadaan proyek
dinyatakan pemanggil lewat parameter, sehingga proyek yang belum memasang
kendalinya tetap dapat diimpor **tanpa korpusnya terbaca bersih**.

C ditolak: bendera yang ditunda adalah bendera yang tidak ada ketika data
pribadi lolos, dan KM-05 memeriksanya harian.

---

## 6 · Rencana uji mutasi

| Yang dimutasi | Yang wajib gagal |
|---|---|
| `.get()` bernilai bawaan menggantikan indeks | Uji bentuk ekspor yang dirusak |
| `bendera_terkumpul` dihapus; bendera kosong ditulis `[]` | Uji korpus tidak terbaca bersih |
| Id pengguna dipakai apa adanya ketika tidak ada pada tabel | Uji id mentah tidak masuk korpus |
| Rentang tak sejajar token digeser ke batas terdekat | Uji CoNLL melaporkan, tidak menggeser |
| `was_cancelled` diabaikan | Uji anotasi batal tidak masuk korpus |

---

## 7 · Ketergantungan

**Nol.** JSON pustaka baku; tokenisasi sudah ada dari fitur 015.
`[sistem.label_studio]` ditambahkan **bersama** perluasan pemeriksa R-18 yang
membandingkannya — patokan tanpa pemeriksa tidak menjaga apa pun.
