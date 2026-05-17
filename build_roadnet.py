import requests
import json
import os
import xml.etree.ElementTree as ET

# =====================================================================
# CẤU HÌNH KHUNG TỌA ĐỘ BẢN ĐỒ (Quận 1 - TP.HCM)
# =====================================================================
SOUTH = 10.768
WEST = 106.693
NORTH = 10.782
EAST = 106.710

OSM_FILE = "map.osm"
ROADNET_FILE = "roadnet.json"

def download_osm_data():
    # Nếu file map.osm đã tồn tại từ lần chạy trước thành công, bỏ qua không tải lại
    if os.path.exists(OSM_FILE) and os.path.getsize(OSM_FILE) > 1000:
        print(f"[1] Tìm thấy file {OSM_FILE} có sẵn. Bỏ qua bước tải.")
        return True

    print(f"[1] Bắt đầu kích hoạt tiến trình tải bản đồ vùng Quận 1...")
    API_SERVERS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    
    query = f"[out:xml][timeout:90];(node({SOUTH},{WEST},{NORTH},{EAST});way({SOUTH},{WEST},{NORTH},{EAST});relation({SOUTH},{WEST},{NORTH},{EAST}););out body;>;out skel qt;"
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "text/plain"}
    
    for url in API_SERVERS:
        print(f" -> Đang thử kết nối tới: {url} ...")
        try:
            response = requests.post(url, data=query.encode('utf-8'), headers=headers, timeout=20)
            if response.status_code == 200:
                with open(OSM_FILE, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f" ✅ THÀNH CÔNG! Đã tải xong dữ liệu bản đồ.")
                return True
        except Exception:
            pass
    return False

def convert_osm_to_roadnet_native():
    print(f"[2] Đang bóc tách NATIVE và chuyển đổi {OSM_FILE} sang {ROADNET_FILE}...")
    if not os.path.exists(OSM_FILE):
        print(f" ❌ Thất bại: Không tìm thấy file {OSM_FILE} để chuyển đổi!")
        return
    
    try:
        tree = ET.parse(OSM_FILE)
        root = tree.getroot()
        
        # 1. Thu thập tất cả các Node (Điểm tọa độ) và quy đổi sang hệ Mét (X, Y)
        nodes = {}
        for node in root.findall('node'):
            nid = node.get('id')
            lat = float(node.get('lat'))
            lon = float(node.get('lon'))
            
            # Chuyển đổi từ Kinh/Vĩ độ sang mét (Lấy điểm Tây Nam làm gốc 0,0)
            # Hệ số cos(10.77 độ vĩ lõi Q1) ~ 0.9824
            x = (lon - WEST) * 111320 * 0.9824
            y = (lat - SOUTH) * 110540
            nodes[nid] = {"x": round(x, 2), "y": round(y, 2)}
            
        # 2. Thu thập các Way (Đường sá) có tag 'highway'
        roads = []
        intersection_nodes = set()
        
        for way in root.findall('way'):
            is_highway = False
            max_speed = 11.11  # Mặc định vận tốc đô thị ~40km/h (m/s)
            lanes_count = 2    # Mặc định đường có 2 làn
            
            for tag in way.findall('tag'):
                if tag.get('k') == 'highway':
                    is_highway = True
                if tag.get('k') == 'maxspeed':
                    try: max_speed = float(tag.get('v')) / 3.6
                    except: pass
                if tag.get('k') == 'lanes':
                    try: lanes_count = int(tag.get('v'))
                    except: pass
                    
            if is_highway:
                way_id = way.get('id')
                nd_refs = [nd.get('ref') for nd in way.findall('nd')]
                
                # Lấy danh sách tọa độ XY của các node thuộc con đường này
                valid_pts = [nodes[ref] for ref in nd_refs if ref in nodes]
                if len(valid_pts) < 2:
                    continue
                
                start_node = nd_refs[0]
                end_node = nd_refs[-1]
                intersection_nodes.add(start_node)
                intersection_nodes.add(end_node)
                
                # Cấu hình mảng làn đường chuẩn định dạng CityFlow
                lanes = [{"width": 3.5, "maxSpeed": round(max_speed, 2)} for _ in range(lanes_count)]
                
                roads.append({
                    "id": f"road_{way_id}",
                    "points": valid_pts,
                    "lanes": lanes,
                    "startIntersection": f"intersection_{start_node}",
                    "endIntersection": f"intersection_{end_node}"
                })
        
        # 3. Tạo danh sách các nút giao thông (Intersections)
        intersections = []
        for nid in intersection_nodes:
            if nid in nodes:
                # Lọc xem những con đường nào đổ vào hoặc đi ra từ nút giao này
                connected_roads = [
                    r["id"] for r in roads 
                    if r["startIntersection"] == f"intersection_{nid}" or r["endIntersection"] == f"intersection_{nid}"
                ]
                
                intersections.append({
                    "id": f"intersection_{nid}",
                    "point": nodes[nid],
                    "roads": connected_roads,
                    "roadLinks": [],
                    "trafficLight": {"lightPhases": []},
                    "virtual": True  # Virtual=True giúp CityFlow tự điều phối xe không cần cấu hình pha đèn phức tạp
                })
        
        # 4. Đóng gói xuất ra file JSON hoàn chỉnh cho CityFlow
        roadnet_data = {
            "intersections": intersections,
            "roads": roads
        }
        
        with open(ROADNET_FILE, 'w', encoding='utf-8') as f:
            json.dump(roadnet_data, f, indent=4, ensure_ascii=False)
            
        print(f" 🎉 HOÀN TẤT 100%! Đã tạo thành công file cấu hình: {ROADNET_FILE}")
        print(f" -> Thống kê sơ bộ: {len(roads)} đoạn đường | {len(intersections)} nút giao.")
        
    except Exception as e:
        print(f" ❌ Lỗi phân tích cú pháp dữ liệu: {e}")

# =====================================================================
# LUỒNG CHẠY CHÍNH
# =====================================================================
if __name__ == "__main__":
    print("="*50)
    print("BẮT ĐẦU QUY TRÌNH TẠO ROADNET NATIVE CHO CITYFLOW")
    print("="*50)
    
    if download_osm_data():
        convert_osm_to_roadnet_native()