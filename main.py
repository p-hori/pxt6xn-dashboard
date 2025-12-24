import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 유틸
# ===============================
def nfc(text):
    return unicodedata.normalize("NFC", text)

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_env(data_dir):
    env = {}
    for f in data_dir.iterdir():
        if f.suffix == ".csv":
            school = nfc(f.stem.split("_")[0])
            df = pd.read_csv(f)
            df["time"] = pd.to_datetime(df["time"])
            env[school] = df
    return env

@st.cache_data
def load_growth(data_dir):
    growth = {}
    xlsx = next((f for f in data_dir.iterdir() if f.suffix == ".xlsx"), None)
    if xlsx is None:
        return growth

    xls = pd.ExcelFile(xlsx)
    for sheet in xls.sheet_names:
        df = pd.read_excel(xlsx, sheet_name=sheet)
        school = nfc(sheet)
        df["학교"] = school
        growth[school] = df
    return growth

# ===============================
# 데이터 불러오기
# ===============================
DATA_DIR = Path("data")

with st.spinner("📂 데이터 로딩 중..."):
    if not DATA_DIR.exists():
        st.error("❌ data 폴더가 없습니다.")
        st.stop()

    env_data = load_env(DATA_DIR)
    growth_data = load_growth(DATA_DIR)

common_schools = sorted(set(env_data) & set(growth_data))
if not common_schools:
    st.error("❌ 환경 데이터와 생육 데이터가 일치하지 않습니다.")
    st.stop()

# ===============================
# 사이드바
# ===============================
selected_school = st.sidebar.selectbox(
    "🏫 학교 선택",
    ["전체"] + common_schools
)

# ===============================
# 제목
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ===============================
# Tab 1 실험 개요
# ===============================
with tab1:
    st.subheader("🔍 연구 배경 및 목적")
    st.markdown("""
    본 연구는 극지 환경을 모사한 조건에서  
    EC(전기전도도) 농도 차이가 식물 생육에 미치는 영향을 분석하여  
    최적 EC 농도 조건을 도출하는 것을 목표로 한다.
    """)

    summary = []
    total = 0

    for s in common_schools:
        cnt = len(growth_data[s])
        total += cnt
        summary.append({
            "학교명": s,
            "평균 EC": round(env_data[s]["ec"].mean(), 2),
            "개체수": cnt
        })

    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    env_all = pd.concat(env_data.values())
    growth_all = pd.concat(growth_data.values())

    ec_map = {s: env_data[s]["ec"].mean() for s in common_schools}
    growth_all["EC"] = growth_all["학교"].map(ec_map)

    optimal_ec = growth_all.groupby("EC")["생중량(g)"].mean().idxmax()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", total)
    c2.metric("평균 온도(℃)", f"{env_all['temperature'].mean():.1f}")
    c3.metric("평균 습도(%)", f"{env_all['humidity'].mean():.1f}")
    c4.metric("최적 EC", f"{optimal_ec:.2f}", delta="⭐")

# ===============================
# Tab 2 환경 데이터
# ===============================
with tab2:
    st.subheader("📊 학교별 환경 평균")

    avg_env = []
    for s in common_schools:
        df = env_data[s]
        avg_env.append({
            "학교": s,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "EC": df["ec"].mean()
        })

    avg_df = pd.DataFrame(avg_env)

    fig_env = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "평균 EC"]
    )

    fig_env.add_bar(x=avg_df["학교"], y=avg_df["온도"], row=1, col=1)
    fig_env.add_bar(x=avg_df["학교"], y=avg_df["습도"], row=1, col=2)
    fig_env.add_bar(x=avg_df["학교"], y=avg_df["pH"], row=2, col=1)
    fig_env.add_bar(x=avg_df["학교"], y=avg_df["EC"], row=2, col=2)

    fig_env.update_layout(
        height=600,
        font=dict(family="Malgun Gothic")
    )
    st.plotly_chart(fig_env, use_container_width=True)

    st.subheader("📈 학교별 평균 EC 추세")
    fig_ec_line = px.line(
        avg_df.sort_values("EC"),
        x="학교",
        y="EC",
        markers=True
    )
    fig_ec_line.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_ec_line, use_container_width=True)

# ===============================
# Tab 3 생육 결과
# ===============================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    ec_avg = growth_all.groupby("EC")["생중량(g)"].mean().reset_index()

    fig_bar = px.bar(ec_avg, x="EC", y="생중량(g)", text_auto=".2f")
    fig_bar.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_bar, use_container_width=True)

    fig_line = px.line(ec_avg.sort_values("EC"), x="EC", y="생중량(g)", markers=True)
    fig_line.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("📦 학교별 생중량 분포")
    fig_box = px.box(growth_all, x="학교", y="생중량(g)")
    fig_box.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("📈 상관관계 분석")
    c1, c2 = st.columns(2)

    with c1:
        st.plotly_chart(
            px.scatter(growth_all, x="잎 수(장)", y="생중량(g)"),
            use_container_width=True
        )

    with c2:
        st.plotly_chart(
            px.scatter(growth_all, x="지상부 길이(mm)", y="생중량(g)"),
            use_container_width=True
        )

    with st.expander("📥 생육 데이터 다운로드"):
        buffer = io.BytesIO()
        growth_all.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
