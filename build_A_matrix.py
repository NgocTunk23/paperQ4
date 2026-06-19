import requests
import numpy as np
import os
import time

def get_osrm_travel_time(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 'Ok':
                return data['routes'][0]['duration']
    except Exception as e:
        print(f"Lỗi lấy OSRM từ ({lat1},{lon1}) đến ({lat2},{lon2}): {e}")
    return float('inf')

def build_A_matrix(taz_nodes, output_dir):
    N = len(taz_nodes)
    A = np.zeros((N, N))
    print(f"\n[A-Matrix] Bắt đầu tính toán ma trận kề OSRM cho {N} TAZs...")
    
    for i in range(N):
        for j in range(N):
            if i == j:
                A[i][j] = 0.0
            else:
                d_ij = get_osrm_travel_time(
                    taz_nodes[i]['lat'], taz_nodes[i]['lon'],
                    taz_nodes[j]['lat'], taz_nodes[j]['lon']
                )
                A[i][j] = 1.0 / d_ij if (d_ij > 0 and d_ij != float('inf')) else 0.0
                time.sleep(0.1) # Tránh rate limit của public OSRM API
                
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "A_matrix.npy")
    np.save(out_path, A)
    print(f"✅ Đã lưu Ma trận A (Shape: {A.shape}) tại {out_path}")
    return A