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

    Supports configurable generation limits and model
    keep-alive behaviour for performance optimisation.
    """

    def __init__(
        self,
        model="llama3.1:8b",
        base_url="http://localhost:11434",
        timeout=120,
        num_predict=256,
        keep_alive="10m",
    ):
        """
        Initialise the Ollama client.

        Parameters
        ----------
        model : str
            Ollama model name.

        base_url : str
            Ollama server URL.

        timeout : int | float
            HTTP request timeout in seconds.

        num_predict : int | None
            Maximum number of tokens to generate.

            If None, Ollama's default generation limit
            is used.

        keep_alive : str | int | float
            How long Ollama should keep the model loaded
            after a request.

            Examples:
                "10m"
                "30m"
                -1
        """

        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # ----------------------------------------------------------
        # Generation configuration
        # ----------------------------------------------------------

        if num_predict is not None:

            if not isinstance(
                num_predict,
                int,
            ):

                raise TypeError(
                    "num_predict must be an integer "
                    "or None."
                )

            if num_predict <= 0:

                raise ValueError(
                    "num_predict must be greater than 0."
                )

        self.num_predict = num_predict

        self.keep_alive = keep_alive

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

        options = {
            "temperature": temperature,
        }

        # ----------------------------------------------------------
        # Optional output-token limit
        # ----------------------------------------------------------

        if self.num_predict is not None:

            options["num_predict"] = (
                self.num_predict
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": options,
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

        try:

            data = response.json()

        except ValueError as exc:

            raise RuntimeError(
                "Ollama returned an invalid JSON response."
            ) from exc

        answer = data.get(
            "response",
            "",
        )

        if not answer:

            raise RuntimeError(
                "Ollama returned an empty response."
            )

        # ----------------------------------------------------------
        # Preserve Ollama timing information
        # ----------------------------------------------------------

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

        if "prompt_eval_duration" in data:

            metadata["prompt_eval_duration"] = (
                data["prompt_eval_duration"]
            )

        if "eval_count" in data:

            metadata["eval_count"] = (
                data["eval_count"]
            )

        if "eval_duration" in data:

            metadata["eval_duration"] = (
                data["eval_duration"]
            )

        if "load_duration" in data:

            metadata["load_duration"] = (
                data["load_duration"]
            )

        # ----------------------------------------------------------
        # Record optimisation configuration
        # ----------------------------------------------------------

        metadata["num_predict"] = (
            self.num_predict
        )

        metadata["keep_alive"] = (
            self.keep_alive
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
            "num_predict": self.num_predict,
            "keep_alive": self.keep_alive,
        }

    # ----------------------------------------------------------
    # Representation
    # ----------------------------------------------------------

    def __repr__(self):

        return (
            f"LLMClient("
            f"model='{self.model}', "
            f"base_url='{self.base_url}', "
            f"num_predict="
            f"{self.num_predict}, "
            f"keep_alive="
            f"'{self.keep_alive}')"
        )