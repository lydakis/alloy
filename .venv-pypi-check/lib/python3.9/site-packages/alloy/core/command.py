"""
Command decorator system for natural language template creation.

This module implements the @command decorator that allows functions to be converted
into command templates with parameter substitution in docstrings.
"""

import inspect
import re
from typing import Any, Callable, Dict, Optional, Union
from functools import wraps


class Command:
    """
    A command object that represents a natural language template.
    
    Commands are created by decorating functions with @command and provide
    a callable interface that generates formatted prompt strings by substituting
    parameters into the function's docstring template.
    """
    
    def __init__(self, func: Callable, name: Optional[str] = None):
        """
        Initialize a Command from a function.
        
        Args:
            func: The function to convert to a command
            name: Optional custom name for the command (defaults to function name)
        """
        self._func = func
        self.name = name or func.__name__
        self.description = func.__doc__ or f"Command: {self.name}"
        
        # Extract function signature for parameter validation
        self._signature = inspect.signature(func)
        self._parameters = list(self._signature.parameters.keys())
        
        # Extract template from docstring
        self._template = self._extract_template()
        
        # Find template placeholders
        self._placeholders = self._find_placeholders()
        
        # Store function metadata
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = func.__module__
        self.__qualname__ = getattr(func, '__qualname__', func.__name__)
        self.__annotations__ = getattr(func, '__annotations__', {})
    
    def _extract_template(self) -> str:
        """Extract the template string from the function's docstring."""
        if not self.description or self.description == f"Command: {self.name}":
            return f"Execute {self.name} with the provided parameters"
        
        # Use the entire docstring as the template
        return self.description.strip()
    
    def _find_placeholders(self) -> set:
        """Find all {parameter} placeholders in the template."""
        placeholders = set()
        for match in re.finditer(r'\{([^}]+)\}', self._template):
            placeholders.add(match.group(1))
        return placeholders
    
    def _validate_parameters(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Validate and bind parameters to function signature.
        
        Returns:
            Dict mapping parameter names to their values
        """
        try:
            # Bind arguments to function signature
            bound = self._signature.bind(*args, **kwargs)
            bound.apply_defaults()
            return dict(bound.arguments)
        except TypeError as e:
            raise ValueError(f"Invalid parameters for command '{self.name}': {e}")
    
    def _format_template(self, params: Dict[str, Any]) -> str:
        """
        Format the template string with parameter values.
        
        Args:
            params: Dictionary of parameter names to values
            
        Returns:
            Formatted template string
        """
        try:
            # Convert all values to strings for template substitution
            str_params = {k: str(v) for k, v in params.items()}
            return self._template.format(**str_params)
        except KeyError as e:
            missing_param = e.args[0]
            raise ValueError(
                f"Template parameter '{missing_param}' not found in function parameters. "
                f"Available parameters: {list(params.keys())}"
            )
        except Exception as e:
            raise ValueError(f"Error formatting template for command '{self.name}': {e}")
    
    def __call__(self, *args, **kwargs) -> str:
        """
        Execute the command by formatting the template with provided parameters.
        
        Args:
            *args: Positional arguments for the command
            **kwargs: Keyword arguments for the command
            
        Returns:
            Formatted prompt string ready for agent consumption
        """
        # Validate and bind parameters
        params = self._validate_parameters(*args, **kwargs)
        
        # Format template with parameters
        return self._format_template(params)
    
    def __repr__(self) -> str:
        """String representation of the command."""
        return f"Command(name='{self.name}', parameters={self._parameters})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Command '{self.name}': {self.description}"
    
    def help(self) -> str:
        """
        Return help information about the command.
        
        Returns:
            Formatted help string with command details
        """
        lines = [
            f"Command: {self.name}",
            f"Description: {self.description}",
            f"Parameters: {', '.join(self._parameters)}",
            f"Template: {self._template}",
        ]
        
        if self._placeholders:
            lines.append(f"Template placeholders: {', '.join(sorted(self._placeholders))}")
        
        return "\n".join(lines)


def command(func: Optional[Callable] = None, *, name: Optional[str] = None) -> Union[Command, Callable]:
    """
    Decorator to convert a function into a Command object.
    
    The decorated function's docstring becomes a template where {parameter}
    placeholders are substituted with actual parameter values when called.
    
    Args:
        func: Function to decorate (when used as @command)
        name: Optional custom name for the command
        
    Returns:
        Command object that can be called to generate formatted prompts
        
    Examples:
        @command
        def Analyze(data, focus_area="general"):
            '''Analyze the following data for {focus_area} patterns: {data}'''
        
        @command(name="CustomSummarize")
        def summarize_text(text, max_words=100):
            '''Summarize the following text in {max_words} words: {text}'''
        
        # Usage:
        prompt = Analyze(sales_data, focus_area="seasonal")
        result = agent(prompt)
    """
    def decorator(f: Callable) -> Command:
        return Command(f, name=name)
    
    if func is None:
        # Called with arguments: @command(name="...")
        return decorator
    else:
        # Called without arguments: @command
        return decorator(func)


# Convenience function for creating commands dynamically
def create_command(name: str, template: str, parameters: Optional[list] = None) -> Command:
    """
    Create a Command object dynamically without using the decorator.
    
    Args:
        name: Name of the command
        template: Template string with {parameter} placeholders
        parameters: List of parameter names (extracted from template if not provided)
        
    Returns:
        Command object
        
    Examples:
        analyze_cmd = create_command(
            "Analyze",
            "Analyze the following data for {focus_area} patterns: {data}",
            ["data", "focus_area"]
        )
    """
    if parameters is None:
        # Extract parameters from template placeholders in order of appearance
        parameters = []
        seen = set()
        for match in re.finditer(r'\{([^}]+)\}', template):
            param = match.group(1)
            if param not in seen:
                parameters.append(param)
                seen.add(param)
    
    # Create a dummy function with the right signature
    param_strings = []
    for param in parameters:
        param_strings.append(f"{param}=None")
    
    func_code = f"def {name}({', '.join(param_strings)}): pass"
    namespace = {}
    exec(func_code, namespace)
    func = namespace[name]
    func.__doc__ = template
    
    return Command(func, name=name)