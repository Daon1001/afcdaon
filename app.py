import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
from datetime import datetime, date

# PDF 처리를 위한 라이브러리 (배포 시 packages.txt 필수)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [0. 페이지 설정] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

# --- [1. 사용자 관리 및 사용량 DB (자체 승인 시스템)] ---
if 'user_db' not in st.session_state:
    # 관리자 계정 설정 (incheon00@gmail.com 관리자 반영)
    st.session_state.user_db = pd.DataFrame([
        {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
        {"email": "임원근@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_month": date.today().month},
        {"email": "01092541128@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-26", "usage_count": 0, "last_month": date.today().month}
    ])

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

# 📊 월간 횟수 제한 설정 (원하시는 대로 수정 가능)
MAX_MONTHLY_LIMIT = 30 

# --- [2. 사이드바: 로그인 및 승인 신청 시스템] ---
with st.sidebar:
    st.title("🔐 접근 제어")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com").strip().lower()
        col_login, col_req = st.columns(2)
        
        if col_login.button("로그인", use_container_width=True, type="primary"):
            user_row = st.session_state.user_db[st.session_state.user_db['email'] == login_email]
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
                user_row = st.session_state.user_db[st.session_state.user_db['email'] == login_email]
                if user_row.empty:
                    new_user = {
                        "email": login_email, 
                        "approved": False, 
                        "is_admin": False, 
                        "created_at": datetime.now().strftime("%Y-%m-%d"),
                        "usage_count": 0,
                        "last_month": date.today().month
                    }
                    st.session_state.user_db = pd.concat([st.session_state.user_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.info("📩 승인 신청 완료! 관리자에게 승인을 요청하세요.")
                else:
                    st.warning("이미 등록(신청)된 이메일입니다.")
    else:
        st.success(f"👤 로그인 중: {st.session_state.authenticated_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.rerun()

    # 사용량 표시 UI
    if st.session_state.authenticated_user:
        st.divider()
        idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
        
        current_month = date.today().month
        if st.session_state.user_db.at[idx, 'last_month'] != current_month:
            st.session_state.user_db.at[idx, 'usage_count'] = 0
            st.session_state.user_db.at[idx, 'last_month'] = current_month
            
        user_usage = st.session_state.user_db.at[idx, 'usage_count']
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
    
    # 에러 해결: 가장 안정적인 정식 명칭 모델 순서대로 매칭 시도
    # 'gemini-1.5-flash'는 현재 가장 보편적으로 사용 가능한 모델명입니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ API 연결 오류: {e}")
    st.stop()

# --- [4. 관리자 전용: 사용자 승인 제어판] ---
user_idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
if st.session_state.user_db.at[user_idx, 'is_admin']:
    with st.expander("👑 관리자 전용: 사용자 승인 및 관리", expanded=False):
        st.dataframe(st.session_state.user_db, use_container_width=True)
        target_email = st.selectbox("승인/해제 대상 선택", st.session_state.user_db['email'])
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인 처리", use_container_width=True):
            st.session_state.user_db.loc[st.session_state.user_db['email'] == target_email, 'approved'] = True
            st.success(f"{target_email} 승인 완료!")
            st.rerun()
        if c2.button("🚫 승인 해제", use_container_width=True):
            st.session_state.user_db.loc[st.session_state.user_db['email'] == target_email, 'approved'] = False
            st.rerun()

# --- [5. 메인 UI 및 업종 맞춤형 가이드라인] ---
st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
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
            except: st.error("PDF 변환 오류 발생")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청 필수 서류 9가지 준비 확인**")
        
        if st.button("AI 기술 주제 추천받기"):
            if st.session_state.user_db.at[user_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
                st.error("이번 달 사용 횟수를 초과했습니다.")
            else:
                with st.spinner('종목 분석 및 기술 추천 중...'):
                    # 🚀 [업종 맞춤형 가이드라인 강화]
                    recommend_prompt = """
                    사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 제안해줘.
                    
                    **[중요 가이드라인]**
                    1. 모든 추천이 AI, 스마트, 플랫폼 등 IT 기술에만 편중되지 않도록 할 것.
                    2. 업종이 제조업인 경우: 공정 자동화, 신소재 도입, 정밀 가공 기술, 품질 검사 시스템 등 하드웨어적 혁신을 반드시 포함할 것.
                    3. 업종이 서비스/유통인 경우: 물류 혁신, 친환경 패키징, 독자적인 서비스 알고리즘 등 실질적 차별화 요소를 제안할 것.
                    4. 전문적인 기술 명칭과 함께, 왜 이것이 벤처인증(혁신성)에 유리한지 1문장씩 덧붙일 것.
                    """
                    # 리스트 형태로 정확히 전달
                    response = model.generate_content([recommend_prompt, analysis_image])
                    st.session_state.suggestions = response.text
                    st.session_state.user_db.at[user_idx, 'usage_count'] += 1
                    st.rerun()

    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if st.session_state.user_db.at[user_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
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
                    # 이미지 정보가 있으면 함께 전달하여 맥락 강화
                    input_data = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(input_data)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                    st.session_state.user_db.at[user_idx, 'usage_count'] += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"오류: {e}")

# --- [6. 결과 출력] ---
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
