import streamlit as st
from streamlit_google_auth import Authenticate
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리 (배포 시 packages.txt 필수)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [0. 페이지 및 보안 설정] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

try:
    GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except KeyError:
    st.error("⚠️ Streamlit Secrets 설정이 누락되었습니다.")
    st.stop()

REDIRECT_URI = "https://afcdaon-q8nrfdizms9kcgzxtbbq3u.streamlit.app" 
ALLOWED_EMAILS = ["임원근@gmail.com", "01092541128@gmail.com", "incheon00@gmail.com"]

# --- [1. 구글 인증 로직 (에러 완파 버전)] ---
authenticator = Authenticate(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    cookie_name='venture_auth_cookie_v2',
    key='venture_master_key_v2026_final', 
    cookie_expiry_days=1
)

authenticator.check_authentication()

# --- [2. 로그인 및 권한 검증] ---
if not st.session_state.get('connected'):
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 본 서비스는 승인된 인원만 이용 가능합니다. 사이드바에서 로그인을 진행해 주세요.")
    with st.sidebar:
        authenticator.login()
    st.stop()

user_info = st.session_state.get('user_info')
user_email = user_info.get('email')

if user_email not in ALLOWED_EMAILS:
    st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다. 임원근 컨설턴트에게 문의하세요.")
    if st.sidebar.button("다른 계정으로 로그인"):
        authenticator.logout()
    st.stop()

# --- [3. 메인 서비스 UI 및 AI 엔진 설정] ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.sidebar.success(f"✅ {user_info.get('name')}님 (승인됨)")
if st.sidebar.button("로그아웃"):
    authenticator.logout()

st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 서류 가이드")
    uploaded_file = st.file_uploader("사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "png", "jpeg", "pdf"])
    
    analysis_image = None
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                pages = convert_from_bytes(uploaded_file.read())
                if pages: analysis_image = pages[0]
            except Exception:
                st.error("PDF 변환 오류. packages.txt 설정을 확인하세요.")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청 필수 서류 9가지 준비 확인**")
        st.markdown("* ✅ **사업자등록증** | 📋 **법인등기부등본** | 📋 **재무제표** | 📋 **연구소인정서** 등")
        
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('종목 분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 전문적인 제목으로 제안해줘."
                response = model.generate_content([prompt, analysis_image])
                st.session_state.suggestions = response.text
                
    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 상세 리포트를 생성 중입니다...'):
                # 🚀 원근 컨설턴트님이 요청하신 11개 항목 상세 프롬프트 복구
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 11개 항목을 각각 전문적인 문체로 상세히 작성하세요. 
                각 항목은 공백 포함 700자 내외의 풍부한 분량이어야 하며, 실질적인 컨설팅 데이터가 포함되어야 합니다.
                각 항목의 구분은 반드시 '### [항목명]' 형식을 유지하세요.

                ### [1. 신청기술 요약 및 표준 양식]
                (기술의 핵심 정의와 벤처인증 표준 V자 양식을 사용하여 요약 작성)
                ### [2. 개발배경 및 원인분석]
                (해당 산업의 기술적/사회적 문제점과 이를 해결해야 하는 필연성 분석)
                ### [3. 경쟁력 확보방안]
                (본 기술만의 독창적 핵심 알고리즘 또는 공정 방식 기술)
                ### [4. 추진경과 및 향후 계획]
                (R&D 이력과 향후 3개년 제품 고도화 로드맵)
                ### [5. 목표시장 및 고객정의]
                (TAM/SAM/SOM 기반 시장 규모와 핵심 타겟 고객사 정의)
                ### [6. 경쟁사 분석 및 우위성]
                (국내외 주요 경쟁사 기술력 비교 및 압도적 차별화 요소)
                ### [7. 시장진입 및 확대전략 - 추진경과]
                (현재까지의 마케팅 성과 및 파일럿 테스트 결과)
                ### [8. 시장진입 및 확대전략 - 향후계획]
                (유통 채널 확보 및 글로벌 진출 전략)
                ### [9. 지식재산권 및 특허 전략]
                (추천 특허 명칭 3종과 청구항 핵심 아이디어 제안)
                ### [10. 자금조달 계획의 구체적 방안]
                (매출 추정 기반 자금 선순환 구조 및 외부 투자 유치 전략)
                ### [11. 연계 가능 정책자금 추천]
                (중진공, 기보, 신보 등 현재 업력과 기술력에 맞는 최적의 정책자금 매칭)
                """
                try:
                    content = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(content)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# --- [4. 결과 출력 및 다운로드] ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("전체 리포트 다운로드(.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        lines = section.split('\n')
        title = lines[0].strip('[] ')
        content = '\n'.join(lines[1:]).strip()
        with st.expander(f"📌 {title}", expanded=False):
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 25px; border-radius: 12px; line-height: 1.9; border-left: 6px solid #007bff;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
