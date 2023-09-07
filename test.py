import os
import pandas as pd
import geopandas as gpd
import plotly.express as px
import pyproj
import numpy as np
import fiona
import math
import matplotlib.pyplot as plt
from matplotlib import cm
import plotly.graph_objects as go

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
# if(os.path.isfile("gem_map.gpkg")):
#     result = gpd.read_file("gem_map.gpkg")
# else:
# coronasteun = coronasteun.groupby(['Gemeente']).sum(numeric_only=True)
# @Nienke: In jouw dataset van MinFin staat ook 'statnaam', dus die kun je ook in de "right_on" gebruiken.
result = pd.merge(municipal_boundaries, coronasteun, left_on='statnaam', right_on='Gemeente', how='left')
result.to_crs(pyproj.CRS.from_epsg(28992), inplace=True)
# @Nienke: NB: Als je de repository binnenhaalt kun je gem_map.gpkg waarschijnlijk het beste wissen
# of een andere naam geven. Anders gaat de code automatisch mijn tussenbestand inladen.
result.to_file("gem_map.gpkg", driver='GPKG')

# @Nienke: Het onderstaande is voor wat debugging. Gewoon negeren.
report = False
if report == True:
    report_df = pd.DataFrame(coronasteun['Gemeente'].describe(), columns=['left'])
    report_df = report_df.merge(pd.DataFrame(municipal_boundaries['statnaam'].describe(), columns=['right']), left_index=True, right_index=True)
    set_left = set(coronasteun['Gemeente'])
    set_right = set(municipal_boundaries['statnaam'])
    set_info = pd.DataFrame({'left':set_left.issubset(set_right), 'right':set_right.issubset(set_left)}, index=['subset'])
    report_df = report_df.append(set_info)
    set_info = pd.DataFrame({'left':len(set_left.difference(set_right)), 'right':len(set_right.difference(set_left))}, index=['differences'])
    report_df = report_df.append(set_info)
    #Return Random Sample of [5 Differences]
    left_diff = list(set_left.difference(set_right))[0:5]
    if len(left_diff) < 5:
        left_diff = (left_diff + [np.nan]*5)[0:5]
    right_diff = list(set_right.difference(set_left))[0:5]
    if len(right_diff) < 5:
        right_diff = (right_diff + [np.nan]*5)[0:5]
    set_info = pd.DataFrame({'left': left_diff, 'right': right_diff}, index=['diff1', 'diff2', 'diff3', 'diff4', 'diff5'])
    report_df = report_df.append(set_info)
    print(report_df)



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
# plt.clf()

# @Nienke: Eigenlijk heb je hierna niks meer nodig.

# Helper functions
def roundup(x, b):
    return int(math.ceil(x / b)) * b


def rounddown(x, b):
    return int(math.floor(x / b)) * b


def middlepoint(x, y, n, p):
    return int(x + p*(y - x)/n)

print('please stop')


###############################################################
# Totaal
tot_max = max(result['Coronasteun'])
tot_min = min(result['Coronasteun'])
mp0 = roundup(middlepoint(tot_min, tot_max, 5, 1), 100000)/100000
mp1 = roundup(middlepoint(tot_min, tot_max, 5, 2), 100000)/100000
mp2 = roundup(middlepoint(tot_min, tot_max, 5, 3), 100000)/100000
mp3 = roundup(middlepoint(tot_min, tot_max, 5, 4), 100000)/100000
mp4 = roundup(middlepoint(tot_min, tot_max, 5, 5), 100000)/100000

result['totaal_norm'] = result['Coronasteun'] / 100000

map_figure2, ax2 = plt.subplots(1, figsize=(6, 10))
ax2.axis('off')
ax2.set_title('Totale coronasteun (uitgesplitst naar gemeente)\n - (in €100,000)')
# cax = ax.imshow(result, cmap=cm.coolwarm, vmin="€"+ str(min(result['steun_per_bedrijf'])), vmax="€" + str(max(result['steun_per_bedrijf'])))
color_bar2 = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(
    vmin=tot_min/100000, vmax=tot_max/100000))
color_bar2.set_array([])
plt.colorbar(color_bar2, orientation="horizontal", fraction=0.03, pad=0.05, aspect = 20,
             ticks=[roundup(tot_min/100000, 1), mp0, mp1, mp2, mp3, mp4, rounddown(tot_max/100000, 1)]).set_ticklabels([
                                                                "€" + str(roundup(tot_min/100000, 1)) + ".0",
                                                                "€" + str(mp0),
                                                                "€"+ str(mp1),
                                                                "€"+ str(mp2),
                                                                "€"+ str(mp3),
                                                                "€"+ str(mp4),
                                                                "€" + str(rounddown(tot_max/100000, 1)) + ".0"])
geo_fig2 = result.plot(column=result['totaal_norm'], cmap='viridis', linewidth=0.8, ax=ax2, edgecolor='0.8')
plt.savefig("geo_fig_totaal.png", bbox_inches='tight')
# plt.show()
plt.clf()


###############################################################
# Per inwoner
pc_max = max(result['steun_per_inwoner'])
pc_min = min(result['steun_per_inwoner'])
mp0 = roundup(middlepoint(pc_min, pc_max, 5, 1), 1)
mp1 = roundup(middlepoint(pc_min, pc_max, 5, 2), 1)
mp2 = roundup(middlepoint(pc_min, pc_max, 5, 3), 1)
mp3 = roundup(middlepoint(pc_min, pc_max, 5, 4), 1)
mp4 = roundup(middlepoint(pc_min, pc_max, 5, 5), 1)

map_figure3, ax3 = plt.subplots(1, figsize=(6, 10))
ax3.axis('off')
ax3.set_title('Coronasteun per inwoner (uitgesplitst naar gemeente)')
# cax = ax.imshow(result, cmap=cm.coolwarm, vmin="€"+ str(min(result['steun_per_bedrijf'])), vmax="€" + str(max(result['steun_per_bedrijf'])))
color_bar3 = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(
    vmin=pc_min, vmax=pc_max))
color_bar3.set_array([])
plt.colorbar(color_bar3, orientation="horizontal", fraction=0.03, pad=0.05, aspect = 20,
             ticks=[rounddown(pc_min, 1), mp0, mp1, mp2, mp3, mp4, rounddown(pc_max, 1)]).set_ticklabels([
                                                                "€" + str(roundup(pc_min, 1)) + ".0",
                                                                "€" + str(mp0),
                                                                "€" + str(mp1),
                                                                "€" + str(mp2),
                                                                "€" + str(mp3),
                                                                "€" + str(mp4),
                                                                "€" + str(rounddown(pc_max, 1)) + ".0"])
geo_fig3 = result.plot(column=result['steun_per_inwoner'], cmap='viridis', linewidth=0.8, ax=ax3, edgecolor='0.8')
plt.savefig("geo_fig_per_inwoner.png", bbox_inches='tight')
plt.show()

print("Done")
