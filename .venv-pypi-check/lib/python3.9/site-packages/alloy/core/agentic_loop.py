"""
Agentic loop implementation for autonomous agent behavior.
Supports tool calling, planning, and multi-step reasoning.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import asyncio

# Removed Agent import to avoid circular dependency
from ..providers.base import ToolDefinition, ToolCall, ToolResult


@dataclass
class AgentStep:
    """Base class for agent steps in the loop."""
    content: str
    step_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThoughtStep(AgentStep):
    """Agent reasoning/planning step."""
    step_type: str = field(default="thought")


@dataclass
class ActionStep(AgentStep):
    """Agent action (tool call) step."""
    step_type: str = field(default="action")
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservationStep(AgentStep):
    """Observation of action result."""
    step_type: str = field(default="observation")
    success: bool = True
    result: Any = None
    error_message: Optional[str] = None


@dataclass
class FinishStep(AgentStep):
    """Final answer/completion step."""
    step_type: str = field(default="finish")
    final_answer: Any = None


class ToolRegistry:
    """Registry for tools available to agents."""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_definitions: Dict[str, ToolDefinition] = {}
    
    def register_tool(
        self, 
        func: Callable, 
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """Register a tool function."""
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Auto-generate parameters from function signature if not provided
        if parameters is None:
            parameters = self._extract_parameters_from_function(func)
        
        self._tools[tool_name] = func
        self._tool_definitions[tool_name] = ToolDefinition(
            name=tool_name,
            description=tool_description,
            parameters=parameters
        )
    
    def _extract_parameters_from_function(self, func: Callable) -> Dict[str, Any]:
        """Extract parameter schema from function signature."""
        import inspect
        
        sig = inspect.signature(func)
        properties = {}
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
            
            properties[param_name] = param_info
        
        return properties
    
    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call."""
        if tool_call.name not in self._tools:
            return ToolResult(
                tool_call_id=tool_call.id,
                result=None,
                error=f"Unknown tool: {tool_call.name}"
            )
        
        try:
            tool_func = self._tools[tool_call.name]
            
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_call.arguments)
            else:
                result = tool_func(**tool_call.arguments)
            
            return ToolResult(
                tool_call_id=tool_call.id,
                result=result
            )
        
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                result=None,
                error=str(e)
            )
    
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Get all registered tool definitions."""
        return list(self._tool_definitions.values())
    
    def get_tool_names(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())


class AgenticLoop:
    """
    Core agentic loop implementation.
    
    Implements a ReAct (Reasoning + Acting) pattern where the agent:
    1. Thinks about the problem
    2. Takes an action (uses a tool or provides final answer)
    3. Observes the result
    4. Repeats until goal is achieved
    """
    
    def __init__(
        self,
        agent: Any,  # Any agent with _simple_call method
        tools: Optional[ToolRegistry] = None,
        max_iterations: int = 10,
        max_tool_calls_per_iteration: int = 5
    ):
        self.agent = agent
        self.tools = tools or ToolRegistry()
        self.max_iterations = max_iterations
        self.max_tool_calls_per_iteration = max_tool_calls_per_iteration
        self.conversation_history: List[AgentStep] = []
    
    async def run(self, goal: str, context: Optional[str] = None) -> str:
        """
        Run the agentic loop to achieve the goal.
        
        Args:
            goal: The goal/task to accomplish
            context: Optional additional context
            
        Returns:
            The final answer
            
        Raises:
            Exception: If goal cannot be achieved
        """
        self.conversation_history.clear()
        
        # Build initial prompt with tools and goal
        tools_info = self._build_tools_prompt()
        system_prompt = f"""You are an autonomous agent. Your goal is: {goal}

{tools_info}

Follow this pattern:
1. Thought: Think about what you need to do next
2. Action: Either use a tool or provide your final answer
3. Observation: Observe the result of your action

Use this exact format:
Thought: [your reasoning]
Action: [tool_name(arg1="value1", arg2="value2") OR Final Answer: your answer]
Observation: [this will be filled by the system]

Begin!"""
        
        if context:
            system_prompt += f"\n\nAdditional context: {context}"
        
        for iteration in range(self.max_iterations):
            # Build conversation context
            conversation_context = self._build_conversation_context()
            full_prompt = f"{system_prompt}\n\n{conversation_context}"
            
            # Get agent response (use simple call to avoid recursion)
            response = await self.agent._simple_call(full_prompt)
            
            # Handle case where agent has structured output - return the parsed result directly
            if not isinstance(response, str):
                return str(response)
            
            # Parse the response for ReAct format
            parsed_steps = self._parse_agent_response(response)
            
            # Process each step
            for step in parsed_steps:
                self.conversation_history.append(step)
                
                # Handle different step types
                if isinstance(step, FinishStep):
                    return step.final_answer
                
                elif isinstance(step, ActionStep) and step.tool_name:
                    # Execute tool call
                    tool_call = ToolCall(
                        id=f"call_{iteration}_{len(self.conversation_history)}",
                        name=step.tool_name,
                        arguments=step.tool_args
                    )
                    
                    tool_result = await self.tools.execute_tool(tool_call)
                    
                    # Create observation step
                    observation = ObservationStep(
                        content=f"Tool '{step.tool_name}' executed",
                        success=tool_result.error is None,
                        result=tool_result.result,
                        error_message=tool_result.error
                    )
                    self.conversation_history.append(observation)
                    
                    # Check if we have a final result
                    if tool_result.error is None and self._is_goal_likely_achieved(tool_result.result, goal):
                        return str(tool_result.result)
        
        # Max iterations reached
        raise Exception(f"Max iterations ({self.max_iterations}) reached without completing goal")
    
    def _build_tools_prompt(self) -> str:
        """Build the tools section of the prompt."""
        if not self.tools.get_tool_names():
            return """No tools available. You should think through the problem and provide a final answer.
Since you have no tools, your Action should be: Final Answer: [your complete answer to the question]"""
        
        tools_list = []
        for tool_def in self.tools.get_tool_definitions():
            params_str = ", ".join([
                f"{name}={info.get('type', 'string')}" 
                for name, info in tool_def.parameters.items()
            ])
            tools_list.append(f"- {tool_def.name}({params_str}): {tool_def.description}")
        
        return "Available tools:\n" + "\n".join(tools_list)
    
    def _build_conversation_context(self) -> str:
        """Build conversation context from history."""
        if not self.conversation_history:
            return ""
        
        context_parts = []
        for step in self.conversation_history[-10:]:  # Last 10 steps
            if isinstance(step, ThoughtStep):
                context_parts.append(f"Thought: {step.content}")
            elif isinstance(step, ActionStep):
                if step.tool_name:
                    args_str = ", ".join([f"{k}=\"{v}\"" for k, v in step.tool_args.items()])
                    context_parts.append(f"Action: {step.tool_name}({args_str})")
                else:
                    context_parts.append(f"Action: {step.content}")
            elif isinstance(step, ObservationStep):
                if step.success:
                    context_parts.append(f"Observation: {step.result}")
                else:
                    context_parts.append(f"Observation: Error - {step.error_message}")
        
        return "\n".join(context_parts)
    
    def _parse_agent_response(self, response: str) -> List[AgentStep]:
        """Parse agent response into structured steps."""
        steps = []
        lines = response.strip().split('\n')
        
        current_step_type = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for step markers
            if line.startswith("Thought:"):
                if current_step_type and current_content:
                    steps.append(self._create_step(current_step_type, "\n".join(current_content)))
                current_step_type = "thought"
                current_content = [line[8:].strip()]
            
            elif line.startswith("Action:"):
                if current_step_type and current_content:
                    steps.append(self._create_step(current_step_type, "\n".join(current_content)))
                
                action_content = line[7:].strip()
                # Check if this is "Action: Final Answer: ..."
                if action_content.startswith("Final Answer:"):
                    final_answer_content = action_content[13:].strip()
                    steps.append(FinishStep(content=final_answer_content, final_answer=final_answer_content))
                    current_step_type = None
                    current_content = []
                else:
                    current_step_type = "action"
                    current_content = [action_content]
            
            elif line.startswith("Final Answer:"):
                content = line[13:].strip()
                steps.append(FinishStep(content=content, final_answer=content))
                current_step_type = None
                current_content = []
            
            else:
                # Continuation of current step
                if current_step_type:
                    current_content.append(line)
        
        # Handle final step
        if current_step_type and current_content:
            steps.append(self._create_step(current_step_type, "\n".join(current_content)))
        
        return steps
    
    def _create_step(self, step_type: str, content: str) -> AgentStep:
        """Create appropriate step object from type and content."""
        if step_type == "thought":
            return ThoughtStep(content=content)
        
        elif step_type == "action":
            # Try to parse tool call
            tool_name, tool_args = self._parse_tool_call(content)
            if tool_name:
                return ActionStep(
                    content=content,
                    tool_name=tool_name,
                    tool_args=tool_args
                )
            else:
                return ActionStep(content=content)
        
        else:
            return AgentStep(step_type=step_type, content=content)
    
    def _parse_tool_call(self, action_content: str) -> tuple[Optional[str], Dict[str, Any]]:
        """Parse tool call from action content."""
        import re
        
        # Pattern: tool_name(arg1="value1", arg2="value2")
        pattern = r'(\w+)\((.*?)\)'
        match = re.match(pattern, action_content.strip())
        
        if not match:
            return None, {}
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        # Parse arguments
        args = {}
        if args_str.strip():
            # Simple argument parsing (could be more robust)
            for arg_pair in args_str.split(','):
                if '=' in arg_pair:
                    key, value = arg_pair.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    args[key] = value
        
        return tool_name, args
    
    def _is_goal_likely_achieved(self, result: Any, goal: str) -> bool:
        """Simple heuristic to check if goal might be achieved."""
        # This is a simple heuristic - could be made more sophisticated
        if isinstance(result, str) and len(result) > 20:
            return True
        if isinstance(result, (dict, list)) and result:
            return True
        return False


# Decorator for registering tools
def tool(func: Optional[Callable] = None, *, name: Optional[str] = None, description: Optional[str] = None):
    """Decorator to register a function as a tool."""
    def decorator(f: Callable) -> Callable:
        # Add metadata to function for later registration
        f._is_tool = True
        f._tool_name = name or f.__name__
        f._tool_description = description or f.__doc__ or f"Tool: {f.__name__}"
        return f
    
    if func is None:
        return decorator
    else:
        return decorator(func)