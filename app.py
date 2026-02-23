import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리 (에러 방지를 위해 예외 처리 포함)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    st.error("pdf2image 라이브러리가 설치되지 않았습니다. requirements.txt를 확인하세요.")

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")
st.title("🏛️ 벤처인증 통합 컨설팅 대시보드 (PDF 지원)")

# --- 1. [유지] 동적 모델 할당 로직 ---
try:
    API_KEY = st.secrets["gemini_api_key"] 
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ 비밀 금고(Secrets)에서 API 키를 찾을 수 없습니다.")
    st.stop()

available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
except Exception as e:
    st.error(f"⚠️ 구글 AI 서버 통신 오류: {e}")
    st.stop()

target_model_name = ""
for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision', 'gemini-pro']:
    if preferred in available_models:
        target_model_name = preferred
        break

if not target_model_name and available_models:
    target_model_name = available_models[0]

model = genai.GenerativeModel(target_model_name)
st.sidebar.success(f"✅ 가동 중인 AI 엔진: **{target_model_name}**")

# --- 2. UI 레이아웃 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1️⃣ 분석 및 서류 가이드")
    # PDF 확장자 추가
    uploaded_file = st.file_uploader("사업자등록증 업로드 (JPG, PNG, PDF 지원)", type=["jpg", "png", "jpeg", "pdf"])
    
    analysis_image = None
    
    if uploaded_file:
        # PDF 파일 처리 로직
        if uploaded_file.type == "application/pdf":
            try:
                # PDF의 첫 페이지를 이미지로 변환
                pages = convert_from_bytes(uploaded_file.read())
                if pages:
                    analysis_image = pages[0]
            except Exception as e:
                st.error(f"PDF 변환 중 오류가 발생했습니다: {e}")
        else:
            # 일반 이미지 파일 처리
            analysis_image = Image.open(uploaded_file)
        
        # 파일이 정상적으로 로드된 경우 안내 메시지 출력
        if analysis_image:
            st.warning("🔔 **벤처인증 신청을 위해 아래 9가지 서류를 미리 준비해 주세요!**")
            st.markdown("""
            * ✅ **사업자등록증** (현재 업로드됨)
            * 📋 **법인등기부등본** (말소사항 포함)
            * 📋 **부가가치세표준증명원**
            * 📋 **재무제표 (최근 3개년치)**
            * 📋 **고용보험 사업장 취득자 명부**
            * 📋 **4대보험 가입자 명부**
            * 📋 **대표자 건강보험자격득실확인서**
            * 📋 **주주명부** (명판 및 인감 날인)
            * 📋 **연구개발인정서** (기업부설연구소 또는 전담부서)
            """)
            
            if st.button("AI 기술 주제 추천받기"):
                with st.spinner('종목 분석 중...'):
                    prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 전문적인 제목으로 제안해줘."
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
            with st.spinner('베테랑 컨설턴트의 시각으로 상세 리포트를 설계 중입니다...'):
                form_prompt = f"""
                신청기술 [{selected_topic}]에 대해 다음 11개 항목 리포트를 작성하세요. 
                각 항목은 700자 내외로 전문적인 스토리텔링 방식을 사용하세요.
                각 항목의 구분은 반드시 '### [항목명]' 형식을 유지하세요.
                [1. 요약, 2. 개발배경, 3. 경쟁력확보, 4. 추진경과, 5. 목표시장, 6. 경쟁사분석, 7. 시장진입(경과), 8. 시장진입(계획), 9. 특허전략, 10. 자금조달, 11. 정책자금추천]
                """
                try:
                    # 분석용 이미지가 있으면 함께 전송
                    if analysis_image:
                        response = model.generate_content([form_prompt, analysis_image])
                    else:
                        response = model.generate_content(form_prompt)
                    
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# --- 3. 결과 출력 (기존 드롭박스 로직 유지) ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 항목별 상세 컨설팅 리포트")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("전체 리포트 다운로드(.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        lines = section.split('\n')
        title = lines[0].strip('[] ')
        content = '\n'.join(lines[1:]).strip()
        with st.expander(f"📌 {title}", expanded=False):
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
