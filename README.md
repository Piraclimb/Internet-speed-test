# ネットワーク速度監視ツール

リアルタイムでネットワーク速度を測定し、グラフ化するPythonツールです。

## 機能

- 定期的なネットワーク速度測定（ダウンロード・アップロード）
- リアルタイムグラフ表示
- 測定履歴の保存（JSON形式）
- 直感的なインターフェース

## インストール

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python network_speed_monitor.py
```

## 設定

- `test_interval`: 測定間隔（秒）- デフォルト5秒
- `max_data_points`: グラフに表示する最大データ点数 - デフォルト100000点

## 注意事項

- 初回起動時はspeedtestサーバーの検索に時間がかかる場合があります
- Ctrl+Cで終了できます
- 測定データは`speed_history.json`に保存されます
