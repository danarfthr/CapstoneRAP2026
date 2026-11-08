KEYWORDS = [
    # PLTN / nuklir
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

    # PLTU / batu bara
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

    # lintas dua-duanya
    ("transisi energi Indonesia", "UMUM"),
    ("bauran energi nasional", "UMUM"),
    ("RUPTL PLN", "UMUM"),
    ("net zero emission Indonesia", "UMUM"),
    ("dekarbonisasi listrik", "UMUM"),
    ("JETP transisi energi", "UMUM"),
    ("krisis listrik Indonesia", "UMUM"),
]


# Buat uji coba pertama - 5 query saja biar cepat kelihatan kalau ada yang salah.
KEYWORDS_TEST = [
    ("PLTN", "PLTN"),
    ("PLTU", "PLTU"),
    ("pensiun dini PLTU", "PLTU"),
    ("energi nuklir", "PLTN"),
    ("transisi energi Indonesia", "UMUM"),
]

# --- Override dari crawl_worker.py / dashboard (lewat environment variable) ---
# CRAWL_KEYWORDS    = JSON list query yang boleh dipakai, mis. '["PLTU","PLTN"]'
# CRAWL_START_DATE  = "YYYY-MM-DD", CRAWL_END_DATE = "YYYY-MM-DD"
# Kalau tidak di-set, perilakunya sama persis seperti sebelumnya.
import json as _json
import os as _os

_env_kw = _os.getenv("CRAWL_KEYWORDS")
if _env_kw:
    _wanted = set(_json.loads(_env_kw))
    KEYWORDS = [(q, t) for q, t in KEYWORDS if q in _wanted]

# Lookup cepat query -> target, dipakai crawler yang menandai target setelah fetch.
KEYWORD_TARGET_MAP = dict(KEYWORDS)

# Rentang tahun crawling yang dipakai bareng semua sumber.
START_YEAR = 2021
END_YEAR = 2026
START_DATE = f"{START_YEAR}-01-01"
END_DATE = f"{END_YEAR}-12-31"

# Override rentang tanggal dari environment (dipakai crawl_worker.py).
# Catatan: crawler memfilter per TAHUN, jadi rentang ini berlaku kasar (per tahun).
START_DATE = _os.getenv("CRAWL_START_DATE") or START_DATE
END_DATE = _os.getenv("CRAWL_END_DATE") or END_DATE
START_YEAR = int(START_DATE[:4])
END_YEAR = int(END_DATE[:4])
