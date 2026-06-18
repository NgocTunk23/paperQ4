# Scenario files

Thư mục này chứa các file JSON dùng để mô tả các khu vực cần giả lập. Mỗi file quyết định vùng bản đồ (`bbox`), các vùng trọng điểm (`regions`), mật độ xe (`flow`) và các đoạn đường bị tắt (`road_closures`).

## Các file có sẵn

- `area_school.json`: khu vực trường học
- `area_hospital.json`: khu vực bệnh viện
- `area_industrial.json`: khu vực công nghiệp
- `area_school_hospital.json`: trường học + bệnh viện
- `area_school_industrial.json`: trường học + khu công nghiệp
- `area_all.json`: trường học + bệnh viện + khu công nghiệp
- `area_industrial_hospital.json`: khu công nghiệp + bệnh viện

## Các trường cần chú ý

- `bbox`: vùng bao lớn nhất của scenario
- `regions`: các khu vực nhỏ bên trong bbox
  - `area_type` chỉ nên là `school`, `hospital` hoặc `industrial`
  - `latitude` / `longitude` dùng để xác định tâm khu vực
  - `radius_km` xác định mức ảnh hưởng của khu vực đó
- `flow.base_interval`: giá trị nhỏ hơn => xe xuất hiện dày hơn
- `flow.route_multiplier`: nhân số lượng tuyến xe
- `road_closures`: danh sách đoạn đường bị đóng tạm thời để thử AI hoặc quy hoạch thay thế

## Cách chạy mô phỏng cho một scenario

### Local

```bash
python build_roadnet.py --scenario scenarios/area_school.json
python simulate.py --scenario scenarios/area_school.json
```

### Docker

```bash
docker compose run --rm traffic-simulator python simulate.py --scenario scenarios/area_school.json
```

## Output sau khi chạy

Các file kết quả sẽ được lưu theo đúng `output_dir` trong scenario. Nếu không có `output_dir`, hệ thống sẽ tự dùng:

```text
outputs/<scenario_id>/
```


## AI và xử lý ùn tắc

Bạn có thể dùng `road_closures` làm đầu vào cho AI để đề xuất tuyến thay thế. Nên ghi kết quả AI vào thư mục:

```text
outputs/<scenario_id>/ai/
```

Ví dụ:
- `ai_recommendations.json`
- `ai_summary.txt`

Nên gọi AI ở một trong 3 vị trí:
1. Trước khi mô phỏng (đề xuất đường tắt / thay đổi lưu lượng)
2. Trong lúc mô phỏng (điều chỉnh theo trạng thái thực tế)
3. Sau khi mô phỏng (phân tích điểm ùn tắc và gợi ý hành động)

