"""
app.py - Haii-Call 음성 대화 앱
Web Speech API 기반 실시간 음성 대화
"""
import streamlit as st
import time
from html import escape
from dotenv import load_dotenv

from LLM import LLM

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
    .state { text-align: center; padding: 12px 0; font-size: 15px; color: #9ca3af; }
    .state.listening { color: #3b82f6; }
    .state.thinking { color: #a855f7; }
    .state.speaking { color: #22c55e; }
    
    /* 대화창 */
    .chat {
        background: rgba(255,255,255,0.03);
        border-radius: 20px; padding: 16px;
        margin: 12px 0; min-height: 160px; max-height: 45vh;
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
    
    /* 실시간 텍스트 */
    .live { text-align: center; color: #60a5fa; font-size: 14px; min-height: 20px; padding: 8px 0; }
    
    /* 마이크 버튼 */
    .mic-area { text-align: center; padding: 16px 0; }
    .mic {
        width: 88px; height: 88px;
        border-radius: 50%; border: none;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        box-shadow: 0 8px 24px rgba(34, 197, 94, 0.4);
        cursor: pointer; transition: all 0.2s;
        display: inline-flex; align-items: center; justify-content: center;
    }
    .mic:hover { transform: scale(1.05); }
    .mic:active { transform: scale(0.95); }
    .mic.on {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.4);
        animation: rec 1s ease-in-out infinite;
    }
    @keyframes rec {
        0%,100% { box-shadow: 0 8px 24px rgba(239,68,68,0.4); }
        50% { box-shadow: 0 12px 32px rgba(239,68,68,0.6); }
    }
    .mic svg { width: 40px; height: 40px; fill: white; }
    .hint { color: #6b7280; font-size: 13px; margin-top: 12px; }
    
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

# ═══════════════════════════════════════════════════════════════════════════
# LLM
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def get_llm():
    try:
        return LLM()
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
    
    # 대화
    html = []
    for m in st.session_state.messages[-6:]:
        t = escape(m['text'])
        if m['role'] == 'user':
            html.append(f'<div class="msg msg-user"><div class="msg-label">👵 나</div><div class="bubble bubble-user">{t}</div></div>')
        else:
            html.append(f'<div class="msg msg-ai"><div class="msg-label">🤖 하이</div><div class="bubble bubble-ai">{t}</div></div>')
    st.markdown(f'<div class="chat">{"".join(html)}</div>', unsafe_allow_html=True)
    
    # 마지막 AI 메시지 (TTS용)
    last_ai = ""
    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'ai':
        last_ai = st.session_state.messages[-1]['text']
    
    # 음성 UI
    st.markdown(f'''
        <div class="state" id="state">💬 마이크를 누르고 말씀하세요</div>
        <div class="live" id="live"></div>
        <div class="mic-area">
            <button class="mic" id="mic" onclick="toggle()">
                <svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z"/></svg>
            </button>
            <div class="hint">버튼을 누르고 말씀하세요</div>
        </div>
        
        <script>
            let rec = null, on = false, txt = '';
            
            // Edge, Chrome 둘 다 지원
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SR) {{
                rec = new SR();
                rec.lang = 'ko-KR';
                rec.continuous = true;
                rec.interimResults = true;
                
                rec.onresult = e => {{
                    let tmp = '';
                    for (let i = e.resultIndex; i < e.results.length; i++) {{
                        if (e.results[i].isFinal) txt += e.results[i][0].transcript;
                        else tmp += e.results[i][0].transcript;
                    }}
                    document.getElementById('live').textContent = txt + tmp;
                }};
                
                rec.onend = () => {{
                    if (on) {{
                        try {{ rec.start(); }} catch(e) {{}}
                    }} else if (txt.trim()) {{
                        send(txt.trim());
                    }}
                }};
                
                rec.onerror = e => {{
                    console.log('음성 인식 오류:', e.error);
                    if (e.error === 'not-allowed') {{
                        alert('마이크 권한을 허용해주세요!');
                    }}
                    on = false;
                    document.getElementById('mic').classList.remove('on');
                }};
            }}
            
            function toggle() {{
                if (on) stop(); else start();
            }}
            
            function start() {{
                if (!rec) {{
                    alert('이 브라우저는 음성 인식을 지원하지 않습니다. Chrome 또는 Edge를 사용해주세요.');
                    return;
                }}
                on = true; txt = '';
                document.getElementById('mic').classList.add('on');
                document.getElementById('state').textContent = '👂 듣고 있어요...';
                document.getElementById('state').className = 'state listening';
                document.getElementById('live').textContent = '';
                try {{
                    rec.start();
                }} catch(e) {{
                    console.log('시작 오류:', e);
                }}
            }}
            
            function stop() {{
                on = false;
                document.getElementById('mic').classList.remove('on');
                document.getElementById('state').textContent = '🧠 생각하고 있어요...';
                document.getElementById('state').className = 'state thinking';
                if (rec) {{
                    try {{ rec.stop(); }} catch(e) {{}}
                }}
            }}
            
            function send(t) {{
                const u = new URL(location.href);
                u.searchParams.set('q', encodeURIComponent(t));
                location.href = u;
            }}
            
            // TTS
            function speak(t) {{
                if (!t || !window.speechSynthesis) return;
                speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(t);
                u.lang = 'ko-KR'; u.rate = 0.9;
                const v = speechSynthesis.getVoices().find(x => x.lang.includes('ko'));
                if (v) u.voice = v;
                u.onstart = () => {{
                    document.getElementById('state').textContent = '🗣️ 말하고 있어요...';
                    document.getElementById('state').className = 'state speaking';
                }};
                u.onend = () => {{
                    document.getElementById('state').textContent = '💬 마이크를 누르고 말씀하세요';
                    document.getElementById('state').className = 'state';
                }};
                speechSynthesis.speak(u);
            }}
            
            // 음성 로드 후 TTS 실행
            if (window.speechSynthesis) {{
                speechSynthesis.onvoiceschanged = () => speak(`{escape(last_ai)}`);
                if (speechSynthesis.getVoices().length) speak(`{escape(last_ai)}`);
                setTimeout(() => speak(`{escape(last_ai)}`), 500);
            }}
        </script>
    ''', unsafe_allow_html=True)
    
    # 사용자 입력 처리
    q = st.query_params.get('q', '')
    if q:
        import urllib.parse
        text = urllib.parse.unquote(q)
        st.session_state.messages.append({'role': 'user', 'text': text})
        
        llm = get_llm()
        if llm:
            resp = llm.generate(text)
            if resp:
                st.session_state.messages.append({'role': 'ai', 'text': resp})
        
        st.query_params.clear()
        st.rerun()
    
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
