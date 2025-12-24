import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

st.set_page_config(page_title="🌱 스마트팜 환경 & 생육 분석", layout="wide")

st.title("🌱 스마트팜 환경 & 생육 분석 대시보드")

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_env_data():
    data = {}
    for school in ["동산고", "대전과학고", "세종과학고"]:
        filename = f"{school}_환경데이터.csv"
        if os.path.exists(filename):
            data[school] = pd.read_csv(filename)
    return data


@st.cache_data
def load_growth_data():
    data = {}
    for school in ["동산고", "대전과학고", "세종과학고"]:
        filename = f"{school}_생육데이터.csv"
        if os.path.exists(filename):
            data[school] = pd.read_csv(filename)
    return data


env_data = load_env_data()
growth_data = load_growth_data()

# ===============================
# 탭 구성
# ===============================
tab1, tab2, tab3 = st.tabs(["🌡️ 환경 데이터", "📊 생육 결과", "🧪 미니 스마트팜 시뮬레이션"])

# ===============================
# 🌡️ 환경 데이터
# ===============================
with tab1:
    st.subheader("학교별 환경 변화 (꺾은선 그래프)")

    for school, df in env_data.items():
        fig = px.line(
            df,
            x="날짜",
            y=["온도", "습도", "EC", "pH"],
            title=f"{school} 환경 변화"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("학교별 평균 환경값 (막대그래프)")
    avg_list = []
    for school, df in env_data.items():
        avg_list.append({
            "학교": school,
            "습도": df["습도"].mean(),
            "EC": df["EC"].mean(),
            "pH": df["pH"].mean()
        })

    avg_df = pd.DataFrame(avg_list)
    fig_bar = px.bar(avg_df, x="학교", y=["습도", "EC", "pH"], barmode="group")
    st.plotly_chart(fig_bar, use_container_width=True)

# ===============================
# 📊 생육 결과
# ===============================
with tab2:
    st.subheader("EC별 평균 생중량")

    growth_all = pd.concat(growth_data.values(), ignore_index=True)
    ec_avg = growth_all.groupby("EC")["생중량(g)"].mean().reset_index()

    fig_ec = px.bar(ec_avg, x="EC", y="생중량(g)", text_auto=".2f")
    st.plotly_chart(fig_ec, use_container_width=True)

    st.subheader("학교별 생중량 분포")
    fig_box = px.box(growth_all, x="학교", y="생중량(g)")
    st.plotly_chart(fig_box, use_container_width=True)

# ===============================
# 🧪 미니 스마트팜 시뮬레이션
# ===============================
with tab3:
    st.subheader("🌱 생육 조건 시뮬레이션")

    col1, col2 = st.columns([1, 1])

    with col1:
        humidity = st.slider("습도 (%)", 30, 90, 60)
        ec = st.slider("EC (mS/cm)", 0.5, 3.5, 2.0, step=0.1)
        ph = st.slider("pH", 4.5, 7.5, 6.0, step=0.1)

    # 기준 조건 (50점)
    base_cond = {"습도": 60, "EC": 2.0, "pH": 6.0}

    # 실제 데이터 기반 최고 생육량
    base_growth = growth_all["생중량(g)"].mean()
    max_growth = growth_all["생중량(g)"].max()

    # 가중 거리 계산
    dist = (
        abs(humidity - base_cond["습도"]) / 30 +
        abs(ec - base_cond["EC"]) / 1.5 +
        abs(ph - base_cond["pH"]) / 1.5
    )

    predicted_growth = base_growth * (1 + 0.15 * np.exp(-dist))
    growth_index = 50 + (predicted_growth - base_growth) / (max_growth - base_growth) * 50
    growth_index = float(np.clip(growth_index, 0, 100))

    with col2:
        st.metric("🌿 예상 생육지수", f"{growth_index:.1f} / 100")

        size = 80 + growth_index * 2
        fig_leaf = px.scatter(
            x=[0], y=[0],
            size=[size],
            size_max=200,
            color=[growth_index],
            color_continuous_scale="Greens"
        )
        fig_leaf.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300
        )
        st.plotly_chart(fig_leaf, use_container_width=True)

    st.caption("※ 기준 조건(습도 60%, EC 2.0, pH 6.0)은 50점이며, 실험 데이터 기반 최고 생육 조건이 100점입니다.")
