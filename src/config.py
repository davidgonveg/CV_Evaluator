"""Configuración del sistema CV Evaluator."""

import os
from enum import Enum
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Proveedores de LLM soportados."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


class Settings(BaseSettings):
    """Configuración de la aplicación."""

    # LLM Configuration
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OLLAMA,
        description="Proveedor de LLM a utilizar"
    )
    llm_model: str = Field(
        default="mistral:7b-instruct-q4_K_M",
        description="Modelo de LLM a utilizar"
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperatura del modelo (0 = determinístico)"
    )

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="URL base de Ollama"
    )

    # OpenAI Configuration (si se usa)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="API Key de OpenAI"
    )

    # Anthropic Configuration (si se usa)
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="API Key de Anthropic"
    )

    # Application Settings
    app_name: str = Field(default="CV Evaluator")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instancia global de configuración
settings = Settings()
