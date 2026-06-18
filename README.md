# Hướng dẫn chạy scenario theo tọa độ

Bạn chỉ cần chỉnh các file JSON trong [scenarios](scenarios). Mỗi file có 1 phần `bbox` để xác định vùng cần giả lập, và có thể có thêm `regions` để mô tả từng khu vực riêng.

## 1. Các file scenario có sẵn

- [scenarios/area_school.json](scenarios/area_school.json): trường học
- [scenarios/area_hospital.json](scenarios/area_hospital.json): bệnh viện
- [scenarios/area_industrial.json](scenarios/area_industrial.json): khu công nghiệp
- [scenarios/area_industrial_hospital.json](scenarios/area_industrial_hospital.json): khu công nghiệp + bệnh viện
- [scenarios/area_school_hospital.json](scenarios/area_school_hospital.json): trường học + bệnh viện
- [scenarios/area_school_industrial.json](scenarios/area_school_industrial.json): trường học + khu công nghiệp
- [scenarios/area_all.json](scenarios/area_all.json): trường học + bệnh viện + khu công nghiệp

## 2. Cách nhập tọa độ đúng

Mỗi scenario nên có các trường sau:

- `bbox`: khung vùng lớn nhất của scenario
  - `south`: vĩ độ thấp nhất
  - `west`: kinh độ trái nhất
  - `north`: vĩ độ cao nhất
  - `east`: kinh độ phải nhất
- `regions`: danh sách các khu vực nhỏ bên trong vùng đó
  - `latitude`, `longitude`: tọa độ tâm khu vực
  - `radius_km`: bán kính vùng quanh tâm (km)
  - `bbox`: nếu muốn nhập rõ ranh giới cho từng khu vực
- `road_closures`: danh sách đường bị tắt

> Nên nhập theo đúng thứ tự: `south`, `west`, `north`, `east`.
> `south` và `north` là vĩ độ, `west` và `east` là kinh độ.

Ví dụ mẫu:

```json
{
  "id": "area_demo",
  "name": "Demo",
  "bbox": {
    "south": 10.74,
    "west": 106.68,
    "north": 10.80,
    "east": 106.76
  },
  "regions": [
    {
      "name": "Khu vực A",
      "area_type": "hospital",
      "latitude": 10.77,
      "longitude": 106.71,
      "radius_km": 1.0,
      "bbox": {
        "south": 10.75,
        "west": 106.69,
        "north": 10.79,
        "east": 106.73
      }
    }
  ]
}
```

## 3. Chạy một scenario

```bash
python simulate.py --scenario scenarios/area_industrial_hospital.json
```

Hoặc chạy bằng runner mặc định:

```bash
python runner.py --scenario scenarios/area_industrial_hospital.json
```

## 4. Chạy bằng Docker

```bash
docker compose up --build
```

Nếu muốn đổi scenario trong Docker, hãy sửa [docker-compose.yml](docker-compose.yml) thành lệnh bạn cần, ví dụ:

```yaml
command: python runner.py --scenario scenarios/area_industrial_hospital.json
```

## 5. Nếu bạn muốn tạo scenario mới

Bạn có thể chỉnh trực tiếp file JSON trong [scenarios](scenarios), hoặc chạy:

```bash
python create_custom_scenario.py
```

Script này sẽ hỏi bạn nhập:
- tên scenario,
- loại vùng,
- tọa độ tâm (`latitude`, `longitude`),
- bán kính (`radius_km`),
- thời gian tắt đường nếu cần.

