
from litellm import completion, acompletion

def sync_ollama():
    response = completion(
        model="ollama/deepseek-r1", 
        messages=[{ "content": "respond in 20 words. who are you?","role": "user"}], 
        api_base="http://localhost:11434"
    )
    print(response)

async def async_ollama():
    response = await acompletion(
        model="ollama/deepseek-r1", 
        messages=[{ "content": "what's the weather" ,"role": "user"}], 
        api_base="http://localhost:11434", 
        stream=True
    )
    async for chunk in response:
        print(type(chunk))
        print(chunk.choices[0].delta.content, end="", flush=True)

# call async_ollama
import asyncio
asyncio.run(async_ollama())