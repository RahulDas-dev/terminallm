uv run pyclean -d jupyter package ruff -v .
uv run ruff format -v .
uv run ruff check -v .
uv run python -m unittest discover tests


terminallm --llm vertex_ai/claude-3-opus@20240229 --out_dir .
terminallm --llm azure/finaclegpt432k 
terminallm --llm vertex_ai/gemini-pro
