"""
app.py - Haii-Call 음성 대화 앱
모바일 친화적 UI - 실제 전화 앱 느낌

실행: streamlit run app.py
"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import time
import logging
import threading
import base64
from html import escape
from dotenv import load_dotenv

# 로그 숨기기
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)

from audio_recorder_streamlit import audio_recorder

from STT import STT
from LLM import LLM
from TTS import TTS

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# 페이지 설정
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Haii-Call",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════
# CSS - 모바일 친화적 + 전화 앱 스타일
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* 모바일 최적화 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 다크 테마 */
    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(34, 197, 94, 0.08), transparent 26%),
                    radial-gradient(circle at 80% 0%, rgba(59, 130, 246, 0.08), transparent 26%),
                    #05070f;
    }
    
    /* Streamlit 기본 요소 숨김 */
    header, footer, #MainMenu, .stDeployButton { display: none !important; }
    .block-container { 
        padding: 0.75rem !important;
        max-width: 460px !important;
        min-height: 100vh;
    }
    
    /* 로딩 카드 */
    .loading-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 32px 18px 26px;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.35);
        text-align: center;
    }
    
    .loader {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        border: 6px solid rgba(255,255,255,0.08);
        border-top-color: #22c55e;
        animation: spin 1s linear infinite;
        margin: 0 auto 14px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* 상단 상태바 - 박스 제거, 텍스트만 */
    .status-bar {
        text-align: center;
        padding: 12px 0;
        margin-bottom: 8px;
    }
    
    .status-connected {
        color: #22c55e;
        font-size: 14px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #22c55e;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .call-timer {
        color: white;
        font-size: 28px;
        font-weight: 700;
        margin: 4px 0;
    }
    
    /* AI 프로필 */
    .ai-profile {
        text-align: center;
        padding: 16px;
    }
    
    .ai-avatar {
        width: 90px;
        height: 90px;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 45px;
        margin-bottom: 10px;
        box-shadow: 0 8px 32px rgba(34, 197, 94, 0.3);
    }
    
    .ai-name {
        color: white;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    
    .ai-role {
        color: #9ca3af;
        font-size: 13px;
    }
    
    /* AI 상태 표시 - 박스 제거, 텍스트만 */
    .ai-state-text {
        text-align: center;
        padding: 8px 0;
        font-size: 14px;
        color: #9ca3af;
    }
    
    .ai-state-text.listening { color: #3b82f6; }
    .ai-state-text.thinking { color: #a855f7; }
    .ai-state-text.speaking { color: #22c55e; }
    
    /* 대화 영역 */
    .chat-area {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 16px;
        padding: 14px;
        margin: 8px 0 16px 0;
        min-height: 140px;
        max-height: 40vh;
        overflow-y: auto;
        overflow-x: hidden;
    }
    
    /* 마이크 영역 */
    .mic-section {
        background: transparent;
        text-align: center;
        padding: 8px 0;
    }
    
    /* 메시지 버블 */
    .message {
        margin: 10px 0;
        display: flex;
        flex-direction: column;
    }
    
    .message-user {
        align-items: flex-end;
    }
    
    .message-ai {
        align-items: flex-start;
    }
    
    .message-label {
        font-size: 11px;
        color: #6b7280;
        margin-bottom: 3px;
        padding: 0 10px;
    }
    
    .message-bubble {
        max-width: 85%;
        padding: 11px 15px;
        border-radius: 18px;
        font-size: 14px;
        line-height: 1.5;
        word-wrap: break-word;
    }
    
    .bubble-user {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border-bottom-right-radius: 6px;
    }
    
    .bubble-ai {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border-bottom-left-radius: 6px;
    }
    
    .record-hint {
        color: #9ca3af;
        font-size: 14px;
        text-align: center;
        margin-top: 12px;
    }
    
    /* ═══ 마이크 버튼 스타일 ═══ */
    
    /* 컨테이너 - 완전 투명 */
    .stAudioRecorder,
    .stAudioRecorder > div,
    .stAudioRecorder > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .stAudioRecorder {
        display: flex !important;
        justify-content: center !important;
        padding: 20px 0 !important;
    }
    
    /* 원형 마이크 버튼 */
    .stAudioRecorder button {
        width: 80px !important;
        height: 80px !important;
        min-width: 80px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4) !important;
        transition: all 0.15s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        cursor: pointer !important;
    }
    
    .stAudioRecorder button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 8px 28px rgba(34, 197, 94, 0.5) !important;
    }
    
    .stAudioRecorder button:active {
        transform: scale(0.95) !important;
    }
    
    /* 마이크 아이콘 - 크고 흰색 */
    .stAudioRecorder button svg {
        width: 36px !important;
        height: 36px !important;
        color: white !important;
        fill: white !important;
    }
    
    /* 녹음 중 - 빨간색 + 펄스 */
    .stAudioRecorder button[data-testid="stop"],
    .stAudioRecorder button[aria-pressed="true"] {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4) !important;
        animation: recording-pulse 1s ease-in-out infinite !important;
    }
    
    @keyframes recording-pulse {
        0%, 100% { box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 8px 28px rgba(239, 68, 68, 0.6); }
    }
    
    /* 오디오 플레이어 숨김 */
    .stAudioRecorder audio {
        display: none !important;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 16px !important;
        font-weight: 700 !important;
        padding: 14px 32px !important;
        font-size: 16px !important;
        min-height: 52px;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #22c55e, #16a34a) !important;
        border: none !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #6b7280, #4b5563) !important;
        border: none !important;
        color: white !important;
    }
    
    /* 대기/수신 화면 */
    .welcome-screen {
        text-align: center;
        padding: 50px 20px;
    }
    
    .welcome-icon {
        font-size: 70px;
        margin-bottom: 20px;
    }
    
    .welcome-title {
        color: white;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    
    .welcome-subtitle {
        color: #9ca3af;
        font-size: 15px;
        margin-bottom: 40px;
    }
    
    /* 수신 화면 애니메이션 */
    .incoming-avatar {
        width: 110px;
        height: 110px;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 55px;
        margin-bottom: 18px;
        animation: ring 1.5s ease-in-out infinite;
    }
    
    @keyframes ring {
        0%, 100% { 
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 0 20px rgba(34, 197, 94, 0);
            transform: scale(1.02);
        }
    }
    
    /* 모바일 반응형 */
    @media (max-width: 768px) {
        .block-container {
            padding: 0.5rem !important;
        }
        
        .call-timer {
            font-size: 24px;
        }
        
        .ai-avatar {
            width: 75px;
            height: 75px;
            font-size: 38px;
        }
        
        .message-bubble {
            max-width: 90%;
            font-size: 13px;
        }
        
        .chat-area {
            max-height: 260px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 세션 상태 초기화
# ═══════════════════════════════════════════════════════════════════════════
def init_session():
    """세션 상태 초기화"""
    defaults = {
        'state': 'idle',           # idle, loading, ringing, connecting_call, connected
        'ai_state': 'idle',        # idle, listening, thinking, speaking
        'messages': [],
        'start_time': None,
        'last_audio': None,
        'tts_audio': None,         # TTS 오디오 (브라우저 재생용)
        'live_text': '',
        'loading_started_at': None,
        'accepted_started_at': None,
        'greeting_done': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ═══════════════════════════════════════════════════════════════════════════
# 모듈 로드 (캐시 사용, 오류 방지)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_stt():
    """STT 모듈 로드"""
    try:
        return STT()
    except Exception as e:
        logging.error(f"STT 초기화 실패: {e}")
        return None

@st.cache_resource(show_spinner=False)
def get_llm():
    """LLM 모듈 로드"""
    try:
        return LLM()
    except Exception as e:
        logging.error(f"LLM 초기화 실패: {e}")
        return None

@st.cache_resource(show_spinner=False)
def get_tts():
    """TTS 모듈 로드"""
    try:
        return TTS(voice="female_warm", rate="-5%")
    except Exception as e:
        logging.error(f"TTS 초기화 실패: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 유틸리티 함수
# ═══════════════════════════════════════════════════════════════════════════
def get_duration() -> str:
    """통화 시간 계산"""
    if st.session_state.start_time:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        return f"{mins:02d}:{secs:02d}"
    return "00:00"


def reset_call_state():
    """통화 상태 초기화"""
    # LLM 대화 컨텍스트도 초기화
    llm = get_llm()
    if llm:
        llm.reset()
    
    st.session_state.state = 'idle'
    st.session_state.ai_state = 'idle'
    st.session_state.messages = []
    st.session_state.start_time = None
    st.session_state.last_audio = None
    st.session_state.live_text = ''
    st.session_state.loading_started_at = None
    st.session_state.accepted_started_at = None
    st.session_state.greeting_done = False


def process_audio(audio_bytes: bytes):
    """음성 처리 (STT → LLM → TTS)"""
    if not audio_bytes or len(audio_bytes) < 1000:
        st.session_state.live_text = ""
        return
    
    stt = get_stt()
    llm = get_llm()
    tts = get_tts()
    
    if not stt or not llm or not tts:
        st.session_state.live_text = "모듈 로드 실패"
        return
    
    # STT - 음성 인식
    st.session_state.ai_state = 'listening'
    st.session_state.live_text = "말씀 인식 중..."
    
    text = stt.transcribe(audio_bytes, mime_type="audio/wav")
    if not text:
        st.session_state.ai_state = 'idle'
        st.session_state.live_text = ""
        return
    
    st.session_state.live_text = text
    st.session_state.messages.append({'role': 'user', 'text': text})
    
    # LLM - 응답 생성
    st.session_state.ai_state = 'thinking'
    response = llm.generate(text)
    if not response:
        response = "죄송해요, 다시 말씀해 주시겠어요?"
    
    st.session_state.messages.append({'role': 'ai', 'text': response})
    
    # TTS - 음성 합성 (브라우저에서 재생)
    st.session_state.ai_state = 'speaking'
    try:
        audio = asyncio.run(tts.synthesize(response))
        if audio:
            st.session_state.tts_audio = audio
    except Exception as e:
        logging.error(f"TTS 합성 오류: {e}")
    finally:
        st.session_state.ai_state = 'idle'
        st.session_state.live_text = ""


# ═══════════════════════════════════════════════════════════════════════════
# 화면 렌더링 함수
# ═══════════════════════════════════════════════════════════════════════════
def render_idle():
    """대기 화면"""
    st.markdown('''
        <div class="welcome-screen">
            <div class="welcome-icon">📞</div>
            <div class="welcome-title">Haii-Call</div>
            <div class="welcome-subtitle">경도인지장애 어르신을 위한<br>AI 건강 도우미</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📞 전화 걸기", type="primary", use_container_width=True):
            st.session_state.state = 'loading'
            st.session_state.loading_started_at = time.time()
            st.rerun()


def render_loading():
    """로딩 화면"""
    started = st.session_state.loading_started_at or time.time()
    
    # 1.2초 후 수신 화면으로 전환
    if time.time() - started > 1.2:
        st.session_state.state = 'ringing'
        st.session_state.loading_started_at = None
        st.rerun()
    
    st.markdown('''
        <div class="welcome-screen">
            <div class="loading-card">
                <div class="loader"></div>
                <div class="welcome-title">연결 중...</div>
                <div class="welcome-subtitle">조금만 기다려 주세요</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    time.sleep(0.25)
    st.rerun()


def render_ringing():
    """수신 화면"""
    st.markdown('''
        <div class="welcome-screen">
            <div class="incoming-avatar">😊</div>
            <div class="welcome-title">하이</div>
            <div class="welcome-subtitle">AI 건강도우미가 전화했어요</div>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("❌ 거절", use_container_width=True):
            reset_call_state()
            st.rerun()
    with col3:
        if st.button("📞 받기", type="primary", use_container_width=True):
            st.session_state.state = 'connecting_call'
            st.session_state.accepted_started_at = time.time()
            st.session_state.greeting_done = False
            st.rerun()


def render_connecting_call():
    """통화 연결 중 화면"""
    started = st.session_state.accepted_started_at or time.time()
    
    # 0.8초 후 인사말 재생 및 통화 시작
    if (time.time() - started) > 0.8 and not st.session_state.greeting_done:
        st.session_state.start_time = time.time()
        
        llm = get_llm()
        tts = get_tts()
        
        if llm and tts:
            greeting = llm.get_greeting()
            st.session_state.messages.append({'role': 'ai', 'text': greeting})
            
            try:
                audio = asyncio.run(tts.synthesize(greeting))
                if audio:
                    st.session_state.tts_audio = audio  # 브라우저에서 재생
            except Exception as e:
                logging.error(f"인사말 합성 오류: {e}")
        
        st.session_state.greeting_done = True
        st.session_state.state = 'connected'
        st.rerun()
    
    st.markdown('''
        <div class="welcome-screen">
            <div class="loading-card">
                <div class="loader"></div>
                <div class="welcome-title">연결 중...</div>
                <div class="welcome-subtitle">통화에 연결하고 있어요</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    time.sleep(0.25)
    st.rerun()


def render_connected():
    """통화 화면"""
    # 상단 상태바 (박스 없이 텍스트만)
    st.markdown(f'''
        <div class="status-bar">
            <div class="status-connected">
                <span class="status-dot"></span>
                통화 중
            </div>
            <div class="call-timer">{get_duration()}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # AI 프로필
    st.markdown('''
        <div class="ai-profile">
            <div class="ai-avatar">😊</div>
            <div class="ai-name">하이</div>
            <div class="ai-role">AI 건강도우미</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # AI 상태 (박스 없이 텍스트만)
    ai_state = st.session_state.ai_state
    state_map = {
        'idle': ('💬 연결 완료', ''),
        'listening': ('👂 듣고 있어요...', 'listening'),
        'thinking': ('🧠 생각하고 있어요...', 'thinking'),
        'speaking': ('🗣️ 말하고 있어요...', 'speaking'),
    }
    state_text, state_class = state_map.get(ai_state, state_map['idle'])
    
    st.markdown(f'''
        <div class="ai-state-text {state_class}">{state_text}</div>
    ''', unsafe_allow_html=True)
    
    # 대화 영역 - 하나의 완전한 HTML 블록으로 생성
    messages_html = []
    for msg in st.session_state.messages[-6:]:
        role = msg['role']
        text = escape(msg['text'])
        
        if role == 'user':
            messages_html.append(f'<div class="message message-user"><div class="message-label">👵 할머니</div><div class="message-bubble bubble-user">{text}</div></div>')
        else:
            messages_html.append(f'<div class="message message-ai"><div class="message-label">🤖 하이</div><div class="message-bubble bubble-ai">{text}</div></div>')
    
    chat_content = ''.join(messages_html)
    st.markdown(f'<div class="chat-area">{chat_content}</div>', unsafe_allow_html=True)
    
    # 음성 입력 버튼 (아이콘만)
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#22c55e",
        icon_name="microphone",
        icon_size="3x",
        pause_threshold=2.0,
        sample_rate=16000,
        key="voice_recorder"
    )
    
    # 음성 처리
    if audio_bytes and audio_bytes != st.session_state.last_audio:
        st.session_state.last_audio = audio_bytes
        process_audio(audio_bytes)
        st.rerun()
    
    # TTS 오디오 재생 (st.audio 사용 - 브라우저 호환)
    if st.session_state.tts_audio:
        st.audio(st.session_state.tts_audio, format="audio/mp3", autoplay=True)
        st.session_state.tts_audio = None
    
    # 종료 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("통화 끝내기", type="secondary", use_container_width=True):
            reset_call_state()
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════════════════════
def main():
    """메인 함수"""
    state = st.session_state.state
    
    if state == 'idle':
        render_idle()
    elif state == 'loading':
        render_loading()
    elif state == 'ringing':
        render_ringing()
    elif state == 'connecting_call':
        render_connecting_call()
    elif state == 'connected':
        render_connected()


if __name__ == "__main__":
    main()
