import streamlit as st
from PIL import Image
import pytesseract  # 무료 OCR 라이브러리 (설치 필요)
import re

# --- 1. 배경 로직: 키워드 기반 전략 DB ---
def get_venture_strategy(biz_item):
    db = {
        "기계": {"theme": "지능형 자동화 시스템", "topics": ["AI 기반 정밀 제어 제조 공정", "IoT 연동 스마트 설비"]},
        "창호": {"theme": "고효율 친환경 건축소재", "topics": ["에너지 절감형 하이브리드 창호", "탄소저감형 PVP 프레임"]},
        "식품": {"theme": "바이오 푸드테크", "topics": ["천연 보존 기술 기반 기능성 식품", "스마트 패키징 가공 공정"]},
        "전자": {"theme": "차세대 임베디드 시스템", "topics": ["저전력 고효율 회로 설계", "센서 융합 데이터 처리 장치"]}
    }
    for key, val in db.items():
        if key in biz_item: return val
    return {"theme": "제조 공정 혁신", "topics": [f"{biz_item} 공정 최적화 기술", "신소재 기반 제품 고도화"]}

# --- 2. OCR 기능: 이미지에서 텍스트 추출 ---
def extract_biz_info(image):
    # 실제 서비스 시에는 Naver CLOVA OCR이나 Google Vision API를 쓰면 정확도가 99%입니다.
    # 여기서는 로직 설명을 위해 Tesseract 예시를 듭니다.
    text = pytesseract.image_to_string(image, lang='kor')
    
    # 정규표현식으로 '업태'와 '종목' 옆의 글자 추출 (간이 로직)
    biz_type = re.search(r"업\s*태\s*[:\s]*([^\n]+)", text)
    biz_item = re.search(r"종\s*목\s*[:\s]*([^\n]+)", text)
    
    return {
        "type": biz_type.group(1).strip() if biz_type else "추출 실패",
        "item": biz_item.group(1).strip() if biz_item else "직접 입력 필요"
    }

# --- 3. Streamlit UI 구성 ---
st.set_page_config(page_title="제조업 벤처인증 AI", layout="wide")
st.title("📸 사업자등록증 자동 분석 벤처 컨설팅")

uploaded_file = st.file_uploader("사업자등록증 사진을 찍거나 업로드하세요", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="업로드된 이미지", width=400)
    
    with st.spinner("이미지에서 사업 정보를 분석 중입니다..."):
        # 실제 환경에서는 아래 함수가 OCR API를 호출합니다.
        # 가상의 추출 결과 (테스트용)
        extracted = {"type": "제조업", "item": "자동차 부품 및 금속 가공"} 
        # extracted = extract_biz_info(img) # 실제 OCR 연동 시 활성화
        
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📋 인식된 기업 정보")
        final_item = st.text_input("분석된 종목 (수정 가능)", extracted['item'])
        st.write(f"**추출된 업태:** {extracted['type']}")
        
    with col2:
        st.subheader("🚀 맞춤형 벤처 테마")
        strategy = get_venture_strategy(final_item)
        st.info(f"**추천 기술 분야:** {strategy['theme']}")
        
    st.markdown("### 💡 추천 벤처확인 기술 주제")
    for topic in strategy['topics']:
        st.success(f"✅ {topic}")

    # 컨설턴트 메모 기능
    st.text_area("컨설팅 상담 메모", placeholder="대표님의 기술 확보 의지가 높음. 특허 2건 출원 제안함.")
