import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";
import About from "./pages/About";
import Documentation from "./pages/Documentation";
import Research from "./pages/Research";

function App() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const marker = useRef(null);

  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);

  const [outputs, setOutputs] = useState(null);
  const [selectedOutput, setSelectedOutput] = useState("lr_input");
  const [metrics, setMetrics] = useState(null);
  const [resultDetails, setResultDetails] = useState(null);
  const [validationReference, setValidationReference] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState("home");

  const pageComponents = {
    research: Research,
    documentation: Documentation,
    about: About,
  };

  const outputDefinitions = outputs ? [
    ["lr_input", outputs.lr_input, "Low-resolution input", "LR Input"],
    ["sr_output", outputs.sr_output, "AI super-resolution output", "AI SR Output"],
    ["hr_reference", outputs.hr_reference, "Synthetic high-resolution reference", "HR Reference"],
    ["ndvi", outputs.ndvi, "Enhanced NDVI map", "Enhanced NDVI"],
    ["ndwi", outputs.ndwi, "Enhanced NDWI water map", "Enhanced NDWI"],
    ["evi", outputs.evi, "Enhanced EVI map", "Enhanced EVI"],
    ["vegetation_mask", outputs.vegetation_mask, "Vegetation candidate mask", "Vegetation Mask"],
    ["water_mask", outputs.water_mask, "Water candidate mask", "Water Mask"],
    ["error_map", outputs.error_map, "Pixel-wise reconstruction error map", "Error Map"],
    ["flood_before", outputs.flood_before, "Configured before-period image", "Before"],
    ["flood_ndwi_before", outputs.flood_ndwi_before, "Configured before-period NDWI", "Before NDWI"],
    ["validation_dashboard", outputs.validation_dashboard, "Validation dashboard with metric values", "Validation Dashboard"],
  ].filter((definition) => definition[1]) : [];

  async function fetchSentinelImage(selectedLatitude = latitude, selectedLongitude = longitude) {
    if (selectedLatitude === null || selectedLongitude === null) {
      setError("Please select a location on the map first.");
      return;
    }

    setLoading(true);
    setError("");
    setOutputs(null);
    setSelectedOutput("lr_input");
    setMetrics(null);
    setResultDetails(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/sentinel-image?lat=${selectedLatitude}&lon=${selectedLongitude}`
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Failed to fetch Sentinel-2 image");
      }

      const result = await response.json();
      setOutputs(result.outputs);
      setSelectedOutput("lr_input");
      setMetrics(result.metrics);
      setResultDetails(result);
      setValidationReference(result.validation_reference || "");
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

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
      setOutputs(null);
      setSelectedOutput("lr_input");
      setMetrics(null);
      setResultDetails(null);
      setValidationReference("");
      setError("");
      fetchSentinelImage(lat, lng);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  return (
    <div className="app">

      <div className="map-wrapper">
        <div
          ref={mapContainer}
          className="map-container"
        />

        <nav className="top-navigation" aria-label="Main navigation">
          {["home", "research", "documentation", "about"].map((page) => (
            <button
              key={page}
              className={activePage === page ? "is-active" : ""}
              type="button"
              onClick={() => setActivePage(page)}
            >
              {page === "home" ? "Home" : page[0].toUpperCase() + page.slice(1)}
            </button>
          ))}
        </nav>

        {activePage === "home" && <aside className="selection-panel">
          <>
            <div className="brand-mark">GeoSR-AI</div>
            <p className="eyebrow">Deep Learning Satellite Super Resolution</p>
            <h1>Select Location</h1>
            <p className="instruction">Click anywhere on the map to fetch Sentinel-2 imagery.</p>

            {latitude !== null ? (
              <div className="coordinates">
                <div className="coordinate-card"><span>Latitude</span><strong>{latitude.toFixed(6)}</strong></div>
                <div className="coordinate-card"><span>Longitude</span><strong>{longitude.toFixed(6)}</strong></div>
              </div>
            ) : <div className="no-selection">Click on the map to select a location.</div>}

            {loading && <div className="loading-message">Fetching Sentinel-2 image...</div>}
            {error && <div className="error-message">{error}</div>}

          {metrics && (
            <section className="metrics-section">
              <h2>Validation Metrics</h2>
              <div className="metrics-grid">
                <div className="metric-card"><span>PSNR</span><strong>{metrics.psnr.toFixed(2)} dB</strong></div>
                <div className="metric-card"><span>SSIM</span><strong>{metrics.ssim.toFixed(4)}</strong></div>
                <div className="metric-card"><span>SAM</span><strong>{metrics.sam.toFixed(4)} rad</strong></div>
                <div className="metric-card"><span>RMSE</span><strong>{metrics.rmse.toFixed(4)}</strong></div>
                  <div className="metric-card"><span>MAE</span><strong>{metrics.mae.toFixed(4)}</strong></div>
              </div>
              <p className="validation-reference">{validationReference}</p>
            </section>
          )}

            {outputs && (
            <section className="result-section">
              <h2>Validation Outputs</h2>
              <div className="output-viewer">
                <div className="output-grid">
                  {outputDefinitions.map(([key, src, alt, label]) => (
                    <figure
                      key={key}
                      className={`output-figure${key === "validation_dashboard" ? " dashboard-output" : ""}${selectedOutput === key ? " is-selected" : ""}`}
                      onClick={() => setSelectedOutput(key)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setSelectedOutput(key);
                        }
                      }}
                      tabIndex="0"
                      role="button"
                      aria-pressed={selectedOutput === key}
                    >
                      <img src={src} alt={alt} />
                      <figcaption>{label}</figcaption>
                    </figure>
                  ))}
                </div>
                <div className="selected-output">
                  <span className="selected-output-label">Selected preview</span>
                  <img
                    src={outputs[selectedOutput]}
                    alt="Selected validation output preview"
                  />
                </div>
                <section className="analysis-details" aria-live="polite">
                  <h3>Analysis Details</h3>

                  {metrics && (
                    <div className="detail-block">
                      <h4>Validation Comparison</h4>
                      <div className="comparison-table" role="table" aria-label="SEN2SR and bicubic validation metrics">
                        <div className="comparison-row comparison-heading" role="row">
                          <span>Metric</span><span>SEN2SR</span><span>Bicubic</span>
                        </div>
                        {[["PSNR", "psnr", "dB"], ["SSIM", "ssim", ""], ["SAM", "sam", "rad"], ["RMSE", "rmse", ""], ["MAE", "mae", ""]].map(([label, key, unit]) => (
                          <div className="comparison-row" role="row" key={key}>
                            <span>{label}</span>
                            <span>{Number(metrics[key]).toFixed(4)}{unit && ` ${unit}`}</span>
                            <span>{metrics.bicubic ? `${Number(metrics.bicubic[key]).toFixed(4)}${unit ? ` ${unit}` : ""}` : "Unavailable"}</span>
                          </div>
                        ))}
                      </div>
                      {metrics.per_band_rmse && (
                        <div className="band-metrics">
                          <strong>Per-band errors</strong>
                          {metrics.per_band_rmse.map((value, index) => (
                            <span key={`band-${index}`}>Band {index + 1}: RMSE {Number(value).toFixed(4)}, MAE {Number(metrics.per_band_mae[index]).toFixed(4)}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {resultDetails && (
                    <>
                      <div className="detail-block detail-grid">
                        <div><h4>Model</h4><p>{resultDetails.model?.variant || "SEN2SRLite"} | {resultDetails.model?.device || "Device unavailable"}</p><p>{resultDetails.model?.internal_lr || 128}x{resultDetails.model?.internal_lr || 128} LR tiles | {resultDetails.model?.status || "Status unavailable"}</p></div>
                      </div>

                      {resultDetails.analytics && (
                        <div className="detail-block">
                          <h4>Crop and Urban Analytics</h4>
                          <div className="stat-list">
                            <span>NDVI mean: {resultDetails.analytics.ndvi_mean == null ? "Unavailable" : Number(resultDetails.analytics.ndvi_mean).toFixed(4)}</span>
                            <span>Vegetation: {resultDetails.analytics.vegetation_percentage == null ? "Unavailable" : `${Number(resultDetails.analytics.vegetation_percentage).toFixed(2)}%`} (NDVI &gt; 0.30)</span>
                            <span>Stress: {resultDetails.analytics.stress_percentage == null ? "Unavailable" : `${Number(resultDetails.analytics.stress_percentage).toFixed(2)}%`}</span>
                            <span>NDWI mean: {resultDetails.analytics.ndwi_mean == null ? "Unavailable" : Number(resultDetails.analytics.ndwi_mean).toFixed(4)}</span>
                            <span>Water: {resultDetails.analytics.water_percentage == null ? "Unavailable" : `${Number(resultDetails.analytics.water_percentage).toFixed(2)}%`} (NDWI &gt; 0.00)</span>
                            <span>EVI mean: {resultDetails.analytics.evi_mean == null ? "Unavailable" : Number(resultDetails.analytics.evi_mean).toFixed(4)}</span>
                          </div>
                          <p>{resultDetails.analytics.stress_interpretation}</p>
                        </div>
                      )}

                      {resultDetails.error_analysis && (
                        <div className="detail-block">
                          <h4>Error Analysis</h4>
                          <div className="stat-list"><span>Mean error: {Number(resultDetails.error_analysis.mean_error).toFixed(4)}</span><span>Maximum error: {Number(resultDetails.error_analysis.maximum_error).toFixed(4)}</span><span>Reconstruction consistency error: {Number(resultDetails.error_analysis.reconstruction_consistency_error).toFixed(4)}</span></div>
                        </div>
                      )}

                      {resultDetails.panel_mapping && (
                        <div className="detail-block">
                          <h4>Panel Mapping</h4>
                          <div className="stat-list">
                            {Object.entries(resultDetails.panel_mapping).map(([panel, product]) => <span key={panel}>{panel.replaceAll("_", " ")} - {product.replaceAll("_", " ")}</span>)}
                          </div>
                        </div>
                      )}

                      {resultDetails.interpretation && (
                        <div className="detail-block interpretation-list">
                          <h4>Interpretation</h4>
                          {Object.entries(resultDetails.interpretation).map(([key, value]) => <p key={key}><strong>{key.replaceAll("_", " ")}:</strong> {value}</p>)}
                        </div>
                      )}
                      <p className="validation-reference">{resultDetails.validation_reference}</p>
                    </>
                  )}
                </section>
              </div>
            </section>
            )}
          </>
        </aside>}

        {activePage !== "home" && <main className="page-view">
          <div className="info-page">
            <div className="brand-mark">GeoSR-AI</div>
            {(() => {
              const Page = pageComponents[activePage];
              return <Page />;
            })()}
          </div>
        </main>}
      </div>

    </div>
  );
}

export default App;