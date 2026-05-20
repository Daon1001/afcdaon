import streamlit as st
import anthropic
import json
import os
import io
import requests
import base64
import pandas as pd
from datetime import datetime, date

# ── 페이지 설정 ──
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", page_icon="🏛️", layout="wide")

# 💰 가격 정보 (2026년 5월 기준)
MODEL_PRICES = {
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
    "claude-sonnet-4-6":         {"input": 3.0, "output": 15.0},
    "claude-opus-4-7":           {"input": 5.0, "output": 25.0},
}
USD_TO_KRW = 1380
ADMIN_EMAIL = "incheon00@gmail.com"
MODEL_OPTIONS = {
    "⚡ Haiku 4.5 (빠름·저렴)": "claude-haiku-4-5-20251001",
    "⭐ Sonnet 4.6 (균형·기본)": "claude-sonnet-4-6",
    "👑 Opus 4.7 (최고품질·느림)": "claude-opus-4-7",
}

# =========== Gist DB ===========
DB_FILE = "user_database.json"
def _gist_headers():
    token = st.secrets.get("github_token", "")
    if not token: return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
def _gist_id(): return st.secrets.get("gist_id", "")
def _gist_filename(): return st.secrets.get("gist_filename", "venture_users.json")

def load_db():
    headers = _gist_headers(); gist_id = _gist_id()
    if headers and gist_id:
        try:
            resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json(); fn = _gist_filename()
                if fn in data.get("files", {}):
                    db = json.loads(data["files"][fn]["content"])
                    if "usage_logs" not in db: db["usage_logs"] = []
                    if "users" not in db: db["users"] = {}
                    return db
        except: pass
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {
        "users": {ADMIN_EMAIL: {"approved": True, "is_admin": True,
                                "created_at": datetime.now().isoformat(),
                                "approved_at": datetime.now().isoformat()}},
        "usage_logs": []
    }

def save_db(db):
    db["last_updated"] = datetime.now().isoformat()
    headers = _gist_headers(); gist_id = _gist_id()
    if headers and gist_id:
        payload = {"files": {_gist_filename(): {"content": json.dumps(db, ensure_ascii=False, indent=2)}}}
        try: requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
        except: pass
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except: pass
    st.session_state["user_db_cache"] = db

def add_usage_log(email, model_id, input_tokens, output_tokens, action_type):
    db = st.session_state.get("user_db_cache", load_db())
    if "usage_logs" not in db: db["usage_logs"] = []
    price = MODEL_PRICES.get(model_id, {"input": 0, "output": 0})
    cost_usd = (input_tokens * price["input"] + output_tokens * price["output"]) / 1_000_000
    db["usage_logs"].append({
        "timestamp": datetime.now().isoformat(),
        "email": email, "model": model_id,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6), "action": action_type,
    })
    if len(db["usage_logs"]) > 5000:
        db["usage_logs"] = db["usage_logs"][-5000:]
    save_db(db)

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]

# =========== 이미지 ===========
def get_image_src(image_path, fallback_url):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = image_path.lower().split('.')[-1]
            mime = "png" if ext == "png" else "jpeg"
            return f"data:image/{mime};base64,{b64}"
        except: return fallback_url
    return fallback_url

LOGO_SRC = get_image_src("프로필이미지.jpg", "https://placehold.co/300x300/0A1628/C9A961?text=LOGO&font=roboto")
BANNER_SRC = get_image_src("배너광고1.jpg", "https://placehold.co/1330x120/0A1628/C9A961?text=%EB%B6%80%EC%9E%90%EB%93%A4%EC%9D%98+%EB%B9%84%EB%B0%80%EA%B8%88%EA%B3%A0&font=roboto")

# =========== HTML 생성 함수 ===========
def generate_branded_html(topic, sections):
    css = r"""
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&display=swap');
    @page { size: A4 portrait; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Pretendard Variable', Pretendard, 'Noto Sans KR', sans-serif; font-size: 14px; color: #2B2416; line-height: 1.7; background: #2B2416; display: flex; flex-direction: column; align-items: center; padding: 20px 0; letter-spacing: -0.2px; }
    .page { width: 210mm; min-height: 297mm; max-height: 297mm; background: linear-gradient(135deg, #FAF6EE 0%, #F5EDD9 100%); margin-bottom: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.35); position: relative; overflow: hidden; page-break-after: always; display: flex; flex-direction: column; }
    @media print { * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } body { background: white !important; padding: 0 !important; } .page { box-shadow: none !important; margin: 0 !important; background: linear-gradient(135deg, #FAF6EE, #F5EDD9) !important; } .cover-page { background: linear-gradient(135deg, #0A1628, #0F2847, #1B3A6B) !important; } .v-item { background: linear-gradient(135deg, #FFFBF0, #F9F1DC) !important; } }
    .cover-page { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%); color: white; }
    .cover-page .corner-deco { position: absolute; width: 60px; height: 60px; border: 2px solid rgba(201,169,97,0.6); }
    .cover-page .corner-tl { top: 30px; left: 30px; border-right: none; border-bottom: none; }
    .cover-page .corner-tr { top: 30px; right: 30px; border-left: none; border-bottom: none; }
    .cover-page .corner-bl { bottom: 30px; left: 30px; border-right: none; border-top: none; }
    .cover-page .corner-br { bottom: 30px; right: 30px; border-left: none; border-top: none; }
    .cover-inner { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40mm 20mm; }
    .cover-logo { width: 140px; height: 140px; border-radius: 50%; border: 3px solid #C9A961; object-fit: cover; background: white; margin-bottom: 30px; box-shadow: 0 8px 32px rgba(201,169,97,0.45); }
    .cover-brand { font-size: 64px; font-weight: 900; letter-spacing: 14px; background: linear-gradient(180deg, #F4D98A 0%, #C9A961 60%, #8B6F3E 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1; margin-bottom: 12px; text-indent: 14px; }
    .cover-subbrand { font-size: 14px; font-weight: 500; letter-spacing: 8px; color: rgba(244,217,138,0.85); text-transform: uppercase; margin-bottom: 28px; font-family: 'Cormorant Garamond', serif; font-style: italic; }
    .cover-divider { width: 100px; height: 2px; background: linear-gradient(90deg, transparent, #C9A961, #F4D98A, #C9A961, transparent); margin-bottom: 32px; }
    .cover-title { font-size: 32px; font-weight: 700; letter-spacing: 4px; color: white; margin-bottom: 60px; }
    .cover-topic-label { font-size: 11px; font-weight: 600; letter-spacing: 4px; color: #F4D98A; text-transform: uppercase; margin-bottom: 18px; }
    .cover-topic { font-size: 22px; font-weight: 500; color: rgba(255,255,255,0.94); max-width: 80%; text-align: center; padding: 20px 40px; border-top: 1px solid rgba(201,169,97,0.4); border-bottom: 1px solid rgba(201,169,97,0.4); }
    .cover-footer { padding: 18px 20mm; background: linear-gradient(90deg, #F4D98A, #C9A961, #F4D98A); color: #0A1628; font-size: 10px; text-align: center; letter-spacing: 2px; font-weight: 700; }
    .page-header { padding: 15mm 15mm 10mm; border-bottom: 1px solid rgba(201,169,97,0.35); display: flex; align-items: center; gap: 16px; background: linear-gradient(180deg, rgba(201,169,97,0.08) 0%, transparent 100%); }
    .header-logo { width: 44px; height: 44px; border-radius: 50%; border: 2px solid #C9A961; object-fit: cover; background: white; }
    .section-badge { background: linear-gradient(135deg, #8B6F3E 0%, #C9A961 50%, #8B6F3E 100%); color: white; padding: 5px 15px; border-radius: 20px; font-size: 10.5px; font-weight: 700; letter-spacing: 2px; }
    .page-title { font-size: 22px; font-weight: 800; color: #0F2847; flex: 1; }
    .page-body { flex: 1; padding: 12mm 15mm; font-size: 14px; line-height: 1.85; color: #3A2F1E; overflow: hidden; }
    .sub-title { font-size: 16px; font-weight: 800; color: #0F2847; margin: 22px 0 12px; padding: 6px 14px 6px 16px; border-left: 4px solid #C9A961; background: linear-gradient(90deg, rgba(201,169,97,0.12) 0%, transparent 80%); border-radius: 0 6px 6px 0; }
    .v-item { background: linear-gradient(135deg, #FFFBF0 0%, #F9F1DC 100%); border-left: 4px solid #C9A961; padding: 13px 20px; border-radius: 0 10px 10px 0; margin-bottom: 12px; display: flex; gap: 14px; }
    .v-item .v-mark { color: #8B6F3E; font-size: 20px; font-weight: 900; font-family: 'Cormorant Garamond', serif; }
    .v-item .v-content { color: #2B2416; font-size: 13.5px; font-weight: 500; }
    .v-item .v-content strong { color: #0F2847; font-weight: 800; background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%); padding: 0 2px; }
    .bullet-item { padding: 6px 0 6px 26px; position: relative; color: #3A2F1E; font-size: 13.5px; }
    .bullet-item::before { content: '◆'; color: #C9A961; font-size: 11px; position: absolute; left: 8px; top: 9px; }
    .bullet-item strong { color: #0F2847; font-weight: 700; background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%); padding: 0 2px; }
    .body-text { color: #3A2F1E; font-size: 13.5px; line-height: 1.8; margin-bottom: 10px; }
    .footer-banner { width: 100%; height: 28mm; object-fit: cover; border-top: 2px solid #C9A961; }
    .page-number { position: absolute; bottom: 32mm; right: 12mm; font-size: 10px; color: #8B6F3E; font-weight: 700; letter-spacing: 2px; font-family: 'Cormorant Garamond', serif; }
    """
    def render_body(text):
        parts = []
        for line in text.split('\n'):
            s = line.strip()
            if not s: continue
            if s.startswith('V ') or s.startswith('V\t'):
                c = s[2:].strip().replace('[', '<strong>[').replace(']', ']</strong>')
                parts.append(f'<div class="v-item"><span class="v-mark">V</span><span class="v-content">{c}</span></div>')
            elif s.startswith('- 신청기술'):
                parts.append(f'<div class="sub-title">{s.lstrip("-").strip()}</div>')
            elif s.startswith('• ') or s.startswith('- ') or s.startswith('* '):
                c = s.lstrip('•-* ').strip().replace('[', '<strong>[').replace(']', ']</strong>')
                parts.append(f'<div class="bullet-item">{c}</div>')
            elif len(s) >= 2 and s[0].isdigit() and s[1] == '.':
                parts.append(f'<div class="body-text">{s}</div>')
            else:
                parts.append(f'<div class="body-text">{s}</div>')
        return '\n'.join(parts)
    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>벤처인증 마스터 리포트 · {topic}</title><style>{css}</style></head><body>
<div class="page cover-page">
    <div class="corner-deco corner-tl"></div><div class="corner-deco corner-tr"></div><div class="corner-deco corner-bl"></div><div class="corner-deco corner-br"></div>
    <div class="cover-inner">
        <img src="{LOGO_SRC}" class="cover-logo" alt="로고">
        <div class="cover-brand">RSV</div>
        <div class="cover-subbrand">Rich Secret Vault · 부자들의 비밀금고</div>
        <div class="cover-divider"></div>
        <div class="cover-title">벤처인증 마스터 컨설팅 리포트</div>
        <div class="cover-topic-label">— Subject Technology —</div>
        <div class="cover-topic">{topic}</div>
    </div>
    <div class="cover-footer">중소기업경영지원단 · VENTURE CERTIFICATION · {datetime.now().strftime('%Y.%m.%d')}</div>
</div>"""
    n = 0
    for sec in sections:
        if not sec.strip(): continue
        lns = sec.split('\n', 1)
        title = lns[0].strip('[] #').strip()
        if not title: continue
        body = lns[1] if len(lns) > 1 else ""
        n += 1
        html += f"""<div class="page">
    <div class="page-header"><img src="{LOGO_SRC}" class="header-logo"><span class="section-badge">CHAPTER {n:02d}</span><div class="page-title">{title}</div></div>
    <div class="page-body">{render_body(body)}</div>
    <div class="page-number">— {n:02d} —</div>
    <img src="{BANNER_SRC}" class="footer-banner">
</div>"""
    return html + "</body></html>"

def get_sample_sections():
    return """### [1. 신청기술 요약 및 표준 양식]
- 신청기술명: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술
V 기존 시장에 [박스 과잉설계 문제]가 있으며, [경험 의존적 설계]로 어려움
V 당사에서 [FEA 기반 구조 최적화]로 해결, [설계 90% 단축]이라는 차이 보유
V 본 기술 목표는 [통합 자동 설계 시스템] 개발

### [2. 개발배경 및 원인분석]
• 국내 포장산업 약 40조원 규모, 경험 의존적 설계 관행
• 친환경 규제 강화로 재료 절감 요구 급증

### [3. 경쟁력 확보방안]
1. 독자적 AI 알고리즘 보유
2. 설계 리드타임 90% 단축
3. 해외 솔루션 대비 1/3 가격""".split('### ')

# =========== Claude API ===========
def claude_generate(prompt, model_id, max_tokens=8192, image_data=None, pdf_data=None,
                    user_email=None, action_type="generate"):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        blocks = []
        if pdf_data is not None:
            b64 = base64.standard_b64encode(pdf_data).decode("utf-8")
            blocks.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}})
        elif image_data is not None:
            b64 = base64.standard_b64encode(image_data).decode("utf-8")
            blocks.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}})
        blocks.append({"type": "text", "text": prompt})
        
        response = client.messages.create(model=model_id, max_tokens=max_tokens,
                                          messages=[{"role": "user", "content": blocks}])
        if user_email:
            add_usage_log(user_email, model_id, response.usage.input_tokens, response.usage.output_tokens, action_type)
        return {"ok": True, "text": response.content[0].text,
                "input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    except anthropic.RateLimitError as e:
        return {"ok": False, "error": f"Rate Limit 초과: {str(e)[:200]}"}
    except anthropic.APIStatusError as e:
        return {"ok": False, "error": f"API 오류 ({e.status_code}): {str(e.message)[:200]}"}
    except Exception as e:
        import traceback
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "trace": traceback.format_exc()}

# =========== UI 스타일 ===========
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    .stApp { background: #f0f2f5; font-family: 'Pretendard Variable', 'Noto Sans KR', sans-serif; }
    .dash-header { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%); color: white; padding: 30px 40px; border-radius: 16px; border-bottom: 4px solid #C9A961; margin-bottom: 28px; position: relative; overflow: hidden; }
    .dash-header::before { content: ''; position: absolute; top: -50%; right: -10%; width: 60%; height: 200%; background: radial-gradient(ellipse, rgba(201,169,97,0.15) 0%, transparent 60%); }
    .dash-header h1 { color: white !important; font-weight: 900 !important; margin: 0 !important; font-size: 26px !important; }
    .dash-header .brand-tag { display: inline-block; background: linear-gradient(180deg, #F4D98A, #C9A961, #8B6F3E); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; letter-spacing: 4px; font-size: 14px; margin-bottom: 4px; }
    .dash-header p { color: rgba(255,255,255,0.75); margin: 6px 0 0 !important; font-size: 13px; }
    .sec-title { background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; border: 1px solid #E2E8F0; border-left: 4px solid #C9A961; color: #0F2847; font-weight: 800; font-size: 16px; }
    .copy-label { font-weight: 800; color: #0F2847; margin: 18px 0 8px; padding-left: 10px; border-left: 3px solid #C9A961; font-size: 14px; }
    [data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, #C9A961 0%, #A37C3E 100%) !important; color: #0A1628 !important; font-weight: 800 !important; border: none !important; border-radius: 10px !important; }
    .rec-card { background: linear-gradient(135deg, #FCFDFE 0%, #F0F4F9 100%); border: 1px solid #D0D9E3; border-left: 4px solid #C9A961; border-radius: 10px; padding: 16px 18px; margin: 10px 0; }
    .rec-card-title { font-size: 15px; font-weight: 800; color: #0F2847; margin-bottom: 6px; }
    .rec-card-desc { font-size: 13px; color: #4A5568; line-height: 1.6; }
    section[data-testid="stSidebar"] { background: #0A1628 !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stButton > button { background: rgba(201,169,97,0.1) !important; border: 1px solid rgba(201,169,97,0.3) !important; color: #C9A961 !important; font-weight: 700 !important; }
    .admin-stat-card { background: white; border-radius: 12px; padding: 18px 22px; border: 1px solid rgba(201,169,97,0.3); border-top: 4px solid #C9A961; }
    .admin-stat-card .label { font-size: 11px; color: #8B6F3E; font-weight: 700; letter-spacing: 1px; margin-bottom: 6px; }
    .admin-stat-card .value { font-size: 24px; color: #0F2847; font-weight: 900; }
    .admin-stat-card .sub { font-size: 11px; color: #6B7280; margin-top: 4px; }
    .pending-user { background: #FFF8E7; border: 1px solid #F0B429; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# =========== 세션 ===========
if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = False
if 'show_signup' not in st.session_state: st.session_state.show_signup = False

# =========== 로그인 화면 ===========
if st.session_state.authenticated_user is None:
    st.markdown("""
    <div style="text-align:center; padding: 40px 20px 20px;">
        <div style="display:inline-block; background:linear-gradient(180deg,#F4D98A,#C9A961,#8B6F3E); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:#C9A961; font-size:48px; font-weight:900; letter-spacing:12px;">RSV</div>
        <div style="color:#999; letter-spacing:5px; font-size:12px; margin-bottom:8px;">RICH SECRET VAULT</div>
        <div style="color:#0F2847; font-size:22px; font-weight:700; letter-spacing:2px;">벤처인증 AI 마스터 컨설턴트</div>
    </div>
    """, unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if not st.session_state.show_signup:
            st.markdown("### 🔐 로그인")
            email = st.text_input("이메일", placeholder="example@gmail.com", key="login_email").strip().lower()
            lc1, lc2 = st.columns(2)
            with lc1:
                if st.button("로그인", type="primary", use_container_width=True):
                    if email in user_db["users"]:
                        if user_db["users"][email].get("approved"):
                            st.session_state.authenticated_user = email
                            st.rerun()
                        else:
                            st.error("⏳ 승인 대기 중입니다. 관리자(incheon00@gmail.com)에게 문의하세요.")
                    else:
                        st.error("❌ 등록되지 않은 이메일. '승인 신청' 버튼을 눌러주세요.")
            with lc2:
                if st.button("✋ 승인 신청 (신규)", use_container_width=True):
                    st.session_state.show_signup = True
                    st.rerun()
        else:
            st.markdown("### ✋ 신규 사용자 승인 신청")
            st.info("아래 정보를 입력하시면 관리자에게 승인 신청이 전달됩니다.")
            req_email = st.text_input("이메일", placeholder="example@gmail.com").strip().lower()
            req_name = st.text_input("이름", placeholder="홍길동")
            req_company = st.text_input("회사명", placeholder="(주)회사명")
            req_purpose = st.text_area("사용 목적", placeholder="예: 벤처인증 컨설팅 업무에 활용", height=80)
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("📨 승인 요청", type="primary", use_container_width=True):
                    if not req_email or "@" not in req_email:
                        st.error("올바른 이메일을 입력해주세요.")
                    elif req_email in user_db["users"]:
                        if user_db["users"][req_email].get("approved"):
                            st.warning("이미 승인된 이메일입니다.")
                        else:
                            st.info("이미 신청하셨습니다. 승인을 기다려주세요.")
                    else:
                        user_db["users"][req_email] = {
                            "approved": False, "is_admin": False,
                            "name": req_name, "company": req_company, "purpose": req_purpose,
                            "created_at": datetime.now().isoformat()
                        }
                        save_db(user_db)
                        st.success(f"✅ {req_email} 신청 완료! 관리자 승인 후 사용 가능합니다.")
            with sc2:
                if st.button("← 로그인 화면으로", use_container_width=True):
                    st.session_state.show_signup = False
                    st.rerun()
    st.stop()

# =========== 메인 ===========
current_user_data = user_db["users"].get(st.session_state.authenticated_user, {})
is_admin = current_user_data.get("is_admin", False)

hc1, hc2 = st.columns([5, 1])
with hc1:
    st.markdown("""<div class="dash-header">
        <div class="brand-tag">RICH SECRET VAULT</div>
        <h1>🏛️ 벤처인증 AI 마스터 컨설턴트</h1>
        <p>중소기업경영지원단 · 프리미엄 디자인 리포트 & 복사 통합 모드</p>
    </div>""", unsafe_allow_html=True)
with hc2:
    if is_admin:
        st.write(""); st.write("")
        if st.session_state.admin_mode:
            if st.button("🏠 일반 모드", use_container_width=True):
                st.session_state.admin_mode = False; st.rerun()
        else:
            if st.button("👑 관리자 모드", use_container_width=True, type="primary"):
                st.session_state.admin_mode = True; st.rerun()

# =========== 사이드바 ===========
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.authenticated_user}**")
    if is_admin:
        st.markdown("<div style='color:#F4D98A; font-size:11px; letter-spacing:2px;'>★ ADMIN</div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.session_state.admin_mode = False
        st.rerun()
    
    if not st.session_state.admin_mode:
        st.divider()
        st.markdown("### 🤖 AI 품질")
        selected_model_label = st.radio("모델 선택", options=list(MODEL_OPTIONS.keys()), index=1, label_visibility="collapsed")
        selected_model = MODEL_OPTIONS[selected_model_label]
        st.caption(f"`{selected_model}`")
        
        st.divider()
        st.markdown("### 🎨 미리보기")
        st.caption("API 호출 없이 디자인만 확인 (비용 0원)")
        if st.button("🧪 샘플 미리보기", use_container_width=True):
            st.session_state.sections = get_sample_sections()
            st.session_state.step2_topic = "데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술"
            st.rerun()
        
        # 본인 사용량
        my_logs = [l for l in user_db.get("usage_logs", []) if l["email"] == st.session_state.authenticated_user]
        if my_logs:
            st.divider()
            st.markdown("### 📊 내 사용량")
            my_cost = sum(l["cost_usd"] for l in my_logs)
            st.caption(f"누적 호출: **{len(my_logs)}회**")
            st.caption(f"누적 비용: **${my_cost:.4f}** (₩{my_cost*USD_TO_KRW:,.0f})")

# =========== 관리자 모드 ===========
if st.session_state.admin_mode and is_admin:
    st.markdown('<div class="sec-title">👑 관리자 대시보드</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 사용량 통계", "👥 사용자 관리", "✋ 승인 대기", "📜 상세 로그"])
    
    with tab1:
        logs = user_db.get("usage_logs", [])
        # 🛡️ 안전 필터: 필수 필드가 모두 있는 로그만 사용
        REQUIRED_FIELDS = ["timestamp", "email", "model", "input_tokens", "output_tokens", "cost_usd"]
        valid_logs = [l for l in logs if isinstance(l, dict) and all(k in l for k in REQUIRED_FIELDS)]
        
        if not valid_logs:
            if logs:
                st.warning(f"⚠️ 로그가 {len(logs)}건 있지만 형식이 맞지 않아 표시할 수 없습니다. 새 로그가 쌓이면 자동으로 표시됩니다.")
            else:
                st.info("아직 사용량 기록이 없습니다. API를 호출하면 여기에 표시됩니다.")
        else:
            df = pd.DataFrame(valid_logs)
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            
            if len(df) == 0:
                st.info("표시할 사용량 기록이 없습니다.")
            else:
                df['date'] = df['timestamp'].dt.date
                df['input_tokens'] = pd.to_numeric(df['input_tokens'], errors='coerce').fillna(0).astype(int)
                df['output_tokens'] = pd.to_numeric(df['output_tokens'], errors='coerce').fillna(0).astype(int)
                df['cost_usd'] = pd.to_numeric(df['cost_usd'], errors='coerce').fillna(0)
                
                st.markdown("#### 📈 전체 요약")
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1:
                    st.markdown(f'<div class="admin-stat-card"><div class="label">전체 호출</div><div class="value">{len(df):,}</div><div class="sub">건</div></div>', unsafe_allow_html=True)
                with sc2:
                    ti = int(df['input_tokens'].sum())
                    st.markdown(f'<div class="admin-stat-card"><div class="label">입력 토큰</div><div class="value">{ti:,}</div><div class="sub">tokens</div></div>', unsafe_allow_html=True)
                with sc3:
                    to = int(df['output_tokens'].sum())
                    st.markdown(f'<div class="admin-stat-card"><div class="label">출력 토큰</div><div class="value">{to:,}</div><div class="sub">tokens</div></div>', unsafe_allow_html=True)
                with sc4:
                    tc = float(df['cost_usd'].sum())
                    st.markdown(f'<div class="admin-stat-card"><div class="label">누적 비용</div><div class="value">${tc:.2f}</div><div class="sub">≈ ₩{tc*USD_TO_KRW:,.0f}</div></div>', unsafe_allow_html=True)
                
                st.divider()
                st.markdown("#### 👥 사용자별 비용 순위")
                us = df.groupby('email').agg(
                    호출수=('email', 'count'),
                    입력토큰=('input_tokens', 'sum'),
                    출력토큰=('output_tokens', 'sum'),
                    비용USD=('cost_usd', 'sum'),
                ).reset_index()
                us['비용원'] = (us['비용USD'] * USD_TO_KRW).round(0).astype(int)
                us = us.sort_values('비용USD', ascending=False)
                us['비용USD'] = us['비용USD'].round(4)
                st.dataframe(us, use_container_width=True, hide_index=True)
                
                st.divider()
                st.markdown("#### 📅 사용자별 일별 비용 추이")
                
                # 기간 선택
                period_col1, period_col2 = st.columns([1, 3])
                with period_col1:
                    days_back = st.selectbox("표시 기간", [7, 14, 30, 60, 90], index=2,
                                             format_func=lambda x: f"최근 {x}일")
                
                recent = df[df['timestamp'] >= (datetime.now() - pd.Timedelta(days=days_back))]
                if len(recent) > 0:
                    # 사용자별 일별 비용 피벗
                    pivot_cost = recent.pivot_table(
                        index='date', columns='email',
                        values='cost_usd', aggfunc='sum', fill_value=0
                    )
                    
                    # 📊 스택 막대차트 (사용자별 일별 누적)
                    st.markdown("**📊 일별 비용 (사용자별 누적, USD)**")
                    st.bar_chart(pivot_cost, height=300)
                    st.caption("💡 색깔별로 사용자가 구분되며, 막대 높이는 일별 총 비용입니다.")
                    
                    # 📈 일별 호출수
                    pivot_count = recent.pivot_table(
                        index='date', columns='email',
                        values='cost_usd', aggfunc='count', fill_value=0
                    )
                    st.markdown("**📈 일별 호출 수 (사용자별)**")
                    st.bar_chart(pivot_count, height=250)
                    
                    # 📋 상세 피벗 테이블
                    st.markdown("**📋 일별 상세 (USD)**")
                    pivot_display = pivot_cost.copy()
                    pivot_display['일별합계'] = pivot_display.sum(axis=1)
                    pivot_display = pivot_display.round(4)
                    pivot_display = pivot_display.sort_index(ascending=False)  # 최신 날짜 위로
                    st.dataframe(pivot_display, use_container_width=True)
                    
                    # 📋 원화 환산 피벗 테이블
                    st.markdown("**📋 일별 상세 (₩원)**")
                    pivot_krw = (pivot_cost * USD_TO_KRW).round(0).astype(int)
                    pivot_krw['일별합계'] = pivot_krw.sum(axis=1)
                    pivot_krw = pivot_krw.sort_index(ascending=False)
                    st.dataframe(pivot_krw, use_container_width=True)
                else:
                    st.caption(f"최근 {days_back}일 내 사용 기록이 없습니다.")
                
                st.divider()
                st.markdown("#### 🤖 모델별 사용 분포")
                ms = df.groupby('model').agg(호출수=('email', 'count'), 비용USD=('cost_usd', 'sum')).reset_index()
                ms['비용원'] = (ms['비용USD'] * USD_TO_KRW).round(0).astype(int)
                ms['비용USD'] = ms['비용USD'].round(4)
                st.dataframe(ms, use_container_width=True, hide_index=True)
    
    with tab2:
        st.markdown("#### 👥 등록 사용자 목록")
        rows = []
        for email, d in user_db["users"].items():
            rows.append({
                "이메일": email,
                "상태": "✅ 승인" if d.get("approved") else "⏳ 대기",
                "관리자": "👑" if d.get("is_admin") else "",
                "이름": d.get("name", "-"),
                "회사": d.get("company", "-"),
                "가입일": d.get("created_at", "-")[:10] if d.get("created_at") else "-",
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        
        st.divider()
        st.markdown("#### ⚙️ 사용자 정지/해제 / 삭제")
        non_admin = [e for e, d in user_db["users"].items() if not d.get("is_admin", False)]
        if non_admin:
            target = st.selectbox("대상 선택", non_admin)
            tdata = user_db["users"][target]
            mc1, mc2 = st.columns(2)
            with mc1:
                if tdata.get("approved"):
                    if st.button("🚫 사용 정지", use_container_width=True):
                        user_db["users"][target]["approved"] = False
                        save_db(user_db)
                        st.warning(f"{target} 정지됨")
                        st.rerun()
                else:
                    if st.button("✅ 사용 재승인", use_container_width=True, type="primary"):
                        user_db["users"][target]["approved"] = True
                        user_db["users"][target]["approved_at"] = datetime.now().isoformat()
                        save_db(user_db)
                        st.success(f"{target} 재승인 완료!")
                        st.rerun()
            with mc2:
                if st.button("🗑️ 사용자 삭제", use_container_width=True):
                    if st.session_state.get("confirm_delete") == target:
                        del user_db["users"][target]
                        save_db(user_db)
                        st.error(f"{target} 삭제됨")
                        st.session_state.confirm_delete = None
                        st.rerun()
                    else:
                        st.session_state.confirm_delete = target
                        st.warning("⚠️ 한 번 더 누르면 삭제됩니다")
        else:
            st.info("관리자 외 사용자가 없습니다.")
    
    with tab3:
        st.markdown("#### ✋ 승인 대기 사용자")
        pending = {e: d for e, d in user_db["users"].items() 
                   if not d.get("approved", False) and not d.get("is_admin", False)}
        if not pending:
            st.success("🎉 승인 대기 중인 사용자가 없습니다.")
        else:
            st.info(f"**{len(pending)}명**이 승인을 기다리고 있습니다.")
            for email, d in pending.items():
                st.markdown(f"""<div class="pending-user">
                    <strong>{email}</strong><br>
                    <span style="font-size:11px; color:#6B7280;">
                        이름: {d.get('name', '-')} · 회사: {d.get('company', '-')}<br>
                        목적: {d.get('purpose', '-')[:100]}<br>
                        신청일: {d.get('created_at', '-')[:16]}
                    </span>
                </div>""", unsafe_allow_html=True)
                pc1, pc2, pc3 = st.columns([1, 1, 3])
                with pc1:
                    if st.button("✅ 승인", key=f"app_{email}", type="primary"):
                        user_db["users"][email]["approved"] = True
                        user_db["users"][email]["approved_at"] = datetime.now().isoformat()
                        save_db(user_db)
                        st.success(f"{email} 승인 완료!")
                        st.rerun()
                with pc2:
                    if st.button("❌ 거부", key=f"rej_{email}"):
                        del user_db["users"][email]
                        save_db(user_db)
                        st.error(f"{email} 거부됨")
                        st.rerun()
    
    with tab4:
        st.markdown("#### 📜 API 호출 상세 로그")
        logs = user_db.get("usage_logs", [])
        REQUIRED_FIELDS = ["timestamp", "email", "model", "input_tokens", "output_tokens", "cost_usd"]
        valid_logs = [l for l in logs if isinstance(l, dict) and all(k in l for k in REQUIRED_FIELDS)]
        
        if not valid_logs:
            st.info("표시할 로그가 없습니다.")
        else:
            df_log = pd.DataFrame(valid_logs).sort_values('timestamp', ascending=False)
            df_log['cost_usd'] = pd.to_numeric(df_log['cost_usd'], errors='coerce').fillna(0)
            df_log['input_tokens'] = pd.to_numeric(df_log['input_tokens'], errors='coerce').fillna(0).astype(int)
            df_log['output_tokens'] = pd.to_numeric(df_log['output_tokens'], errors='coerce').fillna(0).astype(int)
            df_log['cost_krw'] = (df_log['cost_usd'] * USD_TO_KRW).round(0).astype(int)
            df_log['timestamp'] = df_log['timestamp'].astype(str).str[:19].str.replace('T', ' ')
            if 'action' not in df_log.columns:
                df_log['action'] = '-'
            else:
                df_log['action'] = df_log['action'].fillna('-')
            df_log = df_log[['timestamp', 'email', 'action', 'model', 'input_tokens', 'output_tokens', 'cost_usd', 'cost_krw']]
            df_log.columns = ['시간', '사용자', '작업', '모델', '입력', '출력', '비용($)', '비용(₩)']
            
            fc1, fc2 = st.columns(2)
            with fc1:
                fe = st.selectbox("사용자 필터", ["전체"] + sorted(df_log['사용자'].unique().tolist()))
            with fc2:
                fn = st.number_input("표시 개수", min_value=10, max_value=1000, value=50, step=10)
            if fe != "전체":
                df_log = df_log[df_log['사용자'] == fe]
            st.dataframe(df_log.head(fn), use_container_width=True, hide_index=True)
            csv = df_log.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 CSV 다운로드", csv, file_name=f"usage_logs_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    
    st.stop()

# =========== 일반 사용자: Step 1, 2 ===========
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-title">📋 Step 1 · 기술 주제 추천</div>', unsafe_allow_html=True)
    uploaded_biz = st.file_uploader("📸 사업자등록증 업로드 (선택, JPG/PNG/PDF)", type=["jpg", "jpeg", "png", "pdf"])
    bc1, bc2 = st.columns(2)
    with bc1: biz_type = st.text_input("업태", value="제조업")
    with bc2: biz_item = st.text_input("종목", placeholder="예: 골판지 박스 제조")
    custom_guide = st.text_area("🎯 AI 가이드라인 (선택)", placeholder="예: 친환경/탄소중립 키워드 포함", height=70)
    
    if st.button("✨ AI 주제 추천", type="primary", use_container_width=True):
        with st.spinner(f"AI 분석 중... ({selected_model_label})"):
            extra = f"\n[추가 가이드라인]\n{custom_guide}" if custom_guide else ""
            prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.
[{biz_type}] / [{biz_item}] 업종 회사가 벤처인증에 통할 만한 구체적이고 차별화된 기술 주제 3개를 제안하세요.

[가이드라인]
1. IT 편향 없이 하드웨어/공정/신소재도 균형 있게
2. 각 주제는 실제 벤처인증 심사에서 통할 만큼 구체적으로
3. 종목과의 논리적 연관성이 명확해야 함{extra}

JSON 형식으로만 출력 (마크다운 코드펜스 금지):
{{"suggestions": [{{"tech_name": "구체적 기술명", "reason": "추천 사유"}}, {{...}}, {{...}}]}}
"""
            image_data = None; pdf_data = None
            if uploaded_biz:
                fb = uploaded_biz.getvalue()
                if uploaded_biz.type == "application/pdf":
                    pdf_data = fb
                else:
                    try:
                        from PIL import Image
                        img = Image.open(io.BytesIO(fb))
                        if img.mode != "RGB": img = img.convert("RGB")
                        buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
                        image_data = buf.getvalue()
                    except Exception as e: st.warning(f"이미지 처리 실패: {e}")
            
            result = claude_generate(prompt, selected_model, max_tokens=2000,
                                     image_data=image_data, pdf_data=pdf_data,
                                     user_email=st.session_state.authenticated_user,
                                     action_type="step1_recommend")
            if not result["ok"]:
                st.error(f"⚠️ {result['error']}")
                if "trace" in result:
                    with st.expander("🔍 상세"): st.code(result["trace"])
            else:
                try:
                    clean = result["text"].replace('```json', '').replace('```', '').strip()
                    st.session_state.suggestions = json.loads(clean)
                    cost = (result["input_tokens"]*MODEL_PRICES[selected_model]["input"] + result["output_tokens"]*MODEL_PRICES[selected_model]["output"])/1_000_000
                    st.success(f"✅ 추천 완료 (입력 {result['input_tokens']}, 출력 {result['output_tokens']}, ${cost:.4f} / ₩{cost*USD_TO_KRW:.0f})")
                    st.session_state["user_db_cache"] = load_db()
                except Exception as e:
                    st.error(f"JSON 파싱 실패: {e}")
                    st.code(result["text"])
    
    if "suggestions" in st.session_state and isinstance(st.session_state.suggestions, dict):
        for s in st.session_state.suggestions.get('suggestions', []):
            st.markdown(f"""<div class="rec-card">
                <div class="rec-card-title">🎯 {s.get('tech_name', '')}</div>
                <div class="rec-card-desc">{s.get('reason', '')}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"→ 이 기술로 진행", key=f"pick_{s.get('tech_name', '')}"):
                st.session_state.step2_topic = s.get('tech_name', '')
                st.rerun()

with col2:
    st.markdown('<div class="sec-title">📑 Step 2 · 마스터 리포트 생성</div>', unsafe_allow_html=True)
    topic = st.text_input("확정된 기술명", value=st.session_state.get('step2_topic', ''), placeholder="기술명 입력 또는 Step 1에서 선택")
    
    times = {"claude-haiku-4-5-20251001": "약 15~25초", "claude-sonnet-4-6": "약 30~50초", "claude-opus-4-7": "약 60~90초"}
    est = times.get(selected_model, "약 30~60초")
    st.caption(f"⏱️ 예상 소요: **{est}**")
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not topic:
            st.warning("기술명을 먼저 입력해주세요.")
        else:
            pt = st.empty()
            pt.info(f"🔄 {selected_model_label}로 리포트 생성 중... ({est})")
            with st.spinner("AI가 11개 섹션 작성 중..."):
                prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.

기술명: [{topic}]

위 기술에 대해 벤처인증 심사용 사업계획서 11개 항목을 매우 구체적으로 작성하세요.

[중요 규칙]
1. 표(Table) 절대 금지 - '•' 또는 '1. 2. 3.' 텍스트
2. 항목별로 반드시 '### [번호. 항목명]' 형식
3. 1번 항목에는 'V자 요약' 7문장 필수 ('V '로 시작)
4. 수치는 일반 업계 표현만
5. 각 항목 최소 5줄 이상

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
                result = claude_generate(prompt, selected_model, max_tokens=8192,
                                         user_email=st.session_state.authenticated_user,
                                         action_type="step2_report")
            pt.empty()
            if not result["ok"]:
                st.error(f"❌ 리포트 생성 실패: {result['error']}")
                if "trace" in result:
                    with st.expander("🔍 상세"): st.code(result["trace"])
                st.info("💡 다른 모델(사이드바) 선택해보세요.")
            else:
                st.session_state.report = result["text"]
                st.session_state.sections = result["text"].split('### ')
                cost = (result["input_tokens"]*MODEL_PRICES[selected_model]["input"] + result["output_tokens"]*MODEL_PRICES[selected_model]["output"])/1_000_000
                st.success(f"✅ 생성 완료! (입력 {result['input_tokens']}, 출력 {result['output_tokens']:,}, ${cost:.4f} / ₩{cost*USD_TO_KRW:.0f})")
                st.session_state["user_db_cache"] = load_db()

if "sections" in st.session_state:
    st.divider()
    st.markdown('<div class="sec-title">📄 생성 결과 · 다운로드 및 복사</div>', unsafe_allow_html=True)
    td = topic if topic else st.session_state.get('step2_topic', '샘플')
    html_content = generate_branded_html(td, st.session_state.sections)
    dc1, dc2 = st.columns([2, 1])
    with dc1:
        st.download_button("💎 프리미엄 디자인 리포트 다운로드 (.html)",
                          data=html_content, file_name=f"RSV_벤처인증_리포트_{td}.html",
                          mime="text/html", type="primary", use_container_width=True)
    with dc2:
        st.caption("💡 HTML → 브라우저 열기 → Ctrl+P → PDF 저장!")
    st.divider()
    st.markdown("💡 **벤처인증 사이트에 붙여넣기:** 각 섹션 [복사] 버튼 → 항목별 붙여넣기")
    for sec in st.session_state.sections:
        if not sec.strip(): continue
        ps = sec.split('\n', 1)
        st_title = ps[0].strip('[] #').strip()
        sb = ps[1].strip() if len(ps) > 1 else ""
        if not st_title: continue
        st.markdown(f'<div class="copy-label">📌 {st_title}</div>', unsafe_allow_html=True)
        st.code(sb, language="text")

st.markdown("""
<div style="text-align:center; padding:40px 0 20px; color:#888; font-size:11px; letter-spacing:1.5px;">
    <span style="color:#C9A961; font-weight:700;">RSV</span> · Rich Secret Vault<br>
    © 2026 중소기업경영지원단 & 부자들의 비밀금고
</div>
""", unsafe_allow_html=True)
