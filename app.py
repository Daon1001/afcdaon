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

# --- [0. 페이지 설정 및 CSV DB 설정] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

DB_FILE = "users.csv"

def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
            {"email": "임원근@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
            {"email": "01092541128@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-26", "usage_count": 0, "last_month": date.today().month}
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    return pd.read_csv(DB_FILE)

def save_db(df):
    df.to_csv(DB_FILE, index=False)

# 페이지 로드 시 최신 DB 읽어오기
user_db = load_db()

# --- [1. 시스템 초기화 및 세션 상태 관리] ---
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = "1"

# 📊 월간 횟수 제한 설정
MAX_MONTHLY_LIMIT = 30 

# --- [2. 사이드바: 로그인 및 승인 신청 시스템 (DB 연동)] ---
with st.sidebar:
    st.title("🔐 접근 제어")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com").strip().lower()
        col_login, col_req = st.columns(2)
        
        if col_login.button("로그인", use_container_width=True, type="primary"):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 승인 대기 중입니다. 관리자 승인을 기다려주세요.")
            else:
                st.warning("⚠️ 등록되지 않은 이메일입니다. [승인 신청]을 먼저 하세요.")

        if col_req.button("승인 신청", use_container_width=True):
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
                    st.info("📩 승인 신청 완료! 관리자에게 승인을 요청하세요.")
                else:
                    st.warning("이미 등록(신청)된 이메일입니다.")
    else:
        st.success(f"👤 로그인 중: {st.session_state.authenticated_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.rerun()

    # 사용량 표시 UI 및 월간 초기화
    if st.session_state.authenticated_user:
        st.divider()
        idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
        
        current_month = date.today().month
        if user_db.at[idx, 'last_month'] != current_month:
            user_db.at[idx, 'usage_count'] = 0
            user_db.at[idx, 'last_month'] = current_month
            save_db(user_db)
            
        user_usage = user_db.at[idx, 'usage_count']
        remaining = MAX_MONTHLY_LIMIT - user_usage
        st.caption("🛡️ 개인별 월간 사용량")
        st.write(f"나의 사용량: **{user_usage} / {MAX_MONTHLY_LIMIT}**")
        st.progress(min(user_usage / MAX_MONTHLY_LIMIT, 1.0))

# --- [3. 로그인 체크 및 AI 모델 매칭 로직] ---
if st.session_state.authenticated_user is None:
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 사이드바에서 이메일 로그인 후 이용 가능합니다.")
    st.stop()

try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
    
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
            
    target_model_name = ""
    for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
        if preferred in available_models:
            target_model_name = preferred
            break
            
    if not target_model_name and available_models:
        target_model_name = available_models[0]
        
    model = genai.GenerativeModel(target_model_name)
    st.sidebar.success(f"✅ 가동 중인 AI 엔진: **{target_model_name}**")
except Exception as e:
    st.error(f"⚠️ API 연결 오류: {e}")
    st.stop()

# --- [4. 관리자 전용: 사용자 승인 제어판 (DB 연동)] ---
user_idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
if user_db.at[user_idx, 'is_admin']:
    with st.expander("👑 관리자 전용: 사용자 승인 및 관리", expanded=False):
        # 최신 DB 정보를 보여줍니다. 동료가 신청하면 새로고침 시 여기에 뜹니다.
        st.dataframe(user_db, use_container_width=True)
        target_email = st.selectbox("승인/해제 대상 선택", user_db['email'])
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인 처리", use_container_width=True):
            user_db.loc[user_db['email'] == target_email, 'approved'] = True
            save_db(user_db)
            st.success(f"{target_email} 승인 완료!")
            st.rerun()
        if c2.button("🚫 승인 해제", use_container_width=True):
            user_db.loc[user_db['email'] == target_email, 'approved'] = False
            save_db(user_db)
            st.rerun()

# --- [5. 메인 UI (타이틀 및 초기화 버튼)] ---
col_title, col_reset = st.columns([8, 2])
with col_title:
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
with col_reset:
    st.write("") 
    if st.button("🔄 새 기업 컨설팅 시작 (초기화)", use_container_width=True, type="secondary"):
        for key in ['suggestions', 'report_sections']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
        st.rerun()

# --- [6. 본문 기능 영역] ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 서류 가이드")
    
    biz_type = st.radio(
        "🏢 컨설팅 대상 기업의 업종/업력을 선택하세요",
        ["일반 기업 (제조/서비스 등)", "IT / 소프트웨어", "예비창업자 및 3년 미만 초기기업"],
        horizontal=False
    )
    
    uploaded_file = st.file_uploader("사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "png", "jpeg", "pdf"], key=st.session_state.uploader_key)
    analysis_image = None
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                pages = convert_from_bytes(uploaded_file.read())
                if pages: analysis_image = pages[0]
            except: st.error("PDF 변환 오류 발생")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning(f"🔔 **[{biz_type}] 벤처인증 신청 필수 서류 확인**")
        
        if biz_type == "일반 기업 (제조/서비스 등)":
            st.markdown("""
            1. ✅ **사업자등록증명원** (또는 사업자등록증 사본)
            2. 📋 **법인등기부등본** (말소사항 포함, 최근 3개월 이내 발급분)
            3. 📋 **재무제표** (최근 3개년치 - 재무상태표, 손익계산서 등 포함)
            4. 📋 **부가가치세과세표준증명원** (최근 3개년치)
            5. 📋 **고용보험 사업장 취득자 명부** (전체 인원 확인용)
            6. 📋 **4대 사회보험 사업장 가입자 명부**
            7. 📋 **주주명부** (최근 결산기 기준, 명판 및 인감 날인 필수)
            8. 📋 **기업부설연구소 인증서** (또는 연구개발전담부서 인정서)
            9. 📋 **지식재산권 등록증/출원서** (특허, 실용신안 등 기술력 증빙 서류)
            """)
        elif biz_type == "IT / 소프트웨어":
            st.markdown("""
            1. ✅ **사업자등록증명원** (또는 사업자등록증 사본)
            2. 📋 **법인등기부등본** (말소사항 포함)
            3. 📋 **재무제표 & 부가세증명원** (최근 3개년치)
            4. 📋 **고용/4대보험 가입자 명부** (핵심 개발 인력 비율 확인 필수)
            5. 📋 **주주명부** (최근 결산기 기준, 명판 및 인감 날인 필수)
            6. 📋 **기업부설연구소/전담부서 인정서**
            7. 📋 **프로그램 등록증 및 지식재산권** (SW 저작권 등 필수 증빙)
            8. 📋 **서비스/앱 소개서 및 UI/UX 화면 캡처본** (실적 및 기술성 증빙 보조자료)
            9. 📋 **서버 및 도메인 등록 관련 증빙** (필요시)
            """)
        else:
            st.markdown("""
            1. ✅ **사업자등록증명원** (창업 기업) / 예비창업자는 대표자 신분증 사본
            2. 📋 **법인등기부등본** (법인인 경우 설립일 기준)
            3. 📋 **재무제표 및 부가세증명원** (설립일~최근 결산일, 재무 실적 없으면 추정재무제표)
            4. 📋 **고용/4대보험 가입자 명부** (현재 채용 인원 기준)
            5. 📋 **주주명부** (현재 기준 명판 및 인감 날인)
            6. 📋 **사업계획서** (초기 창업자용 상세 비즈니스 모델 및 기술 계획서 필수)
            7. 📋 **지식재산권 출원서** (등록 전이라도 기술 준비 상황을 증빙할 출원번호 통지서)
            8. 📋 **대표자 및 핵심인력 이력서/경력증명서** (인적 역량 평가용)
            9. 📋 **연구소/전담부서 인정서** (설립된 경우)
            """)
        
        suggestion_placeholder = st.empty()

        if st.button("AI 기술 주제 추천받기"):
            if user_db.at[user_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
                st.error("이번 달 사용 횟수를 초과했습니다.")
            else:
                with st.spinner('종목 분석 및 기술 추천 중...'):
                    recommend_prompt = f"""
                    사업자등록증의 종목을 분석하여 [{biz_type}] 분야의 벤처인증용 혁신 기술 주제 3개를 제안해줘.
                    
                    **[중요 가이드라인]**
                    1. 모든 추천이 AI, 스마트, 플랫폼 등 특정 기술에만 편중되지 않도록 할 것.
                    2. 업종이 제조업인 경우: 공정 자동화, 신소재 도입, 정밀 가공 기술 등 하드웨어적 혁신 포함.
                    3. 업종이 서비스/유통/SW인 경우: 물류 혁신, 친환경 패키징, 독자적인 서비스 알고리즘 등 실질적 차별화 요소 제안.
                    4. 전문적인 기술 명칭과 함께, 왜 이것이 벤처인증(혁신성)에 유리한지 1문장씩 덧붙일 것.
                    """
                    response = model.generate_content([recommend_prompt, analysis_image])
                    st.session_state.suggestions = response.text
                    user_db.at[user_idx, 'usage_count'] += 1
                    save_db(user_db)
                    st.rerun()

        if 'suggestions' in st.session_state and st.session_state.suggestions:
            suggestion_placeholder.success(st.session_state.suggestions)
            
            if st.button("🔄 다른 기술 주제 더 보기"):
                if user_db.at[user_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
                    st.error("이번 달 사용 횟수를 초과했습니다.")
                else:
                    suggestion_placeholder.empty()
                    st.session_state.suggestions = "" 
                    
                    with st.spinner('새로운 혁신 관점으로 다시 탐색 중입니다...'):
                        retry_prompt = f"""
                        사업자등록증의 종목을 분석하여 [{biz_type}] 분야의 벤처인증용 혁신 기술 주제 3개를 '새롭게' 제안해줘.
                        이전에 제안했던 흔한 주제들은 완전히 배제하고, 새로운 융합 기술이나 최신 트렌드를 반영한 완전히 다른 시각에서 접근할 것.
                        
                        **[중요 가이드라인]**
                        1. 모든 추천이 AI, 스마트, 플랫폼 등 특정 기술에만 편중되지 않도록 할 것.
                        2. 업종이 제조업인 경우: 공정 자동화, 신소재 도입, 정밀 가공 기술 등 하드웨어적 혁신 포함.
                        3. 업종이 서비스/유통/SW인 경우: 물류 혁신, 친환경 패키징, 독자적인 서비스 알고리즘 등 실질적 차별화 요소 제안.
                        4. 전문적인 기술 명칭과 함께, 왜 이것이 벤처인증(혁신성)에 유리한지 1문장씩 덧붙일 것.
                        """
                        response = model.generate_content([retry_prompt, analysis_image])
                        st.session_state.suggestions = response.text
                        user_db.at[user_idx, 'usage_count'] += 1
                        save_db(user_db)
                        st.rerun()

with col2:
    st.subheader("2️⃣ 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하거나 왼쪽에서 복사하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if user_db.at[user_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
            st.error("이번 달 사용 횟수를 초과했습니다.")
        elif not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 11개 항목 리포트를 생성 중입니다...'):
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 11개 항목을 각각 상세히 작성하세요. 
                각 항목은 공백 포함 700자 내외의 풍부한 분량이어야 합니다.

                특히 [1. 신청기술 요약 및 표준 양식]은 반드시 아래 형식을 엄격히 준수하세요:

                신청기술(제품/서비스)명: [{selected_topic}]
                신청기술(제품/서비스)요약: [기술의 핵심 정의와 특징 요약]
                (벤처확인에 신청하고자 하는 기술(제품/서비스)에 대해 기술명과 간략한 소개를 작성해주시면 됩니다)
                V 기존 시장에 [문제점] 니즈(문제)가 있는데, [한계점] 이유로 사람들이 여전히 필요로 하고 있음
                V 당사에서 [해결방식]으로 해결책을 찾았으며, 기존 시장 기술 대비 [차별점 3가지] 보유
                V 현재 기술명은 [{selected_topic}]이며, 시장 규모는 [금액], 연평균 [성장률]% 성장이 기대됨
                V 핵심 기술력 기반 [특징 3가지]를 가지며, 잠재고객 만족도가 훨씬 높을 수 있음
                V 지식재산권 출원 준비 및 연구개발 조직 보유로 지속 발전 역량 확보
                V 마케팅 활동 진행으로 현재 [규모] 시장 확보, 향후 3년 유통망 강화 계획 수립
                V 독보적인 노하우와 역량으로 향후 5년 점유율 [목표]% 이상 달성 및 매출 성장 기대

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
                    input_data = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(input_data)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                    user_db.at[user_idx, 'usage_count'] += 1
                    save_db(user_db)
                    st.rerun()
                except Exception as e:
                    st.error(f"오류: {e}")

# --- [7. 결과 출력] ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("전체 리포트 다운로드(.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        if section.strip():
            lines = section.split('\n')
            title = lines[0].strip('[] ')
            content = '\n'.join(lines[1:]).strip()
            with st.expander(f"📌 {title}", expanded=False):
                st.markdown(f"<div style='background-color: #f8f9fa; padding: 25px; border-radius: 12px; line-height: 1.9; border-left: 6px solid #007bff;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
