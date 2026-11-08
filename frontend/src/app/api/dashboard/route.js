/**
 * GET /api/dashboard
 *
 * Endpoint utama untuk mengambil seluruh data dashboard analisis sentimen & stance.
 * Saat ini menggunakan data dummy. Backend developer bisa mengganti isi response
 * ini dengan query ke database (misalnya PostgreSQL, MongoDB, dsb.).
 *
 * Dashboard memanggil endpoint ini dengan filter dari pop-up, contoh:
 *   /api/dashboard?types=pltu,pltn&platforms=youtube,news&range=3m
 *   /api/dashboard?types=pltu&from=2025-01-01&to=2025-06-30
 * Filter dibaca dengan queryToFilter() di src/lib/analysisFilter.js.
 * Saat ini filter BELUM dipakai untuk menyaring data dummy.
 */

import { NextResponse } from "next/server";

// ============================================================================
// DUMMY DATA — Ganti bagian ini dengan query database Anda
// ============================================================================

const pltuData = {
  title: "PLTU Public Analysis",
  description:
    "Public perception and discussion insights surrounding coal-fired power plants based on multi-platform social listening data.",

  // -- Sentiment Distribution (YouTube comments) --
  sentimentDistribution: {
    positive: { count: 576, percentage: 15 },
    negative: { count: 2496, percentage: 65 },
    neutral: { count: 768, percentage: 20 },
    total: 3845,
  },

  // -- Stance Distribution (News articles) --
  stanceDistribution: {
    support: { count: 225, percentage: 15 },
    against: { count: 900, percentage: 60 },
    neutral: { count: 375, percentage: 25 },
    total: 1500,
  },

  // -- Top Discussion Topics & Sentiment (per sentimen: negative, neutral, positive) --
  topDiscussionTopics: {
    negative: [
      { rank: 1, topic: "Air Pollution", mentions: 34200 },
      { rank: 2, topic: "Health Impacts", mentions: 28100 },
      { rank: 3, topic: "Carbon Emissions", mentions: 22500 },
      { rank: 4, topic: "Coal Ash Disposal", mentions: 15800 },
    ],
    neutral: [
      { rank: 1, topic: "Kebijakan Energi", mentions: 31500 },
      { rank: 2, topic: "Transisi Energi", mentions: 25200 },
      { rank: 3, topic: "Kapasitas Listrik", mentions: 19800 },
      { rank: 4, topic: "Regulasi Emisi", mentions: 14300 },
    ],
    positive: [
      { rank: 1, topic: "Ketersediaan Listrik", mentions: 26800 },
      { rank: 2, topic: "Lapangan Kerja", mentions: 21400 },
      { rank: 3, topic: "Ekonomi Daerah", mentions: 17600 },
      { rank: 4, topic: "Infrastruktur Energi", mentions: 12900 },
    ],
  },

  // -- Top Discussion Topics & Stance (per stance: oppose, neutral, support) --
  // Dipakai saat user hanya memilih platform News
  topDiscussionTopicsByStance: {
    oppose: [
      { rank: 1, topic: "Polusi Udara", mentions: 12400 },
      { rank: 2, topic: "Dampak Kesehatan", mentions: 9800 },
      { rank: 3, topic: "Emisi Karbon", mentions: 7600 },
      { rank: 4, topic: "Limbah Abu Batu Bara", mentions: 5100 },
    ],
    neutral: [
      { rank: 1, topic: "Kebijakan Energi", mentions: 10200 },
      { rank: 2, topic: "Transisi Energi", mentions: 8700 },
      { rank: 3, topic: "Regulasi Emisi", mentions: 6300 },
      { rank: 4, topic: "Kapasitas Listrik", mentions: 4900 },
    ],
    support: [
      { rank: 1, topic: "Ketersediaan Listrik", mentions: 9300 },
      { rank: 2, topic: "Ekonomi Daerah", mentions: 7100 },
      { rank: 3, topic: "Lapangan Kerja", mentions: 5800 },
      { rank: 4, topic: "Harga Listrik Terjangkau", mentions: 4200 },
    ],
  },

  // -- Top Actor in News (per sentimen: negative, neutral, positive) --
  topActorSummary: {
    negative: [
      { rank: 1, name: "Prabowo", mentions: 34200 },
      { rank: 2, name: "Bahlil", mentions: 28100 },
      { rank: 3, name: "Gibran", mentions: 22500 },
      { rank: 4, name: "Buna Teddy", mentions: 15800 },
    ],
    neutral: [
      { rank: 1, name: "PLN", mentions: 30500 },
      { rank: 2, name: "DPR RI", mentions: 24200 },
      { rank: 3, name: "Kementerian ESDM", mentions: 18900 },
      { rank: 4, name: "BAPPENAS", mentions: 13400 },
    ],
    positive: [
      { rank: 1, name: "Jokowi", mentions: 28900 },
      { rank: 2, name: "Kementerian ESDM", mentions: 23100 },
      { rank: 3, name: "PLN", mentions: 19500 },
      { rank: 4, name: "Greenpeace", mentions: 14200 },
    ],
  },

  // -- Top Actor in News (per stance: oppose, neutral, support) --
  // Dipakai saat user hanya memilih platform News
  topActorSummaryByStance: {
    oppose: [
      { rank: 1, name: "Greenpeace", mentions: 11800 },
      { rank: 2, name: "WALHI", mentions: 9400 },
      { rank: 3, name: "Warga Suralaya", mentions: 6900 },
      { rank: 4, name: "Trend Asia", mentions: 5200 },
    ],
    neutral: [
      { rank: 1, name: "Kementerian ESDM", mentions: 10600 },
      { rank: 2, name: "DPR RI", mentions: 8300 },
      { rank: 3, name: "BAPPENAS", mentions: 6100 },
      { rank: 4, name: "Gibran", mentions: 4700 },
    ],
    support: [
      { rank: 1, name: "Bahlil", mentions: 12900 },
      { rank: 2, name: "PLN", mentions: 10100 },
      { rank: 3, name: "Prabowo", mentions: 8600 },
      { rank: 4, name: "APBI", mentions: 5300 },
    ],
  },

  // -- Stance Sources (persentase per sumber + breakdown sentimen) --
  stanceSources: {
    // Persentase overall dari tiap sumber
    sourcePercentage: [
      { source: "YouTube", percentage: 30 },
      { source: "News", percentage: 20 },
    ],
    // Breakdown sentimen per sumber (positive, neutral, negative — semua dalam %)
    sourceBreakdown: [
      { source: "YouTube", positive: 20, neutral: 40, negative: 40 },
      { source: "News", positive: 20, neutral: 60, negative: 20 },
    ],
  },

  // -- Top Actor in News (detail per aktor) --
  // Setiap aktor punya daftar berita + stance
  topActorDetail: {
    actors: ["Prabowo", "Bahlil", "Gibran", "Buna Teddy", "PLN"],
    newsPerActor: {
      Prabowo: [
        {
          news: "Presiden Prabowo Subianto menolak permintaan waktu dua pekan dari Menteri ESDM Bahlil Lahadalia untuk mencabut Izin Usaha Pertambangan (IUP) bermasalah di kawasan hutan lindung",
          stance: "oppose",
        },
        {
          news: "Londo irenggg",
          stance: "neutral",
        },
        {
          news: "Prabowo Siapkan BLU Beli Batu Bara-Gas untuk Listrik, Ini Bocorannya",
          stance: "support",
        },
        {
          news: "MBG bermanfaat tidakkkkkk",
          stance: "oppose",
        },
      ],
      Bahlil: [
        {
          news: "Menteri ESDM Bahlil Lahadalia diminta tegas soal pencabutan IUP ilegal di kawasan hutan",
          stance: "oppose",
        },
        {
          news: "Bahlil targetkan bauran energi terbarukan capai 23% di 2025",
          stance: "support",
        },
        {
          news: "Bahlil: Transisi energi harus realistis, tidak bisa instan",
          stance: "neutral",
        },
      ],
      Gibran: [
        {
          news: "Gibran dukung percepatan transisi energi bersih di Solo",
          stance: "support",
        },
        {
          news: "Gibran soal PLTU: perlu dikaji dampak lingkungannya",
          stance: "neutral",
        },
      ],
      "Buna Teddy": [
        {
          news: "Dirut PLN Buna Teddy paparkan roadmap pensiun dini PLTU batu bara",
          stance: "support",
        },
        {
          news: "PLN di bawah Buna Teddy siapkan investasi besar untuk EBT",
          stance: "support",
        },
        {
          news: "Buna Teddy akui tarif listrik sulit turun selama PLTU dominan",
          stance: "oppose",
        },
      ],
      PLN: [
        {
          news: "PLN berencana pensiunkan 5 unit PLTU tua tahun depan",
          stance: "support",
        },
        {
          news: "PLN pastikan pasokan listrik tetap stabil meski kurangi PLTU",
          stance: "neutral",
        },
        {
          news: "PLN minta subsidi pemerintah untuk transisi dari PLTU ke EBT",
          stance: "neutral",
        },
      ],
    },
  },

  // -- Most Discussed Specific Topics --
  // avgSentiment dari komentar YouTube, stance dari berita (dipakai saat hanya News)
  mostDiscussedTopics: [
    {
      topic: "Impact of PM2.5 emissions on surrounding residential areas",
      avgSentiment: "negative",
      stance: "oppose",
    },
    {
      topic: "New filter technology installation timeline and costs",
      avgSentiment: "neutral",
      stance: "neutral",
    },
    {
      topic: "Employment opportunities for local engineering graduates",
      avgSentiment: "positive",
      stance: "support",
    },
    {
      topic: "Water usage and potential thermal pollution in local rivers",
      avgSentiment: "negative",
      stance: "oppose",
    },
  ],

  // -- Sentiment & Stance Breakdown --
  sentimentStanceBreakdown: {
    data: [
      {
        commentNews: "Impact of PM2.5 emissions on surrounding residential areas",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "New filter technology installation timeline and costs",
        stance: "neutral",
        avgSentiment: "neutral",
      },
      {
        commentNews: "Employment opportunities for local engineering graduates",
        stance: "support",
        avgSentiment: "positive",
      },
      {
        commentNews: "Water usage and potential thermal pollution in local rivers",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "Rencana penutupan PLTU Suralaya memicu perdebatan",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "Subsidi pemerintah untuk energi fosil dikritik banyak pihak",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "Program CSR PLTU di Banten diapresiasi warga",
        stance: "support",
        avgSentiment: "positive",
      },
      {
        commentNews: "Pemerintah perlu roadmap realistis untuk transisi energi",
        stance: "neutral",
        avgSentiment: "neutral",
      },
    ],
    totalPages: 50,
    perPage: 4,
  },
};

const pltnData = {
  title: "PLTN Public Analysis",
  description:
    "Public perception and discussion insights surrounding coal-fired power plants based on multi-platform social listening data.",

  // -- Sentiment Distribution --
  sentimentDistribution: {
    positive: { count: 1820, percentage: 42.8 },
    negative: { count: 1150, percentage: 27.1 },
    neutral: { count: 1280, percentage: 30.1 },
    total: 4250,
  },

  // -- Stance Distribution --
  stanceDistribution: {
    support: { count: 580, percentage: 41.4 },
    against: { count: 450, percentage: 32.1 },
    neutral: { count: 370, percentage: 26.4 },
    total: 1400,
  },

  // -- Top Discussion Topics --
  topDiscussionTopics: {
    negative: [
      { rank: 1, topic: "Keamanan Nuklir", mentions: 38500 },
      { rank: 2, topic: "Limbah Radioaktif", mentions: 29200 },
      { rank: 3, topic: "Risiko Gempa", mentions: 24100 },
      { rank: 4, topic: "Biaya Pembangunan", mentions: 18700 },
    ],
    neutral: [
      { rank: 1, topic: "Regulasi Nuklir", mentions: 32000 },
      { rank: 2, topic: "Teknologi SMR", mentions: 26800 },
      { rank: 3, topic: "Lokasi Kandidat", mentions: 21500 },
      { rank: 4, topic: "SDM Nuklir", mentions: 16200 },
    ],
    positive: [
      { rank: 1, topic: "Energi Bersih", mentions: 41200 },
      { rank: 2, topic: "Net Zero 2060", mentions: 33500 },
      { rank: 3, topic: "Kapasitas Besar", mentions: 25800 },
      { rank: 4, topic: "Dukungan IAEA", mentions: 19400 },
    ],
  },

  // -- Top Discussion Topics & Stance (dipakai saat user hanya memilih News) --
  topDiscussionTopicsByStance: {
    oppose: [
      { rank: 1, topic: "Keamanan Nuklir", mentions: 13600 },
      { rank: 2, topic: "Limbah Radioaktif", mentions: 10900 },
      { rank: 3, topic: "Risiko Gempa", mentions: 8200 },
      { rank: 4, topic: "Biaya Pembangunan", mentions: 6400 },
    ],
    neutral: [
      { rank: 1, topic: "Regulasi Nuklir", mentions: 11500 },
      { rank: 2, topic: "Lokasi Kandidat", mentions: 8800 },
      { rank: 3, topic: "SDM Nuklir", mentions: 6900 },
      { rank: 4, topic: "Teknologi SMR", mentions: 5300 },
    ],
    support: [
      { rank: 1, topic: "Energi Bersih", mentions: 14800 },
      { rank: 2, topic: "Net Zero 2060", mentions: 11200 },
      { rank: 3, topic: "Dukungan IAEA", mentions: 7700 },
      { rank: 4, topic: "Kapasitas Besar", mentions: 6100 },
    ],
  },

  // -- Top Actor in News --
  topActorSummary: {
    negative: [
      { rank: 1, name: "Greenpeace", mentions: 31200 },
      { rank: 2, name: "WALHI", mentions: 24800 },
      { rank: 3, name: "Warga Lokal", mentions: 19500 },
      { rank: 4, name: "Aktivis Lingkungan", mentions: 14100 },
    ],
    neutral: [
      { rank: 1, name: "DPR RI", mentions: 28500 },
      { rank: 2, name: "Kementerian ESDM", mentions: 23200 },
      { rank: 3, name: "BAPPENAS", mentions: 17800 },
      { rank: 4, name: "Akademisi", mentions: 13500 },
    ],
    positive: [
      { rank: 1, name: "BRIN", mentions: 35800 },
      { rank: 2, name: "IAEA", mentions: 29400 },
      { rank: 3, name: "Kementerian ESDM", mentions: 24100 },
      { rank: 4, name: "Prabowo", mentions: 18600 },
    ],
  },

  // -- Top Actor in News per stance (dipakai saat user hanya memilih News) --
  topActorSummaryByStance: {
    oppose: [
      { rank: 1, name: "WALHI", mentions: 10400 },
      { rank: 2, name: "Greenpeace", mentions: 8700 },
      { rank: 3, name: "Warga Lokasi Kandidat", mentions: 6200 },
      { rank: 4, name: "Jatam", mentions: 4100 },
    ],
    neutral: [
      { rank: 1, name: "DPR RI", mentions: 9600 },
      { rank: 2, name: "BAPETEN", mentions: 7800 },
      { rank: 3, name: "Kementerian ESDM", mentions: 6500 },
      { rank: 4, name: "PLN", mentions: 4800 },
    ],
    support: [
      { rank: 1, name: "BRIN", mentions: 13200 },
      { rank: 2, name: "Bahlil", mentions: 10500 },
      { rank: 3, name: "IAEA", mentions: 7900 },
      { rank: 4, name: "Prabowo", mentions: 6300 },
    ],
  },

  // -- Stance Sources --
  stanceSources: {
    sourcePercentage: [
      { source: "YouTube", percentage: 35 },
      { source: "News", percentage: 25 },
    ],
    sourceBreakdown: [
      { source: "YouTube", positive: 25, neutral: 45, negative: 30 },
      { source: "News", positive: 20, neutral: 48, negative: 32 },
    ],
  },

  // -- Top Actor Detail --
  topActorDetail: {
    actors: ["BRIN", "IAEA", "Greenpeace", "DPR RI", "Kementerian ESDM"],
    newsPerActor: {
      BRIN: [
        {
          news: "BRIN pastikan teknologi reaktor generasi baru aman untuk Indonesia yang berada di zona rawan gempa",
          stance: "support",
        },
        {
          news: "BRIN kirim 50 peneliti muda untuk pelatihan nuklir di Korea Selatan",
          stance: "support",
        },
        {
          news: "BRIN: Indonesia butuh minimal 10 tahun untuk siapkan SDM nuklir berkualitas",
          stance: "neutral",
        },
      ],
      IAEA: [
        {
          news: "IAEA dukung program nuklir Indonesia dengan asistensi teknis komprehensif",
          stance: "support",
        },
        {
          news: "IAEA: Indonesia perlu perkuat regulasi keselamatan nuklir sebelum bangun PLTN",
          stance: "neutral",
        },
      ],
      Greenpeace: [
        {
          news: "Greenpeace tolak pembangunan PLTN: risiko bencana nuklir di cincin api terlalu besar",
          stance: "oppose",
        },
        {
          news: "Greenpeace: Dana PLTN lebih baik dialihkan untuk solar panel dan angin",
          stance: "oppose",
        },
        {
          news: "Greenpeace ajukan petisi menolak PLTN yang ditandatangani 500 ribu warga",
          stance: "oppose",
        },
      ],
      "DPR RI": [
        {
          news: "DPR minta pemerintah lakukan kajian mendalam sebelum bangun PLTN pertama",
          stance: "neutral",
        },
        {
          news: "Komisi VII DPR gelar rapat dengar pendapat soal RUU Energi Nuklir",
          stance: "neutral",
        },
        {
          news: "Anggota DPR dari fraksi oposisi tolak anggaran PLTN di RAPBN 2027",
          stance: "oppose",
        },
      ],
      "Kementerian ESDM": [
        {
          news: "Kementerian ESDM: PLTN kunci capai target Net Zero Emission 2060",
          stance: "support",
        },
        {
          news: "Kementerian ESDM bentuk tim khusus kajian kelayakan PLTN",
          stance: "neutral",
        },
        {
          news: "Kementerian ESDM: Lokasi PLTN pertama di Kalimantan Barat masih dikaji",
          stance: "neutral",
        },
      ],
    },
  },

  // -- Most Discussed Specific Topics --
  // avgSentiment dari komentar YouTube, stance dari berita (dipakai saat hanya News)
  mostDiscussedTopics: [
    {
      topic: "Risiko gempa dan tsunami terhadap keselamatan PLTN",
      avgSentiment: "negative",
      stance: "oppose",
    },
    {
      topic: "Teknologi SMR sebagai alternatif PLTN konvensional",
      avgSentiment: "positive",
      stance: "support",
    },
    {
      topic: "Kesiapan SDM dan regulasi nuklir Indonesia",
      avgSentiment: "neutral",
      stance: "neutral",
    },
    {
      topic: "Perbandingan biaya PLTN vs energi terbarukan lainnya",
      avgSentiment: "negative",
      stance: "oppose",
    },
  ],

  // -- Sentiment & Stance Breakdown --
  sentimentStanceBreakdown: {
    data: [
      {
        commentNews: "Risiko gempa dan tsunami terhadap keselamatan PLTN",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "Teknologi SMR lebih aman dan fleksibel untuk Indonesia",
        stance: "support",
        avgSentiment: "positive",
      },
      {
        commentNews: "Kesiapan SDM nuklir Indonesia masih perlu ditingkatkan",
        stance: "neutral",
        avgSentiment: "neutral",
      },
      {
        commentNews: "PLTN bisa bantu Indonesia capai Net Zero 2060",
        stance: "support",
        avgSentiment: "positive",
      },
      {
        commentNews: "Limbah radioaktif PLTN berbahaya untuk ribuan tahun",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "IAEA siap bantu Indonesia kembangkan nuklir damai",
        stance: "support",
        avgSentiment: "positive",
      },
      {
        commentNews: "Masyarakat sekitar lokasi kandidat PLTN khawatir dampak radiasi",
        stance: "oppose",
        avgSentiment: "negative",
      },
      {
        commentNews: "Investasi PLTN menciptakan lapangan kerja teknologi tinggi",
        stance: "support",
        avgSentiment: "positive",
      },
    ],
    totalPages: 50,
    perPage: 4,
  },
};

// ============================================================================
// API Handler
// ============================================================================

export async function GET() {
  try {
    const data = {
      pltu: pltuData,
      pltn: pltnData,
      lastUpdated: new Date().toISOString(),
    };

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error fetching dashboard data:", error);
    return NextResponse.json(
      { error: "Failed to fetch dashboard data" },
      { status: 500 }
    );
  }
}
