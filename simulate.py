import json
import os
import cityflow

# =====================================================================
# BƯỚC 1: TỰ ĐỘNG SINH LUỒNG PHƯƠNG TIỆN (FLOW.JSON) TỪ BẢN ĐỒ THỰC TẾ
# =====================================================================
print("==== BƯỚC 1: ĐANG TẠO LUỒNG PHƯƠNG TIỆN TOÀN THÀNH PHỐ ====")

if not os.path.exists("roadnet.json"):
    print("❌ Thất bại: Không tìm thấy file roadnet.json! Hãy chạy build_roadnet.py trước.")
    exit()

with open("roadnet.json", "r", encoding="utf-8") as f:
    roadnet = json.load(f)

# TÌM CÁC LỘ TRÌNH HỢP LỆ (GỒM ÍT NHẤT 2 ĐOẠN ĐƯỜNG NỐI VỚI NHAU)
valid_routes = []
for intersection in roadnet.get("intersections", []):
    # Lọc bỏ các ngã tư ảo (để xe không xuất hiện từ giữa không trung)
    if not intersection.get("virtual", False): 
        for road_link in intersection.get("roadLinks", []):
            start_road = road_link.get("startRoad")
            end_road = road_link.get("endRoad")
            # Bắt buộc phải có đường vào và đường ra
            if start_road and end_road:
                valid_routes.append([start_road, end_road])

# Loại bỏ các lộ trình bị trùng lặp
unique_routes = list(set(tuple(r) for r in valid_routes))
valid_routes = [list(r) for r in unique_routes]

print(f" -> Tìm thấy {len(valid_routes)} lộ trình hợp lệ qua ngã tư.")

flows = []
for route in valid_routes:
    flows.append({
        "vehicle": {
            "length": 5.0,
            "width": 2.0,
            "maxSpeed": 11.11,
            "maxPosAcc": 2.0,
            "maxNegAcc": 4.5,
            "usualPosAcc": 2.0,
            "usualNegAcc": 4.5,
            "minGap": 2.5,
            "maxSpeedReplanning": 11.11,
            "earliestStartReplanning": 0.0,
            "headwayTime": 1.5     
        },
        "route": route,      # CHỖ SỬA LỖI: Gắn mảng [đường_A, đường_B]
        "interval": 20.0,    # Cứ 20 giây bơm 1 xe để máy không bị quá tải
        "startTime": 0,
        "endTime": 3600
    })

# Xuất ra file flow.json
with open("flow.json", "w", encoding="utf-8") as f:
    json.dump(flows, f, indent=4)
print(" ✅ Thành công! Đã tự động tạo file luồng xe flow.json.")

# =====================================================================
# BƯỚC 2: KÍCH HOẠT CỖ MÁY MÔ PHỎNG CITYFLOW
# =====================================================================
print("\n==== BƯỚC 2: KHỞI ĐỘNG ENGINE MÔ PHỎNG CITYFLOW ====")

try:
    # Nạp cấu hình vào Engine
    eng = cityflow.Engine("config.json", thread_num=1)
    print(" -> Engine đã sẵn sàng!")
except Exception as e:
    print(f" ❌ Lỗi khởi động CityFlow: {e}")
    exit()

# Tiến hành chạy mô phỏng qua 3600 giây (tương đương 1 tiếng thực tế)
TOTAL_STEPS = 300
print(f" -> Đang chạy giả lập giao thông qua {TOTAL_STEPS} bước tính toán...")

for step in range(TOTAL_STEPS):
    eng.next_step()
    
    # In báo cáo mỗi 100 bước (tầm 100 giây) để dễ theo dõi hơn
    if step % 100 == 0:
        waiting_cars = eng.get_lane_waiting_vehicle_count()
        total_waiting = sum(waiting_cars.values())
        
        # Lấy tổng số xe đang thực sự di chuyển trên bản đồ
        active_vehicles = eng.get_vehicle_count() 
        
        print(f"   [Bước {step}] Tổng xe đang chạy: {active_vehicles} | Số xe kẹt/chờ: {total_waiting} xe.")

print("\n 🎉 GIẢ LẬP HOÀN TẤT THÀNH CÔNG!")
print(" -> File kết quả mô phỏng đã được lưu: replay_log.txt")