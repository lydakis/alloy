"""
Provider registry for managing and auto-detecting model providers.
"""

from typing import Dict, Optional, Type
import os
from .base import ModelProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .openrouter_provider import OpenRouterProvider


class ProviderRegistry:
    """Registry for managing model providers."""
    
    def __init__(self):
        self._providers: Dict[str, Type[ModelProvider]] = {}
        self._instances: Dict[str, ModelProvider] = {}
        self._model_mappings: Dict[str, str] = {}
        
        # Register default providers
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default providers and model mappings."""
        # Register provider classes
        self.register_provider("openai", OpenAIProvider)
        self.register_provider("anthropic", AnthropicProvider) 
        self.register_provider("openrouter", OpenRouterProvider)
        
        # Register model -> provider mappings
        openai_models = [
            "gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4", "gpt-4-turbo", 
            "gpt-4-vision-preview", "gpt-3.5-turbo", "o1-preview", "o1-mini"
        ]
        
        anthropic_models = [
            "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229", "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307", "claude-4", "claude-3.5-sonnet",
            "claude-3.5-haiku", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"
        ]
        
        for model in openai_models:
            self._model_mappings[model] = "openai"
        
        for model in anthropic_models:
            self._model_mappings[model] = "anthropic"
    
    def register_provider(self, name: str, provider_class: Type[ModelProvider]):
        """Register a provider class."""
        self._providers[name] = provider_class
    
    def register_model_mapping(self, model: str, provider: str):
        """Register a model -> provider mapping."""
        self._model_mappings[model] = provider
    
    def get_provider_for_model(self, model: str) -> str:
        """Get the provider name for a model."""
        # Direct mapping
        if model in self._model_mappings:
            return self._model_mappings[model]
        
        # Pattern matching for provider prefixes - OpenRouter style comes first
        if model.startswith("openrouter/"):
            return "openrouter"
        elif model.startswith("anthropic/") or model.startswith("openai/") or model.startswith("google/") or model.startswith("xai/"):
            # These are OpenRouter model formats
            return "openrouter"
        elif "gpt" in model.lower():
            return "openai"
        elif "claude" in model.lower():
            return "anthropic"
        
        # Default fallback
        return "openrouter"  # OpenRouter supports most models
    
    def get_provider_instance(
        self, 
        provider_name: str, 
        api_key: Optional[str] = None,
        **kwargs
    ) -> ModelProvider:
        """Get or create a provider instance."""
        # Use cached instance if available and no new config
        cache_key = f"{provider_name}:{api_key}"
        if cache_key in self._instances and not kwargs:
            return self._instances[cache_key]
        
        if provider_name not in self._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Auto-detect API key from environment if not provided
        if api_key is None:
            api_key = self._get_api_key_from_env(provider_name)
        
        # Create new instance
        provider_class = self._providers[provider_name]
        instance = provider_class(api_key=api_key, **kwargs)
        
        # Cache the instance
        self._instances[cache_key] = instance
        return instance
    
    def _get_api_key_from_env(self, provider_name: str) -> Optional[str]:
        """Get API key from environment variables."""
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "openrouter": "OPENROUTER_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "xai": "XAI_API_KEY"
        }
        
        env_var = env_var_map.get(provider_name)
        if env_var:
            return os.getenv(env_var)
        
        return None
    
    def get_provider_for_model_instance(
        self, 
        model: str, 
        api_key: Optional[str] = None,
        **kwargs
    ) -> ModelProvider:
        """Get provider instance for a specific model."""
        provider_name = self.get_provider_for_model(model)
        return self.get_provider_instance(provider_name, api_key, **kwargs)
    
    def list_providers(self) -> Dict[str, Type[ModelProvider]]:
        """List all registered providers."""
        return self._providers.copy()
    
    def list_model_mappings(self) -> Dict[str, str]:
        """List all model -> provider mappings."""
        return self._model_mappings.copy()


# Global registry instance
_registry = ProviderRegistry()


def get_provider(
    model: str, 
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> ModelProvider:
    """
    Get a provider instance for a model.
    
    Args:
        model: Model identifier
        provider: Optional provider name (auto-detected if not provided)
        api_key: Optional API key (auto-detected from env if not provided)
        **kwargs: Additional provider configuration
    
    Returns:
        ModelProvider instance
    """
    if provider:
        return _registry.get_provider_instance(provider, api_key, **kwargs)
    else:
        return _registry.get_provider_for_model_instance(model, api_key, **kwargs)


def register_provider(name: str, provider_class: Type[ModelProvider]):
    """Register a new provider class."""
    _registry.register_provider(name, provider_class)


def register_model_mapping(model: str, provider: str):
    """Register a model -> provider mapping."""
    _registry.register_model_mapping(model, provider)