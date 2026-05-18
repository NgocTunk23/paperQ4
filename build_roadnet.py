import os
import sys
import requests
import subprocess

# =====================================================================
# CẤU HÌNH KHUNG TỌA ĐỘ QUẬN 1
# =====================================================================
SOUTH = 10.768
WEST = 106.693
NORTH = 10.782
EAST = 106.710

OSM_FILE = "map.osm"
SUMO_NET_FILE = "map.net.xml"
ROADNET_FILE = "roadnet.json"

def download_osm_data():
    # Kiểm tra nếu file đã có và lớn hơn 1KB thì không tải lại
    if os.path.exists(OSM_FILE) and os.path.getsize(OSM_FILE) > 1000:
        print(f"[1] Tìm thấy file {OSM_FILE} hợp lệ. Bỏ qua bước tải.")
        return True

    print(f"[1] Bắt đầu tiến trình tải bản đồ...")
    # Sử dụng OpenStreetMap Export API chính thức (Bbox format: left, bottom, right, top)
    API_URL = f"https://api.openstreetmap.org/api/0.6/map?bbox={WEST},{SOUTH},{EAST},{NORTH}"
    headers = {
        "User-Agent": "CityFlow-Traffic-Bot/1.0"
    }
    
    print(f" -> Đang kết nối tới API gốc của OSM: {API_URL}")
    try:
        response = requests.get(API_URL, headers=headers, timeout=300)
        
        if response.status_code == 200:
            with open(OSM_FILE, "wb") as f:
                f.write(response.content)
            
            # Kiểm tra nhanh xem file XML có chứa tọa độ (<node>) không
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
    print(f"[2] Bắt đầu chuyển đổi OSM -> SUMO Net...")
    netconvert_cmd = [
        "netconvert",
        "--osm-files", OSM_FILE,
        "-o", SUMO_NET_FILE,
        "--geometry.remove", "true",
        "--roundabouts.guess", "true",
        "--tls.guess-signals", "true",
        "--junctions.join", "true"
    ]
    
    try:
        subprocess.run(netconvert_cmd, check=True)
        print(f" ✅ Đã sinh thành công {SUMO_NET_FILE}")
    except subprocess.CalledProcessError as e:
        print(f" ❌ Lỗi khi chạy SUMO netconvert: {e}")
        sys.exit(1)

    print(f"[3] Bắt đầu chuyển đổi SUMO Net -> CityFlow Roadnet...")
    converter_cmd = [
        "python", "converter.py",
        "--sumonet", SUMO_NET_FILE,
        "--cityflownet", ROADNET_FILE
    ]
    
    try:
        subprocess.run(converter_cmd, check=True)
        print(f" 🎉 HOÀN TẤT 100%! Đã tạo thành công cấu hình chuẩn: {ROADNET_FILE}")
    except subprocess.CalledProcessError as e:
        print(f" ❌ Lỗi khi chạy CityFlow converter: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*60)
    print("BẮT ĐẦU QUY TRÌNH TẠO ROADNET TIÊU CHUẨN (CÓ ĐÈN GIAO THÔNG)")
    print("="*60)
    
    # Dọn dẹp file rác của các lần chạy lỗi trước (nếu dung lượng < 1KB)
    if os.path.exists(OSM_FILE) and os.path.getsize(OSM_FILE) < 1000:
        os.remove(OSM_FILE)
        
    if download_osm_data():
        build_standard_roadnet()
    else:
        print("💥 THẤT BẠI: Không thể tải bản đồ từ máy chủ!")
        sys.exit(1)