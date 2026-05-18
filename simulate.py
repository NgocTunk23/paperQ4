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

# Lấy danh sách tất cả ID các con đường thực tế vừa quét được
road_ids = [road["id"] for road in roadnet.get("roads", [])]
print(f" -> Tìm thấy {len(road_ids)} đoạn đường hợp lệ.")

flows = []
for road_id in road_ids:
    # Cấu hình: Cứ mỗi 8 giây (interval=8.0) sẽ bơm 1 chiếc xe mới vào con đường này
    flows.append({
        "vehicle": {
            "length": 5.0,     # Chiều dài xe (mét)
            "width": 2.0,      # Chiều rộng xe (mét)
            "maxSpeed": 11.11, # Vận tốc tối đa ~40km/h
            "maxPosAcc": 2.0,
            "maxNegAcc": 4.5,
            "usualPosAcc": 2.0,
            "usualNegAcc": 4.5,
            "minGap": 2.5,
            "maxSpeedReplanning": 11.11,
            "earliestStartReplanning": 0.0,
            # CHỖ SỬA LỖI: Nhấc "headwayTime" vào đúng block "vehicle" theo quy chuẩn CityFlow
            "headwayTime": 1.5     
        },
        "route": [road_id],    # Lộ trình chạy trên con đường này
        "interval": 8.0,       # Tần suất xuất hiện xe (giây)
        "startTime": 0,
        "endTime": 3600        # Sinh xe liên tục trong 1 tiếng
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
TOTAL_STEPS = 3600
print(f" -> Đang chạy giả lập giao thông qua {TOTAL_STEPS} bước tính toán...")

for step in range(TOTAL_STEPS):
    eng.next_step()
    
    # Cứ mỗi 10 phút (600 giây) in báo cáo kẹt xe ra màn hình một lần
    if step % 600 == 0:
        waiting_cars = eng.get_lane_waiting_vehicle_count()
        total_waiting = sum(waiting_cars.values())
        print(f"   [Phút {step // 60:02d}] Tổng số xe đang bị ùn tắc/chờ tại nút giao: {total_waiting} xe.")

print("\n 🎉 GIẢ LẬP HOÀN TẤT THÀNH CÔNG!")
print(" -> File kết quả mô phỏng đã được lưu: replay_log.txt")