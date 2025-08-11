"""
Pipeline operations for Alloy.

Provides three methods for creating pipelines:
1. Operator overloading: value >> func1 >> func2
2. Context manager: with pipeline() as p: ...
3. Functional: P(op1, op2, op3)
"""

import builtins
import sys
from typing import Any, Callable, List, Optional, Union, TypeVar, Generic
from contextlib import contextmanager

T = TypeVar('T')
U = TypeVar('U')


class PipelineValue(Generic[T]):
    """
    Wrapper class that enables >> operator on any value.
    
    This class acts as a transparent proxy to the wrapped value,
    supporting all operations while enabling pipeline chaining.
    
    The class implements the full Python data model to make wrapped
    values behave identically to their unwrapped counterparts.
    """
    
    def __init__(self, value: T):
        self.value = value
    
    def __rshift__(self, func: Callable[[T], Any]) -> 'PipelineValue':
        """
        Enable >> chaining for any value.
        
        Always returns a PipelineValue to maintain chaining capability,
        but the PipelineValue acts transparently like the wrapped value.
        
        Exceptions bubble up naturally in the pipeline.
        """
        import inspect
        
        # Try to determine if function can accept an argument
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            
            # If function has no parameters or all parameters have defaults,
            # try calling it without arguments first
            if (not params or 
                all(p.default != inspect.Parameter.empty for p in params)):
                try:
                    result = func()
                except TypeError:
                    # If that fails, try with the value
                    result = func(self.value)
            else:
                # Function has required parameters, pass the value
                result = func(self.value)
        except (ValueError, TypeError):
            # If signature inspection fails, try with value first
            try:
                result = func(self.value)
            except TypeError:
                # If that fails, try without arguments
                result = func()
        
        # Always wrap result to maintain chaining
        if isinstance(result, PipelineValue):
            return result
        return PipelineValue(result)
    
    def unwrap(self) -> T:
        """Extract the wrapped value."""
        return self.value
    
    # Make PipelineValue transparent by delegating all operations to the wrapped value
    def __eq__(self, other: Any) -> bool:
        """Enable equality comparison with the wrapped value."""
        if isinstance(other, PipelineValue):
            return self.value == other.value
        return self.value == other
    
    def __ne__(self, other: Any) -> bool:
        """Enable inequality comparison with the wrapped value."""
        return not self.__eq__(other)
    
    def __lt__(self, other: Any) -> bool:
        """Enable less than comparison with the wrapped value."""
        if isinstance(other, PipelineValue):
            return self.value < other.value
        return self.value < other
    
    def __le__(self, other: Any) -> bool:
        """Enable less than or equal comparison with the wrapped value."""
        if isinstance(other, PipelineValue):
            return self.value <= other.value
        return self.value <= other
    
    def __gt__(self, other: Any) -> bool:
        """Enable greater than comparison with the wrapped value."""
        if isinstance(other, PipelineValue):
            return self.value > other.value
        return self.value > other
    
    def __ge__(self, other: Any) -> bool:
        """Enable greater than or equal comparison with the wrapped value."""
        if isinstance(other, PipelineValue):
            return self.value >= other.value
        return self.value >= other
    
    def __hash__(self) -> int:
        """Enable hashing of the wrapped value."""
        return hash(self.value)
    
    def __str__(self) -> str:
        """String representation delegates to wrapped value."""
        return str(self.value)
    
    def __format__(self, format_spec: str) -> str:
        """Format string delegates to wrapped value."""
        return format(self.value, format_spec)
    
    
    def __repr__(self) -> str:
        """For debugging, show it's a PipelineValue."""
        return f"PipelineValue({self.value!r})"
    
    def __bool__(self) -> bool:
        """Boolean conversion delegates to wrapped value."""
        return bool(self.value)
    
    def __len__(self) -> int:
        """Length operation delegates to wrapped value."""
        return len(self.value)
    
    def __getitem__(self, key):
        """Item access delegates to wrapped value."""
        return self.value[key]
    
    def __setitem__(self, key, value):
        """Item assignment delegates to wrapped value."""
        self.value[key] = value
    
    def __iter__(self):
        """Iteration delegates to wrapped value."""
        return iter(self.value)
    
    def __bytes__(self) -> bytes:
        """Bytes conversion delegates to wrapped value."""
        if hasattr(self.value, '__bytes__'):
            return bytes(self.value)
        return str(self.value).encode('utf-8')
    
    def __contains__(self, item):
        """Contains check delegates to wrapped value."""
        return item in self.value
    
    def __add__(self, other):
        """Addition delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value + other.value)
        return PipelineValue(self.value + other)
    
    def __radd__(self, other):
        """Right addition delegates to wrapped value."""
        return PipelineValue(other + self.value)
    
    def __sub__(self, other):
        """Subtraction delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value - other.value)
        return PipelineValue(self.value - other)
    
    def __rsub__(self, other):
        """Right subtraction delegates to wrapped value."""
        return PipelineValue(other - self.value)
    
    def __mul__(self, other):
        """Multiplication delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value * other.value)
        return PipelineValue(self.value * other)
    
    def __rmul__(self, other):
        """Right multiplication delegates to wrapped value."""
        return PipelineValue(other * self.value)
    
    def __truediv__(self, other):
        """True division delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value / other.value)
        return PipelineValue(self.value / other)
    
    def __rtruediv__(self, other):
        """Right true division delegates to wrapped value."""
        return PipelineValue(other / self.value)
    
    def __floordiv__(self, other):
        """Floor division delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value // other.value) 
        return PipelineValue(self.value // other)
    
    def __rfloordiv__(self, other):
        """Right floor division delegates to wrapped value."""
        return PipelineValue(other // self.value)
    
    def __mod__(self, other):
        """Modulo delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value % other.value)
        return PipelineValue(self.value % other)
    
    def __rmod__(self, other):
        """Right modulo delegates to wrapped value."""
        return PipelineValue(other % self.value)
    
    def __pow__(self, other):
        """Power delegates to wrapped value."""
        if isinstance(other, PipelineValue):
            return PipelineValue(self.value ** other.value)
        return PipelineValue(self.value ** other)
    
    def __rpow__(self, other):
        """Right power delegates to wrapped value."""
        return PipelineValue(other ** self.value)
    
    def __getattr__(self, name):
        """Attribute access delegates to wrapped value."""
        attr = getattr(self.value, name)
        if callable(attr):
            # If it's a method, wrap the result in PipelineValue
            def wrapper(*args, **kwargs):
                # Special handling for string join method - unwrap PipelineValue arguments
                if name == 'join' and args:
                    unwrapped_args = []
                    for arg in args:
                        if hasattr(arg, '__iter__') and not isinstance(arg, (str, bytes)):
                            # It's an iterable, unwrap each PipelineValue in it
                            unwrapped_args.append([
                                str(item.value) if isinstance(item, PipelineValue) else str(item) 
                                for item in arg
                            ])
                        else:
                            unwrapped_args.append(
                                str(arg.value) if isinstance(arg, PipelineValue) else str(arg)
                            )
                    result = attr(*unwrapped_args, **kwargs)
                else:
                    result = attr(*args, **kwargs)
                
                if isinstance(result, PipelineValue):
                    return result
                return PipelineValue(result) if result is not None else result
            return wrapper
        return attr


def _make_pipeable(value: Any) -> PipelineValue:
    """
    Convert any value to a pipeable form.
    
    - Wrap in PipelineValue for pipeline operations
    """
    if isinstance(value, PipelineValue):
        return value
    return PipelineValue(value)


# Import operator module for monkey patching
import operator


# Store original __rshift__ methods to avoid conflicts
_original_rshift_methods = {}


def _enable_pipeline_operators():
    """
    Enable pipeline operators using a different approach since we can't
    monkey patch built-in types directly.
    
    Instead, we'll provide helper functions and rely on the pipe() function
    to create pipeable values.
    """
    # We can't monkey patch built-in types, so this is now a no-op
    # Users will need to use pipe() for built-in types or Result objects
    pass


class Pipeline:
    """
    Context manager for pipeline operations.
    
    Allows:
    with pipeline() as p:
        data = p.load_data("file.csv")
        result = p.process(data)
        p.save(result)
        final = p.execute()
    """
    
    def __init__(self):
        self.operations: List[Callable] = []
        self.results: List[Any] = []
        self._current_value = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up if needed
        pass
    
    def __call__(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation and track it.
        
        This allows: p.some_func(args) or p(some_func, args)
        """
        return self.execute(operation, *args, **kwargs)
    
    def __getattr__(self, name: str) -> Callable:
        """
        Allow calling methods like p.some_function(args).
        
        This enables: p.load_data("file.csv")
        """
        def wrapper(*args, **kwargs):
            # Try to find the function in various scopes
            func = None
            
            # Check if it's a method of a global object
            frame = sys._getframe(1)
            
            # Look in caller's locals and globals
            if name in frame.f_locals:
                func = frame.f_locals[name]
            elif name in frame.f_globals:
                func = frame.f_globals[name]
            else:
                raise AttributeError(f"Function '{name}' not found in pipeline scope")
            
            return self.execute(func, *args, **kwargs)
        
        return wrapper
    
    def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation in the pipeline context.
        
        The operation can be:
        - A regular function
        - An Agent object (callable)
        - A command object
        """
        try:
            # If we have args/kwargs, call with them
            if args or kwargs:
                result = operation(*args, **kwargs)
            # If the current value exists and operation takes parameters
            elif self._current_value is not None:
                # Try to call with current value
                try:
                    result = operation(self._current_value)
                except TypeError:
                    # If that fails, call without args
                    result = operation()
            else:
                # Call without arguments
                result = operation()
            
            # Store the operation and result
            self.operations.append(operation)
            self.results.append(result)
            
            # Update current value and return result directly
            self._current_value = result
            return result
        
        except Exception as e:
            # Let exceptions bubble up naturally
            self.results.append(e)
            raise e


def P(*operations: Callable) -> Any:
    """
    Functional pipeline that executes operations in sequence.
    
    Usage:
    result = P(
        lambda: load_data("file.csv"),
        validate_data,
        lambda d: agent(Analyze(d)),
        format_report
    )
    
    Each operation receives the result of the previous operation.
    If any operation fails (raises exception), the pipeline stops and
    the exception bubbles up naturally.
    """
    if not operations:
        raise ValueError("P() requires at least one operation")
    
    # Start with the first operation
    current = operations[0]()
    
    # Apply remaining operations
    for operation in operations[1:]:
        current = operation(current)
    
    # Return final result directly
    return current


@contextmanager
def pipeline():
    """
    Create a pipeline context manager.
    
    Usage:
    with pipeline() as p:
        data = p.load_data("file.csv")
        result = p.process(data)
        final = p.execute()
    """
    yield Pipeline()


# Initialize pipeline operators when module is imported
_enable_pipeline_operators()


def unwrap_pipeline_values(*values):
    """
    Utility function to unwrap PipelineValue objects.
    
    This is useful when passing pipeline results to functions that don't
    expect PipelineValue objects.
    
    Usage:
    result = some_function(*unwrap_pipeline_values(val1, val2, val3))
    """
    return [val.value if isinstance(val, PipelineValue) else val for val in values]


# Convenience functions for creating pipeable values
def pipe(value: Any) -> PipelineValue:
    """
    Explicitly create a pipeable value.
    
    Usage:
    result = pipe("hello") >> str.upper >> str.split
    
    The result behaves like the original value for all operations
    (comparisons, arithmetic, etc.) while supporting pipeline chaining.
    """
    return PipelineValue(value)


# Monkey patch operator for common types by creating a start function
def start_pipeline(value: Any) -> PipelineValue:
    """
    Alternative to pipe() for starting pipelines.
    
    Usage:
    from alloy.core.pipeline import start_pipeline as _
    result = _(value) >> func1 >> func2
    """
    return PipelineValue(value)


def from_value(value: Any) -> PipelineValue:
    """
    Convert any value to a pipeable form.
    
    Wraps the value in PipelineValue for pipeline operations.
    The result behaves transparently like the original value.
    """
    return PipelineValue(value)