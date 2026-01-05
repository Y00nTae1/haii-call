"""
TTS.py - Edge TTS 기반 음성 합성 모듈
텍스트 → 음성 변환
"""
import asyncio
import logging
import tempfile
import os
import platform
from typing import Optional
import edge_tts

logging.basicConfig(level=logging.INFO, format='%(asctime)s [TTS] %(message)s')
logger = logging.getLogger(__name__)

# 한국어 음성 목록
VOICES = {
    "female_warm": "ko-KR-SunHiNeural",    # 따뜻한 여성 (기본)
    "female_bright": "ko-KR-JiMinNeural",  # 밝은 여성
    "male": "ko-KR-InJoonNeural",          # 남성
}


class TTS:
    """Edge TTS 음성 합성"""
    
    def __init__(self, voice: str = "female_warm", rate: str = "-5%"):
        """
        Args:
            voice: 음성 종류 (female_warm, female_bright, male)
            rate: 말하기 속도 (예: "-10%", "+5%")
        """
        self.voice = VOICES.get(voice, VOICES["female_warm"])
        self.rate = rate
        self.is_speaking = False
        
        logger.info(f"TTS 초기화 완료 (voice: {self.voice}, rate: {self.rate})")
    
    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 합성할 텍스트
            
        Returns:
            MP3 오디오 바이트 데이터
        """
        if not text or not text.strip():
            return None
        
        try:
            logger.info(f"음성 합성 시작: {text[:30]}...")
            
            communicate = edge_tts.Communicate(
                text=text.strip(),
                voice=self.voice,
                rate=self.rate,
            )
            
            # 메모리에 오디오 저장
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            logger.info(f"음성 합성 완료: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"음성 합성 실패: {e}")
            return None
    
    def synthesize_sync(self, text: str) -> Optional[bytes]:
        """동기 음성 합성"""
        return asyncio.run(self.synthesize(text))
    
    def play_audio(self, audio_data: bytes) -> bool:
        """
        오디오 재생
        
        Args:
            audio_data: MP3 오디오 바이트
            
        Returns:
            재생 성공 여부
        """
        if not audio_data:
            return False
        
        self.is_speaking = True
        temp_file = None
        
        try:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_data)
                temp_file = f.name
            
            # OS별 재생
            system = platform.system()
            
            if system == "Windows":
                self._play_windows(temp_file)
            elif system == "Darwin":
                self._play_macos(temp_file)
            else:
                self._play_linux(temp_file)
            
            logger.info("오디오 재생 완료")
            return True
            
        except Exception as e:
            logger.error(f"오디오 재생 실패: {e}")
            return False
            
        finally:
            self.is_speaking = False
            # 임시 파일 정리
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
    
    def _play_windows(self, filepath: str):
        """Windows에서 재생"""
        try:
            # Windows Media Player API 사용
            from ctypes import windll
            windll.winmm.mciSendStringW(f'open "{filepath}" type mpegvideo alias audio', None, 0, 0)
            windll.winmm.mciSendStringW('play audio wait', None, 0, 0)
            windll.winmm.mciSendStringW('close audio', None, 0, 0)
        except Exception as e:
            logger.warning(f"MCI 재생 실패, 대체 방법 시도: {e}")
            # 대체: 기본 앱으로 열기
            os.startfile(filepath)
            import time
            time.sleep(3)
    
    def _play_macos(self, filepath: str):
        """macOS에서 재생"""
        import subprocess
        subprocess.run(["afplay", filepath], check=True)
    
    def _play_linux(self, filepath: str):
        """Linux에서 재생"""
        import subprocess
        # mpg123 또는 ffplay 사용
        try:
            subprocess.run(["mpg123", "-q", filepath], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            subprocess.run(["ffplay", "-nodisp", "-autoexit", filepath], check=True)
    
    def stop(self):
        """재생 중지"""
        self.is_speaking = False
        if platform.system() == "Windows":
            try:
                from ctypes import windll
                windll.winmm.mciSendStringW('stop audio', None, 0, 0)
                windll.winmm.mciSendStringW('close audio', None, 0, 0)
            except Exception:
                pass


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        tts = TTS()
        audio = await tts.synthesize("안녕하세요 할머니, 저는 하이예요!")
        if audio:
            tts.play_audio(audio)
    
    asyncio.run(test())