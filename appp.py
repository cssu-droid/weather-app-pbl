import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. ページ基本設定 ---
st.set_page_config(
    page_title="気圧・湿度チェッカー (気象病対策)",
    page_icon="🌤️",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- 2. 本番API設定 ---
API_KEY = "3a79056c70f2c5211d3f3b786c2ddc01" 

BASE_URL_CURRENT = "https://api.openweathermap.org/data/2.5/weather"
BASE_URL_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"

# --- 3. ヘッダー表示 ---
st.title("🌤️ 気圧・湿度チェッカー")
st.caption("PBL開発成果物 - 日本国内都市限定・リアルタイム気圧予報システム")
st.markdown("---")

# --- 4. ユーザー入力エリア ---
with st.form(key='search_form'):
    city_name = st.text_input(
        label="市区町村名を入力してください（※ローマ字のみ対応 例: kawasaki, okayama）",
        placeholder="地名を入力してEnter...",
        key="city_input_key"
    )
    submit_button = st.form_submit_button(label='天気を取得する')

# --- 5. メイン処理 ---
if submit_button and st.session_state["city_input_key"]:
    current_city = st.session_state["city_input_key"].strip()

    if not current_city:
        st.error("⚠️ 市区町村名が入力されていません。")
    elif API_KEY == "皆さんが取得した実際のAPIキー" or API_KEY == "DUMMY":
        st.error("⚠️ コード内の `API_KEY` を、取得した実際のキーに書き換えてください。")
    else:
        with st.spinner('OpenWeatherMapから日本のリアルタイム気象データを取得中...'):
            try:
                target_city = current_city + ",jp"
                params = {"q": target_city, "appid": API_KEY, "units": "metric", "lang": "ja"}
                
                res_current = requests.get(BASE_URL_CURRENT, params=params, timeout=3.0)
                res_forecast = requests.get(BASE_URL_FORECAST, params=params, timeout=3.0)

                if res_current.status_code == 401 or res_forecast.status_code == 401:
                    st.error("🔑 APIキーの認証に失敗しました。")
                elif res_current.status_code == 404 or res_forecast.status_code == 404:
                    st.error("🔍 場所が見つかりませんでした。")
                elif res_current.status_code != 200 or res_forecast.status_code != 200:
                    st.error("🚨 APIサーバーとの通信で予期せぬエラーが発生しました。")
                else:
                    data_current = res_current.json()
                    data_forecast = res_forecast.json()

                    temp = data_current['main']['temp']
                    pressure = data_current['main']['pressure']
                    humidity = data_current['main']['humidity']
                    display_name = data_current['name']

                    weather_id = data_current['weather'][0]['id']
                    if weather_id >= 200 and weather_id < 700:
                        simple_weather = "雨"
                    elif weather_id >= 801 and weather_id <= 804:
                        simple_weather = "曇り"
                    else:
                        simple_weather = "晴れ"

                    # 📍 ここで「display_name」を使って都市名を自動連動させます
                    st.subheader(f"📍 {display_name} の現在の天気")
                    
                    # 💡 ここで「湿度」という正しいラベルを指定しています（水分は消滅します）
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric(label="現在の天気", value=simple_weather)
                    with col2: st.metric(label="気温", value=f"{temp} °C")
                    with col3: st.metric(label="気圧", value=f"{pressure} hPa")
                    with col4: st.metric(label="湿度", value=f"{humidity} %")
                        
                    st.markdown("---")
                    
                    st.subheader(f"📉 {display_name} の今後24時間の気圧変化予報")
                    
                    forecast_list = data_forecast['list'][:8]
                    chart_data = []
                    for item in forecast_list:
                        time_str = datetime.fromtimestamp(item['dt']).strftime('%m/%d %H:%M')
                        p_val = item['main']['pressure']
                        chart_data.append({"日時": time_str, "気圧 (hPa)": p_val})
                    
                    df = pd.DataFrame(chart_data)
                    
                    fig = go.Figure(go.Scatter(
                        x=df["日時"], y=df["気圧 (hPa)"], 
                        mode='lines+markers', 
                        line=dict(color='#008080', width=3),
                        marker=dict(size=8)
                    ))
                    fig.update_layout(
                        margin=dict(l=20, r=20, t=10, b=10), 
                        height=280, 
                        template="plotly_white",
                        xaxis_title="日時",
                        yaxis_title="気圧 (hPa)"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.success(f"🎯 {display_name} のリアルタイムデータ通信に成功しました！")

            except requests.exceptions.Timeout:
                st.error("⏳ タイムアウト：APIからの応答が3秒以内にありませんでした。")
            except requests.exceptions.RequestException:
                st.error("🌐 ネットワーク接続エラーが発生しました。")