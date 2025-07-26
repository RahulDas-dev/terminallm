# LiteLLM with Proper Type Annotations

This example demonstrates how to implement LiteLLM async completions with proper type annotations in Python.

## Key Features

### 1. **Proper Type Annotations**
```python
async def complete(
    self,
    messages: List[Union[LLMMessage, Dict[str, Any]]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    tools: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> Union[ModelResponse, AsyncIterator[StreamEvent]]:
```

### 2. **Streaming vs Non-Streaming**
- **Non-streaming**: Returns `ModelResponse` 
- **Streaming**: Returns `AsyncIterator[StreamEvent]`

### 3. **Message Formatting**
```python
def _format_messages(
    self, messages: List[Union[LLMMessage, Dict[str, Any]]]
) -> List[ChatCompletionMessageParam]:
```

Converts your custom message format to LiteLLM's expected `ChatCompletionMessageParam` type.

### 4. **Pydantic Models for Type Safety**
```python
class LLMMessage(BaseModel):
    role: str = Field(..., description="Message role: system, user, assistant, tool")
    content: Optional[str] = Field(None, description="Message content")
    name: Optional[str] = Field(None, description="Name of the message sender")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls")
    tool_call_id: Optional[str] = Field(None, description="Tool call response ID")
```

## Usage Examples

### Simple Completion
```python
client = LiteLLMClient()
messages = [
    LLMMessage(role="system", content="You are a helpful assistant."),
    LLMMessage(role="user", content="What is the capital of France?"),
]

response = await client.complete(
    messages=messages,
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=100,
)
```

### Streaming Completion
```python
stream = await client.complete(
    messages=messages,
    model="gpt-3.5-turbo",
    stream=True,
)

async for event in stream:
    if event.event_type == "content":
        print(event.content, end="", flush=True)
```

### Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    },
}]

response = await client.complete(
    messages=messages,
    tools=tools,
    tool_choice="auto",
)
```

## Key Type Safety Benefits

1. **IDE Support**: Full autocomplete and type checking
2. **Runtime Safety**: Pydantic validation of message structure  
3. **Clear Interfaces**: Explicit return types for streaming vs non-streaming
4. **Error Prevention**: Catches type mismatches at development time

## LiteLLM Integration Points

### Supported Models
LiteLLM supports 100+ models from different providers:
- OpenAI (GPT-3.5, GPT-4, etc.)
- Anthropic (Claude)
- Google (Gemini)
- Azure OpenAI
- AWS Bedrock
- And many more...

### Authentication
Set environment variables for your API keys:
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
```

### Model Format
Use the provider prefix for specific models:
```python
model="gpt-4"                    # OpenAI GPT-4
model="claude-3-sonnet-20240229" # Anthropic Claude
model="gemini-pro"               # Google Gemini
model="bedrock/anthropic.claude-v2" # AWS Bedrock
```

## Error Handling

The example includes proper error handling:
```python
try:
    response = await client.complete(messages=messages)
    # Handle response
except Exception as e:
    logger.error(f"LiteLLM completion failed: {e}")
    raise
```

## Running the Example

```bash
# Install dependencies
pip install litellm pydantic

# Set your API keys
export OPENAI_API_KEY="your-openai-key"

# Run the example
python litellm_example.py
```

This implementation provides a solid foundation for building LLM applications with proper type safety and async support!
