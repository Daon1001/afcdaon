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

# --- [0. 페이지 설정 및 디자인 완전 강제 적용 CSS] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

# 프리미엄 디자인 CSS (실버 블루 그라데이션 + 중앙 로그인 + 이미지 최적화)
custom_css = """
<style>
    /* 배경 그라데이션 강제 적용 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
    }
    
    /* 중앙 로그인 박스 레이아웃 최적화 */
    .login-container {
        display: flex !important;
        justify-content: center !important;
        align-items: flex-start !important;
        padding-top: 30px !important;
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

    /* 이미지 잘림 방지 및 크기 조절 */
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
        margin-top: 5px !important;
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
    
    /* 전문가 뱃지/메트릭스 박스 */
    .metric-box {
        background-color: rgba(255, 255, 255, 0.9);
        border-left: 5px solid #0b1f52;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    
    /* 리포트 카드 스타일 */
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
        # 초기 관리자 및 유저 데이터 생성
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
            {"email": "임원근@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month}
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    
    df = pd.read_csv(DB_FILE)
    # [DB 자동 복구] 구형 CSV 파일을 읽더라도 에러가 나지 않도록 누락된 열 자동 추가
    if 'usage_count' not in df.columns:
        df['usage_count'] = 0
    if 'last_month' not in df.columns:
        df['last_month'] = date.today().month
    if 'created_at' not in df.columns:
        df['created_at'] = datetime.now().strftime("%Y-%m-%d")
    if 'approved' not in df.columns:
        df['approved'] = False
    if 'is_admin' not in df.columns:
        df['is_admin'] = False
    return df

def save_db(df):
    df.to_csv(DB_FILE, index=False)

# 최신 DB 로드
user_db = load_db()

# --- [1. 시스템 세션 상태 관리] ---
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = "1"

# 📊 월간 사용 제한
MAX_MONTHLY_LIMIT = 30 

# --- [2. 중앙 집중형 로그인 화면 (네이버/STOVE 스타일)] ---
if st.session_state.authenticated_user is None:
    _, col_mid, _ = st.columns([0.5, 1, 0.5])
    
    with col_mid:
        st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
        
        # 🚀 벤처기업확인서 이미지 (파일명: venture_cert_new.png)
        try:
            logo = Image.open("venture_cert_new.png")
            st.image(logo)
        except:
            st.markdown("<h3 style='color:#0b1f52;'>🏛️ 중소기업경영지원단</h3>", unsafe_allow_html=True)
        
        st.markdown('<div class="login-title">중소기업경영지원단</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#666; font-size: 0.95rem; margin-bottom: 15px;'>벤처인증 AI 마스터 컨설턴트 로그인</p>", unsafe_allow_html=True)
        
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        
        st.write("")
        b_col1, b_col2 = st.columns(2)
        
        if b_col1.button("로그인", type="primary", use_container_width=True):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 승인 대기 중입니다. 관리자 승인을 기다려주세요.")
            else:
                st.warning("⚠️ 등록되지 않은 이메일입니다. [승인 신청]을 먼저 하세요.")
                
        if b_col2.button("승인 신청", use_container_width=True):
            if not login_email:
                st.error("이메일을 입력해주세요.")
            else:
                user_row = user_db[user_db['email'] == login_email]
                if user_row.empty:
                    new_user = pd.DataFrame([{
                        "email": login_email, 
                        "approved": False, 
                        "is_admin": False, 
                        "created_at": datetime.now().strftime("%Y-%m-%d"),
                        "usage_count": 0,
                        "last_month": date.today().month
                    }])
                    user_db = pd.concat([user_db, new_user], ignore_index=True)
                    save_db(user_db)
                    st.success("📩 승인 신청 완료! 관리자 승인을 기다려주세요.")
                else:
                    st.warning("이미 신청된 계정입니다.")
            
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# 로그인 성공 후 메인 대시보드
# =====================================================================

# --- [3. 사이드바 및 관리자 기능] ---
with st.sidebar:
    st.success(f"👤 접속 중: {st.session_state.authenticated_user}")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    
    st.divider()
    idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
    
    # 월간 초기화 로직
    current_month = date.today().month
    if user_db.at[idx, 'last_month'] != current_month:
        user_db.at[idx, 'usage_count'] = 0
        user_db.at[idx, 'last_month'] = current_month
        save_db(user_db)
        
    st.write(f"📊 월 사용량: **{user_db.at[idx, 'usage_count']} / {MAX_MONTHLY_LIMIT}**")
    st.progress(min(user_db.at[idx, 'usage_count'] / MAX_MONTHLY_LIMIT, 1.0))

# AI 엔진 설정
try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ API 키 설정 오류"); st.stop()

# 관리자 승인 제어판
if user_db.at[idx, 'is_admin']:
    with st.expander("👑 관리자 전용: 사용자 승인 관리", expanded=False):
        st.dataframe(user_db, use_container_width=True)
        target_email = st.selectbox("대상 선택", user_db['email'])
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인 처리", use_container_width=True):
            user_db.loc[user_db['email'] == target_email, 'approved'] = True
            save_db(user_db); st.rerun()
        if c2.button("🚫 승인 해제", use_container_width=True):
            user_db.loc[user_db['email'] == target_email, 'approved'] = False
            save_db(user_db); st.rerun()

# --- [4. 대시보드 메인 콘텐츠] ---
st.markdown(f"""
    <div class="premium-header">
        <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
        <p><strong>중소기업경영지원단</strong> 전문가 전용 AI 마스터 시스템</p>
    </div>
""", unsafe_allow_html=True)

col_metric, col_reset = st.columns([8, 2])
with col_metric:
    st.markdown('<div class="metric-box">💡 <strong>주식회사 욜사이트</strong>(혁신성장유형) 성공 사례 기반 최적화 엔진 가동 중</div>', unsafe_allow_html=True)
with col_reset:
    if st.button("🔄 새 기업 초기화", use_container_width=True, type="secondary"):
        for key in ['suggestions', 'report_sections']:
            if key in st.session_state: del st.session_state[key]
        st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
        st.rerun()

# --- [5. 본문 2단 레이아웃] ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 기업 분석 및 기술 추천")
    biz_type = st.radio("업종 선택", ["일반 기업 (제조/서비스)", "IT / 소프트웨어", "초기창업 (3년 미만)"], horizontal=True)
    uploaded_file = st.file_uploader("사업자등록증 업로드", type=["jpg", "png", "pdf"], key=f"up_{st.session_state.uploader_key}")
    
    analysis_image = None
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try: pages = convert_from_bytes(uploaded_file.read()); analysis_image = pages[0]
            except: st.error("PDF 변환 오류")
        else: analysis_image = Image.open(uploaded_file)
        
    user_guide_rec = st.text_area("💡 추천 가이드라인 (선택)", placeholder="예: ESG 경영 요소 강조", key=f"gr_{st.session_state.uploader_key}")
    
    if st.button("AI 기술 주제 추천 ✨", use_container_width=True):
        if user_db.at[idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도를 초과했습니다.")
        else:
            with st.spinner('분석 중...'):
                prompt = f"[{biz_type}] 분야 벤처인증 기술 주제 3개를 추천해줘. {user_guide_rec}"
                content = [prompt, analysis_image] if analysis_image else prompt
                response = model.generate_content(content)
                st.session_state.suggestions = response.text
                user_db.at[idx, 'usage_count'] += 1; save_db(user_db); st.rerun()

    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 마스터 리포트 생성")
    selected_topic = st.text_input("확정 기술명 입력", placeholder="추천받은 기술명을 입력하세요.", key=f"topic_{st.session_state.uploader_key}")
    user_guide_rep = st.text_area("💡 리포트 추가 지시 (선택)", placeholder="예: 시장 규모 숫자 강제 반영 등", key=f"gp_{st.session_state.uploader_key}")
    
    if st.button("마스터 리포트 생성 🚀", type="primary", use_container_width=True):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        elif user_db.at[idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도를 초과했습니다.")
        else:
            with st.spinner('20년 경력 컨설턴트 모드로 리포트 생성 중...'):
                # 🚀 11개 항목 전체 프롬프트 (요약 없음)
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 11개 항목을 각각 상세히 작성하세요. 
                시장 데이터는 실제 통계를 기반으로 보수적으로 작성하고 지어내지 마세요. {user_guide_rep}

                특히 [1. 신청기술 요약 및 표준 양식]은 반드시 아래 형식을 엄격히 준수하세요:
                V 기존 시장에 [문제점] 니즈가 있는데, [한계점] 이유로 필요로 함
                V 당사에서 [해결방식]으로 해결책을 찾았으며, 기존 대비 [차별점 3가지] 보유
                V 현재 기술명은 [{selected_topic}]이며, 시장 규모는 [금액], 연평균 [성장률]% 성장 기대

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
                content = [form_prompt, analysis_image] if analysis_image else form_prompt
                response = model.generate_content(content)
                st.session_state.report_sections = response.text.split('### ')
                user_db.at[idx, 'usage_count'] += 1; save_db(user_db); st.rerun()

# --- [6. 결과 출력 및 다운로드] ---
if 'report_sections' in st.session_state:
    st.divider()
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트 결과")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("💾 전체 리포트 다운로드 (.txt)", full_report, file_name=f"벤처리포트_{selected_topic}.txt", use_container_width=True)

    for section in st.session_state.report_sections:
        if section.strip():
            # 항목 제목과 내용 분리
            parts = section.split('\n', 1)
            title = parts[0].strip('[] ')
            body = parts[1] if len(parts) > 1 else ""
            with st.expander(f"📌 {title}", expanded=False):
                st.markdown(f'<div class="report-card">{body.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
