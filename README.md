# hanna_support

[クラバト管理botハンナ](https://twitter.com/hibi_mhf/status/1208196517145628672)のサポートbot

## 事前準備

[Docker のインストール](http://docs.docker.jp/get-docker.html)

[Docker Compose のインストール](https://docs.docker.jp/compose/install.html)

[heroku CLI のインストール](https://devcenter.heroku.com/articles/heroku-cli)

[botアカウントの作成と招待](https://discordpy.readthedocs.io/ja/latest/discord.html)

## ダウンロード

```sh
git clone git@github.com:horimkin/hanna_support.git
cd hanna_support
```

## 環境変数を設定

```sh
cp .env_base .env
```

### トークンを設定

[Discord 開発者向けページ](https://discord.com/developers/applications)からトークンを取得して.env に設定

>DISCORD_TOKEN=""

### コンテナ作成

```sh
docker-compose build
```

### サーバー情報取得

```sh
docker-compose run bot -o
cat data/guilds.json
```

### サーバー情報設定

.env ファイルの以下の箇所に表示されたサーバー情報から該当する値を設定する

```sh
GUILD_ID       # botを使用するサーバーのID
RESERVE_CH_ID  # ハンナの予約確認板のID
REMAIN_CH_ID   # ハンナの残凸把握板のID
ANNOUNCE_CH_ID # このbotの通知で使用するチャンネルのID
```

### クランバトル期間設定

.env ファイルの以下の箇所に初日と最終日の日付を設定する

```sh
DATE_START="YYYY/MM/DD"
DATE_END="YYYY/MM/DD"
```

### heroku へデプロイ

以下を実行

```sh
./sh/heroku_init.sh
```

ブラウザでログインページが開くのでログイン後ページを閉じる

### スケジューラの設定

```sh
heroku addons:open scheduler
```

ブラウザでスケジューラのページが開くので
[create job]を押し、Schedule を

> [Every hour at...][:00]

に設定

Run Command に

> python src/hanna_support.py

を入力、[Save Job]を押し設定完了
## 設定の変更
クラバト期間の変更、Discordサーバーや通知チャンネルの変更をする際は、.env ファイルの内容を変更後、以下を実行

```sh
heroku config:push --overwrite
```
## アプリ名の変更(任意)
heroku上のアプリの名称は作成時に自動でランダムな名称が設定されているため、わかりやすい名前に変更しておくと判別しやすい。

```sh
heroku apps:rename "変更後の名前"
```