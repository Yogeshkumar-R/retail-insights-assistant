"""
Conversation memory management using a simple windowed buffer.
Stores (role, content) pairs and formats them for prompt injection.
"""
from collections import deque
from config import MEMORY_WINDOW


class ConversationMemory:
    """Sliding window conversation buffer."""

    def __init__(self, window: int = MEMORY_WINDOW):
        self._history: deque[dict] = deque(maxlen=window * 2)  # *2 for user+assistant pairs

    def add_user(self, message: str) -> None:
        """Append a user message to the conversation history."""
        self._history.append({"role": "user", "content": message})

    def add_assistant(self, message: str) -> None:
        """Append an assistant message to the conversation history."""
        self._history.append({"role": "assistant", "content": message})

    def get_formatted(self) -> str:
        """Return conversation history as a formatted string for prompt injection."""
        if not self._history:
            return "No previous conversation."
        lines = []
        for turn in self._history:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        return "\n".join(lines)

    def get_messages(self) -> list[dict]:
        """Return raw list of message dicts."""
        return list(self._history)

    def clear(self) -> None:
        """Clear all messages from the conversation history."""
        self._history.clear()
