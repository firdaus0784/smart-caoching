/*
 * Service worker cangkang luring — T-6 fitur 027, R-15, C-07.
 *
 * Ditulis tangan, tanpa pustaka. Keputusannya satu fungsi murni,
 * `keputusanTembolok`, yang diuji tanpa peramban (`src/halaman.test.ts`).
 *
 * Cangkang — halaman, skrip, gaya, manifes — diambil dari jaringan lebih dulu
 * dan salinannya disimpan; bila jaringan putus, salinan itu yang tersaji,
 * sehingga layar dapat terbuka dan menyatakan KL-E.
 *
 * Permintaan `/api/` TIDAK PERNAH ditembolok. Jawaban lama yang tersaji dari
 * tembolok melanggar C-07 dengan cara yang sama persis dengan riwayat yang
 * menyimpan tanggapan (D-14 Bagian 4.3): regulasi yang dicabut sesudah
 * jawaban disusun akan tetap tampil sebagai dasar.
 */

const NAMA_TEMBOLOK = "smart-coaching-cangkang-1";

/**
 * @param {string} url
 * @param {string} metode
 * @param {string} asal
 * @returns {"jaringan-lalu-tembolok" | "lewati"}
 */
function keputusanTembolok(url, metode, asal) {
  if (metode !== "GET") return "lewati";
  const alamat = new URL(url);
  if (alamat.origin !== asal) return "lewati";
  const jalur = alamat.pathname.toLowerCase();
  if (jalur === "/api" || jalur.startsWith("/api/")) return "lewati";
  return "jaringan-lalu-tembolok";
}

self.keputusanTembolok = keputusanTembolok;

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (peristiwa) => {
  peristiwa.waitUntil(
    caches
      .keys()
      .then((nama) => Promise.all(nama.filter((n) => n !== NAMA_TEMBOLOK).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (peristiwa) => {
  const permintaan = peristiwa.request;
  if (keputusanTembolok(permintaan.url, permintaan.method, self.location.origin) === "lewati") {
    return;
  }
  peristiwa.respondWith(
    fetch(permintaan)
      .then((jawaban) => {
        if (jawaban.ok) {
          const salinan = jawaban.clone();
          caches.open(NAMA_TEMBOLOK).then((t) => t.put(permintaan, salinan));
        }
        return jawaban;
      })
      .catch(() =>
        caches
          .match(permintaan)
          .then((tersimpan) => tersimpan ?? caches.match("/"))
          .then((tersimpan) => tersimpan ?? Response.error()),
      ),
  );
});
