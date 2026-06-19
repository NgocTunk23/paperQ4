import requests
import json
import numpy as np
import os

ZONE_QUERIES = {
    "commercial": 'way["landuse"="commercial"]',
    "industrial": 'way["landuse"="industrial"]',
    "school": 'way["amenity"="school"]',
    "university": 'way["amenity"="university"]',
    "hospital": 'way["amenity"="hospital"]',
    "transportation": '(way["aeroway"]; way["landuse"="transportation"];)',
    "residential": 'way["landuse"="residential"]',
    "park": 'way["leisure"="park"]'
}

def query_overpass_for_node(lat, lon, radius=800):
    z_vector = []
    for zone, query in ZONE_QUERIES.items():
        overpass_query = f"""
        [out:json][timeout:25];
        {query}(around:{radius},{lat},{lon});
        out count;
        """
        try:
            response = requests.get("https://overpass-api.de/api/interpreter", data={'data': overpass_query}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                count = int(data['elements'][0]['tags']['ways']) if data['elements'] else 0
                z_vector.append(1 if count > 0 else 0)
            else:
                print(f"Lỗi truy vấn {zone} tại ({lat}, {lon}): Status {response.status_code}")
                z_vector.append(0)
        except Exception as e:
            print(f"Lỗi kết nối khi truy vấn {zone}: {e}")
            z_vector.append(0)
            
    return z_vector

def build_Z_matrix(taz_nodes, output_dir):
    Z = []
    print("\n[Z-Matrix] Bắt đầu trích xuất nhãn vùng đa nhân...")
    for idx, node in enumerate(taz_nodes):
        print(f" -> Đang quét TAZ {idx+1}/{len(taz_nodes)}: {node['name']} ({node['lat']}, {node['lon']})")
        z_vec = query_overpass_for_node(node['lat'], node['lon'], node.get('radius_m', 800))
        Z.append(z_vec)
    
    Z_matrix = np.array(Z)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "Z_matrix.npy")
    np.save(out_path, Z_matrix)
    print(f"✅ Đã lưu Ma trận Z (Shape: {Z_matrix.shape}) tại {out_path}")
    return Z_matrix