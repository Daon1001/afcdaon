import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 컨설턴트", layout="wide")
st.title("🛡️ 제조업 벤처인증 전략 및 사업요약서 생성기")

# --- 1. 대표님표 강력한 API 및 모델 자동 스캐너 ---
try:
    # 대소문자 주의: Secrets에 설정된 이름과 똑같아야 합니다.
    API_KEY = st.secrets["gemini_api_key"] # 소문자로 통일했습니다.
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ 비밀 금고(Secrets)에서 API 키를 찾을 수 없습니다.")
    st.stop()

available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
except Exception as e:
    st.error(f"⚠️ 구글 AI 서버 통신 오류: {e}")
    st.stop()

target_model_name = ""
for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision', 'gemini-pro']:
    if preferred in available_models:
        target_model_name = preferred
        break

if not target_model_name and available_models:
    target_model_name = available_models[0]

if not target_model_name:
    st.error(f"⚠️ 연결 가능한 AI 모델이 없습니다.\n- 감지된 목록: {available_models}")
    st.stop()

# 동적으로 찾은 최적의 모델 객체 생성
model = genai.GenerativeModel(target_model_name)
st.sidebar.success(f"✅ 가동 중인 AI 엔진:\n**{target_model_name}**")

# --- 2. 세션 상태 관리 ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = ""

# --- 3. 메인 컨설팅 로직 ---
uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "jpeg"])

if uploaded_file and st.session_state.step == 1:
    img = Image.open(uploaded_file)
    st.image(img, width=400)
    
    if st.button("1단계: 기술 주제 제안받기", type="primary"):
        with st.spinner(f'{target_model_name} 엔진이 종목을 분석 중입니다...'):
            try:
                prompt = """
                사업자등록증에서 업태와 종목을 읽고, 벤처인증(혁신성장형)을 받기에 유리한 
                기술 주제 3가지를 '주제 1: [제목]' 형식으로 제안해줘.
                제목은 제조업의 혁신성이 드러나도록 전문적으로 지어줘.
                """
                response = model.generate_content([prompt, img])
                st.session_state.suggestions = response.text
                st.session_state.step = 2
                st.rerun()
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")

# --- 4. 주제 선택 및 사업요약서 자동 완성 ---
if st.session_state.step == 2:
    st.markdown("### 💡 AI 추천 기술 주제")
    st.info(st.session_state.suggestions)
    
    st.divider()
    selected_topic = st.text_input("위 주제 중 확정할 '기술 주제명'을 입력하세요.")

    if st.button("2단계: 표준 양식으로 사업요약서 자동 완성", type="primary"):
        if not selected_topic:
            st.warning("주제를 입력해 주세요.")
        else:
            with st.spinner('전문 컨설팅 리포트를 작성 중입니다...'):
                img = Image.open(uploaded_file)
                form_prompt = f"""
                당신은 벤처인증 전문 컨설턴트입니다. 선택된 주제 [{selected_topic}]를 바탕으로 
                아래 양식의 빈칸(___________)을 전문적인 용어로 가득 채워 완성해 주세요.
                
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
                response = model.generate_content([form_prompt, img])
                st.session_state.final_report = response.text
                st.session_state.step = 3
                st.rerun()

# --- 5. 최종 결과 출력 ---
if st.session_state.step == 3:
    st.subheader("📝 완성된 벤처인증 사업요약서 (초안)")
    st.markdown(st.session_state.final_report)
    
    if st.button("처음으로 돌아가기"):
        st.session_state.step = 1
        st.rerun()
