import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. [유지] 동적 모델 할당 로직 ---
try:
    API_KEY = st.secrets["gemini_api_key"] 
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

model = genai.GenerativeModel(target_model_name)
st.sidebar.success(f"✅ 가동 중인 AI 엔진: **{target_model_name}**")

# --- 2. 세션 상태 관리 ---
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = ""
if 'final_report' not in st.session_state:
    st.session_state.final_report = ""

# --- 3. UI 레이아웃 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 주제 추천 및 분석")
    uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=300)
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 전문적인 제목으로 제안해줘."
                try:
                    response = model.generate_content([prompt, img])
                    st.session_state.suggestions = response.text
                except Exception as e:
                    st.error(f"오류: {e}")

    if st.session_state.suggestions:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 리포트 생성 (요약 + 심층 분석)")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하거나 왼쪽에서 복사하세요.")
    
    if st.button("전문 컨설팅 리포트 생성 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('700자 분량의 심층 분석을 포함한 리포트를 작성 중입니다...'):
                # 섹션 2의 분량을 700자 내외로 유도하는 강화된 프롬프트
                form_prompt = f"""
                당신은 벤처인증 전문 컨설턴트입니다. [{selected_topic}] 주제에 대해 다음 두 섹션을 작성하세요.

                ### [섹션 1: 사업요약서 표준 양식]
                (이 섹션은 기존 양식에 맞춰 핵심만 작성하세요)
                - 신청기술명 : {selected_topic}
                - 신청기술 요약 : (혁신성 위주의 3줄 요약)
                V 기존 시장에 ___________니즈가 있는데, ___________한 이유로 여전히 불편을 겪음
                V 당사에서 ___________한 방식으로 해결책을 찾았으며, 기존과 ___________ 차이가 있음
                V 시장규모는 ___________이며 연평균 ___% 성장을 기대함
                V 당사 기술은 ___________에 기반하여 혁신적인 해결책을 제시함
                V 지식재산권 ___건과 연구인력 ___명을 보유함
                V 향후 3년간 ___________ 마케팅 계획을 수립함

                ### [섹션 2: 개발 배경 및 원인 분석 (공백 포함 700자 내외)]
                이 섹션은 심사위원이 기술 개발의 절실함을 느낄 수 있도록 아주 구체적이고 논리적으로 작성하세요.
                1. 개발 배경(동기): 현재 해당 산업계가 직면한 거시적 환경 변화(인건비, 규제, 글로벌 트렌드 등)와 이로 인한 기업들의 실질적인 고민을 서술하세요.
                2. 배경의 원인: 위와 같은 문제가 해결되지 않고 지속된 근본 원인을 '기술적 한계', '구조적 문제', '시장 데이터 부재' 등의 관점에서 3가지 항목으로 상세히 분석하세요. 
                (전체적으로 전문 용어를 사용하고 문장을 풍부하게 구성하여 분량을 확보하세요.)
                """
                try:
                    if uploaded_file:
                        img = Image.open(uploaded_file)
                        response = model.generate_content([form_prompt, img])
                    else:
                        response = model.generate_content(form_prompt)
                    st.session_state.final_report = response.text
                except Exception as e:
                    st.error(f"오류: {e}")

# --- 4. 결과 출력 및 다운로드 ---
st.divider()
if st.session_state.final_report:
    st.subheader("📄 벤처인증용 통합 컨설팅 리포트")
    st.download_button("리포트 다운로드(.txt)", st.session_state.final_report, file_name="venture_report.txt")
    st.markdown(st.session_state.final_report)
