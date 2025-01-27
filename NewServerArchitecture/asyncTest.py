import asyncio

# Asynchronous function
async def async_function():
    print("Async function starts")
    await asyncio.sleep(2)  # Simulating an asynchronous operation
    print("Async function ends")
    return "Hello from async_function!"

# Synchronous function
def sync_function():
    print("Sync function starts")
    asyncio.create_task(async_function())  # Create task for async_function
    print("Sync function continues")
    print("Sync function ends")

# Main function
async def main():
    print("Main function starts")
    sync_function()
    print("Main function ends")

    await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
