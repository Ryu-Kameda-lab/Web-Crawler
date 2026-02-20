"""
collector.py
Gemini を使って仮想通貨ニュースを収集・分析するモジュール
"""

import os
from google import genai
from google.genai import types
from datetime import datetime

MODEL_NAME = "gemini-2.0-flash"


def collect_crypto_news(existing_report: str = "", update_count: int = 0) -> dict:
    """
    Gemini + Google Search Grounding でニュースを収集し、
    レポートを生成（または更新）する。

    Args:
        existing_report: これまでのレポート本文（初回は空文字）
        update_count: 本日何回目の更新か

    Returns:
        {
            "content": str,       # 生成されたレポート（Markdown）
            "sources": list[dict],# [{"title": ..., "url": ...}, ...]
            "updated_at": str     # 更新日時
        }
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。.env ファイルを確認してください。")

    client = genai.Client(api_key=api_key)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M JST")

    # ──────────────────────────────────────────
    # プロンプト生成
    # ──────────────────────────────────────────
    if not existing_report:
        # 初回：デイリーレポートの初版を作成
        prompt = f"""
あなたは仮想通貨市場の専門アナリストです。
現在時刻: {current_time}

インターネット上の最新情報を広く収集し、**仮想通貨デイリーレポート（初版）**を作成してください。

## 調査すべき項目
1. **主要通貨の動向** - BTC・ETH・主要アルトコインの価格・出来高・トレンド
2. **規制・政策ニュース** - 各国政府・中央銀行・SEC・金融庁などの動き
3. **マクロ経済との連動** - 米株・ドル指数・金利・CPI などとの相関
4. **DeFi・NFT・Web3** - プロトコルの最新アップデート、注目プロジェクト
5. **機関投資家・企業の動き** - ETF 資金フロー、大企業の仮想通貨関連ニュース
6. **SNS・コミュニティの動向** - 以下を必ず調査すること
   - X(Twitter) で今日トレンドになっている仮想通貨関連の話題・ハッシュタグ
   - 影響力のある仮想通貨インフルエンサー（例: @CryptoInfluencer 系アカウント）の注目発言
   - Reddit の r/CryptoCurrency・r/Bitcoin・r/ethereum などのホットな投稿・議論
   - 仮想通貨コミュニティ全体の今日のセンチメント（強気/弱気/中立）

## 出力形式（Markdown）

```
# 仮想通貨デイリーレポート {datetime.now().strftime('%Y年%m月%d日')}
**最終更新: {current_time}（第1回収集）**

---

## 📊 総合サマリー
（今日の最重要トピックを3〜5点、箇条書きで簡潔に）

---

## 1. 主要通貨の動向
（詳細分析）

## 2. 規制・政策ニュース
（詳細分析）

## 3. マクロ経済との連動
（詳細分析）

## 4. DeFi・NFT・Web3
（詳細分析）

## 5. 機関投資家・企業の動き
（詳細分析）

## 6. 📣 SNS・コミュニティの動向
### X(Twitter) トレンド
（トレンドのハッシュタグ・話題・注目ツイートの要約）

### Reddit 注目投稿
（r/CryptoCurrency・r/Bitcoin などのホット投稿・議論の要約）

### コミュニティセンチメント
（全体的な雰囲気: 強気 / 弱気 / 中立、その根拠）

---

## 📎 参照ソース
（各情報のソースURLを列挙）
```

各セクションは具体的な数字・固有名詞・日時を含めて詳述してください。
ソースは必ずURLを記載してください。
SNSセクションは特に具体的な投稿内容・ユーザー名・数値（いいね数・RT数など）を含めてください。
"""
    else:
        # 2回目以降：既存レポートを更新・深化
        prompt = f"""
あなたは仮想通貨市場の専門アナリストです。
現在時刻: {current_time}（本日 第{update_count + 1}回目の情報収集）

## 現在のレポート
---
{existing_report}
---

上記の既存レポートを参考にしながら、**最新情報を収集してレポートを更新・深化**してください。

## 更新のルール
- 新しいニュースや動向があれば各セクションに追記・上書き
- 既存情報に新たな根拠・詳細が得られたら内容を深める
- 総合サマリーは常に最新状況を反映して書き直す
- 「最終更新」の日時を {current_time}（第{update_count + 1}回収集）に更新する
- セクション構成（1〜6）は維持する
- 参照ソースに新しいURLを追加する

## 調査すべき最新情報
1. **主要通貨の動向** - 直近1時間の価格変動・注目イベント
2. **規制・政策ニュース** - 新たな規制・政策の発表
3. **マクロ経済との連動** - 指標発表・市場の反応
4. **DeFi・NFT・Web3** - 新しいアップデート・事件・話題
5. **機関投資家・企業の動き** - 新たな買い付け・発表・提携
6. **SNS・コミュニティの動向** - 以下を必ず更新すること
   - X(Twitter) の直近1時間のトレンド・話題・注目発言
   - Reddit の新たなホット投稿・議論
   - コミュニティセンチメントの変化（前回からの変化があれば言及）

**更新後のレポート全文をそのまま出力してください（省略しないこと）。**
"""

    # ──────────────────────────────────────────
    # Gemini API 呼び出し（Google Search Grounding）
    # ──────────────────────────────────────────
    google_search_tool = types.Tool(google_search=types.GoogleSearch())

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
            ),
        )
    except Exception as e:
        # grounding なしでフォールバック
        print(f"[collector] Search grounding エラー、フォールバック: {e}")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

    # ──────────────────────────────────────────
    # ソース抽出
    # ──────────────────────────────────────────
    sources = []
    try:
        candidate = response.candidates[0]
        gm = getattr(candidate, "grounding_metadata", None)
        if gm:
            for chunk in getattr(gm, "grounding_chunks", []):
                web = getattr(chunk, "web", None)
                if web:
                    sources.append(
                        {
                            "title": getattr(web, "title", ""),
                            "url": getattr(web, "uri", ""),
                        }
                    )
    except Exception:
        pass

    return {
        "content": response.text,
        "sources": sources,
        "updated_at": current_time,
    }
