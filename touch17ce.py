# coding=gbk
import httplib2
import os
import json
import sys
import time
import re
import datetime
import logging





# setup logger
def setupLogger(name, output):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S')

    fileHandler = logging.FileHandler(output + name + '.log')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    fileHandler = logging.StreamHandler()
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    return logger


def postData(http, url, data, logger):
    formData = [ (x[0]+"=" + x[1]) for x in data ]
    body = "&".join(formData)

    logger.debug("postData '" + body + "' to " + url)
    (resp, content) = http.request(url, "POST",
                                   body=body,
                                   headers={
                                       "Content-type" : "application/x-www-form-urlencoded",
                                       "Origin" : "http://www.17ce.com/",
                                       "Referer" : "http://www.17ce.com/"
                                   })
    if resp.status != 200:
        logger.error ("post data failed: " + resp.status)
        return None

    content = content.decode()
    logger.debug("received data: " + content)
    content = re.sub('([{,])(\\s*\\d+\\s*):', '\\1"\\2":', content)
    return json.loads(content)

def makeCsvLine(*args):
    items = [str(x) for x in args]
    return ",".join(items) + "\n"
    
def downloadData(http, url, output):
    rt = '1'
    nocache = '0'
    logger = setupLogger(url, output)
    data = [
        ('',''),
        ('url',  url),
        ('curl',''),
        ('rt', rt),
        ('nocache',nocache),
        ('host', ''),
        ('referer',''),
        ('cookie',''),
        ('agent',''),
        ('speed',''),
        ('postfield',''),
        ('verify', url + '18371' + nocache + rt + '3654'),
        ('pingcount',''),
        ('pingsize',''),
        ('area[]','0'),
        ('area[]','1'),
        ('area[]','2'),
        ('area[]','3'),
        ('',''),
        ('isp[]','0'),
        ('isp[]','1'),
        ('isp[]','2'),
        ('isp[]','6'),
        ('isp[]','7'),
        ('isp[]','8'),
        ('isp[]','4'),
        ('','')
    ]

    reqResult = postData(http, "http://www.17ce.com/site/http", data, logger)

    tid = reqResult['tid']
    if not tid:
        logger.debug("fail to create task")
        return 1

    logger.debug('tid=' + tid)

    f = open(output + url + '.csv','a')

    retry = 30
    while retry > 0:
        reqResult = postData(http, "http://www.17ce.com/site/ajaxfresh", [("tid" , tid) , ("num" ,"70"), ("ajax_over", "0")], logger)

        if not reqResult['speed_backdata']:
            time.sleep(5)
            retry = retry - 1
            continue

        for k in reqResult['speed_backdata']:
            line = makeCsvLine(datetime.datetime.now()
                    , k['ConnectTime']
                    ,k['FileSize']
                    ,k['IP']
                    ,k['NsLookup']
                    ,k['TotalTime']
                    ,k['downtime']
                    ,k['isp']
                    ,k['SrcIP']['srcip']
                    ,k['SrcIP']['ipfrom']
                    ,k['name']
                    ,k['realsize']
                    ,k['sid']
                    ,k['speed']
                    ,str(k['view']))
            f.write(line)
        logger.debug("done")
        break

    f.close()  # you can omit in most cases as the destructor will call it
    return 0

if len(sys.argv) < 3:
    print ("Usage: " + sys.argv[0] + " host output")
    sys.exit(0)

url = sys.argv[1]
output = sys.argv[2]
if not output.endswith("\\"):
    output = output + "\\"

if not os.path.exists(output):
    os.makedirs(output)

ret = downloadData(httplib2.Http(".cache"), url, output)
sys.exit(ret)
