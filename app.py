"""
app.py - Haii-Call 음성 대화 앱
Deepgram STT + Edge TTS
"""
import streamlit as st
import asyncio
import sys
import time
import base64
from html import escape
from dotenv import load_dotenv

# Windows 이벤트 루프 정책
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
# CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Noto Sans KR', sans-serif; }
    
    .stApp {
        background: linear-gradient(180deg, #0a0f1a 0%, #111827 100%);
    }
    
    header, footer, #MainMenu, .stDeployButton { display: none !important; }
    .block-container { 
        padding: 1rem !important;
        max-width: 480px !important;
    }
    
    /* 상태바 */
    .status-bar { text-align: center; padding: 16px 0; }
    .status-text {
        color: #22c55e; font-size: 14px; font-weight: 600;
        display: flex; align-items: center; justify-content: center; gap: 8px;
    }
    .status-dot {
        width: 8px; height: 8px; background: #22c55e;
        border-radius: 50%; animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    .timer { color: white; font-size: 32px; font-weight: 700; margin-top: 4px; }
    
    /* AI 프로필 */
    .profile { text-align: center; padding: 20px 0; }
    .avatar {
        width: 100px; height: 100px;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 50px; margin-bottom: 12px;
        box-shadow: 0 8px 32px rgba(34, 197, 94, 0.3);
    }
    .name { color: white; font-size: 24px; font-weight: 700; }
    .role { color: #9ca3af; font-size: 14px; margin-top: 4px; }
    
    /* 상태 표시 */
    .ai-state { text-align: center; padding: 12px 0; font-size: 15px; color: #9ca3af; }
    .ai-state.listening { color: #3b82f6; }
    .ai-state.thinking { color: #a855f7; }
    .ai-state.speaking { color: #22c55e; }
    
    /* 대화창 */
    .chat {
        background: rgba(255,255,255,0.03);
        border-radius: 20px; padding: 16px;
        margin: 12px 0; min-height: 120px; max-height: 35vh;
        overflow-y: auto;
    }
    .msg { margin: 12px 0; display: flex; flex-direction: column; }
    .msg-user { align-items: flex-end; }
    .msg-ai { align-items: flex-start; }
    .msg-label { font-size: 11px; color: #6b7280; margin-bottom: 4px; padding: 0 12px; }
    .bubble {
        max-width: 85%; padding: 12px 16px;
        border-radius: 20px; font-size: 15px; line-height: 1.5;
    }
    .bubble-user {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white; border-bottom-right-radius: 6px;
    }
    .bubble-ai {
        background: rgba(255,255,255,0.08);
        color: white; border-bottom-left-radius: 6px;
    }
    
    /* 마이크 버튼 스타일 */
    .stAudioRecorder {
        display: flex !important;
        justify-content: center !important;
        padding: 16px 0 !important;
    }
    .stAudioRecorder > div { background: transparent !important; }
    .stAudioRecorder button {
        width: 80px !important; height: 80px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #22c55e, #16a34a) !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4) !important;
    }
    .stAudioRecorder button:hover {
        transform: scale(1.05) !important;
    }
    .stAudioRecorder button svg {
        width: 36px !important; height: 36px !important;
        fill: white !important;
    }
    .stAudioRecorder audio { display: none !important; }
    
    /* 버튼 */
    .stButton > button {
        border-radius: 16px !important; font-weight: 600 !important;
        padding: 14px 32px !important; font-size: 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #22c55e, #16a34a) !important;
        border: none !important;
    }
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #4b5563, #374151) !important;
        border: none !important; color: white !important;
    }
    
    /* 시작 화면 */
    .welcome { text-align: center; padding: 60px 20px; }
    .welcome-icon { font-size: 80px; margin-bottom: 24px; }
    .welcome-title { color: white; font-size: 36px; font-weight: 700; }
    .welcome-sub { color: #9ca3af; font-size: 16px; margin: 8px 0 48px; }
    
    /* 수신 화면 */
    .incoming {
        width: 120px; height: 120px;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 60px; margin-bottom: 20px;
        animation: ring 1.5s ease-in-out infinite;
    }
    @keyframes ring {
        0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); transform: scale(1); }
        50% { box-shadow: 0 0 0 24px rgba(34,197,94,0); transform: scale(1.03); }
    }
    
    /* 오디오 플레이어 숨김 */
    .stAudio { display: none !important; }
    
    .hint { color: #6b7280; font-size: 13px; text-align: center; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 세션 상태
# ═══════════════════════════════════════════════════════════════════════════
if 'state' not in st.session_state:
    st.session_state.state = 'idle'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'last_audio' not in st.session_state:
    st.session_state.last_audio = None
if 'tts_audio' not in st.session_state:
    st.session_state.tts_audio = None
if 'tts_key' not in st.session_state:
    st.session_state.tts_key = 0

# ═══════════════════════════════════════════════════════════════════════════
# 모듈 로드
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_stt():
    try:
        return STT()
    except:
        return None

@st.cache_resource(show_spinner=False)
def get_llm():
    try:
        return LLM()
    except:
        return None

@st.cache_resource(show_spinner=False)
def get_tts():
    try:
        return TTS(voice="female_warm", rate="-5%")
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════════
# 유틸리티
# ═══════════════════════════════════════════════════════════════════════════
def get_time():
    if st.session_state.start_time:
        s = int(time.time() - st.session_state.start_time)
        return f"{s//60:02d}:{s%60:02d}"
    return "00:00"

def reset():
    llm = get_llm()
    if llm: llm.reset()
    st.session_state.state = 'idle'
    st.session_state.messages = []
    st.session_state.start_time = None
    st.session_state.last_audio = None
    st.session_state.tts_audio = None

def synthesize_and_play(text):
    """TTS 합성 후 재생 준비"""
    tts = get_tts()
    if tts and text:
        try:
            audio = asyncio.run(tts.synthesize(text))
            if audio:
                st.session_state.tts_audio = audio
                st.session_state.tts_key += 1
        except Exception as e:
            print(f"TTS 오류: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# 화면
# ═══════════════════════════════════════════════════════════════════════════
def page_idle():
    st.markdown('''
        <div class="welcome">
            <div class="welcome-icon">📞</div>
            <div class="welcome-title">Haii-Call</div>
            <div class="welcome-sub">AI 건강 도우미와 대화해요</div>
        </div>
    ''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("📞 전화 걸기", type="primary", use_container_width=True):
            st.session_state.state = 'ringing'
            st.rerun()


def page_ringing():
    st.markdown('''
        <div class="welcome">
            <div class="incoming">😊</div>
            <div class="welcome-title">하이</div>
            <div class="welcome-sub">AI 건강도우미가 전화했어요</div>
        </div>
    ''', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("❌ 거절", use_container_width=True):
            reset()
            st.rerun()
    with c3:
        if st.button("📞 받기", type="primary", use_container_width=True):
            st.session_state.start_time = time.time()
            llm = get_llm()
            if llm:
                greeting = llm.get_greeting()
                st.session_state.messages.append({'role': 'ai', 'text': greeting})
                # 인사말 TTS
                synthesize_and_play(greeting)
            st.session_state.state = 'call'
            st.rerun()


def page_call():
    # 상태바
    st.markdown(f'''
        <div class="status-bar">
            <div class="status-text"><span class="status-dot"></span>통화 중</div>
            <div class="timer">{get_time()}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # 프로필
    st.markdown('''
        <div class="profile">
            <div class="avatar">😊</div>
            <div class="name">하이</div>
            <div class="role">AI 건강도우미</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # AI 상태
    st.markdown('<div class="ai-state">💬 마이크를 누르고 말씀하세요</div>', unsafe_allow_html=True)
    
    # 대화
    html = []
    for m in st.session_state.messages[-6:]:
        t = escape(m['text'])
        if m['role'] == 'user':
            html.append(f'<div class="msg msg-user"><div class="msg-label">👵 나</div><div class="bubble bubble-user">{t}</div></div>')
        else:
            html.append(f'<div class="msg msg-ai"><div class="msg-label">🤖 하이</div><div class="bubble bubble-ai">{t}</div></div>')
    st.markdown(f'<div class="chat">{"".join(html)}</div>', unsafe_allow_html=True)
    
    # 마이크 버튼
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#22c55e",
        icon_name="microphone",
        icon_size="3x",
        pause_threshold=2.0,
        sample_rate=16000,
        key="mic"
    )
    
    st.markdown('<div class="hint">버튼을 누르고 말씀하세요</div>', unsafe_allow_html=True)
    
    # 음성 처리
    if audio_bytes and audio_bytes != st.session_state.last_audio:
        st.session_state.last_audio = audio_bytes
        
        stt = get_stt()
        llm = get_llm()
        
        if stt and llm:
            # STT
            text = stt.transcribe(audio_bytes, mime_type="audio/wav")
            
            if text:
                st.session_state.messages.append({'role': 'user', 'text': text})
                
                # LLM
                response = llm.generate(text)
                if response:
                    st.session_state.messages.append({'role': 'ai', 'text': response})
                    # TTS
                    synthesize_and_play(response)
        
        st.rerun()
    
    # TTS 오디오 재생 (autoplay)
    if st.session_state.tts_audio:
        audio_b64 = base64.b64encode(st.session_state.tts_audio).decode()
        
        # JavaScript로 자동 재생
        st.markdown(f'''
            <audio id="tts-{st.session_state.tts_key}" autoplay>
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
            <script>
                var audio = document.getElementById("tts-{st.session_state.tts_key}");
                if (audio) {{
                    audio.play().catch(function(e) {{
                        console.log("Autoplay blocked:", e);
                    }});
                }}
            </script>
        ''', unsafe_allow_html=True)
        
        # 재생 후 초기화
        st.session_state.tts_audio = None
    
    # 종료 버튼
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("통화 끝내기", type="secondary", use_container_width=True):
            reset()
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════════════════════
def main():
    s = st.session_state.state
    if s == 'idle': page_idle()
    elif s == 'ringing': page_ringing()
    elif s == 'call': page_call()

if __name__ == "__main__":
    main()
