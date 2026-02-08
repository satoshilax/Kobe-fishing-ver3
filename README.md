# 神戸釣り情報 v5.0 - 完全自動更新システム

🎣 神戸周辺100km圏内の釣り情報をリアルタイム配信！

## 🌟 機能

### ✅ 実装済み
- リアルタイム釣果表示（複数サイトから自動収集）
- AI釣果予測
- 天気予報（3日間）
- 月齢カレンダー（大潮・中潮）
- 26箇所の釣りスポット情報
- ダークモード対応
- レスポンシブデザイン

### 🔄 自動更新システム
- **更新頻度**: 毎日3回（朝6時、昼12時、夕方6時）
- **データ収集元**:
  - フィッシングマックス
  - 須磨海釣り公園公式
  - アングラーズ
  - X（Twitter）ハッシュタグ
  - 釣りブログ
  - 気象庁（天気・潮汐）

## 📦 セットアップ

### 1. GitHubリポジトリ準備
```bash
# リポジトリ作成済み: Kobe-fishing-ver3
```

### 2. ファイル構成
```
/
├── index.html              # メインアプリ
├── fishing-data.json       # 釣果データ
├── collect_fishing_data.py # データ収集スクリプト
└── .github/
    └── workflows/
        └── update-fishing-data.yml  # 自動実行設定
```

### 3. GitHubにアップロード

#### 方法1: GitHub Web UI
1. リポジトリページを開く
2. 「Add file」→「Upload files」
3. 以下のファイルをアップロード：
   - `index.html`
   - `fishing-data.json`
   - `collect_fishing_data.py`
4. `.github/workflows/` フォルダを作成
5. `update-fishing-data.yml` をアップロード

#### 方法2: Git コマンド（PCがある場合）
```bash
git clone https://github.com/satoshilax/Kobe-fishing-ver3.git
cd Kobe-fishing-ver3
# ファイルをコピー
git add .
git commit -m "🎣 自動更新システム追加"
git push
```

### 4. GitHub Pages 有効化（済み）
Settings → Pages → Source: main / (root) → Save

### 5. GitHub Actions 確認
1. リポジトリの「Actions」タブを開く
2. 「釣果データ自動更新」ワークフローが表示される
3. 「Run workflow」で手動実行テスト可能

## 🔧 カスタマイズ

### データ収集の追加
`collect_fishing_data.py` を編集：

```python
def collect_your_source(self):
    """新しいデータソースから収集"""
    # スクレイピングまたはAPI呼び出し
    return data
```

### 更新頻度の変更
`.github/workflows/update-fishing-data.yml` の cron を編集：

```yaml
schedule:
  - cron: '0 21 * * *'  # 朝6時 JST
  - cron: '0 3 * * *'   # 昼12時 JST
  - cron: '0 9 * * *'   # 夕方6時 JST
```

## 📊 データ形式

### fishing-data.json
```json
{
  "lastUpdated": "2026-02-07T20:00:00+09:00",
  "spots": [
    {
      "name": "須磨海釣り公園",
      "area": "神戸",
      "distance": 2.3,
      "info": "ファミリー向け・足場良好",
      "catches": [
        {
          "fish": "アジ",
          "size": 16,
          "count": 25,
          "time": "2時間前",
          "user": "釣り太郎",
          "method": "サビキ"
        }
      ]
    }
  ],
  "weatherForecast": [...],
  "moonPhase": {...}
}
```

## 🌐 公開URL
https://satoshilax.github.io/Kobe-fishing-ver3/

## 📝 更新履歴
- **v5.0** (2026-02-07): 完全自動更新システム実装
- **v4.6** (2026-02-07): リアルタイム更新機能追加
- **v1.0** (2026-02-07): 初版リリース

## 🛠️ 技術スタック
- **フロントエンド**: HTML, CSS, JavaScript
- **データ収集**: Python, BeautifulSoup, Requests
- **自動化**: GitHub Actions
- **ホスティング**: GitHub Pages

## 📄 ライセンス
MIT License

## 🤝 コントリビューション
Issue や Pull Request 歓迎！

---
Made with ❤️ for 神戸の釣り人
