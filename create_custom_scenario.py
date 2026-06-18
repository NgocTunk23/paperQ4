from __future__ import annotations

import json
from pathlib import Path

from scenario_config import VALID_AREA_TYPES


def ask_text(prompt: str, default: str = "") -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else default


def ask_float(prompt: str, default: float | None = None) -> float:
    raw = input(f"{prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
    if not raw:
        if default is None:
            raise ValueError(f"Bạn phải nhập giá trị cho {prompt}")
        return default
    return float(raw)


def ask_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    return int(raw) if raw else default


def main() -> int:
    print("=" * 60)
    print("TẠO SCENARIO THEO TỌA ĐỘ CỦA BẠN")
    print("=" * 60)

    scenario_id = ask_text("Nhập ID scenario", "custom_area")
    scenario_name = ask_text("Nhập tên scenario", scenario_id)
    description = ask_text("Nhập mô tả ngắn", "Scenario nhập tay bằng tọa độ")
    output_name = ask_text("Tên file JSON lưu", f"{scenario_id}.json")

    region_count = ask_int("Số vùng khu vực muốn nhập", 1)

    regions = []
    area_types = []

    for i in range(1, region_count + 1):
        print(f"\n--- Vùng {i} ---")
        region_name = ask_text(f"Tên vùng {i}", f"region_{i}")
        area_type = ask_text(
            f"Loại vùng {i} ({', '.join(VALID_AREA_TYPES)})",
            "hospital",
        )
        if area_type not in VALID_AREA_TYPES:
            print(f"⚠️ Loại '{area_type}' không hợp lệ, dùng 'industrial' mặc định")
            area_type = "industrial"

        latitude = ask_float(f"Vĩ độ (latitude) cho {region_name}", 10.78)
        longitude = ask_float(f"Kinh độ (longitude) cho {region_name}", 106.70)
        radius_km = ask_float(f"Bán kính vùng (km)", 1.0)
        notes = ask_text(f"Ghi chú cho {region_name}", "")

        regions.append(
            {
                "name": region_name,
                "area_type": area_type,
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
                "notes": notes,
            }
        )
        area_types.append(area_type)

    scenario = {
        "id": scenario_id,
        "name": scenario_name,
        "description": description,
        "area_types": list(dict.fromkeys(area_types)),
        "regions": regions,
        "flow": {
            "base_interval": 12.0,
            "start_time": 0,
            "end_time": 3600,
            "route_multiplier": 1.0,
        },
        "road_closures": [
            {
                "road_id": "example_road_id",
                "reason": "custom_region_input",
                "start_time": 300,
                "end_time": 600,
                "severity": "medium",
            }
        ],
    }

    output_path = Path("scenarios") / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scenario, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\n✅ Đã tạo scenario thành công:")
    print(f" -> {output_path}")
    print("\nBạn có thể chạy bằng:")
    print(f" -> python simulate.py --scenario {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
