import requests
import json
import numpy as np
import os
import time

ZONE_QUERIES = {
    "commercial": 'nwr["landuse"="commercial"](around:{radius},{lat},{lon});',
    "industrial": 'nwr["landuse"="industrial"](around:{radius},{lat},{lon});',
    "school": 'nwr["amenity"="school"](around:{radius},{lat},{lon});',
    "university": 'nwr["amenity"="university"](around:{radius},{lat},{lon});',
    "hospital": 'nwr["amenity"="hospital"](around:{radius},{lat},{lon});',
    "transportation": '(nwr["aeroway"](around:{radius},{lat},{lon}); nwr["landuse"="transportation"](around:{radius},{lat},{lon}); nwr["railway"](around:{radius},{lat},{lon}););',
    "residential": 'nwr["landuse"="residential"](around:{radius},{lat},{lon});',
    "park": 'nwr["leisure"="park"](around:{radius},{lat},{lon});'
}

# Danh sách các cụm máy chủ Overpass dự phòng
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter"
]

def query_overpass_for_node(lat, lon, radius=800):
    z_vector = []
    headers = {'User-Agent': 'ZoneAwareGNN-TrafficBot/2.0'}
    
    for zone, query_template in ZONE_QUERIES.items():
        query_str = query_template.format(radius=radius, lat=lat, lon=lon)
        
        # Tăng timeout của câu lệnh QL lên 50s
        overpass_query = f"""
        [out:json][timeout:50];
        {query_str}
        out count;
        """
        
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            # Luân phiên đổi server nếu gặp lỗi
            endpoint = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
            
            try:
                # Tăng timeout của kết nối Python lên 60s
                response = requests.post(
                    endpoint, 
                    data=overpass_query, 
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('elements'):
                        tags = data['elements'][0]['tags']
                        total_count = int(tags.get('nodes', 0)) + int(tags.get('ways', 0)) + int(tags.get('relations', 0))
                        z_vector.append(1 if total_count > 0 else 0)
                    else:
                        z_vector.append(0)
                    success = True
                    break 
                
                elif response.status_code == 429:
                    print(f"     [!] Server {endpoint} quá tải (429). Đang chờ 10s...")
                    time.sleep(10)
                elif response.status_code == 504:
                    print(f"     [!] Server {endpoint} bị Timeout 504. Sẽ đổi server ở lần thử tiếp theo...")
                    time.sleep(2)
                else:
                    print(f"     [!] Lỗi truy vấn {zone} (Status {response.status_code}) từ {endpoint}.")
                    time.sleep(3)
                    
            except requests.exceptions.Timeout:
                print(f"     [!] Mất kết nối (Timeout Python) tới {endpoint}. Đang thử lại...")
                time.sleep(3)
            except Exception as e:
                print(f"     [!] Lỗi mạng khi truy vấn {zone}: {e}")
                time.sleep(3)
                
        if not success:
            print(f"     [!] Bỏ qua nhãn '{zone}' sau {max_retries} lần thử thất bại để tiếp tục tiến trình.")
            z_vector.append(0)
            
        time.sleep(2) # Nghỉ ngơi giữa các nhãn
            
    return z_vector

def build_Z_matrix(taz_nodes, output_dir):
    Z = []
    print("\n[Z-Matrix] Bắt đầu trích xuất nhãn vùng đa nhân...")
    
    for idx, node in enumerate(taz_nodes):
        print(f" -> Đang quét TAZ {idx+1}/{len(taz_nodes)}: {node['name']} ({node['lat']}, {node['lon']})")
        z_vec = query_overpass_for_node(node['lat'], node['lon'], node.get('radius_m', 800))
        Z.append(z_vec)
        
        if idx < len(taz_nodes) - 1:
            time.sleep(5)
    
    Z_matrix = np.array(Z)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "Z_matrix.npy")
    np.save(out_path, Z_matrix)
    print(f"✅ Đã lưu Ma trận Z (Shape: {Z_matrix.shape}) tại {out_path}")
    return Z_matrix