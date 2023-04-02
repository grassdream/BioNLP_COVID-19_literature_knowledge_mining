# _*_ coding: utf-8 _*_
# @Time : 2023-04-02 15:52 
# @Author : YingHao Zhang(池塘春草梦)
# @Version：v0.1
# @File : Key_word.py
# @desc :
'''
首先读取一篇文章，将其分解成句子，句子里面包含着已经得到的实体。
用依存关系计算实体之间的距离，得到一个实体-实体-距离的无向有权图。
用PageRank给实体进行排名，取排名前10的实体。
'''

import time

start_time = time.time()
import sys
import pandas as pd
import numpy as np
from subject_verb_object_extract import findSVOs, nlp
import networkx as nx
import matplotlib.pyplot as plt
import os

# %%
filepath = "D:/000大三下/BioNLP/single_paper/"
output_dir = "D:/000大三下/BioNLP/result/"
# filename = 'xx48478'
# filename = sys.argv[1]

files = os.listdir(filepath)
i=1
for file in files:
    print(file)
    print(i/len(files))
    filename = file
    try:
        sample = open(filepath + filename)  # 本次处理的文章

        line = sample.readlines()  # 得到每一行为一个元素，构成一个列表，存储在line变量里
        line.pop(0)
        title = line[0]  # 标题
        article = line[1]  # 文章内容
        title = title.split('|')[2]  # 去掉前缀
        title = title.split('\n')[0]  # 去掉换行符
        article = article.split('|')[2]  # 去掉前缀
        l_len = len(line)  # 这个文件总共的行数
        t = [title]  # 得到标题的句子
        sentence = article.split('. ')  # 用句号分割文章，构成列表，列表中的元素不含句号
        sentences = t + sentence  # 标题和文章中所有的句子拼起来，因为给出的实体位置里包含了标题
        s_len = len(sentences)  # 一共有多少个句子
        # 这个小节最终想要得到的是entity，一个列表，第一列是句子，后面对应的是句子里的实体
        j = 2
        ae_len_now = 0  # 句子结尾的长度
        entity = []  # 存放句子及其中的实体
        end = 0
        for i in range(0, s_len):
            # print(sentences[i])
            if i == 0:
                s_len_now = len(sentences[i])
                as_len_now = ae_len_now  # 句子开始的长度
            else:
                s_len_now = len(sentences[i]) + 2  # 现在遍历到的这个句子的长度，+1是加上句号的长度
                as_len_now = ae_len_now  # 句子开始的长度
            # print('我是句子开始的长度', as_len_now)
            ae_len_now = ae_len_now + s_len_now  # 句子结尾的长度
            # print('我是句子结束的长度', ae_len_now)
            entity.append([])
            # print('我是第几个句子', i)
            while j < l_len:
                # print('我是第几行实体', j)
                start = int(line[j].split('\t')[1])  # 得到第j行第2列的数字
                # print('我是实体的起始位置', start)
                end = int(line[j].split('\t')[2])  # 得到第j行第3列的数字
                # print('我是实体的终止位置', end)
                if start >= as_len_now and end <= ae_len_now:  # 这个词在开头结尾中间，说明在这个句子中
                    if entity[i] == []:
                        entity[i].append(sentences[i])  # 使第一列为句子内容
                    entity[i].append(line[j].split('\t')[3])
                    # print(line[j].split('\t')[3])
                    j = j + 1
                else:
                    break

        entity_df = pd.DataFrame(entity)  # 将记录entity的list转化为dataframe
        entity_final = entity_df.dropna(axis=0, how='all')  # 去掉整行都是nan的行，得到最终的实体数据框，也就是每一篇文章都想要的结果
        entity_final = entity_final.reset_index(drop=True)


        def calculate_distance(sentence, entity1, entity2):
            tokens = nlp(sentence)
            edges = []
            for token in tokens:
                for child in token.children:
                    # print(token.lower_)
                    # print(child.lower_)
                    edges.append(('{0}'.format(token.lower_),
                                  '{0}'.format(child.lower_)))
            G = nx.Graph(edges)
            # 下面是计算两个给定实体间的距离
            distance = nx.shortest_path_length(G, source=entity1, target=entity2)
            # print('Distance between {} and {} is {}'.format(entity1, entity2, distance))
            return distance


        mesh_network = []
        for i in range(entity_final.shape[0]):
            sentence = entity_final.iloc[i, 0]
            # print(sentence)
            for j in range(1, entity_final.shape[1] - 1):
                entity1 = entity_final.iloc[i, j]
                entity2 = entity_final.iloc[i, j + 1]
                if (entity2 != None):
                    entity1 = entity1.split()[0].lower()
                    entity2 = entity2.split()[0].lower()
                    # print(entity1)
                    # print(entity2)
                    try:
                        distance = calculate_distance(sentence, entity1, entity2)
                        mesh_network.append([entity1, entity2, distance])
                    except:
                        continue

        mesh_network = pd.DataFrame(mesh_network, columns=['source', 'target', 'weight'])
        mesh_network = mesh_network[mesh_network['weight'] > 0]
        max_min_scaler = lambda x: (np.max(x) - x)
        # mesh_network['Distance'] = mesh_network[['Distance']].apply(max_min_scaler)

        G = nx.from_pandas_edgelist(mesh_network, edge_attr="weight")

        pr = nx.pagerank(G, alpha=0.85)
        pr = pd.DataFrame.from_dict([pr]).T
        pr.columns = ['score']
        # %%
        keywords = pr.sort_values(by=['score'], ascending=False)
        if keywords.shape[0] >= 10:
            keywords_10 = pd.DataFrame(keywords.iloc[0:10].index)
            keywords_10.to_csv(output_dir + 'kw10_{}.txt'.format(filename), sep='\t', index=False, header=0)
        else:
            pass

    except:
        pass
    i+=1
end_time = time.time()
run_time = end_time - start_time
print("代码运行时间为：{}分{}秒".format(int(run_time / 60), round(run_time % 60)))
print("Done (/▽＼)")
