"""This script runs forward search for all the 'continuous'(not including
'interval', 'categorical', 'binary', 'ordinal') features.                                    
"""

print __doc__

import pickle
import numpy as np
from time import time
from sklearn.cluster import KMeans
from sklearn.preprocessing import scale
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
from python.COPDGene.utils.sample_wr import sample_wr
import copy

############################# Parameter Setting ##############################
# The number of clusters in KMeans
K = 4
##############################################################################

t0 = time()
# Load training set
file_data_train = open("/home/changyale/dataset/COPDGene/data_train.pkl","rb")
info_con,info_dis,gold = pickle.load(file_data_train)
file_data_train.close()
data_con, features_name_con, features_type_con = info_con

# Choose only 'continuous' features for forward search
data_con_use = []
features_name_use = []
for j in range(len(features_type_con)):
    if features_type_con[j] == 'continuous':
        data_con_use.append(data_con[:,j])
        features_name_use.append(features_name_con[j])
data_con_use = np.array(data_con_use).T

# Prepare reference dataset for continuous features
# Random sample with replacement from training set to form a reference dataset
data_con_use_ref = np.zeros((data_con_use.shape[0],data_con_use.shape[1]))
for j in range(data_con_use.shape[1]):
    tp_index = sample_wr(range(data_con_use_ref.shape[0]),\
            data_con_use_ref.shape[0])
    for i in range(len(tp_index)):
        data_con_use_ref[i,j] = data_con_use[tp_index[i],j]

t1 = time()
print(["Preparing data takes "+str(t1-t0)+" seconds"])

# Forward search for continuous features
# Normalization of the continuous dataset
data = scale(data_con_use)
n_instances, n_features = data.shape

data_ref = scale(data_con_use_ref)

# Start with 'FEV1pp_utah' and 'FEV1_FVC_utah'
bfs = [35,37]
score_best = [0]*n_features
features_add = []

tmp = []
for i in range(len(bfs)):
    tmp = tmp+[bfs[i]]
    data_use = data[:,tmp]
    estimator_1 = KMeans(init='random',n_clusters=K,n_init=10,n_jobs=-1)
    estimator_1.fit(data_use)
    data_use_labels = estimator_1.labels_
    
    data_ref_use = data_ref[:,tmp]
    estimator_2 = KMeans(init='random',n_clusters=K,n_init=10,n_jobs=-1)
    estimator_2.fit(data_ref_use)
    data_ref_use_labels = estimator_2.labels_
    
    score_1 = silhouette_score(data_use,data_use_labels,\
            metric='euclidean')
    score_2 = silhouette_score(data_ref_use,data_ref_use_labels,\
            metric='euclidean')
    score_best[i] = score_1-score_2
    features_add.append(bfs[i])

# Silhouette score for original dataset and reference dataset using the same
# set of features
score = range(n_features)
fs = range(n_features)

while(len(bfs)<n_features):
    t0 = time()
    for i in range(n_features):
        t1 = time()
        if i in set(bfs):
            score[i] = 0
            fs[i] = bfs
        else:
            fs[i] = bfs+[i]
            
            # Candidate from original dataset
            data_use = data[:,fs[i]]
            estimator_1 = KMeans(init='random',n_clusters=K,n_init=10,n_jobs=-1)
            estimator_1.fit(data_use)
            data_use_labels = estimator_1.labels_
            
            # Candiate from reference dataset
            data_ref_use = data_ref[:,fs[i]]
            estimator_2 = KMeans(init='random',n_clusters=K,n_init=10,n_jobs=-1)
            estimator_2.fit(data_ref_use)
            data_ref_use_labels = estimator_2.labels_
            
            # Compute the gap statistic
            score_1 = silhouette_score(data_use,data_use_labels,\
                    metric='euclidean')
            score_2 = silhouette_score(data_ref_use,data_ref_use_labels,\
                    metric='euclidean')
            score[i] = score_1-score_2
            t2 = time()
            print([i,t2-t1])
    for i in range(n_features):
        if score[i] == max(score):
            score_best[len(bfs)] = max(score)
            features_add.append(i)
            bfs = fs[i]
            break
    t3 = time()
    print([score_best[len(bfs)-1],features_add,"RunningTime(s): ",(t3-t0)])

