import asyncio
from agent import handle_user_message



async def local_test():
    while True:
        query = input("You: ")
        if query.lower() in ['quit', 'exit', 'bye']:
            break

        response = await handle_user_message(1, query)
        print("Agent:", response.data)


if __name__ == "__main__":
    asyncio.run(local_test())