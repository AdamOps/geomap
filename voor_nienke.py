import os
import pandas as pd
import geopandas as gpd
import pyproj
import numpy as np
import matplotlib.pyplot as plt

# Common directory
username = os.environ.get("USERNAME")

# Pandas parameters
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# Import covid data
# @Nienke: Deze kun je vervangen met de CSV die je van MinFin hebt gekregen.
coronasteun_oud = pd.read_csv("verdeling.csv", sep=';', encoding="ISO-8859-1")
coronasteun = pd.read_csv("gemeente_steun.csv", sep=';',encoding="UTF-8", decimal=',')

# Read geopckg file, with the correct layer. Need municipalities here.
# municipal_boundaries = gpd.read_file("cbsgebiedsindelingen2022.gpkg")
# @Nienke: Je kunt hier ook voor andere aggregatieniveaus gaan.
# Ik vermoed wel dat het op postcodeniveau wat rommelig kan gaan worden, want dat zijn er gewoon
# echt superveel.
if(os.path.isfile("map.gpkg")):
    municipal_boundaries = gpd.read_file("map.gpkg")
else:
    geodata_url = 'https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName=cbs_gemeente_2021_gegeneraliseerd&outputFormat=json'
    municipal_boundaries = gpd.read_file(geodata_url)
    municipal_boundaries.to_file("map.gpkg")

# Link data from Statistics Netherlands to geodata
# @Nienke: In jouw dataset van MinFin staat ook 'statnaam', dus die kun je ook in de "right_on" gebruiken.
result = pd.merge(municipal_boundaries, coronasteun, left_on='statnaam', right_on='Gemeente', how='left')
result.to_crs(pyproj.CRS.from_epsg(28992), inplace=True)
result.to_file("gem_map.gpkg", driver='GPKG')
result.set_index("statnaam")

# @Nienke: Je zult waarschijnlijk geen log-waardes nodig hebben, dus deze kun je overslaan.
result['ones'] = 1
result['log_totaal'] = np.log(result['steun_per_bedrijf'])
result.fillna(value={'log_totaal': 0}, inplace=True)


###############################################################
# Per bedrijf
map_figure, ax = plt.subplots(1, figsize=(6, 10))
ax.axis('off')
ax.set_title('Coronasteun per bedrijf (uitgesplitst naar gemeente)')
# cax = ax.imshow(result, cmap=cm.coolwarm, vmin="€"+ str(min(result['steun_per_bedrijf'])), vmax="€" + str(max(result['steun_per_bedrijf'])))
color_bar = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(
    vmin=min(result['steun_per_bedrijf']), vmax=max(result['steun_per_bedrijf'])))
color_bar.set_array([])
plt.colorbar(color_bar, orientation="horizontal", fraction=0.03, pad=0.05, aspect = 20, ticks=[1000, 2750, 4500, 6250, 8000]).set_ticklabels(["€1000", "€2750", "€4500", "€6250", "€8000"])
geo_fig = result.plot(column=result['steun_per_bedrijf'], cmap='viridis', linewidth=0.8, ax=ax, edgecolor='0.8')
plt.savefig("geo_fig_per_bedrijf.png", bbox_inches='tight')
plt.show()

# Hopelijk heb je nu een voorbeeld van een plaatje!
