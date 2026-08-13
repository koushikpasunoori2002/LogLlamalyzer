"""
llm_client.py

Provides a client for communicating with a local
Ollama language model.
"""

import requests

from .response import LLMResponse


class LLMClient:
    """
    Client for local Ollama LLM inference.
    """

    def __init__(
        self,
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        timeout=120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ----------------------------------------------------------
    # Generate
    # ----------------------------------------------------------

    def generate(
        self,
        prompt,
        temperature=0.2,
    ):
        """
        Send a prompt to the Ollama model and return
        an LLMResponse.
        """

        if not isinstance(prompt, str):
            raise TypeError(
                "prompt must be a string."
            )

        prompt = prompt.strip()

        if not prompt:
            raise ValueError(
                "prompt cannot be empty."
            )

        url = (
            f"{self.base_url}/api/generate"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        try:

            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.exceptions.ConnectionError as exc:

            raise RuntimeError(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            ) from exc

        except requests.exceptions.Timeout as exc:

            raise RuntimeError(
                "Ollama request timed out."
            ) from exc

        except requests.exceptions.RequestException as exc:

            raise RuntimeError(
                f"Ollama request failed: {exc}"
            ) from exc

        data = response.json()

        answer = data.get(
            "response",
            "",
        )

        if not answer:

            raise RuntimeError(
                "Ollama returned an empty response."
            )

        metadata = {
            "source": "ollama",
            "base_url": self.base_url,
            "done": data.get(
                "done",
                None,
            ),
        }

        if "total_duration" in data:

            metadata["total_duration"] = (
                data["total_duration"]
            )

        if "load_duration" in data:

            metadata["load_duration"] = (
                data["load_duration"]
            )

        if "prompt_eval_count" in data:

            metadata["prompt_eval_count"] = (
                data["prompt_eval_count"]
            )

        if "eval_count" in data:

            metadata["eval_count"] = (
                data["eval_count"]
            )

        return LLMResponse(
            query=prompt,
            answer=answer.strip(),
            model=self.model,
            metadata=metadata,
        )

    # ----------------------------------------------------------
    # Health Check
    # ----------------------------------------------------------

    def is_available(self):
        """
        Check whether Ollama is available.
        """

        try:

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )

            response.raise_for_status()

            return True

        except requests.exceptions.RequestException:

            return False

    # ----------------------------------------------------------
    # Model Check
    # ----------------------------------------------------------

    def model_available(self):
        """
        Check whether the configured model is available
        in the local Ollama installation.
        """

        try:

            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10,
            )

            response.raise_for_status()

            data = response.json()

            models = data.get(
                "models",
                [],
            )

            for model in models:

                name = model.get(
                    "name",
                    "",
                )

                if name == self.model:

                    return True

            return False

        except requests.exceptions.RequestException:

            return False

    # ----------------------------------------------------------
    # Information
    # ----------------------------------------------------------

    def info(self):
        """
        Return client configuration.
        """

        return {
            "component": "LLMClient",
            "provider": "Ollama",
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
        }

    def __repr__(self):

        return (
            f"LLMClient("
            f"model='{self.model}', "
            f"base_url='{self.base_url}')"
        )