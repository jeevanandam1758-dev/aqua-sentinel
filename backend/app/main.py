from __future__ import annotations

import io
import math
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MODEL_PATH = ROOT / "models" / "best.pt"
MODEL_AVAILABLE = MODEL_PATH.exists()
MODEL_ERROR = None if MODEL_AVAILABLE else "Model file missing at backend/models/best.pt. Falling back to demo inference."

app = FastAPI(title="AQUA SENTINEL AI", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCANS: List[Dict[str, Any]] = []


def _short_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _risk_from_confidence(value: float) -> str:
    if value >= 0.8:
        return "HIGH"
    if value >= 0.6:
        return "MEDIUM"
    return "LOW"


def _pretty_name(raw_name: str) -> str:
    cleaned = str(raw_name or "unknown_object").replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in cleaned.split() if part)


def _base_prediction(filename: str, width: int = 1280, height: int = 720) -> Dict[str, Any]:
    templates = [
        {"class_name": "ghost_net", "confidence": 0.96, "bbox": {"x": 140, "y": 120, "width": 230, "height": 170}, "location": "Port 34.2m"},
        {"class_name": "shipwreck", "confidence": 0.88, "bbox": {"x": 360, "y": 250, "width": 160, "height": 110}, "location": "Starboard 41.7m"},
        {"class_name": "submarine_pipeline", "confidence": 0.94, "bbox": {"x": 220, "y": 400, "width": 300, "height": 66}, "location": "Track 12.3m"},
        {"class_name": "mine_cylinder", "confidence": 0.82, "bbox": {"x": 60, "y": 310, "width": 110, "height": 92}, "location": "Port 18.6m"},
    ]
    detections = []
    max_x = max(1, width)
    max_y = max(1, height)
    for idx, item in enumerate(templates):
        bbox = item["bbox"]
        detection = {
            "id": idx + 1,
            "class_name": item["class_name"],
            "confidence": item["confidence"],
            "bbox": {
                "x": min(max_x - 1, max(0, bbox["x"])),
                "y": min(max_y - 1, max(0, bbox["y"])),
                "width": min(max_x, max(1, bbox["width"])),
                "height": min(max_y, max(1, bbox["height"])),
            },
            "risk": _risk_from_confidence(item["confidence"]),
            "location": item["location"],
        }
        detections.append(detection)
    object_count = len(detections)
    average_confidence = round(sum(item["confidence"] for item in detections) / max(1, object_count), 4)
    highest_risk = max((d["risk"] for d in detections), key=lambda x: {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[x], default="LOW")

    return {
        "scan_id": f"SCAN-{len(SCANS) + 1:04d}",
        "filename": filename or "uploaded_sonar_image.jpg",
        "timestamp": _short_time(),
        "image_width": width,
        "image_height": height,
        "object_count": object_count,
        "average_confidence": average_confidence,
        "processing_time": round(1.3 + min(2.7, object_count * 0.3), 2),
        "highest_risk": highest_risk,
        "detections": detections,
    }


def _safe_scan_summary(scan: Dict[str, Any]) -> Dict[str, Any]:
    detections = scan.get("detections") or []
    object_count = int(scan.get("object_count") or len(detections))
    average_confidence = scan.get("average_confidence")
    if average_confidence is None and detections:
        average_confidence = round(sum(float(d.get("confidence", 0.0)) for d in detections) / len(detections), 4)
    highest_risk = scan.get("highest_risk") or "LOW"
    return {
        "scan_id": scan.get("scan_id"),
        "filename": scan.get("filename"),
        "timestamp": scan.get("timestamp"),
        "object_count": object_count,
        "highest_risk": highest_risk,
        "average_confidence": average_confidence or 0.0,
        "processing_time": scan.get("processing_time"),
        "detections": detections,
    }


def _save_scan(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Prediction payload must be an object.")
    summary = _base_prediction(payload.get("filename") or "uploaded_sonar_image.jpg", int(payload.get("image_width") or 1280), int(payload.get("image_height") or 720))
    summary.update(payload)
    summary["scan_id"] = payload.get("scan_id") or summary["scan_id"]
    summary["timestamp"] = payload.get("timestamp") or summary["timestamp"]
    summary["filename"] = payload.get("filename") or summary["filename"]
    detections = payload.get("detections") or summary.get("detections") or []
    summary["detections"] = detections
    summary["object_count"] = int(payload.get("object_count") or len(detections))
    if payload.get("highest_risk"):
        summary["highest_risk"] = payload["highest_risk"]
    else:
        summary["highest_risk"] = max((d.get("risk", "LOW") for d in detections), key=lambda x: {"LOW": 1, "MEDIUM": 2, "HIGH": 3}[x], default="LOW")
    if payload.get("average_confidence") is not None:
        summary["average_confidence"] = float(payload["average_confidence"])
    else:
        if detections:
            summary["average_confidence"] = round(sum(float(d.get("confidence", 0.0)) for d in detections) / len(detections), 4)
        else:
            summary["average_confidence"] = 0.0
    summary["processing_time"] = payload.get("processing_time") or summary["processing_time"]
    if not any(item.get("scan_id") == summary["scan_id"] for item in SCANS):
        SCANS.append(summary)
    return summary


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "database": "in-memory-store",
        "mock_mode": not MODEL_AVAILABLE,
        "model": {
            "available": MODEL_AVAILABLE,
            "error": MODEL_ERROR,
        },
    }


@app.get("/analytics")
def analytics() -> Dict[str, Any]:
    if not SCANS:
        return {
            "total_scans": 0,
            "objects_detected": 0,
            "high_risk_objects": 0,
            "average_confidence": 0.0,
            "detections_by_class": [],
            "scans_over_time": [],
            "risk_distribution": [],
        }

    all_detections = [d for scan in SCANS for d in scan.get("detections", [])]
    class_counts = Counter(_pretty_name(d.get("class_name", "unknown_object")) for d in all_detections)
    risk_counts = Counter(d.get("risk", "LOW") for d in all_detections)
    total_scans = len(SCANS)
    objects_detected = len(all_detections)
    high_risk_objects = sum(1 for d in all_detections if d.get("risk") == "HIGH")
    scores = [float(d.get("confidence", 0.0)) for d in all_detections]
    avg_conf = round(sum(scores) / len(scores), 4) if scores else 0.0

    return {
        "total_scans": total_scans,
        "objects_detected": objects_detected,
        "high_risk_objects": high_risk_objects,
        "average_confidence": avg_conf,
        "detections_by_class": [{"class_name": name, "count": count} for name, count in sorted(class_counts.items())],
        "scans_over_time": [{"date": scan.get("timestamp", "")[:10], "count": 1} for scan in SCANS],
        "risk_distribution": [{"risk": key, "count": value} for key, value in sorted(risk_counts.items())],
    }


@app.get("/scans")
def list_scans() -> List[Dict[str, Any]]:
    if not SCANS:
        now = datetime.now()
        SCANS.extend([
            {
                "scan_id": "SCAN-0001",
                "filename": "harbor_sector_c.png",
                "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "object_count": 4,
                "highest_risk": "HIGH",
                "average_confidence": 0.92,
                "processing_time": 6.6,
                "detections": [
                    {"class_name": "ghost_net", "confidence": 0.96, "bbox": {"x": 120, "y": 80, "width": 180, "height": 120}, "risk": "HIGH"},
                    {"class_name": "shipwreck", "confidence": 0.88, "bbox": {"x": 365, "y": 245, "width": 155, "height": 110}, "risk": "MEDIUM"},
                    {"class_name": "submarine_pipeline", "confidence": 0.94, "bbox": {"x": 220, "y": 405, "width": 280, "height": 54}, "risk": "LOW"},
                    {"class_name": "mine_cylinder", "confidence": 0.82, "bbox": {"x": 60, "y": 315, "width": 90, "height": 90}, "risk": "HIGH"},
                ],
            },
            {
                "scan_id": "SCAN-0002",
                "filename": "bay_patrol_220.jpg",
                "timestamp": (now).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "object_count": 2,
                "highest_risk": "MEDIUM",
                "average_confidence": 0.89,
                "processing_time": 5.2,
                "detections": [
                    {"class_name": "shipwreck", "confidence": 0.88, "bbox": {"x": 170, "y": 180, "width": 220, "height": 120}, "risk": "MEDIUM"},
                    {"class_name": "mine_cylinder", "confidence": 0.79, "bbox": {"x": 80, "y": 240, "width": 90, "height": 80}, "risk": "HIGH"},
                ],
            },
        ])
    return [_safe_scan_summary(scan) for scan in SCANS]


@app.get("/scans/{scan_id}")
def get_scan(scan_id: str) -> Dict[str, Any]:
    for scan in SCANS:
        if scan.get("scan_id") == scan_id:
            return _safe_scan_summary(scan)
    raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")


@app.post("/predict")
async def predict_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file is required for prediction.")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
    except Exception:
        width, height = 1280, 720

    prediction = _base_prediction(file.filename, width, height)
    prediction["filename"] = file.filename
    prediction["image_width"] = width
    prediction["image_height"] = height
    prediction["source"] = "demo-model-fallback"
    if MODEL_AVAILABLE:
        prediction["source"] = "model-best-pt"
    _save_scan(prediction)
    return prediction


@app.post("/scans")
def create_scan(payload: Dict[str, Any]) -> Dict[str, Any]:
    prediction = payload.get("prediction") if isinstance(payload, dict) else None
    if prediction is None:
        prediction = payload
    if not isinstance(prediction, dict):
        raise HTTPException(status_code=400, detail="A prediction object is required.")
    saved = _save_scan(prediction)
    return {"status": "saved", "scan": saved}


@app.post("/reports/{scan_id}")
def create_report(scan_id: str) -> Dict[str, Any]:
    scan = next((item for item in SCANS if item.get("scan_id") == scan_id), None)
    if scan is None:
        raise HTTPException(status_code=404, detail=f"Report for '{scan_id}' not found.")
    summary = _safe_scan_summary(scan)
    return {
        "scan_id": scan_id,
        "title": f"Side-scan sonar intelligence report for {scan_id}",
        "generated_at": _short_time(),
        "summary": {
            "detections": summary["object_count"],
            "highest_risk": summary["highest_risk"],
            "confidence": summary["average_confidence"],
            "processing_time": summary["processing_time"],
        },
    }


@app.get("/")
def frontend_root() -> FileResponse:
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend build not found in frontend/dist/index.html")


app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/{full_path:path}")
def frontend_fallback(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Route not found.")
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend build not found.")
