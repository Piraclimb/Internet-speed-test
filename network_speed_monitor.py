#!/usr/bin/env python3
import speedtest
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import threading
import time
import json
import os
from collections import deque

class NetworkSpeedMonitor:
    def __init__(self, max_data_points=100, test_interval=60):
        self.max_data_points = max_data_points
        self.test_interval = test_interval
        self.download_speeds = deque(maxlen=max_data_points)
        self.upload_speeds = deque(maxlen=max_data_points)
        self.timestamps = deque(maxlen=max_data_points)
        self.data_file = "speed_history.json"
        self.running = False
        self.st = None  # 遅延初期化
        
        self.load_history()
        
    def load_history(self):
        """過去のデータを読み込み"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for entry in data[-self.max_data_points:]:
                        self.timestamps.append(datetime.fromisoformat(entry['timestamp']))
                        self.download_speeds.append(entry['download'])
                        self.upload_speeds.append(entry['upload'])
            except:
                pass
                
    def save_data(self, timestamp, download, upload):
        """データを保存"""
        entry = {
            'timestamp': timestamp.isoformat(),
            'download': download,
            'upload': upload
        }
        
        data = []
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
            except:
                data = []
        
        data.append(entry)
        
        with open(self.data_file, 'w') as f:
            json.dump(data[-1000:], f, indent=2)
            
    def test_speed(self):
        """速度テストを実行"""
        try:
            # 初回実行時にspeedtestを初期化
            if self.st is None:
                print("Initializing speedtest...")
                self.st = speedtest.Speedtest()
                
            self.st.get_best_server()
            download_speed = self.st.download() / 1_000_000  # Mbps
            upload_speed = self.st.upload() / 1_000_000      # Mbps
            return download_speed, upload_speed
        except Exception as e:
            print(f"Speed test error: {e}")
            # エラー時は再初期化を試行
            try:
                print("Retrying with new speedtest instance...")
                self.st = speedtest.Speedtest()
                self.st.get_best_server()
                download_speed = self.st.download() / 1_000_000
                upload_speed = self.st.upload() / 1_000_000
                return download_speed, upload_speed
            except Exception as e2:
                print(f"Retry failed: {e2}")
                return None, None
            
    def speed_test_worker(self):
        """バックグラウンドで速度テストを実行"""
        while self.running:
            download, upload = self.test_speed()
            if download is not None and upload is not None:
                timestamp = datetime.now()
                self.timestamps.append(timestamp)
                self.download_speeds.append(download)
                self.upload_speeds.append(upload)
                self.save_data(timestamp, download, upload)
                print(f"{timestamp.strftime('%H:%M:%S')} - Down: {download:.2f} Mbps, Up: {upload:.2f} Mbps")
            
            time.sleep(self.test_interval)
            
    def update_graph(self, frame):
        """グラフを更新"""
        if len(self.timestamps) == 0:
            return
            
        self.ax1.clear()
        self.ax2.clear()
        
        # 数値インデックスを使用してプロット
        x_values = list(range(len(self.timestamps)))
        times = [t.strftime('%H:%M:%S') for t in self.timestamps]
        
        # カラーパレット
        download_color = '#00FF41'  # Matrix green
        upload_color = '#FF0080'    # Neon pink
        bg_color = '#0D1117'        # Dark background
        grid_color = '#21262D'      # Dark grid
        
        # ダウンロード速度のプロット
        self.ax1.plot(x_values, list(self.download_speeds), 
                     color=download_color, linewidth=2, marker='o', 
                     markersize=5, markerfacecolor=download_color, 
                     markeredgecolor=bg_color, markeredgewidth=1,
                     label='Download', alpha=0.9)
        
        # アップロード速度のプロット
        self.ax2.plot(x_values, list(self.upload_speeds), 
                     color=upload_color, linewidth=2, marker='s', 
                     markersize=5, markerfacecolor=upload_color, 
                     markeredgecolor=bg_color, markeredgewidth=1,
                     label='Upload', alpha=0.9)
        
        # Y軸ラベルを左右に分離し、色を統一
        self.ax1.set_ylabel('Download Speed (Mbps)', color=download_color, fontsize=12, fontweight='bold')
        self.ax2.set_ylabel('Upload Speed (Mbps)', color=upload_color, fontsize=12, fontweight='bold')
        
        # Y軸の目盛りラベルの色を設定
        self.ax1.tick_params(axis='y', labelcolor=download_color, labelsize=10, colors=download_color)
        self.ax2.tick_params(axis='y', labelcolor=upload_color, labelsize=10, colors=upload_color)
        self.ax1.tick_params(axis='x', labelcolor='#58A6FF', labelsize=9, colors='#58A6FF')
        
        # アップロードのY軸ラベルを右側に配置
        self.ax2.yaxis.set_label_position('right')
        self.ax2.yaxis.tick_right()
        
        # 軸の線を明るくする（枠線として表示）
        self.ax1.spines['bottom'].set_color('#7FBAFF')  # より濃いブルー
        self.ax1.spines['left'].set_color('#40FF70')    # より濃いグリーン
        self.ax1.spines['top'].set_color('#7FBAFF')
        self.ax1.spines['right'].set_color('#FF40A0')   # より濃いピンク
        
        # 軸の線幅を太くする
        for spine in self.ax1.spines.values():
            spine.set_linewidth(2)
        
        # Y軸の範囲を動的に設定して変動を抑える
        if len(self.download_speeds) > 0:
            down_speeds = list(self.download_speeds)
            up_speeds = list(self.upload_speeds)
            
            # 現在の最大値から適切な範囲を計算
            max_down = max(down_speeds) if down_speeds else 100
            max_up = max(up_speeds) if up_speeds else 50
            
            # 画面サイズに応じてマージンを調整
            fig_width = self.fig.get_figwidth()
            fig_height = self.fig.get_figheight()
            aspect_ratio = fig_width / fig_height
            
            # ダウンロード軸を100Mbpsまで表示するように設定
            target_max = 100
            if max_down < target_max:
                down_margin = target_max - max_down
            else:
                down_margin = max_down * 0.2
            
            # アップロード軸の設定
            if aspect_ratio < 1.2:  # 縦長画面
                up_margin = max(15, max_up * 0.8)
            else:  # 横長画面
                up_margin = max(8, max_up * 0.4)
            
            # Y軸の範囲を設定
            down_max = max_down + down_margin
            up_max = max_up + up_margin
            
            self.ax1.set_ylim(0, down_max)
            self.ax2.set_ylim(0, up_max)
            
            # Y軸の目盛りを細かく設定（見た目の変動を抑制）
            import numpy as np
            
            # ダウンロード軸の目盛り設定
            if down_max <= 100:
                down_ticks = np.arange(0, down_max + 10, 10)  # 10Mbps間隔
            elif down_max <= 200:
                down_ticks = np.arange(0, down_max + 20, 20)  # 20Mbps間隔
            else:
                down_ticks = np.arange(0, down_max + 25, 25)  # 25Mbps間隔
            
            # アップロード軸の目盛り設定
            if up_max <= 50:
                up_ticks = np.arange(0, up_max + 5, 5)        # 5Mbps間隔
            else:
                up_ticks = np.arange(0, up_max + 10, 10)      # 10Mbps間隔
            
            self.ax1.set_yticks(down_ticks)
            self.ax2.set_yticks(up_ticks)
        
        # グリッドと背景
        self.ax1.grid(True, alpha=0.4, linestyle='-', linewidth=0.8, color='#30363D')
        self.ax1.grid(True, which='minor', alpha=0.2, linestyle=':', linewidth=0.5, color='#21262D')
        self.ax1.minorticks_on()
        self.ax1.set_facecolor(bg_color)
        self.fig.patch.set_facecolor(bg_color)
        
        # X軸の時刻ラベルを適切に設定（画面サイズに応じて調整）
        if len(times) > 0:
            # ウィンドウサイズを取得してラベル数を動的調整
            fig_width = self.fig.get_figwidth()
            fig_height = self.fig.get_figheight()
            aspect_ratio = fig_width / fig_height
            
            # 縦長画面では時刻ラベルを減らし、横長画面では増やす
            if aspect_ratio < 1.2:  # 縦長または正方形
                max_labels = 4
                rotation = 90
                fontsize = 8
            elif aspect_ratio < 1.8:  # 標準的な横長
                max_labels = 6
                rotation = 45
                fontsize = 9
            else:  # 超横長
                max_labels = 8
                rotation = 45
                fontsize = 9
                
            if len(times) <= max_labels:
                self.ax1.set_xticks(x_values)
                self.ax1.set_xticklabels(times, rotation=rotation, ha='right', fontsize=fontsize)
            else:
                step = max(1, len(times) // max_labels)
                tick_positions = list(range(0, len(times), step))
                if tick_positions[-1] != len(times) - 1:
                    tick_positions.append(len(times) - 1)
                self.ax1.set_xticks(tick_positions)
                self.ax1.set_xticklabels([times[i] for i in tick_positions], rotation=rotation, ha='right', fontsize=fontsize)
        
        # タイトル
        self.ax1.set_title('>>> NETWORK_SPEED_MONITOR', fontsize=14, fontweight='bold', 
                          pad=20, color='#58A6FF', family='monospace')
        
        # 現在の速度を表示 (レスポンシブ対応)
        if len(self.download_speeds) > 0 and len(self.upload_speeds) > 0:
            current_down = self.download_speeds[-1]
            current_up = self.upload_speeds[-1]
            
            # 画面サイズに応じてフォントサイズと位置を調整
            fig_width = self.fig.get_figwidth()
            fig_height = self.fig.get_figheight()
            aspect_ratio = fig_width / fig_height
            
            if aspect_ratio < 1.2:  # 縦長画面
                font_size = 9
                # 縦長の場合は上下に配置
                self.ax1.text(0.5, 0.98, f'[DL] {current_down:.1f} Mbps', 
                             transform=self.ax1.transAxes, fontsize=font_size, fontweight='bold',
                             verticalalignment='top', horizontalalignment='center', 
                             color=download_color, family='monospace',
                             bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_color, 
                                     edgecolor=download_color, alpha=0.8))
                self.ax1.text(0.5, 0.02, f'[UP] {current_up:.1f} Mbps', 
                             transform=self.ax1.transAxes, fontsize=font_size, fontweight='bold',
                             verticalalignment='bottom', horizontalalignment='center', 
                             color=upload_color, family='monospace',
                             bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_color, 
                                     edgecolor=upload_color, alpha=0.8))
                
                # 外部領域にステータス情報を追加
                self.add_hacker_status_external()
            else:  # 横長画面
                font_size = 11
                # 横長の場合は左右に配置
                self.ax1.text(0.02, 0.98, f'[DL] {current_down:.1f} Mbps', 
                             transform=self.ax1.transAxes, fontsize=font_size, fontweight='bold',
                             verticalalignment='top', color=download_color, family='monospace',
                             bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_color, 
                                     edgecolor=download_color, alpha=0.8))
                self.ax1.text(0.98, 0.98, f'[UP] {current_up:.1f} Mbps', 
                             transform=self.ax1.transAxes, fontsize=font_size, fontweight='bold',
                             verticalalignment='top', horizontalalignment='right', 
                             color=upload_color, family='monospace',
                             bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_color, 
                                     edgecolor=upload_color, alpha=0.8))
                
                # 横画面でも外部ステータス情報を表示
                self.add_hacker_status_external()
        
        plt.tight_layout()
    
    def add_hacker_status_vertical(self):
        """縦画面用のステータス情報を表示"""
        import datetime
        
        # 現在時刻とセッション情報
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 統計情報を計算
        if len(self.download_speeds) > 0:
            avg_down = sum(self.download_speeds) / len(self.download_speeds)
            max_down = max(self.download_speeds)
            avg_up = sum(self.upload_speeds) / len(self.upload_speeds)
            max_up = max(self.upload_speeds)
            samples = len(self.download_speeds)
        else:
            avg_down = avg_up = max_down = max_up = samples = 0
        
        # ステータステキスト
        status_texts = [
            f">>> SYS_TIME: {current_time}",
            f">>> SAMPLES: {samples:03d}",
            f">>> AVG_DL: {avg_down:.1f} Mbps",
            f">>> MAX_DL: {max_down:.1f} Mbps", 
            f">>> AVG_UP: {avg_up:.1f} Mbps",
            f">>> MAX_UP: {max_up:.1f} Mbps",
            ">>> STATUS: [OK]",
            ">>> CONN: STABLE",
            ">>> PROTO: TCP/IP",
            ">>> MODE: ACTIVE"
        ]
        
        # 右側に縦に表示（グラフと重ならないように）
        y_positions = [0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.45, 0.40, 0.35, 0.30]
        colors = ['#58A6FF', '#00FF41', '#00FF41', '#00FF41', '#FF0080', '#FF0080', 
                 '#00FF41', '#58A6FF', '#58A6FF', '#58A6FF']
        
        for text, y_pos, color in zip(status_texts, y_positions, colors):
            self.ax1.text(0.98, y_pos, text, 
                         transform=self.ax1.transAxes, fontsize=7, fontweight='bold',
                         verticalalignment='center', horizontalalignment='right',
                         color=color, family='monospace', alpha=0.8)
    
    def setup_layout(self):
        """画面サイズに応じてレイアウトを設定"""
        fig_width = self.fig.get_figwidth()
        fig_height = self.fig.get_figheight()
        aspect_ratio = fig_width / fig_height
        
        # 既存のaxesがあれば削除
        self.fig.clear()
        
        if aspect_ratio < 1.2:  # 縦長画面
            # 縦画面：上部にステータス、下部にグラフ（余白なし、間隔少し開ける）
            gs = self.fig.add_gridspec(2, 1, height_ratios=[1, 3], hspace=0.15, 
                                     top=0.98, bottom=0.05, left=0.1, right=0.95)
            self.status_ax = self.fig.add_subplot(gs[0])
            self.ax1 = self.fig.add_subplot(gs[1])
        else:  # 横長画面
            # 横画面：左側にステータス、右側にグラフ（左端余白なし）
            gs = self.fig.add_gridspec(1, 2, width_ratios=[1, 3], wspace=0.05,
                                     top=0.95, bottom=0.1, left=0.02, right=0.98)
            self.status_ax = self.fig.add_subplot(gs[0])
            self.ax1 = self.fig.add_subplot(gs[1])
        
        self.ax2 = self.ax1.twinx()
        
        # ステータス軸の設定
        self.status_ax.set_facecolor('#0D1117')
        self.status_ax.set_xticks([])
        self.status_ax.set_yticks([])
        for spine in self.status_ax.spines.values():
            spine.set_visible(False)
    
    def on_resize(self, event):
        """ウィンドウリサイズ時の処理"""
        self.setup_layout()
    
    def add_hacker_status_external(self):
        """外部領域にステータス情報を表示"""
        import datetime
        
        # ステータス軸をクリア
        self.status_ax.clear()
        self.status_ax.set_facecolor('#0D1117')
        self.status_ax.set_xticks([])
        self.status_ax.set_yticks([])
        for spine in self.status_ax.spines.values():
            spine.set_visible(False)
        
        # 現在時刻とセッション情報
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 統計情報を計算
        if len(self.download_speeds) > 0:
            avg_down = sum(self.download_speeds) / len(self.download_speeds)
            max_down = max(self.download_speeds)
            avg_up = sum(self.upload_speeds) / len(self.upload_speeds)
            max_up = max(self.upload_speeds)
            samples = len(self.download_speeds)
        else:
            avg_down = avg_up = max_down = max_up = samples = 0
        
        # カテゴリ別にASCIIアイコン付きステータステキスト
        status_texts = [
            # システム情報（青系）
            f"[T] SYS_TIME: {current_time}",
            f"[#] SAMPLES: {samples:03d}",
            
            # ダウンロード統計（緑系）
            f"[↓] AVG_DL: {avg_down:.1f} Mbps",
            f"[▲] MAX_DL: {max_down:.1f} Mbps",
            
            # アップロード統計（ピンク系）
            f"[↑] AVG_UP: {avg_up:.1f} Mbps",
            f"[△] MAX_UP: {max_up:.1f} Mbps",
            
            # 接続ステータス（青系）
            f"[✓] STATUS: [OK]",
            f"[~] CONN: STABLE",
            f"[N] PROTO: TCP/IP",
            f"[*] MODE: ACTIVE"
        ]
        
        # カテゴリ別色分け
        colors = [
            '#58A6FF', '#58A6FF',  # システム情報（青）
            '#00FF41', '#00FF41',  # ダウンロード統計（緑）
            '#FF0080', '#FF0080',  # アップロード統計（ピンク）
            '#58A6FF', '#58A6FF', '#58A6FF', '#58A6FF'  # 接続ステータス（青）
        ]
        
        # 画面の向きに応じて配置
        fig_width = self.fig.get_figwidth()
        fig_height = self.fig.get_figheight()
        aspect_ratio = fig_width / fig_height
        
        if aspect_ratio < 1.2:  # 縦長画面：横に並べる
            x_positions = [0.05, 0.55, 0.05, 0.55, 0.05, 0.55, 0.05, 0.55, 0.05, 0.55]
            y_positions = [0.85, 0.85, 0.65, 0.65, 0.45, 0.45, 0.25, 0.25, 0.05, 0.05]
        else:  # 横長画面：縦に並べる（左端余白を削減）
            x_positions = [0.02] * 10
            y_positions = [0.95 - i * 0.09 for i in range(10)]
        
        # カテゴリごとに枠で囲んで表示
        categories = [
            (status_texts[0:2], colors[0:2], "SYSTEM"),          # システム情報
            (status_texts[2:6], colors[2:6], "SPEED_STATS"),     # 速度統計（ダウンロード+アップロード）
            (status_texts[6:10], colors[6:10], "CONNECTION")     # 接続ステータス
        ]
        
        if aspect_ratio < 1.2:  # 縦長画面
            # 縦に3つのボックスを配置（バランス良く）
            cat_positions = [(0.02, 0.68), (0.02, 0.36), (0.02, 0.04)]
            box_width, box_height = 0.95, 0.28
        else:  # 横長画面
            # 横長でも重ならないように調整
            fig_area = fig_width * fig_height
            if fig_area < 30:  # 小さなウィンドウ
                cat_positions = [(0.02, 0.75), (0.02, 0.40), (0.02, 0.05)]
                box_width, box_height = 0.95, 0.30
            else:  # 通常サイズ
                cat_positions = [(0.02, 0.70), (0.02, 0.40), (0.02, 0.10)]
                box_width, box_height = 0.95, 0.25
        
        for (cat_texts, cat_colors, cat_name), (box_x, box_y) in zip(categories, cat_positions):
            # カテゴリボックスを描画
            rect = plt.Rectangle((box_x, box_y), box_width, box_height, 
                               linewidth=1, edgecolor=cat_colors[0], facecolor='none',
                               transform=self.status_ax.transAxes, alpha=0.6)
            self.status_ax.add_patch(rect)
            
            # カテゴリタイトル
            self.status_ax.text(box_x + 0.02, box_y + box_height - 0.05, f"[{cat_name}]",
                               transform=self.status_ax.transAxes, fontsize=8, fontweight='bold',
                               color=cat_colors[0], family='monospace', alpha=0.8)
            
            # カテゴリ内のテキスト
            for i, (text, color) in enumerate(zip(cat_texts, cat_colors)):
                if aspect_ratio < 1.2:  # 縦長画面
                    text_y = box_y + box_height - 0.08 - i * 0.06
                    text_x = box_x + 0.02
                else:  # 横長画面
                    text_y = box_y + box_height - 0.06 - i * 0.05
                    text_x = box_x + 0.02
                    
                self.status_ax.text(text_x, text_y, text,
                                   transform=self.status_ax.transAxes, fontsize=9, fontweight='bold',
                                   verticalalignment='center', color=color, family='monospace',
                                   alpha=0.9)
        
    def start_monitoring(self):
        """監視を開始"""
        self.running = True
        
        # ナビゲーションバーを非表示にする
        plt.rcParams['toolbar'] = 'None'
        
        # 画面サイズに応じてレイアウトを決定
        self.fig = plt.figure(figsize=(12, 6))
        
        # レイアウトの初期化（後でリサイズ時に調整）
        self.setup_layout()
        
        # ウィンドウのタイトルを設定 
        self.fig.canvas.manager.set_window_title('>>> NETWORK_SPEED_MONITOR')
        
        # リサイズイベントを監視
        self.fig.canvas.mpl_connect('resize_event', self.on_resize)
        
        test_thread = threading.Thread(target=self.speed_test_worker, daemon=True)
        test_thread.start()
        
        ani = animation.FuncAnimation(self.fig, self.update_graph, interval=5000, cache_frame_data=False)
        
        plt.show()
        
    def stop_monitoring(self):
        """監視を停止"""
        self.running = False

if __name__ == "__main__":
    print("Network Speed Monitor starting...")
    print("Testing initial connection...")
    
    monitor = NetworkSpeedMonitor(max_data_points=8640, test_interval=10)
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop_monitoring()