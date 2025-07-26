# ruff: noqa: T201
import asyncio
import json
from typing import Any

import litellm
from dotenv import load_dotenv

_ = load_dotenv()


def get_weather(location: str) -> str:
    """
    Get the current weather for a location.
    """
    return f"The weather in {location} is sunny."


def calculate_sum(a: int, b: int) -> str:
    """
    Calculate the sum of two numbers.
    """
    return f"The sum of {a} and {b} is {a + b}."


def save_to_file(filename: str, content: str) -> str:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved content to {filename}."


def read_file(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading {filename}: {e}"


available_functions = {
    "get_weather": get_weather,
    "calculate_sum": calculate_sum,
    "save_to_file": save_to_file,
    "read_file": read_file,
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_sum",
            "description": "Calculate the sum of two numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_file",
            "description": "Save content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "File name to save to."},
                    "content": {"type": "string", "description": "Content to save."},
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "File name to read from."},
                },
                "required": ["filename"],
            },
        },
    },
]

messages: list[dict[str, Any]] = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Use tools if needed. You can chain tools to solve complex tasks.",
    },
    {
        "role": "user",
        "content": "What's the weather in Paris, add 5 and 7, save both results to 'results.txt', "
        "and show me the file content?",
    },
]


async def tool_calling_loop() -> list[dict[str, Any]]:
    while True:
        response = await litellm.acompletion(
            model="gpt-4o",  # Replace with your model name
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=True,
            n=1,
        )
        chunks = []

        async for chunk in response:
            chunks.append(chunk)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            if "content" in delta and delta["content"] is not None:
                print(delta["content"], end="", flush=True)
        response_ = litellm.stream_chunk_builder(chunks)
        # print(response_)
        if response_ is None:
            print("No response from model, exiting loop.")
            break
        response_message = response_.choices[0].message
        messages.append(response_message.model_dump())
        if response_message.tool_calls:
            print(f"\nTool calls detected: {len(response_message.tool_calls)}")
            for tool_call in response_message.tool_calls:
                # Choose argument parsing depending on structure
                if tool_call.function.name not in available_functions:
                    print(f"Unknown function: {tool_call.function.name}, skipping.")
                    continue  # Skip unknown functions
                function_to_call = available_functions.get(tool_call.function.name)
                if function_to_call is None:
                    print(f"Function {tool_call.function.name} not found, skipping.")
                    continue
                print(
                    f"Calling function: {tool_call.function.name} with arguments: {tool_call.function.arguments} ...."
                )
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": function_response,
                    }
                )
                print(f"Function response: {function_response}")

            # DO NOT append the assistant message here!
            # Loop continues so the model can reply to the tool result.
        if response_message.content:
            print(f"\n\nFinal response: {response_message.content}")
            break
    return messages


if __name__ == "__main__":
    chat_history = asyncio.run(tool_calling_loop())
    print("-------------------")
    for msg in chat_history:
        print(msg, end="\n\n")
