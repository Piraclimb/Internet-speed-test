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
        self.st = speedtest.Speedtest()
        
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
            self.st.get_best_server()
            download_speed = self.st.download() / 1_000_000  # Mbps
            upload_speed = self.st.upload() / 1_000_000      # Mbps
            return download_speed, upload_speed
        except Exception as e:
            print(f"Speed test error: {e}")
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
        
        self.ax1.plot(x_values, list(self.download_speeds), 'b-', label='Download', linewidth=2, marker='o', markersize=4)
        self.ax1.set_ylabel('Download Speed (Mbps)', color='b')
        self.ax1.tick_params(axis='y', labelcolor='b')
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.plot(x_values, list(self.upload_speeds), 'r-', label='Upload', linewidth=2, marker='s', markersize=4)
        self.ax2.set_ylabel('Upload Speed (Mbps)', color='r')
        self.ax2.tick_params(axis='y', labelcolor='r')
        
        # X軸の時刻ラベルを適切に設定
        if len(times) > 0:
            # 表示する時刻ラベルの数を制限
            max_labels = 8
            if len(times) <= max_labels:
                self.ax1.set_xticks(x_values)
                self.ax1.set_xticklabels(times, rotation=45, ha='right')
            else:
                step = max(1, len(times) // max_labels)
                tick_positions = list(range(0, len(times), step))
                if tick_positions[-1] != len(times) - 1:
                    tick_positions.append(len(times) - 1)
                self.ax1.set_xticks(tick_positions)
                self.ax1.set_xticklabels([times[i] for i in tick_positions], rotation=45, ha='right')
        
        self.ax1.set_title('Network Speed Monitor - Real Time')
        self.ax1.legend(loc='upper left')
        self.ax2.legend(loc='upper right')
        plt.tight_layout()
        
    def start_monitoring(self):
        """監視を開始"""
        self.running = True
        
        self.fig, self.ax1 = plt.subplots(figsize=(12, 6))
        self.ax2 = self.ax1.twinx()
        
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
    
    monitor = NetworkSpeedMonitor(max_data_points=100000, test_interval=5)
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop_monitoring()