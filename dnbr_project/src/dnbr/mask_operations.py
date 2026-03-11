import ee

def create_combined_water_mask(pre_ndwi: ee.Image, post_ndwi: ee.Image, threshold: float = 0.0) -> ee.Image:
    water_pre = pre_ndwi.gt(threshold)
    water_post = post_ndwi.gt(threshold)
    return water_pre.Or(water_post)
