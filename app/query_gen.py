import llama_cpp
import textwrap
from typing import List
from pydantic import BaseModel

llama = llama_cpp.Llama(
    model_path="Qwen3-0.6B-Q8_0.gguf",
    n_gpu_layers=-1,
    n_ctx=2048,
    verbose=False,
)

class FileTypeIndicator(BaseModel):
    text: str
    extensions: List[str]
    is_specific: bool

class QueryResponse(BaseModel):
    file_type_indicators: List[FileTypeIndicator]
    time_unit: str
    time_unit_value: str
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

                        FILE TYPE INDICATORS:
                        - text: the exact word/phrase that indicates a file type
                        - extensions: file extensions to search for
                        - is_specific: true for exact types (pdf, py, xlsx), false for categories (images, documents, videos)
                        - For categories, use common extensions:
                          * images -> ["jpg","png"]
                          * documents -> ["pdf","docx"]
                          * videos -> ["mp4","avi"]
                          * code -> ["py","js","java","cpp"]
                          * audio -> ["mp3","wav","flac"]
                          * presentations -> ["pptx","ppt"]
                        - IMPORTANT: Only extract actual file type/format words. "report", "invoice", "resume", "script", "brief" are NOT file types.

                        TEMPORAL:
                        - time_unit: "days", "weeks", "months", "years" (plural form only)
                        - time_unit_value: numeric value as string
                        - If no temporal info: time_unit="", time_unit_value=""
                        - Examples:
                          * "yesterday" -> time_unit="days", time_unit_value="1"
                          * "last week" -> time_unit="weeks", time_unit_value="1"
                          * "3 days ago" -> time_unit="days", time_unit_value="3"
                          * "7 months ago" -> time_unit="months", time_unit_value="7"
                          * "today" -> time_unit="days", time_unit_value="0"

                        SOURCE_TEXT:
                        - file_types: original file type phrase from query
                        - time_unit: original temporal phrase (or empty string)
                        - time_unit_value: same as time_unit (or empty string)

                        EXAMPLES:

                        Input: "python scripts"
                        Output: {"file_type_indicators":[{"text":"python","extensions":["py"],"is_specific":true}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"python scripts","time_unit":"","time_unit_value":""}}

                        Input: "pdf files"
                        Output: {"file_type_indicators":[{"text":"pdf","extensions":["pdf"],"is_specific":true}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"pdf files","time_unit":"","time_unit_value":""}}

                        Input: "images"
                        Output: {"file_type_indicators":[{"text":"images","extensions":["jpg","png"],"is_specific":false}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"images","time_unit":"","time_unit_value":""}}

                        Input: "excel spreadsheets"
                        Output: {"file_type_indicators":[{"text":"excel","extensions":["xlsx"],"is_specific":true}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"excel spreadsheets","time_unit":"","time_unit_value":""}}

                        Input: "videos"
                        Output: {"file_type_indicators":[{"text":"videos","extensions":["mp4","avi"],"is_specific":false}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"videos","time_unit":"","time_unit_value":""}}

                        Input: "report pdf"
                        Output: {"file_type_indicators":[{"text":"pdf","extensions":["pdf"],"is_specific":true}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"pdf","time_unit":"","time_unit_value":""}}

                        Input: "files from yesterday"
                        Output: {"file_type_indicators":[],"time_unit":"days","time_unit_value":"1","source_text":{"file_types":"","time_unit":"yesterday","time_unit_value":"yesterday"}}

                        Input: "from 3 days ago"
                        Output: {"file_type_indicators":[],"time_unit":"days","time_unit_value":"3","source_text":{"file_types":"","time_unit":"3 days ago","time_unit_value":"3 days ago"}}

                        Input: "last week"
                        Output: {"file_type_indicators":[],"time_unit":"weeks","time_unit_value":"1","source_text":{"file_types":"","time_unit":"last week","time_unit_value":"last week"}}

                        Input: "7 months ago"
                        Output: {"file_type_indicators":[],"time_unit":"months","time_unit_value":"7","source_text":{"file_types":"","time_unit":"7 months ago","time_unit_value":"7 months ago"}}

                        Input: "2 years ago"
                        Output: {"file_type_indicators":[],"time_unit":"years","time_unit_value":"2","source_text":{"file_types":"","time_unit":"2 years ago","time_unit_value":"2 years ago"}}

                        Input: "python scripts from 3 days ago"
                        Output: {"file_type_indicators":[{"text":"python","extensions":["py"],"is_specific":true}],"time_unit":"days","time_unit_value":"3","source_text":{"file_types":"python scripts","time_unit":"3 days ago","time_unit_value":"3 days ago"}}

                        Input: "images from yesterday"
                        Output: {"file_type_indicators":[{"text":"images","extensions":["jpg","png"],"is_specific":false}],"time_unit":"days","time_unit_value":"1","source_text":{"file_types":"images","time_unit":"yesterday","time_unit_value":"yesterday"}}

                        Input: "photos from yesterday"
                        Output: {"file_type_indicators":[{"text":"photos","extensions":["jpg","png"],"is_specific":false}],"time_unit":"days","time_unit_value":"1","source_text":{"file_types":"photos","time_unit":"yesterday","time_unit_value":"yesterday"}}

                        Input: "pdf 7 months ago"
                        Output: {"file_type_indicators":[{"text":"pdf","extensions":["pdf"],"is_specific":true}],"time_unit":"months","time_unit_value":"7","source_text":{"file_types":"pdf","time_unit":"7 months ago","time_unit_value":"7 months ago"}}

                        Input: "images from last week"
                        Output: {"file_type_indicators":[{"text":"images","extensions":["jpg","png"],"is_specific":false}],"time_unit":"weeks","time_unit_value":"1","source_text":{"file_types":"images","time_unit":"last week","time_unit_value":"last week"}}

                        Input: "excel files from 2 years ago"
                        Output: {"file_type_indicators":[{"text":"excel","extensions":["xlsx"],"is_specific":true}],"time_unit":"years","time_unit_value":"2","source_text":{"file_types":"excel files","time_unit":"2 years ago","time_unit_value":"2 years ago"}}

                        Input: "word documents"
                        Output: {"file_type_indicators":[{"text":"word","extensions":["docx","doc"],"is_specific":true}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"word documents","time_unit":"","time_unit_value":""}}

                        Input: "presentations"
                        Output: {"file_type_indicators":[{"text":"presentations","extensions":["pptx","ppt"],"is_specific":false}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"presentations","time_unit":"","time_unit_value":""}}

                        Input: "audio files"
                        Output: {"file_type_indicators":[{"text":"audio","extensions":["mp3","wav","flac"],"is_specific":false}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"audio files","time_unit":"","time_unit_value":""}}

                        Input: "files from last month"
                        Output: {"file_type_indicators":[],"time_unit":"months","time_unit_value":"1","source_text":{"file_types":"","time_unit":"last month","time_unit_value":"last month"}}

                        Input: "from the past 2 weeks"
                        Output: {"file_type_indicators":[],"time_unit":"weeks","time_unit_value":"2","source_text":{"file_types":"","time_unit":"past 2 weeks","time_unit_value":"past 2 weeks"}}

                        Input: "files from today"
                        Output: {"file_type_indicators":[],"time_unit":"days","time_unit_value":"0","source_text":{"file_types":"","time_unit":"today","time_unit_value":"today"}}

                        Input: "word documents from last month"
                        Output: {"file_type_indicators":[{"text":"word","extensions":["docx","doc"],"is_specific":true}],"time_unit":"months","time_unit_value":"1","source_text":{"file_types":"word documents","time_unit":"last month","time_unit_value":"last month"}}

                        Input: "javascript files from this week"
                        Output: {"file_type_indicators":[{"text":"javascript","extensions":["js"],"is_specific":true}],"time_unit":"weeks","time_unit_value":"1","source_text":{"file_types":"javascript files","time_unit":"this week","time_unit_value":"this week"}}

                        Input: "csv files from 2 months ago"
                        Output: {"file_type_indicators":[{"text":"csv","extensions":["csv"],"is_specific":true}],"time_unit":"months","time_unit_value":"2","source_text":{"file_types":"csv files","time_unit":"2 months ago","time_unit_value":"2 months ago"}}

                        Input: "code files"
                        Output: {"file_type_indicators":[{"text":"code","extensions":["py","js","java","cpp"],"is_specific":false}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"code files","time_unit":"","time_unit_value":""}}

                        Input: "markdown and text documents"
                        Output: {"file_type_indicators":[{"text":"markdown","extensions":["md"],"is_specific":true},{"text":"text","extensions":["txt"],"is_specific":true}],"time_unit":"","time_unit_value":"","source_text":{"file_types":"markdown and text documents","time_unit":"","time_unit_value":""}}

                        Input: "video files from yesterday"
                        Output: {"file_type_indicators":[{"text":"video","extensions":["mp4","avi"],"is_specific":false}],"time_unit":"days","time_unit_value":"1","source_text":{"file_types":"video files","time_unit":"yesterday","time_unit_value":"yesterday"}}

                        Return ONLY the JSON object, no other text."""),
                },
                {"role": "user", "content": query_text},
            ],
            response_format={
                "type": "json_object",
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
                                    "is_specific": {"type": "boolean"}
                                },
                                "required": ["text", "extensions", "is_specific"]
                            }
                        },
                        "time_unit": {"type": "string"},
                        "time_unit_value": {"type": "string"},
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
                    "required": ["file_type_indicators", "time_unit", "time_unit_value", "source_text"],
                },
            },
            temperature=0.1,
        )
        content = response['choices'][0]['message']['content']
        return content