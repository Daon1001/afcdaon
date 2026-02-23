import streamlit as st
import openai
import base64

# --- 1. 이미지 처리 함수 ---
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

def get_venture_consulting(base64_image):
    openai.api_key = st.secrets["openai_api_key"]
    
    # GPT-4o에게 이미지 분석과 주제 생성을 한 번에 요청
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": """
                        이 사업자등록증 이미지에서 '업태'와 '종목'을 찾아내고, 
                        해당 기업이 벤처인증(혁신성장형)을 받기 위해 도전할만한 
                        최신 기술 주제 3가지를 제안해줘.
                        
                        [응답 양식]
                        - 추출된 업종: (업태 / 종목)
                        - 추천 주제 1: (주제명 / 핵심기술 / 기대효과)
                        - 추천 주제 2: (주제명 / 핵심기술 / 기대효과)
                        - 추천 주제 3: (주제명 / 핵심기술 / 기대효과)
                    """},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    },
                ],
            }
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content

# --- 2. UI 구성 ---
st.set_page_config(page_title="벤처인증 AI 컨설턴트", layout="centered")
st.title("🚀 원클릭 벤처인증 전략 생성기")
st.write("사업자등록증 사진 한 장으로 벤처 테마를 제안받으세요.")

uploaded_file = st.file_uploader("사업자등록증 이미지 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="업로드된 이미지", width=400)
    
    if st.button("AI 분석 시작"):
        with st.spinner('이미지를 분석하고 전략을 생성 중입니다...'):
            try:
                # 이미지 인코딩 및 GPT 호출
                base64_img = encode_image(uploaded_file)
                result = get_venture_consulting(base64_img)
                
                st.divider()
                st.markdown("### 📋 AI 컨설팅 결과")
                st.markdown(result)
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
