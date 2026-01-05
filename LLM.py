"""
LLM.py - Gemini 기반 대화 생성 모듈
"""
import logging
import os
from typing import Optional, List, Dict
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format='%(asctime)s [LLM] %(message)s')
logger = logging.getLogger(__name__)

# 시스템 프롬프트
SYSTEM_PROMPT = """당신은 '하이'라는 이름의 AI 건강 도우미입니다.
76세 독거 어르신과 전화 통화를 하고 있습니다.

## 말투 규칙
- 따뜻하고 친근한 손녀 같은 말투로 대화하세요
- 문장은 짧고 명확하게 (2-3문장 이내)
- 높임말을 사용하되 딱딱하지 않게
- 적절한 공감과 칭찬을 표현하세요

## 대화 목표
1. 안부 확인 (기분, 건강 상태)
2. 식사 여부 확인
3. 약 복용 여부 확인
4. 일상 대화로 외로움 해소

## 절대 금지 사항 (매우 중요)
- 이모티콘, 이모지 절대 사용 금지 (😊❤️ 등 모든 특수문자 이모티콘 금지)
- 의료 진단이나 처방 금지
- 텍스트만 사용하세요

## 기타 주의사항
- 응급 상황 시 119 안내
- 항상 긍정적이고 따뜻하게 대화하세요

자연스럽게 대화해주세요. 다시 한번 강조: 이모티콘/이모지를 절대 사용하지 마세요."""


class LLM:
    """Gemini 대화 생성"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Google API 키
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.error("GOOGLE_API_KEY가 설정되지 않았습니다")
            self.model = None
            self.chat = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-lite",  # 무료 티어에서 가장 안정적
                system_instruction=SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.8,
                    "max_output_tokens": 150,
                    "top_p": 0.9,
                }
            )
            
            self.chat = self.model.start_chat(history=[])
            self.history: List[Dict] = []
            
            logger.info("LLM 초기화 완료 (Gemini)")
            
        except Exception as e:
            logger.error(f"LLM 초기화 실패: {e}")
            self.model = None
            self.chat = None
    
    def generate(self, user_input: str) -> str:
        """
        응답 생성 (동기)
        
        Args:
            user_input: 사용자 입력 텍스트
            
        Returns:
            AI 응답 텍스트
        """
        if not user_input or not user_input.strip():
            return ""
        
        if not self.chat:
            logger.warning("LLM이 초기화되지 않아 데모 응답 사용")
            return self._demo_response(user_input)
        
        try:
            logger.info(f"입력: {user_input}")
            
            response = self.chat.send_message(user_input)
            ai_response = response.text.strip()
            
            # 히스토리 저장
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "ai", "content": ai_response})
            
            logger.info(f"응답: {ai_response}")
            return ai_response
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            # 429 쿼터 초과 시 데모 응답으로 폴백
            if "429" in str(e) or "quota" in str(e).lower():
                logger.warning("API 쿼터 초과 - 데모 모드로 전환")
                return self._demo_response(user_input)
            return "죄송해요 할머니, 잘 못 들었어요. 다시 말씀해 주시겠어요?"
    
    async def generate_async(self, user_input: str) -> str:
        """비동기 응답 생성"""
        if not user_input or not user_input.strip():
            return ""
        
        if not self.chat:
            return self._demo_response(user_input)
        
        try:
            logger.info(f"입력: {user_input}")
            
            response = await self.chat.send_message_async(user_input)
            ai_response = response.text.strip()
            
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "ai", "content": ai_response})
            
            logger.info(f"응답: {ai_response}")
            return ai_response
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {e}")
            # 429 쿼터 초과 시 데모 응답으로 폴백
            if "429" in str(e) or "quota" in str(e).lower():
                logger.warning("API 쿼터 초과 - 데모 모드로 전환")
                return self._demo_response(user_input)
            return "죄송해요, 다시 말씀해 주시겠어요?"
    
    def _demo_response(self, text: str) -> str:
        """데모 응답 (API 없을 때)"""
        responses = {
            "안녕": "안녕하세요 할머니~ 오늘 기분이 어떠세요?",
            "약": "약 드셨어요? 건강을 위해 꼭 챙겨 드세요~",
            "밥": "밥 맛있게 드셨군요! 뭐 드셨어요?",
            "아파": "어머, 어디가 불편하세요? 많이 아프시면 병원에 가보셔야 해요.",
            "심심": "심심하시면 저랑 이야기해요! 요즘 뭐 하고 지내세요?",
            "고마": "할머니가 건강하게 지내시는 게 저한테는 가장 큰 선물이에요~",
            "먹": "맛있게 드셨어요? 잘 드셔야 힘이 나요~",
        }
        
        for keyword, response in responses.items():
            if keyword in text:
                return response
        
        return "네 할머니, 더 말씀해 주세요~"
    
    def get_greeting(self) -> str:
        """인사말"""
        return "할머니~ 저 하이예요! 점심 맛있게 드셨어요?"
    
    def reset(self):
        """대화 초기화"""
        if self.model:
            self.chat = self.model.start_chat(history=[])
        self.history.clear()
        logger.info("대화 초기화됨")


# 테스트
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    llm = LLM()
    if llm.chat:
        response = llm.generate("안녕하세요")
        print(f"응답: {response}")
    else:
        print("LLM 초기화 실패")