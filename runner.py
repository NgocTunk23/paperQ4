import subprocess
import time
from datetime import datetime
import sys

# Đặt thời gian nghỉ (tính bằng giây). 
# 1200s = 20 phút (Khuyên dùng để không vượt 2500 request/ngày của TomTom)
# 900s  = 15 phút 
INTERVAL_SECONDS = 3600 # 1 giờ

def run_script():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{current_time}] BẮT ĐẦU CHẠY THU THẬP DỮ LIỆU...")
    
    try:
        # Gọi chạy file main.py
        subprocess.run([sys.executable, "main.py"], check=True)
    except Exception as e:
        print(f"[{current_time}] Lỗi khi chạy main.py: {e}")
        
    next_run = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{next_run}] HOÀN TẤT. Sẽ chạy lại sau {INTERVAL_SECONDS // 60} phút nữa...")

if __name__ == "__main__":
    print(f"Khởi động hệ thống tự động quét giao thông mỗi {INTERVAL_SECONDS // 60} phút.")
    while True:
        run_script()
        # Cho chương trình "ngủ" cho đến lần chạy tiếp theo
        time.sleep(INTERVAL_SECONDS)