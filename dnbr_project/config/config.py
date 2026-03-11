#------------------------------------------------
# Earth Engine Config
EE_PROJECT_ID = "projek3-477107"

# Analysis Area of Interest (AOI) - Rectangle [west, south, east, north]
AOI_COORDS = [3.09, 42.398, 3.19, 42.435]

# Date Range Configuration
PRE_FIRE_DATE_START = "2023-07-30"
PRE_FIRE_DATE_END = "2023-08-01"
POST_FIRE_DATE_START = "2023-08-02"                 #<--w przypadku zmiany zmień to
POST_FIRE_DATE_END = "2023-08-06"

# Specific Image IDs (for reproducibility)
PRE_IMAGE_ID = "20230731T103631_20230731T104041_T31TEG"                 #<--w przypadku zmiany zmień to
POST_IMAGE_ID = "20230805T103629_20230805T103641_T31TEG"                #<--w przypadku zmiany zmień to

SENTINEL2_COLLECTION = "COPERNICUS/S2_SR"
#------------------------------------------------

# Analysis Parameters
NDWI_THRESHOLD = 0.0
SCALE = 20
MAX_PIXELS = 1e9

# 10m Resampled Analysis Parameters
SCALE_10M = 10
RESAMPLING_METHOD = "nearest"  # nearest, bilinear, or bicubic

#------------------------------------------------

# Burn Severity Thresholds (for classification)
SEVERITY_THRESHOLDS = {
    "low": 0.05,
    "moderate_low": 0.075,
    "moderate": 0.1,
    "high": 0.2,
    "very_high": 0.3
}

THRESHOLD_COLORS = {
    0.05: "#0000FF",
    0.075: "#FF0000",
    0.1: "#FFA500",
    0.2: "#FFFF00",
    0.3: "#000000"
}

MIN_AREA_HA = 0.5  # Minimum polygon area in hectares

# Fire Mask Growth Parameters
FIRE_GROWTH_THRESHOLDS = [0.10, 0.075, 0.05]  # Progressive thresholds
BUFFER_DISTANCE = 20  # meters

# Output Configuration
SAVE_OUTPUTS = True
OUTPUT_DIR = "outputs"
