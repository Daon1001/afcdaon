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
            with st.spinner('전체 항목별 700자 분량의 심층 분석을 진행 중입니다...'):
                form_prompt = f"""
                당신은 대한민국 최고의 벤처인증 컨설턴트입니다. [{selected_topic}] 기술에 대해 다음 8가지 항목을 전문적인 용어로 작성하세요. 
                각 항목은 공백 포함 700자 내외의 풍부한 분량으로 논리적이고 구체적으로 서술해야 합니다.

                1. **신청기술 요약 및 표준 양식**: (기존 제공된 V형태 양식 포함 요약)
                2. **개발배경(동기) 및 원인분석**: (산업계 고충 및 구조적 문제 분석)
                3. **경쟁력 확보방안**: (기술적 차별성, 독점적 지위 확보 전략, 진입장벽 구축 방법)
                4. **추진경과**: (아이디어 착안부터 시제품 개발, 테스트, 특허 확보 등 현재까지의 성과)
                5. **향후 3년간 추진계획**: (연도별 R&D 로드맵, 인증 획득, 상용화 및 양산 계획)
                6. **목표시장 및 고객정의**: (3년 내 확보할 시장 규모, 타겟 고객군, 연평균 성장률(CAGR) 근거)
                7. **경쟁사 분석**: (기존 시장 강자의 문제 해결 방식의 한계점과 당사 기술의 우위성)
                8. **시장진입 및 확대전략**: (초기 시장 진입 마케팅, 유통 채널 확보, 3개년 매출 확대 전략)
                9. **자금조달 계획의 구체적 방안**: (벤처 자금, 정부 지원금, 투자 유치, 자체 매출을 통한 자금 선순환 구조)
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
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트")
    st.download_button("리포트 다운로드(.txt)", st.session_state.final_report, file_name="venture_master_report.txt")
    st.markdown(st.session_state.final_report)
