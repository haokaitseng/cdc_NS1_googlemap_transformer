# cdc_NS1_googlemap_transformer

# Dengue NS1 Rapid Test Clinics: Data Processing & Visualization
This Open Data project, supporting the [Taiwan CDC Open Data Portal](https://data.cdc.gov.tw/dataset/dengue_ns1_clinics), provides an automated pipeline for processing, geocoding, and visualizing the locations of medical facilities equipped with Dengue Fever NS1 rapid test kits in Taiwan.

By streamlining the transformation of public health records into accessible formats, this project enhances transparency and utility for both researchers and the general public. It consists of two main Python scripts that handle everything from raw data transformation to the generation of an interactive web map.

Project Overview
## 1. Data Processing & Geocoding (main_NS1_googlemap.py)
This script acts as the data engine. It takes a newly updated clinic roster (Excel) and cross-references it with a historical dataset (CSV) to smartly geocode clinic locations.

- Data Ingestion & Cleaning: Reads the latest clinic list and existing coordinate data. It standardizes column names, removes whitespace, and strictly enforces a 10-digit format for Hospital IDs to prevent data type mismatches.

- Smart Geocoding: Compares the newly ingested roster against the historical dataset. To optimize performance and minimize costs, it only triggers the Google Maps Geocoding API for newly added clinics that lack existing coordinate data.

- Standardized Outputs: Merges the data and exports it into a cleaned CSV (ns1hosp.csv) and a minified GeoJSON file (ns1hosp.json) containing all spatial properties (coordinates, addresses, contact info), uploading into [Taiwan CDC Open Data Portal](https://data.cdc.gov.tw/dataset/dengue_ns1_clinics)

## 2. Interactive Map Generation (visualize.py)
This script transforms the processed geographic data into a user-friendly, interactive web map.

- Mapping Engine: Utilizes the folium library to render a map centered on Taiwan.

- Performance Optimization: Implements MarkerCluster to smoothly render a large volume of clinic points, preventing browser lag.

- Rich Interactive Elements: Parses the ns1hosp.json file to plot location markers. Each marker features a customized HTML popup displaying crucial clinic details, including the hospital name, city, ID, address, and telephone number.

- Output: Generates a standalone HTML webpage (ns1_interactive_map.html) that can be easily opened and navigated in any standard web browser.