# server_start.py
#!/usr/bin/env python3
"""
Start llama-cpp-python OpenAI compatible server
Run: python server_start.py
"""

import subprocess
import sys

MODEL_PATH = "Qwen3-0.6B-Q8_0.gguf"
HOST = "127.0.0.1"
PORT = 8000

cmd = [
    sys.executable, "-m", "llama_cpp.server",
    "--model", MODEL_PATH,
    "--host", HOST,
    "--port", str(PORT),
    "--n_gpu_layers", "-1",  # Use all GPU layers
    "--n_ctx", "1024",       # Context size
    "--chat_format", "chatml",  # Or whatever format Qwen uses
]

print(f"Starting llama-cpp server on {HOST}:{PORT}")
print(f"Model: {MODEL_PATH}")
print("Press Ctrl+C to stop")

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\nServer stopped")