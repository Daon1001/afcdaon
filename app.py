import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. Gemini 설정 및 호출 ---
def get_gemini_response(image, prompt):
    # API 키 설정
    genai.configure(api_key=st.secrets["gemini_api_key"])
    
    # 모델명 후보들을 시도하여 가장 안정적인 모델로 연결
    # 최신 SDK에서는 'gemini-1.5-flash'를 기본으로 사용합니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 이미지와 텍스트를 함께 전달
    response = model.generate_content([prompt, image])
    return response.text

# --- 2. UI 구성 ---
st.set_page_config(page_title="벤처인증 제미나이 컨설턴트", layout="centered")
st.title("♊ 제미나이 벤처인증 전략 생성기")

uploaded_file = st.file_uploader("사업자등록증 이미지 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="업로드된 이미지", width=400)
    
    if st.button("제미나이 분석 시작"):
        with st.spinner('제미나이가 이미지를 읽고 전략을 짜는 중입니다...'):
            try:
                # 컨설턴트님의 요구사항을 담은 프롬프트
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
                # 만약 또 404가 난다면 사용 가능한 모델 리스트를 출력해주는 안내문
                st.error(f"모델 연결 오류가 발생했습니다. API 키가 활성화되었는지 확인해 주세요. 오류 내용: {e}")
