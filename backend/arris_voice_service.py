"""
Creators Hive HQ - ARRIS Voice Interaction Service
Speech-to-Text (Whisper) and Text-to-Speech (TTS) capabilities for Premium users
"""

import os
import logging
import asyncio
import tempfile
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ArrisVoiceService:
    """
    Voice interaction service for ARRIS AI.
    - Speech-to-Text: OpenAI Whisper for transcribing user audio
    - Text-to-Speech: OpenAI TTS for generating audio responses
    """
    
    def __init__(self):
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        self.stt_model = "whisper-1"
        self.tts_model = "tts-1"  # Use tts-1 for faster response, tts-1-hd for higher quality
        self.tts_voice = "nova"  # Energetic, upbeat voice for ARRIS
        
    async def transcribe_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using OpenAI Whisper.
        
        Args:
            audio_data: Raw audio file bytes
            filename: Original filename (used for format detection)
            language: Optional language hint (ISO-639-1 format)
            
        Returns:
            Dict with transcription text and metadata
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            from emergentintegrations.llm.openai import OpenAISpeechToText
            
            # Initialize STT client
            stt = OpenAISpeechToText(api_key=self.api_key)
            
            # Create a temporary file for the audio
            # Get file extension from filename
            ext = filename.split('.')[-1] if '.' in filename else 'webm'
            
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file.flush()
                tmp_path = tmp_file.name
            
            try:
                # Transcribe the audio
                with open(tmp_path, "rb") as audio_file:
                    response = await stt.transcribe(
                        file=audio_file,
                        model=self.stt_model,
                        response_format="json",
                        language=language,
                        prompt="This is a creator asking ARRIS AI about their project or business."
                    )
                
                processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                logger.info(f"ARRIS Voice: Transcribed audio in {processing_time:.2f}s")
                
                return {
                    "success": True,
                    "text": response.text,
                    "processing_time_seconds": round(processing_time, 2),
                    "model": self.stt_model,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"ARRIS Voice: Transcription error - {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Generate speech audio from text using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer)
            speed: Speech speed (0.25 to 4.0)
            output_format: Output format (mp3, opus, aac, flac, wav, pcm)
            
        Returns:
            Dict with base64 encoded audio and metadata
        """
        start_time = datetime.now(timezone.utc)
        voice = voice or self.tts_voice
        
        # Validate speed
        speed = max(0.25, min(4.0, speed))
        
        try:
            from emergentintegrations.llm.openai import OpenAITextToSpeech
            
            # Initialize TTS client
            tts = OpenAITextToSpeech(api_key=self.api_key)
            
            # Generate speech
            audio_bytes = await tts.speak(
                text=text,
                model=self.tts_model,
                voice=voice,
                speed=speed,
                response_format=output_format
            )
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Encode to base64 for easy transmission
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            logger.info(f"ARRIS Voice: Generated speech ({len(text)} chars) in {processing_time:.2f}s")
            
            return {
                "success": True,
                "audio_base64": audio_base64,
                "audio_format": output_format,
                "content_type": f"audio/{output_format}",
                "voice": voice,
                "speed": speed,
                "text_length": len(text),
                "processing_time_seconds": round(processing_time, 2),
                "model": self.tts_model,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"ARRIS Voice: TTS error - {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_base64": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def voice_query(
        self,
        audio_data: bytes,
        filename: str,
        creator_context: Optional[Dict[str, Any]] = None,
        respond_with_voice: bool = True,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete voice interaction: transcribe → process with ARRIS → respond with TTS.
        
        Args:
            audio_data: Raw audio file bytes
            filename: Original filename
            creator_context: Optional context about the creator
            respond_with_voice: Whether to generate audio response
            voice: TTS voice preference
            
        Returns:
            Dict with transcription, ARRIS response, and optional audio
        """
        result = {
            "transcription": None,
            "arris_response": None,
            "audio_response": None,
            "total_processing_time": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        total_start = datetime.now(timezone.utc)
        
        # Step 1: Transcribe audio
        transcription = await self.transcribe_audio(audio_data, filename)
        result["transcription"] = transcription
        
        if not transcription.get("success") or not transcription.get("text"):
            result["error"] = "Failed to transcribe audio"
            return result
        
        user_query = transcription["text"]
        
        # Step 2: Get ARRIS response
        from arris_service import arris_service
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        try:
            # Build context for voice query
            system_message = """You are ARRIS, a friendly AI assistant for Creators Hive HQ. You help content creators build successful businesses.

You are currently having a VOICE conversation, so:
- Keep responses concise (2-4 sentences max)
- Be conversational and friendly
- Avoid bullet points or complex formatting
- Speak naturally as if talking to a friend
- Be encouraging and supportive

If the creator asks about their projects, proposals, or business strategy, provide helpful guidance.
If they have a specific question, answer it directly."""

            # Add creator context if available
            if creator_context:
                system_message += f"""

Creator Profile:
- Name: {creator_context.get('name', 'Creator')}
- Platforms: {', '.join(creator_context.get('platforms', []))}
- Niche: {creator_context.get('niche', 'Content Creation')}"""

            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"arris-voice-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                system_message=system_message
            ).with_model("openai", "gpt-4o")
            
            # Send user message
            response = await chat.send_message(UserMessage(text=user_query))
            
            result["arris_response"] = {
                "success": True,
                "text": response,
                "query": user_query
            }
            
            # Step 3: Generate voice response (if requested)
            if respond_with_voice and response:
                audio_response = await self.generate_speech(
                    text=response,
                    voice=voice
                )
                result["audio_response"] = audio_response
                
        except Exception as e:
            logger.error(f"ARRIS Voice: Query processing error - {str(e)}")
            result["arris_response"] = {
                "success": False,
                "error": str(e),
                "text": "I'm sorry, I encountered an error processing your request. Please try again."
            }
            
            # Still generate error response audio
            if respond_with_voice:
                audio_response = await self.generate_speech(
                    text="I'm sorry, I encountered an error processing your request. Please try again.",
                    voice=voice
                )
                result["audio_response"] = audio_response
        
        result["total_processing_time"] = round(
            (datetime.now(timezone.utc) - total_start).total_seconds(), 2
        )
        
        return result
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available TTS voices"""
        return {
            "voices": [
                {"id": "alloy", "name": "Alloy", "description": "Neutral, balanced"},
                {"id": "ash", "name": "Ash", "description": "Clear, articulate"},
                {"id": "coral", "name": "Coral", "description": "Warm, friendly"},
                {"id": "echo", "name": "Echo", "description": "Smooth, calm"},
                {"id": "fable", "name": "Fable", "description": "Expressive, storytelling"},
                {"id": "nova", "name": "Nova", "description": "Energetic, upbeat (default)"},
                {"id": "onyx", "name": "Onyx", "description": "Deep, authoritative"},
                {"id": "sage", "name": "Sage", "description": "Wise, measured"},
                {"id": "shimmer", "name": "Shimmer", "description": "Bright, cheerful"}
            ],
            "default": "nova",
            "models": {
                "tts-1": "Standard quality, faster",
                "tts-1-hd": "HD quality, slower"
            }
        }


# Global instance
arris_voice_service = ArrisVoiceService()
