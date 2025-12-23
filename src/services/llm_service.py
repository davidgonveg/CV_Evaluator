"""Servicio de abstracción del LLM usando LangChain.

Este servicio permite intercambiar fácilmente entre diferentes proveedores de LLM
(Ollama, OpenAI, Anthropic, etc.) sin cambiar el código del resto de la aplicación.
"""

import json
import re
from typing import Optional, Any
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import settings, LLMProvider


class LLMService:
    """Servicio para interactuar con modelos de lenguaje."""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Inicializa el servicio LLM.

        Args:
            provider: Proveedor de LLM (por defecto usa config)
            model: Modelo específico (por defecto usa config)
            temperature: Temperatura del modelo (por defecto usa config)
        """
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self._llm: Optional[BaseLanguageModel] = None

    def _create_llm(self) -> BaseLanguageModel:
        """Crea la instancia del LLM según el proveedor configurado."""
        if self.provider == LLMProvider.OLLAMA:
            from langchain_ollama import OllamaLLM

            return OllamaLLM(
                model=self.model,
                base_url=settings.ollama_base_url,
                temperature=self.temperature,
            )

        elif self.provider == LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI

            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return ChatOpenAI(
                model=self.model,
                api_key=settings.openai_api_key,
                temperature=self.temperature,
            )

        elif self.provider == LLMProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic

            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            return ChatAnthropic(
                model=self.model,
                api_key=settings.anthropic_api_key,
                temperature=self.temperature,
            )

        elif self.provider == LLMProvider.HUGGINGFACE:
            from langchain_huggingface import HuggingFacePipeline
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

            tokenizer = AutoTokenizer.from_pretrained(self.model)
            model = AutoModelForCausalLM.from_pretrained(self.model)
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=2048,
                temperature=self.temperature,
            )
            return HuggingFacePipeline(pipeline=pipe)

        else:
            raise ValueError(f"Proveedor no soportado: {self.provider}")

    @property
    def llm(self) -> BaseLanguageModel:
        """Obtiene la instancia del LLM (lazy loading)."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def invoke(self, prompt: str, **kwargs) -> str:
        """
        Invoca el LLM con un prompt simple.

        Args:
            prompt: El prompt a enviar al modelo

        Returns:
            Respuesta del modelo como string
        """
        response = self.llm.invoke(prompt)
        # Manejar diferentes tipos de respuesta
        if hasattr(response, "content"):
            return response.content
        return str(response)

    def invoke_with_template(
        self, template: str, variables: dict[str, Any]
    ) -> str:
        """
        Invoca el LLM usando un template de prompt.

        Args:
            template: Template de prompt con variables {variable}
            variables: Diccionario con valores para las variables

        Returns:
            Respuesta del modelo como string
        """
        prompt_template = PromptTemplate.from_template(template)
        chain = prompt_template | self.llm | StrOutputParser()
        return chain.invoke(variables)

    def invoke_json(self, prompt: str, **kwargs) -> dict:
        """
        Invoca el LLM y parsea la respuesta como JSON.

        Args:
            prompt: El prompt a enviar al modelo

        Returns:
            Respuesta parseada como diccionario
        """
        response = self.invoke(prompt, **kwargs)
        return self._parse_json_response(response)

    def invoke_with_template_json(
        self, template: str, variables: dict[str, Any]
    ) -> dict:
        """
        Invoca el LLM con template y parsea respuesta como JSON.

        Args:
            template: Template de prompt
            variables: Variables para el template

        Returns:
            Respuesta parseada como diccionario
        """
        response = self.invoke_with_template(template, variables)
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> dict:
        """
        Extrae y parsea JSON de una respuesta del LLM.

        Args:
            response: Respuesta del modelo

        Returns:
            Diccionario parseado

        Raises:
            ValueError: Si no se puede parsear el JSON
        """
        # Intentar parsear directamente
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Buscar JSON en bloques de código
        json_patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"\{[\s\S]*\}",
        ]

        for pattern in json_patterns:
            match = re.search(pattern, response)
            if match:
                try:
                    json_str = match.group(1) if "```" in pattern else match.group(0)
                    return json.loads(json_str.strip())
                except (json.JSONDecodeError, IndexError):
                    continue

        raise ValueError(f"No se pudo parsear JSON de la respuesta: {response[:200]}...")

    def health_check(self) -> bool:
        """Verifica que el LLM está funcionando correctamente."""
        try:
            response = self.invoke("Responde solo con 'OK'")
            return "OK" in response.upper()
        except Exception:
            return False
