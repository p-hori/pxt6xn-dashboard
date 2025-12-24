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

# ===============================
# 한글 폰트
# ===============================
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
def normalize_name(name):
    return unicodedata.normalize("NFC", name)

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_environment_data(data_dir: Path):
    env_data = {}
    for f in data_dir.iterdir():
        if f.suffix.lower() == ".csv":
            school = normalize_name(f.stem.split("_")[0])
            df = pd.read_csv(f)
            df["time"] = pd.to_datetime(df["time"])
            env_data[school] = df
    return env_data


@st.cache_data
def load_growth_data(data_dir: Path):
    xlsx_file = None
    for f in data_dir.iterdir():
        if f.suffix.lower() == ".xlsx":
            xlsx_file = f
            break

    if xlsx_file is None:
        return {}

    growth = {}
    xls = pd.ExcelFile(xlsx_file)
    for sheet in xls.sheet_names:
        school = normalize_name(sheet)
        df = pd.read_excel(xlsx_file, sheet_name=sheet)
        df["학교"] = school
        growth[school] = df
    return growth


# ===============================
# 데이터 로드
# ===============================
DATA_DIR = Path("data")

with st.spinner("📂 데이터 로딩 중..."):
    if not DATA_DIR.exists():
        st.error("❌ data 폴더를 찾을 수 없습니다.")
        st.stop()

    env_data = load_environment_data(DATA_DIR)
    growth_data = load_growth_data(DATA_DIR)

    if not env_data or not growth_data:
        st.error("❌ 데이터 파일이 없거나 비어 있습니다.")
        st.stop()

# ===============================
# 공통 학교
# ===============================
common_schools = sorted(set(env_data.keys()) & set(growth_data.keys()))

if not common_schools:
    st.error("❌ 환경 데이터와 생육 데이터가 일치하는 학교가 없습니다.")
    st.stop()

# ===============================
# 사이드바
# ===============================
schools = ["전체"] + common_schools
selected_school = st.sidebar.selectbox("🏫 학교 선택", schools)

# ===============================
# 제목 & 탭
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ===============================
# Tab 1: 실험 개요
# ===============================
with tab1:
    st.subheader("🔍 연구 배경 및 목적")
    st.markdown("""
    본 연구는 **극지 환경을 모사한 조건**에서  
    **EC(전기전도도) 농도 차이가 식물 생육에 미치는 영향**을 분석하여  
    **최적 EC 농도 조건**을 도출하는 것을 목표로 한다.
    """)

    summary = []
    total_plants = 0

    for school in common_schools:
        df = growth_data[school]
        total_plants += len(df)

        summary.append({
            "학교명": school,
            "평균 EC": round(env_data[school]["ec"].mean(), 2),
            "개체수": len(df)
        })

    st.dataframe(pd.DataFrame(summary), use_container_width=True)

# ===============================
# Tab 2: 환경 데이터
# ===============================
with tab2:
    st.subheader("📊 학교별 환경 평균 비교")

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

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("평균 온도", "평균 습도", "평균 pH", "평균 EC")
    )

    fig.add_bar(x=avg_df["학교"], y=avg_df["온도"], row=1, col=1)
    fig.add_bar(x=avg_df["학교"], y=avg_df["습도"], row=1, col=2)
    fig.add_bar(x=avg_df["학교"], y=avg_df["pH"], row=2, col=1)
    fig.add_bar(x=avg_df["학교"], y=avg_df["EC"], row=2, col=2)

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    if selected_school != "전체":
        df = env_data[selected_school]
        fig_ts = make_subplots(rows=3, cols=1, shared_xaxes=True)
        fig_ts.add_line(x=df["time"], y=df["temperature"], row=1, col=1)
        fig_ts.add_line(x=df["time"], y=df["humidity"], row=2, col=1)
        fig_ts.add_line(x=df["time"], y=df["ec"], row=3, col=1)
        fig_ts.update_layout(height=700)
        st.plotly_chart(fig_ts, use_container_width=True)

# ===============================
# Tab 3: 생육 결과
# ===============================
with tab3:
    growth_all = pd.concat(growth_data[s] for s in common_schools)
    ec_map = {s: env_data[s]["ec"].mean() for s in common_schools}
    growth_all["EC"] = growth_all["학교"].map(ec_map)

    st.subheader("🥇 EC별 평균 생중량")
    ec_avg = growth_all.groupby("EC")["생중량(g)"].mean().reset_index()
    st.plotly_chart(px.bar(ec_avg, x="EC", y="생중량(g)", text_auto=".2f"), use_container_width=True)

    st.subheader("📦 학교별 생중량 분포")
    st.plotly_chart(px.box(growth_all, x="학교", y="생중량(g)"), use_container_width=True)

    # ===============================
    # 🌱 미니 스마트팜 시뮬레이터 (최종 수정)
    # ===============================
    st.divider()
    st.subheader("🧪 미니 스마트팜 시뮬레이터")

    st.markdown("""
    **기준 상태 (50점)**  
    - 습도: **60%**  
    - EC: **2.0 mS/cm**  
    - pH: **6.0**  

    실험 데이터에서 이 조건보다 생육에 유리할 경우 **50점 이상**,  
    최적 조건에서는 **100점에 도달**할 수 있다.
    """)

    IDEAL_H = 60.0
    IDEAL_EC = 2.0
    IDEAL_PH = 6.0

    def simulate_growth_index(h, ec, ph):
        score = 50
        score += (h - IDEAL_H) * 0.5
        score += (ec - IDEAL_EC) * 15
        score += (ph - IDEAL_PH) * 12
        return max(0, min(100, score))

    col1, col2 = st.columns([2, 1])

    with col1:
        h = st.slider("습도 (%)", 0, 100, 60)
        ec = st.slider("EC (mS/cm)", 0.0, 5.0, 2.0, 0.1)
        ph = st.slider("pH", 4.0, 8.0, 6.0, 0.1)

        score = simulate_growth_index(h, ec, ph)
        st.metric("🌱 예상 생육지수", f"{score:.1f} / 100")

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode="markers",
            marker=dict(
                size=score * 3 + 20,
                color="green",
                symbol="triangle-up"
            )
        ))
        fig.update_layout(
            height=300,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            title="생육 상태 시각화"
        )
        st.plotly_chart(fig, use_container_width=True)
