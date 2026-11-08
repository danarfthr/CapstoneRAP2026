import os
from contextlib import contextmanager
from datetime import date
from typing import Optional

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