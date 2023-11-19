import asyncio
from bs4 import BeautifulSoup
from contextlib import contextmanager
import random
from colorama import Fore
import os.path


class TooManyRetries(Exception):
    def __str__(self):
        class_name = type(self).__name__
        exception_args = self.args
        if len(exception_args) > 0:
            return f'{class_name}: {exception_args[0]}'
        return class_name


class Bot:
    link_list = []
    filename_list = []
    ua_list = [
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; 2201116SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.10",
        ""]
    headers = {'User-Agent': ua_list[3]}

    with open("valid_proxies.txt", "r") as pf:
        proxies = pf.read().split("\n")

    proxies_in_use = []
    WORKERS = 5

    # URLS = [
    #     f"http://books.toscrape.com/catalogue/page-{x}.html" for x in range(1, 11)
    # ]

    async def retry(self, coro, url, max_retries=3, timeout=2.0, retry_interval=1.0):
        for retry_num in range(max_retries):
            try:
                return await asyncio.wait_for(coro, timeout=timeout)
            except TooManyRetries as e:
                # catch any exception because we want to retry upon any failure
                print(f'request to {url} failed. (tried {retry_num + 1} times)')
                await asyncio.sleep(retry_interval)

    async def fetch(self, client, url):
        with self.allocate_proxy() as proxy:
            print(Fore.YELLOW + f"Fetching url: {url[7:55]} (P:{proxy})")
            async with client.get(url, allow_redirects=False,
                                  ssl=False,
                                  raise_for_status=True,
                                  proxy=f"http://{proxy}",
                                  timeout=5,
                                  headers=self.headers) as r:
                r.raise_for_status()

                print(Fore.GREEN + f'request to {url} completed successfully!')
                return await r.text()

    @contextmanager
    def allocate_proxy(self):
        """Get a free proxy and hold it as in use"""
        available_proxies = [p for p in self.proxies if p not in self.proxies_in_use]  # Select proxies that are not in use
        if available_proxies:
            proxy = random.choice(available_proxies)

        else:
            self.proxies_in_use.clear()
            return self.allocate_proxy()
            # proxy = random.choice(proxies) 
        try:
            self.proxies_in_use.append(proxy)
            yield proxy
        finally:
            self.proxies_in_use.remove(proxy)

    async def worker(self, q, client):
        loop = asyncio.get_running_loop()
        while True:
            url = await q.get()
            try:
                html = await self.retry(self.fetch(client, url), url)
                # html = await self.fetch(client, url)   # use this for skip retry feature
            except Exception as e:
                print(Fore.LIGHTRED_EX + f"error: {e.__class__}")
                await asyncio.sleep(0.5)
            else:
                filename_index = self.link_list.index(f"{url}")
                filename = str(self.filename_list[filename_index])
                await loop.run_in_executor(None, self.save_to_disk, url, html, filename)
            finally:
                q.task_done()

    def save_to_disk(self, url, html, f_name):
        soup = BeautifulSoup(html, 'html.parser')
        # print(Fore.BLUE + f"len({len(html)})")
        try:
            file = open(f"results/{f_name}.txt", 'r')
            print(Fore.LIGHTMAGENTA_EX + "file exists")
            # sometimes response can be null, rewrite file with new response
            if os.stat(f"results/{f_name}.txt").st_size == 0:
                if len(html) > 0:
                    file = open(f"results/{f_name}.txt", 'w')
                    file.write(str(soup))
                    print(Fore.LIGHTMAGENTA_EX + "file empty rewritten")
        except FileNotFoundError:
            if len(html) > 0:
                file = open(f"results/{f_name}.txt", 'w')
                file.write(str(soup))
