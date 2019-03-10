#coding=utf-8

# import numpy as np
import datetime
import time
# import MySQLdb
# import cookielib,urllib,urllib2
# from lxml import etree
# from selenium import webdriver
import dbhelper as dba
import threading
import re
import pdb
import json
import comm
from selenium.common import exceptions

def sel_commentlist(commdt,psid):
    commList=commdt['rateList']
    info=list()
    
    for dc in commList:
        tmallcommentID=dc['id']
        CommentText=dc['rateContent']
        username=dc['displayUserNick']
        parames=dc['auctionSku']
        #viplevel=dc['attributesMap']['tmall_vip_level']
        #时有时无，暂时先不抓了。
        viplevel=0
        createtime=dc['rateDate']
        info.append((psid,tmallcommentID,CommentText,username,viplevel,parames,createtime))
    return info

### 用来获取天猫评论内容，从json中。
def get_comment_html(browser,url):
    while True:
        try:
            #request=urllib2.Request(url,headers=header)
            #html=urllib2.urlopen(url).read()
            browser.get(url)
            comm.set_interval(1,3)
            html=browser.page_source
            break
        except Exception as e:
            print("get_comment_html: %s " % e)
            time.sleep(30)
            print('Try again.')
    result=0
    try:
        html=html.encode('utf-8')
        html=re.search('<body>(.*)</body>',html).group(1)
        html=html.strip()
        
        commdt=json.loads(html[13:])
        result=1
    except Exception as e:
        result=0
        commdt={}

    return result,commdt


def add_product_comment(commList):
    """
    return 0 正常，1，已经存在，不再采集。
    """
    res=0
    conn=dba.mysql_conn()

    for it in commList:
        cursor=conn.cursor()
        cursor.callproc("pdi_manager.tm_insert_product_comment",it)
        reval=cursor.fetchone()
        cursor.close()

        if reval[0]>0:
            res=1
            break

    conn.commit()
    conn.close()

    return res

  
### 采集产品详细页 ### 
def get_product_detail(browser,info):
    """
    1、获取产品信息，
    2、评论获取URL

    """
    url=info['url']
    psid=info['id']

    print('get tm content,psid=',psid)

    #转换成mobile
    url=url.replace('detail.tmall','detail.m.tmall')
    if url[:4] != 'http':
        url='https:'+url


    while 1:
        try:
            browser.get(url)
            comm.set_interval(2,5)

            #页面跳转了
            if browser.current_url.find('detail.m.tmall.com')==-1:
                sql="update pdi_data.tm_productlist set status=3,removedTime='%s' where id=%s" %  (today,psid)
                dba.execute_sql(sql)
                return 0

            #商品页面不存在
            if browser.current_url.find('notfound.htm')>0:
                sql="update pdi_data.tm_productlist set status=1,removedTime='%s' where id=%s" %  (today,psid)
                dba.execute_sql(sql)
                return 0

            #商品已经下架
            oa=browser.find_element_by_xpath('//*[@id="s-actionBar-container"]/div/div[2]/a[3]')
            if oa.text==u'已下架':
                sql="update pdi_data.tm_productlist set status=2,removedTime='%s' where id=%s" %  (today,psid)
                dba.execute_sql(sql)
                return 0


            browstitle=browser.title.strip()
            titles=[u'上天猫，就够了',u'淘宝网 - 淘！我喜欢',u'理想生活上天猫']
        
            if browstitle not in titles:
                break
            else:
                s=10
                time.sleep(s)  

        except exceptions.TimeoutException:
            print("Timeout")
            browser.refresh()
        except Exception  as e:
            print(e)
      


    pnamepath='//*[@id="J_mod4"]/div/div/div'
    title1=browser.find_element_by_xpath(pnamepath).text
    productname=title1.strip()

    try:
        tmsell=browser.find_element_by_xpath('//*[@id="J_mod6"]/div/span[2]').text
        tmsell=int(re.sub('月销量|件','',tmsell).strip())
    except:
        tmsell=0

    try:
        commnum=browser.find_element_by_xpath('//*[@id="mui-tagscloud-i"]/div[1]/div[1]').text
        commnum=re.sub('商品评价','',commnum).strip()
        commnum=int(commnum[1:-1])
    except:
        commnum=0


    #更新产品详细信息。sales,commentsnum,title
    #
    try:
        pdinfo=(info['pid'],info['id'],productname,0,tmsell,commnum,0,today)
        dba.execute_proc('pdi_manager.tm_productdetail_add',pdinfo)
    except Exception as e:
         print("Mysql Error %d: %s" % (e.args[0], e.args[1]))

    
    if commnum==0 or tmsell==0:
        return 0


    #获取产品评论信息参数,itemid ,sellerid
    txt=browser.page_source
    txt=txt.encode('utf-8')
    sellerid=re.search(r'"userId":(\d*)',txt).group(1)
    itemid=re.search(r'itemId=(\d*)',txt).group(1)

    currentPage=1
    comm_url='https://rate.tmall.com/list_detail_rate.htm?itemId=%s&sellerId=%s&order=1&pageSize=20' % (itemid,sellerid)
    while True:
        #计算页码，判断如果已经抓取最新的就停止，默认取第一页，按时间排序
        print('title:%s, page:%s' % (productname,currentPage))
        url=comm_url+'&currentPage=%s' % currentPage
        htmljson=get_comment_html(browser,url)

        if htmljson[0]==1:
            commdt=htmljson[1]
        else:
            return 'err_0'

        commList=sel_commentlist(commdt,psid)
        reval=add_product_comment(commList) 
        #如果发现已经存在的评论内容，就停止本次采集。        time.sleep(0.8)
        if reval>0:
            break
       
        try:
            lastpage=commdt['paginator']['lastPage']
            page=commdt['paginator']['page']
    
            if currentPage<lastpage:
                currentPage +=1
            else:
                break   
        except:
            print('find page.')

        time.sleep(0.8)


##############################################################
def run_process():

    brows=comm.create_chrome()
    brows.get('http://tmall.com')
    time.sleep(1)

    while True:
        try:
            item=workQueue.get(block=False)
        
            get_product_detail(brows,item)
            sql="update pdi_data.tm_productlist set updateTime='%s' where id=%s" % (today,item['id'])
            dba.execute_sql(sql)
        except Queue.Empty:
            break
    brows.close()

    print('Completed work, have a rest.')
    ### Step3 End


#####################################################################
import sys
from queue import Queue
import argparse

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('-tnum',type=int,default=1)
    parser.add_argument('-bid',type=int,default=0)

    args=parser.parse_args()
    _bid=args.bid
    _tnum=args.tnum

    while 1:        
        if _bid==0:
            sql="select id,pid,url,newComments from pdi_manager.view_productlist  where status=0 and (updateTime<'%s' or updateTime is null) and flag=1" % today
        else:
            sql="select id,pid,url,newComments from pdi_manager.view_productlist  where status=0 and bid in (%s) and (updateTime<'%s' or updateTime is null) and flag=1" % (_bid,today)
        ds=dba.get_list(sql)
    
        #proc.user_login(brows)
        for item in ds:
            id=item[0]
            pid=item[1]
            url=item[2]
            lastComments=item[3]
    
            info={'id':id,'pid':pid,'url':url,'lastComments':lastComments}
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

