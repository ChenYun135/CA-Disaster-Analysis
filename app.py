import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="加州地震研究", layout="wide")
st.title("🔬 加州百年地震分析 (M4.0+)")

@st.cache_data
def load_data():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": "1926-01-01",
        "minmagnitude": 4.0,
        "minlatitude": 32.5, "maxlatitude": 42.0,
        "minlongitude": -124.5, "maxlongitude": -114.1
    }
    resp = requests.get(url, params=params).json()
    
    features = []
    for f in resp['features']:
        p = f['properties']
        g = f['geometry']
        features.append({
            'time_val': p['time'],
            'mag': p['mag'],
            'place': p.get('place', 'Unknown'),
            'lat': g['coordinates'][1],
            'lon': g['coordinates'][0]
        })
    
    df = pd.DataFrame(features)
    # 【关键修复点】增加 errors='coerce' 和 format='ISO8601'
    # 这样无论是毫秒还是复杂的字符串，Pandas 都能强力转换
    df['time'] = pd.to_datetime(df['time_val'], unit='ms', utc=True)
    df['year'] = df['time'].dt.year
    
    df.to_csv("CA_100Year_Quakes.csv", index=False, encoding="utf-8-sig")
    return df

try:
    df = load_data()
    year_range = st.sidebar.slider("选择年份区间:", 1926, 2026, (1926, 2026))
    f_df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]

    fig = px.scatter_mapbox(f_df, lat="lat", lon="lon", size="mag", color="mag",
                            color_continuous_scale="Reds", hover_name="place",
                            zoom=5, height=600)
    fig.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig, use_container_width=True)
    
    st.success(f"成功加载 {len(f_df)} 条地震记录")
except Exception as e:
    st.error(f"解析出错，请尝试刷新页面: {e}")