import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
from datetime import datetime

# PDF 처리를 위한 라이브러리 (배포 시 packages.txt 필수)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [0. 페이지 설정] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

# --- [1. 사용자 관리 DB (스크린샷 방식 구현)] ---
if 'user_db' not in st.session_state:
    # 기본 관리자 계정 설정
    st.session_state.user_db = pd.DataFrame([
        {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-14 15:17:32"},
        {"email": "01092541128@gmail.com", "approved": True, "is_admin": True, "created_at": "2026-02-26 09:00:00"}
    ])

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

# --- [2. 사이드바: 접근 제어 및 사용량 방어] ---
with st.sidebar:
    st.title("🔐 접근 제어")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com")
        col_l, col_r = st.columns(2)
        if col_l.button("로그인", use_container_width=True):
            user_row = st.session_state.user_db[st.session_state.user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 승인 대기 중입니다.")
            else:
                # 신규 신청 자동 등록
                new_user = {"email": login_email, "approved": False, "is_admin": False, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                st.session_state.user_db = pd.concat([st.session_state.user_db, pd.DataFrame([new_user])], ignore_index=True)
                st.warning("📩 승인 신청되었습니다.")
    else:
        st.success(f"👤 로그인: {st.session_state.authenticated_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.rerun()

    st.divider()
    st.caption("🛡️ 사용량/비용 방어")
    st.write(f"오늘 사용량: 0 / 5 (잔여 5)")
    st.progress(0.1)
    st.caption("이달 사용량: 7 / 100")

# --- [3. 로그인 체크 및 AI 설정] ---
if st.session_state.authenticated_user is None:
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 사이드바에서 이메일 로그인 후 이용 가능합니다.")
    st.stop()

try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ API 키 설정을 확인하세요.")
    st.stop()

# --- [4. 관리자 전용 섹션 (스크린샷 기능 구현)] ---
current_user_row = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user]
if not current_user_row.empty and current_user_row.iloc[0]['is_admin']:
    with st.expander("👑 관리자: 사용자 승인/관리", expanded=False):
        st.dataframe(st.session_state.user_db, use_container_width=True)
        target_email = st.selectbox("대상 이메일 선택", st.session_state.user_db['email'])
        c1, c2 = st.columns(2)
        if c1.button("✅ 승인 완료", use_container_width=True):
            st.session_state.user_db.loc[st.session_state.user_db['email'] == target_email, 'approved'] = True
            st.rerun()
        if c2.button("🚫 승인 해제", use_container_width=True):
            st.session_state.user_db.loc[st.session_state.user_db['email'] == target_email, 'approved'] = False
            st.rerun()

# --- [5. 메인 UI: 기존 분석 및 리포트 로직 전체 복구] ---
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
            except Exception as e:
                st.error(f"PDF 변환 오류: {e}")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청 필수 서류 9가지 준비 확인**")
        st.markdown("""
        * ✅ **사업자등록증** | 📋 **법인등기부등본** | 📋 **재무제표(3년)** * 📋 **고용/4대보험 명부** | 📋 **자격득실확인서** | 📋 **연구개발인정서** 등
        """)
        
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('종목 분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 제안해줘."
                response = model.generate_content([prompt, analysis_image])
                st.session_state.suggestions = response.text
                
    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 상세 리포트를 설계 중입니다...'):
                # 🚀 11개 항목 상세 프롬프트 완전 복구
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 11개 항목을 각각 전문적인 문체로 상세히 작성하세요. 
                각 항목은 공백 포함 700자 내외의 풍부한 분량이어야 하며 '### [항목명]' 형식을 유지하세요.

                ### [1. 신청기술 요약 및 표준 양식] (V자 양식 포함)
                ### [2. 개발배경 및 원인분석] (산업적 필요성 분석)
                ### [3. 경쟁력 확보방안] (핵심 기술력 및 차별화)
                ### [4. 추진경과 및 향후 계획] (R&D 실적 및 로드맵)
                ### [5. 목표시장 및 고객정의] (시장 규모 및 핵심 타겟)
                ### [6. 경쟁사 분석 및 우위성] (우위 요소 분석)
                ### [7. 시장진입 및 확대전략 - 추진경과] (마케팅 성과)
                ### [8. 시장진입 및 확대전략 - 향후계획] (글로벌 확장 전략)
                ### [9. 지식재산권 및 특허 전략] (특허 아이디어 3종)
                ### [10. 자금조달 계획의 구체적 방안] (자금 선순환 구조)
                ### [11. 연계 가능 정책자금 추천] (기보, 신보 자금 매칭)
                """
                try:
                    content = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(content)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# --- [6. 결과 출력] ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 벤처인증 마스터 컨설팅 리포트")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("전체 리포트 다운로드(.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        lines = section.split('\n')
        title = lines[0].strip('[] ')
        content = '\n'.join(lines[1:]).strip()
        with st.expander(f"📌 {title}", expanded=False):
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 25px; border-radius: 12px; line-height: 1.9; border-left: 6px solid #007bff;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
