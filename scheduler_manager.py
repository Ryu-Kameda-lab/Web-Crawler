"""
scheduler_manager.py
APScheduler を使って1時間ごとにニュース収集ジョブを実行するモジュール
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import streamlit as st

from collector import collect_crypto_news
from report_manager import get_today_key, load_report, save_report

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

JOB_ID = "crypto_news_job"


def run_collection_job():
    """APScheduler から呼び出されるジョブ関数"""
    logger.info("[Scheduler] ニュース収集ジョブ開始")
    try:
        date_key = get_today_key()
        report_data = load_report(date_key)

        existing_content = report_data.get("content", "")
        update_count = report_data.get("update_count", 0)

        result = collect_crypto_news(
            existing_report=existing_content,
            update_count=update_count,
        )

        save_report(
            date_key=date_key,
            content=result["content"],
            sources=result["sources"],
            updated_at=result["updated_at"],
        )
        logger.info(f"[Scheduler] 収集完了 ({result['updated_at']})")

    except Exception as e:
        logger.error(f"[Scheduler] ジョブエラー: {e}", exc_info=True)


def get_scheduler() -> BackgroundScheduler:
    """
    @st.cache_resource でキャッシュされたスケジューラーを返す。
    初回呼び出し時にスケジューラーを起動する。
    """
    scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
    scheduler.add_job(
        run_collection_job,
        trigger=IntervalTrigger(hours=1),
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("[Scheduler] スケジューラー起動（1時間ごと）")
    return scheduler


def trigger_now(scheduler: BackgroundScheduler):
    """手動で即時収集を実行する"""
    from apscheduler.triggers.date import DateTrigger
    from datetime import datetime, timedelta

    run_time = datetime.now() + timedelta(seconds=2)
    scheduler.add_job(
        run_collection_job,
        trigger=DateTrigger(run_date=run_time),
        id="manual_job",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("[Scheduler] 手動収集ジョブをキューに追加")


def get_next_run_time(scheduler: BackgroundScheduler) -> str:
    """次回実行予定時刻を文字列で返す"""
    job = scheduler.get_job(JOB_ID)
    if job and job.next_run_time:
        return job.next_run_time.strftime("%H:%M:%S")
    return "不明"
