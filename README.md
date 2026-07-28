# line-article-bot

SoraがLINEに送ったメモを、X記事の型（`knowledge/テーマ別記事_型.md`）に沿ってGemini APIで整形し、LINEに返信するBot。

## ローカル実行

```bash
pip install -r requirements.txt
cp .env.example .env
# .env にLINE_CHANNEL_SECRET / LINE_CHANNEL_ACCESS_TOKEN / GEMINI_API_KEY を設定
uvicorn main:app --reload
```

## テスト

```bash
pytest -v
```

## Railwayへのデプロイ

1. このディレクトリのリポジトリをGitHubにpushする
2. Railwayで新規プロジェクトを作成し、そのGitHubリポジトリを接続する
3. Railwayの環境変数に `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` / `GEMINI_API_KEY` を設定する
4. デプロイ完了後に発行されるURL + `/webhook` を、LINE Developersコンソールの Webhook URL に設定する
5. LINE Developersコンソールで「Webhookの利用」をONにする

## 属人性ファイルの更新

`knowledge/属人性.md` の中身が確定したら、このファイルを上書きしてRailwayに再デプロイする（git push で自動反映）。

## 実運用の確認手順（手動・要クレデンシャル）

以下はコードやテストでは自動化できない、実際のLINE/Geminiクレデンシャルを使った最終確認手順。

1. Soraが用意した `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` / `GEMINI_API_KEY` を Railway の環境変数に設定する
2. GitHubリポジトリを作成しpush、RailwayでそのリポジトリからデプロイURLを発行する
3. LINE DevelopersコンソールのWebhook URLに `{デプロイURL}/webhook` を設定し、Webhook利用をONにする
4. Soraの個人LINEから、そのLINE公式アカウントに実際にメモを送り、テーマに沿った草稿が返ってくることを確認する
