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
                        Extract file search information by identifying ONLY actual file types, not content descriptors.
                        
                        file_type_indicators: Extract ONLY file type/format mentions
                        Rules:
                        - File types: extensions (pdf, py, mp4), format names (python, excel), or categories (images, documents)
                        - NOT file types: content words (report, invoice, resume, photo, script, brief)
                        - is_specific: true for exact types/extensions, false for categories
                        
                        Examples:
                        "report pdf" → 
                        [{text: "pdf", extensions: ["pdf"], is_specific: true}]
                        
                        "python scripts" →
                        [{text: "python", extensions: ["py"], is_specific: true}]
                        
                        "wedding photos" →
                        [{text: "photos", extensions: ["jpg","png"], is_specific: false}]
                        
                        "invoice documents" →
                        [{text: "documents", extensions: ["pdf","docx"], is_specific: false}]
                        
                        "budget.xlsx excel" →
                        [{text: "excel", extensions: ["xlsx"], is_specific: true}]
                        
                        "images from yesterday" →
                        [{text: "images", extensions: ["jpg","png"], is_specific: false}]
                        
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