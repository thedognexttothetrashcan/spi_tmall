#coding=utf-8
import pymysql

def mysql_conn():
    # conn=pymysql.connect(host='localhost',user='pdiuser01',passwd='h87skwu62k',db='pdi_manager',charset='utf8')
    conn=pymysql.connect(host='211.103.199.79',port=60036,user='pdimanager',passwd='h9k8@j89sks.',db='pdi_data',charset='utf8')

    return conn

def get_list(sql):
    conn=mysql_conn()
    cur=conn.cursor()
    cur.execute(sql)
    ds=cur.fetchall()
    cur.close()
    conn.close()
    return ds


def get_one(sql):
    conn=mysql_conn()
    cur=conn.cursor()
    cur.execute(sql)
    ds=cur.fetchone()
    cur.close()
    conn.close()
    return ds


def execute_sql(sql):
    conn=mysql_conn()
    cur=conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

def execute_proc(proname,val):
    conn=mysql_conn()
    cur=conn.cursor()
    cur.callproc(proname,val)
    reval=cur.fetchone()
    cur.close()
    conn.commit()
    conn.close()
    return reval
    
