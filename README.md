# line-article-bot

SoraがLINEに送ったメモを、X記事の型（`knowledge/theme_templates.md`）に沿ってGemini APIで整形し、LINEに返信するBot。

`knowledge/`配下のファイル名は英数字のみ（Cloud Runのコンテナビルドが日本語ファイル名で失敗するため）。

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

## Google Cloud Runへのデプロイ

前提：Google Cloudアカウント（無料枠）と `gcloud` CLIのセットアップ、このリポジトリがGitHubにpush済みであること。

1. `gcloud` CLIでログインし、プロジェクトを選択する
   ```bash
   gcloud auth login
   gcloud config set project <あなたのGCPプロジェクトID>
   ```
2. このディレクトリからCloud Runにデプロイする（`Dockerfile` を自動検出してビルド・デプロイまで一括実行）
   ```bash
   gcloud run deploy line-article-bot \
     --source . \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --set-env-vars LINE_CHANNEL_SECRET=xxx,LINE_CHANNEL_ACCESS_TOKEN=xxx,GEMINI_API_KEY=xxx
   ```
   （`xxx` の部分は実際の値に置き換える。環境変数は後からコンソール上でも変更できる）
3. デプロイ完了後に表示されるURL（例: `https://line-article-bot-xxxxx.a.run.app`）+ `/webhook` を、LINE Developersコンソールの Webhook URL に設定する
4. LINE Developersコンソールで「Webhookの利用」をONにする

### 再デプロイ（コード・型・ルールを更新したとき）

GitHubにpushしただけでは自動反映されない（Railwayと違いCloud Runはデフォルトで継続的デプロイが無い）。変更後は毎回、上記Step 2の `gcloud run deploy` を再実行する。

## 属人性ファイルの更新

`knowledge/persona.md` の中身が確定したら、このファイルを上書きし、上記の `gcloud run deploy` を再実行する。

## 実運用の確認手順（手動・要クレデンシャル）

以下はコードやテストでは自動化できない、実際のLINE/Geminiクレデンシャルを使った最終確認手順。

1. 上記の手順でCloud Runにデプロイし、発行されたURLを控える
2. LINE DevelopersコンソールのWebhook URLに `{デプロイURL}/webhook` を設定し、Webhook利用をONにする
3. LINE公式アカウントマネージャー（LINE Developersとは別コンソール）で「あいさつメッセージ」「自動応答メッセージ」をOFFにする（ONのままだとBotの返信より先にLINEの定型応答が返り、動作確認の妨げになる）
4. Soraの個人LINEから、そのLINE公式アカウントに実際にメモを送り、テーマに沿った草稿が返ってくることを確認する
5. 返信が来ない・おかしい場合は、Cloud Runのログを確認する（`gcloud run services logs read line-article-bot --region asia-northeast1`。Gemini APIのモデル名やクレデンシャルの問題はログに出る）
