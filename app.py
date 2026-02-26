import streamlit as st
from streamlit_google_auth import Authenticate
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [1. 보안 및 환경 설정] ---
try:
    GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except KeyError:
    st.error("⚠️ Streamlit Secrets 설정이 누락되었습니다. (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, gemini_api_key)")
    st.stop()

# 🚀 중요: 구글 콘솔의 '승인된 리디렉션 URI'와 100% 일치해야 함
REDIRECT_URI = "https://afcdaon-q8nrfdizms9kcgzxtbbq3u.streamlit.app" 

# 🔒 [이메일 승인 명단] 여기에 동료분들의 이메일을 추가하세요.
ALLOWED_EMAILS = [
    "임원근@gmail.com", 
    "01092541128@gmail.com",
    "incheon00@gmail.com"
]
MY_CONTACT = "010-9254-1128"

# --- [2. 구글 인증 설정] ---
# TypeError 방지를 위해 최신 규격인 secret_credential_dict를 사용합니다.
authenticator = Authenticate(
    secret_credential_dict={
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    },
    cookie_name='venture_auth_cookie',
    cookie_key='venture_master_key_final_v1', # 세션 충돌 방지를 위해 키 갱신
    redirect_uri=REDIRECT_URI,
    cookie_expiry_days=1
)

# 인증 상태 체크 (라이브러리에 따라 authentication/authentification 철자 주의)
authenticator.check_authentication()

# --- [3. 로그인 전 화면 처리] ---
if not st.session_state.get('connected'):
    st.set_page_config(page_title="다온 벤처인증 마스터", layout="centered")
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 본 서비스는 승인된 컨설턴트 전용입니다. 구글로 로그인해 주세요.")
    with st.sidebar:
        authenticator.login()
    st.stop()

# 인증 성공 후 이메일 화이트리스트 검증
user_info = st.session_state.get('user_info')
user_email = user_info.get('email')

if user_email not in ALLOWED_EMAILS:
    st.set_page_config(page_title="권한 없음", layout="centered")
    st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다.")
    st.warning(f"임원근 컨설턴트({MY_CONTACT})에게 등록을 요청하세요.")
    if st.sidebar.button("다른 계정으로 로그인"):
        authenticator.logout()
    st.stop()

# --- [4. 메인 서비스 UI (인증 및 승인 완료 시)] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")
st.sidebar.success(f"👤 {user_info.get('name')}님 환영합니다!")
if st.sidebar.button("로그아웃"):
    authenticator.logout()

# Gemini 모델 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

# --- 2. UI 레이아웃 (기존 분석 로직 그대로 유지) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 서류 가이드")
    uploaded_file = st.file_uploader("사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "png", "jpeg", "pdf"])
    
    analysis_image = None
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                pages = convert_from_bytes(uploaded_file.read())
                if pages:
                    analysis_image = pages[0]
            except Exception as e:
                st.error(f"PDF 변환 오류: {e}. 시스템에 poppler가 설치되어 있어야 합니다.")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청을 위해 아래 9가지 서류를 미리 준비해 주세요!**")
        st.markdown("""
        * ✅ **사업자등록증** (현재 완료)
        * 📋 **법인등기부등본** | 📋 **부가가치세표준증명원**
        * 📋 **재무제표 (최근 3개년치)** | 📋 **고용보험/4대보험 명부**
        * 📋 **대표자 건강보험자격득실확인서** | 📋 **주주명부** | 📋 **연구개발인정서**
        """)
        
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('종목 분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 전문적인 제목으로 제안해줘."
                response = model.generate_content([prompt, analysis_image])
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
            with st.spinner('베테랑 컨설턴트의 시각으로 11개 항목 리포트를 생성 중입니다...'):
                form_prompt = f"신청기술 [{selected_topic}]에 대해 전문적인 11개 항목 벤처인증 리포트를 작성하세요. 각 항목은 '### [항목명]' 형식을 유지하세요."
                try:
                    # 분석 이미지가 있으면 함께 전달하여 맥락 유지
                    content = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(content)
                    
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# --- 3. 결과 출력 ---
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
