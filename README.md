# 📰 仮想通貨デイリーレポーター

Gemini 2.5 Pro + Google Search Grounding を使って、1時間ごとに仮想通貨の最新ニュースを収集し、1日1つの深化するレポートを自動生成する Streamlit アプリです。

---

## ✨ 主な機能

| 機能 | 詳細 |
|------|------|
| ⏱ 1時間ごとの自動収集 | APScheduler がバックグラウンドで動作 |
| 🔄 レポートの深化 | 毎時の収集内容を1つのレポートに統合・追記 |
| 👀 リアルタイム閲覧 | 作成過程をそのまま閲覧可能（60秒自動更新） |
| 📁 レポート保存 | `reports/` フォルダに Markdown で保存・蓄積 |
| ⬇️ ダウンロード | Markdown / テキスト形式でダウンロード可能 |
| 🔗 ソース表示 | Google Search Grounding で取得した参照元を表示 |

---

## 🚀 セットアップ

### 1. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

### 2. API キーの設定
`.env.example` をコピーして `.env` を作成し、Gemini API キーを記入します。

```bash
cp .env.example .env
```

`.env` ファイルを編集：
```
GEMINI_API_KEY=your_actual_api_key_here
```

> Gemini API キーは [Google AI Studio](https://aistudio.google.com/app/apikey) で取得できます。

### 3. アプリの起動
```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開いてください。

---

## 📁 ファイル構成

```
crypto_reporter/
├── app.py                  # Streamlit メインアプリ
├── collector.py            # Gemini API によるニュース収集
├── report_manager.py       # レポートのファイル保存・読み込み
├── scheduler_manager.py    # APScheduler による定期実行
├── requirements.txt        # 依存ライブラリ
├── .env                    # API キー（自分で作成）
├── .env.example            # API キーのテンプレート
└── reports/                # 保存されたレポート（自動生成）
    ├── 2025-01-01.md
    ├── 2025-01-01_meta.json
    └── ...
```

---

## 📋 レポートの構成

各レポートは以下のセクションで構成されます：

1. **総合サマリー** — その日の最重要トピック
2. **主要通貨の動向** — BTC・ETH・アルトコイン
3. **規制・政策ニュース** — 各国政府・金融機関の動き
4. **マクロ経済との連動** — 株式・ドル指数・金利との相関
5. **DeFi・NFT・Web3** — 最新プロジェクト・動向
6. **機関投資家・企業の動き** — ETF・大手企業の仮想通貨関連情報

---

## ⚠️ 注意事項

- Gemini API の利用には料金が発生する場合があります
- Google Search Grounding は Gemini API の有料機能です
- レポートは `reports/` ディレクトリに蓄積されるため、定期的な整理をお勧めします
- Streamlit を停止するとスケジューラーも停止します（24時間稼働させる場合はサーバー上で実行してください）
