"""Larangan impor pustaka model di luar `src/llm/` — R-04, C-08.

C-08 berbunyi: seluruh pemanggilan model lewat `src/llm/`, tanpa pengecualian.
ADR-11 memperjelas cakupannya — LLM, sematan, NER, dan klasifikasi, bukan LLM
saja. Pembungkus tunggal itulah yang mencatat versi model, konfigurasi, waktu,
dan biaya; tanpa aturan ini, pencatatan versi bergantung pada ingatan penulis
kode, dan NFR-15 berhenti menjadi jaminan.

Daftar `PUSTAKA_MODEL` bukan daftar ketergantungan. Menambah nama ke dalamnya
adalah menambah larangan, bukan menambah paket, sehingga ia tidak melewati
persetujuan C-12. Daftar sengaja memuat pustaka yang belum dipakai: BT-14
masih terbuka, dan larangan yang dipasang setelah pustakanya masuk selalu
lebih sulit ditegakkan.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python, impor_pada

# Penyedia LLM melalui API, dan pustaka model lokal untuk sematan, NER, dan
# klasifikasi. Keduanya tunduk pada C-08.
PUSTAKA_MODEL = frozenset(
    {
        # Penyedia melalui API
        "anthropic",
        "openai",
        "cohere",
        "mistralai",
        "google",
        "vertexai",
        "boto3",
        "litellm",
        # Kerangka orkestrasi yang membungkus pemanggilan model
        "langchain",
        "langchain_core",
        "langchain_community",
        "llama_index",
        "haystack",
        "dspy",
        # Model lokal: sematan, NER, klasifikasi
        "torch",
        "transformers",
        "sentence_transformers",
        "tokenizers",
        "onnxruntime",
        "spacy",
        "flair",
    }
)

# Satu-satunya tempat pustaka di atas boleh diimpor.
JALUR_DIIZINKAN = ("src", "llm")


def _di_dalam_pembungkus(berkas: Path, akar: Path) -> bool:
    bagian = berkas.relative_to(akar).parts
    return bagian[: len(JALUR_DIIZINKAN)] == JALUR_DIIZINKAN


def periksa_impor_penyedia(akar: Path) -> list[Temuan]:
    """Setiap impor pustaka model di luar `src/llm/`.

    Cakupan meliputi seluruh repositori, termasuk `tests/` dan `perkakas/`.
    Uji yang memanggil penyedia langsung melanggar G4-15 (tanpa pemanggilan
    jaringan selama uji) sekaligus C-08, dan alat bantu pembangunan tidak
    punya urusan dengan model.
    """
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar):
        if _di_dalam_pembungkus(berkas, akar):
            continue
        for impor in impor_pada(berkas):
            if impor.modul in PUSTAKA_MODEL:
                temuan.append(
                    Temuan(
                        berkas=berkas,
                        baris=impor.baris,
                        pesan=(
                            f"impor pustaka model {impor.modul!r} di luar src/llm/ — "
                            "C-08 mensyaratkan seluruh pemanggilan model melewati "
                            "pembungkus tunggal yang mencatat versinya"
                        ),
                    )
                )
    return temuan
