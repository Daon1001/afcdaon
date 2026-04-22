import streamlit as st
import google.generativeai as genai
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
# 💎 CSS — Streamlit 위젯과 충돌하지 않는 안전한 셀렉터만 사용
# =====================================================================
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("""
<style>
/* ── 전역 ── */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 1200px !important;
}
header[data-testid="stHeader"] { display: none !important; }
.stApp {
    background: #f0f2f5 !important;
    font-family: 'Noto Sans KR', -apple-system, sans-serif !important;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: #0b1f52 !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] summary {
    color: white !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: white !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.2) !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {
    color: #333 !important;
}
section[data-testid="stSidebar"] .stDataFrame,
section[data-testid="stSidebar"] .stDataFrame * {
    color: #333 !important;
}
section[data-testid="stSidebar"] .stDownloadButton > button {
    background: rgba(212,175,55,0.2) !important;
    border: 1px solid rgba(212,175,55,0.4) !important;
    color: #d4af37 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}

/* ── 대시보드 헤더 ── */
.dash-header {
    background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 60%, #2a5298 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 20px;
    border-bottom: 4px solid #d4af37;
}
.dash-header h1 {
    color: white !important;
    font-size: 26px;
    font-weight: 900;
    margin: 0 !important;
}
.dash-header p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 14px;
    margin: 6px 0 0 !important;
}
.dash-header .gold { color: #d4af37 !important; font-weight: 700; }

/* ── 섹션 타이틀 ── */
.sec-title {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.sec-title h3 {
    margin: 0 !important;
    font-size: 16px;
    font-weight: 700;
    color: #0b1f52;
}

/* ── AI 결과 카드 ── */
.ai-result {
    background: linear-gradient(135deg, #fffdf5, #fefce8);
    border: 1px solid #e5d9a8;
    border-left: 5px solid #d4af37;
    border-radius: 12px;
    padding: 20px 22px;
    margin-top: 14px;
    line-height: 1.85;
    font-size: 14px;
    color: #1f2937;
}
.ai-result b { color: #92700c; }

/* ── 리포트 섹션 ── */
.rpt-body {
    background: white;
    border: 1px solid #e5e7eb;
    border-left: 5px solid #0b1f52;
    border-radius: 12px;
    padding: 20px 22px;
    line-height: 1.85;
    font-size: 14px;
    color: #374151;
}

/* ── V자 요약 ── */
.v-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 8px;
    padding: 8px 12px;
    background: #f0f4ff;
    border-radius: 8px;
    font-size: 13.5px;
    line-height: 1.7;
    color: #374151;
}
.v-badge {
    flex-shrink: 0;
    width: 24px; height: 24px;
    background: #0b1f52;
    color: #d4af37;
    font-weight: 900;
    font-size: 13px;
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 2px;
}

/* ── primary 버튼 ── */
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #d4af37 0%, #b8952e 100%) !important;
    color: #0b1f52 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
}

/* ── 인풋 ── */
.stTextInput input, .stTextArea textarea {
    border-radius: 10px !important;
    border: 1.5px solid #d1d5db !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #d4af37 !important;
    box-shadow: 0 0 0 2px rgba(212,175,55,0.15) !important;
}

/* ── 로그인 전용 ── */
.login-hero {
    background: linear-gradient(160deg, #0b1f52, #1a3a7a 50%, #2a5298);
    padding: 48px 20px 36px;
    border-radius: 18px;
    text-align: center;
    margin-bottom: 20px;
}
.login-hero .badge {
    display: inline-block;
    background: rgba(212,175,55,0.2);
    color: #d4af37;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    padding: 5px 14px;
    border-radius: 20px;
    margin-bottom: 14px;
    border: 1px solid rgba(212,175,55,0.3);
}
.login-hero .title {
    font-size: 26px;
    font-weight: 900;
    color: white;
    margin: 0 0 4px;
}
.login-hero .sub {
    font-size: 13px;
    color: rgba(255,255,255,0.65);
}
</style>
""", unsafe_allow_html=True)

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
        <div style="font-size:12px;margin-top:3px;opacity:0.7;">{daily_used} / {DAILY_API_LIMIT} 회 (무료 한도)</div>
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

        with st.expander("회원 승인 관리", expanded=True):
            rows = [{"이메일": em, "상태": "✅" if i.get("approved") else "⏳", "사용": i.get("usage_count", 0)} for em, i in user_db["users"].items()]
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

# ── Gemini API ──
try:
    API_KEY = st.secrets["gemini_api_key"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ Secrets에서 gemini_api_key를 찾을 수 없습니다.")
    st.stop()

available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
except Exception as e:
    st.error(f"⚠️ Google AI 통신 오류: {e}")
    st.stop()

target_model_name = ""
for pref in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
    if pref in available_models:
        target_model_name = pref
        break
if not target_model_name and available_models:
    target_model_name = available_models[0]
model = genai.GenerativeModel(target_model_name)
st.sidebar.caption(f"🤖 엔진: `{target_model_name}`")

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

if st.button("🔄 새 기업 컨설팅 시작"):
    st.session_state.suggestions = None
    st.session_state.report_sections = None
    st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
    st.rerun()

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

    user_guide_rec = st.text_area("추천 가이드 (선택)", placeholder="예: ESG 강조, 수출 중심", key=f"gr_{st.session_state.uploader_key}", height=80)

    if st.button("✨ AI 기술 주제 추천", type="primary", use_container_width=True):
        if current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도 초과")
        elif st.session_state.daily_api_count >= DAILY_API_LIMIT:
            st.error("🚫 오늘 무료 API 한도를 모두 사용했습니다.")
        else:
            with st.spinner('AI 분석 중...'):
                prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.
[{biz_type}] 분야 기업에 대해 벤처인증에 적합한 기술 주제 3개를 추천하세요.
각 주제: ① 기술명 ② 추천 사유 ③ 벤처인증 적합도
{f'추가: {user_guide_rec}' if user_guide_rec else ''}"""
                content = [prompt, analysis_content] if analysis_content else prompt
                
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        resp = model.generate_content(content)
                        st.session_state.suggestions = resp.text
                        st.session_state.daily_api_count += 1
                        user_db["users"][current_user_email]["usage_count"] += 1
                        save_db(user_db)
                        break
                    except Exception as e:
                        if ("429" in str(e) or "ResourceExhausted" in str(e)) and attempt < max_retries - 1:
                            st.warning(f"⏳ API 한도 감지, 30초 후 자동 재시도... ({attempt+1}/{max_retries})")
                            time.sleep(30)
                        elif "429" in str(e) or "ResourceExhausted" in str(e):
                            st.session_state.daily_api_count = DAILY_API_LIMIT
                            st.error("🚫 Google AI 무료 한도 초과.")
                        else:
                            st.error(f"⚠️ 오류: {e}")

    if st.session_state.suggestions is not None:
        st.markdown(f'<div class="ai-result"><b>💡 AI 추천 기술 주제</b><br><br>{st.session_state.suggestions.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sec-title"><h3>📑 Step 2 · 마스터 리포트 생성</h3></div>', unsafe_allow_html=True)
    selected_topic = st.text_input("확정 기술명", placeholder="예: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술", key=f"topic_{st.session_state.uploader_key}")
    user_guide_rep = st.text_area("리포트 지시사항 (선택)", placeholder="예: 시장규모 숫자 강조", key=f"gp_{st.session_state.uploader_key}", height=80)

    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not selected_topic:
            st.warning("기술명을 입력하세요.")
        elif current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도 초과")
        elif st.session_state.daily_api_count >= DAILY_API_LIMIT:
            st.error("🚫 오늘 무료 API 한도를 모두 사용했습니다.")
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
                content = [form_prompt, analysis_content] if analysis_content else form_prompt
                
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        resp = model.generate_content(content)
                        st.session_state.report_sections = resp.text.split('### ')
                        st.session_state.daily_api_count += 1
                        user_db["users"][current_user_email]["usage_count"] += 1
                        save_db(user_db)
                        break
                    except Exception as e:
                        if ("429" in str(e) or "ResourceExhausted" in str(e)) and attempt < max_retries - 1:
                            st.warning(f"⏳ API 한도 감지, 30초 후 자동 재시도... ({attempt+1}/{max_retries})")
                            time.sleep(30)
                        elif "429" in str(e) or "ResourceExhausted" in str(e):
                            st.session_state.daily_api_count = DAILY_API_LIMIT
                            st.error("🚫 Google AI 무료 한도 초과.")
                        else:
                            st.error(f"⚠️ 오류: {e}")

# =====================================================================
# 📄 리포트 출력
# =====================================================================
if st.session_state.report_sections is not None:
    st.divider()
    st.markdown('<div class="sec-title"><h3>📄 마스터 리포트 결과</h3></div>', unsafe_allow_html=True)
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("💾 전체 리포트 다운로드", full_report, file_name=f"벤처리포트_{selected_topic or 'report'}.txt")

    for section in st.session_state.report_sections:
        if not section.strip():
            continue
        lines = section.split('\n', 1)
        title = lines[0].strip('[] #')
        body = lines[1] if len(lines) > 1 else ""
        if not title.strip():
            continue
        with st.expander(f"📌 {title}", expanded=False):
            if "신청기술 요약" in title or "표준 양식" in title:
                parts = []
                for line in body.split('\n'):
                    s = line.strip()
                    if s.startswith('V ') or s.startswith('V\u3000'):
                        parts.append(f'<div class="v-item"><span class="v-badge">V</span><span>{s[2:]}</span></div>')
                    elif s.startswith('- 신청기술') or s.startswith('-신청기술'):
                        parts.append(f'<div style="font-weight:600;color:#0b1f52;margin:6px 0;">{s}</div>')
                    elif s:
                        parts.append(f'{s}<br>')
                st.markdown(f'<div class="rpt-body">{"".join(parts)}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="rpt-body">{body.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

# =====================================================================
# 🎯 Step 3: ALOA 방식 웹 화면 스캔 및 컨설팅 (클라우드 호환 완벽 적용)
# =====================================================================
st.divider()
st.markdown('<div class="sec-title"><h3>🎯 Step 3 · 화면 스캔 및 결과 복사 (ALOA 방식)</h3></div>', unsafe_allow_html=True)

col3_1, col3_2 = st.columns([2, 1])

with col3_1:
    st.info("""
    **[스캔 및 복사 사용 가이드]**
    1. 우측의 **'📸 스캔 시작'** 버튼을 누릅니다. (브라우저 상단 권한 허용 필요)
    2. 팝업창에서 **'창(Window)'** 또는 **'전체 화면'** 탭을 클릭해 작성할 정부 사이트 창을 선택 후 '공유'를 누릅니다.
    3. 약 2~3초 뒤 프로그램이 창 화면을 캡처하고 분석을 시작합니다.
    4. 분석 완료 후 아래에 생성된 결과물 우측 상단의 **[복사 아이콘]**을 클릭하여 정부 사이트에 쉽게 붙여넣기(Ctrl+V) 하세요.
    """)

with col3_2:
    # JavaScript 기반 화면 스캔 엔진 (Streamlit Cloud 환경의 한계를 돌파하는 핵심 기능)
    scan_html = """
    <div id="container" style="text-align: center; margin-top: 10px;">
        <button id="scanBtn" style="padding: 15px 30px; background: linear-gradient(135deg, #d4af37 0%, #b8952e 100%); color: #0b1f52; font-weight: bold; font-size: 16px; border: none; border-radius: 10px; cursor: pointer; width: 100%; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
            📸 화면 스캔 시작 (공유)
        </button>
        <video id="video" style="display:none;" autoplay></video>
        <canvas id="canvas" style="display:none;"></canvas>
    </div>
    <script>
        document.getElementById('scanBtn').onclick = async () => {
            try {
                // 브라우저 화면 공유 API 호출
                const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                // 화면이 완전히 로드될 수 있도록 2.5초 대기 후 캡처
                setTimeout(() => {
                    const canvas = document.getElementById('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    
                    // 캡처된 이미지를 Base64 데이터로 변환 후 Python(Streamlit)으로 전송
                    const imageData = canvas.toDataURL('image/jpeg', 0.8);
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: imageData
                    }, '*');
                    
                    // 캡처 완료 후 스트림 강제 종료 (화면 공유 끄기)
                    stream.getTracks().forEach(track => track.stop());
                }, 2500); 
            } catch (err) {
                console.error("사용자가 화면 공유를 취소했거나 오류 발생:", err);
            }
        };
    </script>
    """
    
    # HTML 컴포넌트 실행 및 데이터 수신
    captured_data = components.html(scan_html, height=100)

# JS에서 스캔 데이터를 Python으로 넘겨주면 아래 로직이 즉시 자동 실행됩니다.
if captured_data:
    try:
        # Base64 문자열 파싱 및 Pillow 이미지 객체로 변환
        header, encoded = captured_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        screen_img = Image.open(io.BytesIO(image_bytes))
        
        st.success("✅ 대상 사이트 화면 스캔이 완료되었습니다!")
        
        with st.expander("👀 스캔된 원본 화면 확인", expanded=False):
            st.image(screen_img, caption="스캔된 웹사이트 스크린샷", use_column_width=True)
        
        with st.spinner("AI 컨설턴트가 화면 문맥을 파악하고 최적의 문구를 작성 중입니다..."):
            rpa_prompt = """당신은 20년 경력의 중소기업 벤처인증 전문 컨설턴트입니다.
            제공된 데이터를 종합하여 지시를 수행하세요.
            [이미지 1]: 사업자등록증 (혹은 사용자 제공 문서)
            [이미지 2]: 사용자가 작성 중인 벤처인증/연구소 포털 사이트 화면 스크린샷. 이 화면에서 가장 크거나 활성화된 입력창의 제목(예: 사업개요, 기술혁신성 등)과 주변 문맥을 파악하세요.
            
            [지시사항]
            화면 스크린샷이 요구하는 주제에 정확하게 부합하는 300~500자 분량의 전문적인 사업계획서 텍스트를 작성하세요.
            어조는 매우 논리적이고 전문적이어야 합니다. 인사말이나 안내 멘트는 절대 하지 말고, 사용자가 즉시 복사해서 붙여넣을 수 있는 **최종 본문 텍스트만** 출력하세요."""
            
            # Step 1에서 업로드된 분석 자료가 살아있는 경우 통합 전달
            content = [rpa_prompt, screen_img] 
            if 'analysis_content' in locals() and analysis_content:
                content.insert(1, analysis_content)
                
            # Gemini에 이미지 및 프롬프트 전송
            resp = model.generate_content(content)
            generated_text = resp.text.strip()
            
            # API 사용량 카운트 (스캔 1회당 1차감)
            st.session_state.daily_api_count += 1
            user_db["users"][current_user_email]["usage_count"] += 1
            save_db(user_db)
            
            st.markdown('<div class="sec-title"><h3>📋 생성된 컨설팅 내용 (복사 전용)</h3></div>', unsafe_allow_html=True)
            
            # Streamlit의 st.code는 우측 상단에 복사(Copy) 버튼이 기본 내장되어 있어 클라우드 환경에서 매우 유용합니다.
            st.code(generated_text, language="text")
            st.caption("👆 위 텍스트 박스 우측 상단의 **'복사' 아이콘**을 클릭하면 내용이 복사됩니다.")
            st.balloons()
            
    except Exception as e:
        st.error(f"이미지 분석 중 오류가 발생했습니다: {str(e)}")
        st.warning("화면 공유 기능이 올바르게 실행되지 않았을 수 있습니다. 브라우저 설정을 확인해주세요.")

st.markdown('<div style="text-align:center;padding:28px 0 10px;color:#9ca3af;font-size:11px;">© 2026 중소기업경영지원단 · 벤처인증 AI 마스터 컨설턴트</div>', unsafe_allow_html=True)
