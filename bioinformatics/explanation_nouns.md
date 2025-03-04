# 名词解释： 
### 进化相关知识
**cross-alignment**:交叉比对，将一个物种的基因组序列和另一个物种的基因组序列比对，揭示两个物种的遗传相似性、差异性以及可能的进化关系。\
**profile**：通常指的是蛋白质的序列档案（Protein profiles），其中包含了蛋白质的序列信息及其进化信息（描述了每个位置各种氨基酸残基出现的概率分布，这些信息通过MSA获得）的数据结构。\
**singletons**：在蛋白质聚类分析中，如果某个蛋白质在所有物种或样本中被检测到一次，没有和其他物种的蛋白形成聚类，那么称该蛋白为“singletons”。这意味着该蛋白质在研究样本中独一无二，不与其他蛋白质共享相似的序列或结构特征。\
**纯化选择**（Purifying selection）：也称为负选择或稳定性选择，该作用下对生物体功能至关重要的基因或蛋白质会保持稳定，即有助于维持基因或蛋白质功能，减少有害突变的积累。\
**多样化选择**（Diversifying selection）：又称为正选择，该作用下会促进那些增加生物体适应性的遗传变异的传播，这种选择可以导致基因和蛋白质序列的快速进化，因为有利于适应环境的变异被自然选择所青睐。
**染色体的平均固定指数**（Average Fixation Index，通常用 FST 表示）：是群体遗传学中的一个重要指标，用于衡量不同群体之间遗传分化程度的大小，反映了基因在不同群体中的固定程度。


### 抗菌肽相关知识
**参考文章**：https://doi.org/10.1111/j.1469-0691.2011.03570.x

多重耐药细菌（multi-drug resistance bacteria,MDRO）: 指对对**至少三种**或更多**抗菌药物类别**中的一种药物表现出**获得性不敏感**的细菌。\
广泛耐药细菌（extensively drug-resistant bacteria,XDR）：对除**两种或更少抗菌药物类别**之外的所有类别中至少一种药物**不敏感**（即细菌分离株仅对一种或两种类别敏感）。\
泛耐药细菌（pandrug-resistant bacteria,PDR）：对**所有抗菌药物类别**中的所有药物均不敏感。\
**常见的抗菌药物类别**如下所示：\
eg.Criteria for defining MDR, XDR and PDR in S. aureus
| Antimicrobial category | Antimicrobial agent | Results of antimicrobial susceptibility testing (S or NS) |
| :----: | :----: | :----: | 
| Aminoglycosides | Gentamicin | |
| Ansamycins | Rifampin/rifampicin | |
| Anti-MRSA cephalosporins | Ceftaroline | |
| Anti-staphylococcal β-lactams (or cephamycins) | Oxacillin (or cefoxitin)a | |
| Fluoroquinolones | Ciprofloxacin | |
|                  | Moxifloxacin | |
| Folate pathway inhibitors | Trimethoprim-sulphamethoxazole | |
| Fucidanes | Fusidic acid | |
| Glycopeptides | Vancomycin | |
|               | Teicoplanin | |
|               | Telavancin | |
| Glycylcyclines | Tigecycline | |	
| Lincosamides | Clindamycin | |
| Lipopeptides | Daptomycin | |
| Macrolides | Erythromycin	| |
| Oxazolidinones | Linezolid | |	
| Phenicols | Chloramphenicol	| |
| Phosphonic acids | Fosfomycin | |	
| Streptogramins | Quinupristin-dalfopristin | |
| Tetracyclines | Tetracycline | |
|               | Doxycycline	| |
|               | Minocycline	| |

**抗菌机制**包括：药物作用靶位改变、产生抗菌药物灭活酶（如氨基糖苷修饰酶）、药物到达作用靶位量减小（外膜孔蛋白通透性下降）等。

### 生物信息学相关知识
**基因组组装质量良好的评估因素**：基因组的完整性、污染度。且基因组的单拷贝基因的多拷贝占比应尽可能接近0%，即绝大多数单拷贝基因的拷贝数应该为1。\
结合**Tetra (四核苷酸频率)和t-SNE**的分析过程通常如下:
  1. 四核苷酸频率的计算:从一组基因组序列中提取四核苷酸频率特征,每个基因组可以被表示为一个具有不同四核苷酸频率的向量。
  2. 高维数据矩阵构建：只要基因组集数据够大，就可以构建一个高维特征向量。
  3. t-SNE降维：通过 t-SNE 算法，将这些高维特征向量映射到二维或三维空间中。t-SNE 会尽量保持基因组之间的相似性，将相似的基因组聚集在一起，而不同的基因组则分开。
  4. 可视化
