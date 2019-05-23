
##  需要 python3.5及以上环境
##  安装有 requests_html 模块
##  运行环境安装有 sendmail

##  单行线程运行

from requests_html import HTMLSession
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import re
import json
import logging
import hashlib

session = HTMLSession()     #连接对象
hashm = hashlib.md5()
float_max=float("inf")
my_mail=""
sender=""
code = ""
sendname=""

# 设置日志对象
logging.basicConfig(level=logging.INFO,
                    format='<%(asctime)s >> %(filename)s[line:%(lineno)d] %(levelname)s> %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='get_prices_info.log',
                    filemode='a')
logging.basicConfig(level=logging.ERROR,
                    format='<%(asctime)s >> %(filename)s[line:%(lineno)d] %(levelname)s> %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='get_prices_error.log',
                    filemode='a')

logger = logging.getLogger("GetPrices")

# 需要监测的物品列表

jk_iterms=json.loads(open("./items","r").read())


cookie=""
user_agent=""

## 淘宝请求头
tb_cookie=""
tb_user_agent=""

#设置京东价格类型 p:折扣后的价格, tpp:plus会员价, m:原价,op:暂时不知,一般和p相同
jtype="tpp"


# 实时汇率api
cover_url=""


##################################


# 获取已发送列表
def __getSended():
    logger.info("读取已发送列表...")
    return open("./sended", "r").read().split("\n")[:-1]

# 获取页面
def __getHtml(url):
    return session.request(url=url, headers={"Cookie": cookie,"User-Agent":user_agent}, method="get")

# 获取淘宝价格json
def __getHtml1(url,headers):
    return session.request(url=url, headers=headers, method="get")

# 获取美亚的商品价格
def __amazonGet(url):
    try:
        logger.info("获取美亚数据")
        r = __getHtml(url)
        nprice = r.html.xpath("//span[@id=\"priceblock_ourprice\"]")[0].text.replace("$","")
        product=r.html.xpath("//span[@id=\"productTitle\"]")[0].text
        return (product,__coverMoney("USD",float(nprice)))
    except:
        logger.error("获取美亚数据报错 --> {}".format(url))
        return ("",float_max)

# 提取京东商品的sku
def __getSKU(url):
    return re.findall(r"\d+?\.",url)[0][:-1]

# 获取京东的商品价格
def __jdGet(url):
    try:
        global jtype
        logger.info("获取京东数据")
        sku=__getSKU(url)
        tmp_url = "https://p.3.cn/prices/mgets?type=1&area=22_1930_49324_49396&pdtk=&pduid=15537537192491296471519&pdpin=&pdbp=0&skuIds=J_{}&ext=11100000&callback=".format(sku)
        r= __getHtml(tmp_url)
        product=__getHtml(url).html.xpath("//div[@class=\"sku-name\"]")[0].text
        all_prices:dict = json.loads(r.text[1:-3])[0]
        if jtype not in all_prices.keys():
            jtype="p"
        nprice=float(all_prices[jtype])
        return (product,nprice)
    except:
        logger.error("获取京东数据报错 --> {}".format(url))
        return ("",float_max)

#获取天猫数据
def __tmailGet(url):
    try:
        logger.info("获取天猫数据")
        r = __getHtml(url)
        product = r.html.xpath("//h1")[1].text
        jurl = "https:" + re.findall(r"//mdskip\.taobao\.com/core/initItemDetail\.htm.+?\"",r.text)[0][:-1]
        headers={"cookie":tb_cookie,"referer":url,"user-agent":tb_user_agent}
        r2 = __getHtml1(jurl, headers)
        prices = re.findall(r"\"price\":\"(.+?)\"",r2.text)
        nprice=float_max
        for p in prices:
            if float(p)<nprice:
                nprice=float(p)
        return (product,nprice)
    except:
        logger.error("天猫数据获取失败! --> {}".format(url))
        return ("",float_max)

def __taobaoGet(url,flag):
    try:
        logger.info("获取淘宝数据")
        r = __getHtml(url)
        product = r.html.xpath("//h3")[0].text+" --> {} ".format(flag)
        pString = re.findall(r"propertyMemoMap: (.+?})",r.text)[0]
        pJson = json.loads(pString)
        newP={}
        for k,v in pJson.items():
            newP[v]=k
        jurl = "https:" + re.findall(r"//detailskip\.taobao\.com/service/getData/1/p1/item/detail/sib\.htm.+?\'",r.text)[0][:-1]+"&callback=onSibRequestSuccess"
        headers={"cookie":tb_cookie,"referer":url,"user-agent":tb_user_agent}
        r2 = __getHtml1(jurl, headers)
        startFlag = ";{};".format(newP[flag])
        prices=re.findall(r"\"%s\":(.+?})" %startFlag,r2.text)
        nprice = float_max
        for n in prices:
            nn=json.loads(n.replace("[","").replace("]","")).get("price")
            if nn!= None and float(nn)<nprice:
                nprice=float(nn)
        return (product,nprice)
    except Exception as e:
        logger.error(e)
        logger.error("淘宝数据获取失败! --> {}".format(url))
        return ("",float_max)

# 美元USD , 人民币CNY
def __coverMoney(fm,price):
    try:
        logger.info("转换货币")
        mult = float(__getHtml(cover_url.format("{}_CNY".format(fm))).text.split(":")[1].replace("}",""))
        return round(price*mult,2)
    except:
        logger.error("货币转换失败! --> {}-{}".format(fm, str(price)))
        return 0.00

# 检查今日是否发送过消息
def __checkHasSend(text):
    return text in sendedlist

# 消息发送后写入已发送文件
def __writeHasSended(text):
    try:
        print(text)
        with open("./sended","a") as f:
            f.write(text+"\n")
        logger.info("已发送消息写入成功! --> {}".format(text))
    except Exception as e:
        print(e)
        logger.error("已发送消息写入失败!")

# 创建邮件头
def __createToMessage(receivers,names):
    me = ""
    for i in range(0,len(receivers)):
        me += "{} <{}> ;".format(names[i], receivers[i])
    return me

# 发送邮件
def __sendEMail(text,mailTo):
    hashm.update(text.encode("utf8"))
    md5 = hashm.hexdigest()
    if __checkHasSend(md5):
        logger.info("{} ^|^ 今天已经发送过!".format(hashm.hexdigest()))
        return
    logger.info("开始发送邮件!")
    receivers=[my_mail]
    for i in mailTo.split(","):
        receivers.append(i)
    names =receivers
    message = MIMEText(text, "plain", "utf-8")
    message["From"]="{} <{}>".format(sendname,sender)
    message["To"]=__createToMessage(receivers,names)
    title = "Prices数据监控"
    message["Subject"]=Header(title,"utf-8")
    try:
        smt = smtplib.SMTP_SSL("smtp.qq.com",465)
        smt.login(sender,code)
        smt.sendmail(sender,receivers,message.as_string())
        logger.info("邮件发送成功! 接受人:{}".format(str(receivers)))
        __writeHasSended(md5)
        smt.quit()
    except Exception as e:
        logger.error(e)
        logger.error("邮件发送失败!")

################################################

# 获取相应商品的当前价格
def getNowPrice():
    product=""
    nprice=float("inf")
    for item in jk_iterms["all"]:
        url = item["url"]
        pt = item["pt"]
        if url.startswith("https://www.amazon.com"):
            product,nprice = __amazonGet(url)
        elif url.startswith("https://item.jd.com/"):
            product,nprice=__jdGet(url)
        elif url.startswith("https://detail.tmall.com"):
            product,nprice=__tmailGet(url)
        elif url.startswith("https://item.taobao.com"):
            flag = item["flag"]
            product, nprice = __taobaoGet(url,flag)
        if nprice<pt:
            __sendEMail("物品<<{}>> ({}) 的当前价格 {}CNY 小于设定价格 {}CNY 。".format(product, url, str(nprice), str(pt)),item["mailTo"])
        logger.info("物品: {}, 网址: {}, 当前价格: {}, 目标价格: {} \n".format(product,url,str(nprice),str(pt)))

#################################

if __name__ == '__main__':
    sendedlist = __getSended()
    getNowPrice()
