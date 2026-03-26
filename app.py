import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
import os
import json
import hashlib
from datetime import datetime, date

# PDF 처리를 위한 라이브러리
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [0. 페이지 설정] ---
st.set_page_config(
    page_title="벤처인증 AI 마스터 컨설턴트",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 🔒 영구 저장 시스템 (JSON 기반 - CSV보다 안정적)
# Streamlit Cloud 재배포 시에도 session_state 캐시 활용
# =====================================================================
DB_FILE = "user_database.json"
BACKUP_KEY = "db_backup_state"

def get_default_db():
    """기본 관리자 계정이 포함된 초기 DB"""
    return {
        "users": {
            "incheon00@gmail.com": {
                "approved": True,
                "is_admin": True,
                "created_at": "2026-02-14",
                "usage_count": 0,
                "last_reset_month": date.today().month
            },
            "임원근@gmail.com": {
                "approved": True,
                "is_admin": True,
                "created_at": "2026-02-14",
                "usage_count": 0,
                "last_reset_month": date.today().month
            }
        },
        "last_updated": datetime.now().isoformat()
    }

def load_db():
    """JSON DB 로드 - 파일 → session_state 캐시 순으로 복구"""
    # 1순위: 파일에서 로드
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
            # session_state에도 백업 저장
            st.session_state[BACKUP_KEY] = json.dumps(db, ensure_ascii=False)
            return db
        except (json.JSONDecodeError, Exception):
            pass
    
    # 2순위: session_state 백업에서 복구
    if BACKUP_KEY in st.session_state:
        try:
            db = json.loads(st.session_state[BACKUP_KEY])
            save_db(db)  # 파일로 재저장
            return db
        except Exception:
            pass
    
    # 3순위: 초기 DB 생성
    db = get_default_db()
    save_db(db)
    return db

def save_db(db):
    """DB를 파일과 session_state 양쪽에 동시 저장 (이중 백업)"""
    db["last_updated"] = datetime.now().isoformat()
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # session_state에도 항상 백업
    st.session_state[BACKUP_KEY] = json.dumps(db, ensure_ascii=False)

def get_user(db, email):
    return db["users"].get(email)

def reset_monthly_usage(db):
    """매월 1일 사용량 자동 초기화"""
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

# --- DB 로드 및 월간 초기화 ---
user_db = load_db()
user_db = reset_monthly_usage(user_db)

# =====================================================================
# 💎 프리미엄 커스텀 CSS
# =====================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=Playfair+Display:wght@700;900&display=swap');

/* ── 전역 리셋 ── */
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 1200px !important;
}
header[data-testid="stHeader"] { display: none !important; }

.stApp {
    background: #f0f2f5 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* ── 로그인 화면 ── */
.login-wrapper {
    min-height: 92vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(160deg, #0b1f52 0%, #1a3a7a 40%, #2a5298 100%);
    border-radius: 0;
    margin: -1rem -1rem 0 -1rem;
    padding: 2rem;
}

.login-card {
    background: rgba(255,255,255,0.97);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 48px 44px 40px;
    max-width: 440px;
    width: 100%;
    box-shadow: 0 32px 64px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.1);
    position: relative;
    overflow: hidden;
}
.login-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 5px;
    background: linear-gradient(90deg, #d4af37, #f0d060, #d4af37);
}

.login-badge {
    display: inline-block;
    background: #0b1f52;
    color: #d4af37;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    padding: 6px 16px;
    border-radius: 20px;
    margin-bottom: 20px;
    text-transform: uppercase;
}

.login-heading {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 900;
    color: #0b1f52;
    margin: 0 0 4px;
    line-height: 1.2;
}
.login-sub {
    color: #6b7280;
    font-size: 14px;
    margin-bottom: 28px;
    font-weight: 400;
}

/* ── 대시보드 헤더 ── */
.dash-header {
    background: linear-gradient(135deg, #0b1f52 0%, #1a3a7a 60%, #2a5298 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
    border-bottom: 4px solid #d4af37;
}
.dash-header::after {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(212,175,55,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.dash-header h1 {
    color: white;
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 900;
    margin: 0;
    position: relative;
    z-index: 1;
}
.dash-header p {
    color: rgba(255,255,255,0.75);
    font-size: 14px;
    margin: 6px 0 0;
    position: relative;
    z-index: 1;
}
.dash-header .gold-line {
    color: #d4af37;
    font-weight: 700;
}

/* ── 섹션 카드 ── */
.section-card {
    background: white;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid #e5e7eb;
    margin-bottom: 16px;
}
.section-card h3 {
    font-size: 17px;
    font-weight: 700;
    color: #0b1f52;
    margin: 0 0 18px;
    padding-bottom: 12px;
    border-bottom: 2px solid #f0f2f5;
}

/* ── AI 결과 카드 ── */
.result-card {
    background: linear-gradient(135deg, #fefce8 0%, #fffdf5 100%);
    border: 1px solid #e5d9a8;
    border-left: 5px solid #d4af37;
    border-radius: 12px;
    padding: 24px;
    margin-top: 16px;
    line-height: 1.85;
    color: #1f2937;
    font-size: 14.5px;
}
.result-card h4 {
    color: #92700c;
    font-size: 15px;
    font-weight: 700;
    margin: 0 0 12px;
}

/* ── 리포트 카드 ── */
.report-section {
    background: white;
    border: 1px solid #e5e7eb;
    border-left: 5px solid #0b1f52;
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 10px;
    line-height: 1.85;
    font-size: 14.5px;
    color: #374151;
}

/* ── V자 요약 양식 ── */
.v-summary-box {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
    border: 2px solid #c7d2fe;
    border-radius: 14px;
    padding: 24px;
    margin: 16px 0;
}
.v-summary-box .v-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 13.5px;
    line-height: 1.7;
    color: #374151;
}
.v-summary-box .v-marker {
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    background: #0b1f52;
    color: #d4af37;
    font-weight: 900;
    font-size: 14px;
    border-radius: 6px;
    margin-top: 2px;
}
.v-summary-title {
    font-size: 15px;
    font-weight: 700;
    color: #0b1f52;
    margin-bottom: 14px;
}

/* ── 사이드바 스타일 ── */
section[data-testid="stSidebar"] {
    background: #0b1f52 !important;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: white !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.2) !important;
}

/* ── 버튼 오버라이드 ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #d4af37 0%, #b8952e 100%) !important;
    color: #0b1f52 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(212,175,55,0.35) !important;
}

/* ── 인풋 필드 ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 10px !important;
    border: 1.5px solid #d1d5db !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #d4af37 !important;
    box-shadow: 0 0 0 2px rgba(212,175,55,0.15) !important;
}

/* ── 익스팬더 ── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 14.5px !important;
    color: #0b1f52 !important;
}

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #c4c4c4; border-radius: 3px; }

/* ── 백업 알림 배너 ── */
.backup-alert {
    background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
    border: 1px solid #f59e0b;
    border-left: 5px solid #f59e0b;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.backup-alert .alert-icon {
    font-size: 24px;
    flex-shrink: 0;
}
.backup-alert .alert-text {
    font-size: 13.5px;
    color: #92400e;
    line-height: 1.6;
}
.backup-alert .alert-text b {
    color: #78350f;
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
if 'last_backup_date' not in st.session_state:
    st.session_state.last_backup_date = None
if 'backup_dismissed' not in st.session_state:
    st.session_state.backup_dismissed = False

MAX_MONTHLY_LIMIT = 30
AUTO_BACKUP_INTERVAL_DAYS = 3  # 3일마다 백업 알림

# =====================================================================
# 🔐 로그인 화면
# =====================================================================
if st.session_state.authenticated_user is None:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown("""
            <div class="login-card">
                <div style="text-align:center;">
                    <span class="login-badge">VENTURE CERTIFICATION</span>
                    <div class="login-heading">중소기업경영지원단</div>
                    <div class="login-sub">벤처인증 AI 마스터 컨설턴트</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        login_email = st.text_input(
            "이메일", 
            placeholder="example@gmail.com",
            label_visibility="collapsed"
        ).strip().lower()
        
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
                    "approved": False,
                    "is_admin": False,
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "usage_count": 0,
                    "last_reset_month": date.today().month
                }
                save_db(user_db)
                st.success("📩 승인 신청이 완료되었습니다. 관리자 승인 후 이용 가능합니다.")
            elif login_email in user_db["users"]:
                st.warning("이미 등록된 이메일입니다.")
            else:
                st.warning("이메일을 입력해주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# =====================================================================
# ✅ 로그인 성공 → 메인 대시보드
# =====================================================================
current_user_email = st.session_state.authenticated_user
current_user = get_user(user_db, current_user_email)

if not current_user:
    st.session_state.authenticated_user = None
    st.rerun()

# --- 사이드바 ---
with st.sidebar:
    st.markdown(f"""
        <div style="padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.15); margin-bottom: 16px;">
            <div style="font-size: 12px; color: rgba(255,255,255,0.5); letter-spacing: 2px; text-transform: uppercase;">접속 계정</div>
            <div style="font-size: 15px; font-weight: 600; margin-top: 4px;">{current_user_email}</div>
        </div>
    """, unsafe_allow_html=True)
    
    usage = current_user.get("usage_count", 0)
    progress = min(usage / MAX_MONTHLY_LIMIT, 1.0)
    st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 6px;">월간 사용량</div>
            <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #d4af37, #f0d060); width: {progress*100}%; height: 100%; border-radius: 8px; transition: width 0.3s;"></div>
            </div>
            <div style="font-size: 13px; margin-top: 4px; color: rgba(255,255,255,0.7);">{usage} / {MAX_MONTHLY_LIMIT} 회</div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()

    # --- 관리자 패널 ---
    if current_user.get("is_admin"):
        st.divider()
        st.markdown("""
            <div style="font-size: 12px; color: #d4af37; letter-spacing: 2px; font-weight: 700; margin-bottom: 12px;">
                👑 관리자 패널
            </div>
        """, unsafe_allow_html=True)
        
        if 'admin_msg' in st.session_state:
            st.success(st.session_state.admin_msg)
            del st.session_state.admin_msg
        
        with st.expander("회원 승인 관리", expanded=True):
            user_list = []
            for email, info in user_db["users"].items():
                user_list.append({
                    "이메일": email,
                    "승인": "✅" if info.get("approved") else "⏳",
                    "사용량": info.get("usage_count", 0),
                    "가입일": info.get("created_at", "-")
                })
            if user_list:
                st.dataframe(pd.DataFrame(user_list), use_container_width=True, hide_index=True)
            
            target = st.selectbox("대상 선택", list(user_db["users"].keys()))
            c1, c2 = st.columns(2)
            if c1.button("✅ 승인", use_container_width=True, key="admin_approve"):
                user_db["users"][target]["approved"] = True
                save_db(user_db)
                st.session_state.admin_msg = f"'{target}' 승인 완료!"
                st.rerun()
            if c2.button("🚫 해제", use_container_width=True, key="admin_revoke"):
                user_db["users"][target]["approved"] = False
                save_db(user_db)
                st.session_state.admin_msg = f"'{target}' 승인 해제됨"
                st.rerun()
        
        with st.expander("🔐 DB 백업 / 복구", expanded=False):
            # ── 백업 필요성 안내 ──
            st.markdown("""
                <div style="background: rgba(255,200,50,0.15); border: 1px solid rgba(255,200,50,0.3); border-radius: 8px; padding: 12px; margin-bottom: 14px; font-size: 12.5px; color: #ffd700;">
                    ⚠️ <b>Streamlit Cloud는 서버 재배포 시 파일이 초기화됩니다.</b><br>
                    회원 데이터를 안전하게 보존하려면 정기적으로 백업 파일을 다운로드하세요.
                </div>
            """, unsafe_allow_html=True)
            
            # ── 현재 DB 상태 요약 ──
            total_users = len(user_db["users"])
            approved_count = sum(1 for u in user_db["users"].values() if u.get("approved"))
            pending_count = total_users - approved_count
            last_updated = user_db.get("last_updated", "알 수 없음")
            last_backup = st.session_state.get("last_backup_date", "백업 기록 없음")
            
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; margin-bottom: 14px; font-size: 12px; line-height: 1.8;">
                    📊 총 회원: <b>{total_users}명</b> (승인 {approved_count} / 대기 {pending_count})<br>
                    🕐 DB 최종 수정: <b>{last_updated[:16] if len(str(last_updated)) > 16 else last_updated}</b><br>
                    💾 마지막 백업: <b>{last_backup if last_backup else '아직 백업하지 않음'}</b>
                </div>
            """, unsafe_allow_html=True)
            
            # ── 1. 즉시 백업 다운로드 ──
            st.markdown("**1단계: 백업 파일 다운로드**", help="클릭하면 현재 회원 DB가 JSON 파일로 다운로드됩니다.")
            db_json = json.dumps(user_db, ensure_ascii=False, indent=2)
            backup_filename = f"venture_db_backup_{date.today().strftime('%Y%m%d')}.json"
            
            if st.download_button(
                "📥 지금 백업 다운로드",
                db_json,
                file_name=backup_filename,
                mime="application/json",
                use_container_width=True,
                key="backup_download_main"
            ):
                st.session_state.last_backup_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.backup_dismissed = True
            
            # ── 2. Google Drive 자동 보관 가이드 ──
            st.divider()
            st.markdown("**2단계: Google Drive에 보관 (권장)**")
            st.markdown("""
                <div style="background: rgba(255,255,255,0.06); border-radius: 8px; padding: 12px; font-size: 11.5px; line-height: 1.9; color: rgba(255,255,255,0.8);">
                    ① 위 버튼으로 <b>.json 파일</b>을 다운로드<br>
                    ② <a href="https://drive.google.com" target="_blank" style="color: #d4af37;">Google Drive</a>에 <b>'벤처인증_백업'</b> 폴더를 만들어 업로드<br>
                    ③ 서버 초기화 시 아래 복구 기능으로 즉시 복원 가능<br>
                    <span style="color: #d4af37;">💡 TIP: 매주 월요일 백업을 습관화하세요!</span>
                </div>
            """, unsafe_allow_html=True)
            
            # ── 3. 백업 복구 ──
            st.divider()
            st.markdown("**3단계: 백업 파일로 복구**")
            uploaded_db = st.file_uploader(
                "📤 백업 JSON 파일 업로드", 
                type=["json"], 
                key="db_restore",
                help="이전에 다운로드한 .json 백업 파일을 선택하세요."
            )
            if uploaded_db:
                # 업로드된 파일 미리보기
                try:
                    preview_data = json.loads(uploaded_db.read())
                    uploaded_db.seek(0)  # 읽기 위치 리셋
                    if "users" in preview_data:
                        preview_count = len(preview_data["users"])
                        preview_updated = preview_data.get("last_updated", "알 수 없음")
                        st.markdown(f"""
                            <div style="background: rgba(100,200,100,0.15); border: 1px solid rgba(100,200,100,0.3); border-radius: 8px; padding: 10px; font-size: 12px; margin-bottom: 8px;">
                                ✅ 유효한 백업 파일<br>
                                👥 회원 수: <b>{preview_count}명</b> | 🕐 백업 시점: <b>{str(preview_updated)[:16]}</b>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🚨 이 백업으로 전체 DB 덮어쓰기", type="primary", use_container_width=True):
                            save_db(preview_data)
                            st.session_state.admin_msg = f"✅ DB 복구 완료! ({preview_count}명 회원 데이터 복원)"
                            st.rerun()
                    else:
                        st.error("❌ 올바른 백업 파일 형식이 아닙니다. 'users' 키가 필요합니다.")
                except json.JSONDecodeError:
                    st.error("❌ JSON 파일을 읽을 수 없습니다. 파일이 손상되었을 수 있습니다.")
            
            # ── 4. 자동 백업 주기 설정 ──
            st.divider()
            st.markdown("**⚙️ 백업 알림 설정**")
            backup_interval = st.select_slider(
                "백업 알림 주기",
                options=[1, 2, 3, 5, 7],
                value=3,
                format_func=lambda x: f"{x}일마다",
                key="backup_interval_slider"
            )
            if backup_interval:
                st.session_state["auto_backup_interval"] = backup_interval
                st.caption(f"📅 {backup_interval}일마다 로그인 시 백업 알림이 표시됩니다.")

# --- Gemini API 설정 ---
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
    st.error(f"⚠️ Google AI 서버 통신 오류: {e}")
    st.stop()

target_model_name = ""
for preferred in ['gemini-2.0-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision', 'gemini-pro']:
    if preferred in available_models:
        target_model_name = preferred
        break
if not target_model_name and available_models:
    target_model_name = available_models[0]

model = genai.GenerativeModel(target_model_name)
st.sidebar.caption(f"🤖 엔진: `{target_model_name}`")

# =====================================================================
# 🏛️ 대시보드 헤더
# =====================================================================
st.markdown("""
    <div class="dash-header">
        <h1>🏛️ 벤처인증 통합 컨설팅 대시보드</h1>
        <p><span class="gold-line">중소기업경영지원단</span> · AI 마스터 컨설턴트 시스템</p>
    </div>
""", unsafe_allow_html=True)

# =====================================================================
# 🔔 관리자 자동 백업 알림 시스템
# =====================================================================
if current_user.get("is_admin") and not st.session_state.get("backup_dismissed"):
    backup_interval = st.session_state.get("auto_backup_interval", AUTO_BACKUP_INTERVAL_DAYS)
    last_backup = st.session_state.get("last_backup_date")
    show_backup_alert = False
    
    if last_backup is None:
        # 한 번도 백업한 적 없음
        show_backup_alert = True
        alert_reason = "아직 한 번도 백업하지 않았습니다."
    else:
        try:
            last_dt = datetime.strptime(last_backup, "%Y-%m-%d %H:%M")
            days_since = (datetime.now() - last_dt).days
            if days_since >= backup_interval:
                show_backup_alert = True
                alert_reason = f"마지막 백업 후 {days_since}일이 경과했습니다."
        except ValueError:
            show_backup_alert = True
            alert_reason = "백업 날짜를 확인할 수 없습니다."
    
    if show_backup_alert:
        backup_col1, backup_col2 = st.columns([5, 1])
        with backup_col1:
            st.warning(f"""
                🔔 **DB 백업이 필요합니다!** — {alert_reason}  
                서버 초기화 시 회원 데이터가 유실될 수 있습니다. 좌측 사이드바 **관리자 패널 → DB 백업/복구**에서 백업해주세요.
            """)
        with backup_col2:
            st.write("")
            if st.button("✕ 닫기", key="dismiss_backup_alert"):
                st.session_state.backup_dismissed = True
                st.rerun()

if st.button("🔄 새 기업 컨설팅 시작"):
    for key in ['suggestions', 'report_sections']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.uploader_key = str(int(st.session_state.uploader_key) + 1)
    st.rerun()

# =====================================================================
# 메인 2단 레이아웃
# =====================================================================
col1, col2 = st.columns(2, gap="large")

# --- 좌측: 분석 및 기술 추천 ---
with col1:
    st.markdown("""
        <div class="section-card">
            <h3>📋 Step 1 · 분석 및 기술 주제 추천</h3>
        </div>
    """, unsafe_allow_html=True)
    
    biz_type = st.radio("업종 선택", ["일반 기업", "IT / SW", "초기기업"], horizontal=True)
    uploaded_file = st.file_uploader(
        "사업자등록증 업로드 (JPG, PNG, PDF)",
        type=["jpg", "png", "pdf"],
        key=f"up_{st.session_state.uploader_key}"
    )
    
    analysis_content = None
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.type == "application/pdf":
            analysis_content = {"mime_type": "application/pdf", "data": file_bytes}
        else:
            analysis_content = Image.open(uploaded_file)
    
    user_guide_rec = st.text_area(
        "추천 가이드 (선택)",
        placeholder="예: ESG 강조, 수출 중심, 특정 산업 키워드 등",
        key=f"gr_{st.session_state.uploader_key}",
        height=80
    )
    
    if st.button("✨ AI 기술 주제 추천 받기", type="primary", use_container_width=True):
        if current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 사용 한도를 초과했습니다.")
        else:
            with st.spinner('AI가 최적의 기술 주제를 분석하고 있습니다...'):
                prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다.
[{biz_type}] 분야 기업에 대해 벤처인증에 적합한 기술 주제 3개를 추천해주세요.
각 주제에 대해 ① 기술명 ② 추천 사유 ③ 벤처인증 적합도를 설명하세요.
{f'추가 요청사항: {user_guide_rec}' if user_guide_rec else ''}
"""
                content = [prompt, analysis_content] if analysis_content else prompt
                try:
                    response = model.generate_content(content)
                    st.session_state.suggestions = response.text
                    user_db["users"][current_user_email]["usage_count"] = current_user.get("usage_count", 0) + 1
                    save_db(user_db)
                    st.rerun()
                except Exception as e:
                    if "ResourceExhausted" in str(e) or "429" in str(e):
                        st.error("⏳ Google AI 서버 한도 초과입니다. 1~2분 후 다시 시도해주세요.")
                    else:
                        st.error(f"⚠️ 오류 발생: {e}")
    
    if 'suggestions' in st.session_state:
        st.markdown(f"""
            <div class="result-card">
                <h4>💡 AI 추천 기술 주제</h4>
                {st.session_state.suggestions.replace(chr(10), "<br>")}
            </div>
        """, unsafe_allow_html=True)

# --- 우측: 마스터 리포트 ---
with col2:
    st.markdown("""
        <div class="section-card">
            <h3>📑 Step 2 · 마스터 리포트 생성</h3>
        </div>
    """, unsafe_allow_html=True)
    
    selected_topic = st.text_input(
        "확정 기술(제품/서비스)명",
        placeholder="예: 데이터기반 고강도·경량화 골판지 박스 구조 최적화 설계 기술",
        key=f"topic_{st.session_state.uploader_key}"
    )
    
    user_guide_rep = st.text_area(
        "리포트 추가 지시사항 (선택)",
        placeholder="예: 시장규모 숫자 강조, 특허 전략 중시 등",
        key=f"gp_{st.session_state.uploader_key}",
        height=80
    )
    
    if st.button("🚀 마스터 리포트 생성", type="primary", use_container_width=True):
        if not selected_topic:
            st.warning("기술(제품/서비스)명을 입력해주세요.")
        elif current_user.get("usage_count", 0) >= MAX_MONTHLY_LIMIT:
            st.error("월간 사용 한도를 초과했습니다.")
        else:
            with st.spinner('마스터 리포트를 생성하고 있습니다... (30초~1분 소요)'):
                form_prompt = f"""당신은 20년 경력의 벤처인증 전문 컨설턴트입니다. 아래 확정된 기술에 대해 벤처인증용 마스터 리포트를 작성하세요.

확정 기술(제품/서비스)명: [{selected_topic}]
{f'추가 지시사항: {user_guide_rep}' if user_guide_rep else ''}

⚠️ 중요 규칙:
- 지어낸 숫자 금지 (시장규모 등은 공신력 있는 출처 명시)
- 각 항목은 구체적이고 논리적으로 서술
- 아래 V자 요약 양식을 [1. 신청기술 요약 및 표준 양식] 항목에 반드시 포함

[V자 요약 양식 - 반드시 아래 형식으로 작성]
- 신청기술(제품/서비스)명: {selected_topic}
- 신청기술(제품/서비스)요약: (제품 특성 및 기술 요약을 간략하게 작성)
V 기존 시장에 [문제점]이 있는데, [기존 업체들의 한계]라는 이유로 사람들이 여전히 필요로 하고(불편을 겪고) 있음
V 당사에서 [해결 방법]으로 해결책을 찾았으며, 이는 기존 시장의 기술과 [차별점]이라는 확실한 기술적 차이를 보유하고 있음
V 현재 당사에서 보유 또는 개발 중인 기술명은 [기술명]으로써, 전체 시장은 [시장 규모]이며 이 기술로 잠재 고객들의 니즈를 충족시킬 경우 [성장 전망]을 기대할 수 있음
V 당사 기술은 [핵심 특징]을 갖고 있으며 [고객 가치]라는 이유로 기존 문제에 대한 혁신적인 해결책으로, 잠재 고객들의 만족도가 훨씬 높을 수 있음
V 기술에 대한 [지식재산권 현황]이며 [연구개발 조직]을 보유하여 끊임없는 연구개발에 노력하고 있으며, 지속 발전이 가능한 기술적 역량을 보유하고 있음
V 기술을 통한 시장진입을 위해 [마케팅 활동 현황]을 진행 중으로 현재 [현재 시장 확보 규모]의 시장을 확보하고 있으며, 시장 확대를 위해 [향후 마케팅 계획]을 수립하여 진행할 계획
V 당사가 제시하는 이러한 성과가 가능한 이유는 당사에 [핵심 역량]이 있기 때문이며 이를 더욱 강화하여 향후 [성장 목표]의 공격적인 성장을 해낼 것임

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
                try:
                    response = model.generate_content(content)
                    st.session_state.report_sections = response.text.split('### ')
                    user_db["users"][current_user_email]["usage_count"] = current_user.get("usage_count", 0) + 1
                    save_db(user_db)
                    st.rerun()
                except Exception as e:
                    if "ResourceExhausted" in str(e) or "429" in str(e):
                        st.error("⏳ 서버 한도 초과입니다. 리포트는 자원을 많이 사용하므로 2분 후 재시도해주세요.")
                    else:
                        st.error(f"⚠️ 오류 발생: {e}")

# =====================================================================
# 📄 리포트 결과 출력
# =====================================================================
if 'report_sections' in st.session_state:
    st.divider()
    
    st.markdown("""
        <div class="section-card">
            <h3>📄 마스터 리포트 결과</h3>
        </div>
    """, unsafe_allow_html=True)
    
    full_report = "\n\n".join(st.session_state.report_sections)
    
    r1, r2 = st.columns([1, 3])
    with r1:
        st.download_button(
            "💾 전체 리포트 다운로드 (.txt)",
            full_report,
            file_name=f"벤처리포트_{selected_topic or 'report'}.txt",
            use_container_width=True
        )
    
    for section in st.session_state.report_sections:
        if section.strip():
            lines = section.split('\n', 1)
            title = lines[0].strip('[] #')
            body = lines[1] if len(lines) > 1 else ""
            if title.strip():
                with st.expander(f"📌 {title}", expanded=False):
                    # V자 요약이 포함된 첫 번째 섹션은 특별 렌더링
                    if "신청기술 요약" in title or "표준 양식" in title:
                        # V 마커가 있는 줄을 특별 처리
                        formatted_body = ""
                        for line in body.split('\n'):
                            stripped = line.strip()
                            if stripped.startswith('V ') or stripped.startswith('V\u3000'):
                                formatted_body += f'<div class="v-summary-box"><div class="v-row"><span class="v-marker">V</span><span>{stripped[2:]}</span></div></div>'
                            elif stripped.startswith('- 신청기술') or stripped.startswith('-신청기술'):
                                formatted_body += f'<div style="font-weight:600; color:#0b1f52; margin:6px 0;">{stripped}</div>'
                            else:
                                formatted_body += f'{stripped}<br>'
                        st.markdown(f'<div class="report-section">{formatted_body}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="report-section">{body.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

# --- 하단 푸터 ---
st.markdown("""
    <div style="text-align: center; padding: 32px 0 16px; color: #9ca3af; font-size: 12px;">
        © 2026 중소기업경영지원단 · 벤처인증 AI 마스터 컨설턴트
    </div>
""", unsafe_allow_html=True)
