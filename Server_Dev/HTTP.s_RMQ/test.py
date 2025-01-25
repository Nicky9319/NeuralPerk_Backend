import aiohttp
import asyncio

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            text = await response.text()
            return [response,text]

async def main():
    url = 'http://127.0.0.1:8000/test'
    response = await fetch(url)
    print(response)
    print(response[1])
    print(response[0].status)
    print(response[0].reason)

if __name__ == '__main__':
    asyncio.run(main())