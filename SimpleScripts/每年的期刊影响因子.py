import requests
import json
import pandas as pd

# 发送GET请求到API
response = requests.get("https://medcite.cn/api/openjournal/findJournal?current=1&size=1000000")
#response = requests.get('https://www.pubmed.pro/api/openjournal/findJournal?name=&current=1&size=100000')
# 解析JSON响应
data = response.json()
journal_data = data["data"]
# data和journal_data现在是一个包含API返回数据的Python字典

#也可以选择先下载json文件后在进行提取数据
"""

# 假设你有一个名为data.json的文件
filename = '2024年ImpactFactor.json'

# 以读取模式打开文件
with open(filename, 'r', encoding='utf-8') as file:
    # 加载并解析JSON数据
    data = json.load(file)
    journal_data = data["data"]
print(journal_data.keys())
"""
##初始化各种变量列表
id = []
issn = []
name = []
ifactor = []
section = []
homePage = []
publishGuide = []
focus = []
domainClass = []
secondDomainClass = []
description = []
sectionTwo = []
isWarning = []
chineseRate = []
publishTotal = []

count = 0
results = []

##遍历网站返回的journal_data字典数据
for journal in journal_data["object"]:
    id.append(journal['id'])
    issn.append(journal['issn'])
    name.append(journal['name'])
    ifactor.append(journal['ifactor'])
    section.append(journal['section'])
    homePage.append(journal['homePage'])
    publishGuide.append(journal['publishGuide'])
    focus.append(journal['focus'])
    domainClass.append(journal['domainClass'])
    secondDomainClass.append(journal['secondDomainClass'])
    description.append(journal['description'])
    sectionTwo.append(journal['sectionTwo'])
    isWarning.append(journal['isWarning'])
    chineseRate.append(journal['chineseRate'])
    publishTotal.append(journal['publishTotal'])
    count = count + 1

for i in range(len(id)):
    results.append([id[i],issn[i],name[i],ifactor[i],section[i],homePage[i],publishGuide[i],focus[i],domainClass[i],secondDomainClass[i],description[i],sectionTwo[i],isWarning[i],chineseRate[i],publishTotal[i]])
#列表是多维的，可以将其转换为 DataFrame。
results = pd.DataFrame(results,columns=["id","issn","name","ifactor","section","homePage","publishGuide","focus","domainClass","secondDomainClass","description","sectionTwo","isWarning","chineseRate","publishTotal"])

#使用pandas写入文件

results.to_excel("2024年影响因子.xlsx", index=False)
