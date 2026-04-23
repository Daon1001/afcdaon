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

.rpt-body { background: white; border: 1px solid #e5e7eb; border-left: 5px solid #0b1f52; border-radius: 12px; padding: 20px 22px; line-height: 1.85; font-size: 14px; color: #374151; }

.v-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; padding: 8px 12px; background: #f0f4ff; border-radius: 8px; font-size: 13.5px; line-height: 1.7; color: #374151; }
.v-badge { flex-shrink: 0; width: 24px; height: 24px; background: #0b1f52; color: #d4af37; font-weight: 900; font-size: 13px; border-radius: 5px; display: flex; align-items: center; justify-content: center; margin-top: 2px; }

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
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = []  # 실시간 스캔 결과 누적 저장
if 'admin_dashboard_mode' not in st.session_state:
    st.session_state.admin_dashboard_mode = False

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
# 이용 가능한 모델 3종 (비용/품질 트레이드오프)
MODEL_CHOICES = {
    "⚡ 절약형 (Haiku 4.5)":    {"id": "claude-haiku-4-5-20251001", "desc": "빠르고 저렴",    "input": 1.00,  "output": 5.00},
    "⭐ 균형형 (Sonnet 4.6)":   {"id": "claude-sonnet-4-6",          "desc": "최적 가성비",   "input": 3.00,  "output": 15.00},
    "👑 최고급 (Opus 4.7)":     {"id": "claude-opus-4-7",             "desc": "최상급 품질",   "input": 5.00,  "output": 25.00},
}

# 기본값은 Secrets 또는 Sonnet
_default_model_id = st.secrets.get("claude_model", "claude-sonnet-4-6")
_default_label = "⭐ 균형형 (Sonnet 4.6)"
for label, info in MODEL_CHOICES.items():
    if info["id"] == _default_model_id:
        _default_label = label
        break

# 세션 초기화
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
    
    # 선택한 모델 정보 카드
    st.markdown(f"""
    <div style="background:rgba(212,175,55,0.08);border:1px solid rgba(212,175,55,0.25);border-radius:8px;padding:8px 10px;margin-top:6px;font-size:11px;">
        <div style="color:#d4af37;font-weight:700;">{_info['desc']}</div>
        <div style="opacity:0.7;margin-top:3px;">입력 ${_info['input']} · 출력 ${_info['output']} /1M</div>
        <div style="opacity:0.6;margin-top:2px;font-family:monospace;font-size:10px;">{target_model_name}</div>
    </div>
    """, unsafe_allow_html=True)


model_name = target_model_name  # 호환성을 위해 기존 변수명 유지


# ── Claude 호출 헬퍼 함수 ──
def build_content_blocks(prompt_text, extra_content=None, extra_content2=None):
    """프롬프트 + 선택적 이미지/PDF를 Claude messages 형식으로 구성"""
    blocks = []
    
    # 첨부 콘텐츠 처리 (이미지 또는 PDF)
    for content in [extra_content, extra_content2]:
        if content is None:
            continue
        if isinstance(content, dict) and content.get("mime_type") == "application/pdf":
            # PDF는 base64 인코딩
            pdf_b64 = base64.standard_b64encode(content["data"]).decode("utf-8")
            blocks.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}
            })
        elif isinstance(content, Image.Image):
            # Pillow 이미지 → base64
            buf = io.BytesIO()
            if content.mode != "RGB":
                content = content.convert("RGB")
            content.save(buf, format="JPEG", quality=85)
            img_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
            blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
    
    # 텍스트 프롬프트는 마지막에
    blocks.append({"type": "text", "text": prompt_text})
    return blocks


def claude_generate(prompt_text, extra_content=None, extra_content2=None, max_tokens=4096):
    """Claude API 호출 → (텍스트, input_tokens, output_tokens) 튜플 반환. 예외는 호출측에서 처리."""
    content_blocks = build_content_blocks(prompt_text, extra_content, extra_content2)
    response = client.messages.create(
        model=target_model_name,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content_blocks}]
    )
    # 응답 텍스트 추출 (여러 블록 있을 수 있음)
    text = "".join(block.text for block in response.content if hasattr(block, "text"))
    # 토큰 사용량 추출 (usage 객체)
    in_tokens = getattr(response.usage, "input_tokens", 0) or 0
    out_tokens = getattr(response.usage, "output_tokens", 0) or 0
    return text, in_tokens, out_tokens


# ── Claude API 가격 정보 (claude-sonnet-4-6 기준, 2026년 4월) ──
# https://platform.claude.com/docs/en/about-claude/pricing
CLAUDE_PRICING = {
    "claude-sonnet-4-6":       {"input": 3.00,  "output": 15.00},  # per 1M tokens
    "claude-opus-4-7":         {"input": 5.00,  "output": 25.00},
    "claude-opus-4-6":         {"input": 5.00,  "output": 25.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
}

def calc_cost_usd(model, in_tok, out_tok):
    """토큰 수 → USD 비용 계산"""
    p = CLAUDE_PRICING.get(model, CLAUDE_PRICING["claude-sonnet-4-6"])
    return (in_tok / 1_000_000) * p["input"] + (out_tok / 1_000_000) * p["output"]


def log_usage(db, user_email, step_name, in_tokens, out_tokens, model):
    """사용자별 상세 사용 로그 추가. DB에 영구 저장."""
    # 로그 배열이 없으면 초기화
    if "usage_logs" not in db:
        db["usage_logs"] = []
    
    cost = calc_cost_usd(model, in_tokens, out_tokens)
    
    log_entry = {
        "ts": datetime.now().isoformat(timespec='seconds'),  # ISO 타임스탬프
        "email": user_email,
        "step": step_name,  # "Step 1", "Step 2", "Step 3"
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
        "cost_usd": round(cost, 6),
        "model": model
    }
    db["usage_logs"].append(log_entry)
    
    # 로그가 너무 많아지면 오래된 것부터 삭제 (Gist 용량 제한 대응 - 최근 5000개만 유지)
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
            st.session_state.scan_results = []
            st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
            # 대시보드 모드도 해제
            st.session_state.admin_dashboard_mode = False
            st.rerun()
    with bcol2:
        _is_dash = bool(st.session_state.admin_dashboard_mode)
        dash_label = "📊 컨설팅 화면으로" if _is_dash else "📈 관리자 대시보드"
        if st.button(dash_label, use_container_width=True, type="primary" if not _is_dash else "secondary"):
            st.session_state.admin_dashboard_mode = not _is_dash
            st.rerun()
    
    # ── 디버그: 세션 상태 노출 (문제 확인 후 제거 가능) ──
    with st.expander("🔧 디버그 정보 (관리자 전용)", expanded=False):
        st.caption(f"admin_dashboard_mode = `{st.session_state.admin_dashboard_mode}` · is_admin = `{current_user.get('is_admin')}` · 로그수 = `{len(user_db.get('usage_logs', []))}`")
else:
    if st.button("🔄 새 기업 컨설팅 시작"):
        st.session_state.suggestions = None
        st.session_state.report_sections = None
        st.session_state.scan_results = []
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
        st.info("📭 아직 누적된 사용 로그가 없습니다. 사용자가 Step 1/2/3 기능을 실행하면 여기에 쌓입니다.")
    else:
        # ── DataFrame 변환 ──
        df = pd.DataFrame(logs)
        df['ts'] = pd.to_datetime(df['ts'])
        df['date'] = df['ts'].dt.date
        df['hour'] = df['ts'].dt.hour
        df['weekday'] = df['ts'].dt.day_name()
        df['total_tokens'] = df['in_tokens'] + df['out_tokens']
        
        # ── 상단 KPI 카드 4개 ──
        total_calls = len(df)
        total_cost = df['cost_usd'].sum()
        total_tokens = df['total_tokens'].sum()
        unique_users = df['email'].nunique()
        
        # 이번 달 필터
        current_month_mask = (df['ts'].dt.month == date.today().month) & (df['ts'].dt.year == date.today().year)
        month_cost = df[current_month_mask]['cost_usd'].sum()
        month_calls = current_month_mask.sum()
        
        # 오늘 필터
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
        
        # ── 필터 ──
        fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
        with fcol1:
            period = st.selectbox("📅 기간", ["전체 기간", "오늘", "최근 7일", "최근 30일", "이번 달"], index=0)
        with fcol2:
            user_filter = st.selectbox("👤 사용자 필터", ["전체"] + sorted(df['email'].unique().tolist()))
        with fcol3:
            st.write("")  # 맞춤
            refresh = st.button("🔄 새로고침", use_container_width=True)
            if refresh:
                st.session_state["user_db_cache"] = load_db()
                st.rerun()
        
        # ── 필터 적용 ──
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
            
            # ── 1. 사용자별 랭킹 테이블 ──
            st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">🏆 사용자별 사용량 순위 (비용 기준)</div>', unsafe_allow_html=True)
            
            user_agg = filtered.groupby('email').agg(
                호출수=('ts', 'count'),
                입력토큰=('in_tokens', 'sum'),
                출력토큰=('out_tokens', 'sum'),
                총토큰=('total_tokens', 'sum'),
                비용USD=('cost_usd', 'sum'),
                마지막사용=('ts', 'max')
            ).reset_index().sort_values('비용USD', ascending=False)
            
            user_agg['비용원'] = (user_agg['비용USD'] * 1400).astype(int)
            user_agg['마지막사용'] = user_agg['마지막사용'].dt.strftime('%Y-%m-%d %H:%M')
            user_agg.columns = ['이메일', '호출수', '입력토큰', '출력토큰', '총토큰', '비용($)', '마지막사용', '비용(₩)']
            
            # 순위 추가
            user_agg.insert(0, '순위', range(1, len(user_agg) + 1))
            # 표시 순서: 순위, 이메일, 호출수, 총토큰, 비용($), 비용(₩), 마지막사용
            display_agg = user_agg[['순위', '이메일', '호출수', '입력토큰', '출력토큰', '총토큰', '비용($)', '비용(₩)', '마지막사용']].copy()
            display_agg['비용($)'] = display_agg['비용($)'].apply(lambda x: f"${x:.4f}")
            display_agg['비용(₩)'] = display_agg['비용(₩)'].apply(lambda x: f"₩{x:,}")
            display_agg['입력토큰'] = display_agg['입력토큰'].apply(lambda x: f"{x:,}")
            display_agg['출력토큰'] = display_agg['출력토큰'].apply(lambda x: f"{x:,}")
            display_agg['총토큰'] = display_agg['총토큰'].apply(lambda x: f"{x:,}")
            
            st.dataframe(display_agg, use_container_width=True, hide_index=True)
            
            # ── 2. 기능별(Step별) 사용 분포 ──
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
            
            # ── 모델별 사용 분포 (여러 모델 사용 시에만) ──
            if 'model' in filtered.columns and filtered['model'].nunique() > 1:
                st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">🤖 모델별 사용 비율</div>', unsafe_allow_html=True)
                _model_short = {
                    "claude-opus-4-7": "👑 Opus 4.7",
                    "claude-opus-4-6": "👑 Opus 4.6",
                    "claude-sonnet-4-6": "⭐ Sonnet 4.6",
                    "claude-haiku-4-5-20251001": "⚡ Haiku 4.5",
                }
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
            
            # ── 3. 일별 추이 ──
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
            
            # ── 4. 시간대별 히트맵 (요일 × 시간) ──
            st.markdown('<div style="font-size:14px;font-weight:700;color:#0b1f52;margin:18px 0 8px;">🕐 시간대별 사용 패턴 (요일 × 시)</div>', unsafe_allow_html=True)
            
            # 요일을 한글로 매핑하고 순서 고정
            weekday_map = {'Monday': '월', 'Tuesday': '화', 'Wednesday': '수', 'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'}
            filtered_copy = filtered.copy()
            filtered_copy['요일'] = filtered_copy['weekday'].map(weekday_map)
            
            heatmap = filtered_copy.groupby(['요일', 'hour']).size().unstack(fill_value=0)
            # 요일 순서 고정
            weekday_order = ['월', '화', '수', '목', '금', '토', '일']
            heatmap = heatmap.reindex([w for w in weekday_order if w in heatmap.index])
            # 시간대 0~23 전부 채우기
            for h in range(24):
                if h not in heatmap.columns:
                    heatmap[h] = 0
            heatmap = heatmap[sorted(heatmap.columns)]
            
            if not heatmap.empty:
                st.dataframe(
                    heatmap.style.background_gradient(cmap='YlOrRd', axis=None).format("{:.0f}"),
                    use_container_width=True
                )
                st.caption("💡 색이 진할수록 해당 시간대에 많이 사용됨 (숫자 = 호출 횟수)")
            
            # ── 5. 상세 로그 ──
            with st.expander(f"🔍 상세 로그 보기 (총 {len(filtered)}건)", expanded=False):
                detail = filtered.sort_values('ts', ascending=False).copy()
                detail['시각'] = detail['ts'].dt.strftime('%Y-%m-%d %H:%M:%S')
                detail['비용($)'] = detail['cost_usd'].apply(lambda x: f"${x:.5f}")
                # 모델명을 읽기 쉽게 축약
                _model_short = {
                    "claude-opus-4-7": "👑 Opus 4.7",
                    "claude-opus-4-6": "👑 Opus 4.6",
                    "claude-sonnet-4-6": "⭐ Sonnet 4.6",
                    "claude-haiku-4-5-20251001": "⚡ Haiku 4.5",
                }
                detail['모델'] = detail['model'].apply(lambda x: _model_short.get(x, x))
                detail_display = detail[['시각', 'email', 'step', '모델', 'in_tokens', 'out_tokens', '비용($)']].copy()
                detail_display.columns = ['시각', '이메일', '기능', '모델', '입력토큰', '출력토큰', '비용($)']
                st.dataframe(detail_display, use_container_width=True, hide_index=True)
            
            # ── 6. CSV 다운로드 ──
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                csv_summary = user_agg.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 사용자별 요약 CSV",
                    csv_summary,
                    file_name=f"사용량요약_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with dl_col2:
                csv_detail = filtered[['ts', 'email', 'step', 'in_tokens', 'out_tokens', 'cost_usd', 'model']].to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 상세 로그 CSV",
                    csv_detail,
                    file_name=f"상세로그_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # ── 7. 로그 관리 (위험) ──
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
    
    # 대시보드 모드에서는 아래 Step 1/2/3을 숨김
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
        # Step 3에서 사용하기 위해 세션에 저장 (PDF는 바이트, 이미지는 Pillow 객체)
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
        # 🔥 버튼 클릭 즉시 피드백 표시 (디버깅용)
        st.info(f"🔄 버튼 감지됨 · 모델: `{target_model_name}` · 업종: {biz_type}")
        
        if current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 한도 초과")
        elif st.session_state.daily_api_count >= DAILY_API_LIMIT:
            st.error("🚫 오늘 API 한도를 모두 사용했습니다.")
        else:
            with st.spinner(f'AI 분석 중... ({target_model_name})'):
                prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.
[{biz_type}] 분야 기업에 대해 벤처인증에 적합한 기술 주제 3개를 추천하세요.
각 주제: ① 기술명 ② 추천 사유 ③ 벤처인증 적합도
{f'추가: {user_guide_rec}' if user_guide_rec else ''}"""
                
                max_retries = 2
                last_error = None
                for attempt in range(max_retries):
                    try:
                        result_text, in_tok, out_tok = claude_generate(prompt, analysis_content, max_tokens=2048)
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
        st.markdown(f'<div class="ai-result"><b>💡 AI 추천 기술 주제</b><br><br>{st.session_state.suggestions.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="sec-title"><h3>📑 Step 2 · 마스터 리포트 생성</h3></div>', unsafe_allow_html=True)
    selected_topic = st.text_input("확정 기술명", placeholder="예: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술", key=f"topic_{st.session_state.uploader_key}")
    # Step 3에서 참조하기 위해 세션에 저장
    if selected_topic:
        st.session_state['step2_topic'] = selected_topic
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
                        # 마스터 리포트는 긴 출력 필요 → max_tokens 8192
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
# 🎯 Step 3: 드래그 크롭 방식 — 입력란 영역 선택 → 정확한 문구 생성
# =====================================================================
st.divider()
st.markdown('<div class="sec-title"><h3>🎯 Step 3 · 영역 선택 자동 작성 (드래그 크롭 방식)</h3></div>', unsafe_allow_html=True)

st.info("""
**[사용법 — 초정확 영역 선택 방식]**
1. **'🔴 화면 공유 시작'** 버튼 → 벤처인증 사이트 창/탭 선택 → 공유 시작
2. 아래 **미리보기 화면**에서 작성하려는 **입력란 위에 마우스로 드래그**하여 노란 사각형을 그리세요.
3. **'🔍 이 영역 분석'** 버튼을 누르면 해당 영역의 라벨/질문을 파악하고 **전문 문구**를 생성합니다.
4. 다른 입력란으로 이동하려면 **다시 드래그**해서 영역을 새로 지정하세요 (자동 재분석 아님).
5. 스크롤은 벤처인증 사이트에서 자유롭게 하세요. 화면이 바뀌면 미리보기도 자동으로 따라갑니다.

💡 **장점:** 전체 화면이 아닌 **선택 영역만** 전송하므로 API 비용이 약 **1/5~1/10** 로 절감되고, AI가 엉뚱한 입력란을 잡을 일이 없습니다.
""")

# ── 드래그 크롭 컴포넌트 ──
scan_component_html = """
<div id="scan-root" style="font-family: 'Noto Sans KR', sans-serif;">
    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap;">
        <button id="startBtn" style="
            padding: 12px 20px;
            background: linear-gradient(135deg, #d4af37 0%, #b8952e 100%);
            color: #0b1f52;
            font-weight: 700;
            font-size: 14px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            box-shadow: 0px 4px 10px rgba(212,175,55,0.3);
        ">🔴 화면 공유 시작</button>
        
        <button id="analyzeBtn" disabled style="
            padding: 12px 20px;
            background: #e5e7eb;
            color: #6b7280;
            font-weight: 700;
            font-size: 14px;
            border: none;
            border-radius: 10px;
            cursor: not-allowed;
        ">🔍 이 영역 분석</button>
        
        <button id="stopBtn" disabled style="
            padding: 12px 20px;
            background: #e5e7eb;
            color: #6b7280;
            font-weight: 700;
            font-size: 14px;
            border: none;
            border-radius: 10px;
            cursor: not-allowed;
        ">⏹ 중지</button>
        
        <div id="status" style="
            font-size: 13px;
            color: #6b7280;
            padding: 8px 14px;
            background: #f3f4f6;
            border-radius: 8px;
            font-weight: 500;
            flex: 1;
            min-width: 200px;
        ">⚪ 대기 중 — 화면 공유를 시작하세요</div>
    </div>
    
    <div id="preview-box" style="display: none; margin-top: 10px; position: relative;">
        <div id="canvas-wrap" style="position: relative; display: inline-block; width: 100%; border-radius: 10px; overflow: hidden; border: 2px solid #d4af37; background: #000;">
            <video id="video" autoplay playsinline style="display:none;"></video>
            <canvas id="liveCanvas" style="display: block; width: 100%; height: auto; cursor: crosshair;"></canvas>
            <div id="selection-box" style="
                display: none;
                position: absolute;
                border: 3px dashed #d4af37;
                background: rgba(212, 175, 55, 0.15);
                pointer-events: none;
                box-shadow: 0 0 0 9999px rgba(0,0,0,0.35);
            "></div>
            <div id="coord-label" style="
                display: none;
                position: absolute;
                background: #0b1f52;
                color: #d4af37;
                font-size: 11px;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 4px;
                pointer-events: none;
                z-index: 10;
            "></div>
        </div>
        <div style="font-size: 11px; color: #9ca3af; margin-top: 6px;">
            👆 위 화면에서 <b style="color:#d4af37;">작성할 입력란을 드래그</b>로 선택하세요. 선택 후 <b>[🔍 이 영역 분석]</b> 버튼을 누르면 분석됩니다.
        </div>
    </div>
</div>

<script>
(function() {
    const startBtn = document.getElementById('startBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const stopBtn = document.getElementById('stopBtn');
    const status = document.getElementById('status');
    const previewBox = document.getElementById('preview-box');
    const video = document.getElementById('video');
    const liveCanvas = document.getElementById('liveCanvas');
    const selectionBox = document.getElementById('selection-box');
    const coordLabel = document.getElementById('coord-label');
    const canvasWrap = document.getElementById('canvas-wrap');
    
    let stream = null;
    let drawLoopId = null;
    let scanCount = 0;
    
    // 드래그 선택 상태
    let isDrawing = false;
    let startX = 0, startY = 0;
    let currentRect = null;  // {x, y, w, h} in canvas pixel coordinates
    
    function setStatus(text, type) {
        status.innerHTML = text;
        const colors = {
            ready: ['#f3f4f6', '#6b7280'],
            live:  ['#d1fae5', '#065f46'],
            warn:  ['#fef3c7', '#92400e'],
            err:   ['#fee2e2', '#991b1b'],
            sel:   ['#fef9c3', '#854d0e']
        };
        const [bg, col] = colors[type] || colors.ready;
        status.style.background = bg;
        status.style.color = col;
    }
    
    function enableAnalyzeBtn(enabled) {
        analyzeBtn.disabled = !enabled;
        if (enabled) {
            analyzeBtn.style.background = 'linear-gradient(135deg, #d4af37 0%, #b8952e 100%)';
            analyzeBtn.style.color = '#0b1f52';
            analyzeBtn.style.cursor = 'pointer';
            analyzeBtn.style.boxShadow = '0px 4px 10px rgba(212,175,55,0.3)';
        } else {
            analyzeBtn.style.background = '#e5e7eb';
            analyzeBtn.style.color = '#6b7280';
            analyzeBtn.style.cursor = 'not-allowed';
            analyzeBtn.style.boxShadow = 'none';
        }
    }
    
    // 실시간 비디오 → 캔버스 렌더링 (드래그 조작을 위해)
    function drawLoop() {
        if (!stream || !video.videoWidth) {
            drawLoopId = requestAnimationFrame(drawLoop);
            return;
        }
        // 캔버스 크기를 비디오 해상도에 맞춤 (한번만)
        if (liveCanvas.width !== video.videoWidth) {
            liveCanvas.width = video.videoWidth;
            liveCanvas.height = video.videoHeight;
        }
        const ctx = liveCanvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        drawLoopId = requestAnimationFrame(drawLoop);
    }
    
    // 화면 좌표 → 캔버스 픽셀 좌표 변환
    function toCanvasCoords(clientX, clientY) {
        const rect = liveCanvas.getBoundingClientRect();
        const scaleX = liveCanvas.width / rect.width;
        const scaleY = liveCanvas.height / rect.height;
        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    }
    
    // 드래그 선택 UI 업데이트
    function updateSelectionBox(cssX1, cssY1, cssX2, cssY2) {
        const x = Math.min(cssX1, cssX2);
        const y = Math.min(cssY1, cssY2);
        const w = Math.abs(cssX2 - cssX1);
        const h = Math.abs(cssY2 - cssY1);
        selectionBox.style.display = 'block';
        selectionBox.style.left = x + 'px';
        selectionBox.style.top = y + 'px';
        selectionBox.style.width = w + 'px';
        selectionBox.style.height = h + 'px';
        
        coordLabel.style.display = 'block';
        coordLabel.style.left = x + 'px';
        coordLabel.style.top = (y - 22) + 'px';
        coordLabel.textContent = `${Math.round(w)} × ${Math.round(h)} px`;
    }
    
    // 마우스 이벤트 (드래그 선택)
    liveCanvas.addEventListener('mousedown', (e) => {
        if (!stream) return;
        isDrawing = true;
        const wrapRect = canvasWrap.getBoundingClientRect();
        startX = e.clientX - wrapRect.left;
        startY = e.clientY - wrapRect.top;
        updateSelectionBox(startX, startY, startX, startY);
        enableAnalyzeBtn(false);
    });
    
    liveCanvas.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        const wrapRect = canvasWrap.getBoundingClientRect();
        const curX = e.clientX - wrapRect.left;
        const curY = e.clientY - wrapRect.top;
        updateSelectionBox(startX, startY, curX, curY);
    });
    
    liveCanvas.addEventListener('mouseup', (e) => {
        if (!isDrawing) return;
        isDrawing = false;
        const wrapRect = canvasWrap.getBoundingClientRect();
        const endX = e.clientX - wrapRect.left;
        const endY = e.clientY - wrapRect.top;
        
        // 너무 작으면 무시
        if (Math.abs(endX - startX) < 15 || Math.abs(endY - startY) < 15) {
            selectionBox.style.display = 'none';
            coordLabel.style.display = 'none';
            currentRect = null;
            enableAnalyzeBtn(false);
            setStatus('⚠️ 선택 영역이 너무 작습니다. 더 크게 드래그하세요.', 'warn');
            return;
        }
        
        // CSS 좌표 → 캔버스 픽셀 좌표 변환
        const rect1 = toCanvasCoords(e.clientX - (endX - startX), e.clientY - (endY - startY));
        const rect2 = toCanvasCoords(e.clientX, e.clientY);
        currentRect = {
            x: Math.min(rect1.x, rect2.x),
            y: Math.min(rect1.y, rect2.y),
            w: Math.abs(rect2.x - rect1.x),
            h: Math.abs(rect2.y - rect1.y)
        };
        enableAnalyzeBtn(true);
        setStatus(`✅ 영역 선택 완료 (${Math.round(currentRect.w)}×${Math.round(currentRect.h)}px) — [🔍 이 영역 분석] 버튼을 누르세요`, 'sel');
    });
    
    liveCanvas.addEventListener('mouseleave', () => {
        if (isDrawing) isDrawing = false;
    });
    
    // 분석 버튼 — 선택 영역만 크롭해서 전송
    analyzeBtn.onclick = () => {
        if (!currentRect || !stream) return;
        
        // 오프스크린 캔버스로 크롭
        const cropCanvas = document.createElement('canvas');
        cropCanvas.width = Math.round(currentRect.w);
        cropCanvas.height = Math.round(currentRect.h);
        const cropCtx = cropCanvas.getContext('2d');
        cropCtx.drawImage(
            liveCanvas,
            Math.round(currentRect.x), Math.round(currentRect.y),
            Math.round(currentRect.w), Math.round(currentRect.h),
            0, 0,
            Math.round(currentRect.w), Math.round(currentRect.h)
        );
        
        const imageData = cropCanvas.toDataURL('image/jpeg', 0.85);
        scanCount++;
        
        setStatus(`🟢 스캔 #${scanCount} 전송 중... (${Math.round(currentRect.w)}×${Math.round(currentRect.h)}px)`, 'live');
        
        // Streamlit으로 전송
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: { image: imageData, timestamp: Date.now(), count: scanCount }
        }, '*');
        
        // 전송 후엔 중복 전송 방지를 위해 분석 버튼 잠시 비활성화
        enableAnalyzeBtn(false);
        setTimeout(() => {
            if (currentRect) enableAnalyzeBtn(true);
        }, 3000);
    };
    
    startBtn.onclick = async () => {
        try {
            stream = await navigator.mediaDevices.getDisplayMedia({
                video: { frameRate: 15 },
                audio: false
            });
            video.srcObject = stream;
            previewBox.style.display = 'block';
            
            startBtn.disabled = true;
            startBtn.style.background = '#9ca3af';
            startBtn.style.cursor = 'not-allowed';
            startBtn.style.boxShadow = 'none';
            
            stopBtn.disabled = false;
            stopBtn.style.background = '#dc2626';
            stopBtn.style.color = 'white';
            stopBtn.style.cursor = 'pointer';
            
            setStatus('🟢 공유 중 — 미리보기에서 입력란을 드래그로 선택하세요', 'live');
            
            // 브라우저에서 사용자가 직접 공유 중지 시
            stream.getVideoTracks()[0].onended = () => { stopScan(); };
            
            // 렌더링 루프 시작 (비디오 → 캔버스)
            drawLoop();
            
        } catch (err) {
            setStatus('❌ 화면 공유 권한 거부 또는 취소됨', 'err');
            console.error(err);
        }
    };
    
    function stopScan() {
        if (drawLoopId) cancelAnimationFrame(drawLoopId);
        if (stream) stream.getTracks().forEach(t => t.stop());
        stream = null;
        drawLoopId = null;
        previewBox.style.display = 'none';
        selectionBox.style.display = 'none';
        coordLabel.style.display = 'none';
        currentRect = null;
        
        startBtn.disabled = false;
        startBtn.style.background = 'linear-gradient(135deg, #d4af37 0%, #b8952e 100%)';
        startBtn.style.cursor = 'pointer';
        startBtn.style.boxShadow = '0px 4px 10px rgba(212,175,55,0.3)';
        
        enableAnalyzeBtn(false);
        
        stopBtn.disabled = true;
        stopBtn.style.background = '#e5e7eb';
        stopBtn.style.color = '#6b7280';
        stopBtn.style.cursor = 'not-allowed';
        
        setStatus(`⚪ 중지됨 (총 ${scanCount}회 분석)`, 'ready');
    }
    
    stopBtn.onclick = stopScan;
})();
</script>
"""

# 컴포넌트 실행 (높이 넉넉히 — 미리보기 영역 고려)
captured_frame = components.html(scan_component_html, height=600)

# =====================================================================
# 🧠 캡처된 크롭 영역 분석 로직
# =====================================================================
frame_data = None
if captured_frame:
    if isinstance(captured_frame, dict) and 'image' in captured_frame:
        frame_data = captured_frame
    elif isinstance(captured_frame, str) and captured_frame.startswith('data:image'):
        frame_data = {'image': captured_frame, 'timestamp': 0, 'count': 0}

# 마지막 처리한 timestamp 추적 (중복 처리 방지)
if 'last_processed_ts' not in st.session_state:
    st.session_state.last_processed_ts = 0

if frame_data and frame_data.get('timestamp', 0) > st.session_state.last_processed_ts:
    st.session_state.last_processed_ts = frame_data['timestamp']
    
    # API 한도 체크
    if current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
        st.error("월간 한도 초과")
    elif st.session_state.daily_api_count >= DAILY_API_LIMIT:
        st.error("🚫 오늘 API 한도 초과")
    else:
        try:
            header, encoded = frame_data['image'].split(",", 1)
            image_bytes = base64.b64decode(encoded)
            crop_img = Image.open(io.BytesIO(image_bytes))
            
            # 기업 컨텍스트 구성
            company_topic = st.session_state.get('step2_topic', '').strip()
            context_str = f"확정 기술명: {company_topic}" if company_topic else "(기술명 미입력 — 화면에서 유추)"
            
            # 크롭 영역 전용 프롬프트 (전체 페이지 아님)
            scan_prompt = f"""당신은 20년 경력의 중소기업 벤처인증 전문 컨설턴트입니다.

[기업 컨텍스트]
{context_str}

[작업]
제공된 이미지는 사용자가 벤처인증/R&D/정책자금 신청 포털 화면에서 **마우스로 드래그하여 직접 선택한 특정 입력란 영역**입니다.
이미지에는 보통 **1개의 입력란과 그 라벨(제목/질문)**이 포함되어 있습니다.

1. 이미지에서 입력란의 **라벨(제목, 질문 문구)**을 정확히 찾아내세요.
2. 해당 입력란에 들어갈 **전문적인 벤처인증 문구**를 작성하세요.

[출력 규칙]
- 반드시 아래 JSON 형식으로만 출력 (마크다운 코드펜스 금지, 설명 금지)
- content는 300~500자 분량의 전문 서술형
- 지어낸 숫자/수치 금지, 일반적 업계 표현 사용
- 인사말/안내멘트 금지, 즉시 붙여넣기 가능한 본문만
- 라벨이 불명확하면 detected_page에 "라벨 불명확 — 재선택 권장"으로 표기

[JSON 스키마]
{{
  "detected_page": "파악한 입력란 라벨 (예: 기술의 독창성 서술)",
  "fields": [
    {{"label": "입력란 제목", "content": "작성 문구"}}
  ]
}}
"""
            
            # Step 1 분석자료 (사업자등록증)가 있으면 함께 전달 (컨텍스트 강화)
            analysis_extra = None
            if st.session_state.get('step1_analysis_type') == 'pdf':
                analysis_extra = {"mime_type": "application/pdf", "data": st.session_state['step1_analysis_data']}
            elif st.session_state.get('step1_analysis_type') == 'image':
                analysis_extra = Image.open(io.BytesIO(st.session_state['step1_analysis_data']))
            
            with st.spinner(f"🤖 영역 분석 중... (#{frame_data.get('count', '?')})"):
                raw_text = None
                in_tok = 0
                out_tok = 0
                try:
                    raw_text, in_tok, out_tok = claude_generate(scan_prompt, analysis_extra, crop_img, max_tokens=2048)
                except anthropic.RateLimitError:
                    st.warning("⏳ Claude API Rate Limit. 잠시 후 다시 분석 버튼을 누르세요.")
                except anthropic.APIStatusError as e:
                    if e.status_code == 429:
                        st.session_state.daily_api_count = DAILY_API_LIMIT
                        st.error("🚫 크레딧 부족 또는 한도 초과.")
                    else:
                        st.error(f"⚠️ API 오류 ({e.status_code}): {e.message}")
                
                if raw_text:
                    # JSON 파싱 (마크다운 코드펜스 제거)
                    clean_text = raw_text.replace('```json', '').replace('```', '').strip()
                    try:
                        parsed = json.loads(clean_text)
                        result_entry = {
                            'timestamp': frame_data['timestamp'],
                            'scan_num': frame_data.get('count', 0),
                            'detected_page': parsed.get('detected_page', '알 수 없음'),
                            'fields': parsed.get('fields', []),
                            'time_str': datetime.now().strftime('%H:%M:%S'),
                            'crop_bytes': image_bytes  # 선택 영역 미리보기용
                        }
                        st.session_state.scan_results.insert(0, result_entry)
                        st.session_state.scan_results = st.session_state.scan_results[:5]
                        
                        st.session_state.daily_api_count += 1
                        user_db["users"][current_user_email]["usage_count"] += 1
                        log_usage(user_db, current_user_email, "Step 3 (영역 스캔)", in_tok, out_tok, target_model_name)
                        save_db(user_db)
                    except json.JSONDecodeError:
                        st.warning(f"⚠️ AI 응답을 JSON으로 파싱하지 못했습니다. 원문: {raw_text[:300]}...")
        except Exception as e:
            st.error(f"⚠️ 분석 오류: {e}")

# =====================================================================
# 📋 영역 분석 결과 (카드 + 선택 영역 미리보기)
# =====================================================================
if st.session_state.scan_results:
    st.divider()
    
    latest = st.session_state.scan_results[0]
    
    # ── 헤더 정보 ──
    st.markdown(f'''
    <div style="background: linear-gradient(135deg, #0b1f52, #1a3a7a); border-radius: 12px; padding: 18px 22px; margin-bottom: 16px; border-left: 5px solid #d4af37;">
        <div style="color: #d4af37; font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 6px;">LATEST ANALYSIS · {latest["time_str"]}</div>
        <div style="color: white; font-size: 18px; font-weight: 700;">📄 감지된 입력란: {latest["detected_page"]}</div>
        <div style="color: rgba(255,255,255,0.6); font-size: 12px; margin-top: 4px;">{len(latest["fields"])}개 문구 생성 완료</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # ── 선택한 영역 미리보기 (접기 가능) ──
    if latest.get('crop_bytes'):
        with st.expander("🖼️ 이번에 분석한 영역 보기", expanded=False):
            st.image(latest['crop_bytes'], caption=f"선택한 입력란 영역 (#{latest['scan_num']})", use_column_width=True)
    
    if not latest['fields']:
        st.warning("⚠️ 이 영역에서는 벤처인증 입력란을 감지하지 못했습니다. 입력란과 라벨이 함께 보이도록 더 크게 드래그해보세요.")
    else:
        # ── 표 형태 요약 ──
        with st.expander("📊 표 형태로 한눈에 보기", expanded=False):
            tbl_rows = [{'입력란': f['label'], '작성 문구 미리보기': (f['content'][:80] + '...') if len(f['content']) > 80 else f['content']} for f in latest['fields']]
            st.dataframe(pd.DataFrame(tbl_rows), use_container_width=True, hide_index=True)
        
        # ── 카드 형태 (각 입력란별 복사 버튼) ──
        st.markdown('<div style="font-size: 14px; font-weight: 700; color: #0b1f52; margin: 12px 0 8px;">📝 생성된 문구 (우측 상단 [복사] 아이콘 클릭)</div>', unsafe_allow_html=True)
        
        for idx, field in enumerate(latest['fields']):
            st.markdown(f'''
            <div style="background: white; border: 1px solid #e5e7eb; border-left: 4px solid #d4af37; border-radius: 10px; padding: 12px 16px; margin-top: 10px; margin-bottom: -5px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: #0b1f52; color: #d4af37; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 5px;">#{idx+1}</span>
                    <span style="font-weight: 700; color: #0b1f52; font-size: 14px;">{field["label"]}</span>
                    <span style="font-size: 11px; color: #9ca3af; margin-left: auto;">{len(field["content"])}자</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            # st.code 는 우측 상단에 복사버튼이 기본 내장됨
            st.code(field['content'], language="text")
    
    # ── 이전 분석 이력 ──
    if len(st.session_state.scan_results) > 1:
        with st.expander(f"🕒 이전 분석 이력 ({len(st.session_state.scan_results)-1}개)", expanded=False):
            for old in st.session_state.scan_results[1:]:
                st.markdown(f"**#{old['scan_num']} · {old['time_str']} · {old['detected_page']}** — {len(old['fields'])}개 문구")
                for f in old['fields']:
                    st.caption(f"  • {f['label']}")

st.markdown('<div style="text-align:center;padding:28px 0 10px;color:#9ca3af;font-size:11px;">© 2026 중소기업경영지원단 · 벤처인증 AI 마스터 컨설턴트</div>', unsafe_allow_html=True)
