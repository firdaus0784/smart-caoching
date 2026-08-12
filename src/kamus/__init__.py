"""Kamus data — enum milik `docs/D14.md` Bagian 5 dan D-13 Bagian 6.

Menopang C-02 (FR-D06), C-19 (FR-F15), dan C-07 (KL-07): ketiga pasal itu
terbaca pada enum yang tinggal di sini, dan enum yang berumah dua membuat
salah satu pembacaannya luput saat D-14 berubah.

Lapisan paling bawah: **tidak mengimpor apa pun dari `src/`**, dan setiap
lapisan lain boleh mengimpornya.

Ia ada karena `IndeksTujuan` sempat ditulis dua kali — `src/llm/tipe.py` pada
fitur 001 dan `src/penyimpanan/indeks.py` pada fitur 006 — dan sebabnya bukan
kecerobohan tunggal melainkan **enum itu tidak punya rumah**. Nilai yang
dimiliki D-14 bukan milik pembungkus model maupun milik lapisan penyimpanan;
menaruhnya pada salah satunya membuat lapisan berikutnya yang membutuhkannya
menulis ulang alih-alih mengimpor ke atas.
"""
