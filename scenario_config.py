from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

# Đã cập nhật 8 loại vùng theo bài nghiên cứu
VALID_AREA_TYPES = (
    "commercial", "industrial", "school", "university",
    "hospital", "transportation", "residential", "park"
)
DEFAULT_SCENARIO_DIR = Path("scenarios")
DEFAULT_SCENARIO = DEFAULT_SCENARIO_DIR / "area_all.json"


def load_scenario(path: str | Path) -> Dict[str, Any]:
    """Load and validate a scenario configuration file."""
    scenario_path = Path(path)
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    with scenario_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    normalized = normalize_scenario(data, scenario_path)
    return normalized


def _normalize_bbox(raw_bbox: Any) -> Dict[str, float] | None:
    if not isinstance(raw_bbox, dict):
        return None
    try:
        return {
            "south": float(raw_bbox.get("south", raw_bbox.get("SOUTH", 0.0))),
            "west": float(raw_bbox.get("west", raw_bbox.get("WEST", 0.0))),
            "north": float(raw_bbox.get("north", raw_bbox.get("NORTH", 0.0))),
            "east": float(raw_bbox.get("east", raw_bbox.get("EAST", 0.0))),
        }
    except (TypeError, ValueError):
        return None


def _normalize_regions(data: Dict[str, Any]) -> list[Dict[str, Any]]:
    raw_regions = data.get("regions") or []
    if isinstance(raw_regions, dict):
        raw_regions = [raw_regions]

    normalized_regions = []
    for item in raw_regions:
        if not isinstance(item, dict):
            continue

        # Lấy danh sách các loại vùng (hỗ trợ Đa Nhãn)
        area_types_raw = item.get("area_types") or item.get("area_type") or item.get("type") or []
        if isinstance(area_types_raw, str):
            area_types_raw = [area_types_raw]
            
        # Lọc ra các vùng hợp lệ
        valid_areas = [a for a in area_types_raw if a in VALID_AREA_TYPES]
        if not valid_areas:
            valid_areas = ["industrial"] # Default fallback

        lat = item.get("latitude") if item.get("latitude") is not None else item.get("lat")
        lon = item.get("longitude") if item.get("longitude") is not None else item.get("lon")

        normalized_regions.append(
            {
                "name": item.get("name") or item.get("region_name") or "region",
                "area_types": valid_areas, # Đổi thành list để lưu đa nhãn
                "latitude": float(lat) if lat is not None else None,
                "longitude": float(lon) if lon is not None else None,
                "bbox": _normalize_bbox(item.get("bbox") or item.get("area_bbox")),
                "radius_m": float(item.get("radius_m", item.get("radius", 800.0))),
                "notes": item.get("notes", ""),
            }
        )

    return normalized_regions


def normalize_scenario(data: Dict[str, Any], scenario_path: Path) -> Dict[str, Any]:
    """Ensure a scenario has all defaults needed by the simulator."""
    scenario_id = data.get("id") or scenario_path.stem
    area_types = data.get("area_types") or []
    if isinstance(area_types, str):
        area_types = [area_types]

    normalized_regions = _normalize_regions(data)

    if normalized_regions:
        # Gộp tất cả area_types từ các regions
        region_area_types = []
        for region in normalized_regions:
            region_area_types.extend(region["area_types"])
        area_types = list(dict.fromkeys(area_types + region_area_types))

    normalized = {
        "id": scenario_id,
        "name": data.get("name") or scenario_id,
        "description": data.get("description") or "",
        "area_types": [a for a in area_types if a in VALID_AREA_TYPES],
        "bbox": _normalize_bbox(data.get("bbox") or data.get("area_bbox")),
        "regions": normalized_regions,
        "flow": {
            "base_interval": float(data.get("flow", {}).get("base_interval", 20.0)),
            "start_time": int(data.get("flow", {}).get("start_time", 0)),
            "end_time": int(data.get("flow", {}).get("end_time", 3600)),
            "vehicle_length": float(data.get("flow", {}).get("vehicle_length", 5.0)),
            "vehicle_width": float(data.get("flow", {}).get("vehicle_width", 2.0)),
            "max_speed": float(data.get("flow", {}).get("max_speed", 11.11)),
            "route_multiplier": float(data.get("flow", {}).get("route_multiplier", 1.0)),
        },
        "road_closures": data.get("road_closures") or [],
        "output_dir": data.get("output_dir") or f"outputs/{scenario_id}",
        "metadata": {
            "created_from": str(scenario_path),
        },
    }

    closures = []
    for item in normalized["road_closures"]:
        if not isinstance(item, dict):
            continue
        closures.append(
            {
                "road_id": item.get("road_id", ""),
                "reason": item.get("reason", "unknown"),
                "start_time": int(item.get("start_time", 0)),
                "end_time": int(item.get("end_time", 0)),
                "severity": item.get("severity", "medium"),
            }
        )
    normalized["road_closures"] = closures

    return normalized


def iter_scenarios(directory: str | Path = DEFAULT_SCENARIO_DIR) -> Iterable[Path]:
    base = Path(directory)
    if not base.exists():
        return []
    return sorted(base.glob("*.json"))