import streamlit as st
from streamlit_google_auth import Authenticate
import google.generativeai as genai
from PIL import Image
import io

# --- [1. 보안 및 환경 설정] ---
try:
    GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except KeyError:
    st.error("⚠️ Streamlit Secrets 설정이 누락되었습니다.")
    st.stop()

# 🚀 구글 콘솔 리디렉션 URI와 100% 일치해야 함
REDIRECT_URI = "https://afcdaon-q8nrfdizms9kcgzxtbbq3u.streamlit.app" 

# 승인된 이메일 화이트리스트
ALLOWED_EMAILS = [
    "임원근@gmail.com", 
    "01092541128@gmail.com",
    "incheon00@gmail.com"
]

# --- [2. 구글 인증 로직 수정] ---
# 라이브러리 버전에 따라 인자 이름이 다를 수 있어 가장 안정적인 구조로 변경했습니다.
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
    cookie_key='venture_master_key_v2', # 키 갱신
    redirect_uri=REDIRECT_URI,
    cookie_expiry_days=1
)

# ⚠️ 중요: 라이브러리에 따라 'authentication' (n 있음)이 맞습니다. 
# 이전 코드의 'authentification' (n 없음) 오타를 수정했습니다.
authenticator.check_authentication()

# --- [3. 로그인 전 화면 처리] ---
if not st.session_state.get('connected'):
    st.set_page_config(page_title="다온 벤처인증 마스터", layout="centered")
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 서비스를 이용하시려면 사이드바의 [Google로 로그인] 버튼을 클릭해 주세요.")
    with st.sidebar:
        authenticator.login()
    st.stop()

# --- [4. 인증 성공 후 권한 및 메인 UI] ---
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email')
    
    if user_email not in ALLOWED_EMAILS:
        st.error(f"🔒 [{user_email}]님은 권한이 없습니다.")
        if st.sidebar.button("로그아웃"):
            authenticator.logout()
        st.stop()

    # 메인 페이지 설정
    st.set_page_config(page_title="벤처인증 마스터", layout="wide")
    st.sidebar.success(f"👤 {user_info.get('name')}님 환영합니다!")
    if st.sidebar.button("로그아웃"):
        authenticator.logout()

    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    
    # Gemini 모델 설정
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # [이후 분석 로직 동일...]
    st.write("사업자등록증을 업로드하여 기술 분석을 시작하세요.")
