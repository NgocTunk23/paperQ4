import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

# Thời gian nghỉ giữa các lần cào dữ liệu TomTom (1200 giây = 20 phút)
INTERVAL_SECONDS = 300  # 3600 giây = 1 tiếng, điều chỉnh tùy theo nhu cầu


def run_task(script_name, scenario=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{current_time}] -> Đang thực thi: {script_name}...")
    try:
        command = [sys.executable, script_name]
        if scenario:
            command.extend(["--scenario", scenario])
        subprocess.run(command, check=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] -> {script_name} hoàn thành thành công.")
        return True
    except Exception as e:
        print(f"[{current_time}] ❌ LỖI khi chạy {script_name}: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy hệ thống mô phỏng giao thông theo kịch bản.")
    parser.add_argument(
        "--scenario",
        default="scenarios/area_all.json",
        help="File JSON mô tả kịch bản khu vực và tắt đường.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("KHỞI ĐỘNG HỆ THỐNG ĐIỀU PHỐI GIAO THÔNG TỰ ĐỘNG TRÊN DOCKER")
    print("=" * 60)

    print("\n[BƯỚC CHUẨN BỊ BẢN ĐỒ & GIẢ LẬP]")

    if not os.path.exists("roadnet.json"):
        run_task("build_roadnet.py", scenario=args.scenario)
    else:
        print("-> Đã có sẵn file roadnet.json, bỏ qua bước khởi tạo bản đồ.")

    run_task("simulate.py", scenario=args.scenario)

    print(f"\n[BƯỚC THU THẬP DATA] Bắt đầu quét dữ liệu TomTom định kỳ mỗi {INTERVAL_SECONDS // 60} phút.")
    while True:
        run_task("main.py")
        print(f" -> Đang ngủ {INTERVAL_SECONDS // 60} phút trước lượt quét kế tiếp...")
        time.sleep(INTERVAL_SECONDS)