import streamlit as st
from google.cloud import vision
import openai
import json

# --- 1. API 클라이언트 설정 ---
def get_vision_client():
    # Streamlit Secrets에 저장된 Google 키 사용
    key_dict = json.loads(st.secrets["google_cloud_key"])
    return vision.ImageAnnotatorClient.from_service_account_info(key_dict)

def get_gpt_suggestion(biz_item):
    # Streamlit Secrets에 저장된 OpenAI API 키 사용
    openai.api_key = st.secrets["openai_api_key"]
    
    prompt = f"""
    당신은 대한민국 최고의 벤처기업인증 전문 컨설턴트입니다.
    다음 사업 종목을 가진 제조 기업이 '혁신성장형 벤처인증'을 받으려고 합니다.
    
    기업 종목: {biz_item}
    
    위 종목을 바탕으로 벤처인증 통과 가능성이 가장 높은 고부가가치 기술 주제 3가지를 생성해 주세요.
    각 주제는 다음 형식을 지켜주세요:
    1. 주제명: (기술적이고 혁신적인 느낌의 제목)
    2. 핵심기술: (해당 주제에서 강조해야 할 구체적인 기술 포인트)
    3. 기대효과: (생산성 향상, 에너지 절감 등 경제적 이득)
    """

    response = openai.chat.completions.create(
        model="gpt-4o", # 또는 gpt-3.5-turbo
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# --- 2. UI 구성 ---
st.set_page_config(page_title="벤처인증 AI 컨설턴트", layout="wide")
st.title("🚀 AI 기반 벤처인증 전략 생성기")
st.sidebar.info("구글 Vision으로 읽고, GPT-4로 전략을 짭니다.")

uploaded_file = st.file_uploader("사업자등록증 이미지를 업로드하세요", type=["jpg", "png", "jpeg"])

if uploaded_file:
    content = uploaded_file.read()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 업로드된 문서")
        st.image(content, use_container_width=True)

    with col2:
        with st.spinner('구글 AI가 정보를 추출하고 있습니다...'):
            # 1단계: Google Vision OCR로 종목 추출
            client = get_vision_client()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            full_text = response.text_annotations[0].description if response.text_annotations else ""
            
            # 종목 추출 로직 (정규표현식 보완 가능)
            try:
                biz_item = full_text.split("종목")[1].split("\n")[0].replace(":", "").strip()
            except:
                biz_item = st.text_input("종목 인식 실패. 직접 입력해주세요:", "자동차 부품 제조")

        if biz_item:
            st.success(f"🔍 인식된 종목: **{biz_item}**")
            
            with st.spinner('GPT가 맞춤형 전략을 생성 중입니다...'):
                # 2단계: GPT API로 주제 생성
                consulting_result = get_gpt_suggestion(biz_item)
                
                st.divider()
                st.subheader("💡 벤처인증 권장 기술 주제")
                st.markdown(consulting_result)
                
                # 컨설턴트 의견 추가용
                st.text_area("✍️ 현장 상담 기록", placeholder="대표님 미팅 결과 및 향후 추진 일정 기록...")
