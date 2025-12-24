import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="🌱 극지식물 최적 EC 농도 연구", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# =========================
# 유니코드 안전 파일 찾기
# =========================
def find_file(directory: Path, target: str):
    t_nfc = unicodedata.normalize("NFC", target)
    t_nfd = unicodedata.normalize("NFD", target)

    for f in directory.iterdir():
        f_nfc = unicodedata.normalize("NFC", f.name)
        f_nfd = unicodedata.normalize("NFD", f.name)
        if f_nfc == t_nfc or f_nfd == t_nfd:
            return f
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_env_data():
    data = {}
    for school in ["동산고", "송도고", "아라고", "하늘고"]:
        file = find_file(DATA_DIR, f"{school}_환경데이터.csv")
        if file is None:
            st.error(f"❌ 환경 데이터 없음: {school}")
            st.stop()
        df = pd.read_csv(file)
        df["time"] = pd.to_datetime(df["time"])
        data[school] = df
    return data

@st.cache_data
def load_growth_data():
    xlsx = find_file(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if xlsx is None:
        st.error("❌ 생육결과 XLSX 없음")
        st.stop()

    sheets = pd.ExcelFile(xlsx, engine="openpyxl").sheet_names
    return {s: pd.read_excel(xlsx, sheet_name=s) for s in sheets}

with st.spinner("데이터 로딩 중..."):
    env_data = load_env_data()
    growth_data = load_growth_data()

# =========================
# 생육 데이터 통합 (원본 보존)
# =========================
@st.cache_data
def merge_growth(growth_dict, env_dict):
    out = []
    for school, df in growth_dict.items():
        tmp = df.copy()
        tmp["학교"] = school
        tmp["EC"] = round(env_dict[school]["ec"].mean(), 2)
        out.append(tmp)
    return pd.concat(out, ignore_index=True)

growth_all = merge_growth(growth_data, env_data)

# =========================
# UI
# =========================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =========================
# TAB 1
# =========================
with tab1:
    st.markdown("""
### 🔍 연구 배경 및 목적
극지 환경을 모사한 조건에서  
EC(전기전도도) 농도가 식물 생육에 미치는 영향을 분석하여  
최적 EC 농도를 도출한다.
""")

    summary = []
    total = 0
    for school, df in growth_data.items():
        summary.append({
            "학교명": school,
            "EC 목표": round(env_data[school]["ec"].mean(), 2),
            "개체수": len(df)
        })
        total += len(df)

    st.dataframe(pd.DataFrame(summary), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", total)
    c2.metric("평균 온도", round(pd.concat(env_data.values())["temperature"].mean(), 2))
    c3.metric("평균 습도", round(pd.concat(env_data.values())["humidity"].mean(), 2))
    c4.metric("최적 EC", "2.0 ⭐ (하늘고)")

# =========================
# TAB 2 환경 데이터
# =========================
with tab2:
    for school, df in env_data.items():
        st.subheader(f"🏫 {school}")

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=["온도", "습도", "pH", "EC"]
        )
        fig.add_bar(x=[school], y=[df["temperature"].mean()], row=1, col=1)
        fig.add_bar(x=[school], y=[df["humidity"].mean()], row=1, col=2)
        fig.add_bar(x=[school], y=[df["ph"].mean()], row=2, col=1)
        fig.add_bar(x=[school], y=[df["ec"].mean()], row=2, col=2)

        fig.update_layout(font=dict(family="Malgun Gothic"), height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.line_chart(df.set_index("time")[["temperature", "humidity", "ec"]])

# =========================
# TAB 3 생육 결과
# =========================
with tab3:
    ec_avg = growth_all.groupby("EC", as_index=False)["생중량(g)"].mean()

    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(ec_avg, x="EC", y="생중량(g)", text_auto=".2f"), True)
    c2.plotly_chart(px.line(ec_avg, x="EC", y="생중량(g)", markers=True), True)

    st.plotly_chart(px.box(growth_all, x="학교", y="생중량(g)"), True)

    with st.expander("📥 생육 데이터 원본"):
        st.dataframe(growth_all, use_container_width=True)
        buf = io.BytesIO()
        growth_all.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            "XLSX 다운로드",
            data=buf,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
