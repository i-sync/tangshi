#!/usr/bin/env python
# _*_ coding: utf-8 _*_

import json
import os
import os.path
import re
import requests
import threading
import time
import socket
from colors import PrintInColor

url1 = 'http://duguoxue.cn/tangshi/sanbaishou/index.html'
url2 = 'http://duguoxue.cn/tangshi/sanbaishou/list-2.html'
url3 = 'http://duguoxue.cn/tangshi/sanbaishou/list-3.html'

reg_url = re.compile(r'<a href="(http://www.duguoxue.com/tangshi/\d+.html)"')
reg_file = re.compile(r'<video src="(http://v2014.duguoxue.com/.+/.*\.mp3)"')

urls = []
proxy = []
success = []
fail_proxy = []

success_file = 'success.txt'
fail_proxy_file = 'fail_proxy.txt'

lock_proxy = threading.Lock()
lock_proxy_file = threading.Lock()
lock_file = threading.Lock()


def init():
    with open('proxy.json', 'r') as f:
        data = f.readline().strip('\n')
        proxy.extend(json.loads(data))
        #print(proxy)

    print('proxy count:{}'.format(len(proxy)))


    with open(fail_proxy_file, 'r') as f:
        for line in f.readlines():
            line = line.strip('\n')
            fail_proxy.append(line)
        #print(proxy)

    print('fail_proxy count:{}'.format(len(fail_proxy)))

    if os.path.exists(success_file):
        with open(success_file, 'r') as f:
            for line in f.readlines():
                line = line.strip('\n')
                success.append(line)
            #print(proxy)

    print('success count:{}'.format(len(success)))

def write_success(url):
    with lock_file:
        with open(success_file, 'a+') as f:
            f.write('{}\n'.format(url))

def write_fail_proxy(host):
    with lock_proxy_file:
        with open(fail_proxy_file, 'a+') as f:
            f.write('{}\n'.format(host))

def get_proxy():
    '''
    get a worked proxy
    :return: proxy
    '''
    with lock_proxy:
        current_proxy = None
        if len(proxy) > 0:
            current_proxy = proxy.pop()
            #while current_proxy['type'] != 'http' or current_proxy['host'] in fail_proxy:
            
            while current_proxy['host'] in fail_proxy:
                if len(proxy) > 0:
                    current_proxy = proxy.pop()
                else:
                    current_proxy = None
                    print('proxy pool is empty...')
                    break
            
        else:
            print('proxy pool is empty...')

    return current_proxy

def put_proxy(x):
    with lock_proxy:
        proxy.append(x)

def get_urls(url):
    res = requests.get(url)
    if res.status_code == 200:
        data = res.text
        url_data = reg_url.findall(data)
        if len(url_data) > 0:
            for i in url_data:
                print(i)
                urls.append(i)
    else:
        print('{} get error...'.format(url))
        return


def get_files(urls):
    print('start get file...')

    current_proxy = get_proxy()
    while current_proxy is None:
        print('first no proxy to use, sleep 60s ... proxy count:{}'.format(len(proxy)))
        time.sleep(60)
        current_proxy = get_proxy()

    proxies = {
        '{}'.format(current_proxy['type']): '{}://{}:{}'.format(current_proxy['type'], current_proxy['host'], current_proxy['port'])
    }

    for url in urls:
        try:
            res = requests.get(url, proxies = proxies, timeout = 10)
            if res.status_code == 200:
                data = res.content.decode('utf-8')
                match = reg_file.search(data)
                if match:
                    file_url = match.group(1)
                    file_name = file_url.split('/')[-1]
                    if file_url not in success:
                        r = requests.get(file_url, proxies = proxies, timeout = 60)

                        if r.status_code == 200:
                            with open('files/{}'.format(file_name), 'wb') as f:
                                f.write(r.content)
                            PrintInColor.green('{}: success...'.format(file_url))
                            write_success(file_url)
                        else:
                            PrintInColor.red('{}: download failed, status_code :{} ...'.format(file_url, r.status_code))
                    else:
                        PrintInColor.red('{}: has been download...'.format(file_url))
                else:
                    PrintInColor.red('{}: no mp3 file...'.format(url))
            else:
                continue
        except Exception as e:
            write_fail_proxy(current_proxy['host'])
            PrintInColor.yellow(str(e))

            current_proxy = get_proxy()
            while current_proxy is None:
                print('no proxy to use, sleep 60s ... proxy count:{}'.format(len(proxy)))
                time.sleep(60)
                current_proxy = get_proxy()

            proxies = {
                '{}'.format(current_proxy['type']): '{}://{}:{}'.format(current_proxy['type'], current_proxy['host'], current_proxy['port'])
            }

        time.sleep(5)

        #put current proxy to proxy pool
    plen = len(proxy)
    put_proxy(current_proxy)
    nlen = len(proxy)
    print('put proxy:{} into proxy pool, prev num:{} next num:{}.'.format(current_proxy['host'], plen,nlen))

def main():
    init()

    get_urls(url1)
    get_urls(url2)
    get_urls(url3)
    #urls = ['http://www.duguoxue.com/tangshi/25436.html', 'http://www.duguoxue.com/tangshi/25437.html']
    print('urls count:{}'.format(len(urls)))

    threads = []
    count = 5

    threadNum = len(urls) // count + (0 if len(urls) % count == 0 else 1)
    for i in range(threadNum):
        u = urls[i * count: (i+1)* count]
        threads.append(threading.Thread(target= get_files, args = (u,)))
    
    print('threads num: {}'.format(len(threads)))

    #sleep 5 second
    time.sleep(5)

    print('start threads...')
    for t in threads:
        t.start()

    # waitting all thread ends
    print('waitting all threads end...')
    for t in threads:
        t.join()

    print('all threads are done...')


if __name__ == '__main__':
    main()