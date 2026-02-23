import streamlit as st
import random

# 벤처인증의 5대 혁신 키워드 (제조업 공통)
INNOVATION_TYPES = {
    "신소재/고기능화": "기존 제품 대비 내구성, 경량화 또는 신소재를 적용한 차세대 제품 개발",
    "공정 자동화/지능화": "생산성 향상을 위한 로봇 연동, 자동 펀칭, 후공정 자동화 시스템 도입",
    "친환경/에너지절감": "탄소 배출 저감 공정 또는 에너지 효율을 극대화한 제품 라인업 구축",
    "스마트/IoT 융합": "제품에 센서 및 모니터링 기술을 접합하여 데이터 기반 관리 솔루션 제공",
    "안전/품질 혁신": "작업자 안전 확보 시스템 또는 AI 기반의 비정형 불량 검사 자동화"
}

def generate_venture_themes(item_name):
    """
    어떤 종목이 들어와도 5가지 벤처 주제를 생성하는 함수
    """
    themes = [
        f"AI 기반의 {item_name} 제조 공정 최적화 및 스마트 팩토리 시스템",
        f"친환경 소재를 적용한 고부가가치 {item_name} 제품화 기술",
        f"생산성 200% 향상을 위한 {item_name} 전용 자동화 라인 및 통합 제어 솔루션",
        f"IoT 센서 융합형 {item_name} 유지보수 및 예지보전 플랫폼",
        f"수출 경쟁력 확보를 위한 고기능성/초정밀 {item_name} 가공 기술 개발"
    ]
    return themes

st.title("🚀 전 업종 대응 벤처인증 자동 추천 시스템")
st.write("사업자등록증의 '종목'을 분석하여 최적의 벤처 인증 테마 5가지를 즉시 제안합니다.")

# 1. 업로드 및 텍스트 인식 (OCR 시뮬레이션)
uploaded_file = st.file_uploader("사업자등록증을 업로드하세요", type=["jpg", "png", "pdf"])

if uploaded_file:
    # 실제 OCR 적용 시 이 부분에서 텍스트를 추출합니다.
    # 현재는 사용자 편의를 위해 추출된 종목을 확인하는 창으로 구성합니다.
    st.success("이미지 스캔 완료!")
    
    # OCR이 읽어온 가상의 종목명 (실제 배포시엔 OCR 결과값이 들어감)
    detected_item = st.text_input("인식된 종목 (수정 가능):", value="PVC 창호 및 금속 가공")

    if detected_item:
        st.divider()
        st.subheader(f"💡 '{detected_item}' 분야 벤처인증 유망 주제 (5가지)")
        
        # 5가지 주제 생성
        recommended_themes = generate_venture_themes(detected_item)
        
        for i, theme in enumerate(recommended_themes):
            with st.expander(f"추천 {i+1}: {theme}"):
                # 벤처 유형 자동 매칭 설명
                innovation_key = list(INNOVATION_TYPES.keys())[i % 5]
                st.write(f"**📌 인증 유형:** {innovation_key}")
                st.write(f"**📝 기술 핵심:** {INNOVATION_TYPES[innovation_key]}")
                st.write(f"**🎯 기대 효과:** 기술적 차별성을 강조하여 '혁신성장유형' 인증 가능성 극대화")
                if st.button(f"팀 보고서에 담기 (주제 {i+1})"):
                    st.toast(f"'{theme}' 저장 완료!")

# 2. 팀원 협업 대시보드 (하단)
st.sidebar.title("👥 팀 협업 현황")
st.sidebar.info("현재 3명의 팀원이 접속 중입니다.")
st.sidebar.write("- 허자현: (주)OO제조 분석 완료")
st.sidebar.write("- 김철수: XX산업 테마 선정 중")
