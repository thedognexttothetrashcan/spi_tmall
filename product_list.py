#! /usr/bin/python
# encoding=utf-8
"""
*从产品列表页面获取产品列表
*更多商家列表，用以抓取更多的产品，和评论
参数说明:
rt: 1,0 如果是1，立即运行。
"""

#print __doc__
from queue import Queue
# import numpy as np
import datetime,time
# import MySQLdb
# import cookielib,urllib,urllib2
from lxml import etree
import json
from selenium import webdriver
import dbhelper as dba
import comm
import pdb

log='product_list.log'
maxsize=15

### Step1: 采集产品列表:w
def get_product_list(brows,item):
    url=item['url']
    bid=item['id']

    while True:
        try:
            brows.get(url)
            print('waiting...')
            comm.set_interval(2,4)
            browstitle=brows.title.strip()
            titles=['上天猫，就够了','淘宝网 - 淘！我喜欢','理想生活上天猫','SecurityMatrix']
        
            if browstitle not in titles:
                break
            else:
                s=30
                print('Please impot verycode!')
                while True:
                    browstitle=brows.title.strip()
                    time.sleep(s)
                    if browstitle not in titles:
                        break
        except Exception as e:
            print("Get_product_list:%s"  % e)
            return 0

    for pn in range(1,maxsize):
        #get list from json
        parms=url.split('?')[1]
        jsonurl='https://list.tmall.com/m/search_items.htm?page_size=20&page_no=%s&%s' % (pn,parms)
        #print jsonul
        #raise Exception('stop....')
        while True:
            try:
                txt=urllib2.urlopen(jsonurl).read()
                comm.set_interval(3,7)
        
                data=json.loads(txt)
                break
            except:
                print('Load json error,waiting 30s.')
                time.sleep(30)
                brows.get(url)

        prols=data['item']
        for item in prols:
            product_url=item['url']
            product_name=item['title']
            price=float(item['price'])
            comment_num=item['comment_num']
            if comment_num=='':
                comment_num=0
            else:
                comment_num=int(comment_num)

            sold=item['sold']
            if sold=='***':
                sold=-1
            elif sold.find('万')>0:
                sold=float(sold.replace('万',''))*10000
            else:
                sold=float(sold)
    
            #add product to tm_product
            product_id=dba.execute_proc('pdi_manager.tm_product_add',(bid,product_name))[0]        

            shop_name=item['shop_name']
            
            #step4: add to productlist
            psinfo=(product_id,product_name,shop_name,product_url,comment_num,sold)
            psid=dba.execute_proc('pdi_manager.tm_productlist_add',psinfo)[0]
        
            score=0
            pdinfo=(product_id,psid,product_name,price,sold,comment_num,score,today)
            dba.execute_proc('pdi_manager.tm_productdetail_add',pdinfo)
                            
            #product_name,price,salesNum      
            salesinfo=(product_id,price,sold,today)
            dba.execute_proc('pdi_manager.tm_productsales_add',salesinfo)
            print('Get Product:[%s] %s ' % (product_id,product_name))
            

 
#############################################################
def run_process():

    brows=comm.create_chrome()
    brows.get('http://tmall.com')
    time.sleep(1)
    while True:
        try:
            item=workQueue.get(block=False)
            bid=item['id']

            get_product_list(brows,item)

            sql="update pdi_manager.tm_brand set LastDate='%s' where id=%s" % (today,bid)
            dba.execute_sql(sql)
        except Queue.Empty:
            break
    brows.close()


############## main block  ##################################
import sys

import argparse

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-tnum',type=int,default=1)
    parser.add_argument('-bid',type=int,default=0)

    args=parser.parse_args()
    _bid=args.bid
    _tnum=args.tnum

    while 1:

        print('Step1:begin')
        #Set workQueue
        if _bid==0: 
            sql="select id,url from pdi_manager.tm_brand where flag=1 and LastDate<'%s'" % today
        else:
            sql="select id,url from pdi_manager.tm_brand where flag=1 and id=%s" % bid
        dataset=dba.get_list(sql)
        print('test1 %s' %len(dataset))
        for dr in dataset:
            brid=dr[0]
            burl=dr[1]
            info={'id':brid,'url':burl}
            workQueue.put(info)
    
        if _tnum==1:
            run_process()
        else:
            comm.threading_pool(_tnum,run_process)
        
        wt=3600*12
        print('complete.waiting 12h...')
        time.sleep(wt)

        
if __name__=='__main__':
    workQueue=Queue()
    today=datetime.datetime.now().strftime('%Y-%m-%d')
    main()
