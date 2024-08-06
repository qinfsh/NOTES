##学习R语言ggplot的一些心得体会  
#1.背景知识  
  
    ggplot2是R中的一个绘画包,基于Leland Wilkinson提出的“Grammar of Graphics”理念，即图形语法，其基本思路就是将图表的主体看成是数据和几何图形的视觉特征结合到一起；同时将图表看成一些简单的相互正交的特征组合而成的结果。比如，数据点(visual cue)和坐标轴(coordinates)就可以组合得到21（7*3）种不同的图形类别。  
 
<p align="center">
    <img src=https://upload-images.jianshu.io/upload_images/1183348-44711940bf1a752c.png?imageMogr2/auto-orient/strip|imageView2/2/w/538/format/webp >
</p>

#2.ggplot绘图原理  
'''
  通过组合不同的图形元素来构建图形。一些基本概念： 
      美学映射（Aesthetic Mapping）———— 将数据映射到图形的美学的属性上，如x/y轴的位置，颜色，形状，大小。
      几何对象———— 点图、线图、条形图以及箱型图等。
      刻度（Scales）———— 定义数据范围，包括轴的刻度和标签。
      坐标系统（Coordinate System）———— 笛卡尔坐标系和极坐标系。
      分面（Faceting）———— 将图形分割成多个小图形，每个小图形显示数据的一个子集，可以表示不同的分类变量。
      主题（Themes）———— 图形的整体外观，包括颜色，字体，背景。
      图层（Layers）———— ggplot2的核心原理是图层叠加。每个图层可以包含数据子集、特定的几何对象、映射和统计变换。
      统计变换（Statistical Transformations）————  用于数据的统计变换，如平滑（stat_smooth()）、密度估计（stat_density()）等

'''
