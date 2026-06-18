# Hướng dẫn chạy giả lập giao thông theo scenario

Project này gồm 3 bước chính:
1. Tải dữ liệu bản đồ theo `bbox` của scenario.
2. Chuyển đổi bản đồ sang định dạng CityFlow.
3. Chạy mô phỏng xe và lưu kết quả vào thư mục `outputs/`.

## 1. Các file scenario có sẵn

Các file JSON trong [scenarios](scenarios) dùng để xác định vùng cần giả lập, các khu vực trọng điểm và hành vi ùn tắc.

- [scenarios/area_school.json](scenarios/area_school.json): khu vực trường học
- [scenarios/area_hospital.json](scenarios/area_hospital.json): khu vực bệnh viện
- [scenarios/area_industrial.json](scenarios/area_industrial.json): khu vực công nghiệp
- [scenarios/area_industrial_hospital.json](scenarios/area_industrial_hospital.json): khu công nghiệp + bệnh viện
- [scenarios/area_school_hospital.json](scenarios/area_school_hospital.json): trường học + bệnh viện
- [scenarios/area_school_industrial.json](scenarios/area_school_industrial.json): trường học + khu công nghiệp
- [scenarios/area_all.json](scenarios/area_all.json): trường học + bệnh viện + khu công nghiệp

## 2. Cấu trúc của một scenario

Mỗi scenario nên có các trường sau:

- `id`: mã định danh scenario
- `name`: tên hiển thị
- `description`: mô tả ngắn cho khu vực
- `bbox`: khung vùng lớn nhất
  - `south`, `west`, `north`, `east` theo đúng thứ tự vĩ độ/kinh độ
- `regions`: danh sách khu vực phụ bên trong bbox
  - `name`, `area_type`, `latitude`, `longitude`, `radius_km`
  - `bbox` có thể bỏ qua nếu chỉ cần tâm điểm và bán kính
- `flow`: cấu hình dòng xe
  - `base_interval`: khoảng cách giữa các dòng xe (giá trị nhỏ hơn => xe nhiều hơn)
  - `start_time`, `end_time`: thời gian bắt đầu/kết thúc nhập xe
  - `route_multiplier`: hệ số nhân để tăng/giảm tổng lượng xe
- `road_closures`: danh sách đoạn đường bị đóng tạm
  - mỗi mục gồm `road_id`, `reason`, `start_time`, `end_time`, `severity`
- `output_dir`: nơi lưu file kết quả cho scenario đó

Ví dụ mẫu:

```json
{
  "id": "area_demo",
  "name": "Demo",
  "description": "Mô phỏng vùng thử nghiệm",
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
      "notes": "Điểm nóng vào giờ cao điểm"
    }
  ],
  "flow": {
    "base_interval": 15,
    "start_time": 0,
    "end_time": 1800,
    "route_multiplier": 1.0
  },
  "road_closures": [
    {
      "road_id": "road_001",
      "reason": "sự cố giao thông",
      "start_time": 300,
      "end_time": 900,
      "severity": "high"
    }
  ]
}
```

## 3. Cách tạo/điều chỉnh ùn tắc

Để mô phỏng ùn tắc rõ hơn, có thể dùng một hoặc nhiều cách sau:

- Giảm `flow.base_interval` để tăng mật độ xe.
- Tăng `flow.route_multiplier` để tăng số lượng tuyến xe.
- Thêm các mục vào `road_closures` để mô phỏng đường bị tắt.
- Chọn `regions` có `area_type` là `school`, `hospital` hoặc `industrial` để tăng trọng số vùng đó.
- Điều chỉnh `radius_km` để làm vùng ảnh hưởng lớn hơn hoặc nhỏ hơn.

> Nếu muốn thử AI đề xuất đường thay thế, hãy để `road_closures` là đầu vào cho module AI, sau đó ghi kết quả đề xuất vào thư mục output hoặc JSON riêng.

## 4. Chạy local

### 4.1 Cài đặt môi trường

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Tạo roadnet cho scenario

```bash
python build_roadnet.py --scenario scenarios/area_industrial_hospital.json
```

Script này sẽ:
- tải file OSM theo bbox,
- tạo `map.osm`,
- tạo `map.net.xml`,
- tạo `roadnet.json`.

### 4.3 Chạy mô phỏng

```bash
python simulate.py --scenario scenarios/area_industrial_hospital.json
```

Nếu `cityflow` chưa được cài đặt, script vẫn sẽ tạo các file cấu hình nhưng sẽ không chạy mô phỏng thực tế.

### 4.4 Chạy qua runner (khuyến nghị)

```bash
python runner.py --scenario scenarios/area_industrial_hospital.json
```

Runner sẽ chạy lần lượt:
- `build_roadnet.py`
- `simulate.py`
- `main.py` (nếu cần thu thập dữ liệu giao thông)

## 5. Chạy bằng Docker

### 5.1 Khởi động toàn bộ stack

```bash
docker compose up --build
```

### 5.2 Chạy một scenario cụ thể trong container

Bạn có thể sửa [docker-compose.yml](docker-compose.yml) để đổi command, ví dụ:

```yaml
command: python runner.py --scenario scenarios/area_industrial_hospital.json
```

### 5.3 Lưu ý quan trọng với Docker

- Volume hiện tại là `./:/app`, nên mọi file tạo ra trong container (bao gồm `outputs/`, `roadnet.json`, `map.osm`, `map.net.xml`) sẽ được giữ lại trên máy host.
- Nếu cần chạy scenario khác, chỉ cần đổi `command` hoặc dùng lệnh sau:

```bash
docker compose run --rm traffic-simulator python simulate.py --scenario scenarios/area_school.json
```

## 6. Nơi lưu output để dùng cho frontend

Mỗi lần chạy scenario, project sẽ lưu kết quả theo cấu hình trong `output_dir` của scenario. Nếu scenario không có `output_dir`, hệ thống mặc định dùng `outputs/<scenario_id>`.

Các file quan trọng gồm:

- `outputs/<scenario_id>/scenario.json`: nội dung scenario đã chuẩn hóa
- `outputs/<scenario_id>/closures.json`: danh sách đường bị đóng
- `outputs/<scenario_id>/flow.json`: cấu hình dòng xe dùng cho CityFlow
- `outputs/<scenario_id>/config.json`: cấu hình engine mô phỏng
- `outputs/<scenario_id>/replay_log.txt`: replay log để xem lại kết quả mô phỏng

> Khi bạn chạy xong, hãy dùng các file trong `outputs/<scenario_id>/` để đưa lên frontend hoặc CityFlow replay viewer.

## 7. Cách nhúng AI để giải quyết ùn tắc

Có thể tích hợp AI ở 3 điểm trong quy trình:

### 7.1 Trước khi mô phỏng
- AI đọc scenario và đề xuất `road_closures`, `flow`, hoặc `regions` phù hợp.
- Nơi chạy tốt nhất: thêm một script riêng (ví dụ `ai_control.py`) và gọi nó trước khi chạy [simulate.py](simulate.py).

### 7.2 Trong lúc mô phỏng
- AI theo dõi trạng thái `replay_log.txt` hoặc dữ liệu từ `cityflow` để đề xuất tuyến thay thế hoặc điều chỉnh lưu lượng.
- Nơi chạy tốt nhất: thêm logic vào [simulate.py](simulate.py) trong hàm `run_simulation()` hoặc sau mỗi bước mô phỏng.

### 7.3 Sau khi mô phỏng
- AI phân tích `outputs/<scenario_id>/` để tổng hợp nguyên nhân ùn tắc, điểm kẹt và đề xuất hành động.
- Nơi chạy tốt nhất: script riêng đọc `flow.json`, `config.json`, `replay_log.txt` rồi sinh báo cáo JSON/CSV.

Khuyến nghị triển khai:
- Ghi kết quả AI ra thư mục `outputs/<scenario_id>/ai/`
- Dùng file `ai_recommendations.json` để frontend đọc được
- Nếu cần, có thể dùng [main.py](main.py) để thu thập dữ liệu đường thật trước khi chạy AI

## 8. Tạo scenario mới

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

