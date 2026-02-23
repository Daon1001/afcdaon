import streamlit as st
import google.generativeai as genai
from PIL import Image

def get_gemini_response(image, prompt):
    # API 키 설정
    genai.configure(api_key=st.secrets["gemini_api_key"])
    
    # 404 오류 방지를 위해 모델명을 'models/' 프리픽스를 붙여 명시적으로 호출하거나
    # 최신 SDK 표준인 'gemini-1.5-flash'를 사용합니다.
    try:
        # 시도 1: 표준 모델명
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, image])
    except Exception:
        # 시도 2: 대안 모델명 (버전 호환성 대비)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content([prompt, image])
        
    return response.text

# --- UI 부분은 동일하게 유지 ---
st.set_page_config(page_title="벤처인증 제미나이 컨설턴트", layout="centered")
st.title("♊ 제미나이 벤처인증 전략 생성기")

uploaded_file = st.file_uploader("사업자등록증 이미지 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="업로드된 이미지", width=400)
    
    if st.button("제미나이 분석 시작"):
        with st.spinner('제미나이가 분석 중입니다...'):
            try:
                prompt = """
                당신은 대한민국 벤처기업인증 전문 컨설턴트입니다.
                이미지에서 '업태'와 '종목'을 추출하고, 
                '혁신성장형 벤처인증'을 받기 위한 3가지 핵심 기술 주제를 제안하세요.
                [업태/종목 정보, 주제명, 핵심기술, 기대효과]를 포함해 주세요.
                """
                result = get_gemini_response(img, prompt)
                st.markdown(result)
            except Exception as e:
                st.error(f"연결 오류: {e}\n\nAI Studio에서 'Gemini API'가 활성화된 새 키를 발급받아보세요.")
