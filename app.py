import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. API 설정 및 모델 진단
def initialize_gemini():
    api_key = st.secrets["gemini_api_key"]
    genai.configure(api_key=api_key)
    
    # 사용 가능한 모델 리스트 스캔
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    return available_models

# 2. UI 구성
st.set_page_config(page_title="벤처인증 AI 진단 도구", layout="wide")
st.title("🔍 벤처인증 AI 시스템 진단 및 컨설팅")

# 시스템 진단 정보 표시
with st.expander("🛠️ 시스템 연결 상태 확인 (로그)"):
    try:
        models = initialize_gemini()
        st.write("✅ 연결 성공! 사용 가능한 모델 목록:")
        st.code(models)
        
        # 가장 적합한 모델 자동 선택 로직
        if 'models/gemini-1.5-flash' in models:
            target_model = 'gemini-1.5-flash'
        elif 'models/gemini-pro' in models:
            target_model = 'gemini-pro'
        else:
            target_model = models[0] if models else None
        
        st.success(f"현재 최적의 연결 모델: **{target_model}**")
    except Exception as e:
        st.error(f"연결 실패: {e}")
        target_model = None

st.divider()

# 3. 메인 분석 기능
uploaded_file = st.file_uploader("사업자등록증 이미지 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file and target_model:
    img = Image.open(uploaded_file)
    st.image(img, caption="업로드된 이미지", width=400)
    
    if st.button("벤처인증 전략 생성"):
        with st.spinner(f'{target_model} 엔진으로 분석 중...'):
            try:
                model = genai.GenerativeModel(target_model)
                prompt = "사업자등록증의 업태/종목을 분석하여 벤처인증용 기술 주제 3개를 제안해줘."
                
                # 이미지와 프롬프트 전송 (모델별 대응)
                response = model.generate_content([prompt, img])
                st.markdown("### 📋 AI 컨설팅 리포트")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"실행 중 오류 발생: {e}")
