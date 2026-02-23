import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. API 설정 및 모델 호출 함수 ---
def get_gemini_response(image, prompt):
    genai.configure(api_key=st.secrets["gemini_api_key"])
    # 404 에러 방지를 위해 명시적인 모델 경로 사용
    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    response = model.generate_content([prompt, image])
    return response.text

# --- 2. UI 레이아웃 ---
st.set_page_config(page_title="벤처인증 AI 컨설턴트", layout="wide")
st.title("🛠️ 제조업 벤처인증 전략 및 사업요약서 생성기")

# 세션 상태 초기화 (단계별 진행을 위해)
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = ""

# --- STEP 1: 이미지 업로드 및 주제 제안 ---
uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file and st.session_state.step == 1:
    img = Image.open(uploaded_file)
    st.image(img, width=400)
    
    if st.button("1단계: 기술 주제 제안받기"):
        with st.spinner('제미나이가 종목을 분석하고 주제를 생성 중입니다...'):
            try:
                prompt = """
                이미지에서 업태와 종목을 추출하고, 이 기업이 벤처인증을 받기 위해 필요한 
                혁신적인 기술 주제 3가지를 '주제 1: 제목' 형식으로 제안해줘. 
                제목은 전문적인 기술 용어를 섞어서 멋지게 지어줘.
                """
                st.session_state.suggestions = get_gemini_response(img, prompt)
                st.session_state.step = 2
                st.rerun()
            except Exception as e:
                st.error(f"연결 오류 발생: {e}. API 키와 라이브러리 버전을 확인하세요.")

# --- STEP 2: 주제 선택 및 요약서 완성 ---
if st.session_state.step == 2:
    st.success("✅ 주제 제안이 완료되었습니다.")
    st.markdown("### 💡 AI 추천 기술 주제")
    st.info(st.session_state.suggestions)
    
    st.divider()
    selected_topic = st.text_input("위 주제 중 대표님과 상의한 '확정 주제'를 입력하세요 (또는 직접 입력)")

    if st.button("2단계: 벤처인증 표준 양식 작성"):
        if not selected_topic:
            st.warning("주제를 입력해 주세요.")
        else:
            with st.spinner('선택한 주제로 사업요약서를 작성 중입니다...'):
                img = Image.open(uploaded_file)
                form_prompt = f"""
                당신은 벤처인증 전문 컨설턴트입니다. 선택된 주제 [{selected_topic}]를 바탕으로 
                아래 양식의 빈칸(___________)을 전문적인 용어로 채워 완성된 리포트를 만들어주세요.
                
                [작성 양식]
                - 신청기술(제품/서비스)명 : {selected_topic}
                - 신청기술(제품/서비스) 요약 : (이 기술에 대한 혁신적인 요약 3줄)

                V 기존 시장에 ___________니즈(문제)가 있는데, ___________한 이유로 사람들이 여전히 불편을 겪고 있음
                V 당사에서 ___________한 방식으로 해결책을 찾았으며, 이는 기존시장의 기술과 ___________ 차이를 보유함
                V 현재 당사가 보유한 기술명은 {selected_topic}로써, 전체 시장은 ___________ 규모이며 연평균 ___%의 성장을 기대함
                V 당사 기술은 ___________에 기반하여 ___________한 특징을 갖고 있으며 혁신적인 해결책임
                V 기술에 대한 특허 등 ___ 건의 지식재산권과 ___명의 연구개발조직을 보유하여 기술력을 입증함
                V 마케팅을 위해 ___________ 활동을 진행중이며 향후 3년간 ___________ 계획임
                V 이러한 성과가 가능한 이유는 당사에 ___________한 역량이 있기 때문이며 향후 ___년간 ___________ 성장을 해낼 것임
                """
                final_text = get_gemini_response(img, form_prompt)
                st.session_state.final_report = final_text
                st.session_state.step = 3
                st.rerun()

# --- STEP 3: 최종 결과 확인 및 복사 ---
if st.session_state.step == 3:
    st.subheader("📝 완성된 벤처인증 사업요약서")
    st.markdown(st.session_state.final_report)
    
    if st.button("처음부터 다시 시작"):
        st.session_state.step = 1
        st.rerun()
