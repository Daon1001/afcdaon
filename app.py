import streamlit as st
import google.generativeai as genai
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from PIL import Image
import io

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 마스터", layout="wide")

# --- 1. 보안 설정 (Secrets 필수) ---
try:
    CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except KeyError:
    st.error("⚠️ Secrets 설정이 누락되었습니다.")
    st.stop()

# 반드시 구글 콘솔의 '리디렉션 URI'와 일치해야 함
REDIRECT_URI = "https://afcdaon-q8nrfdizms9kcgzxtbbq3u.streamlit.app" 
ALLOWED_EMAILS = ["incheon00@gmail.com", "01092541128@gmail.com"]

# --- 2. 구글 로그인 로직 (표준 Flow 방식) ---
client_config = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

flow = Flow.from_client_config(
    client_config,
    scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_uri=REDIRECT_URI
)

# 로그인 세션 관리
if 'connected' not in st.session_state:
    st.session_state.connected = False

# URL에서 인증 코드 확인
query_params = st.query_params
if "code" in query_params and not st.session_state.connected:
    flow.fetch_token(code=query_params["code"])
    credentials = flow.credentials
    # 사용자 정보 가져오기
    import requests
    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    ).json()
    st.session_state.user_info = user_info
    st.session_state.connected = True
    st.rerun()

# --- 3. 화면 분기 ---
if not st.session_state.connected:
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.info("💡 서비스를 이용하시려면 아래 버튼을 눌러 로그인해 주세요.")
    st.markdown(f'<a href="{auth_url}" target="_self" style="text-decoration:none;"><div style="background-color:#4285F4;color:white;padding:10px;border-radius:5px;text-align:center;width:200px;font-weight:bold;">Google로 로그인</div></a>', unsafe_allow_html=True)
    st.stop()

# 이메일 화이트리스트 검증
user_email = st.session_state.user_info.get('email')
if user_email not in ALLOWED_EMAILS:
    st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다. (문의: 010-9254-1128)")
    if st.button("로그아웃"):
        st.session_state.connected = False
        st.rerun()
    st.stop()

# --- 4. 메인 서비스 (인증 성공 시) ---
st.sidebar.success(f"👤 {st.session_state.user_info.get('name')}님 환영합니다!")
if st.sidebar.button("로그아웃"):
    st.session_state.connected = False
    st.query_params.clear()
    st.rerun()

st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# (이하 기존 사업자등록증 분석 및 리포트 생성 로직 동일)
col1, col2 = st.columns(2)
with col1:
    st.subheader("1️⃣ 분석 및 서류 가이드")
    uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "jpeg", "pdf"])
    # ... [기존 코드 동일하게 유지] ...



