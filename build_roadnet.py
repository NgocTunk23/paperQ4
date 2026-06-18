import argparse
import os
import subprocess
import sys

import requests

from scenario_config import load_scenario

# Default bbox for the sample area if the user does not specify one.
DEFAULT_BBOX = {
    "south": 10.768,
    "west": 106.693,
    "north": 10.782,
    "east": 106.710,
}

OSM_FILE = "map.osm"
SUMO_NET_FILE = "map.net.xml"
ROADNET_FILE = "roadnet.json"


def get_bbox_from_scenario(path):
    if not path:
        return DEFAULT_BBOX

    scenario = load_scenario(path)
    bbox = scenario.get("bbox")
    if bbox:
        return bbox

    regions = scenario.get("regions", [])
    region_boxes = [region.get("bbox") for region in regions if region.get("bbox")]
    if region_boxes:
        south = min(item.get("south", DEFAULT_BBOX["south"]) for item in region_boxes)
        west = min(item.get("west", DEFAULT_BBOX["west"]) for item in region_boxes)
        north = max(item.get("north", DEFAULT_BBOX["north"]) for item in region_boxes)
        east = max(item.get("east", DEFAULT_BBOX["east"]) for item in region_boxes)
        return {"south": south, "west": west, "north": north, "east": east}

    return DEFAULT_BBOX


def download_osm_data(bbox):
    if os.path.exists(OSM_FILE) and os.path.getsize(OSM_FILE) > 1000:
        print(f"[1] Tìm thấy file {OSM_FILE} hợp lệ. Bỏ qua bước tải.")
        return True

    print(f"[1] Bắt đầu tiến trình tải bản đồ...")
    api_url = (
        f"https://overpass-api.de/api/map?bbox={bbox['west']},{bbox['south']},"
        f"{bbox['east']},{bbox['north']}"
    )
    headers = {"User-Agent": "CityFlow-Traffic-Bot/1.0"}

    print(f" -> Đang kết nối tới API gốc của OSM: {api_url}")
    try:
        response = requests.get(api_url, headers=headers, timeout=300)
        if response.status_code == 200:
            with open(OSM_FILE, "wb") as f:
                f.write(response.content)

            with open(OSM_FILE, "r", encoding="utf-8", errors="ignore") as f:
                if "<node" not in f.read(2000):
                    print(" ❌ File tải về thành công nhưng không chứa dữ liệu giao thông (file rỗng/thông báo lỗi)!")
                    return False

            print(f" ✅ THÀNH CÔNG! Đã tải xong dữ liệu {OSM_FILE} chuẩn.")
            return True
        else:
            print(f" ❌ Server phản hồi lỗi: {response.status_code}")
            print(f" Chi tiết: {response.text[:200]}")
    except Exception as e:
        print(f" ⚠️ Lỗi kết nối: {e}")

    return False


def build_standard_roadnet():
    print("[2] Bắt đầu chuyển đổi OSM -> SUMO Net...")
    netconvert_cmd = [
        "netconvert",
        "--osm-files", OSM_FILE,
        "-o", SUMO_NET_FILE,
        "--geometry.remove", "true",
        "--roundabouts.guess", "true",
        "--tls.guess-signals", "true",
        "--junctions.join", "true",
    ]

    try:
        subprocess.run(netconvert_cmd, check=True)
        print(f" ✅ Đã sinh thành công {SUMO_NET_FILE}")
    except subprocess.CalledProcessError as e:
        print(f" ❌ Lỗi khi chạy SUMO netconvert: {e}")
        sys.exit(1)

    print("[3] Bắt đầu chuyển đổi SUMO Net -> CityFlow Roadnet...")
    converter_cmd = [
        "python", "converter.py",
        "--sumonet", SUMO_NET_FILE,
        "--cityflownet", ROADNET_FILE,
    ]

    try:
        subprocess.run(converter_cmd, check=True)
        print(f" 🎉 HOÀN TẤT 100%! Đã tạo thành công cấu hình chuẩn: {ROADNET_FILE}")
    except subprocess.CalledProcessError as e:
        print(f" ❌ Lỗi khi chạy CityFlow converter: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo roadnet cho một vùng cụ thể bằng tọa độ bbox.")
    parser.add_argument(
        "--scenario",
        default=None,
        help="Đường dẫn tới file scenario JSON để lấy bbox cần dùng.",
    )
    args = parser.parse_args()

    bbox = get_bbox_from_scenario(args.scenario)
    print("=" * 60)
    print("BẮT ĐẦU QUY TRÌNH TẠO ROADNET THEO BBOX")
    print(f"BBox dùng: south={bbox['south']}, west={bbox['west']}, north={bbox['north']}, east={bbox['east']}")
    print("=" * 60)

    if os.path.exists(OSM_FILE) and os.path.getsize(OSM_FILE) < 1000:
        os.remove(OSM_FILE)

    if download_osm_data(bbox):
        build_standard_roadnet()
    else:
        print("💥 THẤT BẠI: Không thể tải bản đồ từ máy chủ!")
        sys.exit(1)