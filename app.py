import streamlit as st
from streamlit_google_auth import Authenticate
import google.generativeai as genai
from PIL import Image
import io

# --- [0. 페이지 설정] 반드시 최상단 ---
st.set_page_config(page_title="벤처인증 마스터", layout="wide")

# PDF 처리 라이브러리
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [1. 보안 및 환경 설정] ---
try:
    # Streamlit Cloud의 Secrets에서 값을 가져옵니다.
    GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    GEMINI_API_KEY = st.secrets["gemini_api_key"]
except KeyError:
    st.error("⚠️ Secrets 설정이 누락되었습니다. (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, gemini_api_key)")
    st.stop()

# 구글 콘솔에 등록한 리디렉션 URI (정확히 일치해야 함)
REDIRECT_URI = "https://your-app-name.streamlit.app" 

# 승인된 이메일 목록 (화이트리스트)
ALLOWED_EMAILS = [
    "incheon00@gmail.com", 
    "01092541128@gmail.com"
]

# --- [2. 구글 인증 로직] 최신 라이브러리 규격(딕셔너리 방식) 적용 ---
# 이 방식이 TypeError를 해결하는 핵심입니다.
auth_config = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI],
    }
}

authenticator = Authenticate(
    secret_credential_dict=auth_config,  # 딕셔너리 형태로 전달
    cookie_name='venture_auth_cookie',
    cookie_key='venture_master_secret_key',
    redirect_uri=REDIRECT_URI,
    cookie_expiry_days=1
)

# 인증 상태 확인
authenticator.check_authentication()

# 로그인 전 화면
if not st.session_state.get('connected'):
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 서비스를 이용하시려면 사이드바의 [Google로 로그인] 버튼을 클릭해 주세요.")
    authenticator.login()
    st.stop()

# 인증 성공 시 이메일 검증
user_info = st.session_state.get('user_info')
if user_info:
    user_email = user_info.get('email')
    if user_email not in ALLOWED_EMAILS:
        st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다. 임원근 컨설턴트(010-9254-1128)에게 문의하세요.")
        if st.sidebar.button("로그아웃"):
            authenticator.logout()
        st.stop()

    # --- [3. 메인 서비스 UI] ---
    st.sidebar.success(f"👤 {user_info.get('name')}님 환영합니다!")
    if st.sidebar.button("로그아웃"):
        authenticator.logout()

    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

    # Gemini 설정
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 업무 레이아웃
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
                    st.error("PDF 변환 실패. packages.txt 설정을 확인하세요.")
            else:
                analysis_image = Image.open(uploaded_file)
            
            st.warning("🔔 **벤처인증 신청 필수 서류 안내**")
            st.markdown("* ✅ **사업자등록증** | 📋 **법인등기부등본** | 📋 **재무제표** | 📋 **연구개발인정서** 등")
            
            if st.button("AI 기술 주제 추천받기"):
                with st.spinner('분석 중...'):
                    prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 제안해줘."
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
                with st.spinner('리포트 생성 중...'):
                    # 11대 항목 프롬프트
                    form_prompt = f"""
                    신청기술 [{selected_topic}]에 대해 다음 11개 항목 리포트를 작성하세요. 
                    항목 구분은 '### [항목명]' 형식을 유지하고 전문적인 문체를 사용하세요.

                    ### [1. 신청기술 요약 및 표준 양식] (V자 양식 포함)
                    ### [2. 개발배경 및 원인분석] (산업 구조적 문제 분석)
                    ### [3. 경쟁력 확보방안] (기술적 차별성 및 진입장벽)
                    ### [4. 추진경과 및 향후 계획] (R&D 실적 및 3개년 로드맵)
                    ### [5. 목표시장 및 고객정의] (시장 규모 및 성장률 근거)
                    ### [6. 경쟁사 분석 및 우위성] (기존 방식 대비 우위성)
                    ### [7. 시장진입 및 확대전략 - 추진경과] (마케팅 실적 및 시장 반응)
                    ### [8. 시장진입 및 확대전략 - 향후계획] (3개년 점유율 확대 전략)
                    ### [9. 지식재산권 및 특허 전략] (추천 특허 3종 및 청구항 아이디어)
                    ### [10. 자금조달 계획의 구체적 방안] (자금 선순환 구조 설계)
                    ### [11. 연계 가능 정책자금 추천] (중진공/기보/신보 자금 및 선정 포인트)
                    """
                    try:
                        response = model.generate_content([form_prompt, analysis_image]) if analysis_image else model.generate_content(form_prompt)
                        report_text = response.text
                        sections = report_text.split('### ')
                        st.session_state.report_sections = [s for s in sections if s.strip()]
                    except Exception as e:
                        st.error(f"오류: {e}")

    # --- [4. 결과 출력] ---
    st.divider()
    if 'report_sections' in st.session_state:
        st.subheader("📄 항목별 상세 컨설팅 리포트")
        for section in st.session_state.report_sections:
            lines = section.split('\n')
            title = lines[0].strip('[] ')
            content = '\n'.join(lines[1:]).strip()
            with st.expander(f"📌 {title}", expanded=False):
                st.markdown(f"<div style='background-color: #f8f9fa; padding: 25px; border-radius: 12px; line-height: 1.9; border-left: 6px solid #007bff;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
