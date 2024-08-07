import re
import pandas as pd

def fill_list(lst, length, fill_value):
    while len(lst) < length:
        lst.append(fill_value)

def find_metadata(path,filename):
    """
    该脚本用于提取在NCBI的biosample数据库中宏基因组的metadata信息。
    """
    #样本信息
    #Identifiers
    BioSample = []
    Sample_name = []
    SRA_number = []
    #Organism
    organism = []
    #Attributes
    collection_time = []
    depth = []
    broad_scale_environment = []
    local_scale_environment = []
    environment = [] #全称是environmental medium
    location = [] #全称是geographic location
    latitude_and_longitude = []
    Id = []
    accession = []

    count = 0

    with open(path+filename,"r",encoding="utf-8") as file:
        content = file.readline()
        #在读取的时候要注意该方式的读取将换行符也读取到content中
        content = content.rstrip('\n')  # 去除行尾的换行符
        while content:
            if "Identifiers" in content:
                count = count + 1 
                identify = content[13:].split(";")
                for data in identify:
                    if "BioSample" in data:
                        BioSample.append(data[11:])
                    elif "Sample name" in data:
                        Sample_name.append(data[14:])
                    elif "SRA" in data:
                        SRA_number.append(data[6:])
            elif content[0:8] == "Organism":
                organism.append(content[10:])
            elif "collection date" in content:
                collection_time.append(re.findall(r'"(.*?)"',content)[0])#使用正则表达式提取""中的内容;re.search返回第一个匹配值；re.findall返回一个列表
            elif "broad-scale environmental context" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    broad_scale_environment.append(re.findall(r'"(.*?)"',content)[0])
            elif "local-scale environmental context" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    local_scale_environment.append(re.findall(r'"(.*?)"',content)[0])
            elif "environmental medium" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    environment.append(re.findall(r'"(.*?)"',content)[0])
            elif "geographic location" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    location.append(re.findall(r'"(.*?)"',content)[0])
            elif "latitude and longitude" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    latitude_and_longitude.append(re.findall(r'"(.*?)"',content)[0])
            elif "depth" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    depth.append(re.findall(r'"(.*?)"',content)[0])
            elif "Id" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    Id.append(re.findall(r'"(.*?)"',content)[0])
            elif "Accession" in content:
                accession.append(content[11:24])
                fill_list(Sample_name,count,"")
                fill_list(SRA_number,count,"")
                fill_list(organism,count,"")
                fill_list(broad_scale_environment,count,"")
                fill_list(local_scale_environment,count,"")
                fill_list(environment,count,"")
                fill_list(location,count,"")
                fill_list(latitude_and_longitude,count,"")
                fill_list(collection_time,count,"")
                fill_list(depth,count,"")
                fill_list(Id,count,"")
            content = file.readline()
        results = []
        for i in range(len(accession)):
            results.append([BioSample[i],Sample_name[i],SRA_number[i],Id[i],depth[i],organism[i],\
                            broad_scale_environment[i],local_scale_environment[i],environment[i],\
                                location[i],latitude_and_longitude[i],collection_time[i],accession[i]])
        #列表是多维的，可以将其转换为 DataFrame。
        results = pd.DataFrame(results,columns=["BioSample","Sample name","SRA number","Id","depth",\
                                                "organism","broad scale environment","local scale environment",\
                                                    "environmental medium","geographic location","latitude and longitude","collection time","accession"])
        return results
 

path = "D:\\schoolData\\data\\Sci_research_projects\\PTPE\\PRGR_hot_spring\\Global_hotspring_metagenome\\"
file1 = "Hs_biosample_result.txt"
file2 = "Hv_biosample_result.txt"
hot_spring_data = find_metadata(path,file1)
Hydrothermal_vent_data = find_metadata(path,file2)

#使用pandas包中的concat()函数按行合并，即将第二个数据框追加到第一个数据框的下方。
data = pd.concat([hot_spring_data,Hydrothermal_vent_data],ignore_index=True) ##按列合并将ignore_index=True换成axis=1
#使用pandas写入文件
data.to_excel("hot_spring_metadata.xlsx", index=False)
