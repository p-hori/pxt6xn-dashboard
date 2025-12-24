import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ===============================
# 기본 설정
# ===============================
st.set_page_config(page_title="🌱 스마트팜 환경 & 생육 분석 대시보드", layout="wide")

# ===============================
# 데이터 로드 (없으면 더미)
# ===============================
@st.cache_data
def load_env_data():
    schools = ["동산고", "대건고", "제일고"]
    data = {}

    for school in schools:
        filename = f"{school}_환경데이터.csv"
        if os.path.exists(filename):
            df = pd.read_csv(filename)
        else:
            df = pd.DataFrame({
                "날짜": pd.date_range("2024-01-01", periods=30),
                "온도": np.random.uniform(18, 28, 30),
                "습도": np.random.uniform(40, 80, 30),
                "EC": np.random.uniform(1.0, 3.0, 30),
                "pH": np.random.uniform(5.5, 6.5, 30),
            })
        df["학교"] = school
        data[school] = df

    return data


# ===============================
# 생육지수 계산 (기본 50점)
# ===============================
def calculate_growth_index(humidity, ec, ph, env_df):
    base = 50

    avg_h = env_df["습도"].mean()
    avg_ec = env_df["EC"].mean()
    avg_ph = env_df["pH"].mean()

    score = base
    score += (humidity - avg_h) * 0.4
    score += (ec - avg_ec) * 10
    score += (ph - avg_ph) * 8

    return max(0, min(100, score))


# ===============================
# 메인
# ===============================
st.title("🌱 스마트팜 환경 & 생육 분석 대시보드")

env_data = load_env_data()
env_all = pd.concat(env_data.values(), ignore_index=True)

tab1, tab2, tab3 = st.tabs(["🌡️ 환경 데이터", "📊 환경 요약", "🧪 생육 시뮬레이션"])

# ===============================
# TAB 1 꺾은선그래프
# ===============================
with tab1:
    metric = st.selectbox("변수 선택", ["온도", "습도", "EC", "pH"])

    fig = px.line(
        env_all,
        x="날짜",
        y=metric,
        color="학교",
        markers=True,
        title=f"학교별 {metric} 변화"
    )
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# TAB 2 막대그래프
# ===============================
with tab2:
    avg_df = env_all.groupby("학교")[["습도", "EC", "pH"]].mean().reset_index()
    avg_long = avg_df.melt("학교", var_name="항목", value_name="평균값")

    fig_bar = px.bar(
        avg_long,
        x="학교",
        y="평균값",
        color="항목",
        barmode="group",
        title="학교별 평균 환경 비교"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ===============================
# TAB 3 미니 스마트팜 시뮬레이션
# ===============================
with tab3:
    st.markdown("""
- **기본 50점**: 습도 60% / EC 2.0 / pH 6.0  
- 실험 데이터 평균보다 좋으면 최대 **100점**
""")

    c1, c2 = st.columns([2, 1])

    with c1:
        h = st.slider("습도 (%)", 0, 100, 60)
        ec = st.slider("EC (mS/cm)", 0.0, 5.0, 2.0, 0.1)
        ph = st.slider("pH", 4.0, 8.0, 6.0, 0.1)

        gi = calculate_growth_index(h, ec, ph, env_all)
        st.metric("🌱 예상 생육지수", f"{gi:.1f} / 100")

    with c2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            mode="markers",
            marker=dict(
                size=gi * 3 + 20,
                symbol="triangle-up",
                color="green"
            )
        ))
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            title="생육 상태",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

st.success("✅ matplotlib 제거 완료 → Streamlit Cloud 정상 실행")
