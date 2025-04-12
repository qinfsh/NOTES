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
    # Description
    Id = []
    accession = []

    # 预定义的变量列表
    final_var = ["BioSample","Sample_name","SRA_number","organism","Id","accession"]
    count = 0
    is_Attributes = "no"

    # 使用字典来存储动态变量的值
    dynamic_vars = {
        "BioSample": BioSample,
        "Sample_name": Sample_name,
        "SRA_number": SRA_number,
        "organism": organism,
        "Id": Id,
        "accession": accession
    }

    with open(path+filename,"r",encoding="utf-8") as file:
        content = file.readline()
        #在读取的时候要注意该方式的读取将换行符也读取到content中
        content = content.rstrip('\n')  # 去除行尾的换行符
        while content:
            content = content.rstrip('\n')  # 去除行尾的换行符
            if "Identifiers" in content:
                count += 1 
                is_Attributes = "no"
                identify = content[13:].split(";")
                for data in identify:
                    if "BioSample" in data:
                        BioSample.append(data[11:])
                    elif "Sample name" in data:
                        Sample_name.append(data[14:])
                    elif "SRA" in data:
                        SRA_number.append(data[6:])
            elif "Organism" in content:
                organism.append(content[10:])
            elif "Attributes" in content:
                is_Attributes = "yes"
            elif "Description" in content:
                is_Attributes = "no"
            elif "ID:" in content:
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    Id.append(re.findall(r'"(.*?)"',content)[0])
            elif "Accession" in content:
                accession.append(content[11:24])

            # 进行下一个判断语句，将Attributes中的所有信息保存
            if is_Attributes == "yes":
                # 使用正则表达式提取""中的内容;re.search返回第一个匹配值；re.findall返回一个列表
                if len(re.findall(r'"(.*?)"',content))!=0 :
                    new_value = re.findall(r'"(.*?)"',content)[0]
                    pattern = r'/(?=[^/]+=)([^=]+)'
                    var = re.findall(pattern, content)
                    if not var:
                        print(f"Warning: No variable found in content: {content}")
                    else:
                        var = var[0]
                        var = re.sub(r' +', '_', var)
                        if var in final_var:
                            # 如果这个列表存在，便将值添加进去
                            dynamic_vars[var].append(new_value)
                        else:
                            # 列表不存在
                            # 创建一个包含 count 个空列表的结构
                            final_var.append(var)
                            if count == 1:
                                dynamic_vars[var] = []
                            else :
                                dynamic_vars[var] = [""] * count
                                dynamic_vars[var][-1] = new_value
            # 填充所有列表，确保长度一致
            for var_name in final_var :
                fill_list(dynamic_vars[var_name],count,"")

            content = file.readline()
        results = []
        for i in range(count):
            result = []
            for var_name in final_var:
                result.append(dynamic_vars[var_name][i])
            results.append(result)
        
        #列表是多维的，可以将其转换为 DataFrame。
        results = pd.DataFrame(results,columns=final_var)
        return results
 

path = "D:\\schoolData\\data\\Sci_research_projects\\PTPE\\PRGR_hot_spring\\Global_hotspring_metagenome\\"
file1 = "Hs_biosample_result.txt"
file2 = "Hv_biosample_result.txt"
hot_spring_data = find_metadata(path,file1)
# 将 "N/A" 替换为 ""
hot_spring_data = hot_spring_data.replace('N/A', "")
Hydrothermal_vent_data = find_metadata(path,file2)
# 将 "N/A" 替换为 ""
Hydrothermal_vent_data = Hydrothermal_vent_data.replace('N/A', "")

#使用pandas包中的concat()函数按行合并，即将第二个数据框追加到第一个数据框的下方。
data = pd.concat([hot_spring_data,Hydrothermal_vent_data],ignore_index=True) ##按列合并将ignore_index=True换成axis=1
#使用pandas写入文件
# 运行结束可以把不重要的列删除
data.to_csv(path+"hot_spring_metadata.csv", index=False)
