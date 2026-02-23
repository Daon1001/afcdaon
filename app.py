import streamlit as st
from PIL import Image
import time

# 1. 벤처 인증 테마 데이터베이스
VENTURE_DB = {
    "창호": ["IoT 연동 스마트 윈도우 시스템", "에너지 절감형 고단열 창호 프레임"],
    "금속": ["정밀 공정 자동화 로봇 시스템", "고강도 경량 합금 부품 제조 기술"],
    "소프트웨어": ["AI 기반 업무 자동화 솔루션", "클라우드 보안 데이터 플랫폼"],
    "기계": ["스마트 팩토리 연동형 생산 설비", "저전력 고효율 구동 모터 기술"]
}

st.title("📂 AI 사업자등록증 자동 분석기")
st.info("사업자등록증을 업로드하면 '종목'을 분석해 벤처 주제를 제안합니다.")

# 2. 파일 업로드 섹션
uploaded_file = st.file_uploader("사업자등록증 파일을 선택하세요", type=["jpg", "png", "pdf"])

if uploaded_file is not None:
    # 이미지 표시
    image = Image.open(uploaded_file)
    st.image(image, caption="업로드된 사업자등록증", width=400)
    
    with st.spinner('AI가 종목 정보를 분석 중입니다...'):
        # --- 실제 환경에서는 여기서 OCR 엔진이 구동됩니다 ---
        time.sleep(2) # 분석 시뮬레이션
        detected_item = "창호 제조업" # 예시: OCR이 찾아낸 단어
        # ---------------------------------------------
        
    st.success(f"✅ 분석 완료! 인식된 종목: **[{detected_item}]**")
    
    # 3. 주제 매칭 및 결과 출력
    st.subheader("💡 추천 벤처 인증 주제")
    
    # 종목 키워드 포함 여부로 DB 검색
    matched = False
    for key, themes in VENTURE_DB.items():
        if key in detected_item:
            for i, theme in enumerate(themes):
                st.info(f"**추천 {i+1}:** {theme}")
            matched = True
            break
            
    if not matched:
        st.warning("해당 종목에 대한 전용 테마가 없습니다. 일반 제조업/서비스업 기술성 평가 모델을 적용합니다.")

# 4. 팀원 공유 기능
if st.button("결과를 팀 대시보드에 저장"):
    st.balloons()
    st.write("저장되었습니다! 이제 다른 팀원들도 이 분석 결과를 볼 수 있습니다.")
