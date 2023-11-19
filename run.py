import asyncio
import aiohttp
import urllib3
import time
from colorama import Fore
import bot_class


# Disable warnings about SSL verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

bot = bot_class.Bot()


for x in range(1, 11):
    bot.link_list.append(f"http://books.toscrape.com/catalogue/page-{x}.html")
    bot.filename_list.append(f"result{x}")


async def main():
    q = asyncio.Queue(maxsize=400)
    tasks = []

    async with aiohttp.ClientSession() as client:

        for _ in range(bot.WORKERS):
            tasks.append(asyncio.create_task(bot.worker(q, client)))

        for url in bot.link_list:
            await q.put(url)

        await q.join()

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    t = time.time()
    main = asyncio.run(main())
    total = time.time() - t
    print(Fore.LIGHTWHITE_EX + str(total))

    # print(bot.link_list)
    # print(bot.filename_list)
