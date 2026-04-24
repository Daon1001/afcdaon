import streamlit as st
import anthropic
from PIL import Image
import io
import pandas as pd
import os
import json
import requests
from datetime import datetime, date
import time
import base64
import streamlit.components.v1 as components

# ── 페이지 설정 ──
st.set_page_config(
    page_title="벤처인증 AI 마스터 컨설턴트",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
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
# 💎 CSS 및 HTML 리포트 생성 (로고 픽스 & 텍스트 최적화)
# =====================================================================
st.markdown("""
<style>
.stApp { background: #f0f2f5; font-family: 'Noto Sans KR', sans-serif; }
.dash-header { background: linear-gradient(135deg, #0b1f52, #1a3a7a); border-radius: 16px; padding: 25px; margin-bottom: 20px; border-bottom: 4px solid #d4af37; color: white; }
.sec-title { background: white; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #e5e7eb; color: #0b1f52; font-weight: 700; }
.copy-card { background: white; border: 1px solid #d1d5db; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
.copy-label { font-weight: 800; color: #0b1f52; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
</style>
""", unsafe_allow_html=True)

def generate_html_report(topic, sections):
    # 로고 잘림 수정을 위해 x, y 좌표 및 viewBox 여백 조정
    logo_svg = """
    <svg style="width:45px;height:45px;flex-shrink:0;" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="1" width="40" height="40" rx="8" fill="#1B3A6B"/>
        <path d="M21 11L31 21L21 31L11 21L21 11Z" fill="#C9A961"/>
    </svg>
    """
    cover_logo = """
    <svg style="width:100px;height:100px;margin-bottom:20px;" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="1" width="40" height="40" rx="8" fill="#1B3A6B" stroke="#C9A961" stroke-width="1.5"/>
        <path d="M21 9L33 21L21 33L9 21L21 9Z" fill="#C9A961"/>
        <circle cx="21" cy="21" r="4" fill="white"/>
    </svg>
    """
    
    css = """
    @page { size: 1330px 940px; margin: 0; }
    body { font-family: 'Pretendard Variable', sans-serif; background: #E8E0E0; margin: 0; padding: 10px; }
    .page { width: 1330px; height: 940px; background: white; margin: 0 auto 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); position: relative; overflow: hidden; page-break-after: always; }
    .cover-page { background: linear-gradient(135deg, #0A1628, #1B3A6B); color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .header { display: flex; align-items: center; gap: 15px; padding: 30px 60px; border-bottom: 2px solid #E2E8F0; }
    .body { padding: 40px 60px; height: 780px; overflow-y: auto; font-size: 17px; line-height: 1.8; color: #333; }
    .v-item { display: flex; gap: 15px; background: #F0F4F9; border-left: 5px solid #C9A961; padding: 20px; margin-bottom: 15px; border-radius: 8px; }
    .bold { font-weight: 800; color: #0F2847; margin: 25px 0 10px; font-size: 19px; }
    """

    html = f"<html><head><style>{css}</style></head><body>"
    html += f'<div class="page cover-page">{cover_logo}<h1 style="font-size:50px; letter-spacing:10px;">중소기업경영지원단</h1><h2>벤처인증 마스터 리포트</h2><h3>{topic}</h3></div>'

    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n', 1)
        title = lines[0].strip('[] #')
        body = lines[1] if len(lines) > 1 else ""
        
        body_html = ""
        for line in body.split('\n'):
            s = line.strip()
            if not s: continue
            if s.startswith('V '): body_html += f'<div class="v-item"><b>V</b> {s[2:]}</div>'
            elif s.startswith('- ') or s.startswith('###'): body_html += f'<div class="bold">{s.strip("- #")}</div>'
            else: body_html += f'<div>{s}</div>'

        html += f'<div class="page"><div class="header">{logo_svg}<div style="font-size:28px; font-weight:800; color:#0F2847;">{title}</div></div><div class="body">{body_html}</div></div>'
    
    html += "</body></html>"
    return html

# =====================================================================
# Claude API 호출
# =====================================================================
def claude_generate(prompt, max_tokens=4096):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        response = client.messages.create(
            model=st.session_state.get('model_id', 'claude-sonnet-4-6'),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

# =====================================================================
# 메인 UI
# =====================================================================
if st.session_state.authenticated_user is None:
    st.title("🏛️ 벤처인증 AI 마스터 컨설턴트")
    email = st.text_input("이메일 로그인").strip().lower()
    if st.button("로그인"):
        if email in user_db["users"]:
            st.session_state.authenticated_user = email
            st.rerun()
    st.stop()

st.markdown('<div class="dash-header"><h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1><p>중소기업경영지원단 · <b>복사&붙여넣기 최적화 모드</b></p></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="sec-title">Step 1 · 기술 주제 추천</div>', unsafe_allow_html=True)
    biz = st.selectbox("업종", ["일반 제조", "IT/SW", "서비스/기타"])
    if st.button("✨ 주제 추천받기", type="primary", use_container_width=True):
        with st.spinner('추천 중...'):
            res = claude_generate(f"{biz} 업종 벤처인증용 기술주제 3개를 JSON(tech_name, reason)으로 추천해줘.")
            st.session_state.suggestions = json.loads(res.replace('```json', '').replace('```', '').strip())
    
    if st.session_state.get('suggestions'):
        for s in st.session_state.suggestions['suggestions']:
            st.info(f"**{s['tech_name']}**\n\n{s['reason']}")
            if st.button(f"이 기술 선택", key=s['tech_name']):
                st.session_state.step2_topic = s['tech_name']

with col2:
    st.markdown('<div class="sec-title">Step 2 · 마스터 리포트 생성</div>', unsafe_allow_html=True)
    topic = st.text_input("확정 기술명", value=st.session_state.get('step2_topic', ''))
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        with st.spinner('리포트 생성 중 (약 1분)...'):
            # 표(Table) 사용을 엄격히 금지하는 프롬프트
            p = f"""기술명 [{topic}]에 대해 벤처인증용 11개 항목 사업계획서를 작성해라.
            중요: 벤처인증 사이트 입력창은 '표' 삽입이 안 되므로, 절대 표를 만들지 말고 '•' 또는 '1. 2. 3.' 형식의 텍스트로만 작성해라.
            항목 구분은 반드시 '### [번호. 항목명]' 형식을 사용해라. 아주 구체적이고 전문적으로 써라."""
            res = claude_generate(p, max_tokens=8000)
            st.session_state.report_sections = res.split('### ')

# 리포트 결과 표시 및 복사 기능
if st.session_state.get('report_sections'):
    st.divider()
    st.subheader("📄 생성된 리포트 (대표님 보고용 및 복사용)")
    
    # 상단 다운로드 버튼
    h_data = generate_html_report(topic, st.session_state.report_sections)
    st.download_button("💾 디자인 리포트 HTML 다운로드", h_data, file_name=f"벤처리포트_{topic}.html", type="primary")
    
    st.write("---")
    st.markdown("💡 **Tip:** 각 항목 우측 상단의 복사 버튼을 눌러 벤처인증 사이트에 바로 붙여넣으세요.")
    
    for sec in st.session_state.report_sections:
        if not sec.strip(): continue
        lines = sec.split('\n', 1)
        title = lines[0].strip('[] #')
        content = lines[1].strip() if len(lines) > 1 else ""
        
        with st.container():
            st.markdown(f'<div class="copy-label">📌 {title}</div>', unsafe_allow_html=True)
            # st.code는 우측 상단에 복사 버튼이 기본으로 생겨서 매우 편리함
            st.code(content, language="text")

st.sidebar.button("새로고침/로그아웃", on_click=lambda: st.session_state.clear())
