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
    if not token:
        return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _gist_id():
    return st.secrets.get("gist_id", "")

def _gist_filename():
    return st.secrets.get("gist_filename", "venture_users.json")

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
    if not headers or not gist_id:
        return None
    try:
        resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            fn = _gist_filename()
            if fn in data.get("files", {}):
                return json.loads(data["files"][fn]["content"])
    except Exception:
        pass
    return None

def gist_save(db):
    headers = _gist_headers()
    gist_id = _gist_id()
    if not headers or not gist_id:
        return False
    try:
        payload = {"files": {_gist_filename(): {"content": json.dumps(db, ensure_ascii=False, indent=2)}}}
        resp = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False

def _save_local(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
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
        except Exception:
            pass
    if BACKUP_KEY in st.session_state:
        try:
            db = json.loads(st.session_state[BACKUP_KEY])
            if "users" in db:
                _save_local(db)
                gist_save(db)
                return db
        except Exception:
            pass
    db = get_default_db()
    save_db(db)
    return db

def save_db(db):
    db["last_updated"] = datetime.now().isoformat()
    gist_ok = gist_save(db)
    _save_local(db)
    st.session_state["gist_sync_failed"] = not gist_ok
    st.session_state["user_db_cache"] = db

def is_gist_connected():
    return bool(_gist_headers() and _gist_id())

def get_user(db, email):
    return db["users"].get(email)

def reset_monthly_usage(db):
    current_month = date.today().month
    changed = False
    for email, user in db["users"].items():
        if user.get("last_reset_month") != current_month:
            user["usage_count"] = 0
            user["last_reset_month"] = current_month
            changed = True
    if changed:
        save_db(db)
    return db

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]
user_db = reset_monthly_usage(user_db)

# =====================================================================
# 💎 CSS
# =====================================================================
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("""
<style>
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 1200px !important; }
header[data-testid="stHeader"] { display: none !important; }
.stApp { background: #f0f2f5 !important; font-family: 'Noto Sans KR', -apple-system, sans-serif !important; }
section[data-testid="stSidebar"] { background: #0b1f52 !important; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem !important; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] summary { color: white !important; }
section[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,0.1) !important; border: 1px solid rgba(255,255,255,0.25) !important; color: white !important; border-radius: 8px !important; }
section[data-testid="stSidebar"] .stButton > button:hover { background: rgba(255,255,255,0.2) !important; }
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * { color: #333 !important; }
section[data-testid="stSidebar"] .stDataFrame, section[data-testid="stSidebar"] .stDataFrame * { color: #333 !important; }
section[data-testid="stSidebar"] .stDownloadButton > button { background: rgba(212,175,55,0.2) !important; border: 1px solid rgba(212,175,55,0.4) !important; color: #d4af37 !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

.dash-header { background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 60%, #2a5298 100%); border-radius: 16px; padding: 28px 36px; margin-bottom: 20px; border-bottom: 4px solid #d4af37; }
.dash-header h1 { color: white !important; font-size: 26px; font-weight: 900; margin: 0 !important; }
.dash-header p { color: rgba(255,255,255,0.7) !important; font-size: 14px; margin: 6px 0 0 !important; }
.dash-header .gold { color: #d4af37 !important; font-weight: 700; }

.sec-title { background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; border: 1px solid #e5e7eb; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.sec-title h3 { margin: 0 !important; font-size: 16px; font-weight: 700; color: #0b1f52; }

.ai-result { background: linear-gradient(135deg, #fffdf5, #fefce8); border: 1px solid #e5d9a8; border-left: 5px solid #d4af37; border-radius: 12px; padding: 20px 22px; margin-top: 14px; line-height: 1.85; font-size: 14px; color: #1f2937; }
.ai-result b { color: #92700c; }

[data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, #d4af37 0%, #b8952e 100%) !important; color: #0b1f52 !important; font-weight: 700 !important; border: none !important; border-radius: 10px !important; }

.stTextInput input, .stTextArea textarea { border-radius: 10px !important; border: 1.5px solid #d1d5db !important; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color: #d4af37 !important; box-shadow: 0 0 0 2px rgba(212,175,55,0.15) !important; }

.login-hero { background: linear-gradient(160deg, #0b1f52, #1a3a7a 50%, #2a5298); padding: 48px 20px 36px; border-radius: 18px; text-align: center; margin-bottom: 20px; }
.login-hero .badge { display: inline-block; background: rgba(212,175,55,0.2); color: #d4af37; font-size: 10px; font-weight: 700; letter-spacing: 2.5px; padding: 5px 14px; border-radius: 20px; margin-bottom: 14px; border: 1px solid rgba(212,175,55,0.3); }
.login-hero .title { font-size: 26px; font-weight: 900; color: white; margin: 0 0 4px; }
.login-hero .sub { font-size: 13px; color: rgba(255,255,255,0.65); }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# HTML 템플릿 생성 헬퍼 함수
# =====================================================================
def generate_html_report(topic, sections):
    css = """
    @page { size: 1330px 940px; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Pretendard Variable', 'Noto Sans KR', sans-serif; font-size: 14px; color: #1A1A1A; line-height: 1.55; background: #E8E0E0; display: flex; flex-direction: column; align-items: center; padding: 10px 0; letter-spacing: -0.1px; }
    .page { width: 1330px; height: 940px; page-break-after: always; page-break-inside: avoid; position: relative; overflow: hidden; background: white; margin-bottom: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
        body { background: white !important; padding: 0 !important; }
        .page { height: 940px; overflow: hidden; margin-bottom: 0; box-shadow: none; page-break-after: always; page-break-inside: avoid; }
        .page:last-child { page-break-after: avoid; }
        .cover-page { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%) !important; }
    }
    .cover-page { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .gold-deco { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1; }
    .cover-bg { padding: 60px 100px; color: white; height: 85%; position: relative; z-index: 2; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    .cover-brand { font-size: 50px; font-weight: 900; letter-spacing: 10px; background: linear-gradient(180deg, #F4D98A 0%, #C9A961 50%, #8B6F3E 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; color: #C9A961; margin-bottom: 16px; }
    .cover-title { font-size: 40px; font-weight: 700; margin-bottom: 32px; letter-spacing: 5px; color: white; }
    .cover-company { font-size: 24px; font-weight: 300; color: rgba(255,255,255,0.88); letter-spacing: 2px; }
    
    .content-page { padding: 0; display: flex; flex-direction: column; }
    .page-header { display: flex; align-items: center; gap: 14px; padding: 24px 50px; border-bottom: 2px solid #E2E8F0; position: relative; }
    .page-header::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 120px; height: 2px; background: linear-gradient(90deg, #C9A961, transparent); }
    .page-title-main { font-size: 26px; font-weight: 800; color: #0F2847; letter-spacing: -0.3px; }
    .page-body { padding: 30px 50px; flex: 1; overflow-y: auto; }
    
    .v-item { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 12px; padding: 14px 18px; background: #F0F4F9; border-radius: 8px; font-size: 15px; line-height: 1.7; color: #1A1A1A; border-left: 4px solid #C9A961; }
    .v-badge { flex-shrink: 0; width: 28px; height: 28px; background: linear-gradient(135deg, #0F2847, #1B3A6B); color: white; font-weight: 900; font-size: 14px; border-radius: 5px; display: flex; align-items: center; justify-content: center; margin-top: 2px; }
    .text-line { margin-bottom: 8px; line-height: 1.65; font-size: 15px; color: #333; }
    .bold-line { font-weight: 800; color: #0F2847; margin: 20px 0 8px; font-size: 17px; }
    .logo-svg { width: 45px; height: 45px; flex-shrink: 0; }
    """

    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<title>벤처인증 마스터 리포트</title>
<style>{css}</style>
</head>
<body>
    <div class="page cover-page">
        <svg class="gold-deco" viewBox="0 0 1330 940" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#C9A961" stop-opacity="0.6"/>
                    <stop offset="100%" stop-color="#8B6F3E" stop-opacity="0.15"/>
                </linearGradient>
            </defs>
            <circle cx="1330" cy="0" r="420" fill="none" stroke="url(#goldGrad)" stroke-width="1"/>
            <circle cx="1330" cy="0" r="520" fill="none" stroke="url(#goldGrad)" stroke-width="0.8" opacity="0.6"/>
            <circle cx="0" cy="940" r="380" fill="none" stroke="url(#goldGrad)" stroke-width="1" opacity="0.5"/>
            <line x1="1100" y1="0" x2="1330" y2="230" stroke="#C9A961" stroke-width="1" opacity="0.25"/>
        </svg>
        <div class="cover-bg">
            <svg style="width:100px;height:100px;margin-bottom:20px;filter: drop-shadow(0 6px 20px rgba(201,169,97,0.4));" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="40" height="40" rx="8" fill="#1B3A6B" stroke="#C9A961" stroke-width="2"/>
                <path d="M20 8L32 20L20 32L8 20L20 8Z" fill="#C9A961"/>
                <circle cx="20" cy="20" r="4" fill="white"/>
            </svg>
            <div class="cover-brand">중소기업경영지원단</div>
            <div style="width: 80px; height: 2px; background: linear-gradient(90deg, transparent, #C9A961, transparent); margin: 0 auto 28px;"></div>
            <div class="cover-title">벤처인증 마스터 리포트</div>
            <div class="cover-company">{topic}</div>
        </div>
    </div>
""")

    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n', 1)
        title = lines[0].strip('[] #')
        body = lines[1] if len(lines) > 1 else ""
        if not title.strip(): continue

        body_html = ""
        for line in body.split('\n'):
            s = line.strip()
            if not s: continue
            if s.startswith('V ') or s.startswith('V\u3000'):
                body_html += f'<div class="v-item"><span class="v-badge">V</span><span>{s[2:]}</span></div>\n'
            elif s.startswith('- ') or s.startswith('-'):
                body_html += f'<div class="bold-line">{s}</div>\n'
            else:
                body_html += f'<div class="text-line">{s}</div>\n'

        html_parts.append(f"""
    <div class="page content-page">
        <div class="page-header">
            <svg class="logo-svg" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="40" height="40" rx="8" fill="#1B3A6B"/>
                <path d="M20 10L30 20L20 30L10 20L20 10Z" fill="#C9A961"/>
            </svg>
            <div class="page-title-main">{title}</div>
        </div>
        <div class="page-body">
            {body_html}
        </div>
    </div>
        """)

    html_parts.append("</body>\n</html>")
    return "\n".join(html_parts)

# =====================================================================
# 세션 초기화
# =====================================================================
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = "1"
if 'backup_dismissed' not in st.session_state:
    st.session_state.backup_dismissed = False
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = None
if 'report_sections' not in st.session_state:
    st.session_state.report_sections = None
if 'admin_dashboard_mode' not in st.session_state:
    st.session_state.admin_dashboard_mode = False
if 'picked_tech' not in st.session_state:
    st.session_state.picked_tech = None
if 'step2_topic' not in st.session_state:
    st.session_state.step2_topic = ''

MAX_MONTHLY_LIMIT = 30
DAILY_API_LIMIT = 230
if 'daily_api_count' not in st.session_state:
    st.session_state.daily_api_count = 0
    st.session_state.daily_api_date = date.today().isoformat()

if st.session_state.daily_api_date != date.today().isoformat():
    st.session_state.daily_api_count = 0
    st.session_state.daily_api_date = date.today().isoformat()

# =====================================================================
# 🔐 로그인
# =====================================================================
if st.session_state.authenticated_user is None:
    _, lc, _ = st.columns([1, 1.5, 1])
    with lc:
        st.markdown("""
            <div class="login-hero">
                <span class="badge">VENTURE CERTIFICATION</span>
                <div class="title">🏛️ 중소기업경영지원단</div>
                <div class="sub">벤처인증 AI 마스터 컨설턴트</div>
            </div>
        """, unsafe_allow_html=True)

        login_email = st.text_input("이메일", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        st.write("")
        b1, b2 = st.columns(2)
        if b1.button("로그인", type="primary", use_container_width=True):
            user = get_user(user_db, login_email)
            if user and user.get("approved"):
                st.session_state.authenticated_user = login_email
                st.rerun()
            else:
                st.error("❌ 미등록 계정이거나 승인 대기 중입니다.")
        if b2.button("승인 신청", use_container_width=True):
            if login_email and login_email not in user_db["users"]:
                user_db["users"][login_email] = {
                    "approved": False, "is_admin": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "usage_count": 0, "last_reset_month": date.today().month
                }
                save_db(user_db)
                st.success("📩 승인 신청 완료! 관리자 승인 후 이용 가능합니다.")
            elif login_email in user_db["users"]:
                st.warning("이미 등록된 이메일입니다.")
            else:
                st.warning("이메일을 입력해주세요.")
    st.stop()

# =====================================================================
# ✅ 메인 대시보드
# =====================================================================
current_user_email = st.session_state.authenticated_user
current_user = get_user(user_db, current_user_email)
if not current_user:
    st.session_state.authenticated_user = None
    st.rerun()

# ── 사이드바 ──
with st.sidebar:
    st.markdown(f"**👤 {current_user_email}**")
    usage = current_user.get("usage_count", 0)
    pct = min(usage / MAX_MONTHLY_LIMIT, 1.0)
    st.markdown(f"""
        <div style="margin:8px 0 4px;font-size:12px;opacity:0.6;">월간 사용량</div>
        <div style="background:rgba(255,255,255,0.12);border-radius:6px;height:7px;overflow:hidden;">
            <div style="background:linear-gradient(90deg,#d4af37,#f0d060);width:{pct*100}%;height:100%;border-radius:6px;"></div>
        </div>
        <div style="font-size:12px;margin-top:3px;opacity:0.7;">{usage} / {MAX_MONTHLY_LIMIT} 회</div>
    """, unsafe_allow_html=True)

    daily_used = st.session_state.daily_api_count
    daily_pct = min(daily_used / DAILY_API_LIMIT, 1.0)
    daily_color = "#4ade80" if daily_pct < 0.7 else ("#facc15" if daily_pct < 0.9 else "#f87171")
    st.markdown(f"""
        <div style="margin:8px 0 4px;font-size:12px;opacity:0.6;">오늘 API 사용량</div>
        <div style="background:rgba(255,255,255,0.12);border-radius:6px;height:7px;overflow:hidden;">
            <div style="background:{daily_color};width:{daily_pct*100}%;height:100%;border-radius:6px;"></div>
        </div>
        <div style="font-size:12px;margin-top:3px;opacity:0.7;">{daily_used} / {DAILY_API_LIMIT} 회 (일일 한도)</div>
    """, unsafe_allow_html=True)

    gist_on = is_gist_connected()
    gist_fail = st.session_state.get("gist_sync_failed", False)
    if gist_on and not gist_fail:
        st.markdown('<p style="font-size:11px;color:#4ade80;margin-top:8px;">🟢 Gist 동기화 정상</p>', unsafe_allow_html=True)
    elif gist_on:
        st.markdown('<p style="font-size:11px;color:#facc15;margin-top:8px;">🟡 Gist 동기화 지연</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-size:11px;color:#f87171;margin-top:8px;">🔴 Gist 미연결</p>', unsafe_allow_html=True)

    st.write("")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()

    if current_user.get("is_admin"):
        st.divider()
        st.markdown('<p style="font-size:11px;color:#d4af37;letter-spacing:2px;font-weight:700;">👑 관리자</p>', unsafe_allow_html=True)
        if 'admin_msg' in st.session_state:
            st.success(st.session_state.admin_msg)
            del st.session_state.admin_msg
        
        # ── 빠른 요약 카드 (사이드바용) ──
        _logs = user_db.get("usage_logs", [])
        if _logs:
            _total_cost = sum(l.get('cost_usd', 0) for l in _logs)
            _today_cost = sum(l.get('cost_usd', 0) for l in _logs if l.get('ts', '').startswith(date.today().isoformat()))
            _total_calls = len(_logs)
            st.markdown(f"""
            <div style="background:rgba(212,175,55,0.08);border:1px solid rgba(212,175,55,0.25);border-radius:8px;padding:10px 12px;margin-bottom:10px;font-size:11px;">
                <div style="color:#d4af37;font-weight:700;margin-bottom:4px;">💰 API 사용 요약</div>
                <div style="opacity:0.85;">총 <b>${_total_cost:.4f}</b> · ₩{int(_total_cost*1400):,}</div>
                <div style="opacity:0.85;">오늘 <b>${_today_cost:.4f}</b> · {_total_calls}회</div>
                <div style="opacity:0.6;margin-top:4px;">📈 상세는 <b>메인 화면 우측 상단</b></div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("회원 승인 관리", expanded=True):
            # 사용자별 누적 비용 계산
            _user_costs = {}
            for l in _logs:
                em = l.get('email', '')
                _user_costs[em] = _user_costs.get(em, 0) + l.get('cost_usd', 0)
            
            rows = []
            for em, i in user_db["users"].items():
                rows.append({
                    "이메일": em,
                    "상태": "✅" if i.get("approved") else "⏳",
                    "사용": i.get("usage_count", 0),
                    "비용($)": f"{_user_costs.get(em, 0):.3f}"
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            target = st.selectbox("대상", list(user_db["users"].keys()), label_visibility="collapsed")
            ac1, ac2 = st.columns(2)
            if ac1.button("✅ 승인", use_container_width=True, key="adm_ok"):
                user_db["users"][target]["approved"] = True
                save_db(user_db)
                st.session_state.admin_msg = f"'{target}' 승인됨"
                st.rerun()
            if ac2.button("🚫 해제", use_container_width=True, key="adm_no"):
                user_db["users"][target]["approved"] = False
                save_db(user_db)
                st.session_state.admin_msg = f"'{target}' 해제됨"
                st.rerun()

        with st.expander("🔐 DB 저장소 관리"):
            if gist_on:
                if not gist_fail:
                    st.success("✅ Gist 연결 정상 — 데이터 영구 보존")
                else:
                    st.warning("⚠️ Gist 동기화 지연")
                    if st.button("🔄 수동 동기화", use_container_width=True, key="sync_btn"):
                        if gist_save(user_db):
                            st.session_state.gist_sync_failed = False
                            st.session_state.admin_msg = "✅ 동기화 성공!"
                            st.rerun()
                        else:
                            st.error("실패. 토큰/ID 확인")
            else:
                st.error("🔴 Gist 미연결")
                with st.expander("📖 연결 가이드"):
                    st.markdown("""
**1. GitHub Token 생성**
- [Settings → Tokens](https://github.com/settings/tokens)
- "Generate new token (classic)" → **gist** 체크

**2. Gist 생성**
- [gist.github.com](https://gist.github.com)
- 파일명: `venture_users.json` / 내용: `{}`

**3. Secrets에 추가**
                    """)
                    st.code('github_token = "ghp_토큰"\ngist_id = "Gist아이디"\ngist_filename = "venture_users.json"', language="toml")

            st.divider()
            total = len(user_db["users"])
            approved = sum(1 for u in user_db["users"].values() if u.get("approved"))
            st.caption(f"📊 회원 {total}명 (승인 {approved}) · 저장: {'Gist' if gist_on else '로컬'}")

            st.download_button("📥 DB 백업", json.dumps(user_db, ensure_ascii=False, indent=2), file_name=f"backup_{date.today()}.json", mime="application/json", use_container_width=True)

            uploaded_db = st.file_uploader("📤 복구", type=["json"], key="db_restore", label_visibility="collapsed")
            if uploaded_db:
                try:
                    preview = json.loads(uploaded_db.read())
                    uploaded_db.seek(0)
                    if "users" in preview:
                        st.caption(f"✅ 유효: {len(preview['users'])}명")
                        if st.button("🚨 덮어쓰기", type="primary", use_container_width=True):
                            save_db(preview)
                            st.session_state.admin_msg = f"✅ {len(preview['users'])}명 복구!"
                            st.rerun()
                    else:
                        st.error("올바른 파일 아님")
                except Exception:
                    st.error("JSON 파싱 실패")

    if current_user.get("is_admin"):
        st.divider()
        if st.button("🔄 DB 새로고침", use_container_width=True, key="refresh_db"):
            st.session_state["user_db_cache"] = load_db()
            st.rerun()

# ── Claude API ──
try:
    API_KEY = st.secrets["anthropic_api_key"]
    client = anthropic.Anthropic(api_key=API_KEY)
except Exception:
    st.error("⚠️ Secrets에서 anthropic_api_key를 찾을 수 없습니다.\n\n`.streamlit/secrets.toml`에 다음을 추가하세요:\n```\nanthropic_api_key = \"sk-ant-...\"\n```")
    st.stop()

# =====================================================================
# 🎛️ 모델 선택 UI (사이드바 상단에 배치 — API 호출 전에 선정)
# =====================================================================
MODEL_CHOICES = {
    "⚡ 절약형 (Haiku 4.5)":    {"id": "claude-haiku-4-5-20251001", "desc": "빠르고 저렴",    "input": 1.00,  "output": 5.00},
    "⭐ 균형형 (Sonnet 4.6)":   {"id": "claude-sonnet-4-6",          "desc": "최적 가성비",   "input": 3.00,  "output": 15.00},
    "👑 최고급 (Opus 4.7)":     {"id": "claude-opus-4-7",             "desc": "최상급 품질",   "input": 5.00,  "output": 25.00},
}

_default_model_id = st.secrets.get("claude_model", "claude-sonnet-4-6")
_default_label = "⭐ 균형형 (Sonnet 4.6)"
for label, info in MODEL_CHOICES.items():
    if info["id"] == _default_model_id:
        _default_label = label
        break

if 'selected_model_label' not in st.session_state:
    st.session_state.selected_model_label = _default_label

with st.sidebar:
    st.divider()
    st.markdown('<p style="font-size:11px;color:#d4af37;letter-spacing:2px;font-weight:700;margin-bottom:4px;">🤖 AI 품질 선택</p>', unsafe_allow_html=True)
    
    selected_label = st.radio(
        "모델",
        list(MODEL_CHOICES.keys()),
        index=list(MODEL_CHOICES.keys()).index(st.session_state.selected_model_label),
        label_visibility="collapsed",
        key="model_radio"
    )
    st.session_state.selected_model_label = selected_label
    
    _info = MODEL_CHOICES[selected_label]
    target_model_name = _info["id"]
    
    st.markdown(f"""
    <div style="background:rgba(212,175,55,0.08);border:1px solid rgba(212,175,55,0.25);border-radius:8px;padding:8px 10px;margin-top:6px;font-size:11px;">
        <div style="color:#d4af37;font-weight:700;">{_info['desc']}</div>
        <div style="opacity:0.7;margin-top:3px;">입력 ${_info['input']} · 출력 ${_info['output']} /1M</div>
        <div style="opacity:0.6;margin-top:2px;font-family:monospace;font-size:10px;">{target_model_name}</div>
    </div>
    """, unsafe_allow_html=True)

model_name = target_model_name

# ── Claude 호출 헬퍼 함수 ──
def build_content_blocks(prompt_text, extra_content=None, extra_content2=None):
    blocks = []
    for content in [extra_content, extra_content2]:
        if content is None:
            continue
        if isinstance(content, dict) and content.get("mime_type") == "application/pdf":
            pdf_b64 = base64.standard_b64encode(content["data"]).decode("utf-8")
            blocks.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}
            })
        elif isinstance(content, Image.Image):
            buf = io.BytesIO()
            if content.mode != "RGB":
                content = content.convert("RGB")
            content.save(buf, format="JPEG", quality=85)
            img_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
            blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
    blocks.append({"type": "text", "text": prompt_text})
    return blocks

def claude_generate(prompt_text, extra_content=None, extra_content2=None, max_tokens=4096):
    content_blocks = build_content_blocks(prompt_text, extra_content, extra_content2)
    response = client.messages.create(
        model=target_model_name,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content_blocks}]
    )
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    in_tokens = getattr(response.usage, "input_tokens", 0) or 0
    out_tokens = getattr(response.usage, "output_tokens", 0) or 0
    return text, in_tokens, out_tokens

CLAUDE_PRICING = {
    "claude-sonnet-4-6":       {"input": 3.00,  "output": 15.00},
    "claude-opus-4-7":         {"input": 5.00,  "output": 25.00},
    "claude-opus-4-6":         {"input": 5.00,  "output": 25.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
}

def calc_cost_usd(model, in_tok, out_tok):
    p = CLAUDE_PRICING.get(model, CLAUDE_PRICING["claude-sonnet-4-6"])
    return (in_tok / 1_000_000) * p["input"] + (out_tok / 1_000_000) * p["output"]

def log_usage(db, user_email, step_name, in_tokens, out_tokens, model):
    if "usage_logs" not in db:
        db["usage_logs"] = []
    cost = calc_cost_usd(model, in_tokens, out_tokens)
    log_entry = {
        "ts": datetime.now().isoformat(timespec='seconds'),
        "email": user_email,
        "step": step_name,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "cost_usd": round(cost, 6),
        "model": model
    }
    db["usage_logs"].append(log_entry)
    if len(db["usage_logs"]) > 5000:
        db["usage_logs"] = db["usage_logs"][-5000:]
    return log_entry

# =====================================================================
# 헤더 + 경고
# =====================================================================
st.markdown("""
    <div class="dash-header">
        <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
        <p><span class="gold">중소기업경영지원단</span> · AI 마스터 컨설턴트</p>
    </div>
""", unsafe_allow_html=True)

if current_user.get("is_admin") and not is_gist_connected() and not st.session_state.get("backup_dismissed"):
    wc1, wc2 = st.columns([6, 1])
    with wc1:
        st.error("🔴 **Gist 미연결!** 서버 재시작 시 회원 데이터가 초기화됩니다. 사이드바에서 설정하세요.")
    with wc2:
        if st.button("✕", key="dismiss_alert"):
            st.session_state.backup_dismissed = True
            st.rerun()

if current_user.get("is_admin"):
    bcol1, bcol2 = st.columns([3, 1])
    with bcol1:
        if st.button("🔄 새 기업 컨설팅 시작"):
            st.session_state.suggestions = None
            st.session_state.report_sections = None
            st.session_state.picked_tech = None
            st.session_state.step2_topic = ''
            st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
            st.session_state.admin_dashboard_mode = False
            st.rerun()
    with bcol2:
        _is_dash = bool(st.session_state.admin_dashboard_mode)
        dash_label = "📊 컨설팅 화면으로" if _is_dash else "📈 관리자 대시보드"
        if st.button(dash_label, use_container_width=True, type="primary" if not _is_dash else "secondary"):
            st.session_state.admin_dashboard_mode = not _is_dash
            st.rerun()
else:
    if st.button("🔄 새 기업 컨설팅 시작"):
        st.session_state.suggestions = None
        st.session_state.report_sections = None
        st.session_state.picked_tech = None
        st.session_state.step2_topic = ''
        st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
        st.rerun()

# =====================================================================
# 📈 관리자 대시보드 모드
# =====================================================================
if current_user.get("is_admin") and st.session_state.admin_dashboard_mode:
    st.markdown('<div class="sec-title"><h3>📈 관리자 대시보드 · 전체 사용량 분석</h3></div>', unsafe_allow_html=True)
    logs = user_db.get("usage_logs", [])
    users_dict = user_db.get("users", {})
    
    if not logs:
        st.info("📭 아직 누적된 사용 로그가 없습니다.")
    else:
        df = pd.DataFrame(logs)
        df['ts'] = pd.to_datetime(df['ts'])
        df['date'] = df['ts'].dt.date
        df['hour'] = df['ts'].dt.hour
        df['weekday'] = df['ts'].dt.day_name()
        df['total_tokens'] = df['in_tokens'] + df['out_tokens']
        
        total_calls = len(df)
        total_cost = df['cost_usd'].sum()
        total_tokens = df['total_tokens'].sum()
        unique_users = df['email'].nunique()
        
        current_month_mask = (df['ts'].dt.month == date.today().month) & (df['ts'].dt.year == date.today().year)
        month_cost = df[current_month_mask]['cost_usd'].sum()
        month_calls = current_month_mask.sum()
        
        today_mask = df['date'] == date.today()
        today_cost = df[today_mask]['cost_usd'].sum()
        today_calls = today_mask.sum()
        
        kpi_html = f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px;">
            <div style="background:linear-gradient(135deg,#0b1f52,#1a3a7a);color:white;padding:18px;border-radius:12px;border-left:4px solid #d4af37;">
                <div style="font-size:11px;color:#d4af37;font-weight:700;letter-spacing:1.5px;">TOTAL COST</div>
                <div style="font-size:24px;font-weight:900;margin-top:4px;">${total_cost:,.4f}</div>
                <div style="font-size:11px;opacity:0.7;margin-top:4px;">≈ ₩{int(total_cost*1400):,} · {total_calls}회 호출</div>
            </div>
            <div style="background:linear-gradient(135deg,#1a3a7a,#2a5298);color:white;padding:18px;border-radius:12px;border-left:4px solid #4ade80;">
                <div style="font-size:11px;color:#4ade80;font-weight:700;letter-spacing:1.5px;">THIS MONTH</div>
                <div style="font-size:24px;font-weight:900;margin-top:4px;">${month_cost:,.4f}</div>
                <div style="font-size:11px;opacity:0.7;margin-top:4px;">≈ ₩{int(month_cost*1400):,} · {month_calls}회</div>
            </div>
            <div style="background:linear-gradient(135deg,#1a3a7a,#2a5298);color:white;padding:18px;border-radius:12px;border-left:4px solid #facc15;">
                <div style="font-size:11px;color:#facc15;font-weight:700;letter-spacing:1.5px;">TODAY</div>
                <div style="font-size:24px;font-weight:900;margin-top:4px;">${today_cost:,.4f}</div>
                <div style="font-size:11px;opacity:0.7;margin-top:4px;">≈ ₩{int(today_cost*1400):,} · {today_calls}회</div>
            </div>
            <div style="background:linear-gradient(135deg,#0b1f52,#1a3a7a);color:white;padding:18px;border-radius:12px;border-left:4px solid #f472b6;">
                <div style="font-size:11px;color:#f472b6;font-weight:700;letter-spacing:1.5px;">ACTIVE USERS</div>
                <div style="font-size:24px;font-weight:900;margin-top:4px;">{unique_users}명</div>
                <div style="font-size:11px;opacity:0.7;margin-top:4px;">{total_tokens:,} 토큰 사용</div>
            </div>
        </div>
        """
        st.markdown(kpi_html, unsafe_allow_html=True)
        
        fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
        with fcol1:
            period = st.selectbox("📅 기간", ["전체 기간", "오늘", "최근 7일", "최근 30일", "이번 달"], index=0)
        with fcol2:
            user_filter = st.selectbox("👤 사용자 필터", ["전체"] + sorted(df['email'].unique().tolist()))
        with fcol3:
            st.write("")
            refresh = st.button("🔄 새로고침", use_container_width=True)
            if refresh:
                st.session_state["user_db_cache"] = load_db()
                st.rerun()
        
        filtered = df.copy()
        if period == "오늘":
            filtered = filtered[filtered['date'] == date.today()]
        elif period == "최근 7일":
            cutoff = pd.Timestamp(date.today()) - pd.Timedelta(days=7)
            filtered = filtered[filtered['ts'] >= cutoff]
        elif period == "최근 30일":
            cutoff = pd.Timestamp(date.today()) - pd.Timedelta(days=30)
            filtered = filtered[filtered['ts'] >= cutoff]
        elif period == "이번 달":
            filtered = filtered[(filtered['ts'].dt.month == date.today().month) & (filtered['ts'].dt.year == date.today().year)]
        
        if user_filter != "전체":
            filtered = filtered[filtered['email'] == user_filter]
        
        if filtered.empty:
            st.warning("⚠️ 선택한 기간에 데이터가 없습니다.")
        else:
            st.caption(f"📊 필터 결과: **{len(filtered)}건**, 총 **${filtered['cost_usd'].sum():.4f}** (₩{int(filtered['cost_usd'].sum()*1400):,})")
            
            st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">🏆 사용자별 사용량 순위 (비용 기준)</div>', unsafe_allow_html=True)
            user_agg = filtered.groupby('email').agg(
                호출수=('ts', 'count'), 입력토큰=('in_tokens', 'sum'), 출력토큰=('out_tokens', 'sum'), 총토큰=('total_tokens', 'sum'), 비용USD=('cost_usd', 'sum'), 마지막사용=('ts', 'max')
            ).reset_index().sort_values('비용USD', ascending=False)
            
            user_agg['비용원'] = (user_agg['비용USD'] * 1400).astype(int)
            user_agg['마지막사용'] = user_agg['마지막사용'].dt.strftime('%Y-%m-%d %H:%M')
            user_agg.columns = ['이메일', '호출수', '입력토큰', '출력토큰', '총토큰', '비용($)', '마지막사용', '비용(₩)']
            user_agg.insert(0, '순위', range(1, len(user_agg) + 1))
            display_agg = user_agg[['순위', '이메일', '호출수', '입력토큰', '출력토큰', '총토큰', '비용($)', '비용(₩)', '마지막사용']].copy()
            display_agg['비용($)'] = display_agg['비용($)'].apply(lambda x: f"${x:.4f}")
            display_agg['비용(₩)'] = display_agg['비용(₩)'].apply(lambda x: f"₩{x:,}")
            display_agg['입력토큰'] = display_agg['입력토큰'].apply(lambda x: f"{x:,}")
            display_agg['출력토큰'] = display_agg['출력토큰'].apply(lambda x: f"{x:,}")
            display_agg['총토큰'] = display_agg['총토큰'].apply(lambda x: f"{x:,}")
            st.dataframe(display_agg, use_container_width=True, hide_index=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:8px 0;">📊 기능별 호출 횟수</div>', unsafe_allow_html=True)
                step_counts = filtered.groupby('step').size().reset_index(name='호출수').sort_values('호출수', ascending=False)
                st.bar_chart(step_counts.set_index('step'))
            with c2:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:8px 0;">💰 기능별 비용 분포</div>', unsafe_allow_html=True)
                step_cost = filtered.groupby('step')['cost_usd'].sum().reset_index()
                step_cost.columns = ['step', '비용(USD)']
                st.bar_chart(step_cost.set_index('step'))
            
            if 'model' in filtered.columns and filtered['model'].nunique() > 1:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">🤖 모델별 사용 비율</div>', unsafe_allow_html=True)
                _model_short = {"claude-opus-4-7": "👑 Opus 4.7", "claude-opus-4-6": "👑 Opus 4.6", "claude-sonnet-4-6": "⭐ Sonnet 4.6", "claude-haiku-4-5-20251001": "⚡ Haiku 4.5"}
                mc1, mc2 = st.columns(2)
                with mc1:
                    st.caption("📞 모델별 호출 횟수")
                    model_cnt = filtered.copy()
                    model_cnt['모델'] = model_cnt['model'].apply(lambda x: _model_short.get(x, x))
                    st.bar_chart(model_cnt.groupby('모델').size())
                with mc2:
                    st.caption("💰 모델별 누적 비용 (USD)")
                    model_cost_df = filtered.copy()
                    model_cost_df['모델'] = model_cost_df['model'].apply(lambda x: _model_short.get(x, x))
                    st.bar_chart(model_cost_df.groupby('모델')['cost_usd'].sum())
            
            st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">📈 일별 사용 추이</div>', unsafe_allow_html=True)
            daily = filtered.groupby('date').agg(호출수=('ts', 'count'), 비용USD=('cost_usd', 'sum')).reset_index()
            daily['date'] = pd.to_datetime(daily['date'])
            daily = daily.set_index('date')
            dc1, dc2 = st.columns(2)
            with dc1:
                st.caption("📞 일별 호출 횟수")
                st.line_chart(daily[['호출수']])
            with dc2:
                st.caption("💵 일별 비용 (USD)")
                st.line_chart(daily[['비용USD']])
            
            st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">🕐 시간대별 사용 패턴 (요일 × 시)</div>', unsafe_allow_html=True)
            weekday_map = {'Monday': '월', 'Tuesday': '화', 'Wednesday': '수', 'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'}
            filtered_copy = filtered.copy()
            filtered_copy['요일'] = filtered_copy['weekday'].map(weekday_map)
            heatmap = filtered_copy.groupby(['요일', 'hour']).size().unstack(fill_value=0)
            weekday_order = ['월', '화', '수', '목', '금', '토', '일']
            heatmap = heatmap.reindex([w for w in weekday_order if w in heatmap.index])
            for h in range(24):
                if h not in heatmap.columns:
                    heatmap[h] = 0
            heatmap = heatmap[sorted(heatmap.columns)]
            if not heatmap.empty:
                st.dataframe(heatmap.style.background_gradient(cmap='YlOrRd', axis=None).format("{:.0f}"), use_container_width=True)
                st.caption("💡 색이 진할수록 해당 시간대에 많이 사용됨 (숫자 = 호출 횟수)")
            
            with st.expander(f"🔍 상세 로그 보기 (총 {len(filtered)}건)", expanded=False):
                detail = filtered.sort_values('ts', ascending=False).copy()
                detail['시각'] = detail['ts'].dt.strftime('%Y-%m-%d %H:%M:%S')
                detail['비용($)'] = detail['cost_usd'].apply(lambda x: f"${x:.5f}")
                _model_short = {"claude-opus-4-7": "👑 Opus 4.7", "claude-opus-4-6": "👑 Opus 4.6", "claude-sonnet-4-6": "⭐ Sonnet 4.6", "claude-haiku-4-5-20251001": "⚡ Haiku 4.5"}
                detail['모델'] = detail['model'].apply(lambda x: _model_short.get(x, x))
                detail_display = detail[['시각', 'email', 'step', '모델', 'in_tokens', 'out_tokens', '비용($)']].copy()
                detail_display.columns = ['시각', '이메일', '기능', '모델', '입력토큰', '출력토큰', '비용($)']
                st.dataframe(detail_display, use_container_width=True, hide_index=True)
            
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                csv_summary = user_agg.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 사용자별 요약 CSV", csv_summary, file_name=f"사용량요약_{date.today()}.csv", mime="text/csv", use_container_width=True)
            with dl_col2:
                csv_detail = filtered[['ts', 'email', 'step', 'in_tokens', 'out_tokens', 'cost_usd', 'model']].to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 상세 로그 CSV", csv_detail, file_name=f"상세로그_{date.today()}.csv", mime="text/csv", use_container_width=True)
            
            with st.expander("⚠️ 로그 관리 (위험 구역)"):
                st.caption(f"현재 DB에 저장된 총 로그: **{len(logs)}건**")
                if st.button("🗑️ 모든 로그 삭제 (복구 불가)", key="del_logs"):
                    if st.session_state.get('confirm_del_logs'):
                        user_db['usage_logs'] = []
                        save_db(user_db)
                        st.session_state['confirm_del_logs'] = False
                        st.success("✅ 모든 로그가 삭제되었습니다.")
                        st.rerun()
                    else:
                        st.session_state['confirm_del_logs'] = True
                        st.warning("⚠️ 정말 삭제하시겠습니까? 한 번 더 버튼을 누르면 삭제됩니다.")
    
    st.stop()

# =====================================================================
# 메인 2단 (Step 1 & Step 2)
# =====================================================================
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="sec-title"><h3>📋 Step 1 · 분석 및 기술 주제 추천</h3></div>', unsafe_allow_html=True)
    biz_type = st.radio("업종", ["일반 기업", "IT / SW", "초기기업"], horizontal=True)
    uploaded_file = st.file_uploader("사업자등록증 (JPG/PNG/PDF)", type=["jpg", "png", "pdf"], key=f"up_{st.session_state.uploader_key}")

    analysis_content = None
    if uploaded_file:
        fb = uploaded_file.getvalue()
        analysis_content = {"mime_type": "application/pdf", "data": fb} if uploaded_file.type == "application/pdf" else Image.open(uploaded_file)
        if uploaded_file.type == "application/pdf":
            st.session_state['step1_analysis_type'] = 'pdf'
            st.session_state['step1_analysis_data'] = fb
        else:
            st.session_state['step1_analysis_type'] = 'image'
            buf = io.BytesIO()
            Image.open(uploaded_file).save(buf, format='PNG')
            st.session_state['step1_analysis_data'] = buf.getvalue()

    user_guide_rec = st.text_area("추천 가이드 (선택)", placeholder="예: ESG 강조, 수출 중심", key=f"gr_{st.session_state.uploader_key}", height=80)

    if st.button("✨ AI 기술 주제 추천", type="primary", use_container_width=True):
        st.info(f"🔄 버튼 감지됨 · 모델: `{target_model_name}` · 업종: {biz_type}")
        
        if current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도 초과")
        elif st.session_state.daily_api_count >= DAILY_API_LIMIT:
            st.error("🚫 오늘 API 한도를 모두 사용했습니다.")
        else:
            with st.spinner(f'AI 분석 중... ({target_model_name})'):
                prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.
[{biz_type}] 분야 기업에 대해 벤처인증에 적합한 기술 주제 3개를 추천하세요.
{f'추가 지시사항: {user_guide_rec}' if user_guide_rec else ''}

[출력 규칙]
- 반드시 아래 JSON 형식으로만 출력 (마크다운 코드펜스 금지, 설명 금지)
- 3개의 기술 주제를 배열로 제공
- 각 기술명은 벤처인증 심사에서 통할 만큼 구체적이고 전문적으로

[JSON 스키마]
{{
  "suggestions": [
    {{
      "tech_name": "구체적인 기술명 (예: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술)",
      "reason": "추천 사유 (2-3문장)",
      "fitness": "벤처인증 적합도 평가 (1-2문장)"
    }},
    {{...}},
    {{...}}
  ]
}}
"""
                max_retries = 2
                last_error = None
                for attempt in range(max_retries):
                    try:
                        result_text, in_tok, out_tok = claude_generate(prompt, analysis_content, max_tokens=2048)
                        clean_text = result_text.replace('```json', '').replace('```', '').strip()
                        try:
                            parsed = json.loads(clean_text)
                            if 'suggestions' in parsed and isinstance(parsed['suggestions'], list):
                                st.session_state.suggestions = parsed
                            else:
                                st.session_state.suggestions = result_text
                        except json.JSONDecodeError:
                            st.session_state.suggestions = result_text
                        
                        st.session_state.daily_api_count += 1
                        user_db["users"][current_user_email]["usage_count"] += 1
                        log_usage(user_db, current_user_email, "Step 1 (기술 주제 추천)", in_tok, out_tok, target_model_name)
                        save_db(user_db)
                        last_error = None
                        break
                    except anthropic.RateLimitError as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            st.warning(f"⏳ Rate Limit 감지, 30초 후 재시도... ({attempt+1}/{max_retries})")
                            time.sleep(30)
                        else:
                            st.error("🚫 Claude API Rate Limit 초과. 잠시 후 다시 시도하세요.")
                    except anthropic.APIStatusError as e:
                        last_error = e
                        if e.status_code == 429:
                            st.session_state.daily_api_count = DAILY_API_LIMIT
                            st.error("🚫 API 한도 초과 또는 크레딧 부족. [console.anthropic.com](https://console.anthropic.com)에서 확인하세요.")
                        elif e.status_code == 401:
                            st.error("🚫 API 키 인증 실패. Streamlit Secrets의 `anthropic_api_key` 값을 확인하세요.")
                        elif e.status_code == 400:
                            st.error(f"🚫 잘못된 요청 (400): {e.message}")
                        else:
                            st.error(f"⚠️ API 오류 ({e.status_code}): {e.message}")
                        break
                    except Exception as e:
                        last_error = e
                        import traceback
                        st.error(f"⚠️ 예외 발생: `{type(e).__name__}` — {str(e)}")
                        with st.expander("🔍 전체 에러 트레이스백 보기"):
                            st.code(traceback.format_exc(), language="python")
                        break
                
                if last_error is None and st.session_state.suggestions:
                    st.success("✅ 생성 완료!")

    if st.session_state.suggestions is not None:
        suggestions = st.session_state.suggestions
        if isinstance(suggestions, dict) and 'suggestions' in suggestions:
            st.markdown('<div style="font-size:13px;font-weight:700;color:#92700c;margin:12px 0 6px;">💡 AI 추천 기술 주제 · 마음에 드는 걸 선택하세요</div>', unsafe_allow_html=True)
            for idx, sug in enumerate(suggestions['suggestions'], 1):
                tech_name = sug.get('tech_name', '이름 없음')
                reason = sug.get('reason', '')
                fitness = sug.get('fitness', '')
                st.markdown(f'''
                <div style="background:linear-gradient(135deg,#fffdf5,#fefce8);border:1px solid #e5d9a8;border-left:4px solid #d4af37;border-radius:10px;padding:12px 16px;margin:10px 0 0;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                        <span style="background:#0b1f52;color:#d4af37;font-weight:700;font-size:11px;padding:3px 8px;border-radius:5px;">#{idx}</span>
                        <span style="font-weight:700;color:#0b1f52;font-size:14px;">{tech_name}</span>
                    </div>
                    <div style="font-size:12.5px;color:#555;line-height:1.6;margin-top:4px;"><b>추천 사유:</b> {reason}</div>
                    <div style="font-size:12.5px;color:#555;line-height:1.6;margin-top:3px;"><b>적합도:</b> {fitness}</div>
                </div>
                ''', unsafe_allow_html=True)
                
                if st.button(f"→ 이 기술로 진행", key=f"pick_tech_{idx}", use_container_width=True):
                    st.session_state['picked_tech'] = tech_name
                    st.session_state['step2_topic'] = tech_name
                    st.rerun()
        else:
            raw_text = str(suggestions) if not isinstance(suggestions, str) else suggestions
            st.markdown(f'<div class="ai-result"><b>💡 AI 추천 기술 주제</b><br><br>{raw_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            st.caption("💡 위 추천 중 마음에 드는 기술명을 복사해서 오른쪽 Step 2 '확정 기술명'에 붙여넣거나, 원하는 기술명을 직접 입력하세요.")

with col2:
    st.markdown('<div class="sec-title"><h3>📑 Step 2 · 마스터 리포트 생성</h3></div>', unsafe_allow_html=True)
    
    _prefill = st.session_state.get('picked_tech', '') or st.session_state.get('step2_topic', '')
    selected_topic = st.text_input(
        "확정 기술명",
        value=_prefill,
        placeholder="예: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술",
        key=f"topic_{st.session_state.uploader_key}",
        help="AI 추천 중 선택 버튼을 누르면 자동으로 채워집니다. 직접 타이핑/수정도 가능해요."
    )
    if selected_topic:
        st.session_state['step2_topic'] = selected_topic
        if st.session_state.get('picked_tech') and selected_topic != st.session_state.get('picked_tech'):
            st.session_state['picked_tech'] = None
    user_guide_rep = st.text_area("리포트 지시사항 (선택)", placeholder="예: 시장규모 숫자 강조", key=f"gp_{st.session_state.uploader_key}", height=80)

    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not selected_topic:
            st.warning("기술명을 입력하세요.")
        elif current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도 초과")
        elif st.session_state.daily_api_count >= DAILY_API_LIMIT:
            st.error("🚫 오늘 API 한도를 모두 사용했습니다.")
        else:
            with st.spinner('리포트 생성 중... (30초~1분)'):
                form_prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.

확정 기술(제품/서비스)명: [{selected_topic}]
{f'추가 지시사항: {user_guide_rep}' if user_guide_rep else ''}

⚠️ 규칙: 지어낸 숫자 금지, 구체적 서술, V자 요약 양식을 1번 항목에 반드시 포함

[V자 요약 양식]
- 신청기술(제품/서비스)명: {selected_topic}
- 신청기술(제품/서비스)요약: (기술 요약)
V 기존 시장에 [문제점]이 있는데, [기존 업체 한계]라는 이유로 사람들이 여전히 불편을 겪고 있음
V 당사에서 [해결 방법]으로 해결책을 찾았으며, 기존 시장 기술과 [차별점]이라는 확실한 기술적 차이를 보유
V 현재 당사 보유/개발 중 기술명은 [기술명], 전체 시장은 [시장 규모]이며 잠재 고객 니즈 충족 시 [성장 전망] 기대
V 당사 기술은 [핵심 특징]을 갖고 있으며 [고객 가치]라는 이유로 혁신적 해결책, 잠재 고객 만족도가 높을 수 있음
V 기술에 대한 [지식재산권 현황]이며 [연구개발 조직] 보유, 끊임없는 R&D로 지속 발전 가능한 기술적 역량 보유
V 시장진입을 위해 [마케팅 활동 현황] 진행 중, 현재 [확보 규모] 시장 확보, 향후 [마케팅 계획] 수립하여 진행 예정
V 당사 성과가 가능한 이유는 [핵심 역량]이 있기 때문이며 향후 [성장 목표]의 공격적 성장을 해낼 것임

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
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        result_text, in_tok, out_tok = claude_generate(form_prompt, analysis_content, max_tokens=8192)
                        st.session_state.report_sections = result_text.split('### ')
                        st.session_state.daily_api_count += 1
                        user_db["users"][current_user_email]["usage_count"] += 1
                        log_usage(user_db, current_user_email, "Step 2 (마스터 리포트)", in_tok, out_tok, target_model_name)
                        save_db(user_db)
                        break
                    except anthropic.RateLimitError:
                        if attempt < max_retries - 1:
                            st.warning(f"⏳ Rate Limit 감지, 30초 후 재시도... ({attempt+1}/{max_retries})")
                            time.sleep(30)
                        else:
                            st.error("🚫 Claude API Rate Limit 초과. 잠시 후 다시 시도하세요.")
                    except anthropic.APIStatusError as e:
                        if e.status_code == 429:
                            st.session_state.daily_api_count = DAILY_API_LIMIT
                            st.error("🚫 API 한도 초과 또는 크레딧 부족.")
                        else:
                            st.error(f"⚠️ API 오류 ({e.status_code}): {e.message}")
                        break
                    except Exception as e:
                        st.error(f"⚠️ 오류: {e}")
                        break

# =====================================================================
# 📄 HTML 리포트 출력 및 다운로드 (Step 3 대체)
# =====================================================================
if st.session_state.report_sections is not None:
    st.divider()
    st.markdown('<div class="sec-title"><h3>📄 마스터 리포트 완성 (HTML 다운로드)</h3></div>', unsafe_allow_html=True)
    st.success("✅ **AI 리포트 생성이 완료되었습니다.** 아래 버튼을 눌러 디자인이 적용된 HTML 리포트 원본을 다운로드하세요.")
    
    # 세션에서 생성된 섹션 데이터를 HTML로 변환
    html_content = generate_html_report(selected_topic, st.session_state.report_sections)
    
    col_dl, col_space = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="💾 디자인 리포트 다운로드 (.html)",
            data=html_content,
            file_name=f"벤처인증_마스터리포트_{selected_topic or '결과'}.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )
    
    st.info("💡 **안내:** 다운로드한 `.html` 파일을 더블클릭하면 웹 브라우저(크롬, 엣지 등)에서 서식과 로고가 적용된 깔끔한 보고서를 확인하고 바로 인쇄/PDF 저장하실 수 있습니다.")

st.markdown('<div style="text-align:center;padding:28px 0 10px;color:#9ca3af;font-size:11px;">© 2026 중소기업경영지원단 · 벤처인증 AI 마스터 컨설턴트</div>', unsafe_allow_html=True)
