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

try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# ── 페이지 설정 ──
st.set_page_config(
    page_title="벤처인증 AI 마스터 컨설턴트",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 🔒 GitHub Gist DB 시스템
# =====================================================================
DB_FILE = "user_database.json"
BACKUP_KEY = "db_backup_state"

def _gist_headers():
    token = st.secrets.get("github_token", "")
    if not token: return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _gist_id(): return st.secrets.get("gist_id", "")
def _gist_filename(): return st.secrets.get("gist_filename", "venture_users.json")

def get_default_db():
    return {
        "users": {
            "incheon00@gmail.com": {"approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_reset_month": date.today().month},
            "임원근@gmail.com": {"approved": True, "is_admin": True, "created_at": "2026-02-14", "usage_count": 0, "last_reset_month": date.today().month}
        },
        "last_updated": datetime.now().isoformat()
    }

def gist_load():
    headers = _gist_headers()
    gist_id = _gist_id()
    if not headers or not gist_id: return None
    try:
        resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            fn = _gist_filename()
            if fn in data.get("files", {}):
                return json.loads(data["files"][fn]["content"])
    except Exception: pass
    return None

def gist_save(db):
    headers = _gist_headers()
    gist_id = _gist_id()
    if not headers or not gist_id: return False
    try:
        payload = {"files": {_gist_filename(): {"content": json.dumps(db, ensure_ascii=False, indent=2)}}}
        resp = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception: return False

def _save_local(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception: pass
    st.session_state[BACKUP_KEY] = json.dumps(db, ensure_ascii=False)

def load_db():
    db = gist_load()
    if db and "users" in db:
        _save_local(db)
        return db
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
            if "users" in db:
                st.session_state[BACKUP_KEY] = json.dumps(db, ensure_ascii=False)
                gist_save(db)
                return db
        except Exception: pass
    if BACKUP_KEY in st.session_state:
        try:
            db = json.loads(st.session_state[BACKUP_KEY])
            if "users" in db:
                _save_local(db)
                gist_save(db)
                return db
        except Exception: pass
    db = get_default_db()
    save_db(db)
    return db

def save_db(db):
    db["last_updated"] = datetime.now().isoformat()
    gist_ok = gist_save(db)
    _save_local(db)
    st.session_state["gist_sync_failed"] = not gist_ok
    st.session_state["user_db_cache"] = db

def reset_monthly_usage(db):
    current_month = date.today().month
    changed = False
    for email, user in db["users"].items():
        if user.get("last_reset_month") != current_month:
            user["usage_count"] = 0
            user["last_reset_month"] = current_month
            changed = True
    if changed: save_db(db)
    return db

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]
user_db = reset_monthly_usage(user_db)

# =====================================================================
# 💎 CSS 및 HTML 리포트 생성 로직
# =====================================================================
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("""
<style>
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 1200px !important; }
header[data-testid="stHeader"] { display: none !important; }
.stApp { background: #f0f2f5 !important; font-family: 'Noto Sans KR', sans-serif !important; }
section[data-testid="stSidebar"] { background: #0b1f52 !important; }
.dash-header { background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 60%, #2a5298 100%); border-radius: 16px; padding: 28px 36px; margin-bottom: 20px; border-bottom: 4px solid #d4af37; }
.dash-header h1 { color: white !important; font-size: 26px; font-weight: 900; margin: 0 !important; }
.dash-header .gold { color: #d4af37 !important; font-weight: 700; }
.sec-title { background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; border: 1px solid #e5e7eb; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.sec-title h3 { margin: 0 !important; font-size: 16px; font-weight: 700; color: #0b1f52; }
.ai-result { background: linear-gradient(135deg, #fffdf5, #fefce8); border: 1px solid #e5d9a8; border-left: 5px solid #d4af37; border-radius: 12px; padding: 20px 22px; margin-top: 14px; line-height: 1.85; font-size: 14px; }
[data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, #d4af37 0%, #b8952e 100%) !important; color: #0b1f52 !important; font-weight: 700 !important; border-radius: 10px !important; }
.login-hero { background: linear-gradient(160deg, #0b1f52, #1a3a7a 50%, #2a5298); padding: 48px 20px 36px; border-radius: 18px; text-align: center; margin-bottom: 20px; }
.login-hero .title { font-size: 26px; font-weight: 900; color: white; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

def generate_html_report(topic, sections):
    # 로고 잘림 수정을 위해 viewBox 내 좌표와 stroke 위치 조정
    logo_svg = """
    <svg style="width:45px;height:45px;flex-shrink:0;" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="1" width="38" height="38" rx="8" fill="#1B3A6B"/>
        <path d="M20 10L30 20L20 30L10 20L20 10Z" fill="#C9A961"/>
    </svg>
    """
    cover_logo = """
    <svg style="width:100px;height:100px;margin-bottom:20px;filter: drop-shadow(0 6px 20px rgba(201,169,97,0.4));" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="1" y="1" width="38" height="38" rx="8" fill="#1B3A6B" stroke="#C9A961" stroke-width="1.5"/>
        <path d="M20 8L32 20L20 32L8 20L20 8Z" fill="#C9A961"/>
        <circle cx="20" cy="20" r="4" fill="white"/>
    </svg>
    """
    
    css = """
    @page { size: 1330px 940px; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Pretendard Variable', sans-serif; background: #E8E0E0; display: flex; flex-direction: column; align-items: center; padding: 10px 0; }
    .page { width: 1330px; height: 940px; page-break-after: always; position: relative; background: white; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
    .cover-page { background: linear-gradient(135deg, #0A1628 0%, #1B3A6B 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }
    .cover-brand { font-size: 52px; font-weight: 900; letter-spacing: 12px; background: linear-gradient(180deg, #F4D98A, #C9A961); -webkit-background-clip: text; color: transparent; margin-bottom: 20px; }
    .cover-title { font-size: 38px; font-weight: 700; margin-bottom: 40px; }
    .page-header { display: flex; align-items: center; gap: 15px; padding: 30px 60px; border-bottom: 2px solid #E2E8F0; }
    .page-title { font-size: 28px; font-weight: 800; color: #0F2847; }
    .page-body { padding: 40px 60px; height: 780px; overflow-y: auto; font-size: 16px; line-height: 1.8; }
    .v-item { display: flex; gap: 15px; background: #F0F4F9; border-left: 5px solid #C9A961; padding: 20px; margin-bottom: 15px; border-radius: 8px; }
    .v-badge { width: 30px; height: 30px; background: #0F2847; color: white; display: flex; align-items: center; justify-content: center; border-radius: 5px; font-weight: 900; flex-shrink: 0; }
    .bold-section { font-weight: 800; color: #0F2847; margin: 25px 0 10px; font-size: 19px; }
    """

    html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{css}</style></head><body>
    <div class="page cover-page">
        {cover_logo}
        <div class="cover-brand">중소기업경영지원단</div>
        <div class="cover-title">벤처인증 마스터 컨설팅 리포트</div>
        <div style="font-size:26px; opacity:0.9;">{topic}</div>
    </div>"""

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
                body_html += f'<div class="v-item"><div class="v-badge">V</div><div>{s[2:]}</div></div>'
            elif s.startswith('- ') or s.startswith('###'):
                body_html += f'<div class="bold-section">{s.strip("- #")}</div>'
            else:
                body_html += f'<div style="margin-bottom:8px;">{s}</div>'

        html += f"""<div class="page"><div class="page-header">{logo_svg}<div class="page-title">{title}</div></div>
                    <div class="page-body">{body_html}</div></div>"""
    
    html += "</body></html>"
    return html

# =====================================================================
# 세션 및 로그인 로직
# =====================================================================
if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None
if 'report_sections' not in st.session_state: st.session_state.report_sections = None
if 'suggestions' not in st.session_state: st.session_state.suggestions = None

if st.session_state.authenticated_user is None:
    _, lc, _ = st.columns([1, 1.5, 1])
    with lc:
        st.markdown('<div class="login-hero"><div class="title">🏛️ 중소기업경영지원단</div><p>AI 마스터 컨설턴트</p></div>', unsafe_allow_html=True)
        login_email = st.text_input("이메일", placeholder="example@gmail.com").strip().lower()
        if st.button("로그인", type="primary", use_container_width=True):
            user = user_db["users"].get(login_email)
            if user and user.get("approved"):
                st.session_state.authenticated_user = login_email
                st.rerun()
            else: st.error("❌ 미등록 계정입니다.")
    st.stop()

# =====================================================================
# 메인 UI (Step 1 & Step 2)
# =====================================================================
current_user_email = st.session_state.authenticated_user
with st.sidebar:
    st.markdown(f"**👤 {current_user_email}**")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    st.divider()
    model_choice = st.radio("🤖 모델 선택", list(MODEL_CHOICES.keys()), index=1)
    target_model_name = MODEL_CHOICES[model_choice]["id"]

st.markdown('<div class="dash-header"><h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1><p><span class="gold">중소기업경영지원단</span> · AI 마스터 컨설턴트</p></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="sec-title"><h3>📋 Step 1 · 기술 주제 추천</h3></div>', unsafe_allow_html=True)
    biz_type = st.radio("업종", ["일반 기업", "IT / SW", "초기기업"], horizontal=True)
    uploaded_file = st.file_uploader("사업자등록증 분석", type=["jpg", "png", "pdf"])
    
    if st.button("✨ AI 기술 주제 추천", type="primary", use_container_width=True):
        with st.spinner('분석 중...'):
            prompt = f"[{biz_type}] 분야 기업 벤처인증용 구체적 기술 주제 3개를 JSON(tech_name, reason, fitness) 형식으로 추천해줘."
            text, in_t, out_t = claude_generate(prompt, max_tokens=2000)
            try:
                st.session_state.suggestions = json.loads(text.replace('```json', '').replace('```', '').strip())
            except: st.error("추천 생성 실패")

    if st.session_state.suggestions:
        for idx, sug in enumerate(st.session_state.suggestions.get('suggestions', []), 1):
            st.markdown(f'<div class="ai-result"><b>#{idx} {sug["tech_name"]}</b><br>{sug["reason"]}</div>', unsafe_allow_html=True)
            if st.button(f"→ {idx}번 기술 선택", key=f"btn_{idx}"):
                st.session_state.step2_topic = sug["tech_name"]

with col2:
    st.markdown('<div class="sec-title"><h3>📑 Step 2 · 마스터 리포트 생성</h3></div>', unsafe_allow_html=True)
    final_topic = st.text_input("확정 기술명", value=st.session_state.get('step2_topic', ''))
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not final_topic: st.warning("기술명을 입력하세요.")
        else:
            with st.spinner('리포트 생성 중 (약 1분)...'):
                report_prompt = f"기술명 [{final_topic}]에 대해 벤처인증용 11개 항목(V자 요약 포함) 사업계획서를 아주 구체적으로 작성해줘. 항목번호 ### 로 구분해줘."
                text, in_t, out_t = claude_generate(report_prompt, max_tokens=8000)
                st.session_state.report_sections = text.split('### ')
                user_db["users"][current_user_email]["usage_count"] += 1
                log_usage(user_db, current_user_email, "Step 2", in_t, out_t, target_model_name)
                save_db(user_db)

# 리포트 완성 시 HTML 다운로드 버튼 노출
if st.session_state.report_sections:
    st.divider()
    st.success("✅ **리포트 생성이 완료되었습니다.**")
    html_data = generate_html_report(final_topic, st.session_state.report_sections)
    st.download_button(
        label="💾 디자인 리포트 HTML 다운로드",
        data=html_data,
        file_name=f"벤처인증_마스터리포트_{final_topic}.html",
        mime="text/html",
        type="primary"
    )
    st.info("💡 다운로드한 HTML 파일을 열어 브라우저에서 '인쇄 -> PDF로 저장'하면 깔끔한 문서가 됩니다.")

st.markdown('<div style="text-align:center;padding:40px;color:#9ca3af;font-size:12px;">© 2026 중소기업경영지원단</div>', unsafe_allow_html=True)
