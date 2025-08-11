"""
Memory system for agents to store and retrieve context.
Supports conversation history, explicit memories, and shared memory.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import time


class MemoryType(Enum):
    """Types of memory storage."""
    CONVERSATION = "conversation"
    EXPLICIT = "explicit" 
    SHARED = "shared"


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    prompt: str
    response: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Memory:
    """
    Memory system for storing and retrieving agent context.
    
    Supports different memory types:
    - conversation: Stores prompt/response pairs
    - explicit: Stores key-value memories
    - shared: Shared between multiple agents
    """
    
    def __init__(
        self, 
        type: Union[MemoryType, str] = MemoryType.EXPLICIT,
        max_turns: Optional[int] = None,
        max_entries: Optional[int] = None
    ):
        if isinstance(type, str):
            type = MemoryType(type)
        
        self.memory_type = type
        self.max_turns = max_turns
        self.max_entries = max_entries
        
        # Storage
        self._conversation: List[ConversationTurn] = []
        self._memories: Dict[str, MemoryEntry] = {}
        
    def add_exchange(self, prompt: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a conversation exchange (prompt/response pair).
        
        Args:
            prompt: The input prompt
            response: The agent's response
            metadata: Optional metadata for this turn
        """
        turn = ConversationTurn(
            prompt=prompt, 
            response=response, 
            metadata=metadata or {}
        )
        
        self._conversation.append(turn)
        
        # Enforce max turns limit
        if self.max_turns and len(self._conversation) > self.max_turns:
            self._conversation = self._conversation[-self.max_turns:]
    
    def remember(self, key: str, value: Any, tags: Optional[List[str]] = None) -> None:
        """
        Store an explicit memory.
        
        Args:
            key: Memory key for retrieval
            value: Value to store
            tags: Optional tags for categorization
        """
        entry = MemoryEntry(key=key, value=value, tags=tags or [])
        self._memories[key] = entry
        
        # Enforce max entries limit
        if self.max_entries and len(self._memories) > self.max_entries:
            # Remove oldest entry
            oldest_key = min(self._memories.keys(), key=lambda k: self._memories[k].timestamp)
            del self._memories[oldest_key]
    
    def recall(self, key: str) -> Optional[Any]:
        """
        Retrieve a memory by key.
        
        Args:
            key: Memory key
            
        Returns:
            The stored value, or None if not found
        """
        entry = self._memories.get(key)
        return entry.value if entry else None
    
    def recall_all(self, tag: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve all memories, optionally filtered by tag.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        for key, entry in self._memories.items():
            if tag is None or tag in entry.tags:
                result[key] = entry.value
        return result
    
    def get_context(self, max_turns: Optional[int] = None) -> str:
        """
        Get conversation context as a formatted string.
        
        Args:
            max_turns: Maximum number of recent turns to include
            
        Returns:
            Formatted conversation context
        """
        if not self._conversation:
            return ""
        
        turns = self._conversation
        if max_turns:
            turns = turns[-max_turns:]
        
        context_parts = []
        for turn in turns:
            context_parts.append(f"Human: {turn.prompt}")
            context_parts.append(f"Assistant: {turn.response}")
        
        return "\n".join(context_parts)
    
    def get_conversation_history(self) -> List[ConversationTurn]:
        """Get the full conversation history."""
        return self._conversation.copy()
    
    def clear(self) -> None:
        """Clear all stored memories and conversation history."""
        self._conversation.clear()
        self._memories.clear()
    
    def clear_conversation(self) -> None:
        """Clear only conversation history."""
        self._conversation.clear()
    
    def clear_memories(self) -> None:
        """Clear only explicit memories."""
        self._memories.clear()
    
    def forget(self, key: str) -> bool:
        """
        Remove a specific memory.
        
        Args:
            key: Memory key to remove
            
        Returns:
            True if the key was found and removed, False otherwise
        """
        if key in self._memories:
            del self._memories[key]
            return True
        return False
    
    def export_memories(self) -> Dict[str, Any]:
        """
        Export all memories to a serializable format.
        
        Returns:
            Dictionary containing all memory data
        """
        return {
            "memory_type": self.memory_type.value,
            "conversation": [
                {
                    "prompt": turn.prompt,
                    "response": turn.response,
                    "timestamp": turn.timestamp,
                    "metadata": turn.metadata
                }
                for turn in self._conversation
            ],
            "memories": {
                key: {
                    "value": entry.value,
                    "timestamp": entry.timestamp,
                    "tags": entry.tags,
                    "metadata": entry.metadata
                }
                for key, entry in self._memories.items()
            }
        }
    
    def import_memories(self, data: Dict[str, Any]) -> None:
        """
        Import memories from a serializable format.
        
        Args:
            data: Memory data from export_memories()
        """
        # Import conversation history
        for turn_data in data.get("conversation", []):
            turn = ConversationTurn(
                prompt=turn_data["prompt"],
                response=turn_data["response"],
                timestamp=turn_data.get("timestamp", time.time()),
                metadata=turn_data.get("metadata", {})
            )
            self._conversation.append(turn)
        
        # Import explicit memories
        for key, entry_data in data.get("memories", {}).items():
            entry = MemoryEntry(
                key=key,
                value=entry_data["value"],
                timestamp=entry_data.get("timestamp", time.time()),
                tags=entry_data.get("tags", []),
                metadata=entry_data.get("metadata", {})
            )
            self._memories[key] = entry