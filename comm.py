#! /usr/bin/python
# encoding=utf-8

import os
import datetime,time
from selenium import webdriver
import config
import threading 
import numpy as np

def writelog(msg,log):
    nt=datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    text="[%s] %s " % (nt,msg)
    os.system("echo %s >> %s" % (text.encode('utf8'),log))

def create_chrome():
    ops=webdriver.ChromeOptions()
    ops.add_experimental_option('mobileEmulation',config.mobileEmulation)

    web=webdriver.Chrome(chrome_options=ops)
    web.set_page_load_timeout(10)
    web.set_script_timeout(10)
    web.set_window_size(config.mWidth,config.mHeight)
    return web

#Create Threading Pool 
def threading_pool(tnum,funname):
    threadlist=[]
    for i in range(tnum):
        t=threading.Thread(target=funname)
        threadlist.append(t)

    for t in threadlist:
        t.setDaemon(True) 
        t.start()

    for t in threadlist:
        t.join()
    
    return threadlist

def set_interval(*args):
    s = 3
    e = 6
    if len(args)>=1:
        s = args[0]
    if len(args)>=2:
        e = args[1]
        
    f = np.random.uniform(s,e)
    time.sleep(f)  
