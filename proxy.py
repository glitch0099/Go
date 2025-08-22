import json
import datetime
import requests
import re
import sys
from concurrent.futures import ThreadPoolExecutor

class DownloadProxies:
    def __init__(self) -> None:
        self.api = {
           'socks4':[
                "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all",
                "https://www.proxy-list.download/api/v1/get?type=socks4",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all&simplified=true",
                "https://api.openproxylist.xyz/socks4.txt",
                "https://raw.githubusercontent.com/sunny9577/proxy-scraper/refs/heads/master/generated/socks4_proxies.txt",
                "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
                'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt',
                'https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt',
                'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/socks4.txt',
                'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/socks4_proxies.txt',
                'https://proxyspace.pro/socks4.txt',
                'https://raw.githubusercontent.com/noctiro/getproxy/refs/heads/master/file/socks4.txt',
                'https://raw.githubusercontent.com/mzyui/proxy-list/refs/heads/main/socks4.txt',
                'https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/socks4.txt',
            ],
            'socks5': [
                'https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/socks5.txt',
                "https://raw.githubusercontent.com/mzyui/proxy-list/refs/heads/main/socks5.txt",
                "https://raw.githubusercontent.com/noctiro/getproxy/refs/heads/master/file/socks5.txt",
                "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all&simplified=true",
                "https://www.proxy-list.download/api/v1/get?type=socks5",
                "https://api.openproxylist.xyz/socks5.txt",
                "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
                'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt',
                'https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt',
                'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/socks5_proxies.txt',
                'https://proxyspace.pro/socks5.txt',
                'https://raw.githubusercontent.com/sunny9577/proxy-scraper/refs/heads/master/generated/socks5_proxies.txt',
            ],
            'http': [
                "https://raw.githubusercontent.com/mzyui/proxy-list/refs/heads/main/http.txt",
                "https://raw.githubusercontent.com/noctiro/getproxy/refs/heads/master/file/http.txt",
                "https://raw.githubusercontent.com/noctiro/getproxy/refs/heads/master/file/https.txt",
                "https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt",
                "https://api.proxyscrape.com/?request=displayproxies&proxytype=http",
                "https://www.proxy-list.download/api/v1/get?type=http",
                'https://www.proxy-list.download/api/v1/get?type=https',
                "https://api.openproxylist.xyz/http.txt",
                "https://raw.githubusercontent.com/sunny9577/proxy-scraper/refs/heads/master/generated/http_proxies.txt",
                "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
                'https://raw.githubusercontent.com/aslisk/proxyhttps/refs/heads/main/https.txt',
                'https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/refs/heads/main/cnfree.txt',
                'https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/refs/heads/main/free.txt',
                'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/http.txt',
                'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/https.txt',
                'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/http_proxies.txt',
                'https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/https_proxies.txt',
                'https://raw.githubusercontent.com/yemixzy/proxy-list/refs/heads/main/proxies/http.txt',
                'https://proxyspace.pro/http.txt',
                'https://proxyspace.pro/https.txt',
            ]
        }
        self.proxy_dict = {'socks4': [], 'socks5': [], 'http': []}

    def get_proxy_from_api(self, api_url):
        try:
            response = requests.get(api_url)
            proxies = response.text.splitlines()
            return proxies
        except requests.exceptions.RequestException as e:
            print(f"Error fetching proxies from {api_url}: {e}")
            return []

    def get(self, proxy_type):
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.get_proxy_from_api, api) for api in self.api[proxy_type]]
            for future in futures:
                self.proxy_dict[proxy_type] += future.result()

        self.proxy_dict[proxy_type] = list(set(self.proxy_dict[proxy_type]))
        print(f'> Get {proxy_type} proxies done')

    def save(self, proxy_type=None, filename='proxies.txt'):
        if proxy_type:
            self.proxy_dict[proxy_type] = list(set(self.proxy_dict[proxy_type]))
            with open(filename, 'w') as f:
                for i in self.proxy_dict[proxy_type]:
                    if '#' in i or i == '\n':
                        self.proxy_dict[proxy_type].remove(i)
                    else:
                        f.write(i + '\n')
            print(f"> Have already saved {len(self.proxy_dict[proxy_type])} {proxy_type} proxies list as {filename}")
        else:
            with open(filename, 'w') as f:
                for proxy_type in ['http', 'socks4', 'socks5']:
                    self.proxy_dict[proxy_type] = list(set(self.proxy_dict[proxy_type]))
                    for i in self.proxy_dict[proxy_type]:
                        if '#' in i or i == '\n':
                            self.proxy_dict[proxy_type].remove(i)
                        else:
                            f.write(i + '\n')
            print(f"> Have already saved all proxies list as {filename}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage:")
        print("1: Download HTTP proxies")
        print("2: Download SOCKS4 proxies")
        print("3: Download SOCKS5 proxies")
        print("4: Download all types of proxies")
    elif len(sys.argv) >= 2:
        d = DownloadProxies()
        option = sys.argv[1]
        filename = 'proxies.txt' if len(sys.argv) == 2 else sys.argv[2]
        if option == '1':
            proxy_type = 'http'
            d.get(proxy_type)
            d.save(proxy_type, filename)
        elif option == '2':
            proxy_type = 'socks4'
            d.get(proxy_type)
            d.save(proxy_type, filename)
        elif option == '3':
            proxy_type = 'socks5'
            d.get(proxy_type)
            d.save(proxy_type, filename)
        elif option == '4':
            for proxy_type in ['http', 'socks4', 'socks5']:
                d.get(proxy_type)
            d.save(filename=filename)
        else:
            print("Invalid option. Please use 1 for HTTP, 2 for SOCKS4, 3 for SOCKS5, or 4 for all types.")
            sys.exit(1)
