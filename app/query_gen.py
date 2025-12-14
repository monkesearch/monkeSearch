import llama_cpp
import textwrap
from typing import List
from pydantic import BaseModel

llama = llama_cpp.Llama(
    model_path="Qwen3-0.6B-Q8_0.gguf",
    n_gpu_layers=-1,
    n_ctx=1024,
    verbose=True,
)

class QueryResponse(BaseModel):
    file_types: List[str]
    time_unit: str
    time_unit_value: str
    is_specific: bool
    source_text: dict

class QueryExtractor:
    def llm_query_gen(self, query_text, model_instance=llama):
        response = model_instance.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": textwrap.dedent("""\
                        /no_think
                        Extract file search query components. Return valid JSON only.
                        
                        FILE TYPES:
                        - Extract file extensions (not categories)
                        - is_specific TRUE: exact type mentioned (pdf, py, mp4, xlsx, java, cpp)
                        - is_specific FALSE: category mentioned (images, documents, videos, code)
                        - For categories, return common extensions:
                          * images → ["jpg","png"]
                          * documents → ["pdf","docx"]
                          * videos → ["mp4","avi"]
                          * code → ["py","js"]
                        
                        TEMPORAL:
                        - Extract time_unit: "days", "weeks", "months", "years" (plural form only)
                        - Extract time_unit_value: numeric value as string
                        - If no temporal info: time_unit="", time_unit_value=""
                        - Examples:
                          * "yesterday" → time_unit="days", time_unit_value="1"
                          * "last week" → time_unit="weeks", time_unit_value="1"
                          * "3 days ago" → time_unit="days", time_unit_value="3"
                          * "7 months ago" → time_unit="months", time_unit_value="7"
                        
                        SOURCE_TEXT:
                        - Track exact phrases extracted from query
                        - file_types: original file type phrase
                        - time_unit: original temporal phrase (or empty string)
                        - time_unit_value: same as time_unit field (or empty string)
                        
                        EXAMPLES:
                        Input: "python scripts"
                        Output: {"file_types":["py"],"time_unit":"","time_unit_value":"","is_specific":true,"source_text":{"file_types":"python scripts","time_unit":"","time_unit_value":""}}
                        
                        Input: "images from yesterday"
                        Output: {"file_types":["jpg","png"],"time_unit":"days","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"images","time_unit":"yesterday","time_unit_value":"yesterday"}}
                        
                        Input: "pdf 7 months ago"
                        Output: {"file_types":["pdf"],"time_unit":"months","time_unit_value":"7","is_specific":true,"source_text":{"file_types":"pdf","time_unit":"7 months ago","time_unit_value":"7 months ago"}}
                        
                        Return ONLY the JSON object, no other text."""),
                },
                {"role": "user", "content": query_text},
            ],
            response_format={
                "type": "json_object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "file_types": {"type": "array", "items": {"type": "string"}},
                        "time_unit": {"type": "string"},
                        "time_unit_value": {"type": "string"},
                        "is_specific": {"type": "boolean"},
                        "source_text": {
                            "type": "object",
                            "properties": {
                                "file_types": {"type": "string"},
                                "time_unit": {"type": "string"},
                                "time_unit_value": {"type": "string"}
                            },
                            "required": ["file_types", "time_unit", "time_unit_value"]
                        }
                    },
                    "required": ["file_types", "time_unit", "time_unit_value", "is_specific", "source_text"],
                },
            },
            temperature=0.2,  # Lower for more consistent structured output
        )
        content = response['choices'][0]['message']['content']
        return content