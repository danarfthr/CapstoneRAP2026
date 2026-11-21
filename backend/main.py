import calendar
import math
import os
from contextlib import contextmanager
from datetime import date
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
DEFAULT_LABELER = os.getenv("DEFAULT_LABELER", "final")

app = FastAPI(title="PLTU vs PLTN Opinion Dashboard API")

#Before the public test set ALLOWED_ORIGINS to the real dashboard address.
ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET"], allow_headers=["*"])

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set in .env")
        _pool = SimpleConnectionPool(1, 5, DATABASE_URL)
    return _pool


@contextmanager
def cursor():
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
    finally:
        pool.putconn(conn)


def query(sql, params=None):
    with cursor() as cur:
        cur.execute(sql, params or {})
        return cur.fetchall()



#Shared filters: labeler + topic (PLTU/PLTN/UMUM) + date range
Labeler = Query(DEFAULT_LABELER, description="Labeler name, e.g. final, arin, jessy")
TargetQ = Query(None, pattern="^(PLTN|PLTU|UMUM)$", description="Topic: PLTU, PLTN or UMUM (empty = all)")
DateFrom = Query(None, description="First day, YYYY-MM-DD (inclusive)")
DateTo = Query(None, description="Last day, YYYY-MM-DD (inclusive)")


def _check_dates(date_from, date_to):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be on or before date_to")


def filters(
    labeler: str = Labeler,
    target: Optional[str] = TargetQ,
    date_from: Optional[date] = DateFrom,
    date_to: Optional[date] = DateTo,
) -> dict:
    _check_dates(date_from, date_to)
    return {"labeler": labeler, "target": target, "date_from": date_from, "date_to": date_to}


#SQL fragment used by every endpoint that reads a *_detail view
WHERE = """labeler = %(labeler)s
  and (%(target)s::text is null or target_code = %(target)s)
  and (%(date_from)s::date is null or item_date >= %(date_from)s)
  and (%(date_to)s::date is null or item_date <= %(date_to)s)"""

#Basics
@app.get("/api/health")
def health():
    """Check that the API can reach the database."""
    return {"ok": query("select 1 as ok")[0]["ok"] == 1}


@app.get("/api/labelers")
def labelers():
    """List labelers so the dashboard can offer a dropdown."""
    return query("select name, labeler_type, task from ref.labeler order by name")


@app.get("/api/overview")
def overview(labeler: str = Labeler):
    """Headline numbers, per-source and per-topic counts, and date ranges."""
    totals = query(
        """
        select
          (select count(*) from bronze.news_article)  as n_articles,
          (select count(*) from bronze.yt_video)      as n_videos,
          (select count(*) from bronze.yt_comment)    as n_comments,
          (select count(*) from gold.yt_comment_label g
             join ref.labeler b on b.labeler_id = g.labeler_id
             where b.name = %(labeler)s)              as n_labeled_comments,
          (select count(*) from gold.news_actor_stance s
             join ref.labeler b on b.labeler_id = s.labeler_id
             where b.name = %(labeler)s)              as n_actor_stances
        """,
        {"labeler": labeler},
    )[0]
    by_source = query(
        """select source_id, count(*) as n_articles
           from bronze.news_article group by source_id order by n_articles desc"""
    )
    by_target = query(
        """select target_code,
                  sum(n_articles)::int as n_articles,
                  sum(n_videos)::int   as n_videos,
                  sum(n_comments)::int as n_comments
           from public.v_topic_keywords group by target_code order by target_code"""
    )
    ranges = query(
        """select (select min(published_at) from bronze.news_article) as first_article,
                  (select max(published_at) from bronze.news_article) as last_article,
                  (select min(published_at) from bronze.yt_comment)   as first_comment,
                  (select max(published_at) from bronze.yt_comment)   as last_comment"""
    )[0]
    return {"labeler": labeler, "totals": totals, "articles_by_source": by_source,
            "by_target": by_target, "date_range": ranges}


#real topic modelling would need its own table, keywords are the stand-in for now.
@app.get("/api/topics")
def topics(
    target: Optional[str] = TargetQ,
    by: str = Query("comments", pattern="^(articles|videos|comments)$", description="Rank by"),
    limit: int = Query(20, ge=1, le=100),
):
    """Keywords ranked by how much data they found."""
    col = {"articles": "n_articles", "videos": "n_videos", "comments": "n_comments"}[by]
    return query(
        f"""select keyword, target_code, n_articles, n_videos, n_comments
            from public.v_topic_keywords
            where (%(target)s::text is null or target_code = %(target)s)
            order by {col} desc, keyword
            limit %(limit)s""",
        {"target": target, "limit": limit},
    )


#YouTube comments: sentiment + stance
@app.get("/api/yt/sentiment/summary")
def yt_sentiment_summary(f: dict = Depends(filters)):
    """Comments per sentiment (positive/neutral/negative) with percentage."""
    return query(
        f"""select sentiment, count(*)::int as n_comments,
                   round(100.0 * count(*) / sum(count(*)) over (), 1) as pct
            from public.v_yt_label_detail
            where {WHERE} and sentiment is not null
            group by sentiment order by sentiment""", f)


@app.get("/api/yt/sentiment/monthly")
def yt_sentiment_monthly(f: dict = Depends(filters)):
    """Comments per sentiment per month."""
    return query(
        f"""select date_trunc('month', item_date)::date as month, sentiment, count(*)::int as n_comments
            from public.v_yt_label_detail
            where {WHERE} and sentiment is not null
            group by 1, 2 order by 1, 2""", f)


@app.get("/api/yt/stance/summary")
def yt_stance_summary(f: dict = Depends(filters)):
    """Comments per stance (support/neutral/oppose) with percentage."""
    return query(
        f"""select stance, count(*)::int as n_comments,
                   round(100.0 * count(*) / sum(count(*)) over (), 1) as pct
            from public.v_yt_label_detail
            where {WHERE} and stance is not null
            group by stance order by stance""", f)


@app.get("/api/yt/stance/monthly")
def yt_stance_monthly(f: dict = Depends(filters)):
    """Comments per stance per month."""
    return query(
        f"""select date_trunc('month', item_date)::date as month, stance, count(*)::int as n_comments
            from public.v_yt_label_detail
            where {WHERE} and stance is not null
            group by 1, 2 order by 1, 2""", f)


@app.get("/api/yt/stance-vs-sentiment")
def yt_stance_vs_sentiment(f: dict = Depends(filters)):
    """Cross-table: every stance + sentiment combination."""
    return query(
        f"""select stance, sentiment, count(*)::int as n_comments
            from public.v_yt_label_detail
            where {WHERE} and stance is not null and sentiment is not null
            group by 1, 2 order by 1, 2""", f)


#News articles: stance per actor
@app.get("/api/news/stance/summary")
def news_stance_summary(f: dict = Depends(filters)):
    """Actor stances per stance (support/neutral/oppose) with percentage."""
    return query(
        f"""select stance, count(*)::int as n_stances,
                   count(distinct article_id)::int as n_articles,
                   round(100.0 * count(*) / sum(count(*)) over (), 1) as pct
            from public.v_news_stance_detail
            where {WHERE} and stance is not null
            group by stance order by stance""", f)


@app.get("/api/news/stance/monthly")
def news_stance_monthly(f: dict = Depends(filters)):
    """Actor stances per month."""
    return query(
        f"""select date_trunc('month', item_date)::date as month, stance, count(*)::int as n_stances
            from public.v_news_stance_detail
            where {WHERE} and stance is not null
            group by 1, 2 order by 1, 2""", f)


@app.get("/api/news/stance-by-actor")
def news_stance_by_actor(f: dict = Depends(filters), limit: int = Query(20, ge=1, le=100)):
    """Stance counts for the top N most-mentioned actors."""
    return query(
        f"""with scoped as (
              select actor_name, actor_role, stance
              from public.v_news_stance_detail
              where {WHERE} and stance is not null
            ),
            top as (
              select actor_name, count(*) as total
              from scoped group by actor_name order by total desc, actor_name limit %(limit)s
            )
            select s.actor_name, s.actor_role, s.stance, count(*)::int as n_stances
            from scoped s join top t on t.actor_name = s.actor_name
            group by s.actor_name, s.actor_role, s.stance, t.total
            order by t.total desc, s.actor_name, s.stance""",
        {**f, "limit": limit})


@app.get("/api/news/stance-by-actor/monthly")
def news_stance_by_actor_monthly(f: dict = Depends(filters), actor: Optional[str] = None):
    """Stance per month, optionally for one actor (exact actor_name)."""
    return query(
        f"""select date_trunc('month', item_date)::date as month, actor_name, stance,
                   count(*)::int as n_stances
            from public.v_news_stance_detail
            where {WHERE} and stance is not null
              and (%(actor)s::text is null or actor_name = %(actor)s)
            group by 1, 2, 3 order by 1, 2, 3""",
        {**f, "actor": actor})


@app.get("/api/news/volume")
def news_volume(
    target: Optional[str] = TargetQ,
    source: Optional[str] = None,
    date_from: Optional[date] = DateFrom,
    date_to: Optional[date] = DateTo,
):
    """Articles per month (all collected articles), by source and topic."""
    _check_dates(date_from, date_to)
    return query(
        """select month, source_id, target_code, n_articles
           from public.v_news_volume_monthly
           where (%(target)s::text is null or target_code = %(target)s)
             and (%(source)s::text is null or source_id = %(source)s)
             and (%(date_from)s::date is null or month >= date_trunc('month', %(date_from)s::date))
             and (%(date_to)s::date   is null or month <= %(date_to)s::date)
           order by month, source_id""",
        {"target": target, "source": source, "date_from": date_from, "date_to": date_to})


#Dashboard comparison page (PLTU vs PLTN). Returns the same three distributions for both topics, with percentages per topic so the two can be drawn side by side.
@app.get("/api/compare")
def compare(
    labeler: str = Labeler,
    date_from: Optional[date] = DateFrom,
    date_to: Optional[date] = DateTo,
):
    """YouTube sentiment, YouTube stance and news stance for PLTU vs PLTN."""
    _check_dates(date_from, date_to)
    p = {"labeler": labeler, "target": None, "date_from": date_from, "date_to": date_to}
    scope = WHERE + " and target_code in ('PLTU', 'PLTN')"

    def dist(view, col, count_col):
        return query(
            f"""select target_code, {col}, count(*)::int as {count_col},
                       round(100.0 * count(*) / sum(count(*)) over (partition by target_code), 1) as pct
                from public.{view}
                where {scope} and {col} is not null
                group by target_code, {col} order by target_code, {col}""", p)

    return {
        "labeler": labeler,
        "yt_sentiment": dist("v_yt_label_detail", "sentiment", "n_comments"),
        "yt_stance": dist("v_yt_label_detail", "stance", "n_comments"),
        "news_stance": dist("v_news_stance_detail", "stance", "n_stances"),
    }

#new endpoints for frontend Node.js
PLANT_TYPES = ("pltu", "pltn") 
PLATFORMS = ("youtube", "news")
STANCE_TO_SENTIMENT = {"support": "positive", "neutral": "neutral", "oppose": "negative"}
SENTIMENT_TO_SCORE = "case sentiment when 'positive' then 1 when 'negative' then -1 else 0 end"
STANCE_TO_SCORE = "case stance when 'support' then 1 when 'oppose' then -1 else 0 end"
 
SECTION_TEXT = {
    "pltu": "Public perception and discussion insights surrounding coal-fired power plants (PLTU), "
            "based on YouTube comments and national news articles.",
    "pltn": "Public perception and discussion insights surrounding nuclear power plants (PLTN), "
            "based on YouTube comments and national news articles.",
}
 
 
def _pick(value: Optional[str], allowed) -> List[str]:
    """'pltu,PLTN' -> ['pltu', 'pltn'] (unknown values dropped; empty = everything)."""
    wanted = {v.strip().lower() for v in (value or "").split(",")}
    picked = [a for a in allowed if a in wanted]
    return picked or list(allowed)
 
 
def _resolve_dates(range_: Optional[str], date_from, date_to, labeler: str):
    """Explicit from/to win. '3m'/'6m' count back from the newest labeled item
    (not from today), because the collected data stops at a fixed date."""
    _check_dates(date_from, date_to)
    if date_from or date_to:
        return date_from, date_to
    months = {"3m": 3, "6m": 6}.get(range_)
    if not months:
        return None, None
    anchor = query(
        """select max(d) as d from (
             select item_date as d from public.v_yt_rows   where labeler = %(l)s
             union all
             select item_date      from public.v_news_rows where labeler = %(l)s) x""",
        {"l": labeler})[0]["d"] or date.today()
    anchor = min(anchor, date.today())
    year, month = anchor.year, anchor.month - months
    while month < 1:
        month, year = month + 12, year - 1
    start = date(year, month, min(anchor.day, calendar.monthrange(year, month)[1]))
    return start, anchor
 
 
def _dist(counts: Dict[str, int], keys) -> dict:
    total = sum(counts.get(k, 0) for k in keys)
    out = {k: {"count": counts.get(k, 0),
               "percentage": round(100.0 * counts.get(k, 0) / total, 1) if total else 0} for k in keys}
    out["total"] = total
    return out
 
 
def _ranked(rows, group_key: str, label_key: str, groups, name: str, limit: int = 5) -> dict:
    """rows: [{group_key, label_key, n}] -> {group: [{rank, name, mentions}]} (top `limit` per group)."""
    out = {g: [] for g in groups}
    for r in sorted(rows, key=lambda r: (-r["n"], r[label_key])):
        bucket = out.get(r[group_key])
        if bucket is not None and len(bucket) < limit:
            bucket.append({"rank": len(bucket) + 1, name: r[label_key], "mentions": r["n"]})
    return out
 
 
def _score_label(score, positive: str, negative: str, neutral: str = "neutral"):
    if score is None:
        return None
    return positive if score >= 0.2 else negative if score <= -0.2 else neutral
 
 
def _clip(text: Optional[str], n: int = 220) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "..."
 
 
def _section(plant: str, labeler: str, d_from, d_to, platforms: List[str]) -> dict:
    p = {"labeler": labeler, "target": plant.upper(), "date_from": d_from, "date_to": d_to}
    yt, nw = "youtube" in platforms, "news" in platforms
    rows = lambda sql: query(sql, p)  # noqa: E731  (every query below uses the same filter values)
 
    def counts(view, col):
        return {r[col]: r["n"] for r in rows(
            f"select {col}, count(*)::int as n from public.{view} where {WHERE} and {col} is not null group by 1")}
 
    yt_sent = counts("v_yt_rows", "sentiment") if yt else {}
    yt_stance = counts("v_yt_rows", "stance") if yt else {}
    nw_stance = counts("v_news_rows", "stance") if nw else {}
    both = {k: yt_stance.get(k, 0) + nw_stance.get(k, 0) for k in ("support", "neutral", "oppose")}
    stance_dist = _dist({"support": both["support"], "against": both["oppose"], "neutral": both["neutral"]},
                        ("support", "against", "neutral"))
 
    topics_by_sentiment, topics_by_stance = {}, {}
    if yt:
        topics_by_sentiment = _ranked(rows(
            f"""select keyword, sentiment, count(*)::int as n from public.v_yt_rows
                where {WHERE} and sentiment is not null and keyword is not null group by 1, 2"""),
            "sentiment", "keyword", ("negative", "neutral", "positive"), "topic")
    if nw and not yt:
        topics_by_stance = _ranked(rows(
            f"""select keyword, stance, count(*)::int as n from public.v_news_rows
                where {WHERE} and stance is not null and keyword is not null group by 1, 2"""),
            "stance", "keyword", ("oppose", "neutral", "support"), "topic")
 
    #top actors for news 
    actors_by_stance, actors_by_sentiment, actor_detail = {}, {}, {"actors": [], "newsPerActor": {}}
    if nw:
        actor_rows = rows(
            f"""select actor_name, stance, count(*)::int as n from public.v_news_rows
                where {WHERE} and stance is not null group by 1, 2""")
        actors_by_stance = _ranked(actor_rows, "stance", "actor_name", ("oppose", "neutral", "support"), "name")
        # news actors have a stance, not a sentiment: oppose = negative, support = positive
        actors_by_sentiment = {STANCE_TO_SENTIMENT[k]: v for k, v in actors_by_stance.items()}
        top_actors = [r["actor_name"] for r in rows(
            f"""select actor_name from public.v_news_rows where {WHERE} and stance is not null
                group by 1 order by count(*) desc, actor_name limit 5""")]
        if top_actors:
            articles = query(
                f"""select actor_name, title, stance from (
                      select actor_name, title, stance,
                             row_number() over (partition by actor_name order by item_date desc, stance_id) as rn
                      from public.v_news_rows
                      where {WHERE} and stance is not null and actor_name = any(%(actors)s)) x
                    where rn <= 10 order by actor_name, rn""", {**p, "actors": top_actors})
            actor_detail = {"actors": top_actors,
                            "newsPerActor": {a: [{"news": r["title"], "stance": r["stance"]}
                                                 for r in articles if r["actor_name"] == a] for a in top_actors}}
 
    #stance sources
    sources = None
    if yt and nw:
        n_yt, n_nw = sum(yt_sent.values()), sum(nw_stance.values())
        share = lambda n, tot: round(100.0 * n / tot, 1) if tot else 0  # noqa: E731
        nw_as_sent = {STANCE_TO_SENTIMENT[k]: v for k, v in nw_stance.items()}
        sources = {
            "sourcePercentage": [{"source": "YouTube", "percentage": share(n_yt, n_yt + n_nw)},
                                 {"source": "News", "percentage": share(n_nw, n_yt + n_nw)}],
            "sourceBreakdown": [
                {"source": "YouTube", **{k: share(yt_sent.get(k, 0), n_yt) for k in ("positive", "neutral", "negative")}},
                {"source": "News", **{k: share(nw_as_sent.get(k, 0), n_nw) for k in ("positive", "neutral", "negative")}},
            ]}
 
    #most discussed topics: top keywords, with average sentiment (YouTube) / stance (news)
    yt_kw = {r["keyword"]: r for r in rows(
        f"""select keyword, count(*)::int as n, avg({SENTIMENT_TO_SCORE})::float as score
            from public.v_yt_rows where {WHERE} and sentiment is not null and keyword is not null
            group by 1""")} if yt else {}
    nw_kw = {r["keyword"]: r for r in rows(
        f"""select keyword, count(*)::int as n, avg({STANCE_TO_SCORE})::float as score
            from public.v_news_rows where {WHERE} and stance is not null and keyword is not null
            group by 1""")} if nw else {}
    basis = yt_kw if yt else nw_kw
    most = []
    for kw, r in sorted(basis.items(), key=lambda kv: (-kv[1]["n"], kv[0]))[:8]:
        most.append({"topic": kw,
                     "avgSentiment": _score_label(yt_kw[kw]["score"], "positive", "negative") if kw in yt_kw else None,
                     "stance": _score_label(nw_kw[kw]["score"], "support", "oppose") if kw in nw_kw else None})
 
    #breakdown table: newest labeled comments / article stances
    items = []
    if yt:
        items += [(r["item_date"], {"commentNews": _clip(r["text"]), "stance": r["stance"], "avgSentiment": r["sentiment"]})
                  for r in rows(f"""select text, stance, sentiment, item_date from public.v_yt_rows
                                    where {WHERE} and stance is not null and sentiment is not null
                                    order by item_date desc, label_id limit 40""")]
    if nw:
        items += [(r["item_date"], {"commentNews": _clip(f"{r['title']} ({r['actor_name']})"),
                                    "stance": r["stance"], "avgSentiment": None})
                  for r in rows(f"""select title, actor_name, stance, item_date from public.v_news_rows
                                    where {WHERE} and stance is not null
                                    order by item_date desc, stance_id limit 40""")]
    items.sort(key=lambda it: it[0] or date.min, reverse=True)
    data = [it[1] for it in items[:80]]
 
    return {
        "title": f"{plant.upper()} Public Analysis",
        "description": SECTION_TEXT[plant],
        "sentimentDistribution": _dist(yt_sent, ("positive", "negative", "neutral")),
        "stanceDistribution": stance_dist,
        "topDiscussionTopics": topics_by_sentiment,
        "topDiscussionTopicsByStance": topics_by_stance,
        "topActorSummary": actors_by_sentiment,
        "topActorSummaryByStance": actors_by_stance,
        "stanceSources": sources,
        "topActorDetail": actor_detail,
        "mostDiscussedTopics": most,
        "sentimentStanceBreakdown": {"data": data, "totalPages": max(1, math.ceil(len(data) / 4)), "perPage": 4},
    }
 
 
FromQ = Query(None, alias="from", description="First day YYYY-MM-DD (frontend name)")
ToQ = Query(None, alias="to", description="Last day YYYY-MM-DD (frontend name)")
RangeQ = Query(None, alias="range", pattern="^(3m|6m|all)$", description="3m, 6m or all")
TypesQ = Query(None, description="Comma list: pltu,pltn (empty = both)")
PlatformsQ = Query(None, description="Comma list: youtube,news (empty = both)")
 
 
@app.get("/api/dashboard")
def dashboard(types: Optional[str] = TypesQ, platforms: Optional[str] = PlatformsQ,
              range_: Optional[str] = RangeQ, date_from: Optional[date] = FromQ,
              date_to: Optional[date] = ToQ, labeler: str = Labeler):
    """Everything the dashboard page shows, in the exact shape the React components expect."""
    d_from, d_to = _resolve_dates(range_, date_from, date_to, labeler)
    plats = _pick(platforms, PLATFORMS)
    out = {t: _section(t, labeler, d_from, d_to, plats) for t in _pick(types, PLANT_TYPES)}
    out["labeler"] = labeler
    out["lastUpdated"] = date.today().isoformat()
    return out
 
 
@app.get("/api/dataset")
def dataset(types: Optional[str] = TypesQ, platforms: Optional[str] = PlatformsQ,
            range_: Optional[str] = RangeQ, date_from: Optional[date] = FromQ,
            date_to: Optional[date] = ToQ, labeler: str = Labeler,
            limit: int = Query(1000, ge=1, le=5000, description="Max rows per type and platform (newest first)")):
    """Rows for the Data View page: {pltu: {youtube: [...], news: [...]}, pltn: {...}}."""
    d_from, d_to = _resolve_dates(range_, date_from, date_to, labeler)
    out = {}
    for plant in _pick(types, PLANT_TYPES):
        p = {"labeler": labeler, "target": plant.upper(), "date_from": d_from, "date_to": d_to, "limit": limit}
        out[plant] = {}
        for platform in _pick(platforms, PLATFORMS):
            if platform == "youtube":
                out[plant][platform] = [
                    {"id": f"yt-{r['label_id']}", "text": r["text"], "videoTitle": r["video_title"],
                     "videoUrl": r["video_url"], "stance": r["stance"], "sentiment": r["sentiment"]}
                    for r in query(f"""select label_id, text, video_title, video_url, stance, sentiment
                                       from public.v_yt_rows where {WHERE}
                                       order by item_date desc, label_id limit %(limit)s""", p)]
            else:
                out[plant][platform] = [
                    {"id": f"news-{r['stance_id']}", "title": r["title"], "source": r["source_name"],
                     "actors": [r["actor_name"]], "stance": r["stance"], "evidence": r["evidence"] or ""}
                    for r in query(f"""select stance_id, title, source_name, actor_name, stance, evidence
                                       from public.v_news_rows where {WHERE}
                                       order by item_date desc, stance_id limit %(limit)s""", p)]
    return out
 
 
StanceQ = Query(None, pattern="^(support|neutral|oppose)$")
SearchQ = Query(None, max_length=100, description="Text to search for (case-insensitive)")
 
 
@app.get("/api/yt/comments")
def yt_comments(f: dict = Depends(filters), stance: Optional[str] = StanceQ,
                sentiment: Optional[str] = Query(None, pattern="^(positive|neutral|negative)$"),
                keyword: Optional[str] = None, q: Optional[str] = SearchQ,
                page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    """Labeled YouTube comments, newest first, one page at a time."""
    p = {**f, "stance": stance, "sentiment": sentiment, "keyword": keyword, "q": q,
         "limit": per_page, "offset": (page - 1) * per_page}
    where = f"""{WHERE}
        and (%(stance)s::text    is null or stance = %(stance)s)
        and (%(sentiment)s::text is null or sentiment = %(sentiment)s)
        and (%(keyword)s::text   is null or keyword = %(keyword)s)
        and (%(q)s::text is null or position(lower(%(q)s) in lower(coalesce(text, '') || ' ' || coalesce(video_title, ''))) > 0)"""
    total = query(f"select count(*)::int as n from public.v_yt_rows where {where}", p)[0]["n"]
    rows = query(f"""select cid, text, video_title, video_url, keyword, target_code, item_date, stance, sentiment
                     from public.v_yt_rows where {where}
                     order by item_date desc, label_id limit %(limit)s offset %(offset)s""", p)
    return {"total": total, "page": page, "per_page": per_page, "rows": rows}
 
 
@app.get("/api/news/stances")
def news_stances(f: dict = Depends(filters), stance: Optional[str] = StanceQ,
                 actor: Optional[str] = None, keyword: Optional[str] = None, q: Optional[str] = SearchQ,
                 page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    """Article/actor stances with the evidence quote, newest first, one page at a time."""
    p = {**f, "stance": stance, "actor": actor, "keyword": keyword, "q": q,
         "limit": per_page, "offset": (page - 1) * per_page}
    where = f"""{WHERE}
        and (%(stance)s::text  is null or stance = %(stance)s)
        and (%(actor)s::text   is null or actor_name = %(actor)s)
        and (%(keyword)s::text is null or keyword = %(keyword)s)
        and (%(q)s::text is null or position(lower(%(q)s) in lower(
              coalesce(title, '') || ' ' || coalesce(actor_name, '') || ' ' || coalesce(evidence, ''))) > 0)"""
    total = query(f"select count(*)::int as n from public.v_news_rows where {where}", p)[0]["n"]
    rows = query(f"""select title, url, source_name as source, actor_name, actor_role, keyword, target_code,
                            item_date, stance, evidence
                     from public.v_news_rows where {where}
                     order by item_date desc, stance_id limit %(limit)s offset %(offset)s""", p)
    return {"total": total, "page": page, "per_page": per_page, "rows": rows}