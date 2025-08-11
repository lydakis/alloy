"""
Anthropic provider implementation with tool calling support.
Note: Anthropic uses tool-based structured output, not native JSON schema.
"""

from typing import Any, Dict, List, Optional, Union
import json
import aiohttp

from .base import (
    ModelProvider, ModelCapabilities, ToolDefinition, ToolCall, 
    ModelResponse, StructuredOutputMode, ProviderError
)


class AnthropicProvider(ModelProvider):
    """Anthropic Claude API provider."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, base_url or "https://api.anthropic.com")
        self._model_capabilities_cache = {}
    
    async def get_capabilities(self, model: str) -> ModelCapabilities:
        """Get capabilities for Anthropic models."""
        if model in self._model_capabilities_cache:
            return self._model_capabilities_cache[model]
        
        capabilities = self._get_model_capabilities(model)
        self._model_capabilities_cache[model] = capabilities
        return capabilities
    
    def _get_model_capabilities(self, model: str) -> ModelCapabilities:
        """Define capabilities for known Anthropic models."""
        model_lower = model.lower()
        
        # Claude 3.5 and Claude 4 models
        if any(x in model_lower for x in ["claude-3.5", "claude-4"]):
            return ModelCapabilities(
                function_calling=True,
                structured_output=StructuredOutputMode.TOOL_BASED,  # Via tool calling
                vision="vision" in model_lower or "sonnet" in model_lower or "opus" in model_lower,
                streaming=True,
                max_context_tokens=200000,
                max_output_tokens=8192,
                supports_parallel_function_calls=False,  # Not yet supported
                provider_specific={"supports_computer_use": "computer-use" in model_lower}
            )
        
        # Claude 3 models
        elif "claude-3" in model_lower:
            return ModelCapabilities(
                function_calling=True,
                structured_output=StructuredOutputMode.TOOL_BASED,
                vision="vision" in model_lower or "sonnet" in model_lower or "opus" in model_lower,
                streaming=True,
                max_context_tokens=200000,
                max_output_tokens=4096,
                supports_parallel_function_calls=False
            )
        
        # Older Claude models
        elif "claude" in model_lower:
            return ModelCapabilities(
                function_calling=False,
                structured_output=StructuredOutputMode.NONE,
                streaming=True,
                max_context_tokens=100000,
                max_output_tokens=4096
            )
        
        # Default for unknown models
        else:
            return ModelCapabilities(
                function_calling=False,
                structured_output=StructuredOutputMode.NONE,
                streaming=True,
                max_context_tokens=8192,
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
        """Make a call to Anthropic API."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Anthropic expects system message separately
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        data = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }
        
        if system_message:
            data["system"] = system_message
        
        # Add tools if provided
        if tools:
            data["tools"] = [tool.to_anthropic_format() for tool in tools]
            if tool_choice and tool_choice != "auto":
                # Anthropic has different tool choice format
                if tool_choice == "none":
                    data["tool_choice"] = {"type": "auto"}  # Anthropic doesn't have "none"
                elif isinstance(tool_choice, dict):
                    data["tool_choice"] = tool_choice
        
        # Handle structured output via tool calling
        if response_format and tools is None:
            # Create a structured output tool
            structured_tool = self._create_structured_output_tool(response_format)
            data["tools"] = [structured_tool]
            data["tool_choice"] = {"type": "tool", "name": "structured_output"}
        
        # Add any additional kwargs
        data.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"Anthropic API error {response.status}: {error_text}")
                
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
        """Make a streaming call to Anthropic API."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Process messages and system prompt
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        data = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        
        if system_message:
            data["system"] = system_message
        
        if tools:
            data["tools"] = [tool.to_anthropic_format() for tool in tools]
            if tool_choice and tool_choice != "auto":
                if tool_choice == "none":
                    data["tool_choice"] = {"type": "auto"}
                elif isinstance(tool_choice, dict):
                    data["tool_choice"] = tool_choice
        
        if response_format and tools is None:
            structured_tool = self._create_structured_output_tool(response_format)
            data["tools"] = [structured_tool]
            data["tool_choice"] = {"type": "tool", "name": "structured_output"}
        
        data.update(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ProviderError(f"Anthropic API error {response.status}: {error_text}")
                
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
    
    def _create_structured_output_tool(self, response_format: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tool for structured output in Anthropic format."""
        schema = response_format.get("json_schema", {}).get("schema", response_format)
        
        return {
            "name": "structured_output",
            "description": "Provide a structured response in the requested format",
            "input_schema": schema
        }
    
    def _parse_response(self, response_data: Dict[str, Any]) -> ModelResponse:
        """Parse Anthropic API response."""
        content_blocks = response_data.get("content", [])
        
        content = ""
        tool_calls = []
        
        for block in content_blocks:
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=block["input"]
                ))
        
        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response_data.get("stop_reason"),
            usage=response_data.get("usage"),
            metadata={"provider": "anthropic", "model": response_data.get("model")}
        )
    
    def _parse_streaming_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a streaming chunk from Anthropic."""
        chunk_type = chunk_data.get("type")
        
        if chunk_type == "content_block_delta":
            delta = chunk_data.get("delta", {})
            if delta.get("type") == "text_delta":
                return {"type": "content", "content": delta.get("text", "")}
            elif delta.get("type") == "input_json_delta":
                return {"type": "tool_input", "data": delta.get("partial_json", "")}
        elif chunk_type == "content_block_start":
            content_block = chunk_data.get("content_block", {})
            if content_block.get("type") == "tool_use":
                return {"type": "tool_start", "tool": content_block}
        
        return {"type": "other", "data": chunk_data}