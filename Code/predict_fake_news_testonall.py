#!/usr/bin/python
# -*- coding: ascii -*-
import string, os, sys, code, time, multiprocessing, pickle, glob, re, time
import collections, shelve, copy, itertools, math, random, argparse, warnings
import datetime
import socket

import sys
from pandas.core import sparse

import sklearn
import numpy as np
np.set_printoptions( linewidth=200 )

from sklearn import metrics
from sklearn.datasets import fetch_20newsgroups
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction import DictVectorizer

from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from scipy.sparse import coo_matrix, hstack, csr_matrix
# terminal config
terminal_columns = 300
# this below is just to check if python is in interactive mode
import __main__
if not hasattr(__main__, '__file__'):
   terminal_size = os.popen('stty size', 'r').read().split()
   terminal_rows = int(terminal_size[0])
   terminal_columns = int(terminal_size[1])

import pandas as pd
terminal_columns, terminal_rows = pd.util.terminal.get_terminal_size()

import numpy as np
np.set_printoptions( linewidth=terminal_columns )
np.random.seed(1234567890)
random.seed(1)

import scipy
import scipy.stats
import scipy.optimize

import sklearn
import sklearn.datasets
import sklearn.ensemble
import sklearn.linear_model
import sklearn.tree
import sklearn.svm
import sklearn.neighbors
import sklearn.lda
import sklearn.qda
import sklearn.naive_bayes
import sklearn.feature_selection
import sklearn.preprocessing
import sklearn.grid_search
import matplotlib.pyplot as mplpl
import mord as m

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import basics_fake_news
from sklearn.utils import shuffle
import tweetstxt_basic
# from sklearn.neural_network import MLPClassifier

# output properties
terminal_columns, terminal_rows = pd.util.terminal.get_terminal_size()
pd.set_option( "display.width", terminal_columns )
pd.set_option( 'max_columns', terminal_columns/9 )
pd.set_option( 'display.max_columns', 99 )
pd.set_option( "display.width", 300 )

_SQRT2 = np.sqrt(2)
def normalized_max_min_funct_sikitlearn(demographicsDict):
    min_max_scaler = sklearn.preprocessing.MinMaxScaler()
    X_train_minmax = min_max_scaler.fit_transform(demographicsDict)

    return (X_train_minmax)

def add_med_mean_features(fdf, feature_name, groupby_name):

   df = fdf.copy()

   df.loc[:, 'mean_'+feature_name] = df[feature_name] * 0.0
   df.loc[:, 'med_'+feature_name] = df[feature_name] * 0.0
   df.loc[:, 'above_' + feature_name + '_mean'] = df[feature_name] * 0.0
   df.loc[:, 'above_' + feature_name + '_med'] = df[feature_name] * 0.0
   if 'created_at' not in df:
      df.loc[:, 'created_at'] = df[feature_name] * 0.0

   groupname_list = list(set(list(df[groupby_name][:])))

   grby_mean = df.groupby(groupby_name).mean()
   grby_med = df.groupby(groupby_name).median()
   for source_id in groupname_list:
      source_mean = grby_mean[feature_name][source_id]
      source_med = grby_med[feature_name][source_id]
      index_list = df[df[groupby_name] == source_id].index.tolist()
      for index_m in index_list:
         df['mean_'+feature_name][index_m] = source_mean
         df['med_'+feature_name][index_m] = source_med
         df['tweet_text'][index_m] = fdf['tweet_text'][index_m]
         df['created_at'][index_m] = index_m
         if df[feature_name][index_m] >= source_mean:
            df['above_' + feature_name + '_mean'][index_m] = 1
         else:
            df['above_' + feature_name + '_mean'][index_m] = 0

         if source_med==0:
            if df[feature_name][index_m] > source_med :
               df['above_' + feature_name + '_med'][index_m] = 1
            else:
               df['above_' + feature_name + '_med'][index_m] = 0
         else:
            if df[feature_name][index_m] >= source_med:
               df['above_' + feature_name + '_med'][index_m] = 1
            else:
               df['above_' + feature_name + '_med'][index_m] = 0

   return df

def hellinger1(p, q):
   return scipy.linalg.norm(np.sqrt(p) - np.sqrt(q)) / _SQRT2

def hellinger2(p, q):
   return scipy.spatial.distance.euclidean(np.sqrt(p), np.sqrt(q)) / _SQRT2

def hellinger3(p, q):
   return np.sqrt(np.sum((np.sqrt(p) - np.sqrt(q)) ** 2)) / _SQRT2


def preprocess( filename, dirs, fdf,fdf_t, nshalf,
   # dependentvar='above_num_retweets_med',
   # dependentvar='above_num_retweets_mean',
   dependentvar,
   tm_featnm="label", num_class=2 ):

   if tm_featnm not in fdf.columns:
      fdf.loc[:,tm_featnm] = fdf.index
      fdf_t.loc[:, tm_featnm] = fdf_t.index

   # m_thresh = 0.2

   pd.options.mode.chained_assignment = None
   df_dict = collections.defaultdict(pd.DataFrame)
   for nm_cls in list(set(fdf[dependentvar][:])):
      df_dict[nm_cls] = fdf.ix[ fdf[dependentvar]==nm_cls, : ]

   # dfpos = fdf.ix[ fdf[dependentvar]>m_thresh, : ]
   # dfneg = fdf.ix[ fdf[dependentvar]<=m_thresh, : ]

   # print dfpos.iloc[ 0:20 ]
   # print dfneg.iloc[ 0:20 ]

   # print "Number of samples diff classes", len(dfpos), len(dfneg)
   print "Number of samples diff classes", str([len(df_dict[i_cls]) for i_cls in df_dict])
   # inspect distribution of tweet times
   def inspect_timestamps( tms, description ):
      tms = list(tms)
      quantiles = np.percentile( tms, np.arange( 0, 101, 10).tolist() )
      print "Quantiles of tweet time", description
      def hrtime( epoch ):
         return datetime.datetime.fromtimestamp( int(epoch) ).strftime(
            '%Y-%m-%d %H:%M:%S' )
      for quantile in quantiles:
         print hrtime(quantile),
      print

   '''
   # inspect distribution of tweet times
   try:
      inspect_timestamps( dfpos[tm_featnm].values, "pos" )
      inspect_timestamps( dfneg[tm_featnm].values, "neg" )
   # except ValueError:
   #    print "ValueError in inspect_timestamps, ignoring"
   except:
      print "ValueError in inspect_timestamps, ignoring"
   '''
   # filtering
   featstotrain  = \
      basics_fake_news.get_featnames_from_filename( filename )
   fdf = basics_fake_news.filter_data( fdf, verbose=True )


   return subsample_and_balance( filename, nshalf, df_dict,fdf_t, tm_featnm )


   # return subsample_and_balance(filename, nshalf, dfp, dfn, "index")


# def subsample_and_balance( filename, nshalf, df_dict, tm_featnm="created_at" ):
def subsample_and_balance(filename, nshalf, df_dict,df_t, tm_featnm="createdat"):

   for i_cls in df_dict:
      if tm_featnm not in df_dict[i_cls].columns:
         df_dict[i_cls].loc[:,tm_featnm] = df_dict.index
      if len(df_dict[i_cls])<5:
         return df_dict,df_dict,[],[]


   for i_cls in df_dict:
      df_dict[i_cls].loc[:,"rnd1"] = np.random.rand(len(df_dict[i_cls]))
   # dfp.loc[:,"label"] = 1
   # dfn.loc[:,"label"] = 0

   pd.options.mode.chained_assignment = "warn"

   if "mtest" in filename:
      trainratio = 0.75
      testratio = 1.0-trainratio
      ntestslices = 5

   if "stest" in filename:
      trainratio = .8
      testratio = 1.0-trainratio
      ntestslices = 1

   df_dict_1 = collections.defaultdict(pd.DataFrame)
   df_dict_2 = collections.defaultdict(pd.DataFrame)

   for i_cls in df_dict:
      # tms = df_dict[i_cls][tm_featnm]
      # splittm = np.percentile( tms, int(trainratio*100) )
      # # splittm_train = np.percentile( tms, int(100) )
      # splittm_train = np.percentile( tms, int(trainratio * 100) )
      # df_dict_1[i_cls] = df_dict[i_cls].iloc[ np.where( df_dict[i_cls][tm_featnm]<=splittm_train )[0], : ]
      # # dict[i_cls].iloc[ np.where( df_dict[i_cls][tm_featnm]<splittm_train )[0], : ]
      # df_dict_2[i_cls] = df_dict[i_cls].iloc[ np.where( df_dict[i_cls][tm_featnm]>=splittm )[0], : ]

      tms = df_dict[i_cls][tm_featnm]
      trainratio=1
      splittm = np.percentile( tms, int(trainratio*100) )
      splittm_train = np.percentile( tms, int(100) )
      # splittm_train = np.percentile( tms, int(trainratio * 100) )
      df_dict_1[i_cls] = df_dict[i_cls].iloc[ np.where( df_dict[i_cls][tm_featnm]<=splittm_train )[0], : ]
      # dict[i_cls].iloc[ np.where( df_dict[i_cls][tm_featnm]<splittm_train )[0], : ]
      df_dict_2[i_cls] = df_dict[i_cls].iloc[ np.where( df_dict[i_cls][tm_featnm]<=splittm )[0], : ]


   print "After time-horizon split:", str([(len(df_dict_1[i_cls]), len(df_dict_2[i_cls])) for i_cls in df_dict])



   # prepare the output df
   dftrain = pd.concat([ df_dict_1[i_cls] for i_cls in df_dict ])
   dftrain.sort( tm_featnm, inplace=True  )
   dftest = pd.concat([ df_dict_2[i_cls] for i_cls in df_dict ])
   dftest.sort( tm_featnm, inplace=True  )
   df = pd.concat([ dftrain, dftest ])
   positions_train = set(range(len( dftrain )))
   positions_test = set(range(len( dftest )))

   dftrain = df.copy()
   dftest = df.copy()

   print "Train and test sizes:", len(dftrain), len(dftest)
   print "Train and test ratios:", 1.0*len(dftrain)/len(df), 1.0*len(dftest)/len(df)

   # prepare the output long balancedc df
   # nsampleslong = min( [len(dfp), len(dfn)] )
   nsampleslong = len(dftrain) + len(dftest)
   for i_cls in df_dict:
      nsampleslong = min(len(df_dict[i_cls]), nsampleslong)

   first_round = 0
   for i_cls in df_dict:
      if first_round==0:
         df1long = df_dict[i_cls].loc[random.sample(df_dict[i_cls].index, nsampleslong), :]
         first_round=1
      else:
         df2long = df_dict[i_cls].loc[random.sample(df_dict[i_cls].index, nsampleslong), :]
   # df2long = dfn.loc[random.sample(dfn.index, nsampleslong), :]
         df1long = df1long.append( df2long )

   dflong = df1long
   # get the positions for train and test sets
   positions_all = set(range(len(df_t)))
   # positions_test_all = sorted(list(positions_all - positions_train))
   positions_test_all = sorted(list(positions_all))
   positions_train = list(positions_train)
   slicesize = len(positions_test_all)/ntestslices
   posslices_test = []
   for i in range(ntestslices):
      posslices_test += [ positions_test_all[ slicesize*i : slicesize*(i+1) ] ]

   return df,df_t, dflong, positions_train, posslices_test




def classify( filename, dirs, df,df_t, dflong,
   positions_train, posslices_test, nshalf,
   classifier, featset, tm_featnm="created_at" ):
   # ignore "DeprecationWarning: `fprob` is deprecated"
   warnings.simplefilter('ignore', DeprecationWarning)
   # ignore "Mean of empty slice.", RuntimeWarning
   warnings.simplefilter('ignore', RuntimeWarning)

   # df["rnd2"] = df["label"] + np.random.rand(len(df))
   df["rnd2"] = np.random.rand(len(df))
   dflong["rnd2"] = np.random.rand(len(dflong))


   positions_test = posslices_test[0]
   # print positions_test

   propstoclean, featstotrain  = \
      basics_fake_news.get_featnames_from_filename( filename )

   propdict = collections.defaultdict(list)
   # propdict["featname"] = featstotrain + [ "rnd1", "rnd2", "sima_exp_meme_rnd" ]
   propdict["featname"] = featstotrain + [ "rnd1", "rnd2" ]
   propdict["featname"] = featstotrain
   print "Predicting feats:", propdict["featname"]




   labels = df.iloc[positions_train].loc[:,"label"].values
   samplesdf = df.iloc[positions_train].loc[:,propdict["featname"]]
   print "Negative values:"
   # for col in samplesdf:
   #    if np.sum(samplesdf[col]<0):
   #       print col, np.sum(samplesdf[col]<0)
         # print samplesdf.ix[ samplesdf[col]<0, col ]
   samples = samplesdf.as_matrix()

   labels_test = df_t.iloc[positions_test].loc[:,"label"].values
   samples_test = \
      ( df_t.iloc[positions_test].loc[:,propdict["featname"]] ).as_matrix()
   samples_testdf_full = df_t.iloc[positions_test]
   # labslices_test = []
   # splslices_test = []
   # for myslice in posslices_test:
   #    labslices_test += [ df_t.iloc[myslice].loc[:,"label"].values ]
   #    splslices_test += [
   #       ( df_t.iloc[myslice].loc[:,propdict["featname"]] ).as_matrix() ]


   samplesdf = samplesdf.dropna()
   samples_test_df = samples_test.copy()
#########################
   df_copy = df.copy()
   count = 0
   num_feat_after_vect = collections.defaultdict(int)
   # for feat in featstotrain:
   #     # if feat=="text":
   #     #     if df_copy[feat].dtype==object:
   #         if feat=="text":
   #
   #             count_vect = CountVectorizer(max_features=500, stop_words='english')
   #             # count_vect = CountVectorizer(stop_words='english')
   #             # count_vect = CountVectorizer(stop_words='english')
   #             X_train_counts = count_vect.fit_transform(df_copy[feat])
   #             print "Shape of the matrix of counts:", X_train_counts.shape
   #
   #             tfidf_transformer = TfidfTransformer(use_idf=False)
   #             X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
   #             num_feat_after_vect[feat] = X_train_tfidf.shape[1]
   #             if count==0:
   #                 non_word_feats = X_train_tfidf
   #             else:
   #                non_word_feats = hstack([non_word_feats, X_train_tfidf])
   #         else:
   #             feat_list = df_copy[feat].reshape(len(df_copy),1)
   #             num_feat_after_vect[feat] = feat_list.shape[1]
   #
   #             if count==0:
   #                non_word_feats = coo_matrix(feat_list)
   #             else:
   #                non_word_feats = hstack([non_word_feats, coo_matrix(feat_list)])
   #         count+=1
   # non_word_feats_scr = non_word_feats.tocsr()
   # samples_csr_matrix = non_word_feats_scr[positions_train]
   # count= 0
   #
   # df_t_copy = df_t.copy()
   # count = 0
   # num_feat_after_vect = collections.defaultdict(int)
   # for feat in featstotrain:
   #     # if feat!="text":
   #         if df_t_copy[feat].dtype==object:
   #
   #             count_vect = CountVectorizer(max_features=500, stop_words='english')
   #             # count_vect = CountVectorizer(stop_words='english')
   #             # count_vect = CountVectorizer(stop_words='english')
   #             X_train_counts = count_vect.fit_transform(df_t_copy[feat])
   #             print "Shape of the matrix of counts:", X_train_counts.shape
   #
   #             tfidf_transformer = TfidfTransformer(use_idf=False)
   #             X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
   #             num_feat_after_vect[feat] = X_train_tfidf.shape[1]
   #             if count==0:
   #                 non_word_feats = X_train_tfidf
   #             else:
   #                non_word_feats = hstack([non_word_feats, X_train_tfidf])
   #         else:
   #             feat_list = df_t_copy[feat].reshape(len(df_t_copy),1)
   #             num_feat_after_vect[feat] = feat_list.shape[1]
   #
   #             if count==0:
   #                non_word_feats = coo_matrix(feat_list)
   #             else:
   #                non_word_feats = hstack([non_word_feats, coo_matrix(feat_list)])
   #         count += 1
   # non_word_feats_scr = non_word_feats.tocsr()

   # samples_tsest_csr_matrix = non_word_feats_scr[positions_test]
   # samples_test_csr_matrix = collections.defaultdict(csr_matrix)
   # for myslice in posslices_test:
   #     samples_test_csr_matrix[count] = non_word_feats_scr[myslice]
   #     count +=1


###########################


   def hrtime( epoch ):
      return datetime.datetime.fromtimestamp( int(epoch) ).strftime(
         '%Y-%m-%d %H:%M:%S' )


   # removing nans before computing correlations
   dfc = df.dropna()
   dflongc = dflong.dropna()
   if len(dfc)==0:
      print "WARNING: using df as dfc, otherwise ValueError below"
      dfc=df


   def apply_cdfgoodtrans( samples_var, samples_ref ):
      samplesdf_var = pd.DataFrame(samples_var)
      samplesdf_ref = pd.DataFrame(samples_ref)
      for col in samplesdf_var:
         samplesdf_var[col] = basics_fake_news.transform_values_to_cdf(
            samplesdf_var[col].values, samplesdf_ref[col].values )
      return samplesdf_var.as_matrix()

   if "cdfgoodtrans" in classifier:
      # it has to be done in this order
      samples_test = apply_cdfgoodtrans( samples_test, samples )
      # samples_test = apply_cdfgoodtrans( samples_tsest_csr_matrix.toarray(), samples_tsest_csr_matrix.toarray())
      samples_test = csr_matrix(samples_test)
      # for i in range(len(splslices_test)):
      #    splslices_test[i] = apply_cdfgoodtrans( splslices_test[i], samples )
      samples = apply_cdfgoodtrans( samples, samples )
      # samples = apply_cdfgoodtrans(samples_csr_matrix.toarray(),samples_csr_matrix.toarray())
      samples = csr_matrix(samples)
      # print "After cdfgoodtrans (mean):", samples.mean(axis=0)
      # print "After cdfgoodtrans (min, max):", samples.min(axis=0), samples.max(axis=0)

   if "minmax" in classifier:
      scaler = sklearn.preprocessing.MinMaxScaler()
      # samples = scaler.fit_transform(samples)
      # samples_test = scaler.transform(samples_test)
      samples = scaler.fit_transform(samples_csr_matrix.toarray())
      samples_test = scaler.transform(samples_test_csr_matrix[0].toarray())
      samples_test = csr_matrix(samples_test)
      samples = csr_matrix(samples)
      # for i in range(len(splslices_test)):
      #    splslices_test[i] = scaler.transform(splslices_test[i])
      scaler = sklearn.preprocessing.MinMaxScaler()
      # print "After scaling (mean):", samples.mean(axis=0)
      # print "After scaling (std):", samples.std(axis=0)

   # if "none" in classifier:
   #    print "After scaling (mean):", samples.mean(axis=0)
   #    print "After scaling (std):", samples.std(axis=0)


   # classifier-independent standard feature importance
   sys.stdout.flush()
   # propdict["chi2"] =  sklearn.feature_selection.chi2(samples, labels)[0]
   # propdict["anova"] =  sklearn.feature_selection.f_classif(samples, labels)[0]

   ##### preprocessing
   if "std" in classifier:
      scaler = sklearn.preprocessing.StandardScaler()
      # samples = scaler.fit_transform(samples)
      # samples_test = scaler.transform(samples_test)
      samples = scaler.fit_transform(samples_csr_matrix)
      samples_test = scaler.transform(samples_test_csr_matrix)
      for i in range(len(splslices_test)):
         splslices_test[i] = scaler.transform(splslices_test[i])
      scaler = sklearn.preprocessing.StandardScaler()
      print "After scaling (mean):", samples.mean(axis=0)
      print "After scaling (std):", samples.std(axis=0)

   ##### classifier-dependent feature importance
   # ignore ""
   warnings.simplefilter('ignore', UserWarning)
   clfs = dict()
   ests = dict()
   timeprofiler = dict()
   nonparametric = [ "naive_bayes", "lda", "qda", "rfe_linear2" ,"naive_bayes_fit"]

   propsets = {}
   propsets = {
      # "dists": [ "featname", "hellinger", "jsdiv", "totvar" ],
      "corrs": [ "featname", "spearmanr", "spearmanr_long", "pearsonr", "pearsonr_long" ]
      }

   def fit( clfname, clf, samples=samples ):
      print clfname,
      starttime = time.time()
      if "gridsearch" in classifier:
         if clfname not in nonparametric:
            clf = sklearn.grid_search.GridSearchCV( clf, hparams, cv=10)#,
               #scoring="f1", refit=True)#, score_func=sklearn.metrics.f1_score )
            clf.fit( samples, labels)
            est = clf.best_estimator_
            print "Gridsearch:", clfname, clf.get_params()
         else:
            clf.fit( samples.toarray(), labels)
            est = clf
      else:
         clf.fit( samples, labels)
         est = clf
      clfs[clfname] = clf
      ests[clfname] = est
      timeprofiler[clfname] = time.time() - starttime

   print "Fitting:"

   def fit_RFE( clfname, clf, samples=samples ):
      print clfname,
      num_feat = 3
      starttime = time.time()
      hparams=[0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
      if "gridsearch" in classifier:
         if clfname not in nonparametric:
            param_grid = [
               {'C': [0.01, 0.1, 1, 10, 100, 1000]},
               # {'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001]},
            ]
            # param_grid = [{'estimator_C': [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]}]
            # clf = sklearn.grid_search.GridSearchCV( clf,param_grid, cv=10, scoring=sklearn.metrics.f1_score )

            clf = sklearn.feature_selection.RFECV(clf, step=1, cv=10)
            # clf = sklearn.feature_selection.RFE(clf)
            # param_grid = [{'estimator__C': [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]}]
            # clf = sklearn.grid_search.GridSearchCV( clf, param_grid, cv=10)#,scoring="f1", refit=True)#, score_func=sklearn.metrics.f1_score )
            # clf.fit(samples.toarray(), labels)
            clf.fit(samples, labels)
            est = clf
            # print "Gridsearch:", clfname, clf.get_params()
         else:
            # clf = sklearn.feature_selection.RFE(clf)
            clf = sklearn.feature_selection.RFECV(clf,cv=10)
            clf.fit(samples.toarray(), labels)
            est = clf
      else:
         clf = sklearn.feature_selection.RFE(clf ,n_features_to_select=7)
         clf.fit( samples, labels)
         est = clf
      clfs[clfname] = clf
      ests[clfname] = est
      timeprofiler[clfname] = time.time() - starttime

   print "Fitting:"

   if ("logreg" in classifier or "allclfs" in classifier or "mainclfs" in classifier)and \
      ("none" not in classifier ):#or "cdfgoodtrans" in classifier ):
      clfname = "logreg"
      # hparams = {'C': [0.01, 0.1, 1, 10, 100, 1000, 10000]}
      # fit_RFE( clfname, sklearn.linear_model.LogisticRegression() )
      # print("support : " + str(ests[clfname].support_))
      # print("ranking : " + str(ests[clfname].ranking_))
      # print("scores : " + str(ests[clfname].estimator_.coef_))
      # print("importance : " + str(ests[clfname].estimator_))

      fit_RFE( clfname, sklearn.linear_model.LogisticRegression() )

      # fit( clfname, sklearn.linear_model.Ridge() )
      # fit( clfname, sklearn.linear_model.RidgeCV(alphas=[0.001,0.01,0.1,1,10,100]) )

      # fit( clfname, m.LogisticIT(alpha=1))
      # fit( clfname, m.OrdinalRidge())

      # fit( clfname, m.LogisticAT(alpha=1.))
      # fit( clfname, m.LogisticSE(alpha=1.))
      # yhat = ests[clfname].predict(samples)
      # from sklearn.metrics import accuracy_score

      # print('acc : ' + str(accuracy_score(labels, yhat)))
      # print('corr : ' + str(np.corrcoef(labels, yhat)))
      # print('corr : ' + str(scipy.stats.spearmanr(labels, yhat)))
      # propdict[clfname] =  ests[clfname].coef_[0]

      # print("support : " + str(ests[clfname].support_))
      # print("ranking : " + str(ests[clfname].ranking_))
      # print("scores : " + str(ests[clfname].coef_))
      # print(ests[clfname].coef_[0])
      propsets["logreg"] = [ "featname", clfname ]
      # if "mainclfs" in classifier:
      #    propsets["mainclfs"] += [ clfname ]
      #    propsets["extmainclfs"] += [ clfname ]
      # print("scores : " + str(ests[clfname].coef_))
      # print("support : " + str(ests[clfname].support_))
      # print("ranking : " + str(ests[clfname].ranking_))
      # print("scores : " + str(ests[clfname].estimator_.coef_))

      # yhat = ests[clfname].predict(samples)
      # from sklearn.metrics import accuracy_score
      #
      # print('acc : ' + str(accuracy_score(labels, yhat)))
      # print('corr : ' + str(np.corrcoef(labels, yhat)))
      # print('corr : ' + str(scipy.stats.spearmanr(labels, yhat)))
      # propdict[clfname] =  ests[clfname].coef_[0]
      # # crashes on gridsearch and other places
      # clfname = "rndlogreg"
      # hparams = {'C': [1, 10, 100, 1000]}
      # fit( clfname, sklearn.linear_model.RandomizedLogisticRegression() )
      # propdict[clfname] =  ests[clfname].scores_


   if "svm-lin" in classifier or "allclfs" in classifier:
      clfname = "svm_linear1"
      hparams = {'C': [0.01, 0.1, 1, 10, 100, 1000, 10000]}
      # fit( clfname, sklearn.svm.LinearSVC(class_weight='balanced') )

      # fit( clfname, sklearn.svm.LinearSVC() )
      # propdict[clfname] =  ests[clfname].coef_[0]
      # propsets["svm-lin"] = [ "featname", clfname ]

      fit_RFE( clfname, sklearn.linear_model.LogisticRegression() )
      # print("support : " + str(ests[clfname].support_))
      # print("ranking : " + str(ests[clfname].ranking_))
      # print("scores : " + str(ests[clfname].estimator_.coef_))




   if "naive_bayes" in classifier:
      clfname = "naive_bayes"
      fit_RFE(clfname, sklearn.naive_bayes.MultinomialNB())
      print("support : " + str(ests[clfname].support_))
      print("ranking : " + str(ests[clfname].ranking_))
      print("scores : " + str(ests[clfname].estimator_.coef_))
      # fit(clfname, sklearn.naive_bayes.MultinomialNB())
      # from sklearn.model_selection import KFold, cross_val_score
      # k_fold = KFold(n_splits=5, shuffle=True, random_state=0)
      # clf = sklearn.naive_bayes.GaussianNB()
      # print cross_val_score(clf, samples.toarray(), labels, cv=5, n_jobs=1)


      # fit_RFE( clfname, clf )
      # print("support : " + str(ests[clfname].support_))
      # print("ranking : " + str(ests[clfname].ranking_))
      # print("scores : " + str(ests[clfname].estimator_.coef_))
      # print("scores : " + str(ests[clfname].coef_))

      # yhat = ests[clfname].predict(samples)
      # from sklearn.metrics import accuracy_score
      #
      # print('acc : ' +  str(accuracy_score(labels, yhat)))
      # print('corr : ' + str(np.corrcoef(labels, yhat)))
      # print('corr : ' + str(scipy.stats.spearmanr(labels, yhat)))


   def print_f1_dict(f1_dict):
      for key in sorted( f1_dict.keys(), key=lambda x: float(x.split(", ")[0][1:]) ):
         print "%.2f" % f1_dict[key],
      for key in sorted( f1_dict.keys(), key=lambda x: float(x.split(", ")[0][1:]) ):
         print key,
      return ""

   # gridsearch and cross-validation
   print "Testing:"
   printlist = []
   useravgf1s = dict()
   memeavgf1s = dict()
   pubtable = dict()
   train_liklihood = []
   test_liklihood = []
   for clfname in clfs:
      # if clfname!="naive_bayes": continue
      printitem = [ clfname ]
      starttime = time.time()
      samples_tmp = samples_test
      print "Testing", clfname

      #
      # samples_test = df_gl[''][]
      # labels_test = df_gl['label']

      labels_pred = clfs[clfname].predict( samples_test)
      from sklearn.metrics import accuracy_score

      print('acc test : ' +  str(accuracy_score(labels_test, labels_pred)))
      # print('corr test : ' + str(np.corrcoef(labels_test, labels_pred)))
      # print('corr test : ' + str(scipy.stats.spearmanr(labels_test, labels_pred)))

      for label_tmp in set(labels_test):
          # print('label : ' + str(label_tmp))
          total_c=0; correct_c=0
          for lable_i in range(len(labels_test)):
              if labels_test[lable_i]==label_tmp:
                  total_c+=1
                  if labels_pred[lable_i]==label_tmp:
                      correct_c+=1

          print('accuracy : ' +str(label_tmp) + ' : ' + str(float(correct_c)/total_c))

      acc_gt = collections.defaultdict(dict)
      for tt in set(labels_test):
         acc_gt[tt] = collections.defaultdict(int)
      for label_tmp in set(labels_test):
         total_c = 0;
         correct_c = 0
         for lable_i in range(len(labels_pred)):
            if labels_test[lable_i]==label_tmp:
               acc_gt[label_tmp][labels_pred[lable_i]]+=1
         # print('accuracy : ' + str(float(correct_c) / total_c))

      outp = {}
      outp_var = {}
      # news_cat_list = ['pants-fire', 'false', 'mostly_false', 'half-true', 'mostly-true', 'true']
      # news_cat_list_f = ['mostly-false', 'false', 'half-true', 'true', 'mostly-true', 'pants-fire']
      dataset = 'snopes'
      data_n = 'sp'
      if dataset == 'snopes' or dataset == 'snopes_nonpol':
         # col_l = ['b', 'g', 'c', 'y', 'r']
         col_l = ['red', 'orange', 'gray', 'lime', 'green']
         news_cat_list_t_f = ['FALSE', 'MOSTLY FALSE', 'MIXTURE', 'MOSTLY TRUE', 'TRUE']
         news_cat_list_v = [-2, -1, 0, 1, 2]
         # news_cat_list_v = [1, 2, 3, 4, 5]

         news_cat_list_n = ['FALSE', 'MOSTLY\nFALSE', 'MIXTURE', 'MOSTLY\nTRUE', 'TRUE']
      if dataset == 'politifact':
         # col_l = ['grey','b', 'g', 'c', 'y', 'r']
         col_l = ['darkred', 'red', 'orange', 'gray', 'lime', 'green']

         news_cat_list_n = ['PANTS ON\nFIRE', 'FALSE', 'MOSTLY\nFALSE', 'HALF\nTRUE', 'MOSTLY\nTRUE', 'TRUE']
         news_cat_list_t_f = ['pants-fire', 'false', 'mostly-false', 'half-true', 'mostly-true', 'true']
         news_cat_list_v = [-2, -2, -1, 0, 1, 2]

      if dataset == 'mia':
         # col_l = ['b', 'r']
         col_l = ['red', 'green']
         news_cat_list_n = ['RUMORS', 'NON RUMORS']
         news_cat_list_t_f = ['rumor', 'non-rumor']
         news_cat_list_v = [-1, 1]




      #
      # count = 0
      # Y = [0] * len(news_cat_list_v)
      # # Y1 = [0] * len(thr_list)
      # mplpl.rcParams['figure.figsize'] = 6.8, 5
      # mplpl.rc('xtick', labelsize='large')
      # mplpl.rc('ytick', labelsize='large')
      # mplpl.rc('legend', fontsize='small')
      # cat_num_st = 0
      #
      # width = 0.05
      # for cat_v in news_cat_list_v:
      #    count += 1
      #    outp[cat_v] = []
      #    for ii in news_cat_list_v:
      #       outp[cat_v].append(acc_gt[cat_v][ii])
      #    # for i in range(len(gt_acc[cat_v])):
      #    #     outp[i].append(gt_acc[cat_v][i])
      #    if dataset == 'snopes' or dataset == 'snopes_nonpol':
      #       mplpl.bar([0.09, 0.18, 0.28, 0.38, 0.48], outp[cat_v], width, bottom=np.array(Y), color=col_l[count - 1],
      #                 label=news_cat_list_n[count - 1])
      #    elif dataset == 'politifact':
      #       mplpl.bar([0.09, 0.18, 0.28, 0.38, 0.48], outp[cat_v], width, bottom=np.array(Y), color=col_l[count - 1],
      #                 label=news_cat_list_n[count - 1])
      #    Y = np.array(Y) + np.array(outp[cat_v])
      #
      # mplpl.xlim([0.08, 0.58])
      # mplpl.ylim([0, 60])
      # mplpl.ylabel('Composition of labeled news stories', fontsize=14, fontweight='bold')
      # # mplpl.xlabel('Top k news stories reported by negative PTL', fontsize=13.8,fontweight = 'bold')
      # mplpl.xlabel('Users\' perception', fontsize=14,
      #              fontweight='bold')
      # # mplpl.xlabel('Top k news stories ranked by NAPB', fontsize=18)
      #
      # mplpl.legend(loc="upper right", ncol=3, fontsize='small')
      #
      # mplpl.subplots_adjust(bottom=0.2)
      #
      # mplpl.subplots_adjust(left=0.18)
      # mplpl.grid()
      # # mplpl.title(data_name, fontsize='x-large')
      # labels = news_cat_list_n
      # x = [0.1, 0.2, 0.3, 0.4, 0.5]
      # mplpl.xticks(x, labels)
      # pp = remotedir + '/fig/fig_exp1/news_based/initial/' + data_n + '_vote_composition_gt'
      # pp = '/NS/twitter-8/work/Reza/reliable_news/new_collected_data/fig/news_based/' + data_n + '_vote_composition_gt'
      # pp = '/NS/twitter-8/work/Reza/reliable_news/new_collected_data/fig/news_based/' + data_n + '_napb_composition_gt'
      # pp = '/NS/twitter-8/work/Reza/reliable_news/new_collected_data/fig/news_based/' + data_n + '_gt_accuracy_reg_weight'
      pp = '/NS/twitter-8/work/Reza/reliable_news/new_collected_data/fig/news_based/' + data_n + '_gt_accuracy_ordinalreg_weight'
      # mplpl.savefig(pp + '.pdf', format='pdf')
      # mplpl.savefig(pp + '.png', format='png')

      # labels_pred = clfs[clfname].predict( samples_csr_matrix.toarray())
      # train_liklihood = clfs[clfname].predict_proba(samples_test)
      # test_liklihood = clfs[clfname].predict_proba(samples_test)
      acc = accuracy_score(labels_test, labels_pred)
      corr = np.corrcoef(labels_test, labels_pred)
      corr_pearson = scipy.stats.spearmanr(labels_test, labels_pred)


   # return train_liklihood, test_liklihood, labels_pred
   return acc, corr,corr_pearson

def main():
   global df_gl
   # A = coo_matrix([[1, 2], [3, 4]])
   # B = coo_matrix([[5], [6]])
   # hstack([A,B]).toarray()
   # exit()
   # fdf = basics.load_data( "~/Desktop/icwsm_svn/code/recsys-for-posting/data/extend_uidposts.csv", nrows=100)
   hostname = socket.gethostname()
   parser = argparse.ArgumentParser(prog='PROG')
   parser.add_argument( '-t', default="all",
      help='taskname' )
   parser.add_argument( '-pre', nargs='+', default=None,
      help='what preprocessing to apply' )
   parser.add_argument( '-featsets', nargs='+', default=None,
      help='what feature sets to use' )
   parser.add_argument( '-transforms', nargs='+', default=None,
      help='what transforms to use' )
   parser.add_argument( '-clf', nargs='+', type=str, default=["mainclfs"],#"svm-nonlin"],
      help='apply all classifiers in one thread or in seperate threads' )
   parser.add_argument( '-nr', type=int, default=None,
      help='how many rows to load' )
   parser.add_argument( '-ns', type=int, default=None,
      help='how many samples to use' )
   parser.add_argument( '-nu', default=None,
      help='how many users (corresponding input file needed)' )
   parser.add_argument( '--timeout', type=int, default=60,
      help='timeout per process (the number of seconds)' )
   parser.add_argument( '-gs', action='store_true',
      help='run grid search' )
   parser.add_argument( '-mp', action='store_true',
      help='use multiprocessing?' )
   parser.add_argument( '-meme', default="hashtag",
      help='the type of memes to analyze' )
   parser.add_argument( '-seeds', default=1, help='run for how many seeds?' )
   parser.add_argument( '-topicvec', default="joints-lda-avg",
      help='the name of topical vectors' )
   args = parser.parse_args()
   # print args
   # return

   tm_featnm = "created-at"

   featsets = [
      # "allfeats"
      "worker_pt"
      # "worker_leaning"
      # "pt_count"
      # "worker_leaning_pt_count"
      # "worker_pt_count"
       ]
   preprocessings = [ "std", "minmax", "none" ]
   nusers = "all"
   transforms = [ #"notrans",
      # "cdftrans", "cdfalltrans", "cdflatetrans",
      # "cdflatealltrans", "cdflateaddtrans",
      "cdfgoodtrans",
       # "minmax"
   ]

   wdpath, remotedir = tweetstxt_basic.get_dirs()
   if tweetstxt_basic.is_local_machine():
      nrows = 1e5
      nsamples = int(1e4)
      args.gs = True
   else:
      nrows = None
      nsamples = int(1e5)
      nsamples = int(2e4)

   meme = args.meme
   if args.nr!=None: nrows = args.nr
   if args.ns!=None: nsamples = args.ns
   if args.nu!=None: nusers = args.nu
   if args.pre!=None: preprocessings = args.pre
   if args.featsets!=None: featsets = args.featsets
   if args.transforms!=None: transforms = args.transforms
   if args.topicvec!=None: topicvec = args.topicvec
   if args.clf=="separate": classifiers = [ "trees", "logreg", "svm-lin",
      "svm-nonlin", "svm-sigm", "other", "sgd", "rfe" ]
   else:
      classifiers = args.clf


   methods = []
   for preprocessing in preprocessings:
      for classifier in classifiers:
         for transform in transforms:
            if args.gs: methods += \
               [transform+"-"+preprocessing+"-"+classifier+"-gridsearch"]
            else: methods += \
               [transform+"-"+preprocessing+"-"+classifier]

   if "mainclfs" in classifiers:
      print "Using main methods!"
      methods = [

         # "cdfgoodtrans-mainclfs-stest-gridsearch",########
         # "cdfgoodtrans-mainclfs-stest-naive_bayes",########
         "cdfgoodtrans-mainclfs-stest",########
         #       # "minmax-none-svm-lin-gridsearch-stest-rndimp",

      ]

   # if "svm-lin" in classifiers:
   #    print "Using main methods!"
   #    methods = [
   #       # "notrans-std-mainclfs-gridsearch-stest-rndimp",
   #       # "cdfgoodtrans-none-svm-lin-gridsearch-stest-rndimp",
   #       # "cdfgoodtrans-none-gridsearch-stest-rndimp",
   #       "cdfgoodtrans-none-stest-rndimp",
   #       # "minmax-none-svm-lin-gridsearch-stest-rndimp",
   #       # "notrans-std-mainclfs-gridsearch-mtest",
   #       # "cdfgoodtrans-none-mainclfs-gridsearch-mtest",
   #       # "notrans-minmax-mainclfs-gridsearch"
   #    ]


   dirs={ "png": os.path.expanduser(wdpath+"figs_similarity/"),
          "eps": os.path.expanduser(wdpath+"figs_similarity/"),
          "pdf": os.path.expanduser(wdpath+"figs_similarity/"),
          "data": os.path.expanduser(wdpath+"out_similarity/"),
          "include": os.path.expanduser(wdpath+"draft_similarity/include/"),
          "stdout": os.path.expanduser(wdpath+"mia_binary/") }
          # "stdout": os.path.expanduser(wdpath+"sp_nonpol_binary/") }
          # "stdout": os.path.expanduser(wdpath+"sp_binary/") }
          # "stdout": os.path.expanduser(wdpath+"pf_binary/") }
   for mydir in dirs.values():
      if not os.path.exists(mydir): os.makedirs(mydir)

   manager = multiprocessing.Manager()
   jobs = []
   jobnames = []

   # wdpath = '/NS/twitter-7/work/Reza/fake_news/data/preprocess/new_data_set/'
   # wdpath = '/NS/twitter-8/work/Reza/reliable_news/new_collected_data/snopes/'
   # wdpath_test = '/NS/twitter-8/work/Reza/reliable_news/new_collected_data/snopes/'

   wdpath = ''
   wdpath_test = ''

   pattern = "fake_news_features_sp.csv"
   pattern_test = "fake_news_features_sp.csv"

   # pattern = "fake_news_features_pf.csv"
   # pattern_test = "fake_news_features_pf.csv"

   # pattern = "fake_news_features_mia.csv"
   # pattern_test = "fake_news_features_mia.csv"
   # pattern = "fake_news_features_sp_nonpol.csv"
   # pattern_test = "fake_news_features_sp_nonpol.csv"

   print "Pattern:", pattern
   # inputpaths = glob.glob(wdpath+pattern)
   inputpaths = [wdpath+pattern]



   primes = [ 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59,
      61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137 ]
   seeds = primes[ 0:int(args.seeds) ]

   print "Files:", inputpaths
   print "Featsets:", featsets
   print "Methods:", methods
   for inputpath in inputpaths:
      inputpathbase = "_".join( inputpath.split("_")[:-1] )
      inputfilename = os.path.splitext(os.path.basename(inputpath))[0]
      inputfilenamebase = "_".join( inputfilename.split("_")[:-1] )

      if ".rar" in inputpath: lzmaflag=True
      else: lzmaflag=False
      # fdf = basics.load_data( inputpath, nrows=nrows )
      fdf = pd.read_csv(inputpath, sep="\t")
      fdf_test = pd.read_csv(wdpath_test+pattern_test, sep="\t")
      # fdf_test = pd.read_csv(inputpath, sep="\t")
      print "Loaded",len(fdf),"sample sets."

      #grouping tweets by users id
      df_gl = fdf.copy()
      fdf_dic = {}
      fdf_c = fdf.copy()
      # user_id_list = list(set(list(fdf["tweet_source_id"][:])))
      # max = 0
      # user_list = []
      # for userid in user_id_list:
      #     if userid not in user_list:
      #         fdf_pr = fdf.ix[ fdf["tweet_source_id"]==userid, : ]
      #         fdf_dic[userid] = fdf_pr
      #         if (len(fdf_pr) > 0):
      #             user_list.append(userid)
      #
      # print(len(user_list))
      # print(user_list)
          # else:fdf_c[fdf_c["user_id"] != userid]=np.nan

      output_extra_name = '_all-media'


      # dependentvar = 'above_fake_rep_med'
      # dependentvar = 'consensus_value'
      dependentvar = 'label'
      # dependentvar = 'tpb'

      for index in fdf.index.tolist():


          if fdf['label'][index]==-3:
              fdf['label'][index]=-1
          elif fdf['label'][index]==-2:
              fdf['label'][index]=-1
          elif fdf['label'][index]==-1:
              fdf['label'][index]=-1
          elif fdf['label'][index]==0:
              fdf['label'][index]=0
          elif fdf['label'][index]==1:
              fdf['label'][index]=1
          elif fdf['label'][index]==2:
              fdf['label'][index]=1
          elif fdf['label'][index]==3:
              fdf['label'][index]=1

      fdf=fdf[fdf['label']!=0]

      # for i in range(1, 8):
      #    fdf['pt_count_' + str(i)] = normalized_max_min_funct_sikitlearn(fdf['pt_count_' + str(i)])
      # for i in range(0, 100):
      #    fdf['worker_pt_' + str(i)] = normalized_max_min_funct_sikitlearn(fdf['worker_pt_' + str(i)])



      #
      fdf.loc[:,'label_tpb'] = fdf['tweet_id']*0.0

      tmp_df = fdf.sort('tpb',ascending=False)
      top_h_c = list(tmp_df['tweet_id'][:50])
      df_h_c = fdf[fdf['tweet_id'].isin(top_h_c)]
      for index in df_h_c.index.tolist():
         fdf['label_tpb'][index] = 1
      #
      top_l_c = list(tmp_df['tweet_id'][100:])
      df_l_c = fdf[fdf['tweet_id'].isin(top_l_c)]
      for index in df_l_c.index.tolist():
         fdf['label_tpb'][index] = -1


      mid_l_c = list(tmp_df['tweet_id'][50:100])
      df_l_c = fdf[fdf['tweet_id'].isin(mid_l_c)]
      for index in df_l_c.index.tolist():
         fdf['label_tpb'][index] = 0

      # fdf = fdf[fdf['tweet_id'].isin(list(top_h_c)+list(top_l_c))]

      # dependentvar = 'label_tpb'


      acc_list=[]
      corr_list=[]
      corr_pearson_list=[]

      # main_user_list = list(set(fdf['tweet_source_id']))
      # print(len(main_user_list))



      publisher_classification = {}
      for method in methods:
         for featset in featsets:
            for seed in seeds:
                outfilename = featset+"_"+inputfilenamebase+\
                  "_n%dk"%(nsamples/1000)+"-seed"+str(seed) + output_extra_name + '_based-on_'+dependentvar + '_all_publishers'
                # print(outfilename)
                np.random.seed(seed)
                random.seed(seed)
                print "Processing:", method, outfilename
                sys.stdout = open(dirs["stdout"] + "/classify_" + method + "_" + outfilename, 'w')
                count_user = 0
                # for user_m in main_user_list:
                for predict_c in range(1):
                    print("########################################################################")

                    print('kth round : ' + str(predict_c))
                    # fdf= fdf.iloc[np.random.permutation(len(fdf))]
                    fdf= fdf.iloc[shuffle(range(len(fdf)),random_state=1)]
                    print(fdf.index.tolist())

                          # fdf_c = fdf[fdf["tweet_source_id"] == user_m]
                    fdf_c = fdf.copy()
                    fdf_t = fdf.copy()
                    # fdf_t = fdf.copy()
                    # fdf_t = fdf_test.copy()

                    df, df_t, dflong, positions_train, posslices_test = preprocess(
                      method+"_"+outfilename, dirs, fdf_c,fdf_t, nsamples,dependentvar , tm_featnm=tm_featnm )
                    if len(df)==0 or len(dflong)==0 or len(positions_train)==0 or len(posslices_test)==0:
                      continue
                    print("prediction for publisher " + str(count_user) + 'th')
                    count_user += 1
                    arguments = ( outfilename, dirs, df,df_t, dflong, positions_train,
                      posslices_test, nsamples, method, featset, tm_featnm )

                      # publisher_classification[user_m] = classify( *arguments )
                    # train_liklihood, test_liklihood, publisher_classification = classify( *arguments )
                    acc, corr, corr_pearson = classify( *arguments )
                    acc_list.append(acc)
                    corr_list.append(corr[0][1])
                    corr_pearson_list.append(corr_pearson[0])


             # if featsets[0] == "tweet_text":
          # df_t.to_csv(output, columns=df_t.columns, sep="\t", index=False)

      print("########################################################################")
      print("########################################################################")
      print("########################################################################")
      print('avg acc : ' + str(np.mean(acc_list)))
      print('avg corr : ' + str(np.mean(corr_list)))
      print('avg corr spearman : ' + str(np.mean(corr_pearson_list)))
      print("########################################################################")
      print("########################################################################")
      print("########################################################################")
      slowdown = 1.0*args.timeout/len(methods)/5.0
      print "Slowdown by:", slowdown
      # time.sleep(slowdown)


if __name__ == '__main__':

    main()
