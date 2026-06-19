import os
import json
import urllib.request
import textwrap

SEARCH_SCHEMA = {
    "name": "search_query",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "file_type_indicators": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "extensions": {"type": "array", "items": {"type": "string"}},
                        "is_specific": {"type": "boolean"},
                    },
                    "required": ["text", "extensions", "is_specific"],
                    "additionalProperties": False,
                },
            },
            "time_unit": {"type": "string"},
            "time_unit_value": {"type": "string"},
            "time_direction": {
                "type": "string",
                "enum": ["", "after", "before"],
            },
            "source_text": {
                "type": "object",
                "properties": {
                    "file_types": {"type": "string"},
                    "time_unit": {"type": "string"},
                    "time_unit_value": {"type": "string"},
                },
                "required": ["file_types", "time_unit", "time_unit_value"],
                "additionalProperties": False,
            },
        },
        "required": ["file_type_indicators", "time_unit", "time_unit_value", "time_direction", "source_text"],
        "additionalProperties": False,
    },
}


class LLMServerClient:
    def __init__(self, base_url="http://localhost:8080/v1"):
        self.base_url = base_url.rstrip("/")

    def create_chat_completion(self, messages=None, response_format=None, temperature=0.2, max_tokens=300):
        body = {
            "messages": messages or [],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            body["response_format"] = response_format
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())


server_url = os.environ.get("MONKE_SERVER_URL", "http://localhost:8080/v1")
llama = LLMServerClient(base_url=server_url)


class QueryExtractor:
    def llm_query_gen(self, query_text):
        response = llama.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": textwrap.dedent("""\
                        /no_think
                        Extract file search information from the user's query. Return JSON only.

                        Fields:
                        - file_type_indicators: Array of objects, each with:
                          - text: The exact word/phrase from the query indicating a file type
                          - extensions: Array of matching file extensions
                          - is_specific: true if exact type (python, pdf, mp4, java),
                                         false if category (images, documents, media, code)
                        - time_unit: Unit like "minutes", "hours", "days", "weeks", "months", "years"
                        - time_unit_value: Number as string like "1", "2", "7" or exact word (today/yesterday/tomorrow)
                        - time_direction: "" (empty for non-temporal), "after" (newer than, default), or "before" (older than)
                        - source_text: Object with:
                          - file_types: Exact words used to indicate file types
                          - time_unit: Exact words used to indicate time unit
                          - time_unit_value: Exact words used to indicate time value

                        Examples:
                        "python scripts" → {"file_type_indicators":[{"text":"python","extensions":["py"],"is_specific":true}],"time_unit":"","time_unit_value":"","time_direction":"","source_text":{"file_types":"python","time_unit":"","time_unit_value":""}}
                        "pdf files" → {"file_type_indicators":[{"text":"pdf","extensions":["pdf"],"is_specific":true}],"time_unit":"","time_unit_value":"","time_direction":"","source_text":{"file_types":"pdf","time_unit":"","time_unit_value":""}}
                        "code from last week" → {"file_type_indicators":[{"text":"code","extensions":["py","js","java","cpp","ts","go","rs","rb"],"is_specific":false}],"time_unit":"weeks","time_unit_value":"1","time_direction":"after","source_text":{"file_types":"code","time_unit":"last week","time_unit_value":"last week"}}
                        "images from yesterday" → {"file_type_indicators":[{"text":"images","extensions":["jpg","png","heic","webp"],"is_specific":false}],"time_unit":"days","time_unit_value":"1","time_direction":"after","source_text":{"file_types":"images","time_unit":"yesterday","time_unit_value":"yesterday"}}
                        "documents created today" → {"file_type_indicators":[{"text":"documents","extensions":["pdf","docx","txt"],"is_specific":false}],"time_unit":"days","time_unit_value":"0","time_direction":"after","source_text":{"file_types":"documents","time_unit":"today","time_unit_value":"today"}}
                        "files older than 3 days" → {"file_type_indicators":[],"time_unit":"days","time_unit_value":"3","time_direction":"before","source_text":{"file_types":"","time_unit":"older than 3 days","time_unit_value":"older than 3 days"}}
                        "pdf files older than 3 months" → {"file_type_indicators":[{"text":"pdf","extensions":["pdf"],"is_specific":true}],"time_unit":"months","time_unit_value":"3","time_direction":"before","source_text":{"file_types":"pdf","time_unit":"older than 3 months","time_unit_value":"older than 3 months"}}
                        "meeting notes" → {"file_type_indicators":[],"time_unit":"","time_unit_value":"","time_direction":"","source_text":{"file_types":"","time_unit":"","time_unit_value":""}}

                        JSON only."""),
                },
                {"role": "user", "content": query_text},
            ],
            response_format={"type": "json_schema", "schema": SEARCH_SCHEMA},
            temperature=0.2,
        )
        content = response['choices'][0]['message']['content']
        return content
