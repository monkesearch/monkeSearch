import llama_cpp
import textwrap
from typing import List
from pydantic import BaseModel

llama = llama_cpp.Llama(
    model_path="Qwen3-0.6B-Q8_0.gguf",
    n_gpu_layers=-1,
    n_ctx=2048,
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
                        
                        Input: "pdf files"
                        Output: {"file_types":["pdf"],"time_unit":"","time_unit_value":"","is_specific":true,"source_text":{"file_types":"pdf files","time_unit":"","time_unit_value":""}}
                        
                        Input: "images"
                        Output: {"file_types":["jpg","png"],"time_unit":"","time_unit_value":"","is_specific":false,"source_text":{"file_types":"images","time_unit":"","time_unit_value":""}}
                        
                        Input: "excel spreadsheets"
                        Output: {"file_types":["xlsx"],"time_unit":"","time_unit_value":"","is_specific":true,"source_text":{"file_types":"excel spreadsheets","time_unit":"","time_unit_value":""}}
                        
                        Input: "videos"
                        Output: {"file_types":["mp4","avi"],"time_unit":"","time_unit_value":"","is_specific":false,"source_text":{"file_types":"videos","time_unit":"","time_unit_value":""}}
                        
                        Input: "files from yesterday"
                        Output: {"file_types":[],"time_unit":"days","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"","time_unit":"yesterday","time_unit_value":"yesterday"}}
                        
                        Input: "from 3 days ago"
                        Output: {"file_types":[],"time_unit":"days","time_unit_value":"3","is_specific":false,"source_text":{"file_types":"","time_unit":"3 days ago","time_unit_value":"3 days ago"}}
                        
                        Input: "last week"
                        Output: {"file_types":[],"time_unit":"weeks","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"","time_unit":"last week","time_unit_value":"last week"}}
                        
                        Input: "7 months ago"
                        Output: {"file_types":[],"time_unit":"months","time_unit_value":"7","is_specific":false,"source_text":{"file_types":"","time_unit":"7 months ago","time_unit_value":"7 months ago"}}
                        
                        Input: "2 years ago"
                        Output: {"file_types":[],"time_unit":"years","time_unit_value":"2","is_specific":false,"source_text":{"file_types":"","time_unit":"2 years ago","time_unit_value":"2 years ago"}}
                        
                        Input: "python scripts from 3 days ago"
                        Output: {"file_types":["py"],"time_unit":"days","time_unit_value":"3","is_specific":true,"source_text":{"file_types":"python scripts","time_unit":"3 days ago","time_unit_value":"3 days ago"}}
                        
                        Input: "images from yesterday"
                        Output: {"file_types":["jpg","png"],"time_unit":"days","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"images","time_unit":"yesterday","time_unit_value":"yesterday"}}
                        
                        Input: "photos from yesterday"
                        Output: {"file_types":["jpg","png"],"time_unit":"days","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"photos","time_unit":"yesterday","time_unit_value":"yesterday"}}
                        
                        Input: "pdf 7 months ago"
                        Output: {"file_types":["pdf"],"time_unit":"months","time_unit_value":"7","is_specific":true,"source_text":{"file_types":"pdf","time_unit":"7 months ago","time_unit_value":"7 months ago"}}
                        
                        Input: "images from last week"
                        Output: {"file_types":["jpg","png"],"time_unit":"weeks","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"images","time_unit":"last week","time_unit_value":"last week"}}
                        
                        Input: "excel files from 2 years ago"
                        Output: {"file_types":["xlsx"],"time_unit":"years","time_unit_value":"2","is_specific":true,"source_text":{"file_types":"excel files","time_unit":"2 years ago","time_unit_value":"2 years ago"}}
                        
                        Input: "word documents"
                        Output: {"file_types":["docx","doc"],"time_unit":"","time_unit_value":"","is_specific":true,"source_text":{"file_types":"word documents","time_unit":"","time_unit_value":""}}
                        
                        Input: "presentations"
                        Output: {"file_types":["pptx","ppt"],"time_unit":"","time_unit_value":"","is_specific":false,"source_text":{"file_types":"presentations","time_unit":"","time_unit_value":""}}
                        
                        Input: "audio files"
                        Output: {"file_types":["mp3","wav","flac"],"time_unit":"","time_unit_value":"","is_specific":false,"source_text":{"file_types":"audio files","time_unit":"","time_unit_value":""}}
                        
                        Input: "files from last month"
                        Output: {"file_types":[],"time_unit":"months","time_unit_value":"1","is_specific":false,"source_text":{"file_types":"","time_unit":"last month","time_unit_value":"last month"}}
                        
                        Input: "from the past 2 weeks"
                        Output: {"file_types":[],"time_unit":"weeks","time_unit_value":"2","is_specific":false,"source_text":{"file_types":"","time_unit":"past 2 weeks","time_unit_value":"past 2 weeks"}}
                        
                        Input: "files from today"
                        Output: {"file_types":[],"time_unit":"days","time_unit_value":"0","is_specific":false,"source_text":{"file_types":"","time_unit":"today","time_unit_value":"today"}}
                        
                        Input: "word documents from last month"
                        Output: {"file_types":["docx","doc"],"time_unit":"months","time_unit_value":"1","is_specific":true,"source_text":{"file_types":"word documents","time_unit":"last month","time_unit_value":"last month"}}
                        
                        Input: "javascript files from this week"
                        Output: {"file_types":["js"],"time_unit":"weeks","time_unit_value":"1","is_specific":true,"source_text":{"file_types":"javascript files","time_unit":"this week","time_unit_value":"this week"}}
                        
                        Input: "csv files from 2 months ago"
                        Output: {"file_types":["csv"],"time_unit":"months","time_unit_value":"2","is_specific":true,"source_text":{"file_types":"csv files","time_unit":"2 months ago","time_unit_value":"2 months ago"}}
                        
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