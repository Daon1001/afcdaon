import streamlit as st

def get_venture_strategy(biz_item):
    """
    종목명을 분석하여 업종별 맞춤 전략을 반환합니다.
    """
    # 1. 업종별 전략 사전 (제조업 핵심 분야 확장)
    db = {
        "기계/장비": {
            "keywords": ["기계", "장비", "설비", "금형", "자동화"],
            "tech_theme": "지능형 자동화 및 스마트 팩토리 시스템",
            "topics": ["고정밀 센서를 결합한 자율 제어형 제조 시스템", "에너지 효율 최적화를 위한 지능형 공정 설비"],
            "patents": ["제어 알고리즘", "센서 모듈", "정밀 구동부"]
        },
        "금속/창호": {
            "keywords": ["창호", "샤시", "금속", "알루미늄", "철강"],
            "tech_theme": "고기능성 건축 소재 및 에너지 절감 구조체",
            "topics": ["열손실 최소화 하이브리드 창호 시스템", "내구성이 강화된 고강도 경량 금속 프레임"],
            "patents": ["단열 구조", "결합 기구", "표면 처리법"]
        },
        "식품/바이오": {
            "keywords": ["식품", "가공", "음료", "바이오", "화장품"],
            "tech_theme": "바이오 융합 소재 및 스마트 패키징 기술",
            "topics": ["천연 추출물을 활용한 기능성 소재 상용화", "보존 성능이 향상된 친환경 스마트 패키징"],
            "patents": ["추출 공법", "조성물 특허", "신선도 유지 기술"]
        },
        "IT/소프트웨어": {
            "keywords": ["소프트웨어", "IT", "플랫폼", "데이터", "앱"],
            "tech_theme": "데이터 기반 AI 솔루션 및 클라우드 서비스",
            "topics": ["빅데이터 분석을 통한 비즈니스 최적화 알고리즘", "보안성이 강화된 클라우드 기반 협업 솔루션"],
            "patents": ["데이터 처리 로직", "인증 보안 체계"]
        }
    }

    # 2. 키워드 매칭 로직
    for category, content in db.items():
        if any(key in biz_item for key in content["keywords"]):
            return content

    # 3. 매칭되는 업종이 없을 경우 기본 반환값
    return {
        "tech_theme": "범용 제조 혁신 기술",
        "topics": [f"{biz_item} 공정의 디지털 전환 솔루션", f"차세대 {biz_item} 핵심 부품 제조 기술"],
        "patents": ["공정 개선", "효율화 기술"]
    }

# --- Streamlit UI 연동 ---
st.title("🎯 컨설턴트용 벤처 주제 선정 도구")
biz_item_input = st.text_input("대표님 사업자등록증상 '종목'을 입력하세요", "자동차 부품 제조")

if biz_item_input:
    strategy = get_venture_strategy(biz_item_input)
    
    st.markdown(f"### 📍 [{biz_item_input}] 분석 결과")
    st.info(f"**권장 기술 테마:** {strategy['tech_theme']}")
    
    st.write("**추천 벤처인증 주제:**")
    for topic in strategy['topics']:
        st.success(f"📌 {topic}")
        
    st.write(f"**필요 특허 키워드:** {', '.join(strategy['patents'])}")
