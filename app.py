import streamlit as st
import pandas as pd

# 1. 가상의 벤처 테마 데이터베이스 (업종별 매칭 테이블)
VENTURE_DB = {
    "창호 제조업": ["IoT 연동 스마트 윈도우 시스템", "친환경 재생 수지 활용 고단열 프레임", "에너지 제로 하우스용 진공 유리"],
    "금속 가공업": ["AI 기반 정밀 금형 설계 자동화", "고강도 경량 마그네슘 합금 부품", "로봇 협동 공정 최적화 솔루션"],
    "소프트웨어": ["B2B SaaS 기업용 탄소배출 관리 시스템", "생성형 AI 기반 법률 문서 분석 플랫폼", "블록체인 기반 공급망 투명성 확보"]
}

st.set_page_config(page_title="벤처인증 테마 추천 시스템", layout="wide")
st.title("🚀 벤처인증 유망 주제 검색 & 협업 툴")

# 사이드바: 팀원 선택 및 메뉴
st.sidebar.header("Team Workspace")
user_name = st.sidebar.selectbox("담당 팀원 선택", ["허자현 팀장", "김철수 대리", "이영희 사원"])

# 메인 기능 탭
tab1, tab2 = st.tabs(["🔍 종목 분석 및 추천", "📊 팀 히스토리 공유"])

with tab1:
    st.subheader("사업자등록증 업로드 및 종목 분석")
    uploaded_file = st.file_uploader("사업자등록증 이미지(JPG, PNG)를 업로드하세요.", type=["jpg", "png", "pdf"])
    
    # 예시를 위해 직접 입력 기능 추가
    target_item = st.text_input("또는 분석할 '종목명'을 직접 입력하세요 (예: 창호 제조업)")
    
    if st.button("벤처인증 유망 주제 추출"):
        if target_item:
            st.success(f"'{target_item}' 종목에 적합한 벤처인증 주제를 찾았습니다!")
            
            # DB 매칭 로직 (간이형)
            results = VENTURE_DB.get(target_item, ["신규 분야: 기술성 분석 및 특허 선행 조사가 필요합니다."])
            
            for i, theme in enumerate(results):
                with st.expander(f"추천 주제 {i+1}: {theme}"):
                    st.write("✅ **핵심 기술:** 해당 분야의 독창적 알고리즘 또는 신소재 적용")
                    st.write("📈 **사업 확장성:** 국내외 시장 규모 000억 원대 시장 진입 가능성")
                    if st.button(f"주제 {i+1} 저장하기", key=f"btn_{i}"):
                        st.info("팀 대시보드에 저장되었습니다.")
        else:
            st.warning("종목명을 입력하거나 파일을 업로드해주세요.")

with tab2:
    st.subheader("전체 팀원 분석 현황")
    # 샘플 데이터 (실제로는 DB나 Google Sheet 연동)
    data = {
        "날짜": ["2026-02-21", "2026-02-22", "2026-02-23"],
        "담당자": ["김철수", "이영희", "허자현"],
        "업체명": ["(주)가나다창호", "에이비씨소프트", "진성금속"],
        "선정주제": ["스마트 윈도우 센서", "AI 보안 솔루션", "공정 자동화 로봇"],
        "진행상태": ["서류준비", "검토중", "인증완료"]
    }
    df = pd.DataFrame(data)
    st.table(df)
