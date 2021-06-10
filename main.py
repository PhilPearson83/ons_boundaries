import requests
import pandas as pd
import geopandas as gpd

# grab the service area of interest
def getservicearea():
    fra_endpoint = 'https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/Fire_and_Rescue_Authorities_December_2019_EW_BFC/FeatureServer/0/query?'
    fra_params = {'where': 'FRA19NM=\'Devon & Somerset\'', 'outFields': '*', 'outSR': 27700, 'f': 'geojson'}#, 'returnCountOnly': 'true'}
    req = requests.get(fra_endpoint, params=fra_params)
    j = req.json()
    gdf = gpd.GeoDataFrame.from_features(j['features'])
    gdf.crs = 'EPSG:27700'
    #gdf.to_file("fra.shp")
    return gdf

service_area = getservicearea()
#generate a bounding box of the service area to filter the subsequent boundaries
bbox = service_area.to_crs(epsg=4326).total_bounds

# create a list of names,endpoints and parameters,
layers = []
layers .append(('LSOA_2011_EW_BFC.shp', 
                'https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/Lower_Layer_Super_Output_Areas_December_2011_Boundaries_EW_BFC_V2/FeatureServer/0/query?',
                'LSOA11NM not like \'Cornwall%\' AND LSOA11NM not like \'%Dorset%\' AND LSOA11NM not like \'Wiltshire%\' AND LSOA11NM not like \'North Somerset%\' AND LSOA11NM not like \'Bath%\''
                ))
layers .append(('MSOA_2011_EW_BFC.shp', 
                'https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Middle_Layer_Super_Output_Areas_December_2011_EW_BFC_V2/FeatureServer/0/query?',
                'MSOA11NM not like \'Cornwall%\' AND MSOA11NM not like \'%Dorset%\' AND MSOA11NM not like \'Wiltshire%\' AND MSOA11NM not like \'North Somerset%\' AND MSOA11NM not like \'Bath%\''
                ))

#loop through our list of boundaries to create geodataframes from the output
for name, endpoint, where in layers:
    params = {'where': where,'geometry': bbox, 'geometryType': 'esriGeometryEnvelope', 'InSR': 4326, 'spatialRel':'esriSpatialRelIntersects','outFields': '*', 'outSR': 27700, 'f': 'geojson'}
    countonly = {'returnCountOnly': 'true'}
    z = {**params, **countonly}
    req = requests.get(endpoint, params=z)
    j = req.json()
    recordcount = j['properties']['count']
    print(recordcount)
    dfs = gpd.GeoDataFrame()
    for x in range(0, recordcount, 50):
        #print(x)
        offset = {'resultOffset': x}
        zz = {**params, **offset}
        req = requests.get(endpoint, params=zz)
        j = req.json()
        gdf = gpd.GeoDataFrame.from_features(j['features'])
        dfs = pd.concat([gdf, dfs], sort=False)
    dfs.crs = 'EPSG:27700'
    dfs = gpd.sjoin(dfs, service_area, how="inner", op='intersects')
    dfs.to_file(name)