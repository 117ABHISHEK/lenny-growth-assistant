from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """Stream generated tokens."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Health check for this provider."""
        ...