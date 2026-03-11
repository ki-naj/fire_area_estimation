import ee


def get_aoi_geometry(coords: list) -> ee.Geometry:
    return ee.Geometry.Rectangle(coords)


def get_image_collection(
    collection_name: str,
    aoi: ee.Geometry,       #<-- aoi musi być ee.Geometry
    date_start: str,
    date_end: str
) -> ee.ImageCollection:
    return (
        ee.ImageCollection(collection_name)
        .filterBounds(aoi)      #<-- filtracja obrazów na podstawie obszaru który mu damy
        .filterDate(date_start, date_end)
    )

#wybiera zdj po index i przycina do aoi
def get_specific_image(
    collection: ee.ImageCollection,
    image_id: str,
    aoi: ee.Geometry
) -> ee.Image:
    image = ee.Image(
        collection
        .filter(ee.Filter.eq("system:index", image_id))
        .first()    #<-- wybiera pierwszy obraz bo mimo że mamy filter po id to może być wiećej podobnych ID no i jeszcze ten filter zamienia kolkcje na Image który dopiero możemy przycinać
    ).clip(aoi)
    return image


def inspect_collection(col: ee.ImageCollection, label: str = "Collection") -> None:
    size = col.size().getInfo()
    print(f"{label} - {size} images")
    
    imgs = col.toList(size)
    for i in range(size):
        img = ee.Image(imgs.get(i))
        info = img.toDictionary([
            "system:index",
            "system:time_start",
            "SPACECRAFT_NAME",
            "MGRS_TILE",
            "CLOUDY_PIXEL_PERCENTAGE"
        ]).getInfo()
        
        date = ee.Date(info["system:time_start"]).format("YYYY-MM-dd").getInfo()
        print(f"[{i}] {date} {info['SPACECRAFT_NAME']} Cloud: {info['CLOUDY_PIXEL_PERCENTAGE']} {info['system:index']}%")


def describe_image(img: ee.Image, label: str = "Image") -> dict:
    """Print detailed image metadata."""
    info = img.toDictionary([
        "system:index",
        "system:time_start",
        "SPACECRAFT_NAME",
        "MGRS_TILE",
        "CLOUDY_PIXEL_PERCENTAGE",
        "GRANULE_ID"
    ]).getInfo()
    
    date = ee.Date(info["system:time_start"]).format("YYYY-MM-dd HH:mm").getInfo()
    print(f"  {label}: {date} {info['SPACECRAFT_NAME']} Cloud: {info['CLOUDY_PIXEL_PERCENTAGE']} ID: {info['GRANULE_ID']}%")
    
    return info

#funkcja potrzebuje mieć AOI w postaci ee.Geometry
#bierze zadane aoi liczy powierzchnię, dzieli na 1000 = hektarary i zwraca jako float
def calculate_aoi_area(aoi: ee.Geometry) -> float:
    area_ha = aoi.area(1).divide(10000).getInfo()
    return area_ha


def resample_image_to_10m(image: ee.Image, resampling_method: str = "nearest") -> ee.Image:
    # Earth Engine resamples automatically when using reproject with a new scale
    # The default resampling is bilinear; nearest neighbor is applied via reduceNeighborhood if needed
    return image.reproject(
        crs=image.projection(),
        scale=10
    )
