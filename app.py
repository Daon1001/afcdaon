import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. Gemini 설정 ---
def get_gemini_response(image, prompt):
    # Streamlit Secrets에 저장된 Gemini API 키 설정
    genai.configure(api_key=st.secrets["gemini_api_key"])
    
    # 제미나이 1.5 플래시 모델 사용 (속도가 빠르고 무료 구간이 넉넉함)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    response = model.generate_content([prompt, image])
    return response.text

# --- 2. UI 구성 ---
st.set_page_config(page_title="벤처인증 제미나이 컨설턴트", layout="centered")
st.title("♊ 제미나이 벤처인증 전략 생성기")
st.write("구글의 최신 AI 제미나이가 사업자등록증을 분석합니다.")

uploaded_file = st.file_uploader("사업자등록증 이미지 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="업로드된 이미지", width=400)
    
    if st.button("제미나이 분석 시작"):
        with st.spinner('제미나이가 이미지를 읽고 전략을 짜는 중입니다...'):
            try:
                prompt = """
                당신은 대한민국 벤처기업인증 전문 컨설턴트입니다.
                첨부된 사업자등록증 이미지에서 '업태'와 '종목'을 추출하고, 
                이 기업이 '혁신성장형 벤처인증'을 받기 위해 필요한 3가지 핵심 기술 주제를 제안하세요.
                
                [응답 양식]
                1. 추출된 업종 정보 (업태/종목)
                2. 주제 1: (주제명, 핵심기술, 기대효과)
                3. 주제 2: (주제명, 핵심기술, 기대효과)
                4. 주제 3: (주제명, 핵심기술, 기대효과)
                5. 컨설턴트 한줄평: (인증 통과를 위한 팁)
                """
                
                result = get_gemini_response(img, prompt)
                
                st.divider()
                st.markdown("### 📋 제미나이 컨설팅 리포트")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
