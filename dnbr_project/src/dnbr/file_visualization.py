import ee
import geemap
import matplotlib.pyplot as plt
from typing import Dict, Optional, Tuple
from pathlib import Path

def export_image_to_geotiff(
    image: ee.Image,
    aoi: ee.Geometry,
    filepath: str,
    scale: int = 10
) -> None:
    try:
        geemap.ee_export_image(
            image.clip(aoi),
            filename=filepath,
            scale=scale,
            region=aoi,
            file_per_band=False
        )
        print(f"[SAVED] {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to export {filepath}: {e}")


def export_vectors_to_shapefile(
    features: ee.FeatureCollection,
    filepath: str
) -> None:
    try:
        geemap.ee_export_vector(
            features,
            filename=filepath
        )
        print(f"[SAVED] {filepath}")
    except Exception as e:
        print(f"[ERROR] Failed to export {filepath}: {e}")


def export_all_analysis_layers(
    results: Dict,
    output_dir: str = "exports",
    scale: int = 10,
    analysis_suffix: str = ""
) -> None:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    aoi = results["aoi"]
    
    print(f"\n[EXPORT] Starting export for {results['aoi_name']}...")
    
    # # 1. Export Pre-fire RGB
    # print("[EXPORT] Exporting pre-fire RGB...")
    # pre_rgb = results["pre_image"].select(['B4', 'B3', 'B2'])
    # export_image_to_geotiff(
    #     pre_rgb,
    #     aoi,
    #     f"{output_dir}/pre_fire_rgb{analysis_suffix}.tif",
    #     scale
    # )
    
    # 2. Export Post-fire RGB
    print("[EXPORT] Exporting post-fire RGB...")
    post_rgb = results["post_image"].select(['B4', 'B3', 'B2'])
    export_image_to_geotiff(
        post_rgb,
        aoi,
        f"{output_dir}/post_fire_RGB{analysis_suffix}.tif",
        scale
    )
    
    # # 3. Export Pre-fire NBR
    # print("[EXPORT] Exporting pre-fire NBR...")
    # export_image_to_geotiff(
    #     results["pre_nbr"],
    #     aoi,
    #     f"{output_dir}/pre_fire_nbr{analysis_suffix}.tif",
    #     scale
    # )
    
    # # 4. Export Post-fire NBR
    # print("[EXPORT] Exporting post-fire NBR...")
    # export_image_to_geotiff(
    #     results["post_nbr"],
    #     aoi,
    #     f"{output_dir}/post_fire_nbr{analysis_suffix}.tif",
    #     scale
    # )
    
    # 5. Export dNBR
    print("[EXPORT] Exporting dNBR...")
    export_image_to_geotiff(
        results["dnbr"],
        aoi,
        f"{output_dir}/dNBR{analysis_suffix}.tif",
        scale
    )
    
    # 6. Export Burned Area Mask
    print("[EXPORT] Exporting burned area mask...")
    export_image_to_geotiff(
        results["fire_mask"],
        aoi,
        f"{output_dir}/burned_area_mask{analysis_suffix}.tif",
        scale
    )
    
    # 7. Export Fire Polygons
    print("[EXPORT] Exporting fire polygons...")
    export_vectors_to_shapefile(
        results["fire_vectors"],
        f"{output_dir}/fire_polygons{analysis_suffix}.shp"
    )
    
    # 8. Export AOI Boundary
    print("[EXPORT] Exporting AOI boundary...")
    aoi_feature = ee.FeatureCollection([ee.Feature(aoi)])
    export_vectors_to_shapefile(
        aoi_feature,
        f"{output_dir}/aoi_boundary{analysis_suffix}.shp"
    )
    
    # # 9. Export Bounding Box (jeśli istnieje)
    # if results.get("fire_bbox") is not None:
    #     print("[EXPORT] Exporting fire bounding box...")
    #     bbox_feature = ee.FeatureCollection([ee.Feature(results["fire_bbox"])])
    #     export_vectors_to_shapefile(
    #         bbox_feature,
    #         f"{output_dir}/fire_bbox{analysis_suffix}.shp"
    #     )

    # 10 . Export Water Mask (jeśli istnieje)
    if results.get("water_mask") is not None:
        print("[EXPORT] Exporting water mask...")
        try:
            water_vectors = results["water_mask"].selfMask().reduceToVectors(
                geometry=aoi,
                scale=scale,
                geometryType='polygon',
                eightConnected=False,
                maxPixels=1e9
            )
            export_vectors_to_shapefile(
                water_vectors,
                f"{output_dir}/water_mask_polygons{analysis_suffix}.shp"
        )
        except Exception as e:
            print(f"[SUCCESS] All layers exported to {output_dir}/\n")


#=============================================================================
# HISTOGRAM PLOTTING
#=============================================================================

def plot_dnbr_histogram_with_thresholds(
    hist_data: Dict,
    otsu_threshold: float,
    severity_thresholds: Dict[str, float],
    aoi_name: str = "AOI",
    figsize: Tuple[int, int] = (14, 5),
    save_path: Optional[str] = None
) -> plt.Figure:

    histogram = hist_data["histogram"]
    bucket_means = hist_data["bucketMeans"]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot histogram
    ax.bar(bucket_means, histogram, width=(bucket_means[1] - bucket_means[0]) * 0.9,
           color='steelblue', alpha=0.7, edgecolor='black', label='dNBR Distribution')
    
    # Add Otsu threshold line
    ax.axvline(otsu_threshold, color='red', linestyle='--', linewidth=2.5,
               label=f'Otsu Threshold: {otsu_threshold:.4f}', alpha=0.9, zorder=5)
    
    # Define colors for severity thresholds
    severity_colors = {
        'low': '#0000FF',          # Blue
        'moderate_low': '#FF0000', # Red
        'moderate': '#FFA500',     # Orange
        'high': '#FFFF00',         # Yellow
        'very_high': '#000000'     # Black
    }
    
    # Add severity threshold lines
    for severity, threshold in sorted(severity_thresholds.items(), key=lambda x: x[1]):
        color = severity_colors.get(severity, 'gray')
        label = severity.replace('_', '-').title()
        ax.axvline(threshold, color=color, linestyle=':', linewidth=1.5, 
                   label=f'{label}: {threshold:.4f}', alpha=0.8, zorder=4)
    
    ax.set_xlabel('dNBR Value', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title(f'dNBR Histogram with Thresholds - {aoi_name}', 
                 fontsize=13, fontweight='bold', pad=15)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[SAVED] Histogram saved to {save_path}")
    
    return fig
