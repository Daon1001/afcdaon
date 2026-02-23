import streamlit as st
import pandas as pd

# 페이지 스타일링
st.set_page_config(page_title="제조업 벤처인증 컨설팅 솔루션", layout="wide")

st.title("🛠️ 제조업 전문 벤처인증 전략 수립 시스템")
st.sidebar.header("📋 컨설턴트 전용 메뉴")
client_name = st.sidebar.text_input("고객사명", "OOO 산업")

# 1. 파일 업로드 및 데이터 추출 (가이드)
uploaded_file = st.file_uploader("사업자등록증 업로드 (OCR 분석)", type=["jpg", "png", "pdf"])

# 임의의 데이터 (실제론 OCR 결과값)
biz_item = "PVP 창호 제조 및 금속 창호재"

if uploaded_file:
    st.success(f"✔️ 분석 완료: {biz_item}")
    
    # 2. 업종별 벤처인증 고도화 전략 DB (컨설턴트의 노하우)
    strategy_db = {
        "창호": {
            "type": "스마트 제조 / 친환경 소재",
            "topics": [
                "열교 차단 기술을 적용한 고기밀성 단열 창호 시스템",
                "AI 비전 기반 창호 부재 자동 타공 및 절단 공정 솔루션",
                "폐플라스틱 재생 원료를 활용한 고강도 PVP 프레임 제조 기술"
            ],
            "patents": ["단열 구조", "자동화 센서", "재생 소재 조성물"],
            "funds": ["기보 벤처기반자금", "스마트공장 보급사업"]
        },
        "금속": {
            "type": "고정밀 공정 / 신소재",
            "topics": [
                "초경량 합금을 활용한 산업용 구조체 제조 기술",
                "내식성이 향상된 하이브리드 금속 표면 처리 공정"
            ],
            "patents": ["합금 조성", "표면 처리법"],
            "funds": ["뿌리기업 공정 기술 개발사업"]
        }
    }

    # 분석 로직
    target_strategy = strategy_db.get("창호") # 키워드 매칭 로직 적용

    # 3. 컨설팅 리포트 화면 구성
    st.divider()
    st.subheader(f"💡 {client_name}을 위한 벤처인증 전략 리포트")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🎯 권장 인증 유형")
        st.write("**혁신성장형 (제조업 특화)**")
    with col2:
        st.info("📂 핵심 기술 테마")
        st.write(f"**{target_strategy['type']}**")
    with col3:
        st.info("📜 필요 지식재산권")
        st.write(f"**{', '.join(target_strategy['patents'])}** 관련 특허")

    # 추천 주제 섹션
    st.write("---")
    st.markdown("### 🚀 추천 벤처확인 기술 주제 (사업계획서용)")
    for i, topic in enumerate(target_strategy['topics']):
        st.success(f"**주제 {i+1}:** {topic}")

    # 연계 지원사업 추천
    with st.expander("💰 연계 가능한 정부지원사업/정책자금"):
        for fund in target_strategy['funds']:
            st.write(f"- {fund}")
