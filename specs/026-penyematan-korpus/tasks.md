# Tasks: 026-penyematan-korpus

| | |
|---|---|
| Spec | Gerbang 1 lolos 23 September 2026 (KB-110) |
| Plan | Gerbang 2 lolos 23 September 2026 (KB-111) |
| Status | **Gerbang 3 lolos** — 23 September 2026 (KB-112). T-1 selesai; enam tugas tersisa |
| Kebutuhan | R-01 s.d. R-11; C-02, C-03, C-09, C-12; TK-57, TK-60 |

Satu tugas = satu commit. Uji ditulis lebih dulu. `make check` lulus sebelum
tiap tugas dinyatakan selesai — dijalankan sebagai perintah berdiri sendiri,
tanpa pipa (KB-080).

---

## T-1 · Nama kolom diluruskan ke D-04, dan kolom versi ditambahkan

**Kebutuhan:** R-11; TK-60.

Mendahului seluruhnya. Ia menyentuh fitur 019 yang **sudah lolos Gerbang 4**,
dan menggabungkannya dengan kode baru membuat kegagalan tidak dapat
ditelusuri ke perubahan yang mana.

- [x] Uji: sapuan menemukan `segmen_teks.vektor_sematan` dan
      `segmen_teks.versi_model_sematan` ada pada kedua skema
- [x] Uji: **nama sumber `"vektor"` masih utuh pada 26 tempat** — sapuan
      penjaga atas jebakan (a) `plan.md` Bagian 6
- [x] Uji: tidak ada untai SQL yang menyebut nama kolom di luar tetapannya —
      penjaga atas jebakan (b); dua untai hari ini melewatinya
- [x] `05-kolom-vektor.sql`: `vektor` → `vektor_sematan`; tambah
      `versi_model_sematan text` pada kedua skema
- [x] **Migrasi tabel yang sudah ada** — `CREATE TABLE IF NOT EXISTS` tidak
      menyentuhnya, sehingga berkas selesai dengan status 0 tanpa mengubah apa
      pun. Ditemukan saat T-1 dijalankan, bukan saat direncanakan
- [x] `vektor.py`: tetapan `KOLOM_VEKTOR` → `KOLOM_VEKTOR_SEMATAN`; dua untai
      harfiah disatukan ke tetapan
- [x] Empat berkas uji menyesuaikan nama kolom — dua daftar INSERT, satu
      `ALTER TABLE` pada uji dimensi, satu `UPDATE` pada uji jumlah
- [x] **Tidak ada uji lama bertambah maupun hilang**: 2.108 → 2.115, tepat
      tujuh uji penjaga baru yang tugas ini sendiri tuntut. Kalimat semula
      berbunyi "jumlah sama persis", yang mustahil dipenuhi bersamaan dengan
      tiga uji penjaga — dikoreksi, dan koreksinya dicatat pada KB-112

> Bila `SumberVektor` ternyata perlu berubah lebih dari namanya: **berhenti**.
> Itu berarti abstraksinya bocor, dan perubahannya melewati Gerbang 2
> tersendiri (`plan.md` Bagian 9).

---

## T-2 · `tambah_versi_artefak` pada `src/logbook/`

**Kebutuhan:** R-02; C-09; D-10 Bagian 4.

Tidak menyentuh basis data sama sekali, sehingga dapat berdiri sebelum
jalurnya ada.

- [ ] Uji: bidang yang D-10 Bagian 4 tuntut bagi artefak `indeks` tidak dapat
      luput — kekurangannya tertangkap **saat memanggil**, bukan saat membaca
      berkas berbulan kemudian
- [ ] Uji: baris tertulis ke `L2`, bukan `L1`
- [ ] Uji: berkas hanya bertambah — tidak ada baris lama berubah
- [ ] `tambah_versi_artefak` bertipe, sejajar `tambah_percobaan`

> Bukan `tambah_baris` telanjang. `tambah_percobaan` menerima `Versi` bertipe
> justru agar kelima bidangnya tidak luput karena lupa, dan L2 menuntut lima
> keterangan yang sama mudahnya terlupa.

---

## T-3 · `HasilPenyematan` dan bentuk versi indeks

**Kebutuhan:** K-2; KM-01.

Murni bentuk; tanpa peladen.

- [ ] Uji: versi indeks berbentuk `<indeks>-<YYYYMMDDTHHMMSSZ>`, dinilai atas
      **nilainya** dengan jam tetap yang disuntikkan — bukan atas polanya
- [ ] Uji: `datetime` tanpa zona waktu ditolak (KM-01)
- [ ] Uji: dua pembangunan pada detik berbeda menghasilkan versi berbeda
- [ ] Uji: `HasilPenyematan` beku, `extra="forbid"`, ketiga bidang hitungan
      tidak boleh negatif
- [ ] `HasilPenyematan` dan penyusun versi indeks

---

## T-4 · `sematkan_indeks` beserta keempat penjagaan

**Kebutuhan:** R-01, R-03, R-04, R-05, R-06, R-07.

Inti fitur. Menuntut peladen.

- [ ] Uji: kredensial yang tidak menjangkau indeks sasaran ditolak **sebelum
      satu baris pun dibaca**
- [ ] Uji: penyemat berdimensi lain ditolak sebelum satu baris pun ditulis
- [ ] Uji: segmen bertext kosong dilewati **dan dihitung**, bukan disemat
      menjadi vektor nol
- [ ] Uji: penyemat wajib diserahkan pemanggil — jalur ini tidak menyusun
      penyematnya sendiri (bentuk uji R-02 fitur 019, KB-101)
- [ ] Uji: `versi_model_sematan` tertulis bersama vektornya, satu baris satu
      transaksi
- [ ] `sematkan_indeks` dengan urutan penjagaan `plan.md` Bagian 3

---

## T-5 · Penjalanan ulang dan penolakan percampuran model

**Kebutuhan:** R-08, R-09.

Dipisah dari T-4 dengan sengaja: keduanya sifat atas **dua** penjalanan, dan
uji atas satu penjalanan tidak dapat menyatakannya.

- [ ] Uji: penjalanan kedua atas indeks penuh menulis **nol** baris dan tidak
      menyentuh vektor yang sudah ada
- [ ] Uji: penjalanan kedua dengan penyemat **berbeda versi** ditolak, dan
      pesannya menyebut **kedua** versi
- [ ] Uji: penolakan itu terjadi **sebelum** satu baris pun ditulis — indeks
      tidak boleh tertinggal separuh bercampur
- [ ] Uji: indeks yang separuh tersemat dilanjutkan oleh penyemat **sama
      versi** tanpa menulis ulang yang sudah ada

> R-09 tidak menghasilkan galat bila dilanggar. Ia menghasilkan peringkat
> yang masuk akal dan salah — jarak hanya bermakna di dalam satu ruang
> sematan.

---

## T-6 · Uji mutasi M-1 s.d. M-10, dilaporkan apa adanya

**Kebutuhan:** `plan.md` Bagian 7.3.

- [ ] Kesepuluh mutasi dijalankan
- [ ] Yang tidak menyala **tetap dilaporkan beserta sebabnya**, bukan dihapus
      dari daftar
- [ ] **M-10 menyala** — ia M-7 fitur 019, yang di sana tidak dapat dipasang
      sama sekali

> Bila sebuah mutasi diam, yang **pertama** diperiksa: apakah mutasinya
> terlalu lemah (M-3 fitur 024), atau apakah di seluruh rangkaian uji hanya
> pernah ada satu nilai (M-8 fitur 019, KB-101). Menambah uji adalah langkah
> kedua, bukan pertama.

---

## T-7 · Menutup TK-57 dan TK-60

**Kebutuhan:** TK-57, TK-60.

- [ ] Docstring `HasilSumber.versi_penyemat` diperbarui: setengah R-06 yang
      dinyatakan terbuka di sana kini tertutup
- [ ] TK-57 dan TK-60 berpindah ke **Selesai** pada `docs/D00.md` Bagian 7.12
- [ ] `logbook/L8` bertambah catatan akhir fitur — **juga bila tagihan pasal
      tidak menyusut**, sebab tidak menyusutnya yang wajib terbaca
- [ ] Catatan keputusan pada `logbook/L4`

---

## Urutan dan alasannya

T-1 mendahului sebab ia menyentuh kode yang sudah dinyatakan selesai. T-2 dan
T-3 mendahului T-4 sebab keduanya tidak menyentuh basis data, sehingga bila
bentuknya ternyata tidak pas hal itu terlihat dengan dua tugas sudah aman di
belakang — bentuk yang sama dengan T-1/T-2 fitur 024 dan fitur 019.

T-5 sesudah T-4 sebab ia menuntut jalur yang sudah dapat dijalankan sekali.

## Yang menghentikan pekerjaan, bukan yang memperlambatnya

| Keadaan | Yang dilakukan |
|---|---|
| T-1 menuntut `SumberVektor` berubah lebih dari namanya | Berhenti, ajukan lewat Gerbang 2 tersendiri |
| `Penyemat` ternyata perlu berubah | Berhenti, catat sebagai temuan sebelum mengubah |
| Godaan menulis vektor pengganti bagi segmen yang gagal disemat | **Berhenti.** R-05 melarangnya — vektor karangan tidak menghasilkan galat, ia menghasilkan tetangga terdekat yang salah |
| Godaan menyebut `SEGMEN_PER_KUMPULAN` sebagai ambang | **Berhenti.** Bila ia disebut ambang, C-16 berlaku |
