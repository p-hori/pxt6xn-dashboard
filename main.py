import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import unicodedata
import io
import os  


st.set_page_config(page_title="스마트팜 대시보드", layout="wide")

# ===============================
# 데이터 로드 (CSV 없어도 실행)
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
            # CSV 없을 때 더미 데이터 생성
            df = pd.DataFrame({
                "날짜": pd.date_range("2024-01-01", periods=30),
                "온도": np.random.uniform(18, 28, 30),
                "습도": np.random.uniform(40, 80, 30)
            })
        data[school] = df

    return data


# ===============================
# 생육지수 계산 함수
# ===============================
def calculate_growth_index(humidity, ec, ph):
    # 이상적인 값
    ideal_h, ideal_ec, ideal_ph = 60, 2.0, 6.0

    score = (
        100
        - abs(humidity - ideal_h) * 0.8
        - abs(ec - ideal_ec) * 20
        - abs(ph - ideal_ph) * 15
    )

    return max(0, min(100, score))


# ===============================
# 메인
# ===============================
st.title("🌱 스마트팜 환경 & 생육 분석 대시보드")

env_data = load_env_data()

# -------------------------------
# 환경 데이터 (꺾은선 그래프)
# -------------------------------
st.header("📈 학교별 환경 데이터")

col1, col2 = st.columns(2)

with col1:
    selected_school = st.selectbox("학교 선택", list(env_data.keys()))

with col2:
    selected_var = st.selectbox("변수 선택", ["온도", "습도"])

df = env_data[selected_school]

fig, ax = plt.subplots()
ax.plot(df["날짜"], df[selected_var], marker="o")
ax.set_xlabel("날짜")
ax.set_ylabel(selected_var)
ax.set_title(f"{selected_school} - {selected_var} 변화")
plt.xticks(rotation=45)
st.pyplot(fig)

# -------------------------------
# 생육 결과 요약
# -------------------------------
st.header("📊 생육 결과 요약")

avg_temp = df["온도"].mean()
avg_hum = df["습도"].mean()

st.metric("평균 온도 (°C)", f"{avg_temp:.1f}")
st.metric("평균 습도 (%)", f"{avg_hum:.1f}")

# ===============================
# 🌿 미니 스마트팜 시뮬레이션
# ===============================
st.header("🧪 미니 스마트팜 시뮬레이션")

st.markdown("슬라이더로 환경을 조절하면 **예상 생육지수(0~100)** 가 계산됩니다.")

sim_col1, sim_col2 = st.columns([2, 1])

with sim_col1:
    humidity = st.slider("습도 (%)", 0, 100, 60)
    ec = st.slider("EC (mS/cm)", 0.0, 5.0, 2.0, 0.1)
    ph = st.slider("pH", 4.0, 8.0, 6.0, 0.1)

    growth_index = calculate_growth_index(humidity, ec, ph)

    st.subheader("🌱 예상 생육지수")
    st.metric("생육지수", f"{growth_index:.1f} / 100")

with sim_col2:
    # 새싹 크기 시각화
    size = 50 + growth_index * 5

    fig2, ax2 = plt.subplots()
    ax2.scatter(0, 0, s=size, marker="^")
    ax2.set_xlim(-1, 1)
    ax2.set_ylim(-1, 1)
    ax2.axis("off")
    ax2.set_title("생육 상태")

    st.pyplot(fig2)

st.success("✅ 기존 구조 유지 + 시뮬레이션 정상 추가 완료")
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
    env = {}
    for school in ["동산고", "송도고", "아라고", "하늘고"]:
        file = find_file(DATA_DIR, f"{school}_환경데이터.csv")
        if file is None:
            st.error(f"❌ 환경 데이터 파일 없음: {school}")
            st.stop()
        df = pd.read_csv(file)
        df["time"] = pd.to_datetime(df["time"])
        df["학교"] = school
        env[school] = df
    return env

@st.cache_data
def load_growth_data():
    xlsx = find_file(DATA_DIR, "4개교_생육결과데이터.xlsx")
    if xlsx is None:
        st.error("❌ 생육 결과 XLSX 없음")
        st.stop()

    sheets = pd.ExcelFile(xlsx, engine="openpyxl").sheet_names
    return {s: pd.read_excel(xlsx, sheet_name=s) for s in sheets}

with st.spinner("데이터 로딩 중..."):
    env_data = load_env_data()
    growth_data = load_growth_data()

# =========================
# 환경 데이터 통합
# =========================
@st.cache_data
def merge_env(env_dict):
    return pd.concat(env_dict.values(), ignore_index=True)

env_all = merge_env(env_data)

# =========================
# 생육 데이터 통합
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
# TAB 1 실험 개요
# =========================
with tab1:
    st.markdown("""
### 🔍 연구 배경 및 목적
극지 환경을 모사한 조건에서  
EC(전기전도도) 농도 차이가 식물 생육에 미치는 영향을 분석하여  
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
    c2.metric("평균 온도", round(env_all["temperature"].mean(), 2))
    c3.metric("평균 습도", round(env_all["humidity"].mean(), 2))
    c4.metric("최적 EC", "2.0 ⭐ (하늘고)")

# =========================
# TAB 2 환경 데이터 (⭐ 핵심 수정)
# =========================
with tab2:
    st.subheader("📈 학교별 환경 변화 비교 (꺾은선그래프)")

    metrics = {
        "temperature": "온도 (℃)",
        "humidity": "습도 (%)",
        "ph": "pH",
        "ec": "EC"
    }

    for col, label in metrics.items():
        fig = px.line(
            env_all,
            x="time",
            y=col,
            color="학교",
            markers=True,
            title=f"학교별 {label} 변화"
        )
        fig.update_layout(
            font=dict(family="Malgun Gothic"),
            legend_title_text="학교"
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📥 환경 데이터 원본"):
        st.dataframe(env_all, use_container_width=True)

        buf = io.BytesIO()
        env_all.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            "환경데이터 XLSX 다운로드",
            data=buf,
            file_name="환경데이터_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =========================
# TAB 3 생육 결과
# =========================
with tab3:
    st.subheader("🥇 EC별 평균 생중량")

    ec_avg = growth_all.groupby("EC", as_index=False)["생중량(g)"].mean()

    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(ec_avg, x="EC", y="생중량(g)", text_auto=".2f"), True)
    c2.plotly_chart(px.line(ec_avg, x="EC", y="생중량(g)", markers=True), True)

    st.subheader("📦 학교별 생중량 분포")
    st.plotly_chart(px.box(growth_all, x="학교", y="생중량(g)"), True)

    with st.expander("📥 생육 데이터 원본"):
        st.dataframe(growth_all, use_container_width=True)

        buf = io.BytesIO()
        growth_all.to_excel(buf, index=False, engine="openpyxl")
        buf.seek(0)
        st.download_button(
            "생육결과 XLSX 다운로드",
            data=buf,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
