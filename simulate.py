import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path

from scenario_config import DEFAULT_SCENARIO, load_scenario

try:
    import cityflow
except ImportError:
    cityflow = None

def ensure_writable_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        if os.access(path, os.W_OK):
            return path
    except OSError:
        pass

    fallback = Path.home() / "paperforQ4_outputs" / path.name
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def save_json(file_path: Path, payload):
    file_path = ensure_writable_dir(file_path.parent) / file_path.name
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)

def load_roadnet(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def find_valid_routes(roadnet):
    valid_routes = []
    
    # Lấy ra danh sách các con đường dài và an toàn (tránh các đoạn hẻm/giao lộ siêu ngắn)
    safe_roads = set()
    for road in roadnet.get("roads", []):
        # Dựa vào số điểm cong (points), thường đường chính sẽ có nhiều points hoặc đủ dài
        if len(road.get("lanes", [])) > 0:
            safe_roads.add(road["id"])

    for intersection in roadnet.get("intersections", []):
        if intersection.get("virtual", False):
            continue
        for road_link in intersection.get("roadLinks", []):
            if len(road_link.get("laneLinks", [])) > 0:
                start_road = road_link.get("startRoad")
                end_road = road_link.get("endRoad")
                
                # CHỈ tạo lộ trình nếu cả đường nối đều là đường an toàn
                if start_road in safe_roads and end_road in safe_roads:
                    valid_routes.append([start_road, end_road])

    unique_routes = list(set(tuple(route) for route in valid_routes))
    return [list(route) for route in unique_routes]

def build_flow_data(valid_routes, scenario):
    flow_config = scenario.get("flow", {})
    base_interval = max(3.0, float(flow_config.get("base_interval", 8.0)))
    route_multiplier = max(0.2, float(flow_config.get("route_multiplier", 1.0)))
    start_time = int(flow_config.get("start_time", 0))
    end_time = int(flow_config.get("end_time", 900))

    max_routes = min(len(valid_routes), 40)
    if len(valid_routes) > max_routes:
        random.seed(42)
        valid_routes = random.sample(valid_routes, max_routes)

    flows = []
    for i, route in enumerate(valid_routes):
        interval = max(3.0, base_interval * route_multiplier)
        flows.append(
            {
                "vehicle": {
                    "length": float(flow_config.get("vehicle_length", 3.5)),
                    "width": float(flow_config.get("vehicle_width", 1.8)),
                    "maxPosAcc": 2.0,
                    "maxNegAcc": 4.5,
                    "usualPosAcc": 2.0,
                    "usualNegAcc": 4.5,
                    "minGap": 1.5,
                    "maxSpeed": float(flow_config.get("max_speed", 16.67)),
                    "maxSpeedReplanning": float(flow_config.get("max_speed", 16.67)),
                    "earliestStartReplanning": 0.0,
                    "headwayTime": 1.0,
                },
                "route": route,
                "interval": interval,
                "startTime": start_time + (i % 5),
                "endTime": end_time,
            }
        )
    return flows


def create_config_file(config_path: Path, flow_path: Path, replay_path: Path, roadnet_path: Path):
    config_dir = ensure_writable_dir(config_path.parent)
    config_path = config_dir / config_path.name
    flow_path = config_dir / flow_path.name
    replay_path = config_dir / replay_path.name

    # CityFlow expects config['dir'] + config['roadnetFile'] / config['flowFile'].
    # So both files must be relative to the same base directory, and the directory
    # must end with a separator.
    roadnet_copy_path = config_dir / roadnet_path.name
    shutil.copy2(roadnet_path, roadnet_copy_path)

    config = {
        "interval": 1.0,
        "seed": 0,
        "dir": str(config_dir.resolve()) + "/",
        "roadnetFile": roadnet_copy_path.name,
        "flowFile": flow_path.name,
        "rlTrafficLight": False,
        "saveReplay": False,
        "roadnetLogFile": "replay_roadnet.json",
        "replayLogFile": replay_path.name,
    }
    save_json(config_path, config)

def run_simulation(config_path: Path):
    if cityflow is None:
        print("❗ cityflow chưa được cài đặt. Chỉ tạo file cấu hình cho kiểm thử.")
        return False

    abs_config_path = str(config_path.resolve())
    print(f" -> Đang nạp Engine với config: {abs_config_path}")

    try:
        eng = cityflow.Engine(abs_config_path, thread_num=1)
    except Exception as e:
        print(f"❌ Lỗi Engine CityFlow: {e}")
        return False

    print("\n==== BƯỚC 2: KHỞI ĐỘNG MÔ PHỎNG ====")
    TOTAL_STEPS = 60
    try:
        print(" -> Bắt đầu chạy từng bước mô phỏng...")
        for step in range(TOTAL_STEPS):
            eng.next_step()
            if step == 0 or step % 10 == 0:
                active_vehicles = eng.get_vehicle_count()
                print(f"   [Bước {step}] Tổng xe đang chạy trên bản đồ: {active_vehicles} chiếc.")
    except Exception as e:
        print(f"❌ Lỗi xảy ra khi chạy mô phỏng CityFlow: {e}")
        return False

    print("\n 🎉 GIẢ LẬP HOÀN TẤT THÀNH CÔNG!")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default=str(DEFAULT_SCENARIO))
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    scenario = load_scenario(scenario_path)
    output_dir = Path(scenario.get("output_dir", f"outputs/{scenario['id']}"))
    output_dir = ensure_writable_dir(output_dir)
    print(f" -> Sử dụng thư mục output: {output_dir.resolve()}")

    roadnet_path = Path("roadnet.json")
    if not roadnet_path.exists():
        print("❌ Không tìm thấy roadnet.json! Hãy chạy build_roadnet.py trước.")
        return 1

    roadnet = load_roadnet(roadnet_path)
    valid_routes = find_valid_routes(roadnet)

    if not valid_routes:
        print("❌ Không tìm thấy lộ trình hợp lệ nào trong roadnet.json.")
        return 1

    flows = build_flow_data(valid_routes, scenario)
    flow_path = output_dir / "flow.json"
    save_json(flow_path, flows)

    config_path = output_dir / "config.json"
    replay_path = output_dir / "replay_log.txt"
    create_config_file(config_path, flow_path, replay_path, roadnet_path)

    print(f" -> Đã thiết lập {len(flows)} lộ trình xe chạy.")
    run_simulation(config_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())