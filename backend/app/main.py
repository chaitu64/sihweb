from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from .copernicus import get_access_token
from .validation_pipeline import process_before_snapshot, process_image
import requests


app = FastAPI(
    title="GeoSR-AI Backend",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://geosr-ai.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "GeoSR-AI Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/test-auth")
def test_auth():
    try:
        token = get_access_token()

        return {
            "success": True,
            "message": "Successfully connected to Copernicus"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def _request_sentinel_product(token: str, bbox: list[float], start_date: str, end_date: str, bands: list[str], max_cloud: int = 50) -> bytes:
    band_list = ", ".join(f'"{band}"' for band in bands)
    values = ", ".join(f"2.5 * sample.{band}" for band in bands)
    payload = {
        "input": {
            "bounds": {"bbox": bbox, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {
                "timeRange": {"from": f"{start_date}T00:00:00Z", "to": f"{end_date}T23:59:59Z"},
                "maxCloudCoverage": max_cloud,
            }}],
        },
        "output": {"width": 512, "height": 512, "responses": [{"identifier": "default", "format": {"type": "image/png"}}]},
        "evalscript": f"""//VERSION=3
function setup() {{ return {{ input: [{band_list}], output: {{ bands: {len(bands)} }} }}; }}
function evaluatePixel(sample) {{ return [{values}]; }}""",
    }
    response = requests.post(
        "https://sh.dataspace.copernicus.eu/api/v1/process",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=35,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = response.text.strip()
        raise RuntimeError(
            f"Copernicus image request failed ({response.status_code}): {body[:500] or 'check the date window and AOI'}"
        ) from exc

    if not response.content or len(response.content) < 200:
        raise RuntimeError("Copernicus returned an empty or invalid image response.")

    return response.content


def fetch_sentinel_tile_robust(token: str, bbox: list[float], start_date: str | None = None, end_date: str | None = None) -> bytes:
    bands = ["B04", "B03", "B02", "B08"]
    
    # Try preferred range first (or default 2023-2024 which has global full coverage in CDSE)
    attempts = []
    if start_date and end_date:
        attempts.append((start_date, end_date, 40))
    attempts.extend([
        ("2023-01-01", "2024-12-31", 40),
        ("2024-01-01", "2026-08-28", 50),
        ("2022-01-01", "2023-12-31", 60),
    ])
    
    last_err = None
    for s_date, e_date, cloud in attempts:
        try:
            content = _request_sentinel_product(token, bbox, s_date, e_date, bands, max_cloud=cloud)
            if content and len(content) > 1000:
                return content
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    raise RuntimeError("No Sentinel-2 imagery available for the selected coordinate and time window.")


@app.get("/sentinel-image")
def get_sentinel_image(
    lat: float,
    lon: float,
    start_date: str | None = None,
    end_date: str | None = None,
    include_before: bool = False
):
    try:
        # Get OAuth access token
        token = get_access_token()

        # Area around clicked location (~1km x 1km AOI)
        buffer = 0.01
        bbox = [
            lon - buffer,
            lat - buffer,
            lon + buffer,
            lat + buffer
        ]

        # Fetch main Sentinel-2 tile
        image_bytes = fetch_sentinel_tile_robust(token, bbox, start_date, end_date)

        # Optional before image for disaster/flood comparison
        before_bytes = None
        if include_before:
            try:
                before_bytes = _request_sentinel_product(token, bbox, "2023-01-01", "2023-03-31", ["B04", "B03", "B02", "B08"], max_cloud=40)
            except Exception:
                before_bytes = None

        result = process_image(image_bytes, before_bytes=before_bytes)
        return {
            "success": True,
            **result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Satellite processing failed: {str(e)}"
        )
