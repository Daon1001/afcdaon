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
    st.error("⚠️ Streamlit Secrets 설정이 누락되었습니다.")
    st.stop()

# 🚀 중요: 구글 콘솔의 '승인된 리디렉션 URI'와 100% 일치해야 함
REDIRECT_URI = "https://afcdaon-q8nrfdizms9kcgzxtbbq3u.streamlit.app" 

# 🔒 이메일 승인 명단
ALLOWED_EMAILS = [
    "임원근@gmail.com", 
    "01092541128@gmail.com",
    "incheon00@gmail.com"
]
MY_CONTACT = "010-9254-1128"

# --- [2. 구글 인증 설정 (TypeError 해결 버전)] ---
# 인자명을 'secret_credentials'로 수정하였습니다. 
# 만약 또 에러가 난다면 이 부분을 직접 전달 방식으로 바꿀 준비가 되어 있습니다.
authenticator = Authenticate(
    secret_credentials={
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    },
    cookie_name='venture_auth_cookie',
    cookie_key='venture_master_key_v2026', # 세션 갱신을 위해 키 변경
    redirect_uri=REDIRECT_URI,
    cookie_expiry_days=1
)

# 인증 체크 함수 실행
authenticator.check_authentication()

# --- [3. 로그인 및 권한 검증] ---
if not st.session_state.get('connected'):
    st.set_page_config(page_title="다온 벤처인증 마스터", layout="centered")
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 본 서비스는 승인된 컨설턴트 전용입니다. 사이드바에서 로그인을 진행해 주세요.")
    with st.sidebar:
        authenticator.login()
    st.stop()

# 이메일 화이트리스트 검증
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email')
    if user_email not in ALLOWED_EMAILS:
        st.set_page_config(page_title="권한 없음", layout="centered")
        st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다.")
        st.warning(f"임원근 컨설턴트({MY_CONTACT})에게 등록을 요청하세요.")
        if st.sidebar.button("다른 계정으로 로그인"):
            authenticator.logout()
        st.stop()

# --- [4. 메인 서비스 UI (인증 완료 시)] ---
st.set_page_config(page_title="벤처인증 AI 마스터", layout="wide")
st.sidebar.success(f"👤 {user_info.get('name')}님 (승인됨)")
if st.sidebar.button("로그아웃"):
    authenticator.logout()

# Gemini 모델 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

# 레이아웃 및 분석 로직
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
            except Exception as e:
                st.error(f"PDF 변환 오류: {e}")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청 필수 서류 9가지 준비 확인**")
        
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('종목 분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 제안해줘."
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
            with st.spinner('베테랑 컨설턴트의 시각으로 리포트를 생성 중입니다...'):
                form_prompt = f"신청기술 [{selected_topic}]에 대해 전문적인 11개 항목 벤처인증 리포트를 작성하세요. 각 항목은 '### [항목명]' 형식을 유지하세요."
                try:
                    content = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(content)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# 결과 출력
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트")
    for section in st.session_state.report_sections:
        lines = section.split('\n')
        title = lines[0].strip('[] ')
        content = '\n'.join(lines[1:]).strip()
        with st.expander(f"📌 {title}"):
            st.markdown(content)
