from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class AIClient:
    def __init__(self, api_key: str, model: str) -> None:
        self.offline_mode = not bool(api_key.strip())
        self.client = OpenAI(api_key=api_key) if not self.offline_mode else None
        self.model = model

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=20), reraise=True)
    def generate_html_fragment(self, prompt: str, reference_html: str = None) -> str:
        if self.offline_mode:
            if reference_html:
                # Return the reference HTML as-is for offline mode to maintain UI structure.
                # Global replacements for company name happen in the renderer later.
                return reference_html
            return (
                "<div>"
                "<p>This section was generated in offline fallback mode because OPENAI_API_KEY is not configured in the runtime environment.</p>"
                "</div>"
            )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = resp.choices[0].message.content
        if not text:
            raise RuntimeError("Empty model response")
        return text.strip()
