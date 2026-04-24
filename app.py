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
        requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    st.session_state["user_db_cache"] = db

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]

# =====================================================================
# 🎨 이미지 처리 — 로컬 파일 있으면 base64, 없으면 공개 placeholder
# =====================================================================
def get_image_src(image_path, fallback_url):
    """로컬 파일 있으면 base64 / 없으면 온라인 placeholder URL"""
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
# 📄 프리미엄 디자인 HTML 생성 — RSV 스타일 기반
# =====================================================================
def generate_branded_html(topic, sections):
    """
    RSV 재무경영진단리포트 스타일을 차용한 프리미엄 벤처인증 리포트
    - 다크 네이비 + 골드 그라디언트
    - Pretendard 폰트
    - A4 인쇄 최적화
    """
    css = r"""
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&display=swap');
    
    @page { size: A4 portrait; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
        font-family: 'Pretendard Variable', Pretendard, 'Noto Sans KR', -apple-system, sans-serif;
        font-size: 14px;
        color: #2B2416;
        line-height: 1.7;
        background: #2B2416;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px 0;
        letter-spacing: -0.2px;
        font-weight: 400;
    }
    
    /* A4 페이지 규격 — 샴페인 크림 배경 */
    .page {
        width: 210mm;
        min-height: 297mm;
        max-height: 297mm;
        background: linear-gradient(135deg, #FAF6EE 0%, #F5EDD9 100%);
        margin-bottom: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 2px 8px rgba(201,169,97,0.15);
        position: relative;
        overflow: hidden;
        page-break-after: always;
        page-break-inside: avoid;
        display: flex;
        flex-direction: column;
    }
    
    /* 종이 질감 표현 — 미세한 노이즈 텍스처 */
    .page::before {
        content: '';
        position: absolute;
        inset: 0;
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(201,169,97,0.06) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(139,111,62,0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 1;
    }
    .page > * { position: relative; z-index: 2; }
    
    /* 인쇄 최적화 */
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
        body { background: white !important; padding: 0 !important; }
        .page { box-shadow: none !important; margin: 0 !important; page-break-after: always; background: linear-gradient(135deg, #FAF6EE 0%, #F5EDD9 100%) !important; }
        .page:last-child { page-break-after: avoid; }
        .cover-page { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%) !important; }
        .section-badge { background: linear-gradient(135deg, #8B6F3E, #C9A961) !important; color: white !important; }
        .v-item { background: linear-gradient(135deg, #FFFBF0, #F9F1DC) !important; border-left: 4px solid #C9A961 !important; }
        .highlight-box { background: linear-gradient(135deg, #1B3A6B, #2C5282) !important; color: white !important; }
    }
    
    /* =========================================
       📕 표지 페이지 — 다크 네이비 + 골드 (유지)
       ========================================= */
    .cover-page {
        background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%);
        color: white;
        position: relative;
    }
    
    /* 골드 장식 — 4귀퉁이 코너 데코 */
    .cover-page .corner-deco {
        position: absolute;
        width: 60px;
        height: 60px;
        border: 2px solid rgba(201,169,97,0.6);
        z-index: 3;
    }
    .cover-page .corner-tl { top: 30px; left: 30px; border-right: none; border-bottom: none; }
    .cover-page .corner-tr { top: 30px; right: 30px; border-left: none; border-bottom: none; }
    .cover-page .corner-bl { bottom: 30px; left: 30px; border-right: none; border-top: none; }
    .cover-page .corner-br { bottom: 30px; right: 30px; border-left: none; border-top: none; }
    
    /* 골드 데코 - 배경 조명 효과 */
    .cover-page::before {
        content: '';
        position: absolute;
        top: -30%;
        right: -20%;
        width: 70%;
        height: 70%;
        background: radial-gradient(ellipse, rgba(201,169,97,0.22) 0%, transparent 60%);
        pointer-events: none;
    }
    .cover-page::after {
        content: '';
        position: absolute;
        bottom: -20%;
        left: -15%;
        width: 60%;
        height: 60%;
        background: radial-gradient(ellipse, rgba(201,169,97,0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    
    .cover-inner {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40mm 20mm;
        position: relative;
        z-index: 2;
    }
    
    .cover-logo {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        border: 3px solid #C9A961;
        object-fit: cover;
        background: white;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(201,169,97,0.45), 0 0 0 8px rgba(201,169,97,0.1);
    }
    
    .cover-brand {
        font-size: 64px;
        font-weight: 900;
        letter-spacing: 14px;
        background: linear-gradient(180deg, #F4D98A 0%, #E6C770 30%, #C9A961 60%, #8B6F3E 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: #C9A961;
        line-height: 1.1;
        margin-bottom: 12px;
        text-indent: 14px;
        filter: drop-shadow(0 2px 8px rgba(201,169,97,0.3));
    }
    
    .cover-subbrand {
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 8px;
        color: rgba(244,217,138,0.85);
        text-transform: uppercase;
        margin-bottom: 28px;
        text-indent: 8px;
        font-family: 'Cormorant Garamond', serif;
        font-style: italic;
    }
    
    .cover-divider {
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, transparent, #C9A961, #F4D98A, #C9A961, transparent);
        margin-bottom: 32px;
        position: relative;
    }
    .cover-divider::before,
    .cover-divider::after {
        content: '◆';
        position: absolute;
        top: -9px;
        color: #C9A961;
        font-size: 14px;
    }
    .cover-divider::before { left: -4px; }
    .cover-divider::after { right: -4px; }
    
    .cover-title {
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 4px;
        color: white;
        margin-bottom: 60px;
    }
    
    .cover-topic-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 4px;
        color: #F4D98A;
        text-transform: uppercase;
        margin-bottom: 18px;
    }
    
    .cover-topic {
        font-size: 22px;
        font-weight: 500;
        color: rgba(255,255,255,0.94);
        max-width: 80%;
        text-align: center;
        line-height: 1.55;
        letter-spacing: 0.5px;
        padding: 20px 40px;
        border-top: 1px solid rgba(201,169,97,0.4);
        border-bottom: 1px solid rgba(201,169,97,0.4);
    }
    
    .cover-footer {
        padding: 18px 20mm;
        background: linear-gradient(90deg, #F4D98A, #C9A961, #F4D98A);
        color: #0A1628;
        font-size: 10px;
        text-align: center;
        letter-spacing: 2px;
        font-weight: 700;
    }
    
    /* =========================================
       📄 내용 페이지 — 샴페인 크림 배경
       ========================================= */
    .page-header {
        padding: 15mm 15mm 10mm;
        border-bottom: 1px solid rgba(201,169,97,0.35);
        position: relative;
        display: flex;
        align-items: center;
        gap: 16px;
        background: linear-gradient(180deg, rgba(201,169,97,0.08) 0%, transparent 100%);
    }
    .page-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 180px;
        height: 2px;
        background: linear-gradient(90deg, #C9A961 0%, #F4D98A 50%, transparent 100%);
    }
    
    .header-logo {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        border: 2px solid #C9A961;
        object-fit: cover;
        background: white;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(201,169,97,0.3);
    }
    
    .section-badge {
        background: linear-gradient(135deg, #8B6F3E 0%, #C9A961 50%, #8B6F3E 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 2px;
        border: 1px solid rgba(244,217,138,0.5);
        text-transform: uppercase;
        box-shadow: 0 2px 6px rgba(139,111,62,0.25);
    }
    
    .page-title {
        font-size: 22px;
        font-weight: 800;
        color: #0F2847;
        letter-spacing: -0.4px;
        flex: 1;
    }
    
    /* =========================================
       📝 본문 — 샴페인 크림에서 고급감 업
       ========================================= */
    .page-body {
        flex: 1;
        padding: 12mm 15mm;
        font-size: 14px;
        line-height: 1.85;
        color: #3A2F1E;
        overflow: hidden;
    }
    
    .page-body p {
        margin-bottom: 11px;
    }
    
    /* 서브 섹션 제목 */
    .sub-title {
        font-size: 16px;
        font-weight: 800;
        color: #0F2847;
        margin: 22px 0 12px;
        padding: 6px 14px 6px 16px;
        border-left: 4px solid #C9A961;
        background: linear-gradient(90deg, rgba(201,169,97,0.12) 0%, transparent 80%);
        letter-spacing: -0.3px;
        border-radius: 0 6px 6px 0;
    }
    .sub-title:first-child {
        margin-top: 0;
    }
    
    /* V자 요약 박스 — 더 럭셔리하게 */
    .v-item {
        background: linear-gradient(135deg, #FFFBF0 0%, #F9F1DC 100%);
        border-left: 4px solid #C9A961;
        padding: 13px 20px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 12px;
        display: flex;
        gap: 14px;
        line-height: 1.7;
        box-shadow: 0 1px 3px rgba(139,111,62,0.08), inset 0 1px 0 rgba(255,255,255,0.6);
    }
    .v-item .v-mark {
        color: #8B6F3E;
        font-size: 20px;
        font-weight: 900;
        flex-shrink: 0;
        line-height: 1.4;
        font-family: 'Cormorant Garamond', serif;
    }
    .v-item .v-content {
        color: #2B2416;
        font-size: 13.5px;
        font-weight: 500;
    }
    .v-item .v-content strong {
        color: #0F2847;
        font-weight: 800;
        background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%);
        padding: 0 2px;
    }
    
    /* 불릿 리스트 */
    .bullet-item {
        padding: 6px 0 6px 26px;
        position: relative;
        color: #3A2F1E;
        font-size: 13.5px;
        line-height: 1.75;
    }
    .bullet-item::before {
        content: '◆';
        color: #C9A961;
        font-size: 11px;
        position: absolute;
        left: 8px;
        top: 9px;
    }
    .bullet-item strong {
        color: #0F2847;
        font-weight: 700;
        background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%);
        padding: 0 2px;
    }
    
    /* 일반 단락 */
    .body-text {
        color: #3A2F1E;
        font-size: 13.5px;
        line-height: 1.8;
        margin-bottom: 10px;
    }
    .body-text strong {
        color: #0F2847;
        font-weight: 700;
    }
    
    /* 하이라이트 박스 - 고급 네이비 */
    .highlight-box {
        background: linear-gradient(135deg, #1B3A6B, #2C5282);
        color: white;
        border-radius: 10px;
        padding: 16px 22px;
        margin: 14px 0;
        box-shadow: 0 4px 14px rgba(27,58,107,0.25);
        border: 1px solid rgba(201,169,97,0.3);
    }
    .highlight-box .hl-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #F4D98A;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .highlight-box .hl-content {
        font-size: 14px;
        line-height: 1.6;
        font-weight: 500;
    }
    
    /* =========================================
       🏷️ 하단 배너 광고
       ========================================= */
    .footer-banner {
        width: 100%;
        height: 28mm;
        object-fit: cover;
        border-top: 2px solid #C9A961;
        display: block;
        box-shadow: 0 -2px 8px rgba(201,169,97,0.15);
    }
    
    /* 페이지 번호 - 골드 프레임 */
    .page-number {
        position: absolute;
        bottom: 32mm;
        right: 12mm;
        font-size: 10px;
        color: #8B6F3E;
        font-weight: 700;
        letter-spacing: 2px;
        z-index: 10;
        font-family: 'Cormorant Garamond', serif;
    }
    .page-number::before {
        content: '— ';
        color: #C9A961;
    }
    .page-number::after {
        content: ' —';
        color: #C9A961;
    }
    """

    def render_section_body(body_text):
        """본문 텍스트를 예쁜 HTML 요소들로 변환"""
        html_parts = []
        lines = body_text.split('\n')
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                i += 1
                continue
            
            # V자 요약
            if s.startswith('V ') or s.startswith('V\t'):
                content = s[2:].strip()
                # [키워드] 강조
                content = content.replace('[', '<strong>[').replace(']', ']</strong>')
                html_parts.append(
                    f'<div class="v-item"><span class="v-mark">V</span>'
                    f'<span class="v-content">{content}</span></div>'
                )
            # 서브 섹션 제목 ("- 신청기술..." 같은 헤더)
            elif s.startswith('- 신청기술') or s.startswith('-신청기술'):
                html_parts.append(f'<div class="sub-title">{s.lstrip("-").strip()}</div>')
            # 불릿 리스트
            elif s.startswith('• ') or s.startswith('- ') or s.startswith('* '):
                content = s.lstrip('•-* ').strip()
                content = content.replace('[', '<strong>[').replace(']', ']</strong>')
                html_parts.append(f'<div class="bullet-item">{content}</div>')
            # 번호 리스트 (1. 2. 3.)
            elif len(s) >= 2 and s[0].isdigit() and s[1] == '.':
                content = s[2:].strip()
                # 제목 느낌이면 sub-title
                if len(content) < 40 and (':' in content or content.endswith('략') or content.endswith('안') or content.endswith('획')):
                    html_parts.append(f'<div class="sub-title">{s}</div>')
                else:
                    html_parts.append(f'<div class="body-text">{s}</div>')
            # 일반 텍스트
            else:
                html_parts.append(f'<div class="body-text">{s}</div>')
            i += 1
        return '\n'.join(html_parts)
    
    # HTML 조립
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>벤처인증 마스터 리포트 · {topic}</title>
<style>{css}</style>
</head>
<body>

<!-- 📕 표지 페이지 -->
<div class="page cover-page">
    <div class="corner-deco corner-tl"></div>
    <div class="corner-deco corner-tr"></div>
    <div class="corner-deco corner-bl"></div>
    <div class="corner-deco corner-br"></div>
    <div class="cover-inner">
        <img src="{LOGO_SRC}" class="cover-logo" alt="로고">
        <div class="cover-brand">RSV</div>
        <div class="cover-subbrand">Rich Secret Vault · 부자들의 비밀금고</div>
        <div class="cover-divider"></div>
        <div class="cover-title">벤처인증 마스터 컨설팅 리포트</div>
        <div class="cover-topic-label">— Subject Technology —</div>
        <div class="cover-topic">{topic}</div>
    </div>
    <div class="cover-footer">
        중소기업경영지원단 · VENTURE CERTIFICATION CONSULTING · {datetime.now().strftime('%Y.%m.%d')}
    </div>
</div>
"""

    # 본문 섹션들
    page_num = 0
    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n', 1)
        title_raw = lines[0].strip('[] #').strip()
        if not title_raw: continue
        body_text = lines[1] if len(lines) > 1 else ""
        page_num += 1
        
        # 제목에서 번호 추출 (예: "1. 신청기술 요약" → 번호="01", 제목="신청기술 요약")
        badge_text = f"CHAPTER {page_num:02d}"
        
        body_html = render_section_body(body_text)
        
        html += f"""
<!-- 📄 섹션 {page_num}: {title_raw} -->
<div class="page">
    <div class="page-header">
        <img src="{LOGO_SRC}" class="header-logo" alt="로고">
        <span class="section-badge">{badge_text}</span>
        <div class="page-title">{title_raw}</div>
    </div>
    <div class="page-body">
        {body_html}
    </div>
    <div class="page-number">{page_num:02d}</div>
    <img src="{BANNER_SRC}" class="footer-banner" alt="배너">
</div>
"""
    
    html += """
</body>
</html>"""
    return html


# =====================================================================
# 🧪 샘플 데이터 (API 호출 없이 디자인 테스트용)
# =====================================================================
def get_sample_sections():
    """프리미엄 디자인 테스트용 샘플 데이터 — Claude API 호출 없이 디자인만 확인"""
    sample_raw = """### [1. 신청기술 요약 및 표준 양식]
- 신청기술(제품/서비스)명: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술
- 신청기술(제품/서비스)요약: AI 유한요소해석(FEA) 기반 골판지 박스 구조 자동 설계 플랫폼. 10년간 축적된 실측 데이터와 머신러닝 알고리즘을 결합하여 기존 경험 의존적 설계 방식 대비 설계시간 90% 단축, 재료비 25% 절감을 실현하는 B2B SaaS 솔루션

V 기존 시장에 [박스 과잉설계로 인한 물류비 증가와 재료 낭비 문제]가 있는데, [경험 의존적 설계 관행과 개별 시험 인프라 부재]라는 이유로 중소 제조사들이 여전히 불편을 겪고 있음
V 당사에서 [유한요소해석(FEA) 기반 구조 최적화 알고리즘과 실측 데이터베이스 연계 시스템]으로 해결책을 찾았으며, 기존 시장 기술과 [설계 시간 90% 단축 + 재료비 25% 절감 + 품질 편차 80% 감소]라는 확실한 기술적 차이를 보유
V 현재 당사 보유/개발 중 기술명은 [AI 골판지 최적설계 시스템 OptiPack Pro], 전체 시장은 [국내 3.2조원, 글로벌 58조원 규모]이며 잠재 고객 니즈 충족 시 [연평균 12% 고성장] 기대
V 당사 기술은 [머신러닝 기반 구조해석 자동화 및 실시간 비용 산정 기능]을 갖고 있으며 [설계 리드타임 단축과 품질 균일화로 제조 경쟁력 강화]라는 이유로 혁신적 해결책, 잠재 고객 만족도가 높을 수 있음
V 기술에 대한 [특허 2건 출원 · 1건 등록 · 실용신안 1건 보유]이며 [전담 R&D 조직 5명(박사 2, 석사 3)] 보유, 끊임없는 R&D로 지속 발전 가능한 기술적 역량 보유
V 시장진입을 위해 [국내 주요 박람회 3회 참가 · 파일럿 고객 12개사 확보 · 대학 산학협력 5건] 진행 중, 현재 [연 매출 12억원 규모 시장 확보], 향후 [수출 시장 및 ASEAN 진출 · Series A 투자 유치] 계획 수립하여 진행 예정
V 당사 성과가 가능한 이유는 [10년 이상 축적된 포장 실측 데이터 25만 건과 포장 분야 국내 최고 수준 전문 인력]이 있기 때문이며 향후 [3년 내 매출 3배 성장, 수출 비중 40% 달성]의 공격적 성장을 해낼 것임

### [2. 개발배경 및 원인분석]
• 국내 포장산업은 약 40조원 규모로 성장하고 있으나, 골판지 박스 설계는 여전히 경험 의존적 방식에 머물러 있어 설계 효율성이 현저히 낮음
• 대기업 물류사들은 연간 수백억 원을 박스 과잉설계로 낭비하고 있으며, 이는 ESG 경영 기조와도 정면으로 배치되는 구조적 문제
• 2023년 이후 친환경 규제 강화(EU CBAM, 국내 포장재 재질 규제)로 재료 절감 요구가 급증하고 있으며, 구조해석 기반 최적화 기술의 필요성이 전례 없이 대두됨
• 기존 설계 소프트웨어는 대부분 해외 제품(독일 TOPS, 미국 Artios CAD 등)이며 고가·복잡·한글 미지원으로 국내 중소 제조사의 실질적 접근성이 매우 낮은 실정
• 당사는 이러한 시장 격차를 해소하고 국내 포장 산업의 디지털 전환을 선도하기 위해 본 기술 개발에 착수

### [3. 경쟁력 확보방안]
1. 독자적 AI 알고리즘: 10년 이상 축적된 실측 데이터 25만 건 기반의 머신러닝 모델로 해외 경쟁사 대비 한국 골판지 사양 적합도 30% 이상 우위
2. 설계 리드타임 혁신적 단축: 기존 2주 소요 공정을 1일 이내로 단축하여 고객사의 시장 대응력을 극대화
3. 압도적 비용 구조 우위: 해외 솔루션 대비 1/3 수준의 가격대로 중소 제조사의 진입장벽을 완전히 해소
4. 지속적 기술 고도화: 전담 R&D 조직 운영으로 매년 2회 이상 알고리즘 업데이트 및 신규 기능 추가
5. 국내 최초 한글 완벽 지원: 한국 포장 업계 용어와 KS 규격을 100% 반영한 UI/UX 설계

### [4. 추진경과 및 향후 계획]
1. 2022년 1분기: 기술 기획 수립 및 핵심 알고리즘 프로토타입 개발 착수
2. 2022년 4분기: 알고리즘 검증 완료 및 실증 테스트 착수
3. 2023년 2분기: 특허 출원 2건 및 첫 상업 버전 Alpha 출시
4. 2023년 4분기: 국내 파일럿 고객 3개사 확보 및 피드백 반영
5. 2024년 2분기: 정식 제품 출시 및 국내 박람회 3회 참가
6. 2024년 4분기: 12개 기업과 정식 계약 체결, 연 매출 12억원 달성
7. 2025년 계획: 동남아(베트남·태국) 수출 개시 및 AI 정확도 추가 고도화
8. 2026년 계획: Series A 투자 유치 (목표 50억원) 및 글로벌 진출 본격화

### [5. 목표시장 및 고객정의]
• 1차 타겟(Primary): 국내 중소 골판지 제조사 약 3,500개사 — 시장 규모 1조원, 초기 2년간 집중 공략
• 2차 타겟(Secondary): 중견 물류기업 및 이커머스 포장 담당 — 시장 규모 8,000억원, 3년차부터 확대
• 3차 타겟(Tertiary): ASEAN 지역(베트남·태국·인도네시아) 포장 기업 — 시장 규모 2.5조원, 수출 본격화
• 핵심 페인포인트 분석: 재료비 절감(ROI 12개월), 설계 시간 단축(생산성 5배), 품질 균일화(불량률 80% 감소)
• 고객 의사결정 프로세스: 경영진(비용/ROI), 설계팀(사용 편의성), 품질팀(신뢰도) 3단 어프로치"""
    return sample_raw.split('### ')


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
# 🎨 Streamlit 메인 UI
# =====================================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    
    .stApp {
        background: #f0f2f5;
        font-family: 'Pretendard Variable', 'Noto Sans KR', sans-serif;
    }
    
    /* 메인 헤더 - 다크네이비 + 골드 */
    .dash-header {
        background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%);
        color: white;
        padding: 30px 40px;
        border-radius: 16px;
        border-bottom: 4px solid #C9A961;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .dash-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 60%;
        height: 200%;
        background: radial-gradient(ellipse, rgba(201,169,97,0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    .dash-header h1 {
        color: white !important;
        font-weight: 900 !important;
        letter-spacing: -0.5px;
        margin: 0 !important;
        font-size: 26px !important;
    }
    .dash-header .brand-tag {
        display: inline-block;
        background: linear-gradient(180deg, #F4D98A, #C9A961, #8B6F3E);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        letter-spacing: 4px;
        font-size: 14px;
        margin-bottom: 4px;
    }
    .dash-header p {
        color: rgba(255,255,255,0.75);
        margin: 6px 0 0 !important;
        font-size: 13px;
    }
    
    /* 섹션 타이틀 카드 */
    .sec-title {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #C9A961;
        color: #0F2847;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: -0.3px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* 복사 라벨 */
    .copy-label {
        font-weight: 800;
        color: #0F2847;
        margin: 18px 0 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        padding-left: 10px;
        border-left: 3px solid #C9A961;
    }
    
    /* primary 버튼 - 골드 그라디언트 */
    [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #C9A961 0%, #A37C3E 100%) !important;
        color: #0A1628 !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(201,169,97,0.3) !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 4px 14px rgba(201,169,97,0.45) !important;
        transform: translateY(-1px);
    }
    
    /* 추천 카드 */
    .rec-card {
        background: linear-gradient(135deg, #FCFDFE 0%, #F0F4F9 100%);
        border: 1px solid #D0D9E3;
        border-left: 4px solid #C9A961;
        border-radius: 10px;
        padding: 16px 18px;
        margin: 10px 0;
    }
    .rec-card-title {
        font-size: 15px;
        font-weight: 800;
        color: #0F2847;
        margin-bottom: 6px;
    }
    .rec-card-desc {
        font-size: 13px;
        color: #4A5568;
        line-height: 1.6;
    }
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: #0A1628 !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(201,169,97,0.1) !important;
        border: 1px solid rgba(201,169,97,0.3) !important;
        color: #C9A961 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# 로그인
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

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
    st.markdown("### 🎨 디자인 미리보기")
    st.caption("API 호출 없이 샘플 데이터로 HTML 디자인만 확인하고 싶으실 때 사용하세요. 비용이 전혀 들지 않습니다.")
    if st.button("🧪 샘플 데이터로 미리보기", use_container_width=True):
        st.session_state.sections = get_sample_sections()
        st.session_state.step2_topic = "데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술"
        st.rerun()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-title">📋 Step 1 · 기술 주제 추천</div>', unsafe_allow_html=True)
    biz_type = st.radio("업종 선택", ["일반제조", "IT/SW", "초기창업"], horizontal=True)
    if st.button("✨ AI 주제 추천", type="primary", use_container_width=True):
        with st.spinner("AI가 분석 중입니다..."):
            res = claude_generate(
                f"{biz_type} 업종 벤처인증용 구체적 기술 주제 3개를 제안해줘. "
                f'JSON 형식으로만 출력: {{"suggestions":[{{"tech_name":"...","reason":"..."}},...]}}',
                max_tokens=2000
            )
            try:
                clean = res.replace('```json', '').replace('```', '').strip()
                st.session_state.suggestions = json.loads(clean)
            except:
                st.error("추천 결과 파싱에 실패했습니다. 원문을 확인해주세요.")
                st.code(res)
    
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

with col2:
    st.markdown('<div class="sec-title">📑 Step 2 · 마스터 리포트 생성</div>', unsafe_allow_html=True)
    topic = st.text_input(
        "확정된 기술명",
        value=st.session_state.get('step2_topic', ''),
        placeholder="여기에 기술명을 입력하거나 Step 1에서 선택하세요"
    )
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not topic:
            st.warning("기술명을 먼저 입력해주세요.")
        else:
            with st.spinner("리포트를 생성 중입니다 (약 30~60초 소요)..."):
                prompt = f"""
기술명: [{topic}]

이 기술에 대해 벤처인증 심사용 사업계획서 11개 항목을 아주 구체적으로 작성하라.

[중요 규칙]
1. 벤처인증 사이트 복사용이므로 '표(Table)'는 절대 사용하지 마라. 모든 설명은 '•' 또는 '1. 2. 3.' 텍스트로 풀어써라.
2. 항목별로 반드시 '### [번호. 항목명]'으로 구분하라.
3. 1번 항목에는 반드시 'V자 요약' 7문장을 포함하라 (V로 시작).
4. 수치는 일반적 업계 표현만, 지어낸 숫자 금지.

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
                res = claude_generate(prompt, max_tokens=8192)
                st.session_state.report = res
                st.session_state.sections = res.split('### ')

# =====================================================================
# 결과 출력 영역
# =====================================================================
if "sections" in st.session_state:
    st.divider()
    st.markdown('<div class="sec-title">📄 생성 결과 · 다운로드 및 복사</div>', unsafe_allow_html=True)
    
    topic_display = topic if topic else st.session_state.get('step2_topic', '샘플')
    
    # HTML 다운로드
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
        st.caption("💡 다운받은 HTML을 브라우저로 열고 Ctrl+P → PDF 저장하면 A4 리포트 완성!")
    
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
