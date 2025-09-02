import llama_cpp
from typing import List
from pydantic import BaseModel

llama = llama_cpp.Llama(
    model_path="Qwen3-0.6B-Q4_K_M.gguf",
    n_gpu_layers=-1,
    n_ctx=1024,
    verbose=True,

)

class QueryResponse(BaseModel):
    file_types: List[str]
    time_unit: str
    time_unit_value: str
    misc_keywords: str
    is_specific: bool



def llm_query_gen(query_text, max_result=20):
    llama.create_chat_completion(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant that outputs in JSON.",
        },
        {"role": "user", "content": "Who won the world series in 2020"},
    ],
    response_format={
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {"team_name": {"type": "string"}},
            "required": ["team_name"],
        },
    },
    temperature=0.1,
)
