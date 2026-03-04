import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
import os
from datetime import datetime, date

# PDF 처리를 위한 라이브러리 (배포 시 packages.txt 필수)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [0. 페이지 설정 및 프리미엄 CSS 디자인] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

custom_css = """
<style>
    /* 배경 그라데이션 강제 적용 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    }
    
    /* 중앙 로그인 박스 레이아웃 (스크롤 최소화) */
    .login-container {
        display: flex !important;
        justify-content: center !important;
        align-items: flex-start !important;
        padding-top: 20px !important;
        min-height: 100vh !important;
    }
    
    .login-box {
        background-color: white !important;
        padding: 25px !important;
        border-radius: 15px !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2) !important;
        text-align: center !important;
        max-width: 480px !important;
        width: 100% !important;
        border-top: 8px solid #0b1f52 !important;
    }

    /* 이미지(확인서) 최적화 */
    [data-testid="stImage"] > img {
        width: 100% !important;
        height: auto !important;
        max-height: 280px !important;
        object-fit: contain !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
    }

    .login-title {
        color: #0b1f52 !important;
        font-weight: 800 !important;
        font-size: 24px !important;
    }

    /* 대시보드 내부 프리미엄 헤더 */
    .premium-header {
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%) !important;
        color: white !important;
        padding: 1.5rem !important;
        border-radius: 12px !important;
        border-bottom: 4px solid #d4af37 !important;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .metric-box {
        background-color: rgba(255, 255, 255, 0.9);
        border-left: 5px solid #0b1f52;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    .report-card {
        background-color: white !important;
        padding: 20px !important;
        border-radius: 8px !important;
        line-height: 1.8 !important;
        border: 1px solid #e0e0e0 !important;
        border-left: 6px solid #0b1f52 !important;
        margin-bottom: 10px !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [CSV DB 설정 및 자동 복구 로직] ---
DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
            {"email": "임원근@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month}
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    df = pd.read_csv(DB_FILE)
    for col in ['usage_count', 'last_month', 'created_at', 'approved', 'is_admin']:
        if col not in df.columns:
            df[col] = 0 if 'count' in col else (date.today().month if 'month' in col else False)
    return df

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

# --- [1. 시스템 세션 상태 관리] ---
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = "1"
MAX_MONTHLY_LIMIT = 30 

# --- [2. 중앙 집중형 로그인 화면] ---
if st.session_state.authenticated_user is None:
    _, col_mid, _ = st.columns([0.5, 1, 0.5])
    with col_mid:
        st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
        try:
            logo = Image.open("venture_cert.png")
            st.image(logo)
        except:
            st.markdown("<h3 style='color:#0b1f52;'>🏛️ 중소기업경영지원단</h3>", unsafe_allow_html=True)
        st.markdown('<div class="login-title">중소기업경영지원단</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#666; font-size: 0.95rem; margin-bottom: 15px;'>벤처인증 AI 마스터 컨설턴트 로그인</p>", unsafe_allow_html=True)
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        b1, b2 = st.columns(2)
        if b1.button("로그인", type="primary", use_container_width=True):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty and user_row.iloc[0]['approved']:
                st.session_state.authenticated_user = login_email
                st.rerun()
            else: st.error("❌ 미등록 계정 또는 승인 대기")
        if b2.button("승인 신청", use_container_width=True):
            if login_email and user_db[user_db['email'] == login_email].empty:
                new_user = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "created_at": datetime.now().strftime("%Y-%m-%d"), "usage_count": 0, "last_month": date.today().month}])
                user_db = pd.concat([user_db, new_user], ignore_index=True); save_db(user_db)
                st.success("📩 신청 완료!")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 메인 대시보드 및 동적 AI 제어 시스템] ---
with st.sidebar:
    st.success(f"👤 접속: {st.session_state.authenticated_user}")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
    st.write(f"📊 월 사용량: {user_db.at[idx, 'usage_count']} / {MAX_MONTHLY_LIMIT}")

# 동적 제어 로직: 가용한 모델을 실시간 검색하여 자동 연결
try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
    
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    selected_model = ""
    for target in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
        match = [m for m in models if target in m]
        if match:
            selected_model = match[0]
            break
            
    if not selected_model and models:
        selected_model = models[0]
        
    model = genai.GenerativeModel(selected_model)
    st.sidebar.caption(f"🤖 시스템 가동 엔진: {selected_model.replace('models/', '')}")
except Exception as e:
    st.error(f"⚠️ AI 엔진 동적 제어 실패: {e}"); st.stop()

st.markdown("""
    <div class="premium-header">
        <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
        <p><strong>중소기업경영지원단</strong> 전문가 전용 AI 마스터 시스템</p>
    </div>
""", unsafe_allow_html=True)

if st.button("🔄 새 기업 컨설팅 시작", type="secondary"):
    for key in ['suggestions', 'report_sections']:
        if key in st.session_state: del st.session_state[key]
    st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
    st.rerun()

# --- [4. 기능 영역 (🚀 예외 처리 강화)] ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 기술 추천")
    biz_type = st.radio("업종 선택", ["일반 기업", "IT / SW", "초기기업"], horizontal=True)
    uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "pdf"], key=f"up_{st.session_state.uploader_key}")
    
    analysis_image = None
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try: pages = convert_from_bytes(uploaded_file.read()); analysis_image = pages[0]
            except: st.error("PDF 변환 오류")
        else: analysis_image = Image.open(uploaded_file)
        
    user_guide_rec = st.text_area("💡 추천 가이드라인", placeholder="예: 특정 소재 강조", key=f"gr_{st.session_state.uploader_key}")
    
    if st.button("AI 기술 주제 추천 ✨"):
        if user_db.at[idx, 'usage_count'] >= MAX_MONTHLY_LIMIT: st.error("한도 초과")
        else:
            with st.spinner('분석 중...'):
                prompt = f"[{biz_type}] 벤처 기술 주제 3개 추천. {user_guide_rec}"
                try:
                    # 🚀 API 한도 초과 에러를 부드럽게 잡아내는 예외 처리
                    response = model.generate_content([prompt, analysis_image] if analysis_image else prompt)
                    st.session_state.suggestions = response.text
                    user_db.at[idx, 'usage_count'] += 1; save_db(user_db); st.rerun()
                except Exception as e:
                    if "ResourceExhausted" in str(e) or "429" in str(e):
                        st.error("⏳ 구글 AI 서버의 분당/일일 사용 한도(Quota)를 초과했습니다. 약 1분 정도 기다리신 후 다시 시도해 주세요.")
                    else:
                        st.error(f"⚠️ 분석 중 오류가 발생했습니다: {e}")

    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 마스터 리포트 생성")
    selected_topic = st.text_input("확정 기술명", placeholder="기술명을 입력하세요.", key=f"topic_{st.session_state.uploader_key}")
    user_guide_rep = st.text_area("💡 리포트 지시사항", placeholder="시장 숫자 등", key=f"gp_{st.session_state.uploader_key}")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic: st.warning("기술명을 입력하세요.")
        else:
            with st.spinner('리포트 생성 중...'):
                form_prompt = f"""
                당신은 대한민국 최고의 벤처인증 전문 컨설턴트입니다. [{selected_topic}]에 대해 11개 항목 리포트를 작성하세요.
                시장 데이터는 실제 기반 숫자를 사용하고 지어내지 마세요. V자 요약 양식 필수 포함. {user_guide_rep}
                ### [1. 신청기술 요약 및 표준 양식]
                ### [2. 개발배경 및 원인분석]
                ### [3. 경쟁력 확보방안]
                ### [4. 추진경과 및 향후 계획]
                ### [5. 목표시장 및 고객정의]
                ### [6. 경쟁사 분석 및 우위성]
                ### [7. 시장진입 및 확대전략 - 추진경과]
                ### [8. 시장진입 및 확대전략 - 향후계획]
                ### [9. 지식재산권 및 특허 전략]
                ### [10. 자금조달 계획의 구체적 방안]
                ### [11. 연계 가능 정책자금 추천]
                """
                try:
                    # 🚀 API 한도 초과 에러를 부드럽게 잡아내는 예외 처리
                    response = model.generate_content([form_prompt, analysis_image] if analysis_image else form_prompt)
                    st.session_state.report_sections = response.text.split('### ')
                    user_db.at[idx, 'usage_count'] += 1; save_db(user_db); st.rerun()
                except Exception as e:
                    if "ResourceExhausted" in str(e) or "429" in str(e):
                        st.error("⏳ 구글 AI 서버의 분당/일일 사용 한도(Quota)를 초과했습니다. 리포트 생성은 많은 자원을 소모하므로 잠시 후 다시 시도해 주세요.")
                    else:
                        st.error(f"⚠️ 리포트 생성 중 오류가 발생했습니다: {e}")

if 'report_sections' in st.session_state:
    st.divider()
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("💾 전체 리포트 다운로드", full_report, file_name=f"벤처리포트_{selected_topic}.txt")
    for section in st.session_state.report_sections:
        if section.strip():
            title = section.split('\n', 1)[0].strip('[] ')
            with st.expander(f"📌 {title}", expanded=False):
                st.write(section)
