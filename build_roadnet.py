import requests
import json
import os
import sys
import xml.etree.ElementTree as ET

# =====================================================================
# CẤU HÌNH KHUNG TỌA ĐỘ BẢN ĐỒ (Toàn bộ TP.HCM)
# =====================================================================
# SOUTH = 10.35
# WEST = 106.35
# NORTH = 11.16
# EAST = 107.02
# =====================================================================
# CẤU HÌNH KHUNG TỌA ĐỘ QUẬN 1
# ====================================================================
SOUTH = 10.768
WEST = 106.693
NORTH = 10.782
EAST = 106.710

OSM_FILE = "map.osm"
ROADNET_FILE = "roadnet.json"

def download_osm_data():
    if os.path.exists(OSM_FILE) and os.path.getsize(OSM_FILE) > 1000:
        print(f"[1] Tìm thấy file {OSM_FILE} có sẵn. Bỏ qua bước tải mạng.")
        return True

    print(f"[1] Bắt đầu tiến trình tải bản đồ TOÀN THÀNH PHỐ HỒ CHÍ MINH...")
    API_SERVERS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter"
    ]
    
    query = f"[out:xml][timeout:600];(way[\"highway\"]({SOUTH},{WEST},{NORTH},{EAST}););out body;>;out skel qt;"
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "text/plain"}
    
    for url in API_SERVERS:
        print(f" -> Đang thử kết nối tới: {url} (Vùng lớn toàn thành phố có thể mất 1 - 3 phút để xử lý)...")
        try:
            response = requests.post(url, data=query.encode('utf-8'), headers=headers, timeout=300)
            if response.status_code == 200:
                with open(OSM_FILE, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f" ✅ THÀNH CÔNG! Đã tải xong dữ liệu bản đồ thô toàn TP.HCM.")
                return True
            else:
                print(f" ❌ Server phản hồi mã lỗi: {response.status_code}")
        except Exception as net_error:
            print(f" ⚠️ Lỗi kết nối đến server này: {net_error}")
            
    return False

def convert_osm_to_roadnet_native():
    print(f"[2] Đang bóc tách hình học và chuyển đổi {OSM_FILE} sang {ROADNET_FILE}...")
    if not os.path.exists(OSM_FILE):
        print(f" ❌ Thất bại: Không tìm thấy file {OSM_FILE} để chuyển đổi!")
        sys.exit(1)
    
    try:
        tree = ET.parse(OSM_FILE)
        root = tree.getroot()
        
        # 1. Thu thập tất cả các Node và quy đổi sang hệ Mét (X, Y) phẳng lấy gốc cực Tây Nam TP.HCM
        nodes = {}
        for node in root.findall('node'):
            nid = node.get('id')
            lat = float(node.get('lat'))
            lon = float(node.get('lon'))
            
            x = (lon - WEST) * 111320 * 0.9824
            y = (lat - SOUTH) * 110540
            nodes[nid] = {"x": round(x, 2), "y": round(y, 2)}
            
        # 2. Thu thập các Way (Đường sá) có tag 'highway'
        roads = []
        intersection_nodes = set()
        
        for way in root.findall('way'):
            is_highway = False
            max_speed = 11.11  # Mặc định ~40km/h
            lanes_count = 2    
            
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
                
                # SỬA LỖI QUAN TRỌNG: Chỉ lấy các node thực sự nằm trong phạm vi tọa độ đã lọc thành công
                valid_nd_refs = [ref for ref in nd_refs if ref in nodes]
                if len(valid_nd_refs) < 2:
                    continue
                
                valid_pts = [nodes[ref] for ref in valid_nd_refs]
                
                # Trích xuất điểm đầu/cuối từ tập hợp node hợp lệ để không bị lệch biên bản đồ
                start_node = valid_nd_refs[0]
                end_node = valid_nd_refs[-1]
                
                # Loại bỏ lỗi vòng lặp khép kín trùng đầu đuôi khiến CityFlow crash
                if start_node == end_node:
                    continue
                    
                intersection_nodes.add(start_node)
                intersection_nodes.add(end_node)
                
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
                    "virtual": True  
                })
        
        # 4. Đóng gói xuất ra file JSON cho CityFlow
        roadnet_data = {
            "intersections": intersections,
            "roads": roads
        }
        
        with open(ROADNET_FILE, 'w', encoding='utf-8') as f:
            json.dump(roadnet_data, f, indent=4, ensure_ascii=False)
            
        print(f" 🎉 HOÀN TẤT 100%! Đã tạo thành công file cấu hình toàn TP.HCM: {ROADNET_FILE}")
        print(f" -> Quy mô mô phỏng: {len(roads)} đoạn đường | {len(intersections)} nút giao.")
        
    except Exception as e:
        print(f" ❌ Lỗi bóc tách cú pháp hình học: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("="*60)
    print("BẮT ĐẦU QUY TRÌNH TẠO ROADNET NATIVE TOÀN TP.HCM")
    print("="*60)
    
    if download_osm_data():
        convert_osm_to_roadnet_native()
    else:
        print("💥 THẤT BẠI: Tất cả các máy chủ Overpass đều không thể kết nối hoặc quá tải!")
        sys.exit(1)