import requests
import json
import re
from typing import Dict, Any, List, Optional
from sales_agent.config import config

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or config.ollama_base_url).rstrip("/")
        self.model = model or config.ollama_model

    def is_connected(self) -> bool:
        """Check if local Ollama server is running and reachable."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return res.status_code == 200
        except Exception:
            return False

    def list_available_models(self) -> List[str]:
        """Fetch list of installed models from local Ollama instance."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if res.status_code == 200:
                data = res.json()
                return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3) -> str:
        """Query local Ollama model."""
        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(endpoint, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.base_url}. Ensure Ollama is running (`ollama serve`)."
            )

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None, fallback_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Request JSON output from the model and robustly parse it.
        Includes markdown code block stripping and regex extraction.
        """
        system_instruction = (
            (system_prompt or "") + 
            "\n\nCRITICAL: You must return ONLY a valid JSON object matching the requested schema. "
            "Do not include explanation, thinking text, or commentary outside the JSON."
        ).strip()

        try:
            raw_response = self.generate(prompt, system_prompt=system_instruction, temperature=0.1)
            return self._clean_and_parse_json(raw_response)
        except Exception as e:
            if fallback_dict is not None:
                return fallback_dict
            raise e

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from raw text."""
        # Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Strip markdown fences ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find the first { and last }
        brace_match = re.search(r"(\{[\s\S]*\})", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Failed to parse valid JSON from LLM output: {text[:250]}...")
