import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

function App() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const marker = useRef(null);

  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);

  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,

      // Reliable OpenStreetMap raster style
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: [
              "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            ],
            tileSize: 256,
            attribution:
              "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
          },
        ],
      },

      // Vijayawada initial location
      center: [80.6480, 16.5062],
      zoom: 10,
    });

    map.current.addControl(
      new maplibregl.NavigationControl(),
      "top-right"
    );

    // Map click
    map.current.on("click", (e) => {
      const lat = e.lngLat.lat;
      const lng = e.lngLat.lng;

      console.log("Selected location:", lat, lng);

      setLatitude(lat);
      setLongitude(lng);

      // Remove old marker
      if (marker.current) {
        marker.current.remove();
      }

      // Add new marker
      marker.current = new maplibregl.Marker({
        color: "#65c500",
      })
        .setLngLat([lng, lat])
        .addTo(map.current);

      // Clear previous result
      setImageUrl(null);
      setError("");
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  const fetchSentinelImage = async () => {
    if (latitude === null || longitude === null) {
      setError("Please select a location on the map first.");
      return;
    }

    setLoading(true);
    setError("");
    setImageUrl(null);

    try {
     const response = await fetch(
  `http://127.0.0.1:8000/sentinel-image?lat=${latitude}&lon=${longitude}`
);

      if (!response.ok) {
        const errorText = await response.text();

        throw new Error(
          errorText || "Failed to fetch Sentinel-2 image"
        );
      }

      // IMPORTANT:
      // Backend returns PNG image, NOT JSON
      const blob = await response.blob();

      console.log("Image blob:", blob);

      const url = URL.createObjectURL(blob);

      setImageUrl(url);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">
        <div>
          <h1>GeoSR-AI</h1>
          <p>Deep Learning Based Satellite Super Resolution</p>
        </div>

        <div className="status">
          Sentinel-2 • Copernicus
        </div>
      </header>

      {/* MAP */}
      <div className="map-wrapper">
        <div
          ref={mapContainer}
          className="map-container"
        />

        <div className="map-label">
          Click anywhere to select an area
        </div>
      </div>

      {/* LOCATION PANEL */}
      <section className="selection-section">

        <h2>Select Location</h2>

        <p className="instruction">
          Select any location on the map to retrieve Sentinel-2 satellite imagery.
        </p>

        {latitude !== null ? (
          <>
            <div className="coordinates">

              <div className="coordinate-card">
                <span>Latitude</span>
                <strong>{latitude.toFixed(6)}</strong>
              </div>

              <div className="coordinate-card">
                <span>Longitude</span>
                <strong>{longitude.toFixed(6)}</strong>
              </div>

            </div>

            <button
              className="fetch-button"
              onClick={fetchSentinelImage}
              disabled={loading}
            >
              {loading
                ? "Fetching Sentinel-2 Image..."
                : "Fetch Sentinel-2 Image"}
            </button>
          </>
        ) : (
          <div className="no-selection">
            Click on the map to select a location.
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

      </section>

      {/* SATELLITE IMAGE */}
      {imageUrl && (
        <section className="result-section">

          <h2>Sentinel-2 Satellite Image</h2>

          <div className="image-container">
            <img
              src={imageUrl}
              alt="Sentinel-2 Satellite"
            />
          </div>

        </section>
      )}

    </div>
  );
}

export default App;