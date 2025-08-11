"""
Agent class - ONE class that handles everything cleanly.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable, Iterator, AsyncIterator
from dataclasses import dataclass, is_dataclass
import json
import asyncio
import concurrent.futures
import inspect

from .memory import Memory
from .agentic_loop import AgenticLoop, ToolRegistry
from ..providers.base import ModelProvider, ToolDefinition
from ..providers.registry import get_provider

T = TypeVar('T')


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class ModelNotFoundError(AgentError):
    """Raised when the specified model is not available."""
    pass


class StructuredOutputError(AgentError):
    """Raised when structured output parsing fails."""
    pass


@dataclass
class AgentConfig:
    """Configuration for Agent behavior."""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


class Agent:
    """
    AI Agent - handles LLM communication with optional tools and memory.
    
    Simple, clean interface:
    - agent = Agent("gpt-4") - basic LLM
    - agent = Agent("gpt-4", tools=[func]) - with tools
    - agent = Agent("gpt-4", memory=Memory()) - with memory
    - agent = Agent("gpt-4", tools=[func], memory=Memory()) - full agent
    """
    
    def __init__(
        self,
        model: str,
        provider: Optional[ModelProvider] = None,
        output_schema: Optional[Type] = None,
        instructions: Optional[List[str]] = None,
        memory: Optional[Memory] = None,
        tools: Optional[List[Union[Callable, ToolDefinition]]] = None,
        config: Optional[AgentConfig] = None,
        api_key: Optional[str] = None,
        max_iterations: int = 10,
        **kwargs
    ):
        """
        Initialize an Agent.
        
        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3.5-sonnet")
            provider: Model provider instance (auto-detected if None)
            output_schema: Expected output schema for structured responses
            instructions: List of behavioral instructions
            memory: Memory instance for conversation history (creates default if None)
            tools: List of tools/functions the agent can use
            config: Agent configuration
            api_key: API key for the provider
            max_iterations: Maximum iterations for agentic reasoning
            **kwargs: Additional configuration options
        """
        self.model = model
        
        # Get provider instance
        if isinstance(provider, ModelProvider):
            self.provider = provider
        else:
            self.provider = get_provider(model, api_key=api_key, **kwargs)
        
        self.output_schema = output_schema
        self.instructions = instructions or []
        self.memory = memory or Memory()
        self.config = config or AgentConfig()
        self.max_iterations = max_iterations
        
        # Process tools
        self._tool_functions = {}  # name -> callable
        self.tools = []  # ToolDefinition objects for API calls
        self._tool_registry = ToolRegistry()
        
        if tools:
            self._process_and_register_tools(tools)
        
        # Build system prompt
        self._system_prompt = self._build_system_prompt()
    
    def _process_and_register_tools(self, tools: List[Union[Callable, ToolDefinition]]) -> None:
        """Process tools and register both functions and definitions."""
        for tool in tools:
            if isinstance(tool, ToolDefinition):
                self.tools.append(tool)
            elif callable(tool):
                tool_def = self._function_to_tool_definition(tool)
                self.tools.append(tool_def)
                self._tool_functions[tool_def.name] = tool
                self._tool_registry.register_tool(tool)
    
    def _function_to_tool_definition(self, func: Callable) -> ToolDefinition:
        """Convert a Python function to a ToolDefinition."""
        name = getattr(func, '_tool_name', func.__name__)
        description = getattr(func, '_tool_description', func.__doc__ or f"Function: {func.__name__}")
        
        # Extract parameters from function signature
        sig = inspect.signature(func)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            param_info = {"type": "string"}  # Default type
            
            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list:
                    param_info["type"] = "array"
                elif param.annotation == dict:
                    param_info["type"] = "object"
            
            # Check if parameter has default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            
            parameters[param_name] = param_info
        
        return ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            required=required
        )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt from instructions, schema, and tools."""
        parts = []
        
        if self.instructions:
            parts.append("Instructions:")
            for instruction in self.instructions:
                parts.append(f"- {instruction}")
            parts.append("")
        
        if self.output_schema:
            parts.append(self._build_schema_prompt())
        
        if self.tools:
            parts.append(self._build_tools_prompt())
        
        return "\n".join(parts)
    
    def _build_schema_prompt(self) -> str:
        """Build prompt section for structured output."""
        if not self.output_schema:
            return ""
        
        schema_name = getattr(self.output_schema, '__name__', 'Output')
        
        if is_dataclass(self.output_schema):
            # Generate JSON schema from dataclass
            fields = []
            for field in self.output_schema.__dataclass_fields__.values():
                field_type = field.type
                type_name = getattr(field_type, '__name__', str(field_type))
                fields.append(f'  "{field.name}": {type_name}')
            
            schema_example = "{\n" + ",\n".join(fields) + "\n}"
        else:
            schema_example = f"{{/* {schema_name} structure */}}"
        
        return f"""
Output Format:
Please respond with valid JSON matching this structure:
{schema_example}

Do not include any text outside the JSON response."""
    
    def _build_tools_prompt(self) -> str:
        """Build prompt section for available tools."""
        if not self.tools:
            return ""
        
        tool_descriptions = []
        for tool in self.tools:
            name = tool.name
            description = tool.description
            tool_descriptions.append(f"- {name}: {description}")
        
        return f"""
Available Tools:
{chr(10).join(tool_descriptions)}

You can use these tools to help solve problems."""
    
    def _parse_structured_output(self, response: str) -> Any:
        """Parse structured output according to the schema."""
        if not self.output_schema:
            return response
        
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Handle common cases where model adds extra text
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            data = json.loads(response)
            
            # Convert to schema type if it's a dataclass
            if is_dataclass(self.output_schema):
                return self.output_schema(**data)
            
            return data
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise StructuredOutputError(
                f"Failed to parse response as {self.output_schema.__name__}: {e}\n"
                f"Response was: {response}"
            )
    
    def _create_structured_output_schema(self, schema: Type) -> Dict[str, Any]:
        """Create structured output schema for the provider."""
        if is_dataclass(schema):
            # Generate JSON schema from dataclass
            properties = {}
            required = []
            
            from dataclasses import MISSING
            
            for field in schema.__dataclass_fields__.values():
                field_type = field.type
                
                # Handle Optional types and union types
                if hasattr(field_type, '__origin__'):
                    if field_type.__origin__ is list:
                        # Get the list item type
                        item_type = field_type.__args__[0] if field_type.__args__ else str
                        
                        # Map item type to JSON schema type
                        if item_type == str:
                            item_schema = {"type": "string"}
                        elif item_type == int:
                            item_schema = {"type": "integer"}
                        elif item_type == float:
                            item_schema = {"type": "number"}
                        elif item_type == bool:
                            item_schema = {"type": "boolean"}
                        else:
                            item_schema = {"type": "string"}
                        
                        properties[field.name] = {
                            "type": "array",
                            "items": item_schema
                        }
                        if field.default is MISSING and field.default_factory is MISSING:
                            required.append(field.name)
                        continue
                
                # Simple type mapping
                if field_type == str:
                    properties[field.name] = {"type": "string"}
                elif field_type == int:
                    properties[field.name] = {"type": "integer"}
                elif field_type == float:
                    properties[field.name] = {"type": "number"}
                elif field_type == bool:
                    properties[field.name] = {"type": "boolean"}
                elif field_type == list:
                    properties[field.name] = {"type": "array"}
                else:
                    properties[field.name] = {"type": "string"}
                
                # Check if field is required
                if field.default is MISSING and field.default_factory is MISSING:
                    required.append(field.name)
            
            use_strict = len(required) == len(properties)
            
            schema_obj = {
                "type": "object",
                "properties": properties,
                "additionalProperties": False
            }
            
            if required:
                schema_obj["required"] = required
            
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema_obj,
                    "strict": use_strict
                }
            }
        
        return {"type": "json_object"}
    
    async def _make_call(self, prompt: str, **kwargs) -> str:
        """Make the actual API call with retries."""
        context = self.memory.get_context()
        
        # Build messages array
        messages = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        
        if context:
            messages.append({"role": "assistant", "content": context})
        
        messages.append({"role": "user", "content": prompt})
        
        # Prepare call parameters
        call_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        # Add tools if available
        if self.tools:
            call_params["tools"] = self.tools
        
        # Add response format for structured output
        if self.output_schema:
            response_format = self._create_structured_output_schema(self.output_schema)
            call_params["response_format"] = response_format
        
        call_params.update(kwargs)
        
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self.provider.call(**call_params)
                
                # Extract content and handle tool calls
                content = response.content
                if response.tool_calls:
                    # Check if this is a structured output tool call
                    structured_output_call = None
                    for tool_call in response.tool_calls:
                        if tool_call.name == "structured_output":
                            structured_output_call = tool_call
                            break
                    
                    if structured_output_call and self.output_schema:
                        # For structured output tool calls, return the arguments as JSON
                        content = json.dumps(structured_output_call.arguments)
                    else:
                        # For regular tool calls, include tool call info in response
                        tool_info = f"\n\nTool calls made: {[tc.name for tc in response.tool_calls]}"
                        content += tool_info
                
                # Store in memory
                self.memory.add_exchange(prompt, content)
                
                return content
                
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise AgentError(f"Failed after {self.config.retry_attempts} attempts: {e}")
                
                # Wait before retry
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise AgentError("Unexpected retry loop exit")
    
    def __call__(self, prompt: str, **kwargs) -> Any:
        """
        Call the agent (sync by default, like OpenAI/Anthropic).
        
        Uses agentic reasoning if tools are available, otherwise simple call.
        
        Args:
            prompt: Text prompt
            **kwargs: Additional parameters
            
        Returns:
            The agent's response (parsed if schema is set)
            
        Raises:
            AgentError: If the agent call fails
        """
        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use thread pool
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._call_async(prompt, **kwargs))
                    return future.result()
            except RuntimeError:
                # No running event loop, safe to use asyncio.run
                return asyncio.run(self._call_async(prompt, **kwargs))
            
        except Exception as e:
            raise AgentError(f"Agent call failed: {e}")
    
    async def async_call(self, prompt: str, **kwargs) -> Any:
        """
        Async call for better performance in async contexts.
        
        Args:
            prompt: Text prompt
            **kwargs: Additional parameters
            
        Returns:
            The agent's response (parsed if schema is set)
            
        Raises:
            AgentError: If the async call fails
        """
        try:
            return await self._call_async(prompt, **kwargs)
        except Exception as e:
            raise AgentError(f"Async call failed: {e}")
    
    async def _call_async(self, prompt: str, **kwargs) -> Any:
        """Internal async call implementation."""
        # If we have tools, use agentic reasoning
        if self.tools:
            loop = AgenticLoop(
                agent=self, 
                tools=self._tool_registry,
                max_iterations=self.max_iterations
            )
            return await loop.run(prompt)
        else:
            # Simple call without agentic reasoning
            response = await self._make_call(prompt, **kwargs)
            
            # Parse structured output if schema is set
            if self.output_schema:
                return self._parse_structured_output(response)
            
            return response
    
    async def _simple_call(self, prompt: str, **kwargs) -> Any:
        """Simple call that bypasses agentic reasoning (for internal use)."""
        response = await self._make_call(prompt, **kwargs)
        
        # Parse structured output if schema is set
        if self.output_schema:
            return self._parse_structured_output(response)
        
        return response
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Stream response chunks synchronously.
        
        Args:
            prompt: Text prompt
            **kwargs: Additional parameters
            
        Yields:
            Response chunks as strings as they arrive
            
        Raises:
            AgentError: If streaming fails
        """
        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, use thread pool
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_async_stream, prompt, **kwargs)
                    chunks = future.result()
                    for chunk in chunks:
                        yield chunk
            except RuntimeError:
                # No running event loop, safe to use asyncio.run
                chunks = asyncio.run(self._collect_stream_chunks(prompt, **kwargs))
                for chunk in chunks:
                    yield chunk
                    
        except Exception as e:
            raise AgentError(f"Streaming failed: {e}")
    
    def _run_async_stream(self, prompt: str, **kwargs) -> List[str]:
        """Helper to run async streaming in thread pool."""
        return asyncio.run(self._collect_stream_chunks(prompt, **kwargs))
    
    async def _collect_stream_chunks(self, prompt: str, **kwargs) -> List[str]:
        """Collect all stream chunks into a list for sync streaming."""
        chunks = []
        async for chunk in self.stream_async(prompt, **kwargs):
            chunks.append(chunk)
        return chunks
    
    async def stream_async(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Stream response chunks asynchronously.
        
        Args:
            prompt: Text prompt
            **kwargs: Additional parameters
            
        Yields:
            Response chunks as strings as they arrive
            
        Raises:
            AgentError: If async streaming fails
        """
        try:
            async for chunk in self._stream_call(prompt, **kwargs):
                yield chunk
        except Exception as e:
            raise AgentError(f"Async streaming failed: {e}")
    
    async def _stream_call(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Internal streaming call."""
        context = self.memory.get_context()
        
        # Build messages array
        messages = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        
        if context:
            messages.append({"role": "assistant", "content": context})
        
        messages.append({"role": "user", "content": prompt})
        
        # Prepare call parameters
        call_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        # Add tools if available
        if self.tools:
            call_params["tools"] = self.tools
        
        # Add response format for structured output
        if self.output_schema:
            response_format = self._create_structured_output_schema(self.output_schema)
            call_params["response_format"] = response_format
        
        call_params.update(kwargs)
        
        # Stream response
        full_response = ""
        async for chunk in self.provider.call_streaming(**call_params):
            content = None
            
            # Handle different chunk formats
            if isinstance(chunk, dict) and chunk.get("type") == "content":
                content = chunk.get("content", "")
            elif hasattr(chunk, 'content') and chunk.content:
                content = chunk.content
            elif isinstance(chunk, str):
                content = chunk
            
            if content:
                full_response += content
                yield content
        
        # Store complete response in memory
        if full_response:
            self.memory.add_exchange(prompt, full_response)
    
    def sync(self, prompt: str, **kwargs) -> Any:
        """
        Explicit sync call for blocking operations when async isn't available.
        
        This is an alias for __call__ but makes the synchronous nature explicit.
        
        Args:
            prompt: Text prompt
            **kwargs: Additional parameters
            
        Returns:
            The agent's response (parsed if schema is set)
            
        Raises:
            AgentError: If the agent call fails
        """
        return self.__call__(prompt, **kwargs)
    
    
    def remember(self, key: str, value: Any, tags: Optional[List[str]] = None) -> None:
        """Store a memory."""
        self.memory.remember(key, value, tags)
    
    def recall(self, key: str) -> Optional[Any]:
        """Retrieve a memory."""
        return self.memory.recall(key)
    
    def recall_all(self, tag: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve all memories, optionally filtered by tag."""
        return self.memory.recall_all(tag)
    
    def clear_memory(self) -> None:
        """Clear all memories."""
        self.memory.clear()
    
    def add_tool(self, func: Callable) -> None:
        """Add a tool to the agent."""
        tool_def = self._function_to_tool_definition(func)
        self.tools.append(tool_def)
        self._tool_functions[tool_def.name] = func
        self._tool_registry.register_tool(func)
        # Rebuild system prompt
        self._system_prompt = self._build_system_prompt()
    
    def remove_tool(self, name: str) -> None:
        """Remove a tool by name."""
        self.tools = [t for t in self.tools if t.name != name]
        if name in self._tool_functions:
            del self._tool_functions[name]
        # Note: ToolRegistry doesn't have remove method, would need to recreate
        self._tool_registry = ToolRegistry()
        for func in self._tool_functions.values():
            self._tool_registry.register_tool(func)
        # Rebuild system prompt
        self._system_prompt = self._build_system_prompt()
    
    def get_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def with_schema(self, schema: Type[T]) -> 'Agent':
        """Create a new agent instance with a different output schema."""
        return Agent(
            model=self.model,
            provider=self.provider,
            output_schema=schema,
            instructions=self.instructions,
            memory=self.memory,
            tools=list(self._tool_functions.values()),  # Pass the original functions
            config=self.config,
            max_iterations=self.max_iterations
        )