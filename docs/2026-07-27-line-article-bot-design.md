# LINE → Gemini X記事下書きBot 設計書

作成日：2026-07-27

## 目的

SoraがLINEに思いついたことをメモとして送ると、Gemini APIが該当するX記事テーマの「型」に沿って草稿に整形し、LINEに返信する。Soraはそれをコピーして自分で添削・投稿する。PCを起動する必要がない。

## スコープ（v1）

- テキストメッセージのみ対応（ボイスメッセージは対象外。スマホの音声入力でテキスト化してもらう運用）
- 送信者の制限なし（個人用LINEチャネルのため）
- 返信はLINEチャット内のみ（ファイル自動保存はしない）
- テーマ番号の指定は不要。Geminiが本文内容から4テーマのどれに該当するか自動判定する
- 属人性（口調の癖・経歴実績など）ファイルは今回未定義。空ファイルとして持たせ、後日中身を追加する前提

## アーキテクチャ

```
LINE (Messaging API)
   │ Webhook (テキストメッセージ)
   ▼
FastAPI サーバー（Railway）
   │
   ├─ line_client.py    … 署名検証・LINEへの返信送信
   ├─ gemini_client.py  … knowledge/ の内容とメッセージ本文からプロンプトを組み立て、Gemini APIを呼ぶ
   └─ knowledge/        … テーマ別記事_型.md／発信哲学.md／NGルール.md／属人性.md（空）
   │
   ▼
LINEへ返信（整形済み草稿）
```

## コンポーネント

| ファイル | 役割 |
|---|---|
| `main.py` | FastAPIエントリポイント。`/webhook` でLINEイベントを受信 |
| `line_client.py` | LINE署名検証、返信送信（Reply API） |
| `gemini_client.py` | knowledge読み込み＋プロンプト構築＋Gemini API呼び出し |
| `config.py` | 環境変数管理（`LINE_CHANNEL_SECRET`／`LINE_CHANNEL_ACCESS_TOKEN`／`GEMINI_API_KEY`） |
| `knowledge/テーマ別記事_型.md` | 4テーマの型（既存ファイルをコピー） |
| `knowledge/発信哲学.md` | 既存ファイルをコピー |
| `knowledge/NGルール.md` | 既存ファイルをコピー |
| `knowledge/属人性.md` | 空ファイル（後日追加） |

## データフロー

1. LINEからWebhook受信 → 署名検証（不正なリクエストは401で拒否）
2. テキストメッセージ以外（画像・音声等）は「テキストで送ってください」と返信して終了
3. `knowledge/` 配下の全ファイル＋ユーザーのメッセージ本文をGeminiに渡す
4. Geminiが該当するテーマの型を判断し、そのテーマの型に沿って草稿を生成
5. LINE Reply APIで返信

## エラー処理

| ケース | 対応 |
|---|---|
| Gemini API呼び出し失敗 | 「生成に失敗しました。もう一度送ってください」と返信 |
| メッセージが空・極端に短い | 「もう少し詳しく送ってください」と返信 |
| テキスト以外のメッセージ | 「テキストで送ってください」と返信 |
| LINE署名検証失敗 | 401を返し、処理しない |

## テスト方針

sorabotと同様、pytestで各モジュールの単体テストを用意する。
- `line_client`：署名検証ロジック、返信ペイロード生成
- `gemini_client`：プロンプト組み立てロジック（knowledge読み込み含む）
- Gemini API・LINE APIへの実際の外部通信はモックする

## デプロイ

- Railway（Hobbyプラン、月額$5〜）
- プロジェクト独自のGitリポジトリを持つ（sorabotと同じ構成。ワークスペース全体はGit管理しない）

## 未確定・後日対応

- 属人性ファイルの中身（担当者が別途定義中）
- ボイスメッセージ対応（必要になれば別途検討）

## Soraが用意するもの

- LINE公式アカウントの Channel Secret と Channel Access Token（LINE Developersコンソールから取得）
- Gemini APIキー（Google AI Studioから取得）
- Railwayアカウント
