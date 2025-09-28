"""Manages state for agent and tools throughout the session"""
from typing import Optional, Dict, Any

class ToolContext:
    """Manages state and tool context for tools within a session
    This class provides a simple and safe interface for tools to read, write,
    and delete data related to the current session, enabling stateful
    multi-turn interactions.
    """
    def __init__(self,
                 session_id: str,
                 initial_state: Optional[Dict[str, Any]] = None):
        """Initialize the context
        Args:
            session_id: A unique identifier for the current session.
            initial_state: An optional dictionary to pre-populate the state.
        """
        self.session_id = session_id
        if initial_state:
            self._state = initial_state.copy()
        else:
            self._state = {}
    
    def dump_state(self) -> Dict[str, Any]:
        """
        Returns a copy of the entire state dictionary.
        Returns:
            A shallow copy of the internal state dictionary, preventing direct mutation.
        """
        return self._state.copy()

    def get(self,
            key: str,
            default: Optional[Any] = None) -> Any:
        """
        Retrieves the value of a key from the state.

        Args:
            key: The key of the value to retrieve.
            default: The value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
        """

        return self._state.get(key, default)
    
    def update(self, **kwargs) -> Dict[str, Any]:
        """
        Updates the state with one or more key-value pairs.
        Overwrites keys if they are already present.

        Args:
            **kwargs: Arbitrary keyword arguments to add or update in the state.

        Returns:
            The instance of the class to allow for method chaining (e.g., context.update(...).update(...))

        Usage:
            updated_data = ctx.update(key1=value1, key2=value2...)
            or
            data_to_update = {"key1": "value1", "key2": "value2"}
            updated_data = ctx.update(**data_to_update)
        """
        self._state.update(kwargs)
        return self._state.copy()
    
    def delete(self, key: str) -> bool:
        """
        Deletes a key-value pair from the state if it exists.

        Args:
            key: The key to delete from the state.
        
        Returns:
            True if the key was found and deleted, False otherwise.
        """
        if key in self._state:
            del self._state[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clears the entire state, resetting it to an empty dictionary."""
        self._state = {}
