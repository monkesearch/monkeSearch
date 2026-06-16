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
                        Extract file search information. Answer each field:
                        
                        file_types: List file extensions that match the query
                        
                        is_specific: Answer TRUE or FALSE
                        - TRUE if query mentions exact file type: "python", "pdf", "excel", "mp4", "java"
                        - FALSE if query mentions category: "images", "documents", "media", "code"
                        
                        Examples:
                        "python scripts" → file_types: ["py"], is_specific: true
                        "pdf" → file_types: ["pdf"], is_specific: true  
                        "images" → file_types: ["jpg","png"], is_specific: false
                        "documents" → file_types: ["pdf","docx"], is_specific: false
                        
                        time_unit/time_unit_value: Extract if present, else empty string
                        source_text: Track exact words used
                        
                        JSON only."""),
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
            temperature=0.2,  # Lower for more consistent structured output
        )
        content = response['choices'][0]['message']['content']
        return content