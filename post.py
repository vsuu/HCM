#!/usr/bin/env python

 
import httplib
import threading
import time
import json
import datetime

theaders = {}

URL_LIST = [
    "http://220.181.154.13/youku/6772610CC664383066BC282ADE/0300020100564BBECC8AB60230E41610E48306-7B01-B6AA-657F-C99C773CBE09.flv?special=true",
    "http://v.abcd.com/travel/UK/1.mp4",
"http://img.zxcv.com/local/89.gif",
"http://img.zxcv.com/local/819.gif",
"http://img.zxcv.com/local/829.gif",
"http://img.zxcv.com/local/839.gif",
"http://img.zxcv.com/local/849.gif",
"http://img.zxcv.com/local/859.gif",
"http://img.zxcv.com/local/869.gif",
"http://img.zxcv.com/local/879.gif",
"http://img.zxcv.com/local/889.gif",
"http://img.zxcv.com/local/899.gif",
"http://img.zxcv.com/local/8109.gif",
"http://img.zxcv.com/local/892.gif",
"http://img.zxcv.com/local/893.gif",
"http://img.zxcv.com/local/894.gif",
"http://img.zxcv.com/local/895.gif",
"http://img.zxcv.com/local/896.gif",
"http://img.zxcv.com/local/897.gif",
"http://img.zxcv.com/local/898.gif",
"http://img.zxcv.com/local/899.gif",
"http://img.zxcv.com/local/8910.gif",
"http://img.zxcv.com/local/189.gif",
"http://img.zxcv.com/local/289.gif",
"http://img.zxcv.com/local/389.gif",
"http://img.zxcv.com/local/489.gif",
"http://img.zxcv.com/local/589.gif",
"http://img.zxcv.com/local/689.gif",
"http://img.zxcv.com/local/789.gif",
"http://img.zxcv.com/local/989.gif",
"http://img.zxcv.com/local/1089.gif",
"http://img.zxcv.com/local/1189.gif",
"http://img.zxcv.com/local/1289.gif",
"http://zhidao.baidu.com/question/545884527.html",
    "http://news.baidu.com/ns?cl=2&rn=20&tn=news&word=visual+studio+blend&t=1",
    "http://www.baidu.com/s?cl=3&wd=visual+studio+blend",
    "http://tieba.baidu.com/f?kw=visual+studio+blend&t=4",
    ]

URL_LIST=URL_LIST[:1]

ISOTIMEFORMAT='%Y-%m-%d %X'
import random
import string

def postfun():
    #httpClient = httplib.HTTPConnection('124.126.126.103', 8888, timeout=30)
    httpClient = httplib.HTTPConnection('localhost', 8888, timeout=30)
    while True:
        try:
            tbody = {"TransactionID": 1478,
                    "TimeStamp": "2015-11-11 09:35:02",
                    "MsgType": "UrlRecordPost",
                    "TimeFrom": "2015-11-11 09:30:00",
                    "TimeTo": "2015-11-11 09:35:00",
                    "RecordTotal": 0,
                    "Records": list()}
            for x in xrange(100):
                i = random.randrange(0,len(URL_LIST))
                tbody["RecordTotal"]+=1
                tbody["Records"].append({"serialNum":x+1,
                        "AccessTime":datetime.datetime.now().strftime(ISOTIMEFORMAT),
                         "URL":URL_LIST[i]})
                '''
            for y in xrange(100,1000):
                tbody["Records"].append({"serialNum":y+1,
                    "AccessTime":datetime.datetime.now().strftime(ISOTIMEFORMAT),
                         "URL":string.join(random.sample('zyxwvutsrqponmlkjihgfedcba!@#$%^&*_',3)).replace(' ','') })
            
            for z in xrange(1000,10000):
                tbody["Records"].append({"serialNum":z+1,
                    "AccessTime":datetime.datetime.now().strftime(ISOTIMEFORMAT),
                         "URL":string.join(random.sample('zyxwvutsrqponmlkjihgfedcba',6)).replace(' ','') })
                '''
            b=time.time()                         
            httpClient.request('POST', '/',body=json.dumps(tbody),headers=theaders)
            #response是HTTPResponse对象
            response = httpClient.getresponse()
            print response.read()
            e=time.time()-b
            print "posttime",e
            #print response.status
            #print response.reason
            #print response.read()
        except Exception as e:
            print e
        finally:
            if httpClient:
                httpClient.close()

        time.sleep(1)

def gethoturl():
    bodydata=json.dumps({"TransactionID":"1234","TimeStamp":"2015-11-11 09:34:58",
              "MsgType":"CachedContentUpdate","Mode":1
        })

    #httpClient = httplib.HTTPConnection('124.126.126.103',8888,timeout=30)
    httpClient = httplib.HTTPConnection('localhost',8888,timeout=30)
    while True:
        try:
            b=time.time()
            httpClient.request('POST','/',body=bodydata)
            response = httpClient.getresponse()
            print response.read()
            print "gethoturltime=",time.time()-b
        except Exception as e:
            print e
        finally:
            if httpClient:
                httpClient.close()
        time.sleep(5)


if __name__ == "__main__":
    th=threading.Thread(target=postfun)
    th1=threading.Thread(target=gethoturl)
    th.setDaemon(True)
    th1.setDaemon(True)
    th.start()
    th1.start()
    th.join()
    th1.join()
