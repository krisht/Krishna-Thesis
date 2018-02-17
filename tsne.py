#!/usr/bin/env python

import numpy as np
import matplotlib

import glob
import os
import sys

matplotlib.use('Agg')
import matplotlib.pyplot as plt
font = {'family' : 'FreeSerif',
        'size'   : 18}
plt.rc('text', usetex=True)
matplotlib.rc('font', **font)
plt.rcParams['legend.handlelength'] = 1
plt.rcParams['legend.handleheight'] = 1.125
plt.rcParams['legend.numpoints'] = 1

def plot_embedding(X, y,  num_to_label, file_name, title="t-SNE Embedding of DCNN Clustering Network"):
    x_min, x_max = np.min(X, 0), np.max(X, 0)
    X = (X - x_min) / (x_max - x_min)
    cmap = plt.get_cmap('gist_rainbow')
    color_map = [cmap(1.*i/6) for i in range(6)]
    legend_entry = []
    for ii, c in enumerate(color_map):
        legend_entry.append(matplotlib.patches.Patch(color=c, label=num_to_label[ii]))
 
 
    plt.figure()
    plt.scatter(X[:,0], X[:, 1], marker='o', c=y, cmap=matplotlib.colors.ListedColormap(color_map), s=40, edgecolor='black',linewidth='0.6')
    plt.legend(handles=legend_entry, loc=8,  bbox_to_anchor=(0.5, -0.3), ncol=3)
    ax = plt.gca()
    ax.yaxis.set_major_formatter(matplotlib.ticker.NullFormatter())
    ax.xaxis.set_major_formatter(matplotlib.ticker.NullFormatter())    
    ax.set_aspect('auto')
    #plt.title(title)
    plt.savefig(file_name, bbox_inches='tight')
    #plt.show()
    plt.close()


num_to_class = dict()
 
num_to_class[0] = 'BCKG'
num_to_class[1] = 'ARTF'
num_to_class[2] = 'EYBL'
num_to_class[3] = 'GPED'
num_to_class[4] = 'SPSW'
num_to_class[5] = 'PLED'


if __name__ == '__main__':
	folder = sys.argv[1]
	# files = [os.path.join(folder, f) for f in os.listdir(folder) if '.npz' in f]

	# for f in files:
	# 	a = np.load(f)
	# 	X = a['arr_0']
	# 	labels = a['arr_1']
	# 	file_name = f.replace('.npz', '_2.pdf')
	# 	plot_embedding(X, labels, num_to_class, file_name)
	l = []
	for dirpath, dirs, files in os.walk("."):
		for f in files:
			if '.npz' in f and 'SNE' in f:
				l = l + [os.path.join(dirpath, f)]

	ii = 0
	for ii, f in enumerate(l):
		a = np.load(f)
		X = a['arr_0']
		labels = a['arr_1']
		file_name = f.replace('.npz', '.pdf')
		plot_embedding(X, labels, num_to_class, file_name)
		sys.stdout.write("\r{0}".format((float(ii)/len(l))*100))
		sys.stdout.flush()