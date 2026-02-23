import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")
st.title("🏛️ 벤처인증 · 특허 · 정책자금 통합 컨설팅 리포트")

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
    st.subheader("1️⃣ 이미지 분석 및 주제 추천")
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
    st.subheader("2️⃣ 통합 컨설팅 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하거나 왼쪽에서 복사하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 자금 로드맵까지 설계 중입니다...'):
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 및 정책자금 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 항목들을 공백 포함 각 700자 내외로 풍부하게 작성하세요.

                [작성 항목]
                1. **신청기술 요약 및 표준 양식**: (V형태 양식 포함)
                2. **개발배경(동기) 및 원인분석**: (산업 구조적 문제 분석)
                3. **경쟁력 확보방안**: (기술적 차별성 및 진입장벽)
                4. **추진경과**: (현재까지의 R&D 및 지식재산권 확보 실적)
                5. **향후 3년간 추진계획**: (연도별 상용화 로드맵)
                6. **목표시장 및 고객정의**: (확보할 시장 규모 및 성장률 근거)
                7. **경쟁사 분석**: (기존 방식 대비 당사 기술의 우위성)
                8. **시장진입 및 확대전략 - 추진경과/향후계획**: (마케팅 실적 및 3개년 점유율 확대 전략)
                9. **자금조달 계획의 구체적 방안**: (자금 선순환 구조 설계)
                10. **지식재산권 확보 전략 제안**: (등록 가능한 특허 명칭 3가지 및 핵심 청구항 아이디어)
                
                [보너스 섹션: 연계 가능한 정책자금 추천]
                - 벤처인증 획득 후 해당 기술로 신청 가능한 **정부 정책자금 3가지**를 추천하세요. (예: 중진공 창업기반자금, 기보 벤처평가보증, 혁신성장자금 등)
                - 각 자금별 신청 적기와 예상되는 지원 규모, 그리고 선정 확률을 높이기 위한 핵심 포인트를 전문가적 시선에서 제안하세요.

                [문체 지침]
                - 베테랑 컨설턴트가 직접 상담하는 듯한 전문적이고 신뢰감 있는 문체를 사용하세요.
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

# --- 3. 결과 출력 및 다운로드 ---
st.divider()
if 'final_report' in st.session_state:
    st.subheader("📄 벤처인증 · 특허 · 정책자금 통합 마스터 리포트")
    st.download_button("리포트 다운로드(.txt)", st.session_state.final_report, file_name="venture_finance_report.txt")
    
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 15px; border-left: 10px solid #0056b3; line-height: 1.8;">
        {st.session_state.final_report.replace('\n', '<br>')}
    </div>
    """, unsafe_allow_html=True)
