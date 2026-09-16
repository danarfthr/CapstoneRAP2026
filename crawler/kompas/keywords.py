"""
Daftar query pencarian, dipakai bareng semua sumber (kompas/detik/cnn).

Format: (query, target)
  target -> "PLTN" | "PLTU" | "UMUM"
  dipakai untuk kuota sebaran tahun dan kolom `target` di tabel annotations.
"""

KEYWORDS = [
    # ---------------- PLTN / nuklir ----------------
    ("PLTN", "PLTN"),
    ("pembangkit listrik tenaga nuklir", "PLTN"),
    ("energi nuklir", "PLTN"),
    ("reaktor nuklir", "PLTN"),
    ("listrik tenaga nuklir", "PLTN"),
    ("PLTN Indonesia", "PLTN"),
    ("rencana pembangunan PLTN", "PLTN"),
    ("tolak PLTN", "PLTN"),
    ("penolakan PLTN", "PLTN"),
    ("PLTN Muria", "PLTN"),
    ("PLTN Bangka Belitung", "PLTN"),
    ("PLTN Kalimantan", "PLTN"),
    ("SMR reaktor modular", "PLTN"),
    ("small modular reactor", "PLTN"),
    ("reaktor daya eksperimental", "PLTN"),
    ("limbah radioaktif", "PLTN"),
    ("radiasi nuklir", "PLTN"),
    ("keselamatan nuklir", "PLTN"),
    ("uranium Indonesia", "PLTN"),
    ("thorium", "PLTN"),
    ("BATAN nuklir", "PLTN"),
    ("BAPETEN", "PLTN"),
    ("BRIN nuklir", "PLTN"),
    ("IAEA Indonesia", "PLTN"),
    ("kebijakan nuklir nasional", "PLTN"),

    # ---------------- PLTU / batu bara ----------------
    ("PLTU", "PLTU"),
    ("pembangkit listrik tenaga uap", "PLTU"),
    ("PLTU batu bara", "PLTU"),
    ("PLTU batubara", "PLTU"),
    ("pembangkit batu bara", "PLTU"),
    ("pensiun dini PLTU", "PLTU"),
    ("penghentian PLTU", "PLTU"),
    ("moratorium PLTU", "PLTU"),
    ("PLTU mangkrak", "PLTU"),
    ("emisi PLTU", "PLTU"),
    ("polusi PLTU", "PLTU"),
    ("pencemaran udara PLTU", "PLTU"),
    ("dampak kesehatan PLTU", "PLTU"),
    ("warga tolak PLTU", "PLTU"),
    ("PLTU Suralaya", "PLTU"),
    ("PLTU Paiton", "PLTU"),
    ("PLTU Cirebon", "PLTU"),
    ("PLTU Batang", "PLTU"),
    ("PLTU Celukan Bawang", "PLTU"),
    ("PLTU captive smelter", "PLTU"),
    ("co-firing biomassa PLTU", "PLTU"),
    ("ekspor batu bara listrik", "PLTU"),
    ("harga batu bara PLN", "PLTU"),

    # ---------------- lintas dua-duanya ----------------
    ("transisi energi Indonesia", "UMUM"),
    ("bauran energi nasional", "UMUM"),
    ("RUPTL PLN", "UMUM"),
    ("net zero emission Indonesia", "UMUM"),
    ("dekarbonisasi listrik", "UMUM"),
    ("JETP transisi energi", "UMUM"),
    ("krisis listrik Indonesia", "UMUM"),
]

# Buat uji coba pertama — 5 query saja biar cepat kelihatan kalau ada yang salah.
KEYWORDS_TEST = [
    ("PLTN", "PLTN"),
    ("PLTU", "PLTU"),
    ("pensiun dini PLTU", "PLTU"),
    ("energi nuklir", "PLTN"),
    ("transisi energi Indonesia", "UMUM"),
]