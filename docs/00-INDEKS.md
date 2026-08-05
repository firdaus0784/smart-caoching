# Indeks Himpunan Dokumen
## Pengembangan Sistem Smart-Coaching Adaptif Berbasis NLP — Siklus 2026

| Item | Keterangan |
|---|---|
| Penelitian induk | Skema Penelitian Hibah UPI — *Pengembangan Framework Smart-Coaching Adaptif Berbasis Natural Language Processing untuk Meningkatkan Efektivitas Manajemen Sekolah Dasar* |
| Ketua peneliti | Dr. Cucun Sunaengsih, M.Pd. |
| Cakupan himpunan | **Jalur pengembangan sistem aplikasi.** Dokumen administratif hibah, laporan kemajuan, dan naskah artikel diurus tim lain |
| Lokus | Kabupaten Sumedang |
| Siklus | 8 bulan, target TKT 3 |
| Jumlah dokumen | 15 |
| Tanggal himpunan | 2 Agustus 2026 |
| Status | Draf lengkap, menunggu review tim |

---

## Urutan Membaca

Bagi pembaca baru, urutan ini paling masuk akal. Bagi pelaksana, langsung ke dokumen yang relevan dengan tugasnya.

| Urutan | Berkas | Isi | Untuk siapa |
|---|---|---|---|
| 1 | `D00-Kendali-Dokumen-dan-Konsistensi.md` | Aturan yang mengatur seluruh dokumen: kepemilikan fakta, prosedur audit, riwayat temuan konsistensi | **Baca lebih dulu.** Seluruh tim |
| 2 | `D01-BRD-PRD-Sistem-Smart-Coaching.md` | Kebutuhan bisnis dan produk; 70+ kebutuhan berkode; batas ruang lingkup; risiko | Seluruh tim |
| 3 | `D02-Persona-dan-Peta-Perjalanan-Pengguna.md` | Enam persona; enam peta perjalanan; titik kritis; kalender manajerial | Substansi, antarmuka, lapangan |
| 4 | `D11-Landasan-Ilmiah-dan-Rujukan-Praktik.md` | Basis rujukan ilmiah; audit otentisitas; konteks regulasi terverifikasi | **Ketua peneliti dan penulis naskah** |
| 5 | `D03-Pedoman-Anotasi-dan-Skema-Label.md` | Skema label; aturan rentang; katalog kasus; protokol kesepakatan; beban kerja | Anotator, adjudikator |
| 6 | `D04-Arsitektur-Perangkat-Lunak.md` | Penggerak, prinsip, wadah, model data, 11 catatan keputusan arsitektur | Teknis |
| 7 | `D05-Arsitektur-Informasi-dan-Wireframe.md` | Peta layar; alur; keadaan layar; pola komponen; pedoman mikrokopi | Antarmuka, substansi |
| 8 | `D06-Pipeline-Pengetahuan-dan-SOP-Kurasi.md` | Empat kanal sumber; kepatuhan lisensi; prosedur dan kapasitas kurasi | Kurator, teknis |
| 9 | `D07-Spesifikasi-RAG-dan-Penegakan-Sitasi.md` | Segmentasi, pengambilan, penyusunan jawaban, tujuh pemeriksaan validator | Teknis |
| 10 | `D08-Rencana-Pengujian-dan-Evaluasi-Teknis.md` | Definisi operasional metrik; komposisi *gold set*; aturan pelaporan | Teknis, penilai, penulis naskah |
| 11 | `D09-Runbook-Penyebaran-dan-Operasional-Pilot.md` | Prasyarat; jadwal pilot; protokol insiden; penutupan | Lapangan, ketua peneliti |
| 12 | `D10-Buku-Log-dan-Model-Card.md` | Kerangka pencatatan; model card; datasheet korpus; berkas HKI | **Diisi sejak Bulan 1** |
| 13 | `D12-Panduan-Pengembangan-Agentic-AI.md` | Konstitusi proyek; alur Spec-Driven Development; gerbang manusia | Teknis |
| 14 | `D13-Model-Ancaman-dan-Kendali-Keamanan.md` | Katalog 13 ancaman; peringkat kepercayaan asal segmen; kendali berlapis; uji adversarial | **Teknis, ketua peneliti** |
| 15 | `D14-Kontrak-Antarmuka-dan-Kamus-Data.md` | Peta rute; bentuk tanggapan dan galat; kamus bidang data | Teknis, agen pembangun |

---

## Yang Perlu Diputuskan Lebih Dulu

Tiga hal ini menghambat pekerjaan lain dan sebaiknya diselesaikan pada Bulan 1.

| Prioritas | Butir | Menghambat |
|---|---|---|
| 1 | **KI-01** — volume korpus 1.000 atau 5.000 dokumen. Usulan pada D-01 dan perhitungan beban kerja pada D-03 Bagian 12 | Seluruh Fase 2 |
| 2 | **ET-01** — pengajuan *ethical clearance*. Jurnal terindeks umumnya meminta nomornya dicantumkan dalam naskah | Pengambilan data; publikasi |
| 3 | **TO-02** — koreksi rujukan Design Science Research pada proposal induk (D-11 Bagian 1.2). Perbaikan satu baris | Kredibilitas metodologi |

Selain itu, **D-11 Bagian 2 wajib diverifikasi anggota tim dari Dinas Pendidikan** sebelum skema label dan kanal ingesti dikunci. Isinya berasal dari penelusuran daring, dan untuk rujukan regulasi itu tidak memadai.

---

## Peta Kepemilikan Fakta

Setiap fakta dimiliki tepat satu dokumen. Dokumen lain merujuk, tidak menyalin. Bila terjadi perbedaan, dokumen pemilik yang berlaku. Daftar lengkap pada D-00 Bagian 3.

| Fakta | Pemilik |
|---|---|
| Kode kebutuhan, metrik, aturan lisensi, rambu etika, taksonomi telemetri | D-01 |
| Persona, peta perjalanan, titik kritis, kalender manajerial | D-02 |
| Skema label, aturan rentang, protokol kesepakatan | D-03 |
| Keputusan arsitektur, tumpukan teknologi, model data rinci | D-04 |
| Peta layar, keadaan layar, pola komponen, mikrokopi | D-05 |
| Kanal sumber, penyaringan, format butir, SOP kurasi | D-06 |
| Strategi pengambilan, penyusunan jawaban, aturan validator | D-07 |
| Definisi operasional metrik, *gold set*, aturan pelaporan | D-08 |
| Prosedur pilot, protokol insiden, penutupan | D-09 |
| Riwayat percobaan, model card, datasheet, versi artefak | D-10 |
| Rujukan ilmiah dan rujukan regulasi/praktik | D-11 |
| Konstitusi proyek, alur kerja agen, gerbang manusia | D-12 |
| Katalog ancaman, peringkat kepercayaan segmen, kendali keamanan | D-13 |
| Kontrak antarmuka, model galat, kamus data | D-14 |

---

## Riwayat Audit

Sepuluh audit menghasilkan 52 temuan sebelum satu baris kode ditulis. Audit kesebelas, AK-12, menambah tujuh temuan saat baris pertama ditulis. Rinciannya pada D-00 Bagian 7.

| Audit | Cakupan | Temuan |
|---|---|---|
| AK-01, AK-01b | D-01, D-02 | TK-01 s.d. TK-11 |
| AK-02 | + D-03 | TK-12 s.d. TK-16 |
| AK-03 | + D-04 | TK-17 s.d. TK-21 |
| AK-04 | + D-05 | TK-22 s.d. TK-24 |
| AK-05 | + D-06 | TK-25 s.d. TK-27 |
| AK-06 | + D-07 | TK-28 s.d. TK-31 |
| AK-07 | + D-08 | TK-32 s.d. TK-34 |
| AK-08 | Seluruhnya | TK-35 s.d. TK-37 |
| **AK-09O** | Otentisitas rujukan | TO-01 s.d. TO-10 |
| **AK-13S** | Keamanan dan kepatuhan | TA-01 s.d. TA-05 |
| **AK-12** | Prapembangunan | TK-39 s.d. TK-45 |

Tiga temuan yang paling menentukan mutu penelitian:

**TK-07** — angka rasio penerapan 40% sempat tertulis seolah target penelitian, padahal berasal dari naluri desain produk. Bila dibiarkan, seluruh rancangan akan condong mengejar angka itu dan merusak variabel hasil utama.

**TK-29** — sampai audit keenam, tidak ada satu pun metrik yang mengukur apakah sistem tahu kapan harus menolak menjawab, padahal di situlah letak kebaruan yang diklaim penelitian ini.

**TO-05 s.d. TO-10** — dokumen yang disusun akhir Juli sudah memuat rujukan praktik tidak berlaku pada awal Agustus. Ini bukti empiris paling langsung bahwa pemeriksaan status keberlakuan regulasi (KL-07, VS-06) bukan kehati-hatian berlebihan.

**TA-01** — validator sitasi, kendali yang dirancang sebagai penjaga utama sistem, ternyata dapat mengesahkan jawaban hasil penyisipan instruksi: klaimnya memang didukung segmen yang disusupi. Provenans bukan keabsahan, dan rancangan sebelumnya memperlakukan keduanya sebagai hal yang sama.

---

## Audit Berikutnya

| Kode | Dijalankan | Perhatian |
|---|---|---|
| AK-09 | Setelah Fase 1 | Apakah hasil validasi persona (VA-01 s.d. VA-08) mengubah asumsi desain |
| AK-10 | Sebelum pilot | Apakah prasyarat PS-01 s.d. PS-13 terpenuhi dan terdokumentasi |
| AK-11 | Sebelum naskah | Apakah setiap klaim punya jejak; apakah keterbatasan dan insiden terwakili jujur |
| AK-13 | Setelah uji adversarial | Apakah kegagalan diperbaiki pada pengambilan, bukan dengan melonggarkan validator |

---

*Himpunan ini bersifat hidup. Setiap perubahan dicatat pada riwayat revisi dokumen terkait dan pada register D-00.*
