import streamlit as st
import anthropic
import json
import os
import io
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
# 🔒 GitHub Gist DB 시스템
# =====================================================================
DB_FILE = "user_database.json"

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
                    return json.loads(data["files"][fn]["content"])
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
        try:
            requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
        except: pass
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    st.session_state["user_db_cache"] = db

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]

# =====================================================================
# 🎨 이미지 처리
# =====================================================================
def get_image_src(image_path, fallback_url):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = image_path.lower().split('.')[-1]
            mime = "png" if ext == "png" else "jpeg"
            return f"data:image/{mime};base64,{b64}"
        except:
            return fallback_url
    return fallback_url

LOGO_SRC = get_image_src(
    "프로필이미지.jpg",
    "https://placehold.co/300x300/0A1628/C9A961?text=LOGO&font=roboto"
)
BANNER_SRC = get_image_src(
    "배너광고1.jpg",
    "https://placehold.co/1330x120/0A1628/C9A961?text=%EB%B6%80%EC%9E%90%EB%93%A4%EC%9D%98+%EB%B9%84%EB%B0%80%EA%B8%88%EA%B3%A0&font=roboto"
)

# =====================================================================
# 📄 프리미엄 디자인 HTML (기존 그대로 유지)
# =====================================================================
def generate_branded_html(topic, sections):
    css = r"""
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&display=swap');
    @page { size: A4 portrait; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Pretendard Variable', Pretendard, 'Noto Sans KR', sans-serif; font-size: 14px; color: #2B2416; line-height: 1.7; background: #2B2416; display: flex; flex-direction: column; align-items: center; padding: 20px 0; letter-spacing: -0.2px; font-weight: 400; }
    .page { width: 210mm; min-height: 297mm; max-height: 297mm; background: linear-gradient(135deg, #FAF6EE 0%, #F5EDD9 100%); margin-bottom: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.35); position: relative; overflow: hidden; page-break-after: always; page-break-inside: avoid; display: flex; flex-direction: column; }
    .page::before { content: ''; position: absolute; inset: 0; background-image: radial-gradient(circle at 20% 80%, rgba(201,169,97,0.06) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139,111,62,0.05) 0%, transparent 50%); pointer-events: none; z-index: 1; }
    .page > * { position: relative; z-index: 2; }
    @media print { * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } body { background: white !important; padding: 0 !important; } .page { box-shadow: none !important; margin: 0 !important; background: linear-gradient(135deg, #FAF6EE, #F5EDD9) !important; } .cover-page { background: linear-gradient(135deg, #0A1628, #0F2847, #1B3A6B) !important; } .v-item { background: linear-gradient(135deg, #FFFBF0, #F9F1DC) !important; } }
    .cover-page { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%); color: white; }
    .cover-page .corner-deco { position: absolute; width: 60px; height: 60px; border: 2px solid rgba(201,169,97,0.6); z-index: 3; }
    .cover-page .corner-tl { top: 30px; left: 30px; border-right: none; border-bottom: none; }
    .cover-page .corner-tr { top: 30px; right: 30px; border-left: none; border-bottom: none; }
    .cover-page .corner-bl { bottom: 30px; left: 30px; border-right: none; border-top: none; }
    .cover-page .corner-br { bottom: 30px; right: 30px; border-left: none; border-top: none; }
    .cover-page::before { content: ''; position: absolute; top: -30%; right: -20%; width: 70%; height: 70%; background: radial-gradient(ellipse, rgba(201,169,97,0.22) 0%, transparent 60%); }
    .cover-inner { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40mm 20mm; position: relative; z-index: 2; }
    .cover-logo { width: 140px; height: 140px; border-radius: 50%; border: 3px solid #C9A961; object-fit: cover; background: white; margin-bottom: 30px; box-shadow: 0 8px 32px rgba(201,169,97,0.45); }
    .cover-brand { font-size: 64px; font-weight: 900; letter-spacing: 14px; background: linear-gradient(180deg, #F4D98A 0%, #E6C770 30%, #C9A961 60%, #8B6F3E 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1; margin-bottom: 12px; text-indent: 14px; filter: drop-shadow(0 2px 8px rgba(201,169,97,0.3)); }
    .cover-subbrand { font-size: 14px; font-weight: 500; letter-spacing: 8px; color: rgba(244,217,138,0.85); text-transform: uppercase; margin-bottom: 28px; text-indent: 8px; font-family: 'Cormorant Garamond', serif; font-style: italic; }
    .cover-divider { width: 100px; height: 2px; background: linear-gradient(90deg, transparent, #C9A961, #F4D98A, #C9A961, transparent); margin-bottom: 32px; position: relative; }
    .cover-divider::before, .cover-divider::after { content: '◆'; position: absolute; top: -9px; color: #C9A961; font-size: 14px; }
    .cover-divider::before { left: -4px; }
    .cover-divider::after { right: -4px; }
    .cover-title { font-size: 32px; font-weight: 700; letter-spacing: 4px; color: white; margin-bottom: 60px; }
    .cover-topic-label { font-size: 11px; font-weight: 600; letter-spacing: 4px; color: #F4D98A; text-transform: uppercase; margin-bottom: 18px; }
    .cover-topic { font-size: 22px; font-weight: 500; color: rgba(255,255,255,0.94); max-width: 80%; text-align: center; line-height: 1.55; padding: 20px 40px; border-top: 1px solid rgba(201,169,97,0.4); border-bottom: 1px solid rgba(201,169,97,0.4); }
    .cover-footer { padding: 18px 20mm; background: linear-gradient(90deg, #F4D98A, #C9A961, #F4D98A); color: #0A1628; font-size: 10px; text-align: center; letter-spacing: 2px; font-weight: 700; }
    .page-header { padding: 15mm 15mm 10mm; border-bottom: 1px solid rgba(201,169,97,0.35); display: flex; align-items: center; gap: 16px; background: linear-gradient(180deg, rgba(201,169,97,0.08) 0%, transparent 100%); }
    .header-logo { width: 44px; height: 44px; border-radius: 50%; border: 2px solid #C9A961; object-fit: cover; background: white; }
    .section-badge { background: linear-gradient(135deg, #8B6F3E 0%, #C9A961 50%, #8B6F3E 100%); color: white; padding: 5px 15px; border-radius: 20px; font-size: 10.5px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
    .page-title { font-size: 22px; font-weight: 800; color: #0F2847; flex: 1; }
    .page-body { flex: 1; padding: 12mm 15mm; font-size: 14px; line-height: 1.85; color: #3A2F1E; overflow: hidden; }
    .sub-title { font-size: 16px; font-weight: 800; color: #0F2847; margin: 22px 0 12px; padding: 6px 14px 6px 16px; border-left: 4px solid #C9A961; background: linear-gradient(90deg, rgba(201,169,97,0.12) 0%, transparent 80%); border-radius: 0 6px 6px 0; }
    .v-item { background: linear-gradient(135deg, #FFFBF0 0%, #F9F1DC 100%); border-left: 4px solid #C9A961; padding: 13px 20px; border-radius: 0 10px 10px 0; margin-bottom: 12px; display: flex; gap: 14px; }
    .v-item .v-mark { color: #8B6F3E; font-size: 20px; font-weight: 900; flex-shrink: 0; line-height: 1.4; font-family: 'Cormorant Garamond', serif; }
    .v-item .v-content { color: #2B2416; font-size: 13.5px; font-weight: 500; }
    .v-item .v-content strong { color: #0F2847; font-weight: 800; background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%); padding: 0 2px; }
    .bullet-item { padding: 6px 0 6px 26px; position: relative; color: #3A2F1E; font-size: 13.5px; }
    .bullet-item::before { content: '◆'; color: #C9A961; font-size: 11px; position: absolute; left: 8px; top: 9px; }
    .bullet-item strong { color: #0F2847; font-weight: 700; background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%); padding: 0 2px; }
    .body-text { color: #3A2F1E; font-size: 13.5px; line-height: 1.8; margin-bottom: 10px; }
    .footer-banner { width: 100%; height: 28mm; object-fit: cover; border-top: 2px solid #C9A961; }
    .page-number { position: absolute; bottom: 32mm; right: 12mm; font-size: 10px; color: #8B6F3E; font-weight: 700; letter-spacing: 2px; z-index: 10; font-family: 'Cormorant Garamond', serif; }
    .page-number::before { content: '— '; color: #C9A961; }
    .page-number::after { content: ' —'; color: #C9A961; }
    """
    
    def render_section_body(body_text):
        html_parts = []
        for line in body_text.split('\n'):
            s = line.strip()
            if not s: continue
            if s.startswith('V ') or s.startswith('V\t'):
                content = s[2:].strip().replace('[', '<strong>[').replace(']', ']</strong>')
                html_parts.append(f'<div class="v-item"><span class="v-mark">V</span><span class="v-content">{content}</span></div>')
            elif s.startswith('- 신청기술') or s.startswith('-신청기술'):
                html_parts.append(f'<div class="sub-title">{s.lstrip("-").strip()}</div>')
            elif s.startswith('• ') or s.startswith('- ') or s.startswith('* '):
                content = s.lstrip('•-* ').strip().replace('[', '<strong>[').replace(']', ']</strong>')
                html_parts.append(f'<div class="bullet-item">{content}</div>')
            elif len(s) >= 2 and s[0].isdigit() and s[1] == '.':
                content = s[2:].strip()
                if len(content) < 40 and (':' in content or content.endswith('략') or content.endswith('안') or content.endswith('획')):
                    html_parts.append(f'<div class="sub-title">{s}</div>')
                else:
                    html_parts.append(f'<div class="body-text">{s}</div>')
            else:
                html_parts.append(f'<div class="body-text">{s}</div>')
        return '\n'.join(html_parts)
    
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
    <div class="cover-footer">중소기업경영지원단 · VENTURE CERTIFICATION CONSULTING · {datetime.now().strftime('%Y.%m.%d')}</div>
</div>
"""
    page_num = 0
    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n', 1)
        title_raw = lines[0].strip('[] #').strip()
        if not title_raw: continue
        body_text = lines[1] if len(lines) > 1 else ""
        page_num += 1
        body_html = render_section_body(body_text)
        html += f"""<div class="page">
    <div class="page-header"><img src="{LOGO_SRC}" class="header-logo" alt="로고"><span class="section-badge">CHAPTER {page_num:02d}</span><div class="page-title">{title_raw}</div></div>
    <div class="page-body">{body_html}</div>
    <div class="page-number">{page_num:02d}</div>
    <img src="{BANNER_SRC}" class="footer-banner" alt="배너">
</div>
"""
    return html + "</body></html>"


def get_sample_sections():
    sample_raw = """### [1. 신청기술 요약 및 표준 양식]
- 신청기술(제품/서비스)명: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술
- 신청기술(제품/서비스)요약: AI FEA 기반 골판지 박스 구조 자동 설계 플랫폼

V 기존 시장에 [박스 과잉설계로 인한 물류비 증가]가 있는데, [경험 의존적 설계]라는 이유로 중소 제조사들이 여전히 불편을 겪고 있음
V 당사에서 [FEA 기반 구조 최적화 알고리즘]으로 해결책을 찾았으며, 기존 기술과 [설계 시간 90% 단축 + 재료비 25% 절감]이라는 차이를 보유
V 현재 당사 기술명은 [AI 골판지 최적설계 시스템], 전체 시장은 [국내 3.2조원 규모]이며 [연평균 12% 성장] 기대
V 당사 기술은 [머신러닝 기반 자동화]를 갖고 있으며 [품질 균일화]로 잠재 고객 만족도가 높을 수 있음
V 기술에 대한 [특허 2건 등록]이며 [전담 R&D 5명] 보유, 끊임없는 R&D로 지속 발전 가능
V 시장진입을 위해 [박람회 3회 참가 및 12개사 확보] 진행, 향후 [ASEAN 진출] 계획
V 당사 성과는 [10년 이상 축적된 데이터]가 있기에 가능하며 향후 [매출 3배 성장]을 해낼 것임

### [2. 개발배경 및 원인분석]
• 국내 포장산업은 약 40조원 규모이나 골판지 박스 설계는 경험 의존적 방식
• 친환경 규제 강화로 재료 절감 요구가 급증하며 최적화 기술 필요성 대두
• 기존 설계 SW는 대부분 해외 제품으로 국내 중소 제조사 접근성이 낮음

### [3. 경쟁력 확보방안]
1. 독자적 AI 알고리즘: 10년 축적 실측 데이터 기반 머신러닝 모델로 우위 확보
2. 설계 리드타임 단축: 기존 2주 → 1일 이내로 단축
3. 비용 우위: 해외 솔루션 대비 1/3 가격대로 진입장벽 해소

### [4. 추진경과 및 향후 계획]
1. 2022년: 핵심 알고리즘 프로토타입 개발 완료
2. 2023년: 특허 출원 2건 및 첫 상업 버전 출시
3. 2024년: 정식 제품 출시 및 12개 기업 계약
4. 2025년 계획: ASEAN 수출 개시 및 AI 정확도 고도화

### [5. 목표시장 및 고객정의]
• 1차 타겟: 국내 중소 골판지 제조사 약 3,500개사
• 2차 타겟: 중견 물류기업 및 이커머스 포장 담당
• 3차 타겟: ASEAN 지역 포장 기업"""
    return sample_raw.split('### ')


# =====================================================================
# 🤖 Claude API — 안정성 강화 버전
# =====================================================================
MODEL_OPTIONS = {
    "⚡ Haiku 4.5 (빠름·저렴)": "claude-haiku-4-5-20251001",
    "⭐ Sonnet 4.6 (균형·기본)": "claude-sonnet-4-6",
    "👑 Opus 4.7 (최고품질·느림)": "claude-opus-4-7",
}

def claude_generate(prompt, model_id, max_tokens=8192, image_data=None, pdf_data=None):
    """안정성 강화: 명시적 에러 반환 + 이미지/PDF 지원"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        
        # 콘텐츠 블록 구성
        content_blocks = []
        if pdf_data is not None:
            pdf_b64 = base64.standard_b64encode(pdf_data).decode("utf-8")
            content_blocks.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}
            })
        elif image_data is not None:
            img_b64 = base64.standard_b64encode(image_data).decode("utf-8")
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
        content_blocks.append({"type": "text", "text": prompt})
        
        response = client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content_blocks}]
        )
        return {"ok": True, "text": response.content[0].text, "tokens": response.usage.output_tokens}
    except anthropic.RateLimitError as e:
        return {"ok": False, "error": f"Rate Limit 초과: {str(e)[:200]}"}
    except anthropic.APIStatusError as e:
        return {"ok": False, "error": f"API 오류 ({e.status_code}): {str(e.message)[:200]}"}
    except Exception as e:
        import traceback
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}", "trace": traceback.format_exc()}


# =====================================================================
# 🎨 Streamlit 메인 UI
# =====================================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    .stApp { background: #f0f2f5; font-family: 'Pretendard Variable', 'Noto Sans KR', sans-serif; }
    .dash-header { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%); color: white; padding: 30px 40px; border-radius: 16px; border-bottom: 4px solid #C9A961; margin-bottom: 28px; position: relative; overflow: hidden; }
    .dash-header::before { content: ''; position: absolute; top: -50%; right: -10%; width: 60%; height: 200%; background: radial-gradient(ellipse, rgba(201,169,97,0.15) 0%, transparent 60%); }
    .dash-header h1 { color: white !important; font-weight: 900 !important; margin: 0 !important; font-size: 26px !important; }
    .dash-header .brand-tag { display: inline-block; background: linear-gradient(180deg, #F4D98A, #C9A961, #8B6F3E); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; letter-spacing: 4px; font-size: 14px; margin-bottom: 4px; }
    .dash-header p { color: rgba(255,255,255,0.75); margin: 6px 0 0 !important; font-size: 13px; }
    .sec-title { background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; border: 1px solid #E2E8F0; border-left: 4px solid #C9A961; color: #0F2847; font-weight: 800; font-size: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .copy-label { font-weight: 800; color: #0F2847; margin: 18px 0 8px; padding-left: 10px; border-left: 3px solid #C9A961; font-size: 14px; }
    [data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, #C9A961 0%, #A37C3E 100%) !important; color: #0A1628 !important; font-weight: 800 !important; border: none !important; border-radius: 10px !important; box-shadow: 0 2px 8px rgba(201,169,97,0.3) !important; }
    .rec-card { background: linear-gradient(135deg, #FCFDFE 0%, #F0F4F9 100%); border: 1px solid #D0D9E3; border-left: 4px solid #C9A961; border-radius: 10px; padding: 16px 18px; margin: 10px 0; }
    .rec-card-title { font-size: 15px; font-weight: 800; color: #0F2847; margin-bottom: 6px; }
    .rec-card-desc { font-size: 13px; color: #4A5568; line-height: 1.6; }
    section[data-testid="stSidebar"] { background: #0A1628 !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stButton > button { background: rgba(201,169,97,0.1) !important; border: 1px solid rgba(201,169,97,0.3) !important; color: #C9A961 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# 세션 초기화
if 'authenticated_user' not in st.session_state: st.session_state.authenticated_user = None

# 로그인 화면
if st.session_state.authenticated_user is None:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px 30px;">
        <div style="display:inline-block; background:linear-gradient(180deg,#F4D98A,#C9A961,#8B6F3E); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:#C9A961; font-size:48px; font-weight:900; letter-spacing:12px;">RSV</div>
        <div style="color:#999; letter-spacing:5px; font-size:12px; margin-bottom:8px;">RICH SECRET VAULT</div>
        <div style="color:#0F2847; font-size:22px; font-weight:700; letter-spacing:2px;">벤처인증 AI 마스터 컨설턴트</div>
    </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        email = st.text_input("이메일 로그인", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        if st.button("로그인", type="primary", use_container_width=True):
            if email in user_db["users"]:
                st.session_state.authenticated_user = email
                st.rerun()
            else:
                st.error("등록되지 않은 이메일입니다.")
    st.stop()

# 메인 헤더
st.markdown("""
<div class="dash-header">
    <div class="brand-tag">RICH SECRET VAULT</div>
    <h1>🏛️ 벤처인증 AI 마스터 컨설턴트</h1>
    <p>중소기업경영지원단 · 프리미엄 디자인 리포트 & 복사 통합 모드</p>
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.authenticated_user}**")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    
    st.divider()
    # 🆕 모델 선택
    st.markdown("### 🤖 AI 품질")
    selected_model_label = st.radio(
        "모델 선택",
        options=list(MODEL_OPTIONS.keys()),
        index=1,  # 기본 Sonnet
        label_visibility="collapsed"
    )
    selected_model = MODEL_OPTIONS[selected_model_label]
    st.caption(f"사용 모델: `{selected_model}`")
    
    st.divider()
    st.markdown("### 🎨 디자인 미리보기")
    st.caption("API 호출 없이 디자인만 확인. 비용 0원.")
    if st.button("🧪 샘플 데이터로 미리보기", use_container_width=True):
        st.session_state.sections = get_sample_sections()
        st.session_state.step2_topic = "데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술"
        st.rerun()

col1, col2 = st.columns([1, 1], gap="large")

# =====================================================================
# Step 1: 기술 주제 추천 (사업자등록증 + 업종)
# =====================================================================
with col1:
    st.markdown('<div class="sec-title">📋 Step 1 · 기술 주제 추천</div>', unsafe_allow_html=True)
    
    # 🆕 사업자등록증 업로드
    uploaded_biz = st.file_uploader(
        "📸 사업자등록증 업로드 (선택, JPG/PNG/PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        help="업로드하면 AI가 회사 업종을 자동 분석합니다"
    )
    
    # 🆕 업종/업태 직접 입력
    biz_col1, biz_col2 = st.columns(2)
    with biz_col1:
        biz_type = st.text_input("업태", value="제조업")
    with biz_col2:
        biz_item = st.text_input("종목", placeholder="예: 골판지 박스 제조")
    
    custom_guide = st.text_area(
        "🎯 AI 가이드라인 (선택)",
        placeholder="예: 친환경/탄소중립 키워드 포함",
        height=70
    )
    
    if st.button("✨ AI 주제 추천", type="primary", use_container_width=True):
        with st.spinner(f"AI 분석 중... ({selected_model_label})"):
            extra = f"\n[추가 가이드라인]\n{custom_guide}" if custom_guide else ""
            
            prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.
[{biz_type}] / [{biz_item}] 업종 회사가 벤처인증에 통할 만한 구체적이고 차별화된 기술 주제 3개를 제안하세요.

[가이드라인]
1. IT 편향 없이 하드웨어/공정/신소재도 균형 있게
2. 각 주제는 실제 벤처인증 심사에서 통할 만큼 구체적으로
3. 종목과의 논리적 연관성이 명확해야 함{extra}

[출력 규칙]
반드시 아래 JSON 형식으로만 출력 (마크다운 코드펜스 금지, 설명 금지):
{{
  "suggestions": [
    {{
      "tech_name": "구체적 기술명",
      "reason": "추천 사유 (2-3문장)"
    }},
    {{...}},
    {{...}}
  ]
}}
"""
            
            # 사업자등록증이 있으면 함께 전달
            image_data = None
            pdf_data = None
            if uploaded_biz:
                file_bytes = uploaded_biz.getvalue()
                if uploaded_biz.type == "application/pdf":
                    pdf_data = file_bytes
                else:
                    # 이미지를 JPEG로 변환
                    try:
                        from PIL import Image
                        img = Image.open(io.BytesIO(file_bytes))
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=85)
                        image_data = buf.getvalue()
                    except Exception as e:
                        st.warning(f"이미지 처리 실패, 텍스트만 사용: {e}")
            
            result = claude_generate(prompt, selected_model, max_tokens=2000, 
                                     image_data=image_data, pdf_data=pdf_data)
            
            if not result["ok"]:
                st.error(f"⚠️ {result['error']}")
                if "trace" in result:
                    with st.expander("🔍 상세 에러"):
                        st.code(result["trace"])
            else:
                try:
                    clean = result["text"].replace('```json', '').replace('```', '').strip()
                    st.session_state.suggestions = json.loads(clean)
                    st.success(f"✅ 추천 완료 (출력 토큰: {result['tokens']})")
                except Exception as e:
                    st.error(f"JSON 파싱 실패: {e}")
                    st.code(result["text"])
    
    if "suggestions" in st.session_state and isinstance(st.session_state.suggestions, dict):
        for s in st.session_state.suggestions.get('suggestions', []):
            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-card-title">🎯 {s.get('tech_name', '')}</div>
                <div class="rec-card-desc">{s.get('reason', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"→ 이 기술로 진행", key=f"pick_{s.get('tech_name', '')}"):
                st.session_state.step2_topic = s.get('tech_name', '')
                st.rerun()

# =====================================================================
# Step 2: 마스터 리포트 생성
# =====================================================================
with col2:
    st.markdown('<div class="sec-title">📑 Step 2 · 마스터 리포트 생성</div>', unsafe_allow_html=True)
    topic = st.text_input(
        "확정된 기술명",
        value=st.session_state.get('step2_topic', ''),
        placeholder="여기에 기술명을 입력하거나 Step 1에서 선택"
    )
    
    # 🆕 모델 별 예상 시간 안내
    time_estimates = {
        "claude-haiku-4-5-20251001": "약 15~25초",
        "claude-sonnet-4-6": "약 30~50초",
        "claude-opus-4-7": "약 60~90초",
    }
    est_time = time_estimates.get(selected_model, "약 30~60초")
    st.caption(f"⏱️ 현재 모델 예상 소요 시간: **{est_time}**")
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not topic:
            st.warning("기술명을 먼저 입력해주세요.")
        else:
            # 🆕 명확한 진행 표시
            progress_text = st.empty()
            progress_text.info(f"🔄 {selected_model_label} 모델로 리포트 생성 중... ({est_time} 소요 예상)")
            
            with st.spinner("AI가 11개 섹션을 작성 중..."):
                prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.

기술명: [{topic}]

위 기술에 대해 벤처인증 심사용 사업계획서 11개 항목을 매우 구체적으로 작성하세요.

[중요 규칙]
1. 표(Table) 절대 금지 - 모든 설명은 '•' 또는 '1. 2. 3.' 텍스트로 풀어쓸 것
2. 항목별로 반드시 '### [번호. 항목명]' 형식으로 구분
3. 1번 항목에는 'V자 요약' 7문장 필수 포함 (각 줄 'V '로 시작)
4. 수치는 일반 업계 표현만 사용 (지어낸 숫자 금지)
5. 각 항목은 최소 5줄 이상 구체적으로

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
                result = claude_generate(prompt, selected_model, max_tokens=8192)
            
            progress_text.empty()
            
            if not result["ok"]:
                st.error(f"❌ 리포트 생성 실패: {result['error']}")
                if "trace" in result:
                    with st.expander("🔍 상세 에러 보기"):
                        st.code(result["trace"])
                st.info("💡 다시 시도하거나 다른 모델(사이드바)을 선택해보세요.")
            else:
                st.session_state.report = result["text"]
                st.session_state.sections = result["text"].split('### ')
                st.success(f"✅ 리포트 생성 완료! (출력 토큰: {result['tokens']:,})")

# =====================================================================
# 결과 출력
# =====================================================================
if "sections" in st.session_state:
    st.divider()
    st.markdown('<div class="sec-title">📄 생성 결과 · 다운로드 및 복사</div>', unsafe_allow_html=True)
    
    topic_display = topic if topic else st.session_state.get('step2_topic', '샘플')
    html_content = generate_branded_html(topic_display, st.session_state.sections)
    
    dc1, dc2 = st.columns([2, 1])
    with dc1:
        st.download_button(
            label="💎 프리미엄 디자인 리포트 다운로드 (.html)",
            data=html_content,
            file_name=f"RSV_벤처인증_리포트_{topic_display}.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )
    with dc2:
        st.caption("💡 다운받은 HTML을 브라우저로 열고 Ctrl+P → PDF 저장 → A4 리포트 완성!")
    
    st.divider()
    st.markdown(
        "💡 **벤처인증 사이트에 붙여넣기:** 아래 각 섹션 우측 상단의 **[복사]** 버튼을 클릭하여 항목별로 붙여넣으세요.",
        unsafe_allow_html=True
    )
    
    for sec in st.session_state.sections:
        if not sec.strip(): continue
        parts = sec.split('\n', 1)
        sec_title = parts[0].strip('[] #').strip()
        sec_body = parts[1].strip() if len(parts) > 1 else ""
        if not sec_title: continue
        st.markdown(f'<div class="copy-label">📌 {sec_title}</div>', unsafe_allow_html=True)
        st.code(sec_body, language="text")

# 푸터
st.markdown("""
<div style="text-align:center; padding:40px 0 20px; color:#888; font-size:11px; letter-spacing:1.5px;">
    <span style="color:#C9A961; font-weight:700;">RSV</span> · Rich Secret Vault<br>
    © 2026 중소기업경영지원단 & 부자들의 비밀금고
</div>
""", unsafe_allow_html=True)
