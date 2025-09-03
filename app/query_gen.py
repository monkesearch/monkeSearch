import llama_cpp
import textwrap
from typing import List, Dict
from pydantic import BaseModel

llama = llama_cpp.Llama(
    model_path="Qwen3-0.6B-Q8_0.gguf", # model file downloaded locally for now
    n_gpu_layers=-1,
    n_ctx=1024,
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
                        Extract file search information by segmenting into multiple file type indicators.
                        
                        file_type_indicators: Extract EACH file type mention as separate object
                        For each, provide:
                        - text: exact words from query
                        - extensions: probable file extensions
                        - is_specific: true for exact types ("pdf", "python"), false for categories ("images", "documents")
                        
                        Examples:
                        "pdf invoices" → 
                        [{text: "pdf", extensions: ["pdf"], is_specific: true},
                         {text: "invoices", extensions: ["pdf","xlsx"], is_specific: false}]
                        
                        "python scripts from last week" →
                        [{text: "python scripts", extensions: ["py","ipynb"], is_specific: true}]
                        
                        "images and documents" →
                        [{text: "images", extensions: ["jpg","png"], is_specific: false},
                         {text: "documents", extensions: ["pdf","docx"], is_specific: false}]
                        
                        time_unit/time_unit_value: Extract if present, else empty string
                        source_text: Track exact words used
                        JSON only."""),
                },
                {"role": "user", "content": f"{query_text}"},
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