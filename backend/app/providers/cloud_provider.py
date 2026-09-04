from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from .base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            yield "[Error: ANTHROPIC_API_KEY is not set.]"
            return
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=2000,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Error calling Anthropic API: {str(e)}]"

    async def is_available(self) -> bool:
        return bool(self.api_key)