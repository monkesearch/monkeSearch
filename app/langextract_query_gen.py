import llama_cpp
import textwrap
from typing import List
from pydantic import BaseModel

llama = llama_cpp.Llama(
    model_path="Qwen3-0.6B-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=1024,
    verbose=False,
)

class QueryResponse(BaseModel):
    file_types: List[str]
    time_unit: str
    time_unit_value: str
    misc_keywords: str
    is_specific: bool


class QueryExtractor:
    def llm_query_gen(self, query_text, max_result=20, model_instance=llama):
        response = model_instance.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": textwrap.dedent("""\
                    /no_think
                    Extract file search information from queries.
                    
                    FILE TYPES: Extract relevant file extensions. Set is_specific=true for exact types like "python files", "pdf documents". Set is_specific=false for broad categories like "images", "documents".
                    
                    TEMPORAL: Extract only explicit time references. Use empty strings if no temporal info found.
                    
                    EXAMPLES:
                    "python scripts from 3 days ago" - file_types: ["py", "ipynb"], time_unit: "days", time_unit_value: "3", misc_keywords: "scripts", is_specific: true
                    "old images" - file_types: ["jpg", "png", "gif"], time_unit: "", time_unit_value: "", misc_keywords: "old", is_specific: false
                    "excel files from last week" - file_types: ["xlsx", "xls"], time_unit: "weeks", time_unit_value: "1", misc_keywords: "", is_specific: true
                    
                    Respond only with JSON."""),
            },
            {"role": "user", "content": f"{query_text}"},
        ],
        response_format={
            "type": "json_object",
            "schema": {
                "type": "object",
                "properties": {
                    "file_types": {"type": "array", "items": {"type": "string"}},
                    "time_unit": {"type": "string"},
                    "time_unit_value": {"type": "string"},
                    "misc_keywords": {"type": "string"},
                    "is_specific": {"type": "boolean"}
                },
                "required": ["file_types", "time_unit", "time_unit_value", "misc_keywords", "is_specific"],
            },
        },
        
        temperature=0.1,
    )
        content = response['choices'][0]['message']['content']
        return content
    