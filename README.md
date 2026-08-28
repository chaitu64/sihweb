# 🌍 GeoSR-AI

## Deep Learning Based Super-Resolution Mapping from Medium-Resolution Satellite Imagery

GeoSR-AI is an AI-powered geospatial platform designed to enhance medium-resolution satellite imagery using deep learning-based super-resolution techniques.

The project is being developed for **Problem Statement ID: 26142**, focused on transforming **10m Sentinel-2 satellite imagery into sharper, information-rich outputs with a target spatial resolution below 4m**, while preserving geospatial and spectral consistency.

---

# 📌 Problem Statement

**Problem Statement ID:** 26142

**Title:** Deep Learning Based Super Resolution Mapping (SRM) from Medium Resolution Satellite Imageries

**Organization:** National Technical Research Organisation (NTRO)

**Category:** Software

The objective is to develop an AI-based framework that:

- Accepts medium-resolution satellite imagery.
- Performs preprocessing and geospatial handling.
- Uses Deep Learning / Generative AI for super-resolution.
- Enhances feature visibility.
- Preserves spatial and spectral consistency.
- Validates generated outputs against high-resolution reference data.
- Handles uncertainty in AI-generated details.

---

# 🚀 Current Progress

## ✅ Completed
Sure — you can put the installation process in your `README.md` as simple **point-wise paragraphs** like this:

## ⚙️ Installation and Setup

1. **Clone the repository:** Clone the GeoSR-AI repository to your local system and navigate into the project folder.

```bash
git clone https://github.com/HARINISAI-18/GeoSR-AI.git
cd GeoSR-AI
```

2. **Set up the backend:** Navigate to the backend directory and create a Python virtual environment.

```powershell
cd backend
python -m venv .venv
```

3. **Activate the virtual environment:** Activate the environment before installing the Python dependencies.

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run the following command and activate the environment again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

After successful activation, your terminal should display something similar to:

```text
(.venv) PS ...\GeoSR-AI\backend>
```

4. **Install backend dependencies:** Install all required Python packages listed in `requirements.txt`.

```powershell
pip install -r requirements.txt
```

You can optionally verify the installed packages using:

```powershell
pip list
```

5. **Configure Copernicus credentials:** Inside the `backend` folder, create a `.env` file and add the Copernicus credentials using the environment variable names expected by `copernicus.py`. For example:

```env
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password
```

Or, if your implementation uses OAuth client credentials:

```env
COPERNICUS_CLIENT_ID=your_client_id
COPERNICUS_CLIENT_SECRET=your_client_secret
```

Never upload the `.env` file to GitHub.

6. **Run the backend:** Start the FastAPI server from the `backend` directory.

```powershell
uvicorn app.main:app --reload
```

When running the command from the repository root instead, use:

```powershell
uvicorn backend.app.main:app --reload
```

The backend should start at:

```text
http://127.0.0.1:8000
```

You can also access the FastAPI interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

7. **Set up the frontend:** Open a new terminal, navigate to the frontend directory, and install the required Node.js packages.

```powershell
cd frontend
npm install
```

If MapLibre GL is not installed automatically through the project dependencies, install it using:

```powershell
npm install maplibre-gl
```

8. **Run the frontend:** Start the React application using Vite.

```powershell
npm run dev
```

The terminal will display a local URL similar to:

```text
http://localhost:5173/
```

Open this URL in your browser to use **GeoSR-AI**.

### 🚀 Running the Project Later

After completing the installation once, you only need to run the backend and frontend in two separate terminals.

**Terminal 1 — Backend:**

```powershell
cd GeoSR-AI\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**

```powershell
cd GeoSR-AI\frontend
npm run dev
```


### Satellite Data Acquisition

- Copernicus Data Space Ecosystem integration.
- Copernicus OAuth authentication.
- Sentinel-2 satellite image retrieval.
- Location-based image acquisition using latitude and longitude.
- FastAPI API for satellite image requests.

### Interactive Frontend

- React + Vite frontend.
- Interactive MapLibre map.
- Click anywhere on the map to select a location.
- Dynamic latitude and longitude updates.
- Location marker placement.
- Frontend-to-backend API integration.
- Sentinel-2 image retrieval and display.

### Backend

- FastAPI server.
- Copernicus authentication service.
- Sentinel image retrieval pipeline.
- Environment variable configuration for credentials.

---

# 🏗️ Current Architecture

```text
                    ┌───────────────┐
                    │     User      │
                    └───────┬───────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Interactive Map    │
                 │     MapLibre GL     │
                 └──────────┬──────────┘
                            │
                     User Clicks Map
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Latitude / Longitude│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   React Frontend    │
                 └──────────┬──────────┘
                            │
                        REST API
                            │
                            ▼
                 ┌─────────────────────┐
                 │  FastAPI Backend    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Copernicus OAuth    │
                 │ Authentication      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Copernicus Data     │
                 │ Space Ecosystem     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Sentinel-2 Imagery  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Frontend Display    │
                 └─────────────────────┘
```

---

# 🛠️ Tech Stack

## Frontend

| Technology | Purpose |
|---|---|
| React | User Interface |
| Vite | Frontend Development and Build Tool |
| JavaScript | Application Logic |
| MapLibre GL JS | Interactive Maps |
| CSS | Styling and Responsive UI |
| Fetch API | Communication with Backend |

## Backend

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| FastAPI | REST API Framework |
| Uvicorn | ASGI Server |
| Requests | HTTP Requests |
| Python-dotenv | Environment Variable Management |

## Satellite Data

| Technology | Purpose |
|---|---|
| Copernicus Data Space Ecosystem | Satellite Data Access |
| Sentinel-2 | Medium-Resolution Satellite Imagery |
| OAuth 2.0 | Authentication |

## AI / Machine Learning

The AI model is currently being developed and experimented with separately using Google Colab.

Planned technologies include:

| Technology | Purpose |
|---|---|
| Python | AI Pipeline |
| PyTorch | Deep Learning |
| Google Colab | Model Training and Experimentation |
| NumPy | Numerical Processing |
| Pillow / OpenCV | Image Processing |
| Rasterio | Geospatial Raster Processing |

---

# 📁 Project Structure

```text
GeoSR-AI/
│
├── backend/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── copernicus.py
│   │   └── sentinel_service.py
│   │
│   ├── .env
│   ├── requirements.txt
│   └── .venv/
│
├── frontend/
│   │
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── .gitignore
├── README.md
└── LICENSE
```

> **Note:** `.env`, `.venv`, and `node_modules` should not be uploaded to GitHub.

---

# ⚙️ Prerequisites

Before running the project, install:

## 1. Git

Download and install Git from:

:contentReference[oaicite:0]{index=0}

Check installation:

```bash
git --version
```

---

## 2. Python

Recommended version:

```text
Python 3.10+
```

Check installation:

```bash
python --version
```

---

## 3. Node.js

Install Node.js, preferably the LTS version.

:contentReference[oaicite:1]{index=1}

Check installation:

```bash
node --version
npm --version
```

---

## 4. Copernicus Data Space Account

Create an account with the Copernicus Data Space Ecosystem and configure the credentials required by the backend.

:contentReference[oaicite:2]{index=2}

---

# 🔧 Backend Setup

## Step 1: Navigate to the backend

```bash
cd backend
```

## Step 2: Create a virtual environment

### Windows

```powershell
python -m venv .venv
```

## Step 3: Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Step 4: Install Python dependencies

```powershell
pip install fastapi uvicorn requests python-dotenv
```

Or, if `requirements.txt` is available:

```powershell
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Inside the `backend` folder, create a file:

```text
.env
```

Example:

```env
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password
```

Depending on your current OAuth implementation, the variable names may differ.

For security:

```text
❌ Never upload .env to GitHub
```

You can create a safe example file named:

```text
.env.example
```

Example:

```env
COPERNICUS_USERNAME=your_username_here
COPERNICUS_PASSWORD=your_password_here
```

---

# ▶️ Running the Backend

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

The backend will start at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# 💻 Frontend Setup

Open another terminal.

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

If MapLibre GL is not already installed:

```bash
npm install maplibre-gl
```

---

# ▶️ Running the Frontend

From the `frontend` directory:

```bash
npm run dev
```

Vite will provide a local URL similar to:

```text
http://localhost:5173
```

Open it in your browser.

---

# 🛰️ Current User Workflow

```text
1. User opens GeoSR-AI

          ↓

2. Interactive map loads

          ↓

3. User clicks a location

          ↓

4. Latitude and Longitude are captured

          ↓

5. User clicks "Fetch Sentinel-2 Image"

          ↓

6. React sends coordinates to FastAPI

          ↓

7. FastAPI authenticates with Copernicus

          ↓

8. Sentinel-2 satellite imagery is retrieved

          ↓

9. Satellite image is returned to the frontend

          ↓

10. User views the Sentinel-2 image
```

---

# 📡 Current API

## Sentinel Image Endpoint

```text
GET /sentinel-image
```

### Parameters

```text
lat = Latitude
lon = Longitude
```

Example:

```text
http://127.0.0.1:8000/sentinel-image?lat=16.5062&lon=80.6480
```

The frontend sends the selected coordinates to the backend, and the backend returns the corresponding satellite image.

---

# 🧠 Planned AI Super-Resolution Pipeline

The next phase will connect the current satellite acquisition pipeline with the Deep Learning model.

```text
Sentinel-2 Image
        │
        ▼
Preprocessing
        │
        ├── Normalization
        ├── Band Handling
        ├── Image Tiling
        └── Geospatial Metadata Processing
        │
        ▼
Super-Resolution Model
        │
        ▼
Enhanced Image
        │
        ▼
Post-Processing
        │
        ├── Geospatial Alignment
        ├── Resolution Enhancement
        └── Metadata Preservation
        │
        ▼
Validation & Uncertainty Analysis
        │
        ▼
Final GeoSR-AI Output
```

---

# 🔮 Upcoming Features

## Phase 1 — Satellite Data Pipeline

- [x] Interactive map
- [x] Latitude and longitude selection
- [x] Copernicus authentication
- [x] Sentinel-2 image retrieval
- [x] Frontend image visualization
- [ ] Area of Interest (AOI) selection
- [ ] Date range selection
- [ ] Cloud coverage filtering
- [ ] Sentinel band selection
- [ ] GeoTIFF support

## Phase 2 — AI Super Resolution

- [ ] Finalize model architecture
- [ ] Prepare paired low-resolution and high-resolution datasets
- [ ] Train baseline super-resolution model
- [ ] Evaluate model performance
- [ ] Export trained model

## Phase 3 — Model Integration

- [ ] Integrate trained PyTorch model with FastAPI
- [ ] Create super-resolution inference endpoint
- [ ] Send Sentinel imagery to the model
- [ ] Generate enhanced output
- [ ] Return enhanced image to frontend
- [ ] Before/After image comparison

## Phase 4 — Validation

- [ ] PSNR
- [ ] SSIM
- [ ] RMSE
- [ ] Spectral consistency analysis
- [ ] High-resolution reference validation

## Phase 5 — Uncertainty Analysis

- [ ] AI confidence estimation
- [ ] Uncertainty map generation
- [ ] Identification of model-inferred regions

## Phase 6 — Applications

- [ ] Urban analysis
- [ ] Crop monitoring
- [ ] Disaster assessment
- [ ] Change detection

---

# 📊 Expected Final Workflow

```text
                    GeoSR-AI

                        User
                          │
                          ▼
                  Interactive Map
                          │
                          ▼
                Area of Interest Selection
                          │
                          ▼
                  Sentinel-2 Acquisition
                          │
                          ▼
                    Preprocessing
                          │
                          ▼
              AI Super-Resolution Model
                          │
                          ▼
                Enhanced Satellite Image
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Validation    Uncertainty   Analysis
             │            │            │
             └────────────┼────────────┘
                          │
                          ▼
                    User Dashboard
```

---

# 📊 Evaluation Metrics

The final model will be evaluated using:

- **PSNR** — Peak Signal-to-Noise Ratio
- **SSIM** — Structural Similarity Index
- **RMSE** — Root Mean Square Error
- **SAM** — Spectral Angle Mapper

These metrics will help evaluate both visual reconstruction quality and scientific reliability.

---

# ⚠️ Important Note on AI-Generated Details

Super-resolution models can infer spatial details that were not directly captured by the original satellite sensor.

Therefore, GeoSR-AI will include validation and uncertainty analysis to distinguish between:

```text
Observed Satellite Information
            vs
AI-Inferred Spatial Details
```

The enhanced output should be treated as an analytical reconstruction rather than a replacement for direct high-resolution observation.

---

# 🔒 Security

The following files must never be committed:

```text
.env
.venv/
node_modules/
```

Before pushing changes:

```bash
git status
```

Make sure sensitive credentials and large dependency folders are not included.

---

# 🤝 Contribution

This project is currently under active development.

Future contributions may include improvements in:

- Deep Learning architectures
- Remote sensing preprocessing
- Geospatial data handling
- Model validation
- Frontend visualization
- Uncertainty estimation

---

# 📜 License

This project is licensed under the repository's included license.

---

# 🚧 Development Status

**Current Version: v0.1**

### Current Milestone

> **Sentinel-2 Satellite Image Acquisition and Frontend-Backend Integration**

The current system successfully supports:

```text
Map Location Selection
        ↓
Latitude / Longitude
        ↓
FastAPI
        ↓
Copernicus Data Space Ecosystem
        ↓
Sentinel-2 Image
        ↓
Frontend Visualization
```

### Next Milestone

> **Integrating the Deep Learning Super-Resolution Model into the GeoSR-AI inference pipeline.**