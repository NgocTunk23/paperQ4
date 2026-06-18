import argparse
import json
import sys
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
            start_road = road_link.get("startRoad")
            end_road = road_link.get("endRoad")
            if start_road and end_road:
                valid_routes.append([start_road, end_road])

    unique_routes = list(set(tuple(route) for route in valid_routes))
    return [list(route) for route in unique_routes]


def build_flow_data(valid_routes, scenario):
    flow_config = scenario["flow"]
    base_interval = flow_config["base_interval"]
    route_multiplier = flow_config["route_multiplier"]
    area_count = max(1, len(scenario["area_types"]))

    # region-aware weighting so user-defined coordinates affect traffic intensity.
    region_weight = 0.0
    for region in scenario.get("regions", []):
        area_type = region.get("area_type", "industrial")
        weight_map = {
            "school": 1.0,
            "hospital": 1.5,
            "industrial": 1.2,
        }
        region_weight += weight_map.get(area_type, 1.0)

    flows = []
    for route in valid_routes:
        interval = max(
            1.0,
            base_interval / (route_multiplier * (area_count + region_weight * 0.5)),
        )
        flows.append(
            {
                "vehicle": {
                    "length": flow_config["vehicle_length"],
                    "width": flow_config["vehicle_width"],
                    "maxSpeed": flow_config["max_speed"],
                    "maxPosAcc": 2.0,
                    "maxNegAcc": 4.5,
                    "usualPosAcc": 2.0,
                    "usualNegAcc": 4.5,
                    "minGap": 2.5,
                    "maxSpeedReplanning": flow_config["max_speed"],
                    "earliestStartReplanning": 0.0,
                    "headwayTime": 1.5,
                },
                "route": route,
                "interval": interval,
                "startTime": flow_config["start_time"],
                "endTime": flow_config["end_time"],
            }
        )
    return flows


def create_config_file(config_path: Path, flow_path: Path, replay_path: Path, roadnet_path: Path):
    config = {
        "interval": 1.0,
        "seed": 0,
        "dir": str(config_path.parent),
        "roadnetFile": str(roadnet_path),
        "flowFile": str(flow_path),
        "rlTrafficLight": False,
        "saveReplay": True,
        "roadnetLogFile": str(config_path.parent / "replay_roadnet.json"),
        "replayLogFile": str(replay_path),
    }
    save_json(config_path, config)


def run_simulation(config_path: Path):
    if cityflow is None:
        print("❗ cityflow chưa được cài đặt. Chỉ tạo file cấu hình cho AI/kiểm thử, chưa chạy mô phỏng.")
        return False

    try:
        eng = cityflow.Engine(str(config_path), thread_num=1)
    except Exception as e:
        print(f"❌ Không thể khởi động CityFlow: {e}")
        return False

    print("\n==== BƯỚC 2: KHỞI ĐỘNG ENGINE MÔ PHỎNG CITYFLOW ====")
    print(f" -> Đang chạy mô phỏng với config: {config_path}")

    TOTAL_STEPS = 300
    for step in range(TOTAL_STEPS):
        eng.next_step()
        if step % 100 == 0:
            waiting_cars = eng.get_lane_waiting_vehicle_count()
            total_waiting = sum(waiting_cars.values())
            active_vehicles = eng.get_vehicle_count()
            print(f"   [Bước {step}] Tổng xe đang chạy: {active_vehicles} | Số xe kẹt/chờ: {total_waiting} xe.")

    print("\n 🎉 GIẢ LẬP HOÀN TẤT THÀNH CÔNG!")
    print(f" -> File kết quả mô phỏng: {config_path.parent / 'replay_log.txt'}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run traffic simulation with scenario config support.")
    parser.add_argument(
        "--scenario",
        default=str(DEFAULT_SCENARIO),
        help="Đường dẫn đến file JSON mô tả kịch bản (ví dụ: scenarios/area_school.json)",
    )
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        print(f"❌ File scenario không tồn tại: {scenario_path}")
        return 1

    scenario = load_scenario(scenario_path)
    output_dir = Path(scenario["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"==== KỊCH BẢN: {scenario['name']} ({scenario['id']}) ====")
    print(f" -> Loại khu vực: {', '.join(scenario['area_types']) if scenario['area_types'] else 'không xác định'}")
    print(f" -> Số vùng nhập tay: {len(scenario.get('regions', []))}")
    for region in scenario.get("regions", []):
        lat = region.get("latitude")
        lon = region.get("longitude")
        print(
            f"   -> Vùng '{region.get('name')}' ({region.get('area_type')}) "
            f"tọa độ={lat}, {lon} bán kính={region.get('radius_km')} km"
        )
    print(f" -> Đường tắt: {len(scenario['road_closures'])} mục")

    roadnet_path = Path("roadnet.json")
    if not roadnet_path.exists():
        print("❌ Không tìm thấy roadnet.json! Hãy chạy build_roadnet.py trước.")
        return 1

    roadnet = load_roadnet(roadnet_path)
    valid_routes = find_valid_routes(roadnet)

    save_json(output_dir / "scenario.json", scenario)
    save_json(output_dir / "closures.json", {"road_closures": scenario["road_closures"]})

    flows = build_flow_data(valid_routes, scenario)
    flow_path = output_dir / "flow.json"
    save_json(flow_path, flows)

    config_path = output_dir / "config.json"
    replay_path = output_dir / "replay_log.txt"
    create_config_file(config_path, flow_path, replay_path, roadnet_path)

    print(f" -> Tìm thấy {len(valid_routes)} lộ trình hợp lệ.")
    print(f" -> Đã tạo flow.json tại {flow_path}")
    print(f" -> Đã tạo config.json tại {config_path}")

    run_simulation(config_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())