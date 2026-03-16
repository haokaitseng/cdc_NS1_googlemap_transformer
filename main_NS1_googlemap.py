
# Project name: NS1 Open Data transforming address into latitude and longitude
# 急性組 更新OPEN DATA "登革熱 NS1 快篩試劑配置醫療院所"(URL: https://data.cdc.gov.tw/dataset/dengue_ns1_clinics)
# 請將 OPEN DATA目前掛著的資料下載到"old_data"的資料夾，命名為ns1hosp_old.csv 與ns1hosp_old.json
# 必須啟用 Google Cloud Console 的 Geocoding API
# pip install pandas openpyxl geopy
import pandas as pd
import json
import warnings
import re
from geopy.geocoders import GoogleV3
from geopy.extra.rate_limiter import RateLimiter

# 1. 忽略警告
warnings.simplefilter(action='ignore', category=FutureWarning)

# ==========================================
# 請在這裡填入您的 Google Maps API Key
# ==========================================
GOOGLE_API_KEY = ""

# 2. 讀取資料
# 讀取舊資料作為座標庫 (加入強制字串讀取與更強健的編碼容錯)
try:
    df_old = pd.read_csv('old_data/ns1hosp_old.csv', encoding='cp950', dtype={'hospID': str})
except:
    df_old = pd.read_csv('old_data/ns1hosp_old.csv', encoding='utf-8-sig', dtype={'hospID': str})

df_old.columns = df_old.columns.str.strip() # 清除舊資料欄位空格

# 讀取 115 年 Excel 新資料 (同樣強制將代碼視為字串)
excel_file = '115年「登革熱NS1抗原快速診斷試劑」醫療院所配置點名單_彙整1150309.xlsx'
df_new = pd.read_excel(
    excel_file, 
    sheet_name='名單彙整', 
    skiprows=1, 
    dtype={'醫療院所10碼代碼': str}  # 強制此欄位為字串
)

# 清除 Excel 欄位名稱的所有前後空格
df_new.columns = df_new.columns.str.strip()
print("目前讀取到的 Excel 欄位名稱為：", df_new.columns.tolist())

# 3. 欄位更名映射
def force_10_digits(val):
    if pd.isna(val): return ""
    # 移除小數點 .0 (防止 Excel 轉成 float)
    s = re.sub(r'\.0$', '', str(val).strip())
    # 【核心】補足 10 碼，不足者前面補 0
    return s.zfill(10)

# 套用清洗邏輯
df_new.columns = df_new.columns.str.strip()
df_new = df_new.rename(columns={
    '縣市': 'city',
    '醫療院所名稱': 'hospName',
    '醫療院所10碼代碼': 'hospID',
    '地址': 'hospAddress',
    '聯絡電話': 'hospTel'
})

df_new['hospID'] = df_new['hospID'].apply(force_10_digits)
df_old['hospID'] = df_old['hospID'].apply(force_10_digits)

print(f"範例檢查：原為 545040515 的代碼已變更為 {df_new['hospID'].iloc[4]}")



# 4. 準備代碼比對與映射
# 統一清除 hospID 的空白與小數點 '.0' (避免 Excel 將代碼轉為小數)
df_new['hospID'] = df_new['hospID'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
df_old['hospID'] = df_old['hospID'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

# 建立舊院所代碼的集合 (Set)，用來判斷是否為「新增資料」
old_hosp_ids = set(df_old['hospID'].unique())

# 從舊資料提取代碼映射與舊座標
city_code_map = df_old[['city', 'code']].drop_duplicates().set_index('city')['code'].to_dict()
old_coords = df_old[['hospID', 'latitude', 'longitude']].drop_duplicates('hospID')

# 5. 合併資料
# 填入縣市代碼
df_new['code'] = df_new['city'].map(city_code_map)

# --- 判斷並加上「新增資料」欄位 ---
df_new['新增資料'] = df_new['hospID'].apply(lambda x: '是' if x not in old_hosp_ids else '')

# 合併座標 (只有在此次是"是"的新增資料，latitude 才會是空值)
df_new = df_new.merge(old_coords, on='hospID', how='left')

# 6. 使用 Google Maps API 進行地理編碼 (針對真正新增的院所)
mask = df_new['latitude'].isna()
missing_count = mask.sum()
print(f"共有 {len(df_new)} 筆資料，其中 {missing_count} 筆是新增且無座標，需透過 Google API 查詢...")

if missing_count > 0:
    if GOOGLE_API_KEY == "請填入您的_GOOGLE_API_KEY":
        print("【錯誤】請先在程式碼中設定 GOOGLE_API_KEY 才能執行地理編碼！")
    else:
        print("正在啟動 Google Maps Geocoding 服務...")
        geolocator = GoogleV3(api_key=GOOGLE_API_KEY)
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.1)

        def clean_for_google(addr):
            addr = str(addr).replace('\xa0', '').strip()
            match = re.search(r'(.*?\d+號)', addr)
            return "台灣" + (match.group(1) if match else addr)

        df_new.loc[mask, 'search_address'] = df_new.loc[mask, 'hospAddress'].apply(clean_for_google)
        df_new.loc[mask, 'temp_loc'] = df_new.loc[mask, 'search_address'].apply(geocode)
        
        df_new.loc[mask, 'latitude'] = df_new.loc[mask, 'temp_loc'].apply(lambda x: x.latitude if x else None)
        df_new.loc[mask, 'longitude'] = df_new.loc[mask, 'temp_loc'].apply(lambda x: x.longitude if x else None)
        
        df_new = df_new.drop(columns=['temp_loc', 'search_address'])

# 7. 儲存 CSV 與 JSON
# 可以加上新增資料的欄位來辨識新的院所
csv_cols = ['code', 'city', 'hospName', 'hospID', 'hospAddress', 'latitude', 'longitude', 'hospTel'] # , '新增資料'
df_final = df_new[csv_cols].copy()

# 格式化代碼欄位
df_final['code'] = df_final['code'].apply(lambda x: str(int(x)) if pd.notna(x) else "")

# 存檔 CSV
df_final.to_csv('ns1hosp.csv', index=False, encoding='utf-8-sig')

# 產出 GeoJSON
# 產出 GeoJSON (完全對齊舊版格式)
features = []
for _, row in df_final.iterrows():
    if pd.notna(row['latitude']) and pd.notna(row['longitude']):
        # 按照舊版的欄位順序建立字典
        properties = {
            "city": str(row['city']),
            "hospName": str(row['hospName']),
            "hospID": str(row['hospID']).zfill(10), # 強制補足10碼
            "hospAddress": str(row['hospAddress']),
            "latitude": str(row['latitude']),
            "longitude": str(row['longitude']),
            "hospTel": str(row['hospTel']), 
            "code": str(row['code'])
        }
        
        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Point",
                "coordinates": [float(row['longitude']), float(row['latitude'])]
            }
        }
        features.append(feature)

geojson_data = {"type": "FeatureCollection", "features": features}

# 使用 separators 移除多餘空格與縮排，達到 Minified 效果
with open('ns1hosp.json', 'w', encoding='utf-8') as f:
    json.dump(geojson_data, f, ensure_ascii=False, separators=(',', ':'))

print("JSON 已依照舊版格式優化完成！")

print(f"處理完成！CSV 與 GeoJSON 已產出，共包含 {len(features)} 筆座標資料。")