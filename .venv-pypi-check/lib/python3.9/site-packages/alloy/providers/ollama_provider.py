"""
Ollama provider implementation (stub for now).
"""

from typing import Any, Dict, List, Optional, Union

from .base import (
    ModelProvider, ModelCapabilities, ToolDefinition, ModelResponse, StructuredOutputMode
)


class OllamaProvider(ModelProvider):
    """Ollama local model provider (implementation stub)."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url or "http://localhost:11434")
    
    async def get_capabilities(self, model: str) -> ModelCapabilities:
        """Get capabilities for Ollama models."""
        # TODO: Implement Ollama capability detection
        # This would need to query the model or use a lookup table
        return ModelCapabilities(
            function_calling=False,  # Depends on the specific model
            structured_output=StructuredOutputMode.NONE,  # Depends on the model
            vision=False,
            streaming=True,
            max_context_tokens=4096,  # Varies by model
            max_output_tokens=2048
        )
    
    async def call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """Make a call to Ollama API."""
        # TODO: Implement Ollama API call
        raise NotImplementedError("Ollama provider not yet implemented")
    
    async def call_streaming(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[Union[str, Dict]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Make a streaming call to Ollama API."""
        # TODO: Implement Ollama streaming
        raise NotImplementedError("Ollama provider not yet implemented")