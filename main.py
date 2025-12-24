import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import os
from pathlib import Path

# ===============================
# 기본 설정
# ===============================
st.set_page_config(page_title="🌱 스마트팜 환경 & 생육 분석 대시보드", layout="wide")

# ===============================
# 데이터 로드 (없으면 더미 생성)
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
# 생육지수 계산 (기본 50점 기준)
# ===============================
def calculate_growth_index(humidity, ec, ph, env_df):
    """
    이상 조건(60%, 2.0, 6.0) = 50점
    우리 데이터 평균보다 더 좋으면 50~100
    나쁘면 0~50
    """

    base_score = 50

    # 데이터 기반 평균
    avg_h = env_df["습도"].mean()
    avg_ec = env_df["EC"].mean()
    avg_ph = env_df["pH"].mean()

    score = base_score

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

# ===============================
# TAB 구성
# ===============================
tab1, tab2, tab3 = st.tabs(["🌡️ 환경 데이터", "📊 환경 요약", "🧪 생육 시뮬레이션"])

# ===============================
# TAB 1 환경 데이터 (꺾은선)
# ===============================
with tab1:
    st.subheader("📈 학교별 환경 변화 (꺾은선그래프)")

    metric_map = {
        "온도": "온도 (℃)",
        "습도": "습도 (%)",
        "EC": "EC (mS/cm)",
        "pH": "pH"
    }

    selected_metric = st.selectbox("변수 선택", list(metric_map.keys()))

    fig_line = px.line(
        env_all,
        x="날짜",
        y=selected_metric,
        color="학교",
        markers=True,
        title=f"학교별 {metric_map[selected_metric]} 변화"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ===============================
# TAB 2 환경 데이터 (막대그래프)
# ===============================
with tab2:
    st.subheader("📊 학교별 평균 환경값 (막대그래프)")

    avg_df = env_all.groupby("학교")[["습도", "EC", "pH"]].mean().reset_index()

    # 🔑 반드시 long-form 변환 (에러 방지)
    avg_df_long = avg_df.melt(
        id_vars="학교",
        value_vars=["습도", "EC", "pH"],
        var_name="항목",
        value_name="평균값"
    )

    fig_bar = px.bar(
        avg_df_long,
        x="학교",
        y="평균값",
        color="항목",
        barmode="group",
        title="학교별 평균 환경 비교"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("📥 환경 데이터 원본"):
        st.dataframe(env_all, use_container_width=True)

# ===============================
# TAB 3 미니 스마트팜 시뮬레이션
# ===============================
with tab3:
    st.subheader("🌿 미니 스마트팜 시뮬레이션")

    st.markdown("""
- **기본 50점**: 습도 60% / EC 2.0 / pH 6.0  
- 우리 실험 데이터 평균보다 더 좋은 조건이면 **50~100점**
- 생육지수는 **0~100**
""")

    c1, c2 = st.columns([2, 1])

    with c1:
        humidity = st.slider("습도 (%)", 0, 100, 60)
        ec = st.slider("EC (mS/cm)", 0.0, 5.0, 2.0, 0.1)
        ph = st.slider("pH", 4.0, 8.0, 6.0, 0.1)

        growth_index = calculate_growth_index(
            humidity, ec, ph, env_all
        )

        st.metric("🌱 예상 생육지수", f"{growth_index:.1f} / 100")

    with c2:
        size = 300 + growth_index * 10

        fig, ax = plt.subplots()
        ax.scatter(0, 0, s=size, marker="^")
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.axis("off")
        ax.set_title("생육 상태")

        st.pyplot(fig)

st.success("✅ 환경 분석 + 막대그래프 + 생육 시뮬레이션 정상 동작")
