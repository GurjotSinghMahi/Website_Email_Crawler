from lxml.html import fromstring
import requests
from itertools import cycle
import traceback
import re


######################FIND PROXIES#########################################
def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:299]:   #299 proxies max
        proxy = ":".join([i.xpath('.//td[1]/text()')
        [0],i.xpath('.//td[2]/text()')[0]])
        proxies.add(proxy)
    return proxies