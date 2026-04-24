import streamlit as st
import anthropic
from PIL import Image
import io
import base64
import json
import os
from datetime import datetime, date

# ── 페이지 설정 ──
st.set_page_config(
    page_title="벤처인증 AI 마스터 컨설턴트",
    page_icon="🏛️",
    layout="wide"
)

# =====================================================================
# 🎨 이미지 처리 (Base64 변환)
# =====================================================================
def get_base64_encoded_image(image_path):
    """로컬 이미지 파일을 Base64 문자열로 변환"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

# 실제 파일명에 맞춰 경로 수정 (프로필이미지.jpg, 배너광고1.jpg)
LOGO_BASE64 = get_base64_encoded_image("프로필이미지.jpg")
BANNER_BASE64 = get_base64_encoded_image("배너광고1.jpg")

# =====================================================================
# 📄 디자인 리포트 HTML 생성 (디자인 보강)
# =====================================================================
def generate_branded_html(topic, sections):
    logo_img = f"data:image/jpeg;base64,{LOGO_BASE64}" if LOGO_BASE64 else ""
    banner_img = f"data:image/jpeg;base64,{BANNER_BASE64}" if BANNER_BASE64 else ""
    
    css = """
    @page { size: 1330px 940px; margin: 0; }
    body { font-family: 'Pretendard', 'Noto Sans KR', sans-serif; background: #E8E0E0; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
    .page { width: 1330px; height: 940px; background: white; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; }
    
    /* 표지 디자인 */
    .cover { background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 100%); color: white; justify-content: center; align-items: center; text-align: center; }
    .cover-logo { width: 150px; height: 150px; border-radius: 50%; border: 4px solid #d4af37; margin-bottom: 30px; object-fit: cover; }
    .cover-title { font-size: 55px; font-weight: 900; color: #d4af37; margin-bottom: 10px; }
    .cover-subtitle { font-size: 32px; font-weight: 300; opacity: 0.9; }
    
    /* 내용 페이지 디자인 */
    .header { padding: 30px 60px; border-bottom: 2px solid #f0f2f5; display: flex; align-items: center; gap: 20px; }
    .header-logo { width: 50px; height: 50px; border-radius: 50%; border: 2px solid #d4af37; object-fit: cover; }
    .content { padding: 50px 80px; flex: 1; font-size: 18px; line-height: 1.8; color: #333; overflow-y: auto; }
    
    /* 하단 배너 고정 */
    .footer-banner { width: 100%; height: 100px; object-fit: cover; border-top: 1px solid #eee; }
    
    .v-item { background: #f8faff; border-left: 6px solid #d4af37; padding: 25px; margin-bottom: 20px; border-radius: 10px; font-weight: 500; }
    .section-title { font-size: 28px; font-weight: 800; color: #0b1f52; }
    .sub-point { font-weight: 700; color: #1a3a7a; margin-top: 25px; font-size: 20px; display: block; }
    """

    html = f"<html><head><style>{css}</style></head><body>"
    
    # 1. 표지
    html += f"""
    <div class="page cover">
        <img src="{logo_img}" class="cover-logo">
        <div class="cover-title">중소기업경영지원단</div>
        <div class="cover-subtitle">벤처인증 마스터 컨설팅 리포트</div>
        <div style="margin-top:50px; font-size:24px; border-top:1px solid rgba(255,255,255,0.2); padding-top:20px;">{topic}</div>
    </div>
    """

    # 2. 내용 페이지들
    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n', 1)
        title = lines[0].strip('[] #')
        body = lines[1] if len(lines) > 1 else ""
        
        body_html = ""
        for line in body.split('\n'):
            s = line.strip()
            if not s: continue
            if s.startswith('V '): 
                body_html += f'<div class="v-item"><b>V</b> {s[2:]}</div>'
            elif s.startswith('- ') or s.startswith('•'): 
                body_html += f'<span class="sub-point">{s}</span>'
            else: 
                body_html += f'<div style="margin-bottom:10px;">{s}</div>'

        html += f"""
        <div class="page">
            <div class="header">
                <img src="{logo_img}" class="header-logo">
                <div class="section-title">{title}</div>
            </div>
            <div class="content">{body_html}</div>
            <img src="{banner_img}" class="footer-banner">
        </div>
        """
    
    html += "</body></html>"
    return html

# =====================================================================
# 메인 로직
# =====================================================================
st.markdown("""
<style>
    .dash-header { background: #0b1f52; color: white; padding: 20px; border-radius: 15px; border-bottom: 5px solid #d4af37; margin-bottom: 30px; }
    .copy-box { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="dash-header"><h1>🏛️ 벤처인증 AI 마스터 컨설턴트</h1><p>부자들의 비밀금고 · <b>디자인 & 복사 통합 모드</b></p></div>', unsafe_allow_html=True)

# 모델 설정 (Secrets에서 가져오거나 기본값 사용)
try:
    client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
except:
    st.error("API 키를 확인해주세요.")
    st.stop()

# UI 레이아웃
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Step 1. 기술 주제 추천")
    biz_type = st.radio("업종 선택", ["일반제조", "IT/SW", "초기창업"])
    if st.button("✨ 주제 추천", use_container_width=True):
        with st.spinner("AI가 분석 중입니다..."):
            res = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                messages=[{"role": "user", "content": f"{biz_type} 업종 벤처인증용 기술 주제 3개를 제안해줘."}]
            )
            st.session_state.suggestions = res.content[0].text
    
    if "suggestions" in st.session_state:
        st.info(st.session_state.suggestions)

with col2:
    st.subheader("📑 Step 2. 마스터 리포트 생성")
    topic = st.text_input("확정된 기술명", placeholder="여기에 기술명을 입력하세요")
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not topic:
            st.warning("기술명을 먼저 입력해주세요.")
        else:
            with st.spinner("리포트를 생성 중입니다. 잠시만 기다려주세요..."):
                prompt = f"""
                기술명: [{topic}]
                이 기술에 대해 벤처인증 심사용 사업계획서 11개 항목을 작성하라.
                
                [중요 규칙]
                1. 벤처인증 사이트 복사용이므로 '표'는 절대 사용하지 마라.
                2. 항목별로 '### [항목명]'으로 구분하라.
                3. 전문적이고 구체적인 수치와 기술적 서술을 포함하라.
                """
                res = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                st.session_state.report = res.content[0].text
                st.session_state.sections = st.session_state.report.split('### ')

# 결과 출력 영역
if "sections" in st.session_state:
    st.divider()
    st.subheader("📄 생성 결과 확인")
    
    # 1. HTML 다운로드 (디자인 포함)
    html_content = generate_branded_html(topic, st.session_state.sections)
    st.download_button(
        label="💾 디자인 리포트 HTML 다운로드 (대표님 보고용)",
        data=html_content,
        file_name=f"벤처인증_리포트_{topic}.html",
        mime="text/html",
        type="primary"
    )
    
    st.write("---")
    st.markdown("💡 **복사 가이드:** 아래의 각 항목 우측 상단 '복사' 아이콘을 눌러 벤처인증 사이트에 붙여넣으세요.")
    
    # 2. 항목별 복사 영역 (텍스트 최적화)
    for sec in st.session_state.sections:
        if not sec.strip(): continue
        parts = sec.split('\n', 1)
        sec_title = parts[0].strip()
        sec_body = parts[1].strip() if len(parts) > 1 else ""
        
        with st.expander(f"📌 {sec_title}", expanded=True):
            st.code(sec_body, language="text")

st.markdown('<div style="text-align:center; padding:50px; color:#aaa;">© 2026 중소기업경영지원단 & 부자들의 비밀금고</div>', unsafe_allow_html=True)
