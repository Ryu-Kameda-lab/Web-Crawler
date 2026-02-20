"""
app.py
仮想通貨デイリーレポート生成アプリ（Streamlit）

起動コマンド:
    streamlit run app.py
"""

import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

# ──────────────────────────────────────────────────────────────
# 環境変数読み込み
# ──────────────────────────────────────────────────────────────
load_dotenv()

from report_manager import (
    get_today_key,
    load_report,
    list_reports,
    get_report_md_path,
)
from scheduler_manager import get_scheduler, trigger_now, get_next_run_time

# ──────────────────────────────────────────────────────────────
# ページ設定
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="仮想通貨デイリーレポーター",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# スケジューラー（シングルトン）
# ──────────────────────────────────────────────────────────────
@st.cache_resource
def init_scheduler():
    return get_scheduler()

scheduler = init_scheduler()

# ──────────────────────────────────────────────────────────────
# 自動リフレッシュ（60秒ごとに画面を更新）
# ──────────────────────────────────────────────────────────────
st_autorefresh(interval=60_000, key="auto_refresh")

# ──────────────────────────────────────────────────────────────
# スタイル
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-progress { background:#fff3cd; color:#856404; }
    .badge-completed { background:#d4edda; color:#155724; }
    .report-meta {
        background: #f8f9fa;
        border-left: 4px solid #0d6efd;
        padding: 8px 16px;
        margin-bottom: 16px;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────
# サイドバー
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📰 Crypto Reporter")
    st.caption("Gemini 2.5 Pro × Google Search")

    st.divider()

    # API キー確認
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        st.success("✅ Gemini API キー設定済み")
    else:
        st.error("❌ GEMINI_API_KEY が未設定")
        new_key = st.text_input("API キーを入力", type="password")
        if new_key:
            os.environ["GEMINI_API_KEY"] = new_key
            st.rerun()

    st.divider()

    # スケジューラー状態
    st.subheader("⏱ スケジューラー")
    next_run = get_next_run_time(scheduler)
    st.info(f"次回自動収集: **{next_run}**")

    if st.button("🔄 今すぐ収集する", use_container_width=True, type="primary"):
        if not api_key:
            st.error("API キーを設定してください")
        else:
            trigger_now(scheduler)
            st.success("収集ジョブを開始しました（数秒後に反映）")
            time.sleep(3)
            st.rerun()

    st.divider()

    # レポート一覧（過去ログ）
    st.subheader("📁 過去のレポート")
    all_reports = list_reports()
    if all_reports:
        date_options = [r["date_key"] for r in all_reports]
        selected_date = st.radio(
            "日付を選択",
            options=date_options,
            format_func=lambda d: (
                f"{'📝' if d == get_today_key() else '📄'} {d} "
                f"({'作成中' if any(r['status'] == 'in_progress' and r['date_key'] == d for r in all_reports) else '完了'})"
            ),
            index=0,
        )
    else:
        selected_date = get_today_key()
        st.caption("まだレポートはありません")

    st.divider()
    st.caption("60秒ごとに自動更新")

# ──────────────────────────────────────────────────────────────
# メインエリア
# ──────────────────────────────────────────────────────────────

# 表示するレポートを決定
view_date = selected_date if all_reports else get_today_key()
report = load_report(view_date)

is_today = view_date == get_today_key()

# ヘッダー
col_title, col_status = st.columns([4, 1])
with col_title:
    st.title(f"仮想通貨デイリーレポート")
    st.caption(f"対象日: {view_date}")

with col_status:
    status = report.get("status", "in_progress")
    badge_class = "badge-completed" if status == "completed" else "badge-progress"
    label = "✅ 完了" if status == "completed" else "🔄 作成中"
    st.markdown(
        f'<div style="margin-top:24px">'
        f'<span class="status-badge {badge_class}">{label}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────
# レポートが存在する場合
# ──────────────────────────────────────────────────────────────
content = report.get("content", "")
update_count = report.get("update_count", 0)
history = report.get("history", [])
sources = report.get("sources", [])

if content:
    # メタ情報バー
    last_update = history[-1]["updated_at"] if history else "—"
    st.markdown(
        f'<div class="report-meta">'
        f"📊 収集回数: <b>{update_count}回</b>　|　"
        f"最終更新: <b>{last_update}</b>　|　"
        f"参照ソース数: <b>{len(sources)}件</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # タブ構成
    tab_report, tab_sources, tab_history = st.tabs(
        ["📄 レポート", "🔗 参照ソース一覧", "📋 更新履歴"]
    )

    # ── レポートタブ ──
    with tab_report:
        # ダウンロードボタン
        col_dl1, col_dl2, col_space = st.columns([1.5, 1.5, 5])
        with col_dl1:
            st.download_button(
                label="⬇️ Markdown でダウンロード",
                data=content.encode("utf-8"),
                file_name=f"crypto_report_{view_date}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col_dl2:
            # テキスト形式
            plain_text = content.replace("#", "").replace("**", "").replace("*", "")
            st.download_button(
                label="⬇️ テキストでダウンロード",
                data=plain_text.encode("utf-8"),
                file_name=f"crypto_report_{view_date}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        st.divider()
        st.markdown(content, unsafe_allow_html=False)

    # ── ソースタブ ──
    with tab_sources:
        if sources:
            st.subheader(f"参照ソース一覧（{len(sources)}件）")
            for i, s in enumerate(sources, 1):
                title = s.get("title") or "（タイトル不明）"
                url = s.get("url", "")
                if url:
                    st.markdown(f"{i}. [{title}]({url})")
                else:
                    st.markdown(f"{i}. {title}")
        else:
            st.info("ソース情報はまだありません")

    # ── 更新履歴タブ ──
    with tab_history:
        if history:
            st.subheader("更新履歴")
            for h in reversed(history):
                st.markdown(
                    f"- 第 **{h['update_number']}** 回 収集 — {h['updated_at']}"
                )
        else:
            st.info("まだ更新履歴はありません")

else:
    # レポート未作成の場合
    st.info(
        "📭 まだ本日のレポートは作成されていません。\n\n"
        "サイドバーの「**今すぐ収集する**」ボタンを押すか、"
        "スケジューラーが自動的に収集を開始するまでお待ちください。"
    )

    if not api_key:
        st.warning(
            "⚠️ GEMINI_API_KEY が設定されていません。\n\n"
            "サイドバーで API キーを入力してください。"
        )

# ──────────────────────────────────────────────────────────────
# フッター
# ──────────────────────────────────────────────────────────────
st.divider()
col_f1, col_f2 = st.columns(2)
with col_f1:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"🕐 現在時刻: {now_str}　|　画面は60秒ごとに自動更新")
with col_f2:
    st.caption("Powered by Gemini 2.5 Pro + Google Search Grounding")
