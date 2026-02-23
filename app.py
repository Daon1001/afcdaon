import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. API 및 모델 설정 ---
def get_gemini_response(image, prompt):
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([prompt, image])
    return response.text

# --- 2. UI 구성 ---
st.set_page_config(page_title="벤처인증 전략 수립 툴", layout="wide")
st.title("📄 벤처인증 기술주제 제안 및 요약서 자동화")

if "step2" not in st.session_state:
    st.session_state.step2 = False

uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    if not st.session_state.step2:
        if st.button("1단계: 기술 주제 제안받기"):
            with st.spinner('분석 중...'):
                prompt = """
                이미지에서 업태/종목을 추출하고, 벤처인증용 기술 주제 3개를 짧은 제목 형태로 제안해줘.
                각 주제는 '주제 1: [제목]' 형식으로 작성해줘.
                """
                st.session_state.suggestions = get_gemini_response(img, prompt)
                st.session_state.step2 = True
                st.rerun()

# --- 3. 주제 선택 및 양식 작성 ---
if st.session_state.step2:
    st.markdown("### 💡 제안된 기술 주제")
    st.write(st.session_state.suggestions)
    
    selected_topic = st.text_input("위 주제 중 마음에 드는 주제명을 입력하거나 복사해 주세요.")
    
    if st.button("2단계: 표준 양식으로 요약서 생성"):
        with st.spinner('사업요약서를 작성 중입니다...'):
            form_prompt = f"""
            선택된 주제: {selected_topic}
            
            위 주제를 바탕으로 아래 [양식]의 빈칸(___________)을 전문적인 비즈니스 용어를 사용하여 채워줘. 
            내용은 구체적이고 혁신 성장성이 돋보이게 작성할 것.
            
            [양식]
            - 신청기술(제품/서비스)명 : {selected_topic}
            - 신청기술(제품/서비스) 요약 : (이 주제에 대한 2~3줄 요약)
            
            V 기존 시장에 ___________니즈(문제)가 있는데, ___________한 이유로 사람들이 여전히 불편을 겪고 있음
            V 당사에서 ___________한 방식으로 해결책을 찾았으며, 이는 기존시장의 기술과 ___________ 차이를 보유함
            V 현재 당사가 개발중인 기술명은 {selected_topic}로써, 전체 시장은 ___________ 규모이며 연평균 ___%의 성장을 기대함
            V 당사 기술은 ___________에 기반하여 ___________한 특징을 갖고 있으며 혁신적인 해결책임
            V 기술에 대한 특허 등 ___ 건의 지식재산권과 ___명의 연구조직을 보유함
            V 마케팅을 위해 ___________ 활동을 진행중이며 향후 3년간 ___________ 계획임
            V 이러한 성과가 가능한 이유는 당사에 ___________한 역량이 있기 때문이며 향후 ___년간 ___________ 성장을 해낼 것임
            """
            
            final_report = get_gemini_response(img, form_prompt)
            st.divider()
            st.subheader("📝 완성된 사업요약서 초안")
            st.info("이 내용을 복사하여 벤처확인종합관리시스템에 활용하세요.")
            st.markdown(final_report)
            
            if st.button("처음으로 돌아가기"):
                st.session_state.step2 = False
                st.rerun()
