/**
 * GET /api/dataset
 *
 * Data mentah per baris untuk halaman Data View (/data): komentar YouTube dan
 * berita, lengkap dengan anotasi stance/sentimen. Saat ini masih data dummy —
 * backend developer bisa mengganti isinya dengan query ke database.
 *
 * Dipanggil dengan filter yang sama seperti dashboard, contoh:
 *   /api/dataset?types=pltu&platforms=news&range=3m
 * types & platforms dipakai untuk memilih data yang dikirim.
 * Rentang waktu (range/from/to) BELUM dipakai untuk menyaring data dummy.
 *
 * Bentuk response (hanya type & platform yang dipilih yang ikut):
 * {
 *   pltu: {
 *     youtube: [{ id, text, videoTitle, videoUrl, stance, sentiment }],
 *     news:    [{ id, title, source, actors: [], stance, evidence }],
 *   },
 *   pltn: { ... },
 * }
 * stance    : "support" | "neutral" | "oppose"
 * sentiment : "positive" | "neutral" | "negative"  (hanya YouTube)
 */

import { NextResponse } from "next/server";
import { queryToFilter } from "@/lib/analysisFilter";

// ============================================================================
// DUMMY DATA — Ganti bagian ini dengan query database Anda
// ============================================================================

/** Link dummy: pencarian YouTube berdasarkan judul video. */
const youtubeSearch = (title) =>
  `https://www.youtube.com/results?search_query=${encodeURIComponent(title)}`;

const youtube = (id, text, videoTitle, stance, sentiment) => ({
  id,
  text,
  videoTitle,
  videoUrl: youtubeSearch(videoTitle),
  stance,
  sentiment,
});

const news = (id, title, source, actors, stance, evidence) => ({
  id,
  title,
  source,
  actors,
  stance,
  evidence,
});

const DATASET = {
  pltu: {
    youtube: [
      youtube(
        "pltu-yt-1",
        "Asap dari PLTU ini bikin batuk-batuk warga sekitar tiap pagi gak kelar-kelar, mohon pemerintah segera audit filternya tolong perhatikan nasib anak kecil disini.",
        "Warga Cilegon Keluhkan Debu PLTU Suralaya",
        "oppose",
        "negative"
      ),
      youtube("pltu-yt-2", "Londo irenggg", "Debat Transisi Energi: PLTU Masih Dibutuhkan?", "neutral", "neutral"),
      youtube(
        "pltu-yt-3",
        "Prabowo Siapkan BLU Beli Batu Bara-Gas untuk Listrik, Ini Bocorannya mantap untuk menjaga kestabilan tarif listrik rakyat kecil agar tidak sering mati lampu.",
        "Prabowo Siapkan BLU Batu Bara untuk Listrik",
        "support",
        "positive"
      ),
      youtube("pltu-yt-4", "MBG bermanfaat tidakkkkk", "Debat Transisi Energi: PLTU Masih Dibutuhkan?", "oppose", "negative"),
      youtube(
        "pltu-yt-5",
        "Kalau mau transisi energi ke hijau, bangun dulu alternatifnya yang matang. Kalau langsung dimatikan PLTU-nya yang ada pulau Jawa defisit listrik massal.",
        "Pensiun Dini PLTU: Siapkah Jawa-Bali?",
        "neutral",
        "neutral"
      ),
      youtube(
        "pltu-yt-6",
        "Emisi fly ash dan bottom ash dari cerobong pembakaran batu bara sudah jelas melampaui ambang batas ISPU. Jangan tutup mata demi keuntungan oligarki tambang!",
        "Warga Cilegon Keluhkan Debu PLTU Suralaya",
        "oppose",
        "negative"
      ),
      youtube(
        "pltu-yt-7",
        "Bapak saya kerja di PLTU sudah 15 tahun, kalau ditutup mendadak gimana nasib pekerja lokal?",
        "Pensiun Dini PLTU: Siapkah Jawa-Bali?",
        "support",
        "neutral"
      ),
      youtube(
        "pltu-yt-8",
        "Co-firing biomassa langkah bagus, setidaknya ada usaha kurangi batu bara.",
        "Gibran Tinjau Co-firing Biomassa di Suralaya",
        "support",
        "positive"
      ),
      youtube(
        "pltu-yt-9",
        "Nelayan di sekitar PLTU tangkapannya turun drastis sejak air buangan makin panas.",
        "Dampak PLTU bagi Nelayan Pesisir Utara Jawa",
        "oppose",
        "negative"
      ),
    ],
    news: [
      news(
        "pltu-news-1",
        "Presiden Prabowo Subianto menolak permintaan waktu dua pekan dari Menteri ESDM Bahlil Lahadalia untuk mencabut Izin Usaha Pertambangan (IUP) bermasalah di kawasan hutan lindung",
        "Tempo.co",
        ["Prabowo", "Bahlil"],
        "oppose",
        "Presiden memerintahkan penertiban cepat tanpa kompromi terhadap operasional batu bara ilegal demi menjaga keseimbangan ekosistem dan ketegasan hukum energi."
      ),
      news(
        "pltu-news-2",
        "Gibran Rakabuming Tinjau Kesiapan Transisi Co-firing Biomassa pada PLTU Suralaya untuk Turunkan Emisi Karbon",
        "Kompas",
        ["Gibran"],
        "support",
        "Pemerintah mendorong adopsi teknologi pencampuran biomassa bertahap agar keandalan listrik kawasan industri tetap aman sembari memangkas emisi karbon."
      ),
      news(
        "pltu-news-3",
        "Menteri ESDM Bahlil Lahadalia Paparkan Skema Pendanaan JETP dan Pensiun Dini PLTU Tua",
        "Detik Finance",
        ["Bahlil"],
        "neutral",
        "Kita tidak bisa langsung menutup PLTU tanpa kejelasan komitmen dana hibah internasional. Harus ada keadilan tarif bagi konsumen domestik."
      ),
      news(
        "pltu-news-4",
        "Kementerian LHK Temukan Pelanggaran Emisi Cerobong PLTU di Pesisir Utara Jawa, Sanksi Administratif Disiapkan",
        "Antara News",
        ["KLHK / Pemerintah"],
        "oppose",
        "Hasil pemantauan stasiun CEMS menunjukkan konsentrasi partikulat SO2 dan NOx melampaui baku mutu emisi selama tiga pekan berturut-turut."
      ),
      news(
        "pltu-news-5",
        "PLN Tegaskan Pengoperasian PLTU Modern Supercritical Tetap Diperlukan untuk Menjamin Beban Puncak Industri",
        "CNBC Indonesia",
        ["Direksi PLN"],
        "support",
        "Pembangkit batu bara berteknologi ultra-supercritical memiliki efisiensi termal tinggi dan dilengkapi electro-precipitator 99% debu tangkap."
      ),
      news(
        "pltu-news-6",
        "WALHI Desak Pemerintah Percepat Pensiun Dini PLTU Batu Bara di Banten",
        "CNN Indonesia",
        ["WALHI"],
        "oppose",
        "Setiap tahun penundaan berarti ribuan warga terus menghirup udara tercemar dari cerobong PLTU."
      ),
      news(
        "pltu-news-7",
        "DPR Minta Kajian Dampak Sosial Sebelum Penutupan PLTU Tua",
        "Kompas",
        ["DPR RI"],
        "neutral",
        "Penutupan pembangkit harus disertai rencana alih kerja bagi pekerja dan jaminan pasokan listrik daerah."
      ),
    ],
  },

  pltn: {
    youtube: [
      youtube(
        "pltn-yt-1",
        "Indonesia ini di cincin api, gempa tiap minggu. Bangun PLTN sama aja cari masalah.",
        "PLTN Pertama Indonesia: Aman atau Bahaya?",
        "oppose",
        "negative"
      ),
      youtube(
        "pltn-yt-2",
        "SMR itu teknologinya udah jauh lebih aman dari Fukushima, jangan takut duluan.",
        "Mengenal SMR, Reaktor Nuklir Mini",
        "support",
        "positive"
      ),
      youtube(
        "pltn-yt-3",
        "Yang penting SDM-nya disiapkan dulu, regulasinya juga harus jelas.",
        "BRIN Siapkan SDM Nuklir Nasional",
        "neutral",
        "neutral"
      ),
      youtube(
        "pltn-yt-4",
        "Limbah radioaktifnya mau dibuang ke mana? Ribuan tahun loh bahayanya.",
        "PLTN Pertama Indonesia: Aman atau Bahaya?",
        "oppose",
        "negative"
      ),
      youtube(
        "pltn-yt-5",
        "Kalau mau net zero 2060 ya mau gak mau nuklir harus masuk bauran energi.",
        "Net Zero 2060 dan Peran Energi Nuklir",
        "support",
        "positive"
      ),
      youtube(
        "pltn-yt-6",
        "Biaya bangunnya mahal banget, mending duitnya buat panel surya.",
        "Berapa Biaya Membangun PLTN?",
        "oppose",
        "negative"
      ),
      youtube(
        "pltn-yt-7",
        "Menarik, tapi lokasinya di mana dulu? Warga sekitar harus diajak bicara.",
        "Kalimantan Barat Kandidat Lokasi PLTN",
        "neutral",
        "neutral"
      ),
      youtube(
        "pltn-yt-8",
        "Korea Selatan bisa maju karena nuklir, kita juga pasti bisa asal serius.",
        "Mengenal SMR, Reaktor Nuklir Mini",
        "support",
        "positive"
      ),
    ],
    news: [
      news(
        "pltn-news-1",
        "BRIN Pastikan Teknologi Reaktor Generasi Baru Aman untuk Indonesia yang Berada di Zona Rawan Gempa",
        "Kompas",
        ["BRIN"],
        "support",
        "Reaktor generasi terbaru dirancang dengan sistem keselamatan pasif yang tetap bekerja tanpa pasokan listrik saat terjadi gempa."
      ),
      news(
        "pltn-news-2",
        "Greenpeace Tolak Pembangunan PLTN: Risiko Bencana Nuklir di Cincin Api Terlalu Besar",
        "Tempo.co",
        ["Greenpeace"],
        "oppose",
        "Indonesia tidak boleh mempertaruhkan keselamatan jutaan warga pada teknologi yang risikonya tidak bisa ditarik kembali."
      ),
      news(
        "pltn-news-3",
        "DPR Minta Pemerintah Lakukan Kajian Mendalam Sebelum Bangun PLTN Pertama",
        "Detik Finance",
        ["DPR RI"],
        "neutral",
        "Kajian tapak, kesiapan regulator, dan penerimaan masyarakat harus tuntas sebelum anggaran pembangunan disetujui."
      ),
      news(
        "pltn-news-4",
        "Kementerian ESDM: PLTN Kunci Capai Target Net Zero Emission 2060",
        "CNBC Indonesia",
        ["Kementerian ESDM", "Bahlil"],
        "support",
        "Tanpa pembangkit beban dasar rendah emisi seperti nuklir, target net zero 2060 sulit tercapai."
      ),
      news(
        "pltn-news-5",
        "IAEA Dukung Program Nuklir Indonesia dengan Asistensi Teknis Komprehensif",
        "Antara News",
        ["IAEA"],
        "support",
        "IAEA siap mendampingi Indonesia dalam 19 isu infrastruktur nuklir, mulai dari regulasi hingga pengelolaan limbah."
      ),
      news(
        "pltn-news-6",
        "WALHI: Dana PLTN Lebih Baik Dialihkan untuk Energi Surya dan Angin",
        "CNN Indonesia",
        ["WALHI"],
        "oppose",
        "Biaya pembangunan PLTN berlipat dari energi terbarukan, sementara waktu konstruksinya lebih dari satu dekade."
      ),
    ],
  },
};

// ============================================================================
// API Handler
// ============================================================================

export async function GET(request) {
  try {
    const { types, platforms } = queryToFilter(request.nextUrl.searchParams);

    const data = {};
    types.forEach((type) => {
      data[type] = {};
      platforms.forEach((platform) => {
        data[type][platform] = DATASET[type]?.[platform] ?? [];
      });
    });

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error fetching dataset:", error);
    return NextResponse.json({ error: "Failed to fetch dataset" }, { status: 500 });
  }
}
