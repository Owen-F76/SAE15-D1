from pathlib import Path
import folium
from folium.plugins import FastMarkerCluster
import pandas as pd

# Project directory
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

# ANFR data files
files = {
    "antenne": "sup_antenne.txt",
    "bande": "sup_bande.txt",
    "emetteur": "sup_emetteur.txt",
    "station": "sup_station.txt",
    "support": "sup_support.txt",
}

# Load all data tables
data = {}

for name, filename in files.items():
  file_path = DATA_DIR / filename

  data[name] = pd.read_csv(file_path, sep=";", low_memory=False)

  print(f"{name}: {len(data[name])} rows loaded")


# Prepare support coordinates
support = data["support"].copy()

coordinate_columns = [
    "COR_NB_DG_LAT",
    "COR_NB_MN_LAT",
    "COR_NB_SC_LAT",
    "COR_NB_DG_LON",
    "COR_NB_MN_LON",
    "COR_NB_SC_LON",
]

# Convert coordinates into numbers
for column in coordinate_columns:
  support[column] = pd.to_numeric(support[column], errors="coerce")

# Calculate latitude
support["latitude"] = (
    support["COR_NB_DG_LAT"]
    + support["COR_NB_MN_LAT"] / 60
    + support["COR_NB_SC_LAT"] / 3600
)

# Calculate longitude
support["longitude"] = (
    support["COR_NB_DG_LON"]
    + support["COR_NB_MN_LON"] / 60
    + support["COR_NB_SC_LON"] / 3600
)

# Apply geographical directions
support.loc[
    support["COR_CD_NS_LAT"].astype(str).str.upper() == "S", "latitude"
] *= -1

support.loc[
    support["COR_CD_EW_LON"].astype(str).str.upper() == "W", "longitude"
] *= -1

# Keep valid coordinates
support = support.dropna(subset=["latitude", "longitude"])

# Keep coordinates within mainland France
support = support[
    support["latitude"].between(41, 52) & support["longitude"].between(-6, 10)
]

print("Valid supports:", len(support))


# Create interactive map
radio_map = folium.Map(location=[46.6, 2.5], zoom_start=6, tiles=None)

# Fond de carte principal : Esri WorldStreetMap
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri",
    name="Esri WorldStreetMap",
    overlay=False,
    control=True,
    show=True,
).add_to(radio_map)

# Fond alternatif épuré : Esri WorldGrayCanvas
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri",
    name="Esri Gray Canvas",
    overlay=False,
    control=True,
    show=False,
).add_to(radio_map)

# Prepare geographical coordinates
coordinates = list(zip(support["latitude"], support["longitude"]))

# Add grouped radio installation markers
FastMarkerCluster(
    data=coordinates, name="Installations radioélectriques"
).add_to(radio_map)

# Add layer control
folium.LayerControl().add_to(radio_map)

# Save interactive map
map_path = PROJECT_DIR / "carteradioelectrique.html"

radio_map.save(str(map_path))

print("Map created successfully!")
print("Number of supports displayed:", len(coordinates))
print("Map saved at:", map_path)