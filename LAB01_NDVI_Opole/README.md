# LAB01 - Analiza wskaźnika NDVI dla Opola

**Przedmiot:** Analiza danych przestrzennych
**Autor:** Andrii Zaluskyi
**Obszar:** Opole, Polska
**Data obrazu:** 11.10.2026
**Źródło danych:** Copernicus Browser, Sentinel-2 L2A
**Narzędzia:** QGIS 3.34.4, GDAL 3.8.4

## Cel ćwiczenia
Celem było pobranie danych wielospektralnych i obliczenie znormalizowanego różnicowego wskaźnika wegetacji (NDVI) na podstawie kanałów czerwonego (B04) i bliskiej podczerwieni (B08), a następnie przedstawienie przestrzennego zróżnicowania wyników.

## Etapy
1. W Copernicus Browser wybrano obszar Opola i produkt Sentinel-2 L2A, dla sceny z dnia 11.10.2026 (ustawienie dopuszczalnego zachmurzenia: 30%).
2. Z zakładki **Analytical** pobrano obrazy TIFF (Float32), w tym warstwy surowe B04 i B08 oraz wizualizacje True Color i NDVI.
3. Warstwy wczytano do QGIS i zweryfikowano ich georeferencję: EPSG:4326, 661 × 412 pikseli.
4. W kalkulatorze rastra obliczono **NDVI = (B08 − B04) / (B08 + B04)**.
5. Wynik zapisano jako jednopasmowy GeoTIFF `NDVI_Opole_2026-10-11_R2.tif` i przedstawiono paletą czerwony–żółty–zielony.
6. Projekt zapisano w formacie QGIS `.qgz`.

## Interpretacja
Niższe wartości NDVI (czerwienie) występują m.in. na obszarach wodnych i powierzchniach bez aktywnej roślinności. Wyższe wartości (zieleń) zwykle odpowiadają roślinności. Na widocznej scenie występują chmury i cienie, co **ogranicza wiarygodność interpretacji** dla części pikseli. Kolory nie stanowią automatycznej klasyfikacji użytkowania terenu.

Widoczny zakres legendy dla obliczonego rastra wynosił **−1 do około 0,9365**. To zakres wyświetlania, a nie pełna walidacja wszystkich pikseli. Eksportowana z Copernicus warstwa `NDVI.tiff` była trójkanałową wizualizacją RGB; numeryczny NDVI obliczono niezależnie z B04 i B08.

## Uwaga o rozdzielczości
Eksport miał układ EPSG:4326; wielkość piksela jest zapisana w stopniach, nie w metrach. Wartość 10 m/px w ustawieniach eksportu nie oznacza identycznego rozmiaru terenowego piksela w obu kierunkach.

## Materiały
- [Raport PDF](raport_LAB01_NDVI_Opole.pdf)
- [1. Wybór danych](images/01_copernicus.png)
- [2. Eksport warstw](images/02_eksport.png)
- [3. Warstwy QGIS](images/03_warstwy.png)
- [4. Kalkulator rastra](images/04_kalkulator.png)
- [5. Wynik NDVI](images/05_wynik.png)

## Reprodukowalność
Pliki źródłowe GeoTIFF i projekt QGIS są przechowywane lokalnie. Można je dodać do repozytorium po sprawdzeniu rozmiaru i uprawnień dotyczących publikacji; niniejszy pakiet dokumentacyjny ich **nie zawiera**.

## Źródło
Copernicus Data Space Ecosystem: https://dataspace.copernicus.eu/
Copernicus Browser: https://browser.dataspace.copernicus.eu/
