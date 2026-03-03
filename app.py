import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리 (배포 시 packages.txt에 poppler-utils 필요)
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [0. 페이지 설정 및 보안] ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

# 🔒 패스워드 설정 (원하실 때 이 부분을 수정하여 배포하세요)
WEEKLY_PASSWORD = "251001" 

st.sidebar.title("🔐 접근 권한 인증")
input_password = st.sidebar.text_input("이번 주 인증 코드를 입력하세요", type="password")

if input_password != WEEKLY_PASSWORD:
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.warning("⚠️ 인증 코드가 올바르지 않습니다. 임원근 컨설턴트님께 문의하여 코드를 발급받으세요.")
    st.stop() # 패스워드 틀릴 시 아래 로직 전체 차단

# --- [1. AI 엔진 설정] ---
try:
    API_KEY = st.secrets["gemini_api_key"] 
    genai.configure(api_key=API_KEY)
    # 가장 성능이 안정적인 모델로 우선 할당
    model = genai.GenerativeModel('gemini-1.5-flash')
    st.sidebar.success("✅ AI 엔진 가동 중: gemini-1.5-flash")
except Exception:
    st.error("⚠️ Secrets 설정에서 API 키를 찾을 수 없습니다.")
    st.stop()

st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

# --- [2. UI 레이아웃] ---
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
                st.error(f"PDF 변환 오류: {e}. 시스템에 poppler가 설치되어 있어야 합니다.")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청 필수 서류 9가지 준비 확인**")
        st.markdown("""
        * ✅ **사업자등록증** (현재 완료)
        * 📋 **법인등기부등본** | 📋 **부가가치세표준증명원**
        * 📋 **재무제표(3년)** | 📋 **고용/4대보험 명부**
        * 📋 **자격득실확인서** | 📋 **주주명부** | 📋 **연구개발인정서**
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
            with st.spinner('베테랑 컨설턴트의 시각으로 상세 리포트를 생성 중입니다...'):
                # 🚀 V자 표준 요약 양식이 강제 적용된 프롬프트
                form_prompt = f"""
                당신은 20년 경력의 대한민국 최고의 벤처인증 전문 컨설턴트입니다. 
                신청기술 [{selected_topic}]에 대해 다음 11개 항목을 각각 전문적인 문체로 상세히 작성하세요. 
                각 항목은 공백 포함 700자 내외의 풍부한 분량이어야 합니다.
                각 항목의 구분은 반드시 '### [항목명]' 형식을 유지하세요.

                특히 [1. 신청기술 요약 및 표준 양식]은 반드시 아래 형식을 엄격히 준수하여 출력하세요:

                신청기술(제품/서비스)명: [신청기술명]
                신청기술(제품/서비스)요약: [기술의 핵심 정의와 특징 요약]
                (벤처확인에 신청하고자 하는 기술(제품/서비스)에 대해 기술명과 간략한 소개를 작성해주시면 됩니다)
                V 기존 시장에 [문제점/불편사항] 니즈(문제)가 있는데, [기존 방식 한계] 이유로 사람들이 여전히 필요로 하고(불편을 겪고) 있음
                V 당사에서 [당사 해결 기술 방식]으로 해결책을 찾았으며, 이는 기존 시장의 기술과 비교하여 [차별화 강점 3가지]의 차이를 보유하고 있음
                V 현재 당사에서 보유 또는 개발 중인 기술명은 [기술명]으로써, 전체 시장은 국내 기준 약 [금액] 규모이며 연평균 [성장률]%의 성장을 기대할 수 있음
                V 당사 기술은 [핵심 원천 기술]에 기반하여 [기술적 특성 3가지] 특징을 갖고 있으며 혁신적인 해결책으로, 잠재고객들의 만족도가 훨씬 높을 수 있음
                V 기술에 대한 지식재산권을 출원 준비 중이며 [인원]명의 연구개발 조직을 보유하는 등 지속 발전이 가능한 기술적 역량을 보유하고 있음
                V 시장 진입을 위해 마케팅 활동을 진행 중으로 현재 [금액] 정도의 시장을 확보하고 있으며, 향후 3년간 유통망 강화 등의 마케팅 계획을 수립함
                V 이러한 성과가 가능한 이유는 당사에 독보적인 노하우와 생산자동화 역량이 있기 때문이며 향후 5년간 국내 시장 점유율 [목표]% 이상 및 매출 성장을 해낼 것임

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
                    content = [form_prompt, analysis_image] if analysis_image else form_prompt
                    response = model.generate_content(content)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"리포트 생성 오류: {e}")

# --- [3. 결과 출력] ---
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
