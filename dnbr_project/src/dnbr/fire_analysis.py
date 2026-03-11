import ee
from typing import Tuple

#klasyfikuje i liczy powierzchnie
def classify_by_threshold(
    dnbr: ee.Image,
    threshold: float,
    aoi: ee.Geometry,
    scale: int = 20,
    max_pixels: float = 1e9
) -> Tuple[ee.Image, float]:
    
    mask = dnbr.gt(threshold).selfMask()
    area_img = mask.multiply(ee.Image.pixelArea()).rename("area")
    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=aoi,
        scale=scale,
        maxPixels=max_pixels
    )
    area_ha = ee.Number(stats.get("area")).divide(10000).getInfo()
    return mask, area_ha


def create_seed_mask(dnbr: ee.Image, threshold: float) -> ee.Image:
    return dnbr.gt(ee.Number(threshold)).selfMask()


def vectorize_mask(
    mask: ee.Image,
    aoi: ee.Geometry,
    scale: int = 20,
    max_pixels: float = 1e9
) -> ee.FeatureCollection:
    vectors = mask.reduceToVectors(
        geometry=aoi,
        scale=scale,
        geometryType="polygon",
        eightConnected=True,
        labelProperty="burned",
        maxPixels=max_pixels
    )
    vectors = vectors.map(
        lambda f: f.set('area_ha', f.geometry().area(1).divide(10000))
    )
    return vectors


def filter_by_area(features: ee.FeatureCollection, min_area_ha: float) -> ee.FeatureCollection:
    return features.filter(ee.Filter.gt('area_ha', min_area_ha))


def grow_fire_mask(
    seed_mask: ee.Image,
    dnbr: ee.Image,
    threshold: float,
    aoi: ee.Geometry,
    scale: int = 20,
    min_area_ha: float = 0.5,
    max_pixels: float = 1e9
) -> ee.Image:
    candidate_mask = dnbr.gt(threshold).selfMask()
    vectors = candidate_mask.reduceToVectors(
        geometry=aoi,
        scale=scale,
        geometryType="polygon",
        eightConnected=True,
        labelProperty="burned",
        maxPixels=max_pixels
    )
    # vectors = vectors.map(
    #     lambda f: f.set('area_ha', f.geometry().area(1).divide(10000))
    # )
    
    seed_geom = seed_mask.geometry()
    good_vectors = vectors.filter(
        ee.Filter.Or(
            ee.Filter.intersects(leftField='.geo', rightValue=seed_geom),
        #     ee.Filter.gt('area_ha', min_area_ha)
         )
    )
    
    grown_mask = ee.Image().byte().paint(good_vectors, 1).selfMask()
    new_seed = seed_mask.unmask(0).Or(grown_mask).selfMask()
    return new_seed


def calculate_total_area(features: ee.FeatureCollection) -> float:
    return features.aggregate_sum('area_ha').getInfo()


def create_bounding_box(fire_geom: ee.Geometry, buffer_distance: int = 20) -> ee.Geometry:
    buffered = fire_geom.buffer(buffer_distance)
    return buffered.bounds(1)
