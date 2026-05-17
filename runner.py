import subprocess
import time
from datetime import datetime
import sys
import os

# Thời gian nghỉ giữa các lần cào dữ liệu TomTom (1200 giây = 20 phút)
INTERVAL_SECONDS = 3600 # 3600 giây = 1 tiếng, điều chỉnh tùy theo nhu cầu

def run_task(script_name):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{current_time}] -> Đang thực thi: {script_name}...")
    try:
        # Gọi file python chạy ngầm trong hệ thống
        subprocess.run([sys.executable, script_name], check=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] -> {script_name} hoàn thành thành công.")
        return True
    except Exception as e:
        print(f"[{current_time}] ❌ LỖI khi chạy {script_name}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("KHỞI ĐỘNG HỆ THỐNG ĐIỀU PHỐI GIAO THÔNG TỰ ĐỘNG TRÊN DOCKER")
    print("=" * 60)

    # BƯỚC THIẾT LẬP BAN ĐẦU (Chỉ chạy 1 lần khi bật Docker)
    print("\n[BƯỚC CHUẨN BỊ BẢN ĐỒ & GIẢ LẬP]")
    
    # 1. Tạo file roadnet.json từ OpenStreetMap
    if not os.path.exists("roadnet.json"):
        run_task("build_roadnet.py")
    else:
        print("-> Đã có sẵn file roadnet.json, bỏ qua bước khởi tạo bản đồ.")

    # 2. Chạy thử nghiệm giả lập CityFlow
    run_task("simulate.py")

    # BƯỚC CHẠY LIÊN TỤC (Vòng lặp vô hạn cào dữ liệu thực tế)
    print(f"\n[BƯỚC THU THẬP DATA] Bắt đầu quét dữ liệu TomTom định kỳ mỗi {INTERVAL_SECONDS // 60} phút.")
    while True:
        run_task("main.py")
        
        print(f" -> Đang ngủ {INTERVAL_SECONDS // 60} phút trước lượt quét kế tiếp...")
        time.sleep(INTERVAL_SECONDS)