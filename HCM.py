#-*- encoding=GBK -*-
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httpclient
import tornado.options
import httplib
import json
import os
import time
import thread
import threading
import datetime
import re
from functools import wraps


#-------------------配置项----------------------------------------
ListenPort = 8888                                 #服务监听端口
hotcount = 3                                       #超过这个次数算热URL
hot_url_calc_cycle = datetime.timedelta(0,5,0)    #热点计算周期
expire_time = datetime.timedelta(0,600,0)          #URL过期时间
ISOTIMEFORMAT='%Y-%m-%d %X'                        #URL访问时间格式
UpdateThreadCount=15                          #请求CACHE回源的线程数量
CacheIp = "124.126.126.103:80/302_mark/"
#-------------------end------------------------------------------


#---------------------日志对象配置---------------------------------
import logging
fh = logging.handlers.RotatingFileHandler("HCM.log",maxBytes=100*1024*1024,backupCount=5)
fh.setLevel(logging.NOTSET)
formatter = logging.Formatter('%(asctime)s %(funcName)s %(lineno)d %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log =logging.getLogger()
log.setLevel(logging.NOTSET)
log.addHandler(fh)
#----------------------------end---------------------------------



#装饰器  输出函数的开始时间与结束时间及耗时
def PrintBegEndTime(func):
    @wraps(func)
    def _wrap(*args,**kwargs):
        log.info("Enter Function " + func.__name__)
        b = time.time()
        ret=func(*args,**kwargs)
        log.info("Leave Function %s,Cost %r s",func.__name__,time.time()-b)
        return ret
    return _wrap

pattern_youku = re.compile(r"(\w+://)?([^/]+)(/youku/)(.+/)*([^.?/]+\.(mp4|flv)(?=\?|$))(\?([^&=]+=[^&]+)((&[^=]+=[^&]+)*))?")
filter_set_youku = {'nk','ns','start'}
pattern_star = re.compile(r"[^/]+/")

pattern_default = re.compile(r"(\w+://)?(.+)")

def UrlTrans(url):
    url_MIE=''
    url_cache=''
    match=pattern_youku.match(url)
    if match:
        url_MIE=match.expand(r'\1\2\3'+pattern_star.sub(r'*/',match.expand(r'\4'))+r'\5')
        url_cache=match.expand(r'\1')+CacheIp+match.expand(r'\2\3\4\5')
        tmp = list()
        if match.group(7):
            tmp.append(match.group(8))
            if match.group(9):
                tmp.extend(match.group(9)[1:].split('&'))
        tmpstr=''
        for i in tmp:
            if i.split('=')[0] not in filter_set_youku:
                tmpstr+=i
        if tmpstr:
            url_cache+='?'
            url_cache+=tmpstr
        return url_MIE,url_cache

    
    #default case
    return None
    match = pattern_default.match(url)
    if match.group(1):
        url_cache=match.group(1)
    else:
        url_cache=""
    url_cache+=CacheIp
    url_cache+=match.group(2)
    
    return url,url_cache


Cond_UrlBuff = threading.Condition()
list1 = list()
UrlStorage = dict()
mutex_url_storage = threading.Lock()

@PrintBegEndTime
def UrlRecordPostFun(ip,records):
    '''接收URL列表并处理'''
    log.info("从MIE %r接收到URL记录%d条",ip,len(records))
    #for i in records:
    #    log.info("%r",i)
    Cond_UrlBuff.acquire()
    list1.append(records)
    Cond_UrlBuff.notifyAll()
    Cond_UrlBuff.release()
    return {"MsgType":"UrlRecordPostAck","ErrorCode":0,"ErrorDescription":None}
    
def DesposeUrlRecordThread():
    global list1
    list2=list()
    while 1:
        Cond_UrlBuff.acquire()
        while not list1:
            Cond_UrlBuff.wait()
        list2,list1 = list1,list2
        Cond_UrlBuff.release()

        b = time.time()
        for x in list2:
            for y in x:
                y["URL"] = UrlTrans(y["URL"])

        mutex_url_storage.acquire()
        for x in list2:
            for y in x:
                if not y['URL']:
                    continue
                url,url2c = y['URL']
                actime = y["AccessTime"]
                if url not in UrlStorage:
                    UrlStorage[url]=[url2c,0,dict()]  #cache_url,stat,{actime:count}
                else:
                    UrlStorage[url][0]=url2c
                UrlStorage[url][2][actime]=UrlStorage[url][2].setdefault(actime,0)+1                
        mutex_url_storage.release()
        log.info("本次处理,URL队列长度:%d,耗时%r s",len(list2),time.time()-b)
        del list2[:]

        
Cond_Add_Del=threading.Condition()
url_table_add = list()
mutex_mit = threading.Lock()
mit_table = dict()    #MIT的CACHE缓存列表,格式 { ip:id,}
last_mit_table = set()
records_mode0=json.dumps({
"MsgType":"CachedContentUpdateAck",
"Mode":0,
"ErrorCode":0,
"ErrorDescription":None,
"ContentTotal":0,
"ContentsAll":[]
})[:-1]+','
records_mode0_default = records_mode0
records_mode1=json.dumps({
"MsgType":"CachedContentUpdateAck",
"Mode":0,
"ErrorCode":0,
"ErrorDescription":None,
"ContentAddTotal":0,
"ContentsAdd":[],
"ContentDelTotal":0,
"ContentsDel":[]
})[:-1]+','
records_mode1_default = records_mode1


def CalcHostListFun():
    '''固定周期计算URL热点'''
    t = threading.Timer(hot_url_calc_cycle.seconds,CalcHostListFun)
    t.start()

    lasttime=(datetime.datetime.now()-expire_time).strftime(ISOTIMEFORMAT)    #比这个时间早的URL将不被统计
    log.info("URL热点计算开始,%s之前的数据将被丢弃",lasttime)
    b=time.time()
    urls_del = list()
    keys_ac_del = list()
    add_list = list()
    hot_set = set()
    
    mutex_url_storage.acquire()
    for url,info in UrlStorage.iteritems():
        count=0
        for actime,hitc in info[2].iteritems():
            if actime<lasttime:
                keys_ac_del.append(actime)
            else:
                count+=hitc
        if count==0 and info[1]!=1 :
            urls_del.append(url)
        else:
            for x in keys_ac_del:
                del info[2][x]
        del keys_ac_del[:]
        
        if count>=hotcount:  
            if info[1]==0:
                add_list.append((url,count,info[0]))   #需要增加的热点
                info[1]=1
            elif info[1]==2:
                hot_set.add(url)    #现有热点
        
    for x in urls_del:
        del UrlStorage[x]
    mutex_url_storage.release()

    add_list.sort(key=lambda x:x[1])
    log.info("本次增加的热点URL%d条",len(add_list))
    log.info("本次删除的URL%d条",len(urls_del))

    Cond_Add_Del.acquire()
    global url_table_add
    add_list.extend(url_table_add)
    url_table_add=add_list
    Cond_Add_Del.notifyAll()
    Cond_Add_Del.release()
    log.info("待下载的热点URL%d条",len(url_table_add))

    #热点增量及全量计算   MIE
    global last_mit_table
    url_add = hot_set-last_mit_table
    url_del = last_mit_table -hot_set
    last_mit_table = hot_set

    global records_mode0
    global records_mode1
    mutex_mit.acquire()
    records_mode0=json.dumps(
        {
        "MsgType":"CachedContentUpdateAck",
        "Mode":0,
        "ErrorCode":0,
        "ErrorDescription":None,
        "ContentTotal":len(last_mit_table),
        "ContentsAll":[{"SerialNum":i,"Content":x} for i,x in enumerate(last_mit_table,1)]
        })[:-1]+','
    records_mode1=json.dumps(
        {
            "MsgType":"CachedContentUpdateAck",
            "Mode":1,
            "ErrorCode":0,
            "ErrorDescription":None,
            "ContentAddTotal":len(url_add),
            "ContentsAdd":[{"SerialNum":i,"Content":x} for i,x in enumerate(url_add,1)],
            "ContentDelTotal":len(url_del),
            "ContentsDel":[{"SerialNum":i,"Content":x} for i,x in enumerate(url_del,1)]
        })[:-1]+','
    mutex_mit.release()
    log.info("热点计算结束，本次耗时%r s",time.time()-b)
    


def CacheUpdateThread():
    while 1:
        Cond_Add_Del.acquire()
        while not url_table_add:
            Cond_Add_Del.wait()
        url,count,url2cache = url_table_add.pop()
        Cond_Add_Del.release()

        client = tornado.httpclient.HTTPClient()
        try:
            log.info("download url:%r",url2cache)
            response = client.fetch(url2cache)
        #except tornado.httpclient.HTTPError as e:
        except Exception as e:
            log.error("download error,err=%s,url=%r",str(e),url2cache)
            mutex_url_storage.acquire()
            UrlStorage[url][1]=0
            mutex_url_storage.release()
            continue

        log.info("download success,url:%r",url2cache)
        mutex_url_storage.acquire()
        UrlStorage[url][1]=2
        mutex_url_storage.release()
        
    
@PrintBegEndTime
def BlackNameUpdateFun():
    '''发送黑名单'''
    ret = dict()
    ret["NameTotal"]=0
    ret["Names"]=list()
    ret["MsgType"]="BlackNameUpdateAck"
    ret["ErrorCode"]=0
    ret["ErrorDescription"]=None
    return ret

@PrintBegEndTime
def WhiteNameUpdateFun():
    '''发送白名单'''
    ret=dict()
    ret["NameTotal"]=0
    ret["Names"]=list()
    ret["MsgType"]="WhiteNameUpdateAck"
    ret["ErrorCode"]=0
    ret["ErrorDescription"]=None
    return ret

@PrintBegEndTime
def HealthCheckReqFun():
    '''处理心跳请求'''
    return {"MsgType":"HealthCheckReqAck",} 


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello MIE")
    
    #@PrintBegEndTime
    def post(self):
        body=None
        response=None
        try:
            body = json.loads(self.request.body)
            msgtype = body["MsgType"]
            log.info("MsgType="+msgtype)
            if msgtype == "UrlRecordPost":
                response=UrlRecordPostFun(self.request.remote_ip,body["Records"])
            elif msgtype == "WhiteNameUpdate":
                response=WhiteNameUpdateFun()
            elif msgtype == "BlackNameUpdate":
                response=BlackNameUpdateFun()
            elif msgtype == "CachedContentUpdate":
                mode = body["Mode"]
                add_data = '"TransactionID":'+str(body["TransactionID"])+','\
                        +'"TimeStamp":"' \
                        +time.strftime( ISOTIMEFORMAT, time.localtime())\
                        +'"}'
                final_data = ""
                global records_mode0
                global records_mode0_default
                global records_mode1
                global records_mode1_default
                mutex_mit.acquire()
                print "*****",mit_table.setdefault(self.request.remote_ip,0),id(records_mode0)
                if mit_table.setdefault(self.request.remote_ip,0) == id(records_mode0):
                    if mode == 0:
                        final_data = records_mode0_default+add_data
                    else:
                        final_data = records_mode1_default+add_data
                    print 1
                else:
                    if mode==0:
                        final_data = records_mode0+add_data
                    else:
                        final_data = records_mode1+add_data
                    mit_table[self.request.remote_ip]=id(records_mode0)
                    print 2,id(records_mode0)
                mutex_mit.release()
                self.write(final_data)
                print final_data
                return
            elif msgtype == "HealthCheckReq":
                response=HealthCheckReqFun()
            else:
                response = {"MsgType":msgtype,"ErrorDescription":"unknow msgtype","ErrorCode":0}

            response["TimeStamp"]=time.strftime( ISOTIMEFORMAT, time.localtime())
            response["TransactionID"]=body["TransactionID"]
            self.write(json.dumps(response,indent=4,separators=(',',':')))
        except Exception as e:
            log.error("处理消息出错,msgtype=%s,msgbody=%r,exception occured:%s",msgtype,request.body,e)
                
        
application = tornado.web.Application([
    (r"/",MainHandler),
    ])


threadlist = list()



if __name__ == "__main__":
    CalcHostListFun()
    
    for i in xrange(1):
        th = threading.Thread(target = DesposeUrlRecordThread,name="url post dispose")
        th.setDaemon(True)
        th.start()
        threadlist.append(th)

    for i in xrange(UpdateThreadCount):
        th = threading.Thread(target = CacheUpdateThread,name="content download")
        th.setDaemon(True)
        th.start()
        threadlist.append(th)
        
    if True:
        application.listen(ListenPort)   #单进程模式
    else:
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.bind(ListenPort)
        http_server.start(num_processes=0)
    tornado.ioloop.IOLoop.instance().start()
    
    
