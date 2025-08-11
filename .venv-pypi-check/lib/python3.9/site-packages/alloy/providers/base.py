"""
Base classes for model providers with capability detection.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum


class StructuredOutputMode(Enum):
    """Different modes of structured output support."""
    NONE = "none"                    # No structured output support
    JSON_MODE = "json_mode"          # Basic JSON mode (OpenAI legacy)
    JSON_SCHEMA = "json_schema"      # Full JSON schema enforcement
    TOOL_BASED = "tool_based"        # Via tool calling (Anthropic)


@dataclass
class ModelCapabilities:
    """Capabilities of a specific model."""
    function_calling: bool = False
    structured_output: StructuredOutputMode = StructuredOutputMode.NONE
    vision: bool = False
    streaming: bool = False
    max_context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_system_message: bool = True
    supports_parallel_function_calls: bool = False
    
    # Provider-specific metadata
    provider_specific: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    """Definition of a tool/function that can be called by the model."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema for parameters
    required: List[str] = field(default_factory=list)
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required
                }
            }
        }
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required
            }
        }
    
    def to_gemini_format(self) -> Dict[str, Any]:
        """Convert to Gemini function calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required
            }
        }


@dataclass
class ToolCall:
    """A tool call requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool call."""
    tool_call_id: str
    result: Any
    error: Optional[str] = None


@dataclass
class ModelResponse:
    """Standardized response from any model provider."""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelProvider(ABC):
    """Abstract base class for all model providers."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
    
    @abstractmethod
    async def get_capabilities(self, model: str) -> ModelCapabilities:
        """Get capabilities of a specific model."""
        pass
    
    @abstractmethod
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
        """Make a call to the model provider."""
        pass
    
    @abstractmethod
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
        """Make a streaming call to the model provider."""
        pass
    
    async def supports_structured_output(self, model: str) -> bool:
        """Check if model supports structured output."""
        caps = await self.get_capabilities(model)
        return caps.structured_output != StructuredOutputMode.NONE
    
    async def supports_function_calling(self, model: str) -> bool:
        """Check if model supports function calling."""
        caps = await self.get_capabilities(model)
        return caps.function_calling
    
    def _create_structured_output_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create provider-specific structured output schema."""
        # Default implementation for JSON schema
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "schema": schema,
                "strict": True
            }
        }
    
    def _parse_tool_calls(self, response_data: Any) -> List[ToolCall]:
        """Parse tool calls from provider response."""
        # Default implementation - override in provider classes
        return []
    
    def _build_tool_result_message(self, tool_result: ToolResult) -> Dict[str, Any]:
        """Build a tool result message for the conversation."""
        return {
            "role": "tool",
            "tool_call_id": tool_result.tool_call_id,
            "content": str(tool_result.result) if tool_result.error is None else f"Error: {tool_result.error}"
        }


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    pass


class ModelNotSupportedError(ProviderError):
    """Raised when a model is not supported by the provider."""
    pass


class CapabilityNotSupportedError(ProviderError):
    """Raised when a requested capability is not supported."""
    pass


class ToolCallError(ProviderError):
    """Raised when tool calling fails."""
    pass