import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 컨설턴트", layout="wide")
st.title("🛡️ 제조업 벤처인증 전략 및 사업요약서 생성기")

# --- 1. 대표님표 강력한 API 및 모델 자동 스캐너 (유지) ---
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

if not target_model_name:
    st.error(f"⚠️ 연결 가능한 AI 모델이 없습니다.\n- 감지된 목록: {available_models}")
    st.stop()

model = genai.GenerativeModel(target_model_name)
st.sidebar.success(f"✅ 가동 중인 AI 엔진:\n**{target_model_name}**")

# --- 2. 세션 상태 관리 ---
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = ""
if 'final_report' not in st.session_state:
    st.session_state.final_report = ""

# --- 3. 투트랙(Two-Track) UI 레이아웃 ---
st.write("💡 **이용 가이드:** 왼쪽에서 사업자등록증을 분석해 추천을 받거나, 오른쪽에서 직접 기술명을 입력해 바로 요약서를 생성하세요.")
st.divider()

col1, col2 = st.columns(2)

# [왼쪽 영역] 사업자등록증 업로드 및 AI 추천
with col1:
    st.subheader("1️⃣ 사업자등록증 기반 주제 추천 (선택)")
    uploaded_file = st.file_uploader("사업자등록증 업로드 (이미지가 없어도 우측에서 진행 가능)", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=300)
        
        if st.button("AI 기술 주제 추천받기", type="secondary"):
            with st.spinner(f'{target_model_name} 엔진이 종목을 분석 중입니다...'):
                try:
                    prompt = """
                    사업자등록증에서 업태와 종목을 읽고, 벤처인증(혁신성장형)을 받기에 유리한 
                    기술 주제 3가지를 '주제 1: [제목]' 형식으로 제안해줘.
                    제목은 제조업의 혁신성이 드러나도록 전문적으로 지어줘.
                    """
                    response = model.generate_content([prompt, img])
                    st.session_state.suggestions = response.text
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

    # 추천 결과가 있으면 화면에 표시
    if st.session_state.suggestions:
        st.info("👇 마음에 드는 주제를 복사해서 우측 입력창에 붙여넣으세요.")
        st.success(st.session_state.suggestions)

# [오른쪽 영역] 직접 입력 및 사업요약서 생성
with col2:
    st.subheader("2️⃣ 사업요약서 자동 완성")
    selected_topic = st.text_input("신청기술(제품/서비스)명 입력:", placeholder="예: AI 기반 창호 절단 및 타공 자동화 시스템")
    st.caption("👈 왼쪽에서 추천받은 주제를 복사해 넣거나, 대표님이 직접 구상하신 기술명을 자유롭게 입력하세요.")
    
    if st.button("표준 양식으로 사업요약서 작성 🚀", type="primary"):
        if not selected_topic:
            st.warning("먼저 위 칸에 기술 주제명을 입력해 주세요!")
        else:
            with st.spinner('전문 컨설팅 리포트를 작성 중입니다...'):
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
                try:
                    # 업로드된 이미지가 있으면 참조용으로 같이 보내고, 없으면 텍스트(주제)로만 생성
                    if uploaded_file:
                        img = Image.open(uploaded_file)
                        response = model.generate_content([form_prompt, img])
                    else:
                        response = model.generate_content(form_prompt)
                        
                    st.session_state.final_report = response.text
                except Exception as e:
                    st.error(f"문서 작성 중 오류 발생: {e}")

# --- 4. 최종 결과 출력 및 다운로드 ---
st.divider()
if st.session_state.final_report:
    st.subheader("📝 완성된 벤처인증 사업요약서 (초안)")
    
    # 다운로드 버튼 (텍스트 파일로 즉시 저장)
    st.download_button(
        label="📄 결과물 텍스트(.txt) 파일로 다운로드하기",
        data=st.session_state.final_report,
        file_name=f"벤처인증_사업요약서.txt",
        mime="text/plain"
    )
    
    st.markdown(st.session_state.final_report)
