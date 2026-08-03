# Titik masuk perintah — lihat AGENTS.md bagian Perintah.
#
# Makefile ini juga menyembunyikan pilihan pengelola paket dari alur kerja.
# Penggantian uv ke Poetry menyentuh berkas ini saja, tidak mengubah AGENTS.md.

UV := uv

.PHONY: setup test test-unit lint check compliance

## setup — pasang ketergantungan sesuai uv.lock
setup:
	$(UV) sync

## test — seluruh uji
test:
	$(UV) run pytest

## test-unit — cepat, jalankan sebelum tiap commit
test-unit:
	$(UV) run pytest -m "not lambat"

## lint — linter, pemformat, pemeriksa tipe
lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy

## check — V-01 s.d. V-06, wajib lulus sebelum commit
check:
	@$(UV) run python -m perkakas.pemeriksa.jalankan

## compliance — periksa pasal C-01 s.d. C-20
compliance:
	@$(UV) run python -m perkakas.kepatuhan.jalankan
