import streamlit as st
from streamlit_google_auth import Authenticate
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리 (배포 시 packages.txt에 poppler-utils 필요)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [1. 보안 및 환경 설정] ---
# 깃허브 보안 경고 방지를 위해 Secrets에서 안전하게 불러옵니다.
try:
    GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except KeyError:
    st.error("⚠️ Streamlit Secrets 설정이 누락되었습니다. (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, gemini_api_key)")
    st.stop()

# 🚀 중요: 구글 콘솔 '승인된 리디렉션 URI'와 토씨 하나 안 틀리고 똑같아야 합니다.
# 마지막에 / 가 있는지 없는지도 꼭 확인하세요!
REDIRECT_URI = "https://afcdaon-q8nrfdizms9kcgzxtbbq3u.streamlit.app" 

# 🔒 승인된 이메일 화이트리스트 (여기에 회사 동료분들을 추가하세요)
ALLOWED_EMAILS = [
    "임원근@gmail.com", 
    "01092541128@gmail.com",
    "incheon00@gmail.com" # 테스트용 추가
]
MY_CONTACT = "010-9254-1128"

# --- [2. 구글 인증 로직] ---
# 최신 라이브러리 규격에 맞춰 secret_credential_dict 구조를 적용했습니다.
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
    cookie_key='venture_master_secret_key_1128', # 보안 강화를 위해 키 변경
    redirect_uri=REDIRECT_URI,
    cookie_expiry_days=1
)

# 인증 체크
authenticator.check_authentication()

# --- [3. 로그인 및 권한 검증 화면] ---
if not st.session_state.get('connected'):
    st.set_page_config(page_title="다온 벤처인증 마스터", layout="centered")
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.markdown("### **본 서비스는 승인된 컨설턴트 전용입니다.**")
    st.info("💡 사이드바의 **[Google로 로그인]** 버튼을 클릭해 주세요.")
    
    # 사이드바에 로그인 버튼 배치
    with st.sidebar:
        authenticator.login()
    st.stop()

# 인증 성공 후 이메일 검증 (화이트리스트 체크)
user_info = st.session_state.get('user_info')
user_email = user_info.get('email')

if user_email not in ALLOWED_EMAILS:
    st.set_page_config(page_title="권한 없음", layout="centered")
    st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다.")
    st.warning(f"임원근 컨설턴트({MY_CONTACT})에게 등록을 요청하세요.")
    if st.sidebar.button("다른 계정으로 로그인"):
        authenticator.logout()
    st.stop()

# --- [4. 메인 서비스 UI (승인된 사용자 전용)] ---
st.set_page_config(page_title="벤처인증 마스터", layout="wide")
st.sidebar.success(f"👤 {user_info.get('name')}님 (승인됨)")
if st.sidebar.button("로그아웃"):
    authenticator.logout()

# 여기서부터는 기존의 Gemini 분석 로직이 실행됩니다.
st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

# Gemini 모델 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ... (이후는 기존에 작성하신 col1, col2 분석 로직과 동일합니다)
# 파일 업로드 및 리포트 생성 코드가 이어집니다.
