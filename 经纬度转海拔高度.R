setwd("D:\\schoolData\\data\\Sci_research_projects\\PTPE\\learning")
library(openxlsx)
data<-read.xlsx("青藏高原多圈层宏基因组样本待整理信息-2024.08.02.xlsx")

##安装Elread.xlsx()##安装Elevatr包
install.packages("elevatr")
library(elevatr)
library(sf)

#将度分秒（DMS）格式的经纬度转换为十进制度数


dms_to_decimal <- function(dms_string) {
    contains_degree <- logical(length(dms_string))
    dms_strings<-rep("",length(dms_string))
    for (i in seq_along(dms_string)){
      contains_degree[i] <- grepl("°", dms_string[i])
      if(contains_degree[i]){
        # 使用正则表达式分割度分秒字符串
        parts <- as.numeric(unlist(strsplit(dms_string[i], "°|\'|\"")))
        
        # 计算十进制度数
        if (is.na(parts[2])){
            decimal_degrees<-parts[1]
        }else{
          if (is.na(parts[3])){
            decimal_degrees <-parts[1] + parts[2] / 60
          }
          else{
            decimal_degrees <-parts[1] + parts[2] / 60 + parts[3] / 3600
          }
        }

        #返回结果
        dms_strings[i]<-decimal_degrees
        }
      else{
        dms_strings[i]<-dms_string[i]}
    }
    return(dms_strings)
}
  
#经纬度信息
#读取时发现经纬度两列中的单引号和双引号的字体和编码与本机不一致
##在excel中直接修改替换

# 正确创建点坐标矩阵
LongLat_data<-data.frame(x=round((as.numeric(dms_to_decimal(data$经度))),2),y=round(as.numeric(dms_to_decimal(data$纬度)),2))
#
#unique(is.na(LongLat_data$x))
#unique(is.na(LongLat_data$y))
#LongLat_data<-LongLat_data[!is.na(LongLat_data$x),]
#LongLat_data<-LongLat_data[!is.na(LongLat_data$y),]

ll_prj <- 4326
mts_sf <- st_as_sf(x =LongLat_data, coords = c("x", "y"), crs = ll_prj)

#使用了R语言中的terra包来处理空间数据，具体来说，是创建和操作数字高程模型（DEM）
#Empty Raster
library(terra)
mts_raster <- rast(mts_sf, nrow = 5, ncol = 5)
# Raster with cells for each location
mts_raster_loc <- terra::rasterize(mts_sf, rast(mts_sf, nrow = 5, ncol = 5))
result<-get_elev_point(locations = LongLat_data, prj = ll_prj, src = "aws")
#可以从多个网络服务可以提供栅格高程数据，这些服务允许用户访问地形的数字表示形式。
result1<-get_elev_point(locations = LongLat_data, prj = ll_prj)
high_data<-cbind(LongLat_data,result$elevation)
names(high_data)<-c("经度","纬度","海拔")
unique(is.na(high_data$海拔))
write.xlsx(high_data,"海拔信息.xlsx")
