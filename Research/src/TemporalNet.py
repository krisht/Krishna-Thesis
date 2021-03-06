from __future__ import print_function

import datetime

curr_time = random_seed = datetime.datetime.now()
constant_seed = 42

import os
import random
import sys
import copy
import timeit
import itertools
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import tensorflow.contrib.slim as slim
from sklearn import neighbors
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import normalize
from guppy import hpy
import pdb


# random.seed(constant_seed)

# np.random.seed(constant_seed)

# tf.set_random_seed(constant_seed)

loss_mem = []

def get_loss(loss_mem):
    plt.figure(figsize=(20.0, 20.0))
    plt.plot(loss_mem, 'ro-')
    plt.xlabel("1000 Iterations")
    plt.ylabel("Average Loss in 1000 Iterations")
    plt.title("Iterations vs. Average Loss")
    plt.savefig('./%s Results/%s_convergence_plot.png' % (curr_time, curr_time), bbox_inches='tight')

def plot_confusion_matrix(cm, classes, normalize=True, cmap=plt.cm.Greys, accuracy = None, epoch=None):
    plt.figure(figsize=(5.0, 5.0))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    if normalize:
        cm = np.around(cm.astype('float') / cm.sum(axis=1)[:, np.newaxis],2)
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    print(cm)

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.savefig('./%s Results/%s_confusion_matrix_epoch%s_%.3f%%.png' % (curr_time, curr_time, epoch, accuracy), bbox_inches='tight')



class BrainNet:
	def __init__(self, input_shape=[None, 71, 125], lstm_layers=10, path_to_files='/media/krishna/My Passport/DataForUsage/labeled', l2_weight=0.05, num_output=64, num_classes=6, alpha=.5, validation_size=500, learning_rate=1e-3, batch_size=100, train_epoch=5, keep_prob=0.5, debug=True, classifier=neighbors.KNeighborsClassifier(31),restore_dir=None):
		self.bckg_num = 0
		self.artf_num = 1
		self.eybl_num = 2
		self.gped_num = 3
		self.spsw_num = 4
		self.pled_num = 5

		self.num_to_class = dict()

		self.num_to_class[0] = 'bckg'
		self.num_to_class[1] = 'artf'
		self.num_to_class[2] = 'eybl'
		self.num_to_class[3] = 'gped'
		self.num_to_class[4] = 'spsw'
		self.num_to_class[5] = 'pled'

		self.path_to_files = path_to_files

		self.count_of_triplets = dict()

		self.DEBUG = debug

		self.train_path = os.path.abspath(self.path_to_files + '/Train')
		self.val_path = os.path.abspath(self.path_to_files + '/Validation')

		self.classifier = classifier
		self.lstm_layers = lstm_layers

		path = os.path.abspath(self.path_to_files)
		self.artf = np.load(os.path.abspath(self.train_path + '/artf_files.npy'))
		self.bckg = np.load(os.path.abspath(self.train_path + '/bckg_files.npy'))
		self.spsw = np.load(os.path.abspath(self.train_path + '/spsw_files.npy'))
		self.pled = np.load(os.path.abspath(self.train_path + '/pled_files.npy'))
		self.gped = np.load(os.path.abspath(self.train_path + '/gped_files.npy'))
		self.eybl = np.load(os.path.abspath(self.train_path + '/eybl_files.npy'))

		self.artf_val = np.load(os.path.abspath(self.val_path + '/artf_files.npy'))
		self.bckg_val = np.load(os.path.abspath(self.val_path + '/bckg_files.npy'))
		self.spsw_val = np.load(os.path.abspath(self.val_path + '/spsw_files.npy'))
		self.pled_val = np.load(os.path.abspath(self.val_path + '/pled_files.npy'))
		self.gped_val = np.load(os.path.abspath(self.val_path + '/gped_files.npy'))
		self.eybl_val = np.load(os.path.abspath(self.val_path + '/eybl_files.npy'))

		self.sess = tf.Session()
		self.num_classes = num_classes
		self.num_output = num_output
		self.input_shape = input_shape
		self.batch_size = batch_size
		self.alpha = alpha
		self.train_epoch = train_epoch
		self.learning_rate = learning_rate
		self.keep_prob = keep_prob
		self.validation_size = validation_size
		self.l2_weight = l2_weight
		self.inference_input = tf.placeholder(tf.float32, shape=[None, 125, 71])
		self.inference_model = self.get_model(self.inference_input, reuse=False)
		if restore_dir is not None:
			if self.DEBUG:
				print("Loading saved data...")
			dir = tf.train.Saver()
			dir.restore(self.sess, restore_dir)
			if self.DEBUG:
				print("Finished loading saved data...")

		if not os.path.exists('./%s Results' % curr_time):
			os.makedirs('./%s Results' % curr_time)

		self.metadata_file = './%s Results/METADATA.txt' % curr_time

		with open(self.metadata_file, 'w') as file:
			file.write('LSTM Clustering Network with %d Layers\n' % (self.lstm_layers))  
			file.write('Time of training: %s\n' % curr_time)
			file.write('Input shape: %s\n' % input_shape)
			file.write('Path to files: %s\n' % path_to_files)
			file.write('L2 Regularization Weight: %s\n' % l2_weight)
			file.write('Number of outputs: %s\n' % num_output)
			file.write('Number of classes: %s\n' % num_classes)
			file.write('Alpha value: %s\n' % alpha)
			file.write('Validation Size: %s\n' % validation_size)
			file.write('Learning rate: %s\n' % learning_rate)
			file.write('Batch size: %s\n' % batch_size)
			file.write('Number of Epochs: %s\n' % train_epoch)
			file.write('Dropout probability: %s\n' % keep_prob)
			file.write('Debug mode: %s\n' % debug)
			file.write('Restore directory: %s\n' % restore_dir)
			file.close()


	def triplet_loss(self, alpha):
		self.anchor = tf.placeholder(tf.float32, shape=[None, 125, 71])
		self.positive = tf.placeholder(tf.float32, shape=[None, 125, 71])
		self.negative = tf.placeholder(tf.float32, shape=[None, 125, 71])
		self.anchor_out = self.get_model(self.anchor, reuse=True)
		self.positive_out = self.get_model(self.positive, reuse=True)
		self.negative_out = self.get_model(self.negative, reuse=True)
		with tf.variable_scope('triplet_loss'):
			pos_dist = tf.reduce_sum(tf.square(self.anchor_out - self.positive_out))
			neg_dist = tf.reduce_sum(tf.square(self.anchor_out - self.negative_out))
			basic_loss = tf.maximum(0., alpha + pos_dist - neg_dist)
			loss = tf.reduce_mean(basic_loss)
			return loss

	def get_triplets(self):
		choices = ['bckg', 'eybl', 'gped', 'spsw', 'pled', 'artf']
		neg_choices = list(choices)
		choice = random.choice(choices)
		neg_choices.remove(choice)

		if choice == 'bckg':
			a = np.load(random.choice(self.bckg))
			p = np.load(random.choice(self.bckg))
		elif choice == 'eybl':
			a = np.load(random.choice(self.eybl))
			p = np.load(random.choice(self.eybl))
		elif choice == 'gped':
			a = np.load(random.choice(self.gped))
			p = np.load(random.choice(self.gped))
		elif choice == 'spsw':
			a = np.load(random.choice(self.spsw))
			p = np.load(random.choice(self.spsw))
		elif choice == 'pled':
			a = np.load(random.choice(self.pled))
			p = np.load(random.choice(self.pled))
		else:
			a = np.load(random.choice(self.artf))
			p = np.load(random.choice(self.artf))

		neg_choice = random.choice(neg_choices)

		if neg_choice == 'bckg':
			n = np.load(random.choice(self.bckg))
		elif neg_choice == 'eybl':
			n = np.load(random.choice(self.eybl))
		elif neg_choice == 'gped':
			n = np.load(random.choice(self.gped))
		elif neg_choice == 'spsw':
			n = np.load(random.choice(self.spsw))
		elif neg_choice == 'pled':
			n = np.load(random.choice(self.pled))
		else:
			n = np.load(random.choice(self.artf))

		key = choice + choice + neg_choice

		if key in self.count_of_triplets:
			self.count_of_triplets[key] = self.count_of_triplets[key] + 1
		else:
			self.count_of_triplets[key] = 1
 
		a = noop(a, axis=0, norm='l2').transpose()
		p = noop(p, axis=0, norm='l2').transpose()
		n = noop(n, axis=0, norm='l2').transpose()

		a = np.expand_dims(a, 0)
		p = np.expand_dims(p, 0)
		n = np.expand_dims(n, 0)

		return a, p, n

	def get_model(self, input, reuse=False):
		with slim.arg_scope([slim.layers.conv2d, slim.layers.fully_connected],
							weights_initializer=tf.contrib.layers.xavier_initializer(uniform=True),
							weights_regularizer=slim.l2_regularizer(self.l2_weight), reuse=reuse):
			net = tf.transpose(input, [1, 0, 2])
			net = tf.reshape(net, [-1, self.input_shape[1]])
			net = slim.fully_connected(net, 150, scope='fc1')
			net = tf.split(net, self.input_shape[2], 0)
			lstm1 = tf.contrib.rnn.LSTMCell(150, forget_bias=1.0, initializer=tf.contrib.layers.xavier_initializer(uniform=True), state_is_tuple=True, reuse=reuse)
			lstm_cells = tf.contrib.rnn.MultiRNNCell([lstm1]*self.lstm_layers, state_is_tuple=True)
			net, states = tf.contrib.rnn.static_rnn(lstm_cells, net, dtype=tf.float32)
			net = net[-1]
			net = slim.fully_connected(net, self.num_output, scope='fc2', trainable=True)
			return net

	def train_model(self, outdir=None):
		loss = self.triplet_loss(alpha=self.alpha)
		self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
		self.optim = self.optimizer.minimize(loss=loss)
		self.sess.run(tf.global_variables_initializer())

		count = 0
		ii = 0
		val_percentage = 0
		val_conf_matrix = 0
		epoch=-1
		while True:
			epoch+=1
			ii = 0
			count = 0
			temp_count = 0
			full_loss = 0
			while ii <= self.batch_size:
				ii += 1
				a, p, n = self.get_triplets()

				temploss = self.sess.run(loss, feed_dict={self.anchor: a, self.positive: p, self.negative: n})

				if temploss == 0:
					ii -= 1
					count += 1
					temp_count += 1
					continue

				full_loss += temploss

				if ((ii + epoch * self.batch_size) % 1000 == 0):
					loss_mem.append(full_loss/(1000 + temp_count))
					full_loss = 0
					temp_count = 0
					get_loss(loss_mem)

				_, a, p, n = self.sess.run([self.optim, self.anchor_out, self.positive_out, self.negative_out],
															  feed_dict={self.anchor: a, self.positive: p,
																		 self.negative: n})

				d1 = np.linalg.norm(p - a)
				d2 = np.linalg.norm(n - a)

				if self.DEBUG:
					print("Epoch: %2d, Iter: %7d, IterSkip: %7d, Loss: %.4f, P_Diff: %.4f, N_diff: %.4f"% (epoch, ii, count, temploss, d1, d2))
			val_percentage, val_conf_matrix = self.validate(epoch)

		self.sess.close()
		return epoch, val_percentage, val_conf_matrix

	def get_sample(self, size=1, validation=False):
		data_list = []
		class_list = []

		if not validation: 
			for ii in range(0, size):
				choice = random.choice(['bckg', 'eybl', 'gped', 'spsw', 'pled', 'artf'])

				if choice == 'bckg':
					data_list.append(noop(np.load(random.choice(self.bckg)), axis=0, norm='l2').transpose())
					class_list.append(self.bckg_num)
				elif choice == 'eybl':
					data_list.append(noop(np.load(random.choice(self.eybl)), axis=0, norm='l2').transpose())
					class_list.append(self.eybl_num)
				elif choice == 'gped':
					data_list.append(noop(np.load(random.choice(self.gped)), axis=0, norm='l2').transpose())
					class_list.append(self.gped_num)
				elif choice == 'spsw':
					data_list.append(noop(np.load(random.choice(self.spsw)), axis=0, norm='l2').transpose())
					class_list.append(self.spsw_num)
				elif choice == 'pled':
					data_list.append(noop(np.load(random.choice(self.pled)), axis=0, norm='l2').transpose())
					class_list.append(self.pled_num)
				else:
					data_list.append(noop(np.load(random.choice(self.artf)), axis=0, norm='l2').transpose())
					class_list.append(self.artf_num)
		else:
			for ii in range(0, size):
				choice = random.choice(['bckg', 'eybl', 'gped', 'spsw', 'pled', 'artf'])

				if choice == 'bckg':
					data_list.append(noop(np.load(random.choice(self.bckg_val)), axis=0, norm='l2').transpose())
					class_list.append(self.bckg_num)
				elif choice == 'eybl':
					data_list.append(noop(np.load(random.choice(self.eybl_val)), axis=0, norm='l2').transpose())
					class_list.append(self.eybl_num)
				elif choice == 'gped':
					data_list.append(noop(np.load(random.choice(self.gped_val)), axis=0, norm='l2').transpose())
					class_list.append(self.gped_num)
				elif choice == 'spsw':
					data_list.append(noop(np.load(random.choice(self.spsw_val)), axis=0, norm='l2').transpose())
					class_list.append(self.spsw_num)
				elif choice == 'pled':
					data_list.append(noop(np.load(random.choice(self.pled_val)), axis=0, norm='l2').transpose())
					class_list.append(self.pled_num)
				else:
					data_list.append(noop(np.load(random.choice(self.artf_val)), axis=0, norm='l2').transpose())
					class_list.append(self.artf_num)		

		return data_list, class_list

	def validate(self, epoch):

		if self.DEBUG:
			print("Validation files loaded!")

		inputs, classes = self.get_sample(size=1000, validation=True)

		vector_inputs = self.sess.run(self.inference_model, feed_dict={self.inference_input: inputs})

		tempClassifier = copy.deepcopy(self.classifier)
		tempClassifier.fit(vector_inputs, classes)

		val_inputs, val_classes = self.get_sample(size=self.validation_size)

		vector_val_inputs = self.sess.run(self.inference_model, feed_dict={self.inference_input: val_inputs})

		pred_class = tempClassifier.predict(vector_val_inputs)

		percentage = len([i for i, j in zip(val_classes, pred_class) if i == j]) * 100.0 / self.validation_size

		if self.DEBUG:
			print("Validation Results: %.3f%% of of %d correct" % (percentage, self.validation_size))

		val_classes = list(map(lambda x : self.num_to_class[x], val_classes))
		pred_class = list(map(lambda x : self.num_to_class[x], pred_class))
		class_labels = [0, 1, 2, 3, 4, 5]
		class_labels = list(map(lambda x : self.num_to_class[x], class_labels))
		conf_matrix = confusion_matrix(val_classes, pred_class, labels=class_labels)
		np.set_printoptions(precision=2)

		plot_confusion_matrix(conf_matrix, classes=class_labels, title='Confusion Matrix', epoch=epoch, accuracy=percentage)

		plt.figure(figsize=(15.0, 15.0))

		plt.bar(range(len(list(self.count_of_triplets.keys()))), self.count_of_triplets.values(), align='center', color='b')
		plt.xticks(range(len(self.count_of_triplets)), self.count_of_triplets.keys(), rotation='vertical')
		plt.subplots_adjust(bottom=0.30)
		plt.savefig('./%s Results/%striplet_distribution_epoch%s_%.3f%%.png' % (curr_time, curr_time, epoch, percentage), bbox_inches='tight')
		self.count_of_triplets=dict()

		return percentage, conf_matrix

def noop(vector, axis, norm):
	return vector*10e4