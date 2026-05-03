import os, asyncio
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import groq as groq_plugin
from agent import KYCAgent
from dotenv import load_dotenv

load_dotenv()

async def test():
    llm = groq_plugin.LLM(model="llama-3.3-70b-versatile")
    agent = KYCAgent(room_name="test")
    ctx = ChatContext()
    ctx.messages.append(ChatMessage(role="system", content="You have a tool save_kyc_data. Call it now with name Sanjai."))
    ctx.messages.append(ChatMessage(role="user", content="Call the save_kyc_data tool for name Sanjai"))
    
    try:
        stream = llm.chat(chat_ctx=ctx, fnc_ctx=agent)
        async for chunk in stream:
            print(chunk)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
