"""
OpenAI provider implementation with function calling and structured output support.
"""

from typing import Any, Dict, List, Optional, Union
import json
import aiohttp

from .base import (
    ModelProvider, ModelCapabilities, ToolDefinition, ToolCall, 
    ModelResponse, StructuredOutputMode, ProviderError
)


class OpenAIProvider(ModelProvider):
    """OpenAI API provider with GPT-4o, GPT-4.1 and other models."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url or "https://api.openai.com/v1")
        self._model_capabilities_cache = {}
    
    async def get_capabilities(self, model: str) -> ModelCapabilities:
        """Get capabilities for OpenAI models."""
        if model in self._model_capabilities_cache:
            return self._model_capabilities_cache[model]
        
        # Define capabilities based on model
        capabilities = self._get_model_capabilities(model)
        self._model_capabilities_cache[model] = capabilities
        return capabilities
    
    def _get_model_capabilities(self, model: str) -> ModelCapabilities:
        """Define capabilities for known OpenAI models."""
        model_lower = model.lower()
        
        # GPT-4o and newer models with structured output
        if any(x in model_lower for x in ["gpt-4o", "gpt-4.1", "o1-"]):
            return ModelCapabilities(
                function_calling=True,
                structured_output=StructuredOutputMode.JSON_SCHEMA,
                vision="vision" in model_lower or "gpt-4o" in model_lower,
                streaming=True,
                max_context_tokens=128000,
                max_output_tokens=16384,
                supports_parallel_function_calls=True,
                provider_specific={"supports_strict_schema": True}
            )
        
        # GPT-4 models
        elif "gpt-4" in model_lower:
            return ModelCapabilities(
                function_calling=True,
                structured_output=StructuredOutputMode.JSON_MODE,
                vision="vision" in model_lower,
                streaming=True,
                max_context_tokens=128000 if "turbo" in model_lower else 8192,
                max_output_tokens=4096,
                supports_parallel_function_calls=True
            )
        
        # GPT-3.5 models
        elif "gpt-3.5" in model_lower:
            return ModelCapabilities(
                function_calling=True,
                structured_output=StructuredOutputMode.JSON_MODE,
                streaming=True,
                max_context_tokens=16385,
                max_output_tokens=4096,
                supports_parallel_function_calls=True
            )
        
        # Default for unknown models
        else:
            return ModelCapabilities(
                function_calling=False,
                structured_output=StructuredOutputMode.NONE,
                streaming=True,
                max_context_tokens=4096,
                max_output_tokens=1024
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
        """Make a call to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        # Add tools if provided
        if tools:
            data["tools"] = [tool.to_openai_format() for tool in tools]
            if tool_choice:
                data["tool_choice"] = tool_choice
        
        # Add response format if provided
        if response_format:
            capabilities = await self.get_capabilities(model)
            if capabilities.structured_output == StructuredOutputMode.JSON_SCHEMA:
                data["response_format"] = response_format
            elif capabilities.structured_output == StructuredOutputMode.JSON_MODE:
                data["response_format"] = {"type": "json_object"}
        
        # Add any additional kwargs
        data.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"OpenAI API error {response.status}: {error_text}")
                
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
        """Make a streaming call to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        if tools:
            data["tools"] = [tool.to_openai_format() for tool in tools]
            if tool_choice:
                data["tool_choice"] = tool_choice
        
        if response_format:
            capabilities = await self.get_capabilities(model)
            if capabilities.structured_output == StructuredOutputMode.JSON_SCHEMA:
                data["response_format"] = response_format
            elif capabilities.structured_output == StructuredOutputMode.JSON_MODE:
                data["response_format"] = {"type": "json_object"}
        
        data.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"OpenAI API error {response.status}: {error_text}")
                
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
        """Parse OpenAI API response."""
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
            metadata={"provider": "openai", "model": response_data.get("model")}
        )
    
    def _parse_streaming_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a streaming chunk from OpenAI."""
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