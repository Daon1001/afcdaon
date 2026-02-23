import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")
st.title("🏛️ 벤처인증 통합 전략 및 사업계획서 생성기")

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
    st.subheader("2️⃣ 벤처인증 통합 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하거나 왼쪽에서 복사하세요.")
    
    if st.button("마스터 리포트 생성 (종합 8개 항목) 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 리포트를 작성 중입니다...'):
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 8가지 항목을 작성하세요. 
                
                [작성 지침]
                - '했다', '임' 같은 딱딱한 말투 대신 '추진하고 있습니다', '분석됩니다', '확보하였습니다' 등 전문적이면서도 생동감 있는 문체를 사용하세요.
                - 나열식보다는 문장 간의 인과관계가 명확한 '스토리텔링' 방식을 취하세요.
                - 각 항목은 공백 포함 700자 내외로 풍부하게 작성하세요.

                1. **신청기술 요약 및 표준 양식**: (V형태 양식을 포함하되 문맥이 자연스럽게 연결되도록 작성)
                2. **개발배경(동기) 및 원인분석**: (단순 현상이 아닌 현장의 생생한 고충과 기술적 한계를 분석)
                3. **경쟁력 확보방안**: (남들이 따라올 수 없는 우리만의 '무기'가 무엇인지 설득력 있게 제시)
                4. **추진경과**: (현장에서 흘린 땀이 느껴지도록 구체적인 개발 기록과 특허 확보 과정을 서술)
                5. **향후 3년간 추진계획**: (막연한 장밋빛 미래가 아닌, 단계별로 실현 가능한 로드맵을 제시)
                6. **목표시장 및 고객정의**: (누가 우리 제품을 사줄 것인지, 그 시장이 얼마나 매력적인지 구체적인 수치로 증명)
                7. **경쟁사 분석**: (경쟁사를 깎아내리기보다 그들의 한계를 짚어주고 당사 기술의 당위성을 강조)
                8. **시장진입 및 확대전략**: (현실적인 유통 경로와 마케팅 전략을 바탕으로 한 시장 장악 시나리오)
                9. **자금조달 계획의 구체적 방안**: (안정적인 재무 구조를 만들기 위한 정부자금 및 투자 유치 계획)
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
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트 (전문가 버전)")
    st.download_button("리포트 다운로드(.txt)", st.session_state.final_report, file_name="venture_master_report.txt")
    
    # 가독성을 높이기 위해 결과창 디자인 개선
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 25px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
        {st.session_state.final_report.replace('\n', '<br>')}
    </div>
    """, unsafe_allow_html=True)
