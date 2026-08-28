from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

from app.copernicus import get_access_token
from app.validation_pipeline import process_image
import requests


app = FastAPI(
    title="GeoSR-AI Backend",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
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


@app.get("/sentinel-image")
def get_sentinel_image(lat: float, lon: float):

    try:
        # Get OAuth access token
        token = get_access_token()

        # Area around clicked location
        buffer = 0.01

        bbox = [
            lon - buffer,
            lat - buffer,
            lon + buffer,
            lat + buffer
        ]

        evalscript = """
        //VERSION=3

        function setup() {
            return {
                input: ["B04", "B03", "B02", "B08"],
                output: {
                    bands: 4
                }
            };
        }

        function evaluatePixel(sample) {
            return [
                2.5 * sample.B04,
                2.5 * sample.B03,
                2.5 * sample.B02,
                2.5 * sample.B08
            ];
        }
        """

        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": "2026-01-01T00:00:00Z",
                                "to": "2026-08-27T23:59:59Z"
                            },
                            "maxCloudCoverage": 30
                        }
                    }
                ]
            },

            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ]
            },

            "evalscript": evalscript
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        PROCESS_URL = (
            "https://sh.dataspace.copernicus.eu/"
            "api/v1/process"
        )

        response = requests.post(
            PROCESS_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        result = process_image(response.content)
        return {
            "success": True,
            **result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )