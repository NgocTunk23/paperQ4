# Hướng dẫn nhập liệu, tùy chỉnh địa điểm và chạy mô phỏng giao thông

Dự án `paperQ4` dùng để mô phỏng giao thông theo từng khu vực. Người dùng nhập dữ liệu bằng các file JSON trong thư mục `scenarios/`, hệ thống tải bản đồ từ OpenStreetMap, chuyển bản đồ sang định dạng CityFlow, sinh dòng xe, chạy mô phỏng và xuất file để xem lại trên frontend hoặc dùng cho mô hình Zone-Aware AH-GNN.

## 1. Tổng quan hệ thống

Luồng hoạt động chính:

```text
File scenario JSON
  -> đọc và chuẩn hóa bằng scenario_config.py
  -> tải bản đồ OSM theo bbox bằng build_roadnet.py
  -> chuyển OSM sang SUMO map.net.xml
  -> chuyển SUMO sang CityFlow roadnet.json
  -> sinh flow.json và config.json bằng simulate.py
  -> chạy CityFlow để sinh replay_roadnet.json và replay_log.txt
  -> mở frontend để đọc replay_roadnet.json + replay_log.txt
```

Nếu chạy pipeline đầy đủ bằng `run_pipeline.py`, hệ thống còn tạo thêm:

```text
regions trong scenario
  -> build_Z_matrix.py tạo Z_matrix.npy
  -> build_A_matrix.py tạo A_matrix.npy
```

Hai file `A_matrix.npy` và `Z_matrix.npy` là dữ liệu đầu vào cho phần phân tích vùng/TAZ và mô hình GNN.

## 2. Cấu trúc thư mục

```text
paperQ4/
  scenarios/                 # Nơi nhập và tùy chỉnh các kịch bản mô phỏng
  outputs/                   # Nơi lưu kết quả sau khi chạy
  frontend/                  # Giao diện xem lại replay CityFlow
  build_roadnet.py           # Tải OSM, tạo map.net.xml và roadnet.json
  simulate.py                # Tạo flow/config và chạy CityFlow
  run_pipeline.py            # Chạy đủ pipeline: roadnet, A/Z matrix, simulate
  create_custom_scenario.py  # Công cụ tạo scenario bằng cách nhập từ terminal
  scenario_config.py         # Chuẩn hóa và kiểm tra dữ liệu scenario
  build_A_matrix.py          # Tạo ma trận A từ thời gian di chuyển OSRM
  build_Z_matrix.py          # Tạo ma trận Z từ nhãn khu vực Overpass
  docker-compose.yml         # Chạy mô phỏng và frontend bằng Docker
```

File người dùng cần sửa nhiều nhất là các file trong:

```text
scenarios/*.json
```

## 3. Các file scenario có sẵn

```text
scenarios/area_school.json
scenarios/area_hospital.json
scenarios/area_industrial.json
scenarios/area_school_hospital.json
scenarios/area_school_industrial.json
scenarios/area_industrial_hospital.json
scenarios/area_all.json
```

Mỗi file mô tả một vùng mô phỏng, gồm khung bản đồ, danh sách địa điểm/khu vực quan trọng, mật độ xe, thời gian mô phỏng và cấu hình output.

## 4. Cách tùy chỉnh để bổ sung địa điểm

Có ba cách phổ biến:

1. Sửa trực tiếp một file scenario có sẵn, ví dụ `scenarios/area_all.json`.
2. Sao chép một file scenario mẫu thành file mới, ví dụ `scenarios/my_area.json`.
3. Dùng script nhập liệu nhanh:

```bash
python create_custom_scenario.py
```

Cách khuyến nghị là sao chép file mẫu rồi chỉnh lại, vì bạn kiểm soát được đầy đủ `bbox`, `regions`, `flow` và `output_dir`.

## 5. Quy trình thêm một địa điểm mới vào scenario

Giả sử bạn muốn thêm một bệnh viện mới vào `scenarios/area_all.json`.

### Bước 1: Thêm loại khu vực vào `area_types`

Nếu file chưa có loại `hospital`, thêm vào danh sách:

```json
"area_types": ["school", "hospital", "industrial"]
```

Các loại hợp lệ trong code:

```text
commercial, industrial, school, university, hospital, transportation, residential, park
```

### Bước 2: Thêm một phần tử mới vào `regions`

Ví dụ thêm bệnh viện:

```json
{
  "name": "Bệnh viện mới",
  "area_types": ["hospital"],
  "latitude": 10.765,
  "longitude": 106.682,
  "radius_m": 1000,
  "bbox": {
    "south": 10.755,
    "west": 106.672,
    "north": 10.775,
    "east": 106.692
  },
  "notes": "Khu vực có xe cấp cứu, taxi và xe cá nhân ra vào thường xuyên."
}
```

Nếu một địa điểm có nhiều vai trò, dùng nhiều nhãn:

```json
"area_types": ["hospital", "transportation"]
```

Code vẫn chấp nhận dạng cũ:

```json
"area_type": "hospital"
```

Tuy nhiên nên dùng `area_types` để hỗ trợ nhiều nhãn tốt hơn.

### Bước 3: Mở rộng `bbox` tổng nếu cần

`bbox` ở cấp scenario phải bao trùm tất cả địa điểm trong `regions`. Nếu địa điểm mới nằm ngoài khung cũ, phải chỉnh lại:

```json
"bbox": {
  "south": 10.720,
  "west": 106.650,
  "north": 10.790,
  "east": 106.730
}
```

Quy tắc:

- `south` là vĩ độ nhỏ nhất.
- `north` là vĩ độ lớn nhất.
- `west` là kinh độ nhỏ nhất.
- `east` là kinh độ lớn nhất.
- `south` phải nhỏ hơn `north`.
- `west` phải nhỏ hơn `east`.

Không nên chọn `bbox` quá lớn, vì hệ thống sẽ tải nhiều dữ liệu OSM, tạo file `map.osm`, `map.net.xml` và `roadnet.json` rất nặng.

### Bước 4: Đặt bán kính ảnh hưởng

Nên dùng `radius_m` theo mét:

```json
"radius_m": 1000
```

Một số file mẫu cũ có `radius_km`. Nếu muốn giữ tương thích, có thể ghi cả hai:

```json
"radius_km": 1.0,
"radius_m": 1000
```

`build_Z_matrix.py` đọc `radius_m` để truy vấn Overpass quanh từng vùng TAZ.

### Bước 5: Đổi `output_dir`

Nếu tạo scenario mới, nên đặt output riêng:

```json
"output_dir": "outputs/my_area"
```

Nếu không khai báo, hệ thống tự dùng:

```text
outputs/<id>
```

## 6. Mẫu scenario đầy đủ

```json
{
  "id": "my_area",
  "name": "Khu vực thử nghiệm",
  "description": "Mô phỏng giao thông quanh một khu vực tùy chọn.",
  "area_types": ["school", "hospital"],
  "bbox": {
    "south": 10.720,
    "west": 106.685,
    "north": 10.745,
    "east": 106.710
  },
  "regions": [
    {
      "name": "Trường đại học A",
      "area_types": ["school", "university"],
      "latitude": 10.730,
      "longitude": 106.698,
      "radius_m": 1000,
      "bbox": {
        "south": 10.725,
        "west": 106.690,
        "north": 10.738,
        "east": 106.705
      },
      "notes": "Lưu lượng xe máy và xe buýt cao vào giờ cao điểm."
    },
    {
      "name": "Bệnh viện B",
      "area_types": ["hospital"],
      "latitude": 10.735,
      "longitude": 106.702,
      "radius_m": 800,
      "bbox": {
        "south": 10.728,
        "west": 106.696,
        "north": 10.742,
        "east": 106.708
      },
      "notes": "Có xe cấp cứu và xe cá nhân ra vào thường xuyên."
    }
  ],
  "flow": {
    "base_interval": 8.0,
    "start_time": 0,
    "end_time": 3600,
    "vehicle_length": 5.0,
    "vehicle_width": 2.0,
    "max_speed": 11.11,
    "route_multiplier": 1.0
  },
  "road_closures": [
    {
      "road_id": "example_road_id",
      "reason": "accident",
      "start_time": 300,
      "end_time": 900,
      "severity": "high"
    }
  ],
  "output_dir": "outputs/my_area"
}
```

## 7. Giải thích các trường nhập liệu

| Trường | Nên nhập | Ý nghĩa |
| --- | --- | --- |
| `id` | Có | Mã định danh scenario. Dùng để đặt output mặc định. |
| `name` | Có | Tên hiển thị để dễ nhận biết. |
| `description` | Có | Mô tả ngắn về mục tiêu mô phỏng. |
| `area_types` | Có | Danh sách loại khu vực của toàn scenario. |
| `bbox` | Rất nên có | Khung bản đồ hệ thống sẽ tải từ OSM. |
| `regions` | Có | Danh sách địa điểm/khu vực trọng điểm. |
| `flow` | Có | Cấu hình sinh dòng xe. |
| `road_closures` | Tùy chọn | Dữ liệu mô tả đường bị đóng. Hiện chưa tự chặn route trong mô phỏng. |
| `output_dir` | Nên có | Thư mục lưu kết quả riêng cho scenario. |

## 8. Cách nhập tọa độ địa điểm

Mỗi địa điểm trong `regions` cần:

```json
"latitude": 10.730,
"longitude": 106.698
```

Trong đó:

- `latitude` là vĩ độ.
- `longitude` là kinh độ.
- Có thể lấy tọa độ bằng Google Maps, OpenStreetMap hoặc dữ liệu đo thực tế.
- Khi copy tọa độ từ bản đồ, cần giữ đúng thứ tự: vĩ độ trước, kinh độ sau.

Ví dụ tọa độ dạng:

```text
10.730, 106.698
```

thì nhập:

```json
"latitude": 10.730,
"longitude": 106.698
```

## 9. Cách tùy chỉnh mật độ xe bằng `flow`

Ví dụ:

```json
"flow": {
  "base_interval": 8.0,
  "start_time": 0,
  "end_time": 3600,
  "vehicle_length": 5.0,
  "vehicle_width": 2.0,
  "max_speed": 11.11,
  "route_multiplier": 1.0
}
```

Ý nghĩa:

- `base_interval`: khoảng cách thời gian giữa các xe. Số càng nhỏ thì xe càng dày. Trong `simulate.py`, giá trị này được chặn tối thiểu là `3.0`.
- `start_time`: thời điểm bắt đầu sinh xe, tính bằng giây.
- `end_time`: thời điểm kết thúc sinh xe, tính bằng giây.
- `vehicle_length`: chiều dài xe.
- `vehicle_width`: chiều rộng xe.
- `max_speed`: tốc độ tối đa. Giá trị `11.11` tương đương khoảng 40 km/h.
- `route_multiplier`: trong code hiện tại, trường này nhân vào interval. Nhỏ hơn `1.0` làm xe dày hơn, lớn hơn `1.0` làm xe thưa hơn.

Gợi ý cấu hình:

| Mục tiêu | `base_interval` | `route_multiplier` |
| --- | --- | --- |
| Xe ít | `12.0` đến `20.0` | `1.0` đến `1.5` |
| Xe trung bình | `6.0` đến `10.0` | `1.0` |
| Xe dày, dễ ùn tắc | `3.0` đến `5.0` | `0.5` đến `0.9` |

Lưu ý: `simulate.py` hiện chạy `TOTAL_STEPS = 60`. Nếu muốn replay dài hơn, tăng biến này trong hàm `run_simulation()`.

## 10. Cách nhập đường bị đóng bằng `road_closures`

Ví dụ:

```json
"road_closures": [
  {
    "road_id": "road_001",
    "reason": "accident",
    "start_time": 300,
    "end_time": 900,
    "severity": "high"
  }
]
```

Ý nghĩa:

- `road_id`: ID đường trong CityFlow/SUMO roadnet.
- `reason`: lý do đóng đường, ví dụ `accident`, `construction`, `flood`, `event`.
- `start_time`: thời điểm bắt đầu đóng đường, tính bằng giây.
- `end_time`: thời điểm mở lại, tính bằng giây.
- `severity`: mức độ ảnh hưởng, thường dùng `low`, `medium`, `high`.

Quan trọng: code hiện tại chỉ chuẩn hóa và lưu thông tin `road_closures`. `simulate.py` chưa tự loại các tuyến đi qua `road_id` bị đóng. Trường này phù hợp để làm dữ liệu đầu vào cho AI, báo cáo, hoặc phát triển thêm logic chặn đường sau này.

## 11. Cách tạo scenario mới bằng terminal

Chạy:

```bash
python create_custom_scenario.py
```

Script sẽ hỏi:

- ID scenario.
- Tên scenario.
- Mô tả ngắn.
- Tên file JSON cần lưu.
- Số vùng muốn nhập.
- Tên từng vùng.
- Loại vùng.
- Vĩ độ và kinh độ.
- Bán kính.
- Ghi chú.

Sau khi tạo xong, mở file mới trong `scenarios/` và kiểm tra lại:

- Thêm `bbox` tổng cho scenario nếu file chưa có.
- Thêm `output_dir` riêng.
- Thêm `radius_m` nếu script sinh `radius_km`.
- Kiểm tra dấu phẩy trong JSON khi thêm nhiều phần tử vào `regions`.

## 12. Hệ thống chạy như thế nào

### 12.1 `scenario_config.py`

File này đọc scenario JSON và chuẩn hóa dữ liệu.

Các việc chính:

- Đọc `id`, `name`, `description`.
- Chuẩn hóa `bbox`.
- Chuẩn hóa `regions`.
- Chấp nhận cả `area_type` và `area_types`.
- Lọc loại vùng theo danh sách hợp lệ.
- Gán mặc định cho `flow` nếu thiếu.
- Chuẩn hóa `road_closures`.
- Tự đặt `output_dir = outputs/<id>` nếu không nhập.

### 12.2 `build_roadnet.py`

File này tạo mạng lưới đường.

Các bước:

1. Đọc `bbox` từ scenario.
2. Tải dữ liệu OSM theo `bbox`.
3. Lưu thành `map.osm`.
4. Gọi SUMO `netconvert` để tạo `map.net.xml`.
5. Gọi `converter.py` để chuyển sang `roadnet.json`.

Output chính:

```text
map.osm
map.net.xml
roadnet.json
```

Lưu ý: nếu `map.osm` đã tồn tại và đủ lớn, script có thể bỏ qua bước tải lại bản đồ. Nếu đổi sang một `bbox` khác nhưng vẫn thấy bản đồ cũ, hãy kiểm tra lại các file `map.osm`, `map.net.xml`, `roadnet.json` trước khi chạy lại.

### 12.3 `simulate.py`

File này tạo dữ liệu xe và chạy mô phỏng.

Các bước:

1. Đọc scenario.
2. Đọc `roadnet.json`.
3. Tìm các route hợp lệ từ mạng lưới đường.
4. Tạo `flow.json` dựa trên `flow` trong scenario.
5. Tạo `config.json` cho CityFlow.
6. Sao chép `roadnet.json` vào thư mục output.
7. Nếu đã cài CityFlow, chạy mô phỏng và xuất replay.

Output chính:

```text
outputs/<scenario_id>/flow.json
outputs/<scenario_id>/config.json
outputs/<scenario_id>/roadnet.json
outputs/<scenario_id>/replay_roadnet.json
outputs/<scenario_id>/replay_log.txt
```

Nếu máy chưa cài CityFlow, script vẫn có thể tạo `flow.json` và `config.json`, nhưng không tạo replay thật.

### 12.4 `run_pipeline.py`

File này chạy pipeline đầy đủ cho GNN.

Các bước:

1. Đọc `scenarios/area_all.json`.
2. Lấy danh sách TAZ từ `regions`.
3. Chạy `build_roadnet.py`.
4. Tạo `Z_matrix.npy` bằng `build_Z_matrix.py`.
5. Tạo `A_matrix.npy` bằng `build_A_matrix.py`.
6. Chạy `simulate.py`.

Lưu ý: `run_pipeline.py` hiện đang cố định:

```python
scenario_path = "scenarios/area_all.json"
```

Nếu muốn chạy scenario khác, sửa dòng này thành:

```python
scenario_path = "scenarios/my_area.json"
```

### 12.5 `frontend/`

Frontend không tự chạy mô phỏng. Nó chỉ đọc file replay đã xuất.

Người dùng mở:

```text
frontend/index.html
```

hoặc nếu chạy Docker:

```text
http://localhost:8080/frontend/index.html
```

Sau đó chọn:

```text
Roadnet File -> outputs/<scenario_id>/replay_roadnet.json
Replay File  -> outputs/<scenario_id>/replay_log.txt
Chart File   -> tùy chọn
```

Rồi bấm `Start`.

## 13. Chạy local

### 13.1 Cài thư viện Python

Trên Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Trên Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 13.2 Yêu cầu ngoài Python

Để tạo roadnet và chạy mô phỏng đầy đủ, máy cần:

- SUMO và lệnh `netconvert`.
- `sumolib`/`traci` nếu chạy converter trên local.
- CityFlow nếu muốn chạy mô phỏng thật và tạo replay.
- Kết nối internet để tải OSM, truy vấn Overpass và OSRM.

### 13.3 Tạo roadnet cho một scenario

```bash
python build_roadnet.py --scenario scenarios/area_all.json
```

### 13.4 Chạy mô phỏng

```bash
python simulate.py --scenario scenarios/area_all.json
```

### 13.5 Chạy pipeline đầy đủ

```bash
python run_pipeline.py
```

## 14. Chạy bằng Docker

```bash
docker compose up --build
```

Trong `docker-compose.yml`:

- `traffic-simulator` chạy `python run_pipeline.py`.
- `web-frontend` mở web server tại cổng `8080`.
- Thư mục hiện tại được mount vào `/app`, nên output sinh trong container vẫn nằm lại trên máy host.

Mở frontend:

```text
http://localhost:8080/frontend/index.html
```

Nếu muốn chạy riêng một scenario trong container:

```bash
docker compose run --rm traffic-simulator python simulate.py --scenario scenarios/area_school.json
```

## 15. Hệ thống xuất file gì và file đó được đọc như thế nào

### 15.1 `map.osm`

Được tạo bởi:

```text
build_roadnet.py
```

Nguồn dữ liệu tải từ OpenStreetMap theo `bbox`. Người dùng thường không cần mở file này.

### 15.2 `map.net.xml`

Được tạo bởi:

```text
netconvert
```

Đây là mạng lưới đường theo định dạng SUMO. File này được `converter.py` đọc để tạo `roadnet.json`.

### 15.3 `roadnet.json`

Được tạo bởi:

```text
converter.py
```

File này mô tả đường, làn đường, giao lộ và đèn giao thông theo định dạng CityFlow. `simulate.py` đọc file này để tìm route hợp lệ và sao chép nó vào thư mục output.

Lưu ý: `roadnet.json` không phải file nên chọn trong frontend replay. Frontend replay cần `replay_roadnet.json`.

### 15.4 `outputs/<scenario_id>/flow.json`

Được tạo bởi:

```text
simulate.py
```

File này là danh sách dòng xe. Mỗi phần tử thường có:

```json
{
  "vehicle": {
    "length": 5.0,
    "width": 2.0,
    "maxSpeed": 11.11
  },
  "route": ["road_a", "road_b"],
  "interval": 3.0,
  "startTime": 0,
  "endTime": 3600
}
```

CityFlow đọc file này thông qua `config.json`.

### 15.5 `outputs/<scenario_id>/config.json`

Được tạo bởi:

```text
simulate.py
```

File này chỉ cho CityFlow biết phải đọc roadnet và flow ở đâu:

```json
{
  "dir": "outputs/area_all/",
  "roadnetFile": "roadnet.json",
  "flowFile": "flow.json",
  "saveReplay": true,
  "roadnetLogFile": "replay_roadnet.json",
  "replayLogFile": "replay_log.txt"
}
```

Nếu chạy CityFlow riêng, đây là file cấu hình chính cần truyền vào engine.

### 15.6 `outputs/<scenario_id>/replay_roadnet.json`

Được tạo bởi CityFlow khi `saveReplay = true`.

Frontend đọc file này ở ô:

```text
Roadnet File
```

Nó là bản roadnet dành riêng cho replay, khác với `roadnet.json` gốc.

### 15.7 `outputs/<scenario_id>/replay_log.txt`

Được tạo bởi CityFlow khi `saveReplay = true`.

Frontend đọc file này ở ô:

```text
Replay File
```

File này chứa trạng thái xe và đèn giao thông theo từng bước mô phỏng. Frontend đọc từng dòng để vẽ vị trí xe, màu đèn và tiến trình replay.

### 15.8 `outputs/<scenario_id>/A_matrix.npy`

Được tạo bởi:

```text
build_A_matrix.py
```

File này là ma trận liên kết giữa các vùng TAZ, dựa trên thời gian di chuyển OSRM giữa các cặp tọa độ trong `regions`. File phù hợp để đưa vào mô hình GNN.

### 15.9 `outputs/<scenario_id>/Z_matrix.npy`

Được tạo bởi:

```text
build_Z_matrix.py
```

File này là ma trận nhãn khu vực. Mỗi dòng tương ứng một region/TAZ, mỗi cột tương ứng một loại vùng như `commercial`, `industrial`, `school`, `hospital`, `park`. File phù hợp để đưa vào mô hình GNN.

## 16. Cách kiểm tra output sau khi chạy

Sau khi chạy xong, kiểm tra thư mục:

```text
outputs/<scenario_id>/
```

Một lần chạy đầy đủ nên có:

```text
config.json
flow.json
roadnet.json
replay_roadnet.json
replay_log.txt
A_matrix.npy
Z_matrix.npy
```

Nếu chỉ có `config.json` và `flow.json`, có thể CityFlow chưa chạy thành công hoặc chưa được cài.

Nếu không có `A_matrix.npy` và `Z_matrix.npy`, có thể bạn chỉ chạy `simulate.py`, chưa chạy `run_pipeline.py`.

## 17. Quy trình khuyến nghị khi nhập địa điểm mới

1. Sao chép một file mẫu trong `scenarios/`.
2. Đổi `id`, `name`, `description`.
3. Đặt `output_dir` riêng.
4. Nhập `bbox` tổng bao quanh toàn bộ khu vực.
5. Thêm từng địa điểm vào `regions`.
6. Với mỗi địa điểm, nhập `name`, `area_types`, `latitude`, `longitude`, `radius_m`, `bbox`, `notes`.
7. Cập nhật `area_types` ở cấp scenario.
8. Điều chỉnh `flow` theo mật độ xe mong muốn.
9. Chạy `build_roadnet.py`.
10. Chạy `simulate.py` hoặc `run_pipeline.py`.
11. Mở frontend và chọn `replay_roadnet.json` cùng `replay_log.txt`.

## 18. Lỗi thường gặp

### Không tải được bản đồ

Kiểm tra:

- Máy có internet.
- `bbox` không quá lớn.
- Overpass API không bị quá tải.
- File `map.osm` cũ có đang làm hệ thống bỏ qua bước tải lại hay không.

### Không có `roadnet.json`

Chạy:

```bash
python build_roadnet.py --scenario scenarios/<tên_file>.json
```

### `simulate.py` báo chưa cài CityFlow

Điều này có nghĩa là script chỉ tạo file cấu hình, chưa chạy mô phỏng thật. Cách nhanh nhất để có replay là chạy bằng Docker, vì Dockerfile có cài CityFlow.

### Frontend không hiển thị replay

Kiểm tra đã chọn đúng:

```text
Roadnet File -> replay_roadnet.json
Replay File  -> replay_log.txt
```

Không chọn `roadnet.json` ở ô `Roadnet File` của frontend replay.

### Thêm địa điểm nhưng kết quả không đổi

Kiểm tra:

- Đã mở rộng `bbox` tổng để bao trùm địa điểm mới chưa.
- Đã chạy lại `build_roadnet.py` chưa.
- `map.osm` cũ có làm script bỏ qua bước tải bản đồ mới không.
- Đã chạy đúng file scenario mới chưa.
- `run_pipeline.py` có đang hard-code `scenarios/area_all.json` không.

### Nhập `radius_km` nhưng ma trận Z không đổi

Nên nhập thêm `radius_m`:

```json
"radius_km": 1.5,
"radius_m": 1500
```

`build_Z_matrix.py` ưu tiên đọc `radius_m`.

## 19. Ghi chú phát triển thêm

Hiện tại `road_closures` chưa trực tiếp thay đổi route trong `simulate.py`. Nếu muốn mô phỏng đóng đường thật, cần bổ sung logic trong bước tạo route:

- Đọc danh sách `road_closures`.
- Lấy các `road_id` bị đóng theo thời gian.
- Loại route chứa các `road_id` đó.
- Hoặc tăng chi phí/tạo gợi ý đường thay thế bằng module AI.

Kết quả AI nên lưu vào:

```text
outputs/<scenario_id>/ai/
```

Ví dụ:

```text
ai_recommendations.json
ai_summary.txt
```

## 20. Cách đọc và hiểu các file ma trận `.npy`

Các file `.npy` là file nhị phân của NumPy. Vì vậy bạn không đọc được trực tiếp bằng Notepad, VS Code text editor hoặc trình xem JSON/CSV thông thường. Theo tài liệu NumPy, file `.npy` nên được đọc bằng `numpy.load()` và thường được tạo bằng `numpy.save()`.

Trong dự án này, hai file ma trận chính là:

```text
outputs/<scenario_id>/A_matrix.npy
outputs/<scenario_id>/Z_matrix.npy
```

### 20.1 Ý nghĩa của `A_matrix.npy`

`A_matrix.npy` được tạo bởi:

```text
build_A_matrix.py
```

Đây là ma trận liên kết giữa các vùng TAZ trong `regions`.

Nếu scenario có `N` region, `A_matrix.npy` sẽ có kích thước:

```text
N x N
```

Ý nghĩa:

- Mỗi dòng là một region xuất phát.
- Mỗi cột là một region đích.
- Ô `A[i][j]` biểu diễn mức độ kết nối từ region `i` đến region `j`.
- Trong code hiện tại, giá trị này được tính bằng `1 / travel_time`, với `travel_time` lấy từ OSRM.
- Giá trị càng lớn nghĩa là hai vùng càng gần/dễ di chuyển hơn theo thời gian đường bộ.
- Đường chéo `A[i][i]` thường bằng `0.0`, vì một vùng không cần tự kết nối với chính nó.

Ví dụ nếu có 3 region:

```text
regions[0] = Trường học
regions[1] = Bệnh viện
regions[2] = Khu công nghiệp
```

thì:

```text
A[0][1] = mức kết nối từ Trường học đến Bệnh viện
A[1][2] = mức kết nối từ Bệnh viện đến Khu công nghiệp
A[2][0] = mức kết nối từ Khu công nghiệp đến Trường học
```

Ma trận này phù hợp làm adjacency matrix hoặc weight matrix cho mô hình GNN.

### 20.2 Ý nghĩa của `Z_matrix.npy`

`Z_matrix.npy` được tạo bởi:

```text
build_Z_matrix.py
```

Đây là ma trận đặc trưng khu vực cho các region/TAZ.

Nếu scenario có `N` region và hệ thống đang kiểm tra 8 loại vùng, `Z_matrix.npy` thường có kích thước:

```text
N x 8
```

Thứ tự 8 cột trong code hiện tại là:

```text
0. commercial
1. industrial
2. school
3. university
4. hospital
5. transportation
6. residential
7. park
```

Ý nghĩa:

- Mỗi dòng là một region trong `regions`.
- Mỗi cột là một loại khu vực.
- Giá trị `1` nghĩa là quanh tọa độ region có tìm thấy loại khu vực đó trên Overpass/OSM.
- Giá trị `0` nghĩa là không tìm thấy hoặc truy vấn thất bại.

Ví dụ:

```text
[0, 0, 1, 1, 0, 0, 1, 0]
```

có thể hiểu là region đó có dấu hiệu:

```text
school = 1
university = 1
residential = 1
```

và không thấy các nhãn còn lại.

Ma trận này phù hợp làm feature matrix cho mô hình GNN.

### 20.3 Cài extension trong VS Code để đọc `.npy`

Cách dễ và ổn định nhất là dùng Python/Jupyter trong VS Code, không mở trực tiếp `.npy` như file text.

Nên cài các extension sau trong VS Code:

```text
Python - Microsoft
Jupyter - Microsoft
Data Wrangler - Microsoft
```

Cách cài:

1. Mở VS Code.
2. Vào tab Extensions.
3. Tìm `Python` của Microsoft và cài.
4. Tìm `Jupyter` của Microsoft và cài.
5. Tùy chọn: tìm `Data Wrangler` của Microsoft và cài để xem dữ liệu dạng bảng đẹp hơn.

Ghi chú:

- `Python` giúp chọn interpreter, chạy file `.py`, chạy terminal Python.
- `Jupyter` giúp mở notebook `.ipynb`, chạy từng cell và xem biến bằng Variable Explorer/Data Viewer.
- `Data Wrangler` hữu ích khi bạn chuyển ma trận sang `pandas.DataFrame`; nó không phải cách bắt buộc để mở trực tiếp file `.npy`.

### 20.4 Chuẩn bị môi trường Python trong VS Code

Trong terminal của VS Code, chạy:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install numpy pandas
```

Nếu dùng Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy pandas
```

Sau đó trong VS Code:

1. Nhấn `Ctrl+Shift+P`.
2. Chọn `Python: Select Interpreter`.
3. Chọn interpreter trong `.venv`.

Nếu dùng notebook:

1. Tạo file `read_matrices.ipynb`.
2. Chọn kernel là `.venv`.
3. Chạy các cell đọc ma trận bên dưới.

### 20.5 Đọc nhanh `.npy` bằng Python

Tạo file `read_matrices.py` hoặc chạy trong Jupyter Notebook:

```python
import numpy as np

A = np.load("outputs/area_all/A_matrix.npy")
Z = np.load("outputs/area_all/Z_matrix.npy")

print("A shape:", A.shape)
print("A dtype:", A.dtype)
print(A)

print("Z shape:", Z.shape)
print("Z dtype:", Z.dtype)
print(Z)
```

Chạy:

```bash
python read_matrices.py
```

Nếu muốn xem đẹp hơn trong Jupyter:

```python
import numpy as np
import pandas as pd

A = np.load("outputs/area_all/A_matrix.npy")
Z = np.load("outputs/area_all/Z_matrix.npy")

region_names = [
    "Trường học",
    "Bệnh viện",
    "Khu công nghiệp"
]

zone_labels = [
    "commercial",
    "industrial",
    "school",
    "university",
    "hospital",
    "transportation",
    "residential",
    "park"
]

A_df = pd.DataFrame(A, index=region_names, columns=region_names)
Z_df = pd.DataFrame(Z, index=region_names, columns=zone_labels)

display(A_df)
display(Z_df)
```

Khi chạy cell có `display(A_df)` hoặc `display(Z_df)`, VS Code/Jupyter sẽ hiện bảng. Nếu đã cài Data Wrangler, có thể mở bảng đó trong Data Wrangler để lọc, xem thống kê và xuất dữ liệu.

Lưu ý: danh sách `region_names` phải khớp thứ tự `regions` trong file scenario. Nếu scenario có nhiều hoặc ít hơn 3 region, hãy sửa lại danh sách này cho đúng.

### 20.6 Xuất `.npy` sang `.csv` để dễ mở bằng Excel hoặc VS Code

Nếu muốn đọc bằng Excel, Data Wrangler hoặc extension CSV trong VS Code, hãy chuyển `.npy` sang `.csv`.

Tạo file `export_matrices_to_csv.py`:

```python
import numpy as np
import pandas as pd

scenario_id = "area_all"
output_dir = f"outputs/{scenario_id}"

A = np.load(f"{output_dir}/A_matrix.npy")
Z = np.load(f"{output_dir}/Z_matrix.npy")

region_names = [
    "Trường học",
    "Bệnh viện",
    "Khu công nghiệp"
]

zone_labels = [
    "commercial",
    "industrial",
    "school",
    "university",
    "hospital",
    "transportation",
    "residential",
    "park"
]

A_df = pd.DataFrame(A, index=region_names, columns=region_names)
Z_df = pd.DataFrame(Z, index=region_names, columns=zone_labels)

A_df.to_csv(f"{output_dir}/A_matrix.csv", encoding="utf-8-sig")
Z_df.to_csv(f"{output_dir}/Z_matrix.csv", encoding="utf-8-sig")

print(f"Đã xuất {output_dir}/A_matrix.csv")
print(f"Đã xuất {output_dir}/Z_matrix.csv")
```

Chạy:

```bash
python export_matrices_to_csv.py
```

Sau đó có thể mở:

```text
outputs/<scenario_id>/A_matrix.csv
outputs/<scenario_id>/Z_matrix.csv
```

Trong VS Code, Excel hoặc Data Wrangler.

### 20.7 Tự lấy tên region từ scenario JSON

Nếu không muốn tự gõ `region_names`, có thể đọc trực tiếp từ scenario:

```python
import json
import numpy as np
import pandas as pd

scenario_path = "scenarios/area_all.json"
output_dir = "outputs/area_all"

with open(scenario_path, "r", encoding="utf-8") as f:
    scenario = json.load(f)

region_names = [region["name"] for region in scenario["regions"]]

zone_labels = [
    "commercial",
    "industrial",
    "school",
    "university",
    "hospital",
    "transportation",
    "residential",
    "park"
]

A = np.load(f"{output_dir}/A_matrix.npy")
Z = np.load(f"{output_dir}/Z_matrix.npy")

A_df = pd.DataFrame(A, index=region_names, columns=region_names)
Z_df = pd.DataFrame(Z, index=region_names, columns=zone_labels)

display(A_df)
display(Z_df)
```

Cách này an toàn hơn vì thứ tự dòng/cột của ma trận luôn đi theo thứ tự `regions` trong scenario.

### 20.8 Khi nào cần đọc `.npy`, khi nào đọc `.csv`

Dùng `.npy` khi:

- Đưa dữ liệu vào Python, NumPy, PyTorch, TensorFlow hoặc mô hình GNN.
- Muốn giữ đúng kiểu số và kích thước ma trận.
- Không cần mở bằng Excel.

Dùng `.csv` khi:

- Muốn kiểm tra thủ công bằng mắt.
- Muốn mở bằng Excel.
- Muốn xem bảng bằng Data Wrangler hoặc các extension CSV trong VS Code.
- Muốn gửi dữ liệu cho người không dùng Python.

Khuyến nghị: giữ file `.npy` làm dữ liệu gốc cho mô hình, còn `.csv` chỉ dùng để kiểm tra và trình bày.
