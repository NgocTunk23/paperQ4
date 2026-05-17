import requests
import pandas as pd
from datetime import datetime
import time
import os # Thêm thư viện os để kiểm tra file tồn tại

# =====================================================================
# CẤU HÌNH HỆ THỐNG
# =====================================================================
API_KEY = "FnzitZNIvWNfFNVWStzoGaOZoQQ29mGh"

# ĐỔI TÊN FILE CỐ ĐỊNH: Chạy bao nhiêu lần cũng lưu vào chung 1 file này
OUTPUT_CSV = "Du_lieu_data_giaothong_quan_1_TongHop.csv"

ROUTES = {
    # === CÁC TUYẾN TEST BAN ĐẦU ===
    "Trung_Tam_Q1_di_Q7": {"start": "10.776889,106.700806", "end": "10.729352,106.717522"},
    "San_Bay_Tân_Sơn_Nhất_di_Q1": {"start": "10.814981,106.663558", "end": "10.776889,106.700806"},
    "Cầu_Sài_Gòn_di_Ngã_Tư_Hàng_Xanh": {"start": "10.796338,106.721464", "end": "10.801124,106.710787"},

    # === CÁC TRỤC ĐẠI LỘ VÀ ĐƯỜNG LỚN (Q1) ===
    "Vo_Van_Kiet_Q1": {"start": "10.770900,106.708800", "end": "10.754800,106.684100"}, 
    "Tran_Hung_Dao_Q1": {"start": "10.771600,106.697500", "end": "10.758900,106.681800"}, 
    "Ton_Duc_Thang_Q1": {"start": "10.767500,106.707500", "end": "10.785800,106.707500"}, 
    "Nguyen_Thi_Minh_Khai_Q1": {"start": "10.791500,106.708200", "end": "10.763500,106.682200"}, 
    "Dien_Bien_Phu_Q1": {"start": "10.791400,106.700100", "end": "10.788500,106.693100"}, 
    "Vo_Thi_Sau_Q1": {"start": "10.788500,106.693100", "end": "10.791400,106.700100"}, 
    "Nam_Ky_Khoi_Nghia_Q1": {"start": "10.793800,106.686500", "end": "10.772500,106.702000"}, 
    "Nguyen_Hue_Q1": {"start": "10.776600,106.701100", "end": "10.772200,106.705600"}, 
    "Le_Loi_Q1": {"start": "10.772200,106.698000", "end": "10.776800,106.703200"}, 
    "Le_Duan_Q1": {"start": "10.786500,106.704500", "end": "10.778800,106.696100"}, 
    "Hai_Ba_Trung_Q1": {"start": "10.776200,106.706700", "end": "10.793800,106.686500"}, 
    "Pasteur_Q1": {"start": "10.769800,106.702500", "end": "10.790500,106.688100"}, 
    "Nguyen_Thai_Hoc_Q1": {"start": "10.762800,106.697800", "end": "10.767500,106.692500"}, 

    # === CÁC TUYẾN ĐƯỜNG VỪA / NỘI BỘ QUAN TRỌNG (Q1) ===
    "Nguyen_Dinh_Chieu_Q1": {"start": "10.787800,106.701100", "end": "10.765000,106.678800"}, 
    "Ly_Tu_Trong_Q1": {"start": "10.780100,106.706200", "end": "10.771500,106.691200"}, 
    "Le_Thanh_Ton_Q1": {"start": "10.782500,106.706000", "end": "10.771800,106.694000"}, 
    "Bui_Thi_Xuan_Q1": {"start": "10.768100,106.686000", "end": "10.772500,106.689000"}, 
    "Nguyen_Trai_Q1": {"start": "10.771500,106.691200", "end": "10.760100,106.682100"}, 
    "Ham_Nghi_Q1": {"start": "10.771500,106.697500", "end": "10.769500,106.705800"}, 
    "Dinh_Tien_Hoang_Q1": {"start": "10.785000,106.701500", "end": "10.795100,106.696800"}, 
    "Mac_Dinh_Chi_Q1": {"start": "10.782500,106.699000", "end": "10.790500,106.695500"}, 
    "Phung_Khac_Khoan_Q1": {"start": "10.783100,106.696100", "end": "10.788500,106.693100"}, 
    "Nguyen_Binh_Khiem_Q1": {"start": "10.786500,106.706500", "end": "10.792500,106.700100"}, 
    "Cong_Quynh_Q1": {"start": "10.767500,106.684500", "end": "10.763100,106.688100"}, 
    "Cach_Mang_Thang_Tam_Q1": {"start": "10.771500,106.691200", "end": "10.780500,106.682100"}, 
    "Dong_Khoi_Q1": {"start": "10.778500,106.698500", "end": "10.773500,106.706500"} 
}

# =====================================================================
# HÀM LẤY TỐI ĐA DỮ LIỆU
# =====================================================================
def fetch_max_traffic_data():
    parsed_rows = []
    
    print(f"[1] Bắt đầu quét dữ liệu chuyên sâu lúc: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
    print("-" * 60)
    
    for route_name, coords in ROUTES.items():
        start_pt = coords["start"]
        end_pt = coords["end"]
        
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_pt}:{end_pt}/json"
        
        params = {
            "key": API_KEY,
            "traffic": "true",
            "computeTravelTimeFor": "all",
            "sectionType": "traffic",             
            "routeRepresentation": "summaryOnly"  
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code == 200 and "routes" in data:
                route_info = data['routes'][0]
                summary = route_info.get('summary', {})
                sections = route_info.get('sections', [])
                
                traffic_jams = [sec for sec in sections if sec.get('sectionType') == 'TRAFFIC']
                num_jams = len(traffic_jams)
                
                print(f" -> Xử lý thành công: {route_name} | {num_jams} điểm kẹt xe | Trễ {summary.get('trafficDelayInSeconds', 0)}s")
                
                parsed_rows.append({
                    "Thoi_Gian_Quet": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tuyen_Duong": route_name,
                    "Chieu_Dai_Tong_Met": summary.get('lengthInMeters', 0),
                    "Chieu_Dai_Doan_Ket_Xe_Met": summary.get('trafficLengthInMeters', 0),
                    "Tgian_Ly_Tuong_Giay": summary.get('noTrafficTravelTimeInSeconds', 0),
                    "Tgian_Lich_Su_Giay": summary.get('historicTrafficTravelTimeInSeconds', 0),
                    "Tgian_Su_Co_Realtime_Giay": summary.get('liveTrafficIncidentsTravelTimeInSeconds', 0),
                    "Tgian_Di_Thuc_Te_Giay": summary.get('travelTimeInSeconds', 0),
                    "Do_Tre_Tong_Giay": summary.get('trafficDelayInSeconds', 0),
                    "So_Diem_Ket_Xe": num_jams,
                    "Thoi_Gian_Xuat_Phat": summary.get('departureTime', ''),
                    "Thoi_Gian_Den_Noi": summary.get('arrivalTime', '')
                })
            else:
                print(f" -> Lỗi khi lấy tuyến {route_name}: {data.get('error', response.status_code)}")
                
        except Exception as e:
            print(f" -> Lỗi kết nối ở tuyến {route_name}: {e}")
            
        time.sleep(1) # Tránh Rate Limit
        
    # XUẤT RA FILE CSV (GHI NỐI TIẾP VÀO CUỐI FILE)
    if parsed_rows:
        print("-" * 60)
        df = pd.DataFrame(parsed_rows)
        
        # Kiểm tra xem file đã tồn tại chưa để quyết định có in dòng tiêu đề (header) không
        file_exists = os.path.isfile(OUTPUT_CSV)
        
        # mode='a' là ghi thêm vào cuối file (append) thay vì ghi đè (overwrite)
        df.to_csv(OUTPUT_CSV, mode='a', index=False, header=not file_exists, encoding="utf-8-sig")
        
        print(f"[2] HOÀN TẤT! Đã ghi thêm {len(df)} dòng vào file: {OUTPUT_CSV}")
    else:
        print("\n[!] Không có dữ liệu nào được thu thập.")

if __name__ == "__main__":
    fetch_max_traffic_data()