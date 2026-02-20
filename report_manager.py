"""
report_manager.py
レポートのファイル保存・読み込み・一覧管理を担うモジュール
"""

import os
import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("reports")


def ensure_reports_dir():
    REPORTS_DIR.mkdir(exist_ok=True)


def get_today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_report_paths(date_key: str) -> dict:
    """指定日のレポートファイルパスを返す"""
    return {
        "md": REPORTS_DIR / f"{date_key}.md",
        "meta": REPORTS_DIR / f"{date_key}_meta.json",
    }


# ──────────────────────────────────────────────────────────────
# 読み込み
# ──────────────────────────────────────────────────────────────

def load_report(date_key: str) -> dict:
    """
    指定日のレポートを読み込む。
    Returns:
        {
            "content": str,
            "update_count": int,
            "sources": list,
            "history": list,   # 各更新の記録
            "status": str,     # "in_progress" | "completed"
        }
    """
    ensure_reports_dir()
    paths = get_report_paths(date_key)

    content = ""
    if paths["md"].exists():
        content = paths["md"].read_text(encoding="utf-8")

    meta = {
        "update_count": 0,
        "sources": [],
        "history": [],
        "status": "in_progress",
    }
    if paths["meta"].exists():
        try:
            meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        except Exception:
            pass

    return {"content": content, **meta}


def save_report(date_key: str, content: str, sources: list, updated_at: str):
    """
    レポートを保存する。
    既存メタデータを読み込み、更新カウント・履歴を更新してから保存。
    """
    ensure_reports_dir()
    paths = get_report_paths(date_key)

    # 既存メタ読み込み
    meta = {
        "update_count": 0,
        "sources": [],
        "history": [],
        "status": "in_progress",
    }
    if paths["meta"].exists():
        try:
            meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        except Exception:
            pass

    # 更新
    meta["update_count"] += 1
    meta["history"].append(
        {
            "updated_at": updated_at,
            "update_number": meta["update_count"],
        }
    )

    # 重複を除きソースをマージ
    existing_urls = {s.get("url") for s in meta["sources"]}
    for s in sources:
        if s.get("url") and s["url"] not in existing_urls:
            meta["sources"].append(s)
            existing_urls.add(s["url"])

    # 23:00 以降は completed 扱い（任意）
    hour = datetime.now().hour
    if hour == 23:
        meta["status"] = "completed"

    # 書き込み
    paths["md"].write_text(content, encoding="utf-8")
    paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    return meta


# ──────────────────────────────────────────────────────────────
# 一覧
# ──────────────────────────────────────────────────────────────

def list_reports() -> list[dict]:
    """
    保存済みレポートの一覧を返す（新しい日付順）。
    Returns: [{"date_key": str, "update_count": int, "status": str}, ...]
    """
    ensure_reports_dir()
    result = []
    for md_file in sorted(REPORTS_DIR.glob("*.md"), reverse=True):
        date_key = md_file.stem
        if "_meta" in date_key:
            continue
        meta_path = REPORTS_DIR / f"{date_key}_meta.json"
        meta = {"update_count": 0, "status": "unknown"}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        result.append(
            {
                "date_key": date_key,
                "update_count": meta.get("update_count", 0),
                "status": meta.get("status", "unknown"),
                "history": meta.get("history", []),
            }
        )
    return result


def get_report_md_path(date_key: str) -> Path:
    return REPORTS_DIR / f"{date_key}.md"
