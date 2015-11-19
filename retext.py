import re

textstr = "http://220.181.154.15/youku/777/6973A2989B932823EEF40247DA/0300020100563ABD71FD2B0230E416F0CBC1F3-EE10-EB22-744F-6010E6849F8C.flv?nk=314613209945_24111796410&ns=2880720_2720180&special=true"
#textstr = "http://220.181.154.15/youku/777/6973A2989B932823EEF40247DA/0300020100563ABD71FD2B0230E416F0CBC1F3-EE10-EB22-744F-6010E6849F8C.flv"
#textstr = 'http://127.0.0.1:80/302_mark/p.l.ykimg.com/ykp2pdata?json=%7B%22ac%22:%22110000%22,%22sid%22:%22644772697605310bff2aa%22,%22time%22:1447727005274,%22vid%22:%22347094008%22,%22ct%22:%2291%22,%22data%22:%7B%22index%22:0,%22addErrorData%22:%7B%22useTime%22:30520,%22metaUrl%22:%22http://106.38.249.75/youku/6572D8744C6407B19EF2B2AB3/0300080100564A782EF2760230E416C173656D-E6E7-175B-B61C-E406C4964545.mp4%22,%22processType%22:%22meta%22%7D%7D,%22errorType%22:%22datamgr_metadata_timeout_error%22,%22logType%22:%22fatal%22,%22vt%22:%22mp4%22,%22vs%22:%2210-14-10-56%22,%22acc%22:3,%22dc%22:%2223724%22,%22cfg%22:%22player_yk_601%22%7D'
#pattern = re.compile(r"(\w+://)?([^/]+)(/youku/)(.+/)*([^\?]+)(\?([^&=]+=[^&]+)((&[^=]+=[^&]+)*))?")
pattern = re.compile(r"(\w+://)?([^/]+)(/youku/)(.+/)*([^.?/]+\.(mp4|flv)(?=\?|$))(\?([^&=]+=[^&]+)((&[^=]+=[^&]+)*))?")
"("

match = pattern.match(textstr)

if match:
    for i,x in enumerate(match.groups(),1):
        print i,x


print match.expand(r'\1*\3*/\5')
print match.expand(r'\1\2\3\4\5')
#print match.expand(r'\7')
#print match.expand(r'\8')
a = match.expand(r'\4')
tmppattern = re.compile(r"[^/]+/")
print tmppattern.sub("*/",a)




CacheIp = r'127.0.0.1:80/302_mark/'
pattern_star = re.compile(r"[^/]+/")
pattern_youku = re.compile(r"(\w+://)?([^/]+)(/youku/)(.+/)*([^.?/]+\.(mp4|flv)(?=\?))(\?([^&=]+=[^&]+)((&[^=]+=[^&]+)*))?")
filter_set_youku = {'nk','ns','start'}
def UrlTrans(url):
    url_MIE=''
    url_cache=''
    match=pattern_youku.match(url)
    if match:
        url_MIE=match.expand(r'\1*\3'+pattern_star.sub(r'*/',match.expand(r'\4'))+r'\5')
        url_cache=match.expand(r'\g<1>'+CacheIp+r'\2\3\4\5')
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
    return url,url

print '-----------------------------------------------------'
print UrlTrans(textstr)







text = "127.0.0.1/baidu.com"

pattern_default = re.compile(r"(\w+://)?(.+)")

match = pattern_default.match(text)

if match.group(1):
    url_cache=match.group(1)
else:
    url_cache=""
url_cache+=CacheIp
url_cache+=match.group(2)

print url_cache


"http://iosapps.itunes.apple.com/apple-assets-us-std-000001/Purple69/v4/f6/3a/39/f63a39ad-76ae-77d4-9d2d-a21664cefc89/pre-thinned6390962509010654325.thinned.signed.dpkg.ipa?accessKey=1447331811_8321268509499498333_ngbz9y0%2FANW9WMZOrCcr4%2BRD4tzEwCLWyiQBtTOt%2FdmTjo1Sv4HRW%2BaTCJjSe3Z6T7V4FV%2BqIL5qgbOKDUxbWGcL2v5Fu1w3kU3KcuYcKtLFKIrO1dj43A65z%2BHKBVQ5nPO6ly0JAQAswWhsKOIIMABhZO5%2FpQMvS%2Bel%2FhZdYdSJaddPBYnudLeYYG0OnF6sKol2cLJU6sCMdoF%2BSGEICby75t9fNg7i6caPaPISuWs%3D"



