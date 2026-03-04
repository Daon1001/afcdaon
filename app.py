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

# --- [0. 페이지 설정 및 프리미엄 CSS 디자인 적용] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

# 고급스러운 UI를 위한 커스텀 CSS (벤처확인서 감성: 남색+금색 포인트)
custom_css = """
<style>
    /* 메인 그라데이션 헤더 */
    .premium-header {
        background: linear-gradient(135deg, #0b1f52 0%, #1a3673 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 12px;
        border-bottom: 5px solid #d4af37;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .premium-header h1 {
        color: white;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .premium-header p {
        color: #e0e0e0;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* 전문가 뱃지/메트릭스 박스 */
    .metric-box {
        background-color: #f8f9fa;
        border-left: 5px solid #0b1f52;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* 입체적인 버튼 디자인 */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    
    /* 기본 배경 및 폰트 다듬기 */
    .stApp {
        background-color: #fafbfc;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- CSV DB 설정 (자동 복구 로직 포함) ---
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
    
    df = pd.read_csv(DB_FILE)
    
    # 구형 CSV 파일을 읽더라도 에러가 나지 않도록 누락된 열 자동 추가
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

user_db = load_db()

# --- [1. 시스템 초기화 및 세션 상태 관리] ---
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

# 화면 완전 초기화를 위한 고유 키 관리
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = "1"

# 📊 월간 횟수 제한 설정
MAX_MONTHLY_LIMIT = 30 

# --- [2. 사이드바: 로그인 및 승인 신청 시스템] ---
with st.sidebar:
    st.title("🔐 컨설턴트 전용 로그인")
    
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
                    st.error("❌ 승인 대기 중입니다.")
            else:
                st.warning("⚠️ 등록되지 않은 이메일입니다.")

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
                    st.info("📩 승인 신청 완료!")
                else:
                    st.warning("이미 등록(신청)된 이메일입니다.")
    else:
        st.success(f"👤 접속 중: {st.session_state.authenticated_user}")
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
        st.caption("🛡️ 이번 달 사용 현황")
        st.write(f"사용량: **{user_usage} / {MAX_MONTHLY_LIMIT} 회**")
        st.progress(min(user_usage / MAX_MONTHLY_LIMIT, 1.0))

# --- [3. 로그인 체크 및 AI 모델 매칭 로직] ---
if st.session_state.authenticated_user is None:
    st.markdown("""
        <div class="premium-header">
            <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
            <p>20년 경력의 노하우와 AI 기술의 완벽한 결합 | 혁신성장유형 마스터</p>
        </div>
    """, unsafe_allow_html=True)
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
except Exception as e:
    st.error(f"⚠️ API 연결 오류: {e}")
    st.stop()

# --- [4. 관리자 전용: 사용자 승인 제어판] ---
user_idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
if user_db.at[user_idx, 'is_admin']:
    with st.expander("👑 관리자 전용: 사용자 승인 및 관리", expanded=False):
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

# --- [5. 메인 UI (프리미엄 헤더 및 초기화 버튼)] ---
st.markdown("""
    <div class="premium-header">
        <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
        <p>20년 경력의 노하우와 AI 기술의 완벽한 결합 | <strong>혁신성장유형 마스터</strong></p>
    </div>
""", unsafe_allow_html=True)

col_metric, col_reset = st.columns([8, 2])
with col_metric:
    st.markdown("""
        <div class="metric-box">
            💡 <strong>스마트 가이드:</strong> 업종별 필수 서류를 자동으로 분류하고, AI가 11개 항목의 전문 리포트를 즉시 생성합니다.
        </div>
    """, unsafe_allow_html=True)
with col_reset:
    if st.button("🔄 새 기업 컨설팅 시작", use_container_width=True):
        for key in ['suggestions', 'report_sections']:
            if key in st.session_state:
                del st.session_state[key]
        # 키값을 올려 모든 입력창과 파일업로더를 완전 리셋
        st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
        st.rerun()

# --- [6. 본문 기능 영역] ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 기업 분석 및 서류 가이드")
    
    biz_type = st.radio(
        "🏢 컨설팅 대상 기업의 업종/업력을 선택하세요",
        ["일반 기업 (제조/서비스 등)", "IT / 소프트웨어", "예비창업자 및 3년 미만 초기기업"],
        horizontal=False
    )
    
    uploaded_file = st.file_uploader("사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "png", "jpeg", "pdf"], key=f"uploader_{st.session_state.uploader_key}")
    analysis_image = None
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                pages = convert_from_bytes(uploaded_file.read())
                if pages: analysis_image = pages[0]
            except: st.error("PDF 변환 오류 발생")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.info(f"📋 **[{biz_type}] 필수 증빙 서류 목록**")
        
        if biz_type == "일반 기업 (제조/서비스 등)":
            st.markdown("""
            1. ✅ **사업자등록증명원** (또는 사본)
            2. 📋 **법인등기부등본** (말소사항 포함)
            3. 📋 **재무제표** (최근 3개년치)
            4. 📋 **부가가치세과세표준증명원** (최근 3개년치)
            5. 📋 **고용보험 사업장 취득자 명부**
            6. 📋 **4대 사회보험 사업장 가입자 명부**
            7. 📋 **주주명부** (명판 및 인감 날인 필수)
            8. 📋 **기업부설연구소/전담부서 인정서**
            9. 📋 **지식재산권 등록증/출원서**
            """)
        elif biz_type == "IT / 소프트웨어":
            st.markdown("""
            1. ✅ **사업자등록증명원**
            2. 📋 **법인등기부등본**
            3. 📋 **재무제표 & 부가세증명원**
            4. 📋 **고용/4대보험 가입자 명부** (개발 인력 확인)
            5. 📋 **주주명부**
            6. 📋 **기업부설연구소/전담부서 인정서**
            7. 📋 **프로그램 등록증 및 지식재산권**
            8. 📋 **서비스/앱 소개서 및 UI/UX 화면**
            9. 📋 **서버 및 도메인 등록 관련 증빙**
            """)
        else:
            st.markdown("""
            1. ✅ **사업자등록증명원** (예비창업자는 신분증 사본)
            2. 📋 **법인등기부등본**
            3. 📋 **재무제표 및 부가세증명원** (추정재무제표 가능)
            4. 📋 **고용/4대보험 가입자 명부**
            5. 📋 **주주명부**
            6. 📋 **사업계획서** (상세 비즈니스 모델 필수)
            7. 📋 **지식재산권 출원서** (출원번호 통지서 가능)
            8. 📋 **대표자 및 핵심인력 이력서/경력증명서**
            9. 📋 **연구소/전담부서 인정서** (설립된 경우)
            """)
        
        user_guide_rec = st.text_area(
            "💡 AI 기술 추천 가이드라인 (선택)", 
            placeholder="예: 친환경 패키징 기술 위주로 추천해 주세요.", 
            key=f"guide_rec_{st.session_state.uploader_key}"
        )
        
        suggestion_placeholder = st.empty()

        if st.button("AI 기술 주제 추천받기 ✨"):
            if user_db.at[user_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
                st.error("이번 달 사용 횟수를 초과했습니다.")
            else:
                with st.spinner('종목 분석 및 기술 추천 중...'):
                    recommend_prompt = f"""
                    사업자등록증의 종목을 분석하여 [{biz_type}] 분야의 벤처인증용 혁신 기술 주제 3개를 제안해줘.
                    
                    **[기본 가이드라인]**
                    1. 모든 추천이 특정 IT 기술에만 편중되지 않도록 할 것.
                    2. 업종이 제조업인 경우: 공정 자동화, 신소재 도입 등 하드웨어적 혁신 포함.
                    3. 전문적인 기술 명칭과 함께, 왜 이것이 벤처인증(혁신성)에 유리한지 1문장씩 덧붙일 것.
                    """
                    
                    if user_guide_rec.strip():
                        recommend_prompt += f"\n\n**[컨설턴트 특별 요청사항]**\n다음 내용을 최우선으로 반영하여 추천할 것: {user_guide_rec}"
                    
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
                        이전에 제안했던 흔한 주제들은 완전히 배제하고, 완전히 다른 시각에서 접근할 것.
                        
                        **[기본 가이드라인]**
                        1. 모든 추천이 특정 기술에만 편중되지 않도록 할 것.
                        2. 업종에 맞는 하드웨어/소프트웨어 혁신 반영.
                        3. 전문적인 기술 명칭과 함께 벤처인증 유리 이유 1문장 추가.
                        """
                        
                        if user_guide_rec.strip():
                            retry_prompt += f"\n\n**[컨설턴트 특별 요청사항]**\n다음 내용을 최우선으로 반영하여 추천할 것: {user_guide_rec}"
                        
                        response = model.generate_content([retry_prompt, analysis_image])
                        st.session_state.suggestions = response.text
                        user_db.at[user_idx, 'usage_count'] += 1
                        save_db(user_db)
                        st.rerun()

with col2:
    st.subheader("2️⃣ 마스터 리포트 생성")
    selected_topic = st.text_input(
        "신청기술명 확정:", 
        placeholder="추천받은 기술명을 복사하여 붙여넣으세요.",
        key=f"topic_{st.session_state.uploader_key}"
    )
    
    user_guide_rep = st.text_area(
        "💡 리포트 맞춤형 지시사항 (선택)", 
        placeholder="예: 6번 경쟁사 분석 항목에 A사와의 차별점을 집중 서술. 시장 규모는 5조 원으로 기입.", 
        key=f"guide_rep_{st.session_state.uploader_key}"
    )
    
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

                **[데이터 작성 엄격 가이드]**
                1. 시장 규모, 연평균 성장률 등 숫자 데이터는 절대 허구로 지어내지 마세요.
                2. 신뢰할 수 있는 산업 통계를 기반으로 현실적이고 보수적인 수치를 작성하세요.

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
                
                if user_guide_rep.strip():
                    form_prompt += f"\n\n**[컨설턴트 특별 요청사항]**\n리포트 작성 시 다음 지시사항을 반드시 지켜서 반영할 것:\n{user_guide_rep}"
                
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
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트 결과")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("💾 전체 리포트 다운로드 (.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        if section.strip():
            lines = section.split('\n')
            title = lines[0].strip('[] ')
            content = '\n'.join(lines[1:]).strip()
            with st.expander(f"📌 {title}", expanded=False):
                st.markdown(f"<div style='background-color: white; padding: 25px; border-radius: 8px; line-height: 1.8; border: 1px solid #e0e0e0; border-left: 5px solid #0b1f52;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
