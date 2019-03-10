#coding=utf-8
import tmall_dba as dba


def update_productlist():
    """
    更新productlist
    检查productdetail表格，更新produtlist的 newcomments,newsales字段，
    如果发现评论或销量少于100的，就设置status字段，不再抓取。
    """

    sql="select id from pdi_data.tm_productlist where status=0"
    ds=dba.get_list(sql)

    for p in ds:
        psid=p[0]
        sql="select psid,sales, commentsnum from pdi_data.tm_productdetail where psid=%s order by adddate desc limit 1" % psid
        ds2=dba.get_one(sql)
        print(psid)

        sales=ds2[1]
        newcomments=ds2[2]
        if sales<100:
            sql="update pdi_data.tm_productlist set status=2,newcomments=%s,newsales=%s where id=%s" % (newcomments,sales,psid)
            dba.execute_sql(sql)
        else:
            sql="update pdi_data.tm_productlist set newcomments=%s,newsales=%s where id=%s" % (newcomments,sales,psid)
            dba.execute_sql(sql)

    
