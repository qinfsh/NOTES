library("openxlsx")
data1<-read.xlsx("1.xlsx")
data2<-read.xlsx("2.xlsx")
#文件1.xlsx是待查文献的期刊名称
#文件2.xlsx是影响因子表“2024 最新最全影响因子（附同比）.xlsx”

data1$Source.Title<-toupper(data1$Source.Title)
data2$名字<-toupper(data2$名字)


  
  # 首先确保data1$IF列存在，并且初始化为NA
  data1$IF <- NA
  
  # 使用循环或者apply函数来匹配并赋值
  for (i in 1:nrow(data1)) {
    # 查找data2中名字列与data1中Source.Title列相匹配的行
    match_index <- which(data2$名字 == data1$Source.Title[i])
    
    # 如果找到匹配项，则将对应的2023最新IF值赋给data1$IF
    if (length(match_index) > 0) {
      data1$IF[i] <- data2$`2023最新IF`[match_index[1]]
    }
  }
write.xlsx(data1,"3.xlsx")
