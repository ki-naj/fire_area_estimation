# Automated Wildfire Burned Area Delineation using Open Data and Google Earth Engine

**A proof-of-concept methodology for delineating burned areas from satellite imagery using spectral analysis and open-source geospatial tools.**

**Status:** Experimental / Case Study  
**Tested On:** Single fire event case study (Catalonia, Spain, August 2023)  
**Last Updated:** February 2026

---

## Executive Summary

This project presents an **automated, reproducible workflow** for detecting and quantifying wildfire burned areas using freely available satellite data and open-source geospatial tools. The methodology combines:

- **Spectral change detection** via Normalized Burn Ratio (NBR) and delta-NBR (dNBR)
- **Automatic threshold optimization** using Otsu's method
- **Water body masking** to isolate land areas
- **Multi-stage comparative analysis** to evaluate methodological variations
- **Interactive web-based visualization** of results

The workflow has been validated on a **single test case** (wildfire in Catalonia, Spain, August 2023). This implementation is intended as a **proof-of-concept** to demonstrate the feasibility of automated burn area delineation, not as a production-ready system.

---

## Background and Motivation

Rapid assessment of wildfire extent is critical for disaster response, damage estimation, and post-fire recovery planning. Traditional methods rely on expert interpretation of satellite imagery or field surveys, which are time-consuming and often delayed. 

This project demonstrates how **freely available satellite data** (Sentinel-2) and **free cloud-based geospatial tools** (Google Earth Engine) can be combined with automated spectral analysis to provide rapid, reproducible burn area estimates. The approach is intended to support research, education, and proof-of-concept demonstrations—not operational firefighting or damage assessment.

---

## Methodology

### Data Acquisition

**Satellite Imagery:**
- **Source:** Copernicus Sentinel-2 Level 2A Surface Reflectance (atmospherically corrected)
- **Spatial Resolution:** 20 m (multispectral bands), 10 m resampled option available
- **Temporal Resolution:** 5-day revisit cycle (single location)
- **Spectral Bands Used:** B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), B11–B12 (SWIR)
- **Access Method:** Google Earth Engine API (freely available with registration)

**Area of Interest (AOI):**
- User-defined rectangular region [west, south, east, north] in WGS84 coordinates
- Configurable via `config/config.py`

### Workflow Overview

The analysis proceeds through **four sequential stages** to evaluate different methodological approaches:

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 0: Data Preparation                                       │
│  • Fetch Sentinel-2 imagery (pre- and post-fire)                │
│  • Calculate water mask from NDWI                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐┌─────▼──────┐┌─────▼──────┐┌─────▼──────┐
│  STAGE 1     ││  STAGE 2   ││  STAGE 3   ││  STAGE 4   │
│  Original    ││ Bbox (Fire)││ Original   ││ Bbox (Fire)│
│  AOI - Basic ││ AOI -Basic ││ AOI -Water ││ AOI -Water │
│              ││            ││ Masked     ││ Masked     │
└───────┬──────┘└─────┬──────┘└─────┬──────┘└─────┬──────┘
        │             │             │             │
        └─────────────┼─────────────┼─────────────┘
                      │
         ┌────────────▼───────────┐
         │  Output Generation     │
         │  • 4 HTML Maps         │
         │  • CSV Summary         │
         │  • GeoTIFF Exports     │
         │  • Histograms          │
         └────────────────────────┘
```

### Spectral Index Calculations

#### 1. **Normalized Difference Water Index (NDWI)**
$$\text{NDWI} = \frac{B3 - B8}{B3 + B8}$$

Used to distinguish water bodies from land. Threshold of 0.0 typically separates water (NDWI > 0) from land (NDWI ≤ 0).

#### 2. **Normalized Burn Ratio (NBR)**
$$\text{NBR} = \frac{B8 - B12}{B8 + B12}$$

Highlights recently burned vegetation. Ranges from -1 (water) to +1 (healthy vegetation). Burned areas typically show negative values.

#### 3. **Delta-NBR (dNBR) – Change Detection Index**
$$\text{dNBR} = \text{NBR}_{\text{pre-fire}} - \text{NBR}_{\text{post-fire}}$$

Quantifies the magnitude of vegetation change between pre-fire and post-fire conditions. Higher dNBR values indicate more severe burns.

**Burn Severity Classification (standard thresholds):**
- **Low:** dNBR > 0.05
- **Moderate-Low:** dNBR > 0.075
- **Moderate:** dNBR > 0.1
- **High:** dNBR > 0.2
- **Very High:** dNBR > 0.3

### Fire Delineation Algorithm

**Step 1: Otsu's Automatic Thresholding**
- Compute histogram of dNBR values across AOI
- Apply Otsu's method to find the optimal threshold that maximizes between-class variance
- This automatically identifies the dNBR value best separating burned from unburned pixels
- No manual threshold tuning required for this step

**Step 2: Seed Mask Generation**
- Create initial binary mask of pixels exceeding Otsu threshold
- Vectorize into polygons using 8-connected component labeling

**Step 3: Iterative Mask Growth**
- Progressively expand seed mask using lower dNBR thresholds: [0.10, 0.075, 0.05]
- Grow only polygons that intersect with seed regions (prevents over-expansion)
- Retains connectivity to high-confidence burn pixels

**Step 4: Minimum Area Filtering**
- Remove polygons smaller than 0.5 hectares
- Reduces noise and small misclassifications

**Step 5: Water Masking (Stages 3–4 only)**
- Create combined water mask from pre- and post-fire NDWI
- Apply as negative mask to exclude water pixels from burned area calculations
- Prevents water bodies from being misclassified as burned vegetation

### Multi-Stage Analysis Framework

Each stage applies the algorithm with different configurations:

| Stage | AOI | Water Mask | Purpose |
|-------|-----|-----------|---------|
| 1     | Original study area | None | Baseline analysis on full AOI |
| 2     | Bounding box of fires | None | Fire-focused sub-region analysis |
| 3     | Original study area | Applied | Water-corrected full AOI |
| 4     | Bounding box of fires | Applied | Water-corrected fire-focused |

This multi-stage design allows comparison of:
- **Full AOI vs. fire-focused sub-regions** (effect of spatial extent)
- **Water-masked vs. non-masked** (effect of water bodies on accuracy)

---

## Software Requirements and Dependencies

### Python Environment
- **Python Version:** 3.8, 3.9, 3.10, 3.11, or 3.12
- **Environment Manager:** `venv` (built-in) or `conda` recommended

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `earthengine-api` | ≥1.7.0 | Google Earth Engine Python API |
| `geemap` | ≥0.30.0 | Interactive geospatial mapping (built on `folium`) |
| `numpy` | ≥1.20.0 | Numerical computing (Otsu algorithm) |
| `matplotlib` | ≥3.5.0 | Histogram visualization |
| `google-cloud-storage` | ≥2.0.0 | Cloud data access (Earth Engine backend) |

**Optional Dependencies (for development):**
- `pytest` – unit testing
- `black` – code formatting
- `flake8` – linting
- `isort` – import organization

---

## Installation and Setup

### Prerequisites
- Google account with access to Google Earth Engine (free tier available; [register here](https://earthengine.google.com))
- Python 3.8+ installed on your system
- Git (optional, for cloning project)

### Step-by-Step Installation

**1. Clone or obtain the project:**
```bash
cd path/to/dnbr_project
```

**2. Create a virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

**3. Upgrade pip and install dependencies:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Authenticate with Google Earth Engine:**
```bash
python -c "import ee; ee.Authenticate()"
```

This opens a browser window to authorize access. Follow the prompts to:
- Sign in with your Google account
- Grant permission for Earth Engine
- Copy and paste the authorization code back into the terminal

Your credentials are cached locally after first authentication.

**5. (Optional) Install development tools:**
```bash
pip install pytest black flake8 isort
```

---

## Configuration

All user-configurable parameters are centralized in **`config/config.py`**. Before running an analysis, edit this file to specify your study area and fire dates.

### Required Parameters

```python
# Earth Engine & Project Setup
EE_PROJECT_ID = "your-ee-project-id"      # Your GEE project ID

# Area of Interest (rectangular)
AOI_COORDS = [lon_west, lat_south, lon_east, lat_north]
# Example: [3.09, 42.398, 3.19, 42.435]  (Catalonia test case)

# Pre-fire date range (should be within 2-3 months before fire)
PRE_FIRE_DATE_START = "YYYY-MM-DD"
PRE_FIRE_DATE_END = "YYYY-MM-DD"
PRE_IMAGE_ID = "sentinel2_granule_id"    # Specific image to use (see output logs)

# Post-fire date range (should be 1-7 days after fire for optimal sensitivity)
POST_FIRE_DATE_START = "YYYY-MM-DD"
POST_FIRE_DATE_END = "YYYY-MM-DD"
POST_IMAGE_ID = "sentinel2_granule_id"   # Specific image to use

# Sentinel-2 collection
SENTINEL2_COLLECTION = "COPERNICUS/S2_SR"   # Level 2A Surface Reflectance
```

### Analysis Parameters

```python
# Processing resolution and memory
SCALE = 20                    # Analysis resolution in meters (20m default, 10m available)
MAX_PIXELS = 1e9             # Maximum pixels for computation (1 billion typical)
NDWI_THRESHOLD = 0.0         # NDWI threshold for water detection (0.0 standard)

# Burn severity thresholds (standard USGS dNBR classifications)
SEVERITY_THRESHOLDS = {
    "low": 0.05,
    "moderate_low": 0.075,
    "moderate": 0.1,
    "high": 0.2,
    "very_high": 0.3
}

# Fire mask growth parameters (for polygon refinement)
FIRE_GROWTH_THRESHOLDS = [0.10, 0.075, 0.05]  # Progressive dNBR thresholds
MIN_AREA_HA = 0.5                             # Minimum polygon area (hectares)
BUFFER_DISTANCE = 20                          # Bounding box buffer (meters)
```

### How to Select Image IDs

1. Run the analysis script—the first phase will list available Sentinel-2 images
2. Output will show format:
   ```
   PRE-FIRE - 4 images
   [0] 2023-07-31 Sentinel-2A Cloud: 2.5% ID: 20230731T103631_20230731T104041_T31TEG
   [1] 2023-08-01 Sentinel-2B Cloud: 15.0% ID: ...
   ```
3. Select images with lowest cloud cover over your AOI
4. Copy the full `system:index` value to config file

---

## Usage

### Basic Workflow

**1. Prepare configuration file:**
```bash
# Edit config/config.py with your study area and fire dates
```

**2. Run the analysis:**
```bash
python main.py
```

**3. Monitor progress:**
The script logs each stage:
```
INFO - SETUP: IMAGERY & INDICES
INFO - Collections fetched
INFO - ANALYSIS 1/4: ORIGINAL AOI - BASIC
INFO - ANALYSIS 2/4: BOUNDING BOX - BASIC
INFO - ANALYSIS 3/4: ORIGINAL AOI - WATER MASKED
INFO - ANALYSIS 4/4: BOUNDING BOX - WATER MASKED
INFO - ALL LAYERS EXPORTED SUCCESSFULLY
```

### Advanced Options

**Run with custom output directory:**
```bash
python main.py --output /path/to/custom/output
```

**Enable verbose logging:**
```bash
python main.py --verbose
```

**Use custom configuration file:**
```bash
python main.py --config /path/to/custom/config.py
```

### 10-Meter Resolution Analysis

For higher spatial detail (at increased processing cost), use the 10-meter resolution variant:
```bash
python main_10m.py
```

This resamples Sentinel-2 bands to 10 m and produces separate output files with `_10m_` prefix.

---

## Outputs

### Output Directory Structure

```
output/
├── burn_area_map_01_original_basic.html          # Interactive map - Stage 1
├── burn_area_map_02_bbox_basic.html              # Interactive map - Stage 2
├── burn_area_map_03_original_water.html          # Interactive map - Stage 3
├── burn_area_map_04_bbox_water.html              # Interactive map - Stage 4
├── analysis_summary.csv                          # Tabular results (all stages)
├── analysis_summary_10m.csv                      # 10m resolution results (if run)
├── histograms/
│   ├── histogram_01_original_basic.png
│   ├── histogram_02_bbox_basic.png
│   ├── histogram_03_original_water.png
│   └── histogram_04_bbox_water.png
└── exports/
    ├── aoi_boundary_04.shp(.dbf, .shx, .prj)     # AOI polygons
    ├── fire_polygons_04.shp(.dbf, .shx, .prj)    # Detected fire boundaries
    ├── water_mask_polygons_04.shp(...)           # Water bodies
    ├── dNBR_04.tif                               # dNBR raster (GeoTIFF)
    ├── burned_area_mask_04.tif                   # Binary burn mask (GeoTIFF)
    └── post_fire_RGB_04.tif                      # Post-fire RGB composite
```

### 1. Interactive HTML Maps

**File:** `burn_area_map_XX_*.html`  
**Format:** Interactive web-based maps (open in any browser)  
**Contents:**
- **Base layers:** Satellite RGB imagery (Sentinel-2 true color composite)
- **Overlay layers:**
  - dNBR raster (continuous values, color-coded)
  - Burn severity classifications (0.05, 0.075, 0.1, 0.2, 0.3 thresholds)
  - Fire polygons with area labels
  - Water masks (where applicable)
  - AOI boundaries

**Interactions:**
- Pan and zoom
- Toggle layers on/off
- View pixel values (hover)
- Layer transparency control

### 2. CSV Summary Table

**File:** `analysis_summary.csv`  
**Delimiter:** Semicolon (`;`), RFC 4180 compliant  
**Columns:**

| Column | Description | Example |
|--------|-------------|---------|
| Analysis Name | Stage name | "Original AOI - Water Masked" |
| AOI Type | Full area or fire-focused | "Original AOI" |
| Analysis Type | Method variant | "WATER_MASKED" |
| Water Masked | Mask applied? | "YES" / "NO" |
| AOI Area (ha) | Total area analyzed | "12.5634" |
| Otsu Threshold | Auto-selected dNBR value | "0.0847" |
| Otsu Area (ha) | Burned area by Otsu method | "2.3421" |
| Low (>0.05) | Low severity pixels | "3.1200" |
| Moderate-Low (>0.075) | Moderate-low severity | "2.8956" |
| Moderate (>0.1) | Moderate severity | "2.5342" |
| High (>0.2) | High severity | "1.8765" |
| Very High (>0.3) | Very high severity | "0.9876" |
| Burned Area (ha) | Final polygonized area | "2.3421" |
| Map File | Associated HTML map filename | "burn_area_map_04_bbox_water.html" |
| Timestamp | ISO datetime of execution | "2023-08-15T14:32:11.234567" |

### 3. Histograms

**Files:** `histograms/histogram_XX_*.png`  
**Format:** PNG raster images  
**Contents:**
- dNBR value distribution across AOI
- Otsu threshold marked with vertical line
- Severity thresholds indicated
- Axes: dNBR range [-0.5, 0.8], pixel count

### 4. Georeferenced Exports

**Files:** Shapefiles (`.shp`) and GeoTIFFs (`.tif`)  
**Coordinate System:** EPSG:4326 (WGS84) for vectors; native UTM for rasters  
**Contents:**

- **`aoi_boundary_04.shp`** – Rectangle of analyzed area
- **`fire_polygons_04.shp`** – Detected burned area polygons with attributes:
  - `burned` – Classification flag
  - `area_ha` – Polygon area in hectares
- **`water_mask_polygons_04.shp`** – Water body boundaries
- **`dNBR_04.tif`** – Continuous dNBR raster (-1 to +1)
- **`burned_area_mask_04.tif`** – Binary mask (0=unburned, 1=burned)
- **`post_fire_RGB_04.tif`** – 3-band RGB composite (B4, B3, B2)

**Note:** Only Stage 4 (Bounding Box – Water Masked) results are exported as shapefiles/GeoTIFFs to avoid redundancy.

---

## Expected Inputs and Outputs

### Input Data

**Minimal user input required:**
1. **Google Earth Engine project ID** (free GEE account)
2. **Study area coordinates** (WGS84 rectangle)
3. **Date range** (2–3 month pre-fire window, 1–7 day post-fire window)
4. **Image IDs** (automated lookup with script help)

### Sentinel-2 Scene Requirements

For successful analysis, ensure:
- ✓ Cloud cover < 20% over AOI (ideally < 5%)
- ✓ Pre-fire image within 2–3 months before fire date
- ✓ Post-fire image within 1–7 days after fire date (1–3 days optimal for fresh burns)
- ✓ Same Sentinel-2 tile or overlapping tiles (same MGRS ID recommended)

### Output Data Quality

**Expected accuracy metrics:**
- **Spatial resolution:** 20 m (per-pixel); 10 m available with `main_10m.py`
- **Burn polygons:** ±1–2 pixels (~20–40 m) boundary uncertainty
- **Area estimates:** ±5–15% depending on fire heterogeneity and imagery timing
- **Severity classification:** Relative (low→high) rather than absolute

---

## Limitations and Known Issues

### Methodological Limitations

⚠️ **Case Study Scope**
- Methodology validated on **only one fire event** (Catalonia, August 2023)
- **No cross-validation** across multiple fires or time periods
- **No comparison** with field-surveyed burn perimeters
- Transferability to other regions/fire types **NOT demonstrated**

⚠️ **Sentinel-2 Constraints**
- **Temporal resolution:** 5-day revisit cycle; may miss rapid fire spread
- **Cloud sensitivity:** High cloud cover requires longer pre/post fire windows
- **Spatial resolution:** 20 m (main) or 10 m (variant) too coarse for fine fire details
- **Sun angle:** Higher latitudes suffer seasonal illumination limitations

⚠️ **Misclassification Risks**
- **Post-fire logging/harvesting** produces similar dNBR signature to burns
- **Vegetation stress** (disease, drought) may mimic burn spectral pattern
- **Water bodies** with vegetation (wetlands, mangroves) can be misclassified
- **Urban areas** may show false positives due to surface changes
- **Snow/ice** produces high NBR values (rare in Mediterranean region)

⚠️ **Algorithm Limitations**
- **Otsu threshold** assumes bimodal dNBR distribution (not always valid)
- **Minimum area filter** (0.5 ha) excludes small scattered burns
- **Fixed severity thresholds** may not be optimal for all burn types
- **Polygon growth** algorithm can expand into unburned areas in low-dNBR transitions

### Technical Limitations

⚠️ **Google Earth Engine**
- Requires internet connection and active GEE account
- Computational costs scale with area size (typically < $1 USD per analysis)
- Rate limits on API calls (usually not restrictive for single-user research)

⚠️ **Geospatial Data**
- Output shapefiles create **separate files per layer** (not geodatabase)
- Large areas (> 100,000 ha) may exceed GEE memory limits
- Long computation times possible for regional-scale analysis (> 1 hour)

---

## Validation and Future Improvements

### Recommended Validation Approaches

For production use or peer-reviewed publication, the following validations are **strongly recommended**:

1. **Field Validation**
   - Compare delineated burn areas with GPS field surveys
   - Document any false positives/negatives
   - Quantify omission and commission errors

2. **Cross-Validation with Ground Truth**
   - Compare against official fire perimeter maps (from fire agencies)
   - Compute confusion matrix (sensitivity, specificity, F1-score)
   - Test on multiple fire events across different ecosystems

3. **Sensitivity Analysis**
   - Vary Otsu/growth thresholds and quantify impact
   - Test different pre/post-fire timing windows
   - Evaluate water mask threshold sensitivity

4. **Multi-Sensor Comparison**
   - Cross-check with alternative sensors (Landsat 8/9, PlanetScope)
   - Validate against LiDAR-derived burn severity (where available)

### Suggested Improvements

**Short-term enhancements:**
- [ ] Add confidence/uncertainty metrics to outputs
- [ ] Implement automated cloud masking
- [ ] Add batch processing for multiple fires
- [ ] Dashboard interface for parameter tuning

**Medium-term enhancements:**
- [ ] Integration with Landsat 8/9 for 16-day revisit cycle
- [ ] Machine learning model for burn severity regression
- [ ] Temporal trajectory analysis (vegetation recovery)
- [ ] Integration with fire weather data (FWI, FFMC indices)

**Long-term enhancements:**
- [ ] Comparative study across global fire-prone regions
- [ ] Near-real-time operational system with MODIS/VIIRS data
- [ ] Sub-meter resolution using Planet or Maxar satellite data
- [ ] Multi-temporal analysis for burn severity change detection

---

## Project Structure

```
dnbr_project/
├── main.py                          Main orchestration script (20 m resolution)
├── main_10m.py                      10 m resolution variant (higher detail)
├── config/
│   ├── config.py                    User configuration (EDIT THIS)
│   └── __pycache__/
├── src/
│   └── dnbr/
│       ├── __init__.py              Package initialization
│       ├── earth_engine_utils.py    Earth Engine API wrappers
│       ├── spectral_indices.py      Spectral calculations (NDWI, NBR, dNBR)
│       ├── fire_analysis.py         Fire detection & polygon algorithms
│       ├── mask_operations.py       Water mask creation
│       ├── html_visualization.py    Interactive map generation
│       ├── file_visualization.py    Static visualization (plots, histograms)
│       ├── export_operations.py     CSV/GeoTIFF/Shapefile export
│       └── __pycache__/
├── data/                            Input data directory (optional)
├── output/                          Analysis outputs (generated)
├── requirements.txt                 Python dependencies
├── setup.py                         Package installer metadata
├── .gitignore                       Git exclusions
└── README.md                        This file
```

---

## Getting Started

### Quickstart (5 minutes)

```bash
# 1. Activate environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Edit configuration
nano config/config.py     # Set AOI_COORDS, dates, image IDs

# 3. Run analysis
python main.py

# 4. View results
# Open burn_area_map_04_bbox_water.html in web browser
# View analysis_summary.csv in spreadsheet application
```

### Example Configuration

For the **Catalonia August 2023 case study:**

```python
AOI_COORDS = [3.09, 42.398, 3.19, 42.435]
PRE_FIRE_DATE_START = "2023-07-30"
PRE_FIRE_DATE_END = "2023-08-01"
POST_FIRE_DATE_START = "2023-08-02"
POST_FIRE_DATE_END = "2023-08-06"
PRE_IMAGE_ID = "20230731T103631_20230731T104041_T31TEG"
POST_IMAGE_ID = "20230805T103629_20230805T103641_T31TEG"
```

Then execute:
```bash
python main.py --verbose
```

Expected runtime: ~10–15 minutes (depending on internet speed and GEE load)

---

## Technical References

### Key Publications & Standards

**Spectral Index Methodology:**
- Key, C. H., & Benson, N. C. (2006). *Landscape Assessment (LA) Sampling and Analysis Methods.* USDA Forest Service General Technical Report RMRS-GTR-164-CD.
  - Defines NBR and dNBR burn classification thresholds

**Otsu's Thresholding Algorithm:**
- Otsu, N. (1979). "A Threshold Selection Method from Gray-Level Histograms." *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66.
  - Foundation for automatic threshold optimization

**Sentinel-2 Mission Documentation:**
- ESA Copernicus Sentinel-2 mission overview: https://sentinel.esa.int/web/sentinel/missions/sentinel-2
- Sentinel-2 Level-2A Product Specification: https://sentinels.copernicus.eu/

**Google Earth Engine Documentation:**
- Earth Engine API: https://developers.google.com/earth-engine
- geemap Interactive Mapping: https://geemap.org/

---

## Common Issues and Troubleshooting

### 💡 Installation Issues

**Problem:** `ModuleNotFoundError: No module named 'ee'`
```bash
# Solution: Reinstall earthengine-api
pip install --force-reinstall earthengine-api>=1.7.0
```

**Problem:** `KeyError 'dNBR'` in histogram calculation
```bash
# Solution: Ensure image has calculated spectral indices
# Verify spectral_indices.py is correctly calculating dNBR
```

**Problem:** `PermissionError` when writing output files
```bash
# Solution: Check write permissions to output directory
chmod -R 755 output/  # Linux/Mac
# or check folder properties on Windows
```

### 🔑 Authentication Issues

**Problem:** `EEException: Your Earth Engine account does not have permission to access this dataset`
```bash
# Solution: Ensure your GEE account is approved
# 1. Sign up at https://earthengine.google.com (free tier)
# 2. Re-authenticate: python -c "import ee; ee.Authenticate(force=True)"
# 3. Wait 24–48 hours for approval if newly registered
```

**Problem:** `Access Denied` on Earth Engine API
```bash
# Solution: Clear cached credentials and re-authenticate
# Windows: Delete C:\Users\<username>\.config\earthengine\
# Linux/Mac: rm -rf ~/.config/earthengine/
python -c "import ee; ee.Authenticate()"
```

### 📊 Processing Issues

**Problem:** `MemoryError` or `Computation Timed Out`
```python
# Solution: Reduce processing area or increase MAX_PIXELS
# In config.py:
MAX_PIXELS = 5e8  # Reduce from 1e9

# Or reduce AOI_COORDS extent
AOI_COORDS = [3.12, 42.41, 3.17, 42.42]  # Smaller area
```

**Problem:** No cloud-free images found within date range
```bash
# Solution: Expand date range or inspect collection
# In config.py:
PRE_FIRE_DATE_START = "2023-07-01"  # Expand earlier
PRE_FIRE_DATE_END = "2023-08-05"    # Extend later
```

### 🗺️ Output Issues

**Problem:** HTML maps not displaying / blank maps
```bash
# Solution: Check geemap version and reinstall
pip install --upgrade geemap>=0.30.0

# Verify internet connectivity to tile servers (basemap)
```

**Problem:** CSV file is empty or has only header
```bash
# Solution: Ensure analyses completed successfully
# Check console output for errors during export phase
# Verify results_dict was properly populated
```

---

## Code Examples for Advanced Users

### Custom Threshold Analysis

Modify burn severity thresholds for your specific ecosystem:

```python
# In your custom script:
from src.dnbr import *
from config.config import *

# Custom thresholds for dry forest vs. Mediterranean
CUSTOM_THRESHOLDS = {
    "very_low": 0.01,
    "low": 0.05,
    "moderate": 0.15,
    "high": 0.25
}

# Run classification with custom thresholds
mask, area = classify_by_threshold(dnbr, 0.05, aoi, SCALE, MAX_PIXELS)
print(f"Custom threshold area: {area:.2f} ha")
```

### Accessing Results Programmatically

Post-process results without running full analysis:

```python
import ee
ee.Initialize(project=EE_PROJECT_ID)

# Load previously calculated indices
from config.config import *
aoi = get_aoi_geometry(AOI_COORDS)

# Recalculate with different thresholds
mask_low = dnbr.gt(0.03)
mask_high = dnbr.gt(0.15)

print(f"Area > 0.03: {calculate_area(mask_low, aoi)} ha")
print(f"Area > 0.15: {calculate_area(mask_high, aoi)} ha")
```

### Temporal Analysis (Multi-Year)

Compare multiple fire seasons:

```python
# Modify config.py to loop through years
years = [2022, 2023, 2024]
results = {}

for year in years:
    # Update dates in config
    PRE_FIRE_DATE_START = f"{year}-07-15"
    POST_FIRE_DATE_END = f"{year}-08-31"
    
    # Run analysis and collect results
    results[year] = main()
    
# Export comparison
for year, result in results.items():
    print(f"{year}: {result['total_area']:.2f} ha burned")
```

---

## Contributing and Development

### Setting Up Development Environment

```bash
# Clone repository (if version controlled)
git clone <repository-url>
cd dnbr_project

# Create development virtual environment
python -m venv venv-dev
source venv-dev/bin/activate

# Install with development dependencies
pip install -r requirements.txt
pip install pytest black flake8 isort
```

### Code Style and Quality

This project follows PEP 8 Python conventions:

```bash
# Format code
black src/dnbr/ config/ main.py

# Check linting
flake8 src/dnbr/ config/ main.py --max-line-length=100

# Sort imports
isort src/dnbr/ config/ main.py
```

### Testing

Run test suite (development feature):

```bash
pytest tests/ -v
```

### Project Development Roadmap

**Current Version:** 1.0.0 (Proof of Concept)

**Future Versions:**
- **v1.1:** Real-time processing dashboard (Q2 2026)
- **v1.2:** Landsat 8/9 integration (Q3 2026)
- **v2.0:** Machine learning burn severity model (Q4 2026)
- **v2.1:** Operational monitoring system (Q1 2027)

---

## FAQ (Frequently Asked Questions)

**Q: Can I use this for operational fire management decisions?**  
A: Not recommended in current form. This is a proof-of-concept. For operational use, conduct field validation and sensitivity analysis first.

**Q: What's the minimum AOI size for meaningful results?**  
A: At least 1 km² (100 hectares). Smaller areas may have resolution/statistics issues.

**Q: Can I use Landsat instead of Sentinel-2?**  
A: Yes, modify `config.py` to use `USGS/LANDSAT/LC09/C02/T1_L2`. Adjust spectral bands and thresholds accordingly.

**Q: How far back can I analyze historical fires?**  
A: Sentinel-2 data available since June 2015. Landsat back to 2013 (via Earth Engine).

**Q: What countries/regions work best?**  
A: Mediterranean climate zones, boreal forests, tropical savannas. Tested on southern Europe. Validation needed for other regions.

**Q: Is this cloud-based or desktop-based?**  
A: Hybrid. Data processing occurs on Google Earth Engine cloud servers; visualization and export on local machine.

**Q: Do I need to pay to use this?**  
A: Google Earth Engine free tier includes $300 annual cloud credits. Typical analysis costs <$1. No payment required unless exceeding credits.

**Q: Can I parallelize analysis for multiple fires?**  
A: Not yet built-in. Requires custom scripting to loop through multiple AOIs.

**Q: What's the positional accuracy of burn boundaries?**  
A: ±1–2 Sentinel-2 pixels (~20–40 m) depending on fire edge sharpness and timing.

---

## Disclaimer and Acknowledgments

### Disclaimer

This software is provided **"as is"** without warranty of any kind, express or implied. The authors and contributors are **not responsible** for any losses, damages, or inaccuracies resulting from use of this software. 

**This is a proof-of-concept tool and should NOT be used for:**
- Operational fire response decisions
- Legal/regulatory fire damage assessments
- Insurance claim determinations
- Precise burn severity classifications without field validation

**Appropriate uses include:**
- Research and academic study
- Educational demonstrations
- Rapid situational awareness (not definitive)
- Proof-of-concept methodology testing
- Training and capacity building

### Acknowledgments

- **Google Earth Engine team** for cloud geospatial processing infrastructure
- **ESA Copernicus program** for free Sentinel-2 satellite imagery
- **geemap developers** for interactive mapping library
- **USDA Forest Service** for NBR standardization and burn classification methodology

### Dataset Attribution

Sentinel-2 data © European Union/ESA (2023), distributed through Google Earth Engine.

---

## License and Citation

### License

This project is released under the **MIT License**. See LICENSE file for full text.

Simplified terms:
- ✓ Use for research, education, commercial purposes
- ✓ Modify and adapt code
- ✓ Distribute modified versions
- ✗ Provides no warranty
- ✗ Authors not liable for damages

### Citation

If you use this project in research or publication, please cite:

```bibtex
@software{dnbr_burn_analysis_2026,
  title = {Automated Wildfire Burned Area Delineation using Open Data and Google Earth Engine},
  author = {[Your Name/Affiliation]},
  year = {2026},
  url = {https://github.com/yourusername/dnbr-burn-analysis},
  version = {1.0.0},
  note = {Proof-of-concept case study methodology}
}
```

---

## Contact and Support

**For issues, bug reports, or feature requests:**

1. **Check existing issues** in repository
2. **Search troubleshooting section** above
3. **Create detailed issue report** including:
   - Error message (full traceback)
   - Python version & OS
   - Configuration parameters (sanitized)
   - Steps to reproduce

**For scientific questions about methodology:**
- Review technical references section
- Consult NASA FIRMS / USDA Forest Service burn analysis documentation
- Contact USGS Earth Resources Observation and Science Center

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0.0 | Feb 2026 | Release | Initial proof-of-concept; single case study (Catalonia, Spain) |
| 0.9.0 | Jan 2026 | Beta | Internal testing; 4-stage analysis framework finalized |
| 0.8.0 | Dec 2025 | Alpha | Core algorithms and pipeline development |

---

## Quick Links

- 📚 [Google Earth Engine Documentation](https://developers.google.com/earth-engine)
- 🗺️ [geemap Interactive Mapping Tutorial](https://geemap.org/)
- 🛰️ [Sentinel-2 Mission Info](https://sentinel.esa.int/web/sentinel/missions/sentinel-2)
- 🔥 [USDA Forest Service Burn Analysis](https://www.fs.fed.us/ccrc/topics/fire/monitoring)
- 📡 [NASA FIRMS Fire Detection](https://firms.modaps.eosdis.nasa.gov/)

---

**Last Updated:** February 23, 2026  
**Project Status:** Maintenance (proof-of-concept)  
**Recommended Citation:** "Experimental methodology—for research and validation only"

---

**🔬 Research-Grade Implementation**  
*Demonstrating automated burn area delineation from free and open data sources*

Edit these values to customize your analysis.

## Usage

### Basic Execution

```bash
cd dnbr_project
python main.py
```

### Output

The script generates:
1. **4 Interactive HTML Maps** in `output/`
   - Map for each analysis stage with all layers
   - Pre-fire RGB, post-fire RGB, dNBR, severity classification, burned areas
   - Color-coded fire polygons with bounding boxes

2. **CSV Summary** (`output/analysis_summary.csv`)
   - Analysis name, AOI type, analysis type, water masking status
   - AOI area, Otsu threshold, burned area, map file, timestamp

3. **Console Output** with metrics for each analysis:
   - Original AOI area and burned area
   - Bounding box calculations
   - Comparison between masked and unmasked analyses

### Expected Runtime

- 10-15 minutes for complete 4-stage analysis
- Processing executed on Google Earth Engine cloud servers
- Output size: ~1–3 MB per analysis run

---

**Created:** February 2026  
**Version:** 1.0.0 (Proof of Concept)  
**Status:** Experimental – Single case study validation only
