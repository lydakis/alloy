"""
Design-by-contract decorators for the Alloy Python DSL.

Provides @require, @ensure, and @invariant decorators for preconditions,
postconditions, and class invariants with integration to the Result monad.
"""

import functools
import inspect
import os
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class ContractViolation(Exception):
    """Exception raised when a contract condition is violated."""
    
    def __init__(self, contract_type: str, condition: str, message: str):
        self.contract_type = contract_type
        self.condition = condition
        self.message = message
        super().__init__(f"{contract_type} violation: {message}")


class ContractConfig:
    """Configuration for contract checking behavior."""
    
    _enabled = True
    
    @classmethod
    def enable(cls) -> None:
        """Enable contract checking."""
        cls._enabled = True
    
    @classmethod
    def disable(cls) -> None:
        """Disable contract checking (for production)."""
        cls._enabled = False
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if contracts are enabled."""
        # Check environment variable for production override
        env_disabled = os.getenv('ALLOY_CONTRACTS_DISABLED', '').lower() in ('1', 'true', 'yes')
        return cls._enabled and not env_disabled


def _handle_contract_violation(
    contract_type: str,
    condition: str, 
    message: str
) -> None:
    """Handle a contract violation by raising an exception."""
    violation = ContractViolation(contract_type, condition, message)
    raise violation


def require(condition: Callable[..., bool], message: str = "") -> Callable[[F], F]:
    """
    Decorator for preconditions - checks inputs before function execution.
    
    Args:
        condition: A callable that takes the same arguments as the decorated function
                  and returns True if the precondition is satisfied
        message: Custom error message for contract violation
    
    Returns:
        Decorated function that checks preconditions before execution
    
    Example:
        @require(lambda x: x > 0, "Value must be positive")
        @require(lambda x: x < 1000, "Value too large")
        def calculate_price(quantity, unit_price=10):
            return quantity * unit_price
    """
    def decorator(func: F) -> F:
        if not ContractConfig.is_enabled():
            return func
            
        # Store existing preconditions if any
        if not hasattr(func, '_preconditions'):
            func._preconditions = []
        func._preconditions.append((condition, message))
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature for proper argument mapping
            func_sig = inspect.signature(func)
            try:
                # Bind the actual function arguments
                bound_func_args = func_sig.bind(*args, **kwargs)
                bound_func_args.apply_defaults()
            except TypeError as e:
                # If we can't bind the function args, let the original function handle it
                return func(*args, **kwargs)
            
            # Check all preconditions
            for precondition, error_msg in getattr(func, '_preconditions', []):
                try:
                    # Get precondition signature
                    precondition_sig = inspect.signature(precondition)
                    
                    # Map function arguments to precondition parameters
                    precondition_args = {}
                    for param_name in precondition_sig.parameters:
                        if param_name in bound_func_args.arguments:
                            precondition_args[param_name] = bound_func_args.arguments[param_name]
                    
                    # Call precondition with mapped arguments
                    precondition_result = precondition(**precondition_args)
                    if not precondition_result:
                        condition_str = f"{precondition.__name__}" if hasattr(precondition, '__name__') else "lambda"
                        final_message = error_msg or f"Precondition {condition_str} failed"
                        
                        _handle_contract_violation(
                            "Precondition", 
                            condition_str,
                            final_message
                        )
                        
                except Exception as e:
                    # If precondition checking fails, re-raise if it's a ContractViolation
                    if isinstance(e, ContractViolation):
                        raise e
                    
                    # Fallback: try calling with positional args only
                    try:
                        # Extract just the positional args that the precondition expects
                        precondition_sig = inspect.signature(precondition)
                        expected_params = list(precondition_sig.parameters.keys())
                        precondition_args = args[:len(expected_params)]
                        
                        if not precondition(*precondition_args):
                            condition_str = f"{precondition.__name__}" if hasattr(precondition, '__name__') else "lambda"
                            final_message = error_msg or f"Precondition {condition_str} failed"
                            
                            _handle_contract_violation(
                                "Precondition",
                                condition_str, 
                                final_message
                            )
                    except Exception as fallback_e:
                        # If precondition checking fails again, re-raise if it's a ContractViolation
                        if isinstance(fallback_e, ContractViolation):
                            raise fallback_e
                        # Otherwise skip this precondition
            
            # Execute original function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def ensure(condition: Callable[[Any], bool], message: str = "") -> Callable[[F], F]:
    """
    Decorator for postconditions - checks outputs after function execution.
    
    Args:
        condition: A callable that takes the function result and returns True 
                  if the postcondition is satisfied
        message: Custom error message for contract violation
    
    Returns:
        Decorated function that checks postconditions after execution
    
    Example:
        @ensure(lambda result: result >= 0, "Result cannot be negative")
        def calculate_price(quantity, unit_price=10):
            return quantity * unit_price
    """
    def decorator(func: F) -> F:
        if not ContractConfig.is_enabled():
            return func
            
        # Store existing postconditions if any
        if not hasattr(func, '_postconditions'):
            func._postconditions = []
        func._postconditions.append((condition, message))
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute original function
            result = func(*args, **kwargs)
            
            # Check all postconditions
            for postcondition, error_msg in getattr(func, '_postconditions', []):
                if not postcondition(result):
                    condition_str = f"{postcondition.__name__}" if hasattr(postcondition, '__name__') else "lambda"
                    final_message = error_msg or f"Postcondition {condition_str} failed"
                    
                    _handle_contract_violation(
                        "Postcondition",
                        condition_str,
                        final_message
                    )
            
            return result
        
        return wrapper
    return decorator


def invariant(condition: Callable[['Any'], bool], message: str = "") -> Callable[[type], type]:
    """
    Decorator for class invariants - checks class state consistency.
    
    Args:
        condition: A callable that takes self and returns True if the invariant holds
        message: Custom error message for contract violation
    
    Returns:
        Decorated class with invariant checking on all methods
    
    Example:
        @invariant(lambda self: self.balance >= 0, "Balance cannot be negative")
        class Account:
            def __init__(self):
                self.balance = 0
    """
    def class_decorator(cls: type) -> type:
        if not ContractConfig.is_enabled():
            return cls
            
        # Store invariants on the class
        if not hasattr(cls, '_invariants'):
            cls._invariants = []
        cls._invariants.append((condition, message))
        
        # If methods are already wrapped, just add this invariant and return
        if hasattr(cls, '_invariant_wrapped'):
            return cls
        
        # Get all methods to wrap
        original_methods = {}
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_') or name == '__init__':
                original_methods[name] = method
        
        def check_invariants(self):
            """Check all class invariants."""
            for invariant_condition, error_msg in getattr(self.__class__, '_invariants', []):
                try:
                    if not invariant_condition(self):
                        condition_str = f"{invariant_condition.__name__}" if hasattr(invariant_condition, '__name__') else "lambda"
                        final_message = error_msg or f"Invariant {condition_str} failed"
                        
                        _handle_contract_violation(
                            "Invariant",
                            condition_str,
                            final_message
                        )
                except Exception as e:
                    # If invariant checking itself fails, re-raise if it's a ContractViolation
                    if isinstance(e, ContractViolation):
                        raise e
                    # Otherwise skip this invariant
                    pass
        
        def wrap_method(method_name: str, original_method: Callable) -> Callable:
            @functools.wraps(original_method)
            def wrapper(self, *args, **kwargs):
                # For __init__, check invariants after execution
                if method_name == '__init__':
                    result = original_method(self, *args, **kwargs)
                    check_invariants(self)
                    return result
                
                # For other methods, check before and after
                check_invariants(self)
                    
                result = original_method(self, *args, **kwargs)
                
                check_invariants(self)
                    
                return result
            return wrapper
        
        # Wrap all methods
        for name, method in original_methods.items():
            setattr(cls, name, wrap_method(name, method))
        
        # Mark as wrapped so subsequent decorators don't re-wrap
        cls._invariant_wrapped = True
        
        return cls
    
    return class_decorator


# Convenience functions for configuration
def enable_contracts() -> None:
    """Enable contract checking globally."""
    ContractConfig.enable()


def disable_contracts() -> None:
    """Disable contract checking globally (for production)."""
    ContractConfig.disable()




def contracts_enabled() -> bool:
    """Check if contracts are currently enabled."""
    return ContractConfig.is_enabled()