import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime, date
import os
import io

# --- [1. 페이지 설정 및 시스템 초기화] ---
st.set_page_config(page_title="기업부설연구소 연구과제 추출기", layout="wide", page_icon="🏢")

# CSV 데이터베이스 설정
DB_FILE = "users.csv"
MAX_DAILY_LIMIT = 10  # 일일 사용량 한도

def load_db():
    current_date_str = date.today().strftime("%Y-%m-%d")
    if not os.path.exists(DB_FILE):
        # 파일이 없으면 초기 DB 생성 (관리자 기본 세팅)
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_date": current_date_str},
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    else:
        # 기존 DB 로드 및 호환성 처리 (last_month가 있다면 last_date로 변경)
        df = pd.read_csv(DB_FILE)
        if 'last_date' not in df.columns:
            df['last_date'] = current_date_str
            if 'last_month' in df.columns:
                df = df.drop(columns=['last_month'])
            df.to_csv(DB_FILE, index=False)
        return df

def save_db(df):
    df.to_csv(DB_FILE, index=False)

# 페이지 로드 시 항상 최신 DB를 읽어옵니다.
user_db = load_db()

# [동적 키 제어 로직] API 키를 안전하게 가져오는 함수
def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        return None
    except:
        return None

# 세션 초기화
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if 'research_topics' not in st.session_state:
    st.session_state.research_topics = ""

# --- [2. 사이드바: 로그인 및 승인 관리] ---
with st.sidebar:
    st.title("🔐 컨설턴트 인증")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com").strip().lower()
        col_login, col_req = st.columns(2)
        
        # 로그인
        if col_login.button("로그인", use_container_width=True, type="primary"):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 승인 대기 중입니다.")
            else:
                st.warning("⚠️ [승인 신청]을 먼저 하세요.")

        # 승인 신청
        if col_req.button("승인 신청", use_container_width=True):
            if "@" in login_email:
                if login_email not in user_db['email'].values:
                    new_user = pd.DataFrame([{
                        "email": login_email, 
                        "approved": False, 
                        "is_admin": False, 
                        "usage_count": 0, 
                        "last_date": date.today().strftime("%Y-%m-%d")
                    }])
                    user_db = pd.concat([user_db, new_user], ignore_index=True)
                    save_db(user_db)
                    st.info("📩 신청 완료! 관리자에게 승인을 요청하세요.")
                else:
                    st.warning("이미 신청된 이메일입니다.")
            else:
                st.error("이메일 형식을 확인하세요.")
    else:
        st.success(f"👤 {st.session_state.authenticated_user}님")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.session_state.research_topics = ""
            st.rerun()

    # 일일 사용량 관리 및 자동 초기화
    if st.session_state.authenticated_user:
        st.divider()
        idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
        
        # 일간 초기화 로직 (날짜가 바뀌었으면 0으로 리셋)
        current_date_str = date.today().strftime("%Y-%m-%d")
        if str(user_db.at[idx, 'last_date']) != current_date_str:
            user_db.at[idx, 'usage_count'] = 0
            user_db.at[idx, 'last_date'] = current_date_str
            save_db(user_db)
            
        u_count = user_db.at[idx, 'usage_count']
        is_admin_user = user_db.at[idx, 'is_admin']
        
        st.caption("🛡️ 일일 사용 현황")
        if is_admin_user:
            st.write("권한: **관리자 (무제한)**")
        else:
            st.write(f"오늘 사용량: **{u_count} / {MAX_DAILY_LIMIT}**회")
            st.progress(min(u_count / MAX_DAILY_LIMIT, 1.0))

# --- [3. 메인 화면 구성 및 API 동적 체크] ---
if st.session_state.authenticated_user is None:
    st.title("🏢 기업부설연구소 연구과제 추출기")
    st.info("💡 사이드바에서 이메일 로그인 후 이용 가능합니다.")
    st.stop()

# API 키 동적 로드 및 검증
api_key = get_api_key()
if not api_key:
    st.error("❌ API 키가 설정되지 않았습니다. 관리자 페이지(Secrets)를 확인해주세요.")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ AI 엔진 연결 중 오류가 발생했습니다: {e}")
    st.stop()

# 관리자 제어판 (DB 연동)
user_idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
if user_db.at[user_idx, 'is_admin']:
    with st.expander("👑 [관리자] 사용자 승인 관리", expanded=False):
        st.dataframe(user_db, use_container_width=True)
        pending = user_db[user_db['approved'] == False]['email'].tolist()
        if pending:
            target = st.selectbox("승인할 사용자", pending)
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인 완료", use_container_width=True):
                user_db.loc[user_db['email'] == target, 'approved'] = True
                save_db(user_db)
                st.rerun()
            if c2.button("🚫 승인 거절(삭제)", use_container_width=True):
                user_db = user_db[user_db['email'] != target]
                save_db(user_db)
                st.rerun()

st.title("🏢 기업부설연구소 연구과제 추출기")
st.markdown("---")

uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (이미지/PDF)", type=["jpg", "jpeg", "png", "pdf"])

col1, col2 = st.columns(2)
with col1:
    biz_type = st.text_input("업태", value="제조업")
with col2:
    biz_item = st.text_input("종목", placeholder="예: PVP 창호 프레임 제조")

# --- [4. 분석 실행 함수] ---
def analyze_research(refresh=False):
    # 최신 DB 정보를 다시 확인
    current_db = load_db()
    u_idx = current_db[current_db['email'] == st.session_state.authenticated_user].index[0]
    
    if not current_db.at[u_idx, 'is_admin']:
        if current_db.at[u_idx, 'usage_count'] >= MAX_DAILY_LIMIT:
            st.error("🚫 일일 사용 한도를 모두 소모하셨습니다. 내일 다시 시도해주세요.")
            return

    with st.spinner("전문 기술 스펙트럼 분석 중..."):
        try:
            variation = "이전과 중복되지 않는 관점에서" if refresh else ""
            prompt = f"""
            당신은 중소기업 기술 컨설팅 전문가입니다. 
            업태와 종목을 분석하여 KOITA 인정용 '연구과제' 3가지를 제안하세요.
            [가이드라인]
            1. IT 편향을 버리고 하드웨어/공정 혁신(자동화, 신소재, 부품국산화 등)을 포함할 것.
            2. {variation} 작성할 것.
            [양식] 분류 / 연구과제명 / 목표 및 효과 / 종목 연관성
            """
            
            if uploaded_file:
                if uploaded_file.type == "application/pdf":
                    response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}])
                else:
                    response = model.generate_content([prompt, Image.open(uploaded_file)])
            else:
                response = model.generate_content(f"{prompt}\n업태:{biz_type}, 종목:{biz_item}")
            
            st.session_state.research_topics = response.text
            
            # 사용량 증가 및 CSV 저장
            current_db.at[u_idx, 'usage_count'] += 1
            save_db(current_db)
            st.rerun()
                
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")

# 버튼 및 결과
b1, b2 = st.columns(2)
with b1:
    if st.button("🚀 연구과제 분석하기", use_container_width=True, key="main_analyze"):
        analyze_research(refresh=False)
with b2:
    if st.session_state.research_topics:
        if st.button("🔄 새로운 연구과제 보기", use_container_width=True, key="refresh_analyze"):
            analyze_research(refresh=True)

if st.session_state.research_topics:
    st.success("✅ 분석 완료")
    st.markdown(st.session_state.research_topics)
    with st.expander("📋 필수 서류 안내"):
        st.markdown("도면, 현판(두께포함), 내부사진, 조직도, 재무제표, 4대보험명부 등")
