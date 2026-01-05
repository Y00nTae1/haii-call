"""
STT.py - Deepgram 기반 음성 인식 모듈
오디오 바이트 → 텍스트 변환
"""
import logging
import os
from typing import Optional
from deepgram import DeepgramClient, PrerecordedOptions

logging.basicConfig(level=logging.INFO, format='%(asctime)s [STT] %(message)s')
logger = logging.getLogger(__name__)


class STT:
    """Deepgram 음성 인식"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Deepgram API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        
        if not self.api_key:
            logger.warning("DEEPGRAM_API_KEY가 설정되지 않았습니다")
            self.client = None
        else:
            try:
                self.client = DeepgramClient(self.api_key)
                logger.info("STT 초기화 완료 (Deepgram)")
            except Exception as e:
                logger.error(f"Deepgram 초기화 실패: {e}")
                self.client = None
    
    def transcribe(self, audio_data: bytes, mime_type: str = "audio/wav") -> Optional[str]:
        """
        오디오를 텍스트로 변환 (동기)
        
        Args:
            audio_data: 오디오 바이트 데이터
            mime_type: 오디오 MIME 타입
            
        Returns:
            인식된 텍스트 또는 None
        """
        if not self.client:
            logger.error("STT 클라이언트가 초기화되지 않았습니다")
            return None
        
        if not audio_data or len(audio_data) < 1000:
            logger.warning("오디오 데이터가 너무 짧습니다")
            return None
        
        try:
            logger.info(f"음성 인식 시작... ({len(audio_data)} bytes)")
            
            # Deepgram 옵션 설정
            options = PrerecordedOptions(
                model="nova-2",
                language="ko",  # 한국어
                smart_format=True,
                punctuate=True,
            )
            
            # 오디오 소스
            source = {"buffer": audio_data, "mimetype": mime_type}
            
            # 음성 인식 실행
            response = self.client.listen.rest.v("1").transcribe_file(source, options)
            
            # 결과 추출
            transcript = response.results.channels[0].alternatives[0].transcript
            
            if transcript:
                logger.info(f"인식 결과: {transcript}")
                return transcript.strip()
            else:
                logger.warning("인식된 텍스트가 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"음성 인식 실패: {e}")
            return None
    
    async def transcribe_async(self, audio_data: bytes, mime_type: str = "audio/wav") -> Optional[str]:
        """비동기 음성 인식"""
        # 현재는 동기 버전 사용 (Deepgram SDK 호환성)
        return self.transcribe(audio_data, mime_type)


# 테스트
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    stt = STT()
    print(f"STT 초기화: {'성공' if stt.client else '실패'}")