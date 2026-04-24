import streamlit as st
import anthropic
import json
import os
import requests
import base64
from datetime import datetime, date

# ── 페이지 설정 ──
st.set_page_config(
    page_title="벤처인증 AI 마스터 컨설턴트",
    page_icon="🏛️",
    layout="wide"
)

# =====================================================================
# 🔒 GitHub Gist DB 시스템 (로그인 및 보안)
# =====================================================================
DB_FILE = "user_database.json"
BACKUP_KEY = "db_backup_state"

def _gist_headers():
    token = st.secrets.get("github_token", "")
    if not token: return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _gist_id(): return st.secrets.get("gist_id", "")
def _gist_filename(): return st.secrets.get("gist_filename", "venture_users.json")

def load_db():
    headers = _gist_headers()
    gist_id = _gist_id()
    if headers and gist_id:
        try:
            resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                fn = _gist_filename()
                if fn in data.get("files", {}):
                    db = json.loads(data["files"][fn]["content"])
                    return db
        except: pass
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    # 기본 계정 생성
    return {"users": {"incheon00@gmail.com": {"approved": True, "is_admin": True, "usage_count": 0, "last_reset_month": date.today().month}}, "usage_logs": []}

def save_db(db):
    db["last_updated"] = datetime.now().isoformat()
    headers = _gist_headers()
    gist_id = _gist_id()
    if headers and gist_id:
        payload = {"files": {_gist_filename(): {"content": json.dumps(db, ensure_ascii=False, indent=2)}}}
        requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    st.session_state["user_db_cache"] = db

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]

# =====================================================================
# 🎨 이미지 처리 (Base64 변환)
# =====================================================================
def get_base64_encoded_image(image_path):
    """로컬 이미지 파일을 Base64 문자열로 변환하여 HTML에 직접 삽입"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

# 파일명은 실제 대표님 환경에 맞게 유지
LOGO_BASE64 = get_base64_encoded_image("프로필이미지.jpg")
BANNER_BASE64 = get_base64_encoded_image("배너광고1.jpg")

# =====================================================================
# 📄 디자인 리포트 HTML 생성 (로고/배너 포함)
# =====================================================================
def generate_branded_html(topic, sections):
    logo_img = f"data:image/jpeg;base64,{LOGO_BASE64}" if LOGO_BASE64 else ""
    banner_img = f"data:image/jpeg;base64,{BANNER_BASE64}" if BANNER_BASE64 else ""
    
    css = """
    @page { size: 1330px 940px; margin: 0; }
    body { font-family: 'Pretendard', 'Noto Sans KR', sans-serif; background: #E8E0E0; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
    .page { width: 1330px; height: 940px; background: white; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; }
    
    /* 인쇄 시 여백/배경색 최적화 */
    @media print {
        body { background: white !important; padding: 0 !important; }
        .page { box-shadow: none; margin-bottom: 0; }
        .cover { background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 100%) !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
    
    /* 표지 디자인 */
    .cover { background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 100%); color: white; justify-content: center; align-items: center; text-align: center; }
    .cover-logo { width: 150px; height: 150px; border-radius: 50%; border: 4px solid #d4af37; margin-bottom: 30px; object-fit: cover; }
    .cover-title { font-size: 55px; font-weight: 900; color: #d4af37; margin-bottom: 10px; letter-spacing: 2px; }
    .cover-subtitle { font-size: 32px; font-weight: 300; opacity: 0.9; }
    
    /* 내용 페이지 디자인 */
    .header { padding: 30px 60px; border-bottom: 2px solid #f0f2f5; display: flex; align-items: center; gap: 20px; }
    .header-logo { width: 50px; height: 50px; border-radius: 50%; border: 2px solid #d4af37; object-fit: cover; }
    .content { padding: 50px 80px; flex: 1; font-size: 18px; line-height: 1.8; color: #333; overflow-y: auto; }
    
    /* 하단 배너 고정 */
    .footer-banner { width: 100%; height: 100px; object-fit: cover; border-top: 1px solid #eee; }
    
    .v-item { background: #f8faff; border-left: 6px solid #d4af37; padding: 25px; margin-bottom: 20px; border-radius: 10px; font-weight: 500; display: flex; gap: 15px; }
    .section-title { font-size: 28px; font-weight: 800; color: #0b1f52; }
    .sub-point { font-weight: 800; color: #1a3a7a; margin: 25px 0 10px; font-size: 20px; display: block; }
    """

    html = f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>"
    
    # 1. 표지
    html += f"""
    <div class="page cover">
        <img src="{logo_img}" class="cover-logo" alt="로고">
        <div class="cover-title">중소기업경영지원단</div>
        <div class="cover-subtitle">벤처인증 마스터 컨설팅 리포트</div>
        <div style="margin-top:50px; font-size:24px; border-top:1px solid rgba(255,255,255,0.2); padding-top:20px;">{topic}</div>
    </div>
    """

    # 2. 내용 페이지 생성
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
                body_html += f'<div class="v-item"><b style="color:#0b1f52; font-size:20px;">V</b> <div>{s[2:]}</div></div>'
            elif s.startswith('- ') or s.startswith('•'): 
                body_html += f'<span class="sub-point">{s}</span>'
            else: 
                body_html += f'<div style="margin-bottom:10px;">{s}</div>'

        html += f"""
        <div class="page">
            <div class="header">
                <img src="{logo_img}" class="header-logo" alt="로고">
                <div class="section-title">{title}</div>
            </div>
            <div class="content">{body_html}</div>
            <img src="{banner_img}" class="footer-banner" alt="배너">
        </div>
        """
    
    html += "</body></html>"
    return html

# =====================================================================
# Claude API 호출
# =====================================================================
def claude_generate(prompt, max_tokens=8192):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        response = client.messages.create(
            model=st.secrets.get("claude_model", "claude-sonnet-4-6"),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

# =====================================================================
# 메인 UI
# =====================================================================
st.markdown("""
<style>
    .stApp { background: #f0f2f5; font-family: 'Noto Sans KR', sans-serif; }
    .dash-header { background: linear-gradient(135deg, #0b1f52, #1a3a7a); color: white; padding: 25px; border-radius: 15px; border-bottom: 5px solid #d4af37; margin-bottom: 30px; }
    .sec-title { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e5e7eb; color: #0b1f52; font-weight: 700; font-size: 18px; }
    .copy-label { font-weight: 800; color: #0b1f52; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
</style>
""", unsafe_allow_html=True)

if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.title("🏛️ 벤처인증 AI 마스터 컨설턴트")
    email = st.text_input("이메일 로그인").strip().lower()
    if st.button("로그인"):
        if email in user_db["users"]:
            st.session_state.authenticated_user = email
            st.rerun()
    st.stop()

st.markdown('<div class="dash-header"><h1>🏛️ 벤처인증 AI 마스터 컨설턴트</h1><p>부자들의 비밀금고 · <b>디자인 & 복사 통합 모드</b></p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"**👤 {st.session_state.authenticated_user}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-title">Step 1. 기술 주제 추천</div>', unsafe_allow_html=True)
    biz_type = st.radio("업종 선택", ["일반제조", "IT/SW", "초기창업"], horizontal=True)
    if st.button("✨ 주제 추천", type="primary", use_container_width=True):
        with st.spinner("AI가 분석 중입니다..."):
            res = claude_generate(f"{biz_type} 업종 벤처인증용 구체적 기술 주제 3개를 제안해줘. JSON(tech_name, reason) 형식으로만 출력해.", max_tokens=2000)
            try:
                st.session_state.suggestions = json.loads(res.replace('```json', '').replace('```', '').strip())
            except:
                st.error("추천 결과 파싱에 실패했습니다.")
    
    if "suggestions" in st.session_state and "suggestions" in st.session_state.suggestions:
        for s in st.session_state.suggestions['suggestions']:
            st.info(f"**{s['tech_name']}**\n\n{s['reason']}")
            if st.button(f"이 기술 선택", key=s['tech_name']):
                st.session_state.step2_topic = s['tech_name']

with col2:
    st.markdown('<div class="sec-title">Step 2. 마스터 리포트 생성</div>', unsafe_allow_html=True)
    topic = st.text_input("확정된 기술명", value=st.session_state.get('step2_topic', ''), placeholder="여기에 기술명을 입력하세요")
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not topic:
            st.warning("기술명을 먼저 입력해주세요.")
        else:
            with st.spinner("리포트를 생성 중입니다. (약 1분 소요)..."):
                # 표 사용 금지 및 11개 항목 강제 프롬프트
                prompt = f"""
                기술명: [{topic}]
                이 기술에 대해 벤처인증 심사용 사업계획서 11개 항목을 아주 구체적으로 작성하라.
                
                [중요 규칙]
                1. 벤처인증 사이트 복사용이므로 '표(Table)'는 절대 사용하지 마라. 모든 설명은 '•' 또는 '1. 2. 3.' 텍스트로 풀어써라.
                2. 항목별로 반드시 '### [번호. 항목명]'으로 구분하라.
                3. 1번 항목에는 반드시 'V자 요약' 7문장을 포함하라.
                """
                res = claude_generate(prompt, max_tokens=8192)
                st.session_state.report = res
                st.session_state.sections = res.split('### ')

# =====================================================================
# 결과 출력 및 다운로드 영역
# =====================================================================
if "sections" in st.session_state:
    st.divider()
    st.subheader("📄 생성 결과 확인")
    
    # 1. HTML 다운로드 (로고/배너 포함 디자인)
    html_content = generate_branded_html(topic, st.session_state.sections)
    st.download_button(
        label="💾 디자인 리포트 HTML 다운로드 (대표님 보고용)",
        data=html_content,
        file_name=f"벤처인증_리포트_{topic}.html",
        mime="text/html",
        type="primary"
    )
    
    st.write("---")
    st.markdown("💡 **복사 가이드:** 벤처인증 사이트에 입력할 때는 아래 각 항목 박스 우측 상단의 **[복사] 아이콘**을 클릭하여 붙여넣으세요.")
    
    # 2. 항목별 복사 영역 (st.code 활용)
    for sec in st.session_state.sections:
        if not sec.strip(): continue
        parts = sec.split('\n', 1)
        sec_title = parts[0].strip('[] #')
        sec_body = parts[1].strip() if len(parts) > 1 else ""
        
        with st.container():
            st.markdown(f'<div class="copy-label">📌 {sec_title}</div>', unsafe_allow_html=True)
            st.code(sec_body, language="text")

st.markdown('<div style="text-align:center; padding:50px; color:#aaa; font-size:12px;">© 2026 중소기업경영지원단 & 부자들의 비밀금고</div>', unsafe_allow_html=True)
