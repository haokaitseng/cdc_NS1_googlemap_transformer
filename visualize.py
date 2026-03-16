import folium
import json
from folium.plugins import MarkerCluster

# 1. 讀取產出的 GeoJSON 檔案
with open('ns1hosp.json', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# 2. 初始化地圖中心點（設在台灣中部）
m = folium.Map(location=[23.7, 121.0], zoom_start=8, control_scale=True)

# 3. 使用標記叢集 (Marker Cluster) 處理大量點位，避免地圖卡頓
marker_cluster = MarkerCluster().add_to(m)

# 4. 解析 GeoJSON 並加入標記
for feature in geojson_data['features']:
    coords = feature['geometry']['coordinates'] # [經度, 緯度]
    props = feature['properties']
    
    # 注意：Folium 的 location 順序是 [緯度, 經度]
    lat, lon = coords[1], coords[0]
    
    # 建立彈出視窗的 HTML 內容
    popup_content = f"""
    <div style="font-family: Microsoft JhengHei; width: 250px;">
        <h4 style="color: #2c3e50; margin-bottom: 5px;">{props['hospName']}</h4>
        <hr style="margin: 5px 0;">
        <b>縣市：</b>{props['city']}<br>
        <b>代碼：</b>{props['hospID']}<br>
        <b>地址：</b>{props['hospAddress']}<br>
        <b>電話：</b>{props['hospTel']}<br>
    </div>
    """
    
    folium.Marker(
        location=[lat, lon],
        popup=folium.Popup(popup_content, max_width=300),
        tooltip=props['hospName'],
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(marker_cluster)

# 5. 儲存成 HTML 網頁
output_file = 'ns1_interactive_map.html'
m.save(output_file)

print(f"地圖已成功產出！請使用瀏覽器開啟：{output_file}")