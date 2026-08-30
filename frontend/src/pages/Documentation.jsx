import { useState, useEffect, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

function Documentation() {
  const pdfUrl = "/GeoSR-AI_Complete_Documentation.pdf";
  const [numPages, setNumPages] = useState(null);
  const [scale, setScale] = useState(1.0);
  const [enableText, setEnableText] = useState(false);
  const [containerWidth, setContainerWidth] = useState(1200);

  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Set initial width
    setContainerWidth(containerRef.current.getBoundingClientRect().width);

    const observer = new ResizeObserver((entries) => {
      if (entries[0]) {
        setContainerWidth(entries[0].contentRect.width);
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
  }

  const zoomIn = () => setScale((prev) => Math.min(prev + 0.15, 2.0));
  const zoomOut = () => setScale((prev) => Math.max(prev - 0.15, 0.6));
  const zoomReset = () => setScale(1.0);

  // Side-by-side if container is wider than 850px, otherwise single column
  const isSideBySide = containerWidth > 850;

  // Calculate base page width to fit the screen
  const basePageWidth = isSideBySide
    ? (containerWidth - 40) / 2 // two columns minus the gap
    : containerWidth - 20; // single column minus padding

  return (
    <>
      <p className="eyebrow">How GeoSR-AI Works</p>
      <h1>Documentation</h1>
      <p>
        Select a location on the map to request Sentinel-2 imagery. The service
        prepares the input, runs the super-resolution model, and returns visual
        outputs with validation metrics.
      </p>

      {/* ── Documentation PDF ── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: 36,
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <h2>Technical Documentation</h2>

        {/* Modern PDF Controls Toolbar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            background: "#f3f4f6",
            padding: "6px 12px",
            borderRadius: "30px",
            border: "1px solid #e5e7eb",
            boxShadow: "0 2px 5px rgba(0,0,0,0.05)",
          }}
        >
          {/* Zoom Out */}
          <button
            onClick={zoomOut}
            title="Zoom Out"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "4px",
              color: "#34445e",
              borderRadius: "50%",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "#e5e7eb")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>

          {/* Scale Indicator & Reset */}
          <span
            onClick={zoomReset}
            title="Reset Zoom"
            style={{
              fontSize: "13px",
              fontWeight: "bold",
              color: "#4b5563",
              minWidth: "45px",
              textAlign: "center",
              cursor: "pointer",
              userSelect: "none",
            }}
          >
            {Math.round(scale * 100)}%
          </span>

          {/* Zoom In */}
          <button
            onClick={zoomIn}
            title="Zoom In"
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "4px",
              color: "#34445e",
              borderRadius: "50%",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "#e5e7eb")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>

          <div style={{ width: "1px", height: "18px", background: "#d1d5db" }} />

          {/* Text Selection Toggle */}
          <button
            onClick={() => setEnableText(!enableText)}
            title={
              enableText
                ? "Text selection is enabled"
                : "Enable text selection (may affect layout rendering)"
            }
            style={{
              background: enableText ? "#34445e" : "transparent",
              border: "none",
              borderRadius: "15px",
              padding: "4px 10px",
              fontSize: "12px",
              fontWeight: "600",
              color: enableText ? "#fff" : "#4b5563",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            {enableText ? "✓ Select Text" : "Select Text"}
          </button>
        </div>
      </div>

      <div ref={containerRef} style={{ width: "100%", overflowX: "auto" }}>
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div
              style={{
                textAlign: "center",
                padding: 40,
                color: "#777",
                fontSize: 14,
              }}
            >
              Loading documentation…
            </div>
          }
        >
          <div
            style={{
              display: "flex",
              gap: 20,
              marginTop: 16,
              justifyContent: "center",
              flexWrap: isSideBySide ? "nowrap" : "wrap",
            }}
          >
            {numPages &&
              Array.from({ length: numPages }, (_, i) => (
                <div
                  key={i}
                  style={{
                    border: "1px solid #e3e3e3",
                    borderRadius: 10,
                    overflow: "hidden",
                    background: "#fff",
                    boxShadow: "0 2px 10px rgba(0,0,0,0.08)",
                    flex: "0 0 auto",
                    transition: "all 0.2s ease-in-out",
                  }}
                >
                  <Page
                    pageNumber={i + 1}
                    width={basePageWidth}
                    scale={scale}
                    renderTextLayer={enableText}
                    renderAnnotationLayer={enableText}
                  />
                </div>
              ))}
          </div>
        </Document>
      </div>

      <div style={{ textAlign: "center", marginTop: 24, marginBottom: 32 }}>
        <a
          href={pdfUrl}
          download="GeoSR-AI_Complete_Documentation.pdf"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "10px 22px",
            background: "#34445e",
            color: "#fff",
            borderRadius: 20,
            textDecoration: "none",
            fontSize: 14,
            fontWeight: 600,
            transition: "background 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#4a5a74")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "#34445e")}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download PDF
        </a>
      </div>
    </>
  );
}

export default Documentation;
