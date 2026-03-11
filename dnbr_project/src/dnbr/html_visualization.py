import ee
import geemap
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Optional, Tuple, List


def create_map(
    aoi: ee.Geometry,
    height: int = 700,
    zoom: int = 14
) -> geemap.Map:
    m = geemap.Map(data_ctrl=False, draw_ctrl=False, height=height)
    m.centerObject(aoi, zoom=zoom)
    return m


def add_aoi_boundary(
    m: geemap.Map,
    aoi: ee.Geometry,
    label: str = "AOI boundary"
) -> geemap.Map:
    aoi_layer = ee.Image().byte().paint(
        featureCollection=ee.FeatureCollection([ee.Feature(aoi)]),
        color=1,
        width=2
    )
    m.addLayer(aoi_layer, {"palette": ["red"]}, label)
    return m


def add_rgb_image(
    m: geemap.Map,
    image: ee.Image,
    label: str = "Sentinel-2 RGB"
) -> geemap.Map:
    rgb = image.select(["B4", "B3", "B2"])
    rgb_params = {"min": 0, "max": 3000}
    m.addLayer(rgb, rgb_params, label)
    return m


def add_nbr_layer(
    m: geemap.Map,
    image: ee.Image,
    label: str = "NBR"
) -> geemap.Map:
    nbr = image.normalizedDifference(["B8", "B12"]).rename("NBR")
    nbr_params = {"min": -1, "max": 1, "palette": ["white", "black", "red"]}
    m.addLayer(nbr, nbr_params, label)
    return m


def add_dnbr_layer(
    m: geemap.Map,
    dnbr: ee.Image,
    label: str = "dNBR"
) -> geemap.Map:
    dnbr_params = {"min": -0.5, "max": 0.8, "palette": ["green", "yellow", "red"]}
    m.addLayer(dnbr, dnbr_params, label)
    return m


def add_severity_masks(
    m: geemap.Map,
    dnbr: ee.Image,
    thresholds: Dict[float, str],
    aoi: ee.Geometry
) -> geemap.Map:
    palette_list = list(thresholds.values())
    legend_labels = []
    
    for threshold, color in thresholds.items():
        mask = dnbr.gt(threshold).selfMask()
        m.addLayer(mask, {"palette": [color]}, f"dNBR > {threshold}")
        legend_labels.append(f"dNBR > {threshold}")
    
    m.add_legend(
        legend_title="Burn Severity",
        keys=legend_labels,
        colors=palette_list
    )
    
    return m


def add_burned_area_mask(
    m: geemap.Map,
    burned_mask: ee.Image,
    color: str = "purple",
    label: str = "Burned Area (Otsu)"
) -> geemap.Map:
    m.addLayer(burned_mask, {"palette": [color]}, label)
    return m


def add_fire_polygons(
    m: geemap.Map,
    fire_vectors: ee.FeatureCollection,
    label: str = "Fire Polygons"
) -> geemap.Map:
    m.addLayer(fire_vectors, {}, label)
    return m


def add_bounding_box(
    m: geemap.Map,
    bbox: ee.Geometry,
    label: str = "Fire Bounding Box",
    color: str = "orange"
) -> geemap.Map:
    bbox_layer = ee.Image().byte().paint(
        ee.FeatureCollection([ee.Feature(bbox)]),
        color=1,
        width=2
    )
    m.addLayer(bbox_layer, {"palette": [color]}, label)
    return m


#---------------------------------


def create_comprehensive_map(
    aoi: ee.Geometry,
    pre_image: ee.Image,
    post_image: ee.Image,
    dnbr: ee.Image,
    burned_mask: ee.Image,
    fire_vectors: ee.FeatureCollection,
    severity_thresholds: Dict[float, str],
    zoom: int = 14,
    fire_bbox: Optional[ee.Geometry] = None
) -> geemap.Map:
    m = create_map(aoi, zoom=zoom)
    
    # Add base layers
    m = add_aoi_boundary(m, aoi, "AOI Boundary")
    m = add_rgb_image(m, post_image, "Sentinel-2 RGB (Post-Fire)")
    
    # Add spectral indices
    m = add_dnbr_layer(m, dnbr, "dNBR Index")
    
    # Add severity classification
    m = add_severity_masks(m, dnbr, severity_thresholds, aoi)
    
    # Add final results
    m = add_burned_area_mask(m, burned_mask, "purple", "Burned Area (Otsu)")
    m = add_fire_polygons(m, fire_vectors, "Fire Polygons")
    
    # Add bounding box if provided
    if fire_bbox is not None:
        m = add_bounding_box(m, fire_bbox, "Fire Bounding Box", "orange")
    
    m.centerObject(aoi, zoom=zoom)
    
    return m

def save_map(
    m: geemap.Map,
    filepath: str
) -> None:
    """Save geemap as standalone Leaflet HTML map for full interactivity."""
    m.to_html(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    fix_script = '''
<script>
// Ensure Leaflet map functionality is preserved
document.addEventListener('DOMContentLoaded', function() {
    // Give widgets time to initialize
    setTimeout(function() {
        // Verify map container exists and is properly configured
        var mapContainer = document.querySelector('[id*="map"]');
        if (mapContainer) {
            console.log('Map container found and initialized');
        }
    }, 500);
});

// Prevent widget communication errors from breaking interactivity
if (typeof window.requirejs !== 'undefined') {
    requirejs.onError = function(err) {
        console.warn('RequireJS error (non-fatal):', err);
    };
}
</script>
'''
    
    closing_body_idx = html_content.rfind('</body>')
    if closing_body_idx != -1:
        html_content = html_content[:closing_body_idx] + fix_script + html_content[closing_body_idx:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"[SAVED] Map saved to {filepath}")
