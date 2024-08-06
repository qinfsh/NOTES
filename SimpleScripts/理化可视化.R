library(openxlsx)
library(ggplot2)
HS_data<-read.xlsx("prgr.xlsx",sheet = 1)
HS_data1<-read.xlsx("prgr.xlsx",sheet = 2)


HS_data$group<-""
HS_data[substr(HS_data$样品名称,1,2)=="sp" ,]$group<-"sp"
HS_data[substr(HS_data$样品名称,1,2)=="24" ,]$group<-"24"

HS_data1$group<-""
HS_data1[substr(HS_data1$Name,1,2)=="sp" ,]$group<-"sp"
HS_data1[substr(HS_data1$Name,1,2)=="24" ,]$group<-"24"



p1<-ggplot(HS_data,aes(x=样品名称,y=`结果(NPOC)`,fill=group))+geom_point()+geom_boxplot()+
  ggtitle("A")+
  labs(x="",y = "NPOC (ppm)")+theme_bw(base_size = 14)+
  theme(panel.grid = element_blank(),#去除坐标轴中的网格线
        plot.title = element_text(hjust = -0.1),#hjust = 0表示左对齐标题
        legend.position = "none")+ #隐藏按分类变量生成的颜色示例（通常显示在图例中）
  facet_wrap(~group, scales = "free_x") #scales参数有free,free_x,free_y——x/y轴是否共享
p1  
p2<-ggplot(HS_data,aes(x=样品名称,y=`结果(TN)`,fill=group))+geom_point()+geom_boxplot()+
  ggtitle("B")+
  labs(x="",y = "TN (ppm)")+theme_bw(base_size = 14)+
  theme(panel.grid = element_blank(),
        plot.title = element_text(hjust = -0.1),
        legend.position = "none")+ 
  facet_wrap(~group, scales = "free_x") #scales参数有free,free_x,free_y——x/y轴是否共享
p2

p3<-ggplot(HS_data1,aes(x=Name,y=HS_data2$Amount_Cl,fill=group))+geom_point()+geom_boxplot()+
  ggtitle("C")+
  labs(x="",y = "Cl (ppm)")+theme_bw(base_size = 14)+
  theme(panel.grid = element_blank(),
        plot.title = element_text(hjust = -0.1),
        legend.position = "none")+
  facet_wrap(~group, scales = "free_x") #scales参数有free,free_x,free_y——x/y轴是否共享
p3

p4<-ggplot(HS_data1,aes(x=HS_data2$Name,y=HS_data2$Amount_SO4,fill=group))+geom_point()+geom_boxplot()+
  ggtitle("D")+
  labs(x="",y = "SO4 (ppm)")+theme_bw(base_size = 14)+
  theme(panel.grid = element_blank(),
        plot.title = element_text(hjust = -0.1),
        legend.position = "none")+
  facet_wrap(~group, scales = "free_x") #scales参数有free,free_x,free_y——x/y轴是否共享
p4


####添加显著性检验结果
#install.packages("ggpubr")
library(ggpubr)



##合并两个理化的图
library(gridExtra)
# 使用grid.arrange()合并图形
#widths参数用于设置图形的宽度比例，heights参数用于设置图形的高度比例
#如grid.arrange(plot1, plot2,widths = c(1, 2), heights = c(1, 1))
grid.arrange(p1, p3,p2,p4, ncol = 2)  # 并排排列两个图形

