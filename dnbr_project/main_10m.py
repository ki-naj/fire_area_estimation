import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
import ee
import numpy as np
import matplotlib.pyplot as plt
from src.dnbr.earth_engine_utils import resample_image_to_10m

sys.path.insert(0, str(Path(__file__).parent) )  #<-- Ensure project root is in sys.path

from config.config import *
from src.dnbr import *


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)    #<-- Get module-specific logger

OUTPUT_DIR = "output"

# mamy potrzebne parametry z configu i funkcja jeśli nie wykryje ich z globalnej przestrzeni projektu wrzuci je do missing
# jeśli cokolwiek będzie w missing_params to logger wywoła error jeśli nie to walidacja przeszła pomyślnie
def validate_config() -> bool:
    required_params = [
        'EE_PROJECT_ID', 'AOI_COORDS', 'SENTINEL2_COLLECTION',
        'PRE_FIRE_DATE_START', 'PRE_FIRE_DATE_END',
        'POST_FIRE_DATE_START', 'POST_FIRE_DATE_END',
        'SCALE_10M', 'MAX_PIXELS', 'SEVERITY_THRESHOLDS',
        'RESAMPLING_METHOD'
    ]
    
    missing_params = []
    for param in required_params:
        if param not in globals():
            missing_params.append(param)
    
    if missing_params:
        logger.error(f"Missing required config parameters: {', '.join(missing_params)}")
        return False
    
    logger.info("Configuration validated")
    return True


# funkcja ma zwrócić słownik gdzie klucze są stringami a wartości mogą być dowolnego typu
def run_fire_detection_analysis(
    aoi: ee.Geometry,
    pre_image: ee.Image,
    post_image: ee.Image,
    aoi_name: str = "AOI",
    analysis_type: str = "basic",
    water_mask: Optional[ee.Image] = None,
    zoom: int = 14,
    output_suffix: str = ""
) -> Dict[str, Any]:
    
    aoi_area = calculate_aoi_area(aoi)              #float
    logger.info(f"Full area: {aoi_area:.4f} ha")    #.4f - 4 miejsca po przecinku
    
    # Oblicz NBR dla oryginalnych obrazów (przed resamplingiem)
    pre_nbr = calc_nbr(pre_image)
    post_nbr = calc_nbr(post_image)
    dnbr = calc_dnbr(pre_nbr, post_nbr)
    
    # Resampling do 10m
    logger.info(f"Resampling imagery to {SCALE_10M}m using {RESAMPLING_METHOD} neighbor method...")
    pre_nbr = resample_image_to_10m(pre_nbr, RESAMPLING_METHOD)
    post_nbr = resample_image_to_10m(post_nbr, RESAMPLING_METHOD)
    dnbr = resample_image_to_10m(dnbr, RESAMPLING_METHOD)
    logger.info(f"Resampling complete")
    
    if water_mask is not None:
        logger.info("Applying water mask to images...")
        # Resample water mask do 10m
        water_mask = resample_image_to_10m(water_mask, RESAMPLING_METHOD)
        land_mask = water_mask.eq(0)  # 0 = ląd, 1 = woda
        pre_image_masked = pre_image.updateMask(land_mask)
        post_image_masked = post_image.updateMask(land_mask)

        pre_nbr = pre_nbr.updateMask(land_mask)
        post_nbr = post_nbr.updateMask(land_mask)
        dnbr = dnbr.updateMask(land_mask)  #<-- liczenie nbr dla obszaru bez wody
        
        # Oblicz powierzchnię lądu
        land_area_img = land_mask.multiply(ee.Image.pixelArea()).rename("area")
        land_area_stats = land_area_img.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=aoi,
            scale=SCALE_10M,
            maxPixels=MAX_PIXELS
        )
        aoi_area = ee.Number(land_area_stats.get("area")).divide(10000).getInfo()
        logger.info(f"Land area (after water removal): {aoi_area:.4f} ha")
    else:
        # Bez maski wody - normalnie
        pre_image_masked = pre_image
        post_image_masked = post_image

    logger.info(f"Spectral indices calculated")
    
    # Klasyfikacja progowanie
    logger.info("Severity thresholds:")
    threshold_areas = {}
    for severity, threshold in SEVERITY_THRESHOLDS.items():
        mask, area_ha = classify_by_threshold(dnbr, threshold, aoi, SCALE_10M, MAX_PIXELS)
        threshold_areas[severity] = area_ha
        logger.info(f"  {severity} (dNBR > {threshold}): {area_ha:.4f} ha")
    

    # Obliczamy Otsu
    hist_dnbr = get_histogram(dnbr, aoi, "dNBR", SCALE_10M, MAX_PIXELS)
    otsu_th = otsu_threshold(hist_dnbr["histogram"], hist_dnbr["bucketMeans"])
    logger.info(f"Otsu threshold: {otsu_th:.4f}")
    otsu_mask, otsu_area = classify_by_threshold(dnbr, otsu_th, aoi, SCALE_10M, MAX_PIXELS)
    logger.info(f"Otsu threshold area: {otsu_area:.4f} ha")
    

    # Rozszerzanie maski pożaru
    seed_mask = create_seed_mask(dnbr, otsu_th)
    fire_mask = seed_mask
    for th in FIRE_GROWTH_THRESHOLDS:
        fire_mask = grow_fire_mask(
            seed_mask=fire_mask,
            dnbr=dnbr,
            threshold=th,
            aoi=aoi,
            scale=SCALE_10M,
            min_area_ha=MIN_AREA_HA,
            max_pixels=MAX_PIXELS
        )
    
    fire_vectors_final = vectorize_mask(fire_mask, aoi, SCALE_10M, MAX_PIXELS)
    fire_vectors_final = filter_by_area(fire_vectors_final, MIN_AREA_HA)
    total_area = calculate_total_area(fire_vectors_final)
    logger.info(f"Burned area: {total_area:.4f} ha")
    fire_geom = fire_vectors_final.geometry()
    fire_bbox = create_bounding_box(fire_geom, buffer_distance=BUFFER_DISTANCE)
    
    # koniec analiz teraz tworzymy mapę

    m = create_comprehensive_map(
        aoi=aoi,
        pre_image=pre_image_masked,
        post_image=post_image_masked,
        dnbr=dnbr,
        burned_mask=otsu_mask,
        fire_vectors=fire_vectors_final,
        severity_thresholds=THRESHOLD_COLORS,
        zoom=zoom,
        fire_bbox=fire_bbox
    )
    logger.info(f"Map created for {aoi_name}")
    
    # Save map
    output_dir = Path(__file__).parent / OUTPUT_DIR
    output_dir.mkdir(exist_ok=True)
    
    map_file = output_dir / f"burn_area_map{output_suffix}.html"
    save_map(m, str(map_file))
    
   
    return {
        "aoi": aoi,
        "aoi_area": aoi_area,
        "aoi_name": aoi_name,
        "analysis_type": analysis_type,
        "pre_image": pre_image_masked,
        "post_image": post_image_masked,
        "pre_nbr": pre_nbr,
        "post_nbr": post_nbr,
        "dnbr": dnbr,
        "fire_mask": fire_mask,
        "fire_vectors": fire_vectors_final,
        "fire_bbox": fire_bbox,
        "otsu_threshold": otsu_th,
        "otsu_area": otsu_area,
        "threshold_areas": threshold_areas,
        "total_area": total_area,
        "map": m,
        "map_file": map_file,
        "water_mask": water_mask,
        "water_masked": water_mask is not None,
        "resolution": f"{SCALE_10M}m",
        "resampling_method": RESAMPLING_METHOD
    }


def main() -> Optional[Dict[str, Any]]:
    try:
        if not validate_config():
            logger.error("Configuration validation failed")
            return None
        
        logger.info("dNBR BURN AREA ANALYSIS - 10M RESOLUTION - FOUR-STAGE COMPARISON")
        logger.info(f"Resampling Method: {RESAMPLING_METHOD.upper()} NEIGHBOR")
        
        logger.info("Initializing Earth Engine...")     #<-- Initialize Earth Engine
        ee.Initialize(project=EE_PROJECT_ID)

        logger.info("SETUP: IMAGERY & INDICES (10M RESOLUTION)")
        aoi_original = get_aoi_geometry(AOI_COORDS)
        aoi_area_original = calculate_aoi_area(aoi_original)
        logger.info(f"Original AOI: {aoi_area_original:.4f} ha")  #<-- oryginalna powierzchnia
    
        pre_collection = get_image_collection(
            SENTINEL2_COLLECTION, aoi_original,
            PRE_FIRE_DATE_START, PRE_FIRE_DATE_END
        )   #<-- podaje aoi original a nie jako obliczona area
        post_collection = get_image_collection(
            SENTINEL2_COLLECTION, aoi_original,
            POST_FIRE_DATE_START, POST_FIRE_DATE_END
        )
        logger.info(f"Collections fetched\n")
        inspect_collection(pre_collection, "PRE-FIRE")
        inspect_collection(post_collection, "POST-FIRE")
        
        # otrzymujemy przycięte do oryginalnego obszaru zdj w postaci IMAGE
        pre_image = get_specific_image(pre_collection, PRE_IMAGE_ID, aoi_original)
        post_image = get_specific_image(post_collection, POST_IMAGE_ID, aoi_original)
        logger.info(f"Image chosen\n")
        describe_image(pre_image, "PRE-IMAGE")
        describe_image(post_image, "POST-IMAGE")
        
    #=== tu się kończy przygotowanie obrazów ===
    #=== mamy aoi_original, pre_image, post_image === plus kolekcje i powierzchnie oryginalnego aoi
        
        # tworzymy water mask z całego obszaru oryginalnego aoi
        logger.info("Creating water mask for analyses 3 and 4...")
        pre_ndwi = calc_ndwi(pre_image.toFloat())
        post_ndwi = calc_ndwi(post_image.toFloat()) #<-- for water mask
        water_mask_original = create_combined_water_mask(pre_ndwi, post_ndwi, threshold=NDWI_THRESHOLD)
        logger.info(f"Water mask created\n")

        #1

        logger.info("ANALYSIS 1/4: ORIGINAL AOI - BASIC (10M)")
        results_1 = run_fire_detection_analysis(
            aoi=aoi_original,
            pre_image=pre_image, 
            post_image=post_image,
            aoi_name="Original AOI - Basic (10m)",
            analysis_type="basic",
            water_mask=None,
            zoom=14,
            output_suffix="_05_10m_original_basic"
        )
        logger.info(f"ANALYSIS 1/4: Complete\n")
        
        #2

        logger.info("ANALYSIS 2/4: BOUNDING BOX - BASIC (10M)")
        aoi_bbox = results_1["fire_bbox"]
        pre_image_2 = get_specific_image(pre_collection, PRE_IMAGE_ID, aoi_bbox)
        post_image_2 = get_specific_image(post_collection, POST_IMAGE_ID, aoi_bbox)

        results_2 = run_fire_detection_analysis(
            aoi=aoi_bbox,
            pre_image=pre_image_2,
            post_image=post_image_2,
            aoi_name="Bounding Box - Basic (10m)",
            analysis_type="basic",
            water_mask=None,
            zoom=14,
            output_suffix="_06_10m_bbox_basic"
        )
        logger.info(f"ANALYSIS 2/4: Complete\n")
        

        #3

        logger.info("ANALYSIS 3/4: ORIGINAL AOI - WATER MASKED (10M)")
        results_3 = run_fire_detection_analysis(
            aoi=aoi_original,
            pre_image=pre_image,
            post_image=post_image,
            aoi_name="Original AOI - Water Masked (10m)",
            analysis_type="water_masked",
            water_mask=water_mask_original,
            zoom=14,
            output_suffix="_07_10m_original_water"
        )
        logger.info(f"ANALYSIS 3/4: Complete\n")
        
        #4

        logger.info("ANALYSIS 4/4: BOUNDING BOX - WATER MASKED (10M)")
        aoi_bbox_water = results_3["fire_bbox"]
        pre_image_4 = get_specific_image(pre_collection, PRE_IMAGE_ID, aoi_bbox_water)
        post_image_4 = get_specific_image(post_collection, POST_IMAGE_ID, aoi_bbox_water)
        water_mask_bbox = water_mask_original.clip(aoi_bbox_water)
        results_4 = run_fire_detection_analysis(
            aoi=aoi_bbox_water,
            pre_image=pre_image_4,
            post_image=post_image_4,
            aoi_name="Bounding Box - Water Masked (10m)",
            analysis_type="water_masked",
            water_mask=water_mask_bbox,
            zoom=14,
            output_suffix="_08_10m_bbox_water"
        )
        logger.info(f"ANALYSIS 4/4: Complete\n")

        




        analyses_dict = {
            "analysis_1": results_1,
            "analysis_2": results_2,
            "analysis_3": results_3,
            "analysis_4": results_4
        }
        
        output_dir = Path(__file__).parent / OUTPUT_DIR
        csv_file = export_analysis_to_csv_10m(analyses_dict, output_dir)
        






        # ===================================================================
        # EKSPORT WARSTW DO PLIKÓW GeoTIFF i Shapefile
        # ===================================================================
        
        logger.info("EXPORTING LAYERS TO FILES")
        
        export_dir = output_dir / "exports"
        
        # Eksport dla Analysis 4
        logger.info(" Exporting Analysis 4: Bounding Box - Water Masked")
        export_all_analysis_layers(
            results_4,
            output_dir=str(export_dir),
            scale=SCALE_10M,
            analysis_suffix="_08"
        )
        
        logger.info("ALL LAYERS EXPORTED SUCCESSFULLY\n")
        
        # ===================================================================
        # TWORZENIE HISTOGRAMÓW
        # ===================================================================
        
        logger.info("CREATING HISTOGRAMS")

        histograms_dir = output_dir / "histograms"
        histograms_dir.mkdir(exist_ok=True)
        
        # Lista analiz z sufiksami
        analyses_list = [
            (results_1, "_05_original_basic"),
            (results_2, "_06_bbox_basic"),
            (results_3, "_07_original_water"),
            (results_4, "_08_bbox_water")
        ]
        
        # Tworzenie histogramu dla każdej analizy
        for i, (results, suffix) in enumerate(analyses_list, 1):
            logger.info(f"\n[{i}/4] Creating histogram for {results['aoi_name']}...")
            
            # Pobierz histogram data z Earth Engine
            hist_data = get_histogram(
                results["dnbr"],
                results["aoi"],
                "dNBR",
                SCALE,
                MAX_PIXELS
            )
            
            # Åšcieżka zapisu
            save_path = histograms_dir / f"histogram{suffix}.png"
            
            # UtwÃ³rz histogram
            fig = plot_dnbr_histogram_with_thresholds(
                hist_data,
                results["otsu_threshold"],
                SEVERITY_THRESHOLDS,
                aoi_name=results["aoi_name"],
                save_path=str(save_path)
            )
        logger.info("ALL HISTOGRAMS CREATED SUCCESSFULLY\n")



        logger.info(f"10m Analysis Maps saved to: {output_dir}")
        logger.info(f"  - 4 interactive HTML maps (10m resolution)")
        logger.info(f"  - 1 separate CSV summary file (10m)")
        logger.info(f"  - Resampling method: {RESAMPLING_METHOD.upper()} NEIGHBOR")
        logger.info(f"  - x files")
        
        return {
            "analysis_1": results_1,
            "analysis_2": results_2,
            "analysis_3": results_3,
            "analysis_4": results_4
        }
        
    except ee.EEException as e:
        logger.error(f"Earth Engine error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Analysis failed with unexpected error: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fire burn area detection using dNBR analysis and Otsu thresholding at 10m resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python main_10m.py
  python main_10m.py --verbose
  python main_10m.py --output output_10m
        """
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom configuration file (optional)",
        default=None
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for results (default: output)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    args = parser.parse_args()
    
    # Adjust logging level if verbose flag is set
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    results = main()
    sys.exit(0 if results is not None else 1)