"""
app.py - Haii-Call (Polished UI)
Streamlit Native Chat + 완성도 높은 마이크 버튼 디자인
"""
import asyncio
import sys
import streamlit as st
import time
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

# 모듈 임포트
from STT import STT
from LLM import LLM
from TTS import TTS

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
# CSS (마이크 버튼 완성도 높이기)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* 전체 폰트 및 배경 */
    .stApp {
        background-color: #111111;
        color: white;
    }
    
    /* 오디오 플레이어 숨기기 */
    audio { display: none; }
    
    /* 헤더 숨김 */
    header { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* 일반 버튼 스타일 */
    .stButton > button {
        border-radius: 20px;
        height: 50px;
        font-weight: bold;
    }

    /* --- 마이크 버튼 전용 스타일 --- */
    /* audio_recorder_streamlit 라이브러리의 버튼을 타겟팅 */
    .stAudioRecorder > button {
        background-color: #1f1f1f !important; /* 어두운 원형 배경 */
        border: 1px solid #333 !important;     /* 테두리 */
        border-radius: 50% !important;         /* 완전한 원형 */
        width: 60px !important;                /* 고정 크기 */
        height: 60px !important;
        padding: 0 !important;                 /* 패딩 제거 (아이콘 중앙 정렬) */
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important; /* 그림자 효과 */
        transition: all 0.2s ease-in-out !important; /* 부드러운 전환 */
        margin: auto !important; /* 중앙 정렬 */
    }

    /* 마이크 버튼 호버 효과 */
    .stAudioRecorder > button:hover {
         background-color: #2a2a2a !important;
         transform: scale(1.05) !important; /* 살짝 커짐 */
         box-shadow: 0 6px 12px rgba(0,0,0,0.4) !important;
    }

    /* 마이크 버튼 클릭(녹음중) 효과 */
    .stAudioRecorder > button:active {
         transform: scale(0.95) !important; /* 살짝 눌림 */
         background-color: #111 !important;
    }
    
    /* 녹음 중일 때 아이콘 색상 변경 (라이브러리 내부 동작에 의존) */
    .stAudioRecorder > button[title="Stop recording"] {
        border-color: #ff4b4b !important;
        background-color: rgba(255, 75, 75, 0.1) !important;
    }

    /* 하단 입력창 컨테이너 정렬 */
    [data-testid="column"]:has(.stAudioRecorder) {
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 세션 & 모듈
# ═══════════════════════════════════════════════════════════════════════════
if 'state' not in st.session_state:
    st.session_state.state = 'idle'
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_audio' not in st.session_state:
    st.session_state.last_audio = None

@st.cache_resource
def load_modules():
    return STT(), LLM(), TTS(voice="female_warm", rate="-5%")

# ═══════════════════════════════════════════════════════════════════════════
# 로직 함수
# ═══════════════════════════════════════════════════════════════════════════
def process_audio(audio_bytes):
    if not audio_bytes or len(audio_bytes) < 1000: return

    stt, llm, tts = load_modules()

    # 1. STT
    text = stt.transcribe(audio_bytes, mime_type="audio/wav")
    if not text: return
    
    st.session_state.messages.append({'role': 'user', 'text': text})

    # 2. LLM
    response = llm.generate(text)
    st.session_state.messages.append({'role': 'ai', 'text': response})

    # 3. TTS
    audio_data = asyncio.run(tts.synthesize(response))
    if audio_data:
        st.session_state['autoplay_audio'] = audio_data

# ═══════════════════════════════════════════════════════════════════════════
# 메인 화면
# ═══════════════════════════════════════════════════════════════════════════
def main():
    # --- 1. 대기 화면 ---
    if st.session_state.state == 'idle':
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("https://cdn-icons-png.flaticon.com/512/724/724664.png", width=100)
            st.markdown("<h1 style='text-align: center; color: #4ADE80;'>Haii-Call</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray;'>AI 손녀와 대화하기</p>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("📞 전화 걸기", type="primary", use_container_width=True):
                st.session_state.state = 'connected'
                st.session_state.start_time = time.time()
                
                # 첫 인사
                stt, llm, tts = load_modules()
                greeting = llm.get_greeting()
                st.session_state.messages.append({'role': 'ai', 'text': greeting})
                
                audio = asyncio.run(tts.synthesize(greeting))
                if audio:
                    st.session_state['autoplay_audio'] = audio
                st.rerun()

    # --- 2. 통화 화면 ---
    elif st.session_state.state == 'connected':
        # 상단 헤더
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background: #222; border-radius: 10px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #4ADE80;">통화 중</h3>
            <p style="margin: 0; color: gray;">{get_duration()}</p>
        </div>
        """, unsafe_allow_html=True)

        # 채팅 영역
        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.messages:
                if msg['role'] == 'user':
                    with st.chat_message("user", avatar="👵"):
                        st.write(msg['text'])
                else:
                    with st.chat_message("assistant", avatar="👧"):
                        st.write(msg['text'])
            
            # 오디오 자동 재생
            if 'autoplay_audio' in st.session_state:
                st.audio(st.session_state['autoplay_audio'], format="audio/mp3", autoplay=True)
                del st.session_state['autoplay_audio']

        # 하단 컨트롤
        st.markdown("---")
        
        # [변경] 마이크 버튼 영역을 좀 더 넓게 잡음
        col1, col2 = st.columns([1.2, 3.8])
        
        with col1:
            # 마이크 버튼 (CSS로 스타일링됨)
            audio_bytes = audio_recorder(
                text="", 
                recording_color="#ff4b4b", # 녹음 중일 때 아이콘 색상
                neutral_color="#3b82f6",   # 대기 중일 때 아이콘 색상
                icon_size="2x",
                sample_rate=16000
            )
            
        with col2:
            text_input = st.chat_input("메시지 입력...", key="chat_input")

        # 로직 실행
        if audio_bytes and audio_bytes != st.session_state.last_audio:
            st.session_state.last_audio = audio_bytes
            with st.spinner("듣고 있어요..."):
                process_audio(audio_bytes)
            st.rerun()

        if text_input:
            st.session_state.messages.append({'role': 'user', 'text': text_input})
            stt, llm, tts = load_modules()
            response = llm.generate(text_input)
            st.session_state.messages.append({'role': 'ai', 'text': response})
            
            audio = asyncio.run(tts.synthesize(response))
            if audio:
                st.session_state['autoplay_audio'] = audio
            st.rerun()

        # 종료 버튼
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("통화 종료", type="secondary", use_container_width=True):
            st.session_state.state = 'idle'
            st.session_state.messages = []
            st.rerun()

def get_duration():
    if st.session_state.start_time:
        elapsed = int(time.time() - st.session_state.start_time)
        mins, secs = divmod(elapsed, 60)
        return f"{mins:02d}:{secs:02d}"
    return "00:00"

if __name__ == "__main__":
    main()