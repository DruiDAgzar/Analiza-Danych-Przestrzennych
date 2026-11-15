"""LAB02 – GeoPandas: czujniki PM2.5 w Opolu (kroki A1–A9).

Uruchomienie:  python lab02_geopandas.py
Skrypt odtwarza kroki A1–A9, sprawdza punkty kontrolne instrukcji
i zapisuje mapy (images/) oraz wyniki przestrzenne (wyniki/).
"""
from pathlib import Path

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pyproj import Geod
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
DANE = BASE / "dane"
IMG = BASE / "images"
OUT = BASE / "wyniki"
IMG.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)


def check(cond, msg):
    assert cond, f"Punkt kontrolny NIE zgadza się: {msg}"
    print(f"  ✓ {msg}")


# ---------- A1. Geometria i GeoDataFrame ----------
print("A1")
rynek = Point(17.9226, 50.6681)                      # (x, y) = (długość, szerokość)
square = Polygon([(17.92, 50.66), (17.93, 50.66), (17.93, 50.67), (17.92, 50.67)])
places = gpd.GeoDataFrame({"name": ["Rynek", "Square"]},
                          geometry=[rynek, square], crs="EPSG:4326")
check(places.crs.to_string() == "EPSG:4326", "places.crs = EPSG:4326")
check(list(places.geom_type) == ["Point", "Polygon"], "geom_type = Point, Polygon")

# ---------- A2. Wczytanie surowych danych ----------
print("A2")
raw = pd.read_csv(DANE / "pm25_sensors.csv", parse_dates=["measured_at"])
check(raw.shape == (145, 5), "145 wierszy, 5 kolumn")
check(raw["pm25"].min() == -999, "min pm25 = -999")
check(round(raw["lat"].min(), 2) == 17.87, "min lat ≈ 17,87")
check(raw["lat"].isna().sum() == 3 and raw["lon"].isna().sum() == 4, "braki: lat 3, lon 4")
check(raw.duplicated().sum() == 5, "5 duplikatów")

# ---------- A3. Czyszczenie danych ----------
print("A3")
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
print("  ", report)
check(report == {"input rows": 145, "after drop_duplicates": 140, "after dropna": 134,
                 "swapped rows fixed": 3, "clean rows": 130}, "145 → 140 → 134, 3 naprawione, 130")

# ---------- A4. Z tabeli do GeoDataFrame ----------
print("A4")
sensors = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]),
                           crs="EPSG:4326")
check(sensors.total_bounds.round(2).tolist() == [17.79, 50.62, 18.02, 50.77],
      "total_bounds ≈ [17.79, 50.62, 18.02, 50.77]")

# ---------- A5. Układy współrzędnych ----------
print("A5")
sensors_m = sensors.to_crs("EPSG:2180")
d_m = sensors_m.geometry.iloc[0].distance(sensors_m.geometry.iloc[1])
check(round(d_m) == 4906, f"odległość 2 pierwszych czujników ≈ 4906 m ({d_m:.1f})")

gdansk, zakopane = (18.6466, 54.3520), (19.9496, 49.2992)
pts = gpd.GeoSeries.from_xy([gdansk[0], zakopane[0]], [gdansk[1], zakopane[1]], crs="EPSG:4326")
_, _, true_m = Geod(ellps="WGS84").inv(*gdansk, *zakopane)
dist = {crs: pts.to_crs(crs).iloc[0].distance(pts.to_crs(crs).iloc[1]) for crs in ["EPSG:3857", "EPSG:2180"]}
check(round(true_m / 1000, 1) == 569.3, "geodezyjna ≈ 569,3 km")
check(round(dist["EPSG:2180"] / 1000, 1) == 568.9, "EPSG:2180 ≈ 568,9 km")
check(round(dist["EPSG:3857"] / 1000, 1) == 922.8, "EPSG:3857 ≈ 922,8 km")

# ---------- A6. Dzielnice ----------
print("A6")
districts = gpd.read_file(DANE / "opole_districts.geojson")
check(len(districts) == 29 and districts.crs.to_string() == "EPSG:4326", "29 dzielnic, EPSG:4326")
districts = districts.to_crs("EPSG:2180")
districts["area_km2"] = districts.area / 1e6
check(round(districts["area_km2"].sum(), 1) == 148.8, "powierzchnia miasta 148,8 km²")
big = districts.loc[districts["area_km2"].idxmax()]
small = districts.loc[districts["area_km2"].idxmin()]
check(big["name"] == "Czarnowąsy" and round(big["area_km2"], 1) == 14.1, "największa: Czarnowąsy ≈ 14,1 km²")
check(small["name"] == "Borki" and round(small["area_km2"], 2) == 0.66, "najmniejsza: Borki ≈ 0,66 km²")

# ---------- A7. Złączenie przestrzenne ----------
print("A7")
joined = gpd.sjoin(sensors_m, districts[["name", "geometry"]], how="left", predicate="within")
check(len(joined) == 130 and joined["name"].isna().sum() == 0, "130 czujników, 0 bez dzielnicy")
stats = (joined.groupby("name")
               .agg(pm25_mean=("pm25", "mean"), sensor_count=("pm25", "size"))
               .round(1))
summary = districts.merge(stats, on="name", how="left")
check(summary["sensor_count"].isna().sum() == 3, "3 dzielnice bez czujnika")
top3 = summary[summary["sensor_count"] >= 3].nlargest(3, "pm25_mean")
check(list(zip(top3["name"], top3["pm25_mean"])) ==
      [("Stare Miasto", 29.6), ("Śródmieście", 26.8), ("Zaodrze", 22.5)],
      "top 3: Stare Miasto 29,6; Śródmieście 26,8; Zaodrze 22,5")

# ---------- A8. Bufory ----------
print("A8")
schools = gpd.read_file(DANE / "opole_schools.geojson").to_crs("EPSG:2180")
buffers = schools.copy()
buffers["geometry"] = schools.buffer(500)
near = gpd.sjoin(sensors_m, buffers[["name", "geometry"]], predicate="within")
check(len(schools) == 19, "19 szkół")
check(near["name"].nunique() == 11, "11 szkół z czujnikiem w promieniu 500 m")
check(round(near["pm25"].mean(), 1) == 22.3, "średnie PM2.5 przy szkołach ≈ 22,3 µg/m³")
city = districts.union_all()
coverage = buffers.union_all().intersection(city).area / city.area
check(round(100 * coverage, 1) == 9.5, f"bufory pokrywają ≈ 9,5% miasta ({coverage:.1%})")
b1500 = schools.copy()
b1500["geometry"] = schools.buffer(1500)
n1500 = gpd.sjoin(sensors_m, b1500[["name", "geometry"]], predicate="within")["name"].nunique()
print(f"  (eksperyment) szkoły z czujnikiem w promieniu 1500 m: {n1500}")

# ---------- A9. Zapis wyników ----------
print("A9")
gpkg = OUT / "pm25.gpkg"
summary.to_file(gpkg, layer="districts", driver="GPKG")
sensors_m.to_file(gpkg, layer="sensors", driver="GPKG")
summary.to_crs("EPSG:4326").to_file(OUT / "pm25_districts.geojson", driver="GeoJSON")
layers = gpd.list_layers(gpkg)
check(set(layers["name"]) == {"districts", "sensors"}, "GeoPackage: warstwy districts, sensors")
chk = gpd.read_file(gpkg, layer="districts")
check(len(chk) == 29 and chk.crs.to_string() == "EPSG:2180", "wczytana warstwa: 29 wierszy, EPSG:2180")

# ---------- Mapy ----------
schools_4326 = schools.to_crs("EPSG:4326")
districts_4326 = districts.to_crs("EPSG:4326")

fig, ax = plt.subplots(figsize=(9, 9))
districts_4326.boundary.plot(ax=ax, color="grey", linewidth=0.7)
sensors.plot(ax=ax, column="pm25", cmap="Oranges", legend=True, markersize=40,
             edgecolor="black", linewidth=0.3,
             legend_kwds={"label": "PM2.5 [µg/m³]", "shrink": 0.6})
schools_4326.plot(ax=ax, color="blue", marker="^", markersize=50, label="Szkoły podstawowe")
ax.set_title(f"Czujniki PM2.5 w Opolu po oczyszczeniu danych (n = {len(sensors)})")
ax.set_xlabel("Długość geograficzna [°]")
ax.set_ylabel("Szerokość geograficzna [°]")
ax.legend(loc="lower left")
fig.savefig(IMG / "01_czujniki_pm25_opole.png", dpi=150, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 9))
summary.plot(ax=ax, column="pm25_mean", cmap="Oranges", scheme="quantiles", k=5,
             legend=True, edgecolor="white", linewidth=0.5,
             legend_kwds={"title": "Średnie PM2.5 [µg/m³]", "loc": "lower left"},
             missing_kwds={"color": "lightgrey", "label": "brak czujników"})
ax.set_title("Średnie PM2.5 w dzielnicach Opola (kwantyle, k = 5)")
ax.set_axis_off()
fig.savefig(IMG / "08_kartogram_pm25_dzielnice.png", dpi=150, bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 9))
districts.boundary.plot(ax=ax, color="grey", linewidth=0.7)
buffers.plot(ax=ax, color="orange", alpha=0.4, edgecolor="darkorange")
sensors_m.plot(ax=ax, color="black", markersize=8, label="Czujniki PM2.5")
schools.plot(ax=ax, color="blue", marker="^", markersize=50, label="Szkoły podstawowe")
ax.set_title(f"Bufory 500 m wokół szkół ({coverage:.1%} powierzchni miasta)")
ax.legend(loc="lower left")
ax.set_axis_off()
fig.savefig(IMG / "09_bufory_szkoly_500m.png", dpi=150, bbox_inches="tight")
plt.close(fig)

sensors.explore(column="pm25", cmap="Oranges",
                marker_kwds={"radius": 6}).save(IMG / "mapa_czujniki.html")
summary.explore(column="pm25_mean", cmap="Oranges", scheme="quantiles", k=5,
                legend_kwds={"caption": "mean PM2.5 [µg/m³]"},
                missing_kwds={"color": "lightgray", "label": "no sensors"}).save(IMG / "mapa_kartogram.html")
wrong = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lat"], df["lon"]), crs="EPSG:4326")
wrong.explore(marker_kwds={"radius": 6}).save(IMG / "mapa_bledne_wspolrzedne.html")

print("\nWszystkie punkty kontrolne A1–A9: OK")
print("Mapy:", IMG)
print("Wyniki:", OUT)
