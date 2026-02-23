import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")
st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

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

# --- 2. UI 레이아웃 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 추천")
    uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=300)
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('종목 분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 전문적인 제목으로 제안해줘."
                response = model.generate_content([prompt, img])
                st.session_state.suggestions = response.text
    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하거나 왼쪽에서 복사하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 상세 리포트를 설계 중입니다...'):
                form_prompt = f"""
                신청기술 [{selected_topic}]에 대해 다음 항목들을 각각 전문적인 문체로 상세히 작성하세요. 
                각 항목은 공백 포함 700자 내외의 풍부한 분량이어야 합니다.
                각 항목의 구분은 반드시 '### [항목명]' 형식을 유지하세요.

                ### [1. 신청기술 요약 및 표준 양식]
                (V형태 양식 포함)
                ### [2. 개발배경 및 원인분석]
                (산업 구조적 문제 분석)
                ### [3. 경쟁력 확보방안]
                (기술적 차별성 및 진입장벽 구축)
                ### [4. 추진경과 및 향후 계획]
                (R&D 실적 및 3개년 로드맵)
                ### [5. 목표시장 및 고객정의]
                (시장 규모 및 성장률 근거)
                ### [6. 경쟁사 분석 및 우위성]
                (기존 방식 한계점 대비 우위성)
                ### [7. 시장진입 및 확대전략 - 추진경과]
                (현재까지의 마케팅 및 유통 실적)
                ### [8. 시장진입 및 확대전략 - 향후계획]
                (향후 3개년 점유율 확대 로드맵)
                ### [9. 지식재산권 및 특허 전략]
                (추천 특허 3종 명칭 및 핵심 청구항 아이디어, 방어 전략)
                ### [10. 자금조달 계획의 구체적 방안]
                (자금 선순환 구조 및 재무 확보 전략)
                ### [11. 연계 가능 정책자금 추천]
                (중진공/기보/신보 자금 및 선정 포인트)
                """
                try:
                    if uploaded_file:
                        response = model.generate_content([form_prompt, Image.open(uploaded_file)])
                    else:
                        response = model.generate_content(form_prompt)
                    
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# --- 3. 결과 출력 (드롭박스 형태) ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 항목별 상세 컨설팅 리포트")
    
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("전체 리포트 다운로드(.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        lines = section.split('\n')
        title = lines[0].strip('[] ')
        content = '\n'.join(lines[1:]).strip()
        
        with st.expander(f"📌 {title}", expanded=False):
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; line-height: 1.8; border-left: 5px solid #007bff;">
                {content.replace('\n', '<br>')}
            </div>
            """, unsafe_allow_html=True)
