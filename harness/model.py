import os
from typing import Dict, List, Tuple


class FakeModel:
    """
    A fake model used to test the agent loop.

    It ignores the messages and returns a fixed sequence of responses.
    This lets us test the harness before connecting a real LLM.
    """

    def __init__(self):
        self.responses = [
            "ACTION:\npwd && ls -la",
            "ACTION:\npytest",
            "ACTION:\nsed -i 's/return price + tax_rate/return price * (1 + tax_rate)/' app.py",
            "ACTION:\npytest",
            "FINAL:\nThe bug is fixed and pytest passes.",
        ]
        self.index = 0

    def complete(self, messages: List[Dict[str, str]]) -> str:
        if self.index >= len(self.responses):
            return "FINAL:\nNo more actions."

        response = self.responses[self.index]
        self.index += 1
        return response


class OpenAIModel:
    """
    OpenAI API-backed model.

    It exposes the same interface as FakeModel:

        complete(messages) -> str

    so AgentLoop does not need to know whether the model is fake, API-backed,
    or local/open-weight.
    """

    def __init__(
        self,
        model_name: str = "gpt-4.1-mini",
        max_output_tokens: int = 300,
    ):
        from openai import OpenAI

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Run:\n"
                'export OPENAI_API_KEY="your-key-here"'
            )

        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model_name = model_name
        self.max_output_tokens = max_output_tokens

    def complete(self, messages: List[Dict[str, str]]) -> str:
        instructions, input_text = self._messages_to_responses_input(messages)

        response = self.client.responses.create(
            model=self.model_name,
            instructions=instructions,
            input=input_text,
            max_output_tokens=self.max_output_tokens,
        )

        return response.output_text.strip()

    def _messages_to_responses_input(
        self,
        messages: List[Dict[str, str]],
    ) -> Tuple[str, str]:
        """
        Convert our chat-style message list into Responses API inputs.

        We keep the first system message as instructions, then flatten the rest
        of the conversation into a text transcript.
        """

        instructions = (
            "You are an AI agent. Follow the task instructions exactly. "
            "You must respond with either:\n\n"
            "ACTION:\n<single bash command>\n\n"
            "or:\n\n"
            "FINAL:\n<brief final answer>\n"
        )

        transcript_parts = []

        for message in messages:
            role = message["role"]
            content = message["content"]

            if role == "system":
                instructions = content
            else:
                transcript_parts.append(f"{role.upper()}:\n{content}")

        input_text = "\n\n".join(transcript_parts)

        if not input_text.strip():
            input_text = "Begin the task. What is your next action?"

        return instructions, input_text


class OllamaModel:
    """
    Local open-weight model served by Ollama.

    Ollama exposes an OpenAI-compatible API at http://localhost:11434/v1,
    so we can call it using the OpenAI Python client while keeping the same
    complete(messages) interface as FakeModel and OpenAIModel.
    """

    def __init__(
        self,
        model_name: str = "qwen2.5-coder:1.5b",
        base_url: str = "http://localhost:11434/v1",
        max_tokens: int = 300,
        temperature: float = 0.0,
    ):
        from openai import OpenAI

        self.client = OpenAI(
            base_url=base_url,
            api_key="ollama",  # dummy value; Ollama does not use this like OpenAI
        )
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

    def complete(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content.strip()