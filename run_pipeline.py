import os
import subprocess
import sys
from scenario_config import load_scenario
from build_Z_matrix import build_Z_matrix
from build_A_matrix import build_A_matrix

def main():
    # Mặc định lấy scenario tổng hợp
    scenario_path = "scenarios/area_all.json"
    print("="*60)
    print("🚀 BẮT ĐẦU PIPELINE ZONE-AWARE GNN")
    print("="*60)

    print(f"\n[1] Đọc cấu hình kịch bản: {scenario_path}")
    try:
        scenario = load_scenario(scenario_path)
    except Exception as e:
        print(f"❌ Lỗi nạp kịch bản: {e}")
        sys.exit(1)
    
    taz_nodes = []
    for region in scenario.get("regions", []):
        if region.get("latitude") and region.get("longitude"):
            taz_nodes.append({
                "name": region["name"],
                "lat": region["latitude"],
                "lon": region["longitude"],
                "radius_m": region.get("radius_km", 0.8) * 1000
            })
            
    print(f" -> Đã tìm thấy {len(taz_nodes)} Vùng Phân Tích Giao Thông (TAZs).")
    output_dir = scenario.get("output_dir", "outputs/area_all")

    print("\n[2] Khởi tạo Mạng lưới Đường (Roadnet) & Chuyển đổi CityFlow")
    subprocess.run(["python", "build_roadnet.py", "--scenario", scenario_path], check=True)

    print("\n[3] Trích xuất Ma Trận GNN (A và Z)")
    if taz_nodes:
        build_Z_matrix(taz_nodes, output_dir)
        build_A_matrix(taz_nodes, output_dir)
    else:
        print("⚠️ Cảnh báo: Không có TAZ nào có tọa độ để tạo ma trận!")

    print("\n[4] Khởi chạy Mô Phỏng CityFlow để sinh luồng giao thông động")
    subprocess.run(["python", "simulate.py", "--scenario", scenario_path], check=True)

    print("\n🎉 HOÀN TẤT TOÀN BỘ PIPELINE!")
    print(f"📂 Dữ liệu đầu vào cho Zone-Aware AH-GNN đã sẵn sàng tại: {output_dir}")

if __name__ == "__main__":
    main()