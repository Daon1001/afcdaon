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

# 모델 선택 (우선순위: 품질 vs 비용 균형)
# claude-sonnet-4-6: 추천 (품질 뛰어남, 비용 합리적, 비전 지원)
# claude-opus-4-7: 최고 품질 (비용 5배), claude-haiku-4-5: 최저 비용(품질 낮음)
target_model_name = st.secrets.get("claude_model", "claude-sonnet-4-6")
model_name = target_model_name  # 호환성을 위해 기존 변수명 유지
st.sidebar.caption(f"🤖 엔진: `{target_model_name}`")


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
            st.session_state['admin_dashboard_mode'] = False
            st.rerun()
    with bcol2:
        dash_label = "📊 컨설팅 화면으로" if st.session_state.get('admin_dashboard_mode') else "📈 관리자 대시보드"
        if st.button(dash_label, use_container_width=True, type="primary" if not st.session_state.get('admin_dashboard_mode') else "secondary"):
            st.session_state['admin_dashboard_mode'] = not st.session_state.get('admin_dashboard_mode', False)
            st.rerun()
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
if current_user.get("is_admin") and st.session_state.get('admin_dashboard_mode'):
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
            c1, c2 = st
