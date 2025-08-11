"""
OpenRouter provider implementation with dynamic capability detection.
OpenRouter aggregates models from multiple providers and provides metadata.
"""

from typing import Any, Dict, List, Optional, Union
import json
import aiohttp
from datetime import datetime, timedelta

from .base import (
    ModelProvider, ModelCapabilities, ToolDefinition, ToolCall, 
    ModelResponse, StructuredOutputMode, ProviderError
)


class OpenRouterProvider(ModelProvider):
    """OpenRouter API provider with multi-model support and capability detection."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url or "https://openrouter.ai/api/v1")
        self._model_capabilities_cache = {}
        self._models_cache = None
        self._cache_timestamp = None
        self._cache_duration = timedelta(hours=1)  # Cache models for 1 hour
    
    async def get_capabilities(self, model: str) -> ModelCapabilities:
        """Get capabilities for OpenRouter models via their models API."""
        if model in self._model_capabilities_cache:
            return self._model_capabilities_cache[model]
        
        # Fetch model information from OpenRouter
        model_info = await self._get_model_info(model)
        capabilities = self._parse_model_capabilities(model_info)
        
        self._model_capabilities_cache[model] = capabilities
        return capabilities
    
    async def _get_model_info(self, model: str) -> Dict[str, Any]:
        """Fetch model information from OpenRouter models API."""
        # Use cached models if available and fresh
        if (self._models_cache and self._cache_timestamp and 
            datetime.now() - self._cache_timestamp < self._cache_duration):
            models = self._models_cache
        else:
            models = await self._fetch_models()
        
        # Find the specific model
        for model_data in models.get("data", []):
            if model_data["id"] == model:
                return model_data
        
        # If not found, return default info
        return {"id": model, "capabilities": {}}
    
    async def _fetch_models(self) -> Dict[str, Any]:
        """Fetch all models from OpenRouter API."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers
            ) as response:
                if response.status == 200:
                    models = await response.json()
                    self._models_cache = models
                    self._cache_timestamp = datetime.now()
                    return models
                else:
                    # Return empty if can't fetch
                    return {"data": []}
    
    def _parse_model_capabilities(self, model_info: Dict[str, Any]) -> ModelCapabilities:
        """Parse model capabilities from OpenRouter model info."""
        capabilities_data = model_info.get("capabilities", {})
        
        # Parse structured output support
        structured_output = StructuredOutputMode.NONE
        if capabilities_data.get("supports_structured_outputs", False):
            structured_output = StructuredOutputMode.JSON_SCHEMA
        elif "gpt-4" in model_info["id"] or "claude" in model_info["id"]:
            # Many models support JSON mode even if not explicitly listed
            structured_output = StructuredOutputMode.JSON_MODE
        
        return ModelCapabilities(
            function_calling=capabilities_data.get("supports_function_calling", False),
            structured_output=structured_output,
            vision=capabilities_data.get("supports_vision", False),
            streaming=capabilities_data.get("supports_streaming", True),
            max_context_tokens=model_info.get("context_length"),
            max_output_tokens=model_info.get("max_output_tokens"),
            supports_parallel_function_calls=capabilities_data.get("supports_parallel_function_calling", False),
            provider_specific={
                "openrouter_model_id": model_info["id"],
                "pricing": model_info.get("pricing", {}),
                "top_provider": model_info.get("top_provider", {}),
                "per_request_limits": model_info.get("per_request_limits", {})
            }
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
        """Make a call to OpenRouter API (OpenAI-compatible)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": kwargs.get("http_referer", "https://github.com/alloy-ai/alloy"),
            "X-Title": kwargs.get("x_title", "Alloy DSL")
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        # Check model capabilities before adding features
        capabilities = await self.get_capabilities(model)
        
        # Add tools if supported
        if tools and capabilities.function_calling:
            data["tools"] = [tool.to_openai_format() for tool in tools]
            if tool_choice:
                data["tool_choice"] = tool_choice
        elif tools and not capabilities.function_calling:
            # Model doesn't support function calling, ignore tools
            pass
        
        # Add response format if supported
        if response_format and capabilities.structured_output != StructuredOutputMode.NONE:
            if capabilities.structured_output == StructuredOutputMode.JSON_SCHEMA:
                data["response_format"] = response_format
            elif capabilities.structured_output == StructuredOutputMode.JSON_MODE:
                data["response_format"] = {"type": "json_object"}
        
        # Add provider-specific parameters
        if "provider" in kwargs:
            data["provider"] = kwargs["provider"]
        
        # Remove our custom headers from kwargs
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ["http_referer", "x_title", "provider"]}
        data.update(filtered_kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"OpenRouter API error {response.status}: {error_text}")
                
                result = await response.json()
                return self._parse_response(result)
    
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
        """Make a streaming call to OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": kwargs.get("http_referer", "https://github.com/alloy-ai/alloy"),
            "X-Title": kwargs.get("x_title", "Alloy DSL")
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        capabilities = await self.get_capabilities(model)
        
        if tools and capabilities.function_calling:
            data["tools"] = [tool.to_openai_format() for tool in tools]
            if tool_choice:
                data["tool_choice"] = tool_choice
        
        if response_format and capabilities.structured_output != StructuredOutputMode.NONE:
            if capabilities.structured_output == StructuredOutputMode.JSON_SCHEMA:
                data["response_format"] = response_format
            elif capabilities.structured_output == StructuredOutputMode.JSON_MODE:
                data["response_format"] = {"type": "json_object"}
        
        if "provider" in kwargs:
            data["provider"] = kwargs["provider"]
        
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ["http_referer", "x_title", "provider"]}
        data.update(filtered_kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"OpenRouter API error {response.status}: {error_text}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        if line == 'data: [DONE]':
                            break
                        
                        try:
                            chunk_data = json.loads(line[6:])
                            yield self._parse_streaming_chunk(chunk_data)
                        except json.JSONDecodeError:
                            continue
    
    def _parse_response(self, response_data: Dict[str, Any]) -> ModelResponse:
        """Parse OpenRouter API response (OpenAI-compatible format)."""
        choice = response_data["choices"][0]
        message = choice["message"]
        
        content = message.get("content", "") or ""
        tool_calls = []
        
        # Parse tool calls if present
        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tool_call["id"],
                    name=tool_call["function"]["name"],
                    arguments=json.loads(tool_call["function"]["arguments"])
                ))
        
        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=choice.get("finish_reason"),
            usage=response_data.get("usage"),
            metadata={
                "provider": "openrouter", 
                "model": response_data.get("model"),
                "provider_info": response_data.get("provider", {})
            }
        )
    
    def _parse_streaming_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a streaming chunk from OpenRouter (OpenAI-compatible)."""
        if "choices" not in chunk_data or not chunk_data["choices"]:
            return {"type": "unknown", "data": chunk_data}
        
        choice = chunk_data["choices"][0]
        delta = choice.get("delta", {})
        
        if "content" in delta:
            return {"type": "content", "content": delta["content"]}
        elif "tool_calls" in delta:
            return {"type": "tool_calls", "tool_calls": delta["tool_calls"]}
        else:
            return {"type": "other", "data": delta}
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models with their capabilities."""
        models = await self._fetch_models()
        return models.get("data", [])
    
    async def find_models_with_capability(self, capability: str) -> List[str]:
        """Find models that support a specific capability."""
        models = await self.list_available_models()
        matching_models = []
        
        for model in models:
            capabilities = model.get("capabilities", {})
            if capabilities.get(f"supports_{capability}", False):
                matching_models.append(model["id"])
        
        return matching_models