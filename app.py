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
    /* 전체 배경 그라데이션 (실버 블루 톤) */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* 중앙 로그인 박스 레이아웃 (네이버/STOVE 스타일) */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 5vh;
    }
    .login-box {
        background-color: rgba(255, 255, 255, 0.98);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        text-align: center;
        max-width: 480px;
        border-top: 6px solid #0b1f52;
    }
    .login-title {
        color: #0b1f52;
        font-weight: 900;
        font-size: 28px;
        margin-bottom: 5px;
    }
    .login-subtitle {
        color: #666;
        font-size: 15px;
        margin-bottom: 30px;
    }

    /* 메인 대시보드 헤더 */
    .premium-header {
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 12px;
        border-bottom: 5px solid #d4af37;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .metric-box {
        background-color: rgba(255, 255, 255, 0.9);
        border-left: 5px solid #0b1f52;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    /* 리포트 결과물 스타일 */
    .report-card {
        background-color: white;
        padding: 25px;
        border-radius: 8px;
        line-height: 1.8;
        border: 1px solid #e0e0e0;
        border-left: 6px solid #0b1f52;
        margin-bottom: 15px;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- [CSV DB 설정 및 자동 복구] ---
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
        if col not in df.columns: df[col] = 0 if 'count' in col else (date.today().month if 'month' in col else False)
    return df

def save_db(df): df.to_csv(DB_FILE, index=False)

user_db = load_db()

# --- [1. 세션 상태 관리] ---
if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = "1"
MAX_MONTHLY_LIMIT = 30 

# --- [2. 중앙 집중형 로그인 화면] ---
if st.session_state.authenticated_user is None:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
        # 로고 이미지 (venture_cert.png 파일이 폴더에 있어야 함)
        try:
            logo = Image.open("venture_cert.png")
            st.image(logo, use_container_width=True)
        except:
            st.markdown('<div class="login-title">🏛️ 중소기업경영지원단</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="login-subtitle">벤처인증 AI 마스터 컨설턴트 로그인</div>', unsafe_allow_html=True)
        login_email = st.text_input("이메일 주소", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        
        c1, c2 = st.columns(2)
        if c1.button("로그인", type="primary", use_container_width=True):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty and user_row.iloc[0]['approved']:
                st.session_state.authenticated_user = login_email
                st.rerun()
            else: st.error("❌ 미등록 계정이거나 승인이 필요합니다.")
            
        if c2.button("승인 신청", use_container_width=True):
            if login_email and user_db[user_db['email'] == login_email].empty:
                new_user = pd.DataFrame([{"email": login_email, "approved": False, "is_admin": False, "created_at": datetime.now().strftime("%Y-%m-%d"), "usage_count": 0, "last_month": date.today().month}])
                user_db = pd.concat([user_db, new_user], ignore_index=True); save_db(user_db)
                st.success("📩 신청 완료! 관리자 승인을 기다려주세요.")
            else: st.warning("이미 등록된 계정입니다.")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# --- [3. 메인 대시보드 접속] ---
with st.sidebar:
    st.success(f"👤 접속: {st.session_state.authenticated_user}")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    
    idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
    st.write(f"📊 월 사용량: {user_db.at[idx, 'usage_count']} / {MAX_MONTHLY_LIMIT}")

# AI 엔진 설정
try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("API 키 설정 오류"); st.stop()

# --- [4. 대시보드 상단] ---
st.markdown(f"""
    <div class="premium-header">
        <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
        <p><strong>중소기업경영지원단</strong> 전문가 전용 AI 마스터 시스템</p>
    </div>
""", unsafe_allow_html=True)

col_metric, col_reset = st.columns([8, 2])
with col_reset:
    if st.button("🔄 새 기업 컨설팅 시작", use_container_width=True):
        for key in ['suggestions', 'report_sections']:
            if key in st.session_state: del st.session_state[key]
        st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
        st.rerun()

# --- [5. 기능 섹션] ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 서류 가이드")
    biz_type = st.radio("업종 선택", ["일반 기업 (제조/서비스)", "IT / 소프트웨어", "초기창업 (3년 미만)"], horizontal=True)
    uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "pdf"], key=f"up_{st.session_state.uploader_key}")
    
    analysis_image = None
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try: pages = convert_from_bytes(uploaded_file.read()); analysis_image = pages[0]
            except: st.error("PDF 변환 오류")
        else: analysis_image = Image.open(uploaded_file)
        
        st.info(f"📋 **[{biz_type}] 필수 증빙 서류 목록**")
        st.markdown("* 사업자등록증명원 / 법인등기부등본 / 재무제표 / 부가세증명원 / 4대보험명부 / 주주명부 / 연구소인정서 / 지재권서류 등")
        
    user_guide_rec = st.text_area("💡 추천 가이드 (선택)", placeholder="예: 특정 소재 기술 강조 요청", key=f"gr_{st.session_state.uploader_key}")
    
    if st.button("AI 기술 주제 추천 ✨"):
        if user_db.at[idx, 'usage_count'] >= MAX_MONTHLY_LIMIT: st.error("사용 한도 초과")
        else:
            with st.spinner('분석 중...'):
                prompt = f"사업자등록증을 분석하여 [{biz_type}] 분야의 벤처인증용 기술 주제 3개를 제안해줘. {user_guide_rec}"
                content = [prompt, analysis_image] if analysis_image else prompt
                response = model.generate_content(content)
                st.session_state.suggestions = response.text
                user_db.at[idx, 'usage_count'] += 1; save_db(user_db); st.rerun()

    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)
        if st.button("🔄 다른 기술 주제 더 보기"):
            del st.session_state.suggestions; st.rerun()

with col2:
    st.subheader("2️⃣ 마스터 리포트 생성")
    selected_topic = st.text_input("확정 기술명", placeholder="추천받은 기술명을 입력하세요.", key=f"topic_{st.session_state.uploader_key}")
    user_guide_rep = st.text_area("💡 리포트 지시사항 (선택)", placeholder="시장규모 숫자 등 강제 지시", key=f"gp_{st.session_state.uploader_key}")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic: st.warning("기술명을 입력하세요.")
        else:
            with st.spinner('20년 경력 컨설턴트 모드로 리포트 생성 중...'):
                # 🚀 핵심: 11개 항목 전체 프롬프트 (누락 없음)
                form_prompt = f"""
                당신은 20년 경력의 벤처인증 전문 컨설턴트입니다. 신청기술 [{selected_topic}]에 대해 11개 항목 리포트를 상세히 작성하세요.
                시장 데이터는 실제 통계를 기반으로 보수적으로 작성하고 지어내지 마세요. {user_guide_rep}

                ### [1. 신청기술 요약 및 표준 양식]
                (제품명, 요약, V자 양식 필히 포함)
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
                content = [form_prompt, analysis_image] if analysis_image else form_prompt
                response = model.generate_content(content)
                st.session_state.report_sections = response.text.split('### ')
                user_db.at[idx, 'usage_count'] += 1; save_db(user_db); st.rerun()

# --- [6. 리포트 결과 출력] ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트 결과")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("💾 전체 리포트 다운로드 (.txt)", full_report, file_name=f"벤처리포트_{selected_topic}.txt")

    for section in st.session_state.report_sections:
        if section.strip():
            # 항목 제목과 내용을 분리하여 디자인 적용
            parts = section.split('\n', 1)
            title = parts[0].strip('[] ')
            body = parts[1] if len(parts) > 1 else ""
            with st.expander(f"📌 {title}", expanded=False):
                st.markdown(f'<div class="report-card">{body.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
