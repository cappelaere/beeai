"""Pydantic models matching OpenAPI specification"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TextType(str, Enum):
    """Text input type"""
    TEXT = "text"
    SSML = "ssml"


class OutputFormat(str, Enum):
    """Audio output format"""
    WAV = "wav"
    MP3 = "mp3"


class ReturnMode(str, Enum):
    """Return mode for synthesize endpoint"""
    BYTES = "bytes"
    URL = "url"


class Gender(str, Enum):
    """Voice gender"""
    FEMALE = "Female"
    MALE = "Male"
    NEUTRAL = "Neutral"
    UNKNOWN = "Unknown"


class Voice(BaseModel):
    """Voice information"""
    id: str = Field(..., description="Voice identifier used in synthesize requests")
    name: str
    language_code: str
    gender: Gender = Gender.UNKNOWN
    sample_rates: List[int] = Field(default_factory=list)
    engines: List[str] = Field(default_factory=lambda: ["standard"])


class VoicesResponse(BaseModel):
    """Response for /v1/voices endpoint"""
    voices: List[Voice]


class SynthesizeRequest(BaseModel):
    """Request for /v1/tts/synthesize endpoint"""
    text: str = Field(..., min_length=1, max_length=8000, description="Text or SSML input")
    text_type: TextType = TextType.TEXT
    voice_id: str = Field(..., description="Voice identifier from /v1/voices")
    output_format: OutputFormat = OutputFormat.WAV
    sample_rate: int = Field(default=22050)
    speaking_rate: float = Field(default=1.0, description="Rate multiplier. 1.0 is default.")
    return_mode: ReturnMode = ReturnMode.BYTES
    cache_ttl_seconds: int = Field(default=3600, description="TTL for cached audio if return_mode='url'")
    
    @field_validator('sample_rate')
    @classmethod
    def validate_sample_rate(cls, v):
        valid_rates = [8000, 16000, 22050, 24000]
        if v not in valid_rates:
            raise ValueError(f"sample_rate must be one of {valid_rates}")
        return v
    
    @field_validator('speaking_rate')
    @classmethod
    def validate_speaking_rate(cls, v):
        if v <= 0 or v > 3.0:
            raise ValueError("speaking_rate must be between 0 and 3.0")
        return v


class SynthesizeUrlResponse(BaseModel):
    """Response when return_mode='url'"""
    audio_id: str
    audio_url: str
    content_type: str
    expires_in: int


class ErrorDetail(BaseModel):
    """Error detail"""
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: ErrorDetail
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"
    engine: str = "piper"
    version: str
