"""LAB02 – GeoPandas: czujniki PM2.5 w Opolu (kroki A1–A4).

Uruchomienie:  python lab02_geopandas.py
Wyniki:        images/01_czujniki_pm25_opole.png
               images/mapa_czujniki.html
               images/mapa_bledne_wspolrzedne.html
"""
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
DANE = BASE / "dane"
OUT = BASE / "images"
OUT.mkdir(exist_ok=True)

# ---------- A1. Geometria i GeoDataFrame ----------
rynek = Point(17.9226, 50.6681)                      # (x, y) = (długość, szerokość)
square = Polygon([(17.92, 50.66), (17.93, 50.66), (17.93, 50.67), (17.92, 50.67)])
places = gpd.GeoDataFrame({"name": ["Rynek", "Square"]},
                          geometry=[rynek, square], crs="EPSG:4326")
print("A1:", places.crs, list(places.geom_type), "| contains:", square.contains(rynek))

# ---------- A2. Wczytanie surowych danych ----------
raw = pd.read_csv(DANE / "pm25_sensors.csv", parse_dates=["measured_at"])
print("A2:", raw.shape, "| braki:", raw.isna().sum().to_dict(),
      "| duplikaty:", int(raw.duplicated().sum()))

# ---------- A3. Czyszczenie danych ----------
df = raw.copy()
report = {"input rows": len(df)}
df = df.drop_duplicates()
report["after drop_duplicates"] = len(df)
df = df.dropna(subset=["lat", "lon"])
report["after dropna"] = len(df)
swapped = df["lat"].between(14, 24.5) & df["lon"].between(49, 55)
df.loc[swapped, ["lat", "lon"]] = df.loc[swapped, ["lon", "lat"]].to_numpy()
report["swapped rows fixed"] = int(swapped.sum())
df = df[df["pm25"] >= 0].reset_index(drop=True)
report["clean rows"] = len(df)
print("A3:", report)

# ---------- A4. Z tabeli do GeoDataFrame ----------
sensors = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]),
                           crs="EPSG:4326")
print("A4:", list(sensors.geom_type.unique()), sensors.crs,
      sensors.total_bounds.round(2))

# Kontrola zgodności z punktami kontrolnymi instrukcji
assert report == {"input rows": 145, "after drop_duplicates": 140,
                  "after dropna": 134, "swapped rows fixed": 3, "clean rows": 130}
assert sensors.total_bounds.round(2).tolist() == [17.79, 50.62, 18.02, 50.77]
print("Punkty kontrolne: OK")

# ---------- Mapy ----------
districts = gpd.read_file(DANE / "opole_districts.geojson")
schools = gpd.read_file(DANE / "opole_schools.geojson")

fig, ax = plt.subplots(figsize=(9, 9))
districts.boundary.plot(ax=ax, color="grey", linewidth=0.7)
sensors.plot(ax=ax, column="pm25", cmap="Oranges", legend=True, markersize=40,
             edgecolor="black", linewidth=0.3,
             legend_kwds={"label": "PM2.5 [µg/m³]", "shrink": 0.6})
schools.plot(ax=ax, color="blue", marker="^", markersize=50, label="Szkoły podstawowe")
ax.set_title(f"Czujniki PM2.5 w Opolu po oczyszczeniu danych (n = {len(sensors)})")
ax.set_xlabel("Długość geograficzna [°]")
ax.set_ylabel("Szerokość geograficzna [°]")
ax.legend(loc="lower left")
fig.savefig(OUT / "01_czujniki_pm25_opole.png", dpi=150, bbox_inches="tight")

sensors.explore(column="pm25", cmap="Oranges",
                marker_kwds={"radius": 6}).save(OUT / "mapa_czujniki.html")

wrong = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lat"], df["lon"]),
                         crs="EPSG:4326")            # BŁĄD celowy: x = lat, y = lon
wrong.explore(marker_kwds={"radius": 6}).save(OUT / "mapa_bledne_wspolrzedne.html")
print("Błędne współrzędne – total_bounds:", wrong.total_bounds.round(2))
print("Zapisano mapy w:", OUT)
