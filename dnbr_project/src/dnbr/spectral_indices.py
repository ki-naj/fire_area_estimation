import ee
import numpy as np
from config import *

def calc_ndwi(image: ee.Image) -> ee.Image:
    return image.normalizedDifference(["B3", "B8"]).rename("NDWI")

def calc_nbr(image: ee.Image) -> ee.Image:
    return image.normalizedDifference(["B8", "B12"]).rename("NBR")

def calc_dnbr(pre_nbr: ee.Image, post_nbr: ee.Image) -> ee.Image:
    return pre_nbr.subtract(post_nbr).rename("dNBR")

def get_histogram(
    image: ee.Image,
    aoi: ee.Geometry,
    band: str = "dNBR",
    scale: int = 20,
    max_pixels: float = 1e9
) -> dict:
    hist = image.reduceRegion(
        reducer=ee.Reducer.histogram(maxBuckets=256),
        geometry=aoi,
        scale=scale,
        maxPixels=max_pixels
    ).get(band).getInfo()
    
    return hist

def otsu_threshold(counts: list, bins: list) -> float:
    counts = np.array(counts)
    bins = np.array(bins)
    total = counts.sum()
    sum_total = (bins * counts).sum()
    sumB = 0
    wB = 0
    maximum = 0.0
    threshold = bins[0]
    
    for i in range(len(bins)):
        wB += counts[i]
        if wB == 0:
            continue
        wF = total - wB
        if wF == 0:
            break
        sumB += bins[i] * counts[i]
        mB = sumB / wB
        mF = (sum_total - sumB) / wF
        between = wB * wF * (mB - mF) ** 2
        if between > maximum:
            threshold = bins[i]
            maximum = between
    
    return threshold
