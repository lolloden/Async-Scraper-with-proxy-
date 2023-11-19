import threading
import queue
import requests
import re

q = queue.Queue()
valid_proxies = []
valids = f"valid_proxies.txt"
open(valids, 'w').close()  # erase file content

with open("proxies.txt", "r") as f:     # https://github.com/TheSpeedX/PROXY-List/blob/master/http.txt
    proxies = f.read().split("\n")
    for p in proxies:
        q.put(p)
f.close()
count = 0


def check_proxies():
    global q
    global count

    while not q.empty():
        proxy = q.get()
        try:
            res = requests.get("http://ipinfo.io/json",
                               proxies={"http": proxy,
                                        "https": proxy},
                               timeout=5
                               )
        except IOError:
            print("Connection error!")
            continue
        except Exception as e:
            print("error!")
            continue
        if res.status_code == 200:
            count += 1
            with open(valids, 'a') as myfile:
                myfile.write(proxy + '\n')
                print(f"{count} : {proxy}")

            myfile.close()


for _ in range(10):
    threading.Thread(target=check_proxies).start()
