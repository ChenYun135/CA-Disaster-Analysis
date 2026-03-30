import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

# 页面配置：设置专业标题和宽屏布局
st.set_page_config(page_title="加州地震研究实验室", layout="wide", page_icon="🌋")

# 自定义 CSS 样式，提升专业感
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    </style>
""", unsafe_allow_html=True)

st.title("🛰️ 加州百年地震风险监测系统 (M4.0+)")
st.caption("数据来源：美国地质调查局 (USGS) | 研究范围：1926年至今加利福尼亚州全境")

# 侧边栏：交互控制中心
with st.sidebar:
    st.header("⚙️ 研究参数设定")
    year_range = st.slider("选择观测时间跨度:", 1926, 2026, (1980, 2026))
    min_mag = st.number_input("最低震级筛选:", 4.0, 9.0, 4.5, step=0.5)
    st.divider()
    st.info("💡 提示：滑动滑块可实时动态更新地图分布。")

@st.cache_data(show_spinner="正在同步 USGS 全球数据库...")
def load_data(start_year):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": f"{start_year}-01-01",
        "minmagnitude": 4.0,
        "minlatitude": 32.5, "maxlatitude": 42.0,
        "minlongitude": -124.5, "maxlongitude": -114.1
    }
    try:
        resp = requests.get(url, params=params, timeout=10).json()
        features = []
        for f in resp['features']:
            p, g = f['properties'], f['geometry']
            features.append({
                'time': pd.to_datetime(p['time'], unit='ms', utc=True),
                'mag': p['mag'],
                'place': p.get('place', '未知区域'),
                'lat': g['coordinates'][1],
                'lon': g['coordinates'][0]
            })
        df = pd.DataFrame(features)
        df['year'] = df['time'].dt.year
        return df
    except Exception as e:
        st.error(f"数据获取失败: {e}")
        return pd.DataFrame()

# 数据加载逻辑
raw_df = load_data(year_range[0])

if not raw_df.empty:
    # 动态筛选数据
    df = raw_df[(raw_df['year'] >= year_range[0]) & 
                (raw_df['year'] <= year_range[1]) & 
                (raw_df['mag'] >= min_mag)]

    # --- 第一部分：核心指标看板 ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("观测记录总数", f"{len(df)} 次")
    with col2:
        st.metric("区域最高震级", f"M {df['mag'].max():.1f}")
    with col3:
        st.metric("平均震级", f"M {df['mag'].mean():.1f}")
    with col4:
        st.metric("最活跃年份", int(df['year'].mode()[0]) if not df.empty else "-")

    st.divider()

    # --- 第二部分：多维分析标签页 ---
    tab1, tab2, tab3 = st.tabs(["🗺️ 空间分布地图", "📊 时间序列分析", "📋 原始科研数据"])

    with tab1:
        st.subheader("加州地震空间热力分布")
        fig_map = px.scatter_map(
            df, lat="lat", lon="lon", size="mag", color="mag",
            color_continuous_scale="Reds", 
            hover_name="place", hover_data=["time", "mag"],
            zoom=5, height=700,
            title=f"{year_range[0]}-{year_range[1]} 年间地震分布图"
        )
        fig_map.update_layout(map_style="carto-positron", margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, width="stretch")

    with tab2:
        st.subheader("地震频率年度趋势")
        yearly_counts = df.groupby('year').size().reset_index(name='count')
        fig_line = px.line(yearly_counts, x='year', y='count', 
                          labels={'year': '年份', 'count': '地震次数'},
                          template="plotly_white", markers=True)
        fig_line.update_traces(line_color='#d62728')
        st.plotly_chart(fig_line, width="stretch")
        
        st.subheader("震级分布密度")
        fig_hist = px.histogram(df, x="mag", nbins=20, 
                               labels={'mag': '震级'},
                               template="plotly_white", color_discrete_sequence=['#ff7f0e'])
    
        st.plotly_chart(fig_hist, width="stretch")

    with tab3:
        st.subheader("结构化数据视图")
        st.dataframe(df.sort_values('time', ascending=False), 
                     column_config={
                         "time": "发生时间",
                         "mag": st.column_config.NumberColumn("震级", format="M %.1f"),
                         "place": "地点名称",
                         "lat": "纬度",
                         "lon": "经度"
                     }, use_container_width=True)

else:
    st.warning("暂无符合条件的数据，请调整筛选参数。")