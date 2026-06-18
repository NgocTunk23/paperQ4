import argparse
import json
import sys
import random
from pathlib import Path
from scenario_config import DEFAULT_SCENARIO, load_scenario

try:
    import cityflow
except ImportError:
    cityflow = None

def save_json(file_path: Path, payload):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)

def load_roadnet(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def find_valid_routes(roadnet):
    valid_routes = []
    for intersection in roadnet.get("intersections", []):
        if intersection.get("virtual", False):
            continue
        for road_link in intersection.get("roadLinks", []):
            # CHỈ lấy những route có liên kết làn đường (tránh lỗi cụt đường gây Segfault)
            if len(road_link.get("laneLinks", [])) > 0:
                start_road = road_link.get("startRoad")
                end_road = road_link.get("endRoad")
                if start_road and end_road:
                    valid_routes.append([start_road, end_road])

    unique_routes = list(set(tuple(route) for route in valid_routes))
    return [list(route) for route in unique_routes]

def build_flow_data(valid_routes):
    flows = []
    for route in valid_routes:
        flows.append({
            "vehicle": {
                "length": 5.0,
                "width": 2.0,
                "maxPosAcc": 2.0,
                "maxNegAcc": 4.5,
                "usualPosAcc": 2.0,
                "usualNegAcc": 4.5,
                "minGap": 2.5,
                "maxSpeed": 16.67,
                "headwayTime": 1.5
            },
            "route": route,
            "interval": 20.0,  # 20 giây mới ra 1 xe để đảm bảo RAM không bị ngộp
            "startTime": 0,
            "endTime": 3600
        })
    return flows

def create_config_file(config_path: Path, flow_path: Path, replay_path: Path, roadnet_path: Path):
    # Dùng đường dẫn tương đối chuẩn của CityFlow
    config = {
        "interval": 1.0,
        "seed": 0,
        "dir": f"{config_path.parent}/",      # Đặt thư mục gốc là outputs/area_all/
        "roadnetFile": "../../roadnet.json",  # Lùi 2 bước để thấy file roadnet ở ngoài cùng
        "flowFile": "flow.json",              # Nằm ngay trong dir
        "rlTrafficLight": False,
        "saveReplay": True,
        "roadnetLogFile": "replay_roadnet.json",
        "replayLogFile": "replay_log.txt",
    }
    save_json(config_path, config)

def run_simulation(config_path: Path):
    if cityflow is None:
        print("❗ cityflow chưa được cài đặt.")
        return False

    print(f" -> Đang nạp Engine với config: {config_path.resolve()}")
    try:
        # Nếu hàm này không lỗi nghĩa là map và flow đã hợp lệ 100%
        eng = cityflow.Engine(str(config_path.resolve()), thread_num=1)
    except Exception as e:
        print(f"❌ Lỗi Engine CityFlow: {e}")
        return False

    print("\n==== BƯỚC 2: KHỞI ĐỘNG MÔ PHỎNG ====")
    TOTAL_STEPS = 300
    for step in range(TOTAL_STEPS):
        eng.next_step()
        if step % 50 == 0:
            active_vehicles = eng.get_vehicle_count()
            print(f"   [Bước {step}] Tổng xe đang chạy trên bản đồ: {active_vehicles} chiếc.")

    print("\n 🎉 GIẢ LẬP HOÀN TẤT THÀNH CÔNG!")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default=str(DEFAULT_SCENARIO))
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    scenario = load_scenario(scenario_path)
    output_dir = Path(scenario.get("output_dir", "outputs/area_all"))
    
    roadnet_path = Path("roadnet.json")
    if not roadnet_path.exists():
        print("❌ Không tìm thấy roadnet.json!")
        return 1

    roadnet = load_roadnet(roadnet_path)
    valid_routes = find_valid_routes(roadnet)

    # Cực kỳ quan trọng: Giới hạn xuống chỉ 100 con đường để chạy cực mượt, không sập RAM
    if len(valid_routes) > 100:
        random.seed(42)
        valid_routes = random.sample(valid_routes, 100)

    flows = build_flow_data(valid_routes)
    flow_path = output_dir / "flow.json"
    save_json(flow_path, flows)

    config_path = output_dir / "config.json"
    replay_path = output_dir / "replay_log.txt"
    create_config_file(config_path, flow_path, replay_path, roadnet_path)

    print(f" -> Đã thiết lập an toàn {len(valid_routes)} lộ trình xe chạy.")
    run_simulation(config_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())