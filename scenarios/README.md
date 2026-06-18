# Scenario files

Các file JSON trong thư mục này dùng để mô phỏng các kịch bản khu vực khác nhau.

- `area_school.json`: chỉ chứa khu vực trường học
- `area_hospital.json`: chỉ chứa khu vực bệnh viện
- `area_industrial.json`: chỉ chứa khu vực khu công nghiệp
- `area_school_hospital.json`: trường học + bệnh viện
- `area_school_industrial.json`: trường học + khu công nghiệp
- `area_all.json`: trường học + bệnh viện + khu công nghiệp

Mỗi file có thể chỉnh sửa:
- `area_types`: danh sách các loại khu vực để đánh dấu mức độ ưu tiên luồng xe
- `flow.base_interval`: khoảng cách giữa các dòng xe
- `road_closures`: danh sách các đoạn đường bị tắt để thử AI tìm đường thay thế

Chạy mô phỏng theo kịch bản:

```bash
python simulate.py --scenario scenarios/area_school.json
```
