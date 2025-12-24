# main.py
import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="극지식물 EC 연구", layout="wide")

# =========================
# 데이터 로딩 (캐싱)
# =========================
@st.cache_data
def load_env_data():
    return {
        "동산고": pd.read_csv("동산고_환경데이터.csv"),
        "송도고": pd.read_csv("송도고_환경데이터.csv"),
        "아라고": pd.read_csv("아라고_환경데이터.csv"),
        "하늘고": pd.read_csv("하늘고_환경데이터.csv"),
    }

@st.cache_data
def load_growth_data():
    return {
        "동산고": pd.read_excel("4개교_생육결과데이터.xlsx", sheet_name="동산고"),
        "송도고": pd.read_excel("4개교_생육결과데이터.xlsx", sheet_name="송도고"),
        "아라고": pd.read_excel("4개교_생육결과데이터.xlsx", sheet_name="아라고"),
        "하늘고": pd.read_excel("4개교_생육결과데이터.xlsx", sheet_name="하늘고"),
    }

env_data = load_env_data()
growth_data = load_growth_data()

# =========================
# 생육 데이터 통합 (원본 보존)
# =========================
@st.cache_data
def make_growth_all(growth_dict):
    dfs = []
    for school, df in growth_dict.items():
        temp = df.copy()
        temp["학교"] = school
        dfs.append(temp)
    return pd.concat(dfs, ignore_index=True)

growth_all = make_growth_all(growth_data)
growth_raw = growth_all.copy()   # 🔒 원본 고정

# =========================
# 요약 테이블
# =========================
summary = []
for school, df in growth_data.items():
    summary.append({
        "학교명": school,
        "EC 목표": round(env_data[school]["ec"].mean(), 2),
        "개체수": len(df)
    })
summary_df = pd.DataFrame(summary)

# =========================
# UI
# =========================
st.title("🌱 극지식물 최적 EC 농도 연구")
st.subheader("📊 실험 요약")
st.dataframe(summary_df, use_container_width=True)

tab1, tab2, tab3 = st.tabs(["🌡️ 환경 데이터", "📊 생육 결과", "📈 분석"])

# =========================
# TAB 1 환경 데이터
# =========================
with tab1:
    for school, df in env_data.items():
        st.subheader(f"🏫 {school}")

        fig_env = px.line(
            df,
            x=df.index,
            y="ec",
            markers=True,
            title="EC 변화"
        )
        fig_env.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_env, use_container_width=True)

# =========================
# TAB 2 생육 결과
# =========================
with tab2:
    st.subheader("🥇 EC별 평균 생중량")

    ec_avg = growth_raw.groupby("EC", as_index=False)["생중량(g)"].mean()

    c1, c2 = st.columns(2)

    with c1:
        fig_bar = px.bar(ec_avg, x="EC", y="생중량(g)", text_auto=".2f")
        fig_bar.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        fig_line = px.line(ec_avg, x="EC", y="생중량(g)", markers=True)
        fig_line.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("📦 학교별 생중량 분포")
    fig_box = px.box(growth_raw, x="학교", y="생중량(g)")
    fig_box.update_layout(font=dict(family="Malgun Gothic"))
    st.plotly_chart(fig_box, use_container_width=True)

# =========================
# TAB 3 상관관계
# =========================
with tab3:
    show_trend = st.checkbox("회귀선(OLS) 표시", value=False)
    trend = "ols" if show_trend else None

    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.scatter(
            growth_raw,
            x="잎 수(장)",
            y="생중량(g)",
            trendline=trend
        )
        fig1.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fig2 = px.scatter(
            growth_raw,
            x="지상부 길이(mm)",
            y="생중량(g)",
            trendline=trend
        )
        fig2.update_layout(font=dict(family="Malgun Gothic"))
        st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📥 생육 데이터 원본"):
        st.dataframe(growth_raw, use_container_width=True)

        buffer = io.BytesIO()
        growth_raw.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
