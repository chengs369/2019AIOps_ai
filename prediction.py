import os.path as pth
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import KMeans
from conf import *
import numpy as np


def prediction_by_different_classifier(df, abnrm_ts_f_pth=None):
    X_test = get_abnrm_ts(abnrm_ts_f_pth)
    clf = RandomForestClassifier(max_depth=15, n_estimators=10, max_features=1)
    r_count, _ = df.shape
    X_train = df['timestamp'].values.reshape(-1, 1)
    y_train = df['t_value'].values
    try:
        clf.fit(X_train, y_train)
        X_test = X_train if not abnrm_ts_f_pth else X_test
        predictions = clf.predict(X_test)
        return pd.Series(predictions, index=X_test.ravel())
    except Exception, ex:
        print 'Error: %s' % ex.message


def get_abnrm_ts(abnrm_ts_f_pth=None):
    if not abnrm_ts_f_pth:
        return None
    else:
        abnrm_ts_df = pd.read_csv(abnrm_ts_f_pth)
        return abnrm_ts_df['timestamp'].values.reshape(-1, 1)


def prediction_l1_values(f_path=pth.join('rundata', 'l1_value_output'), abnrm_ts_f_pth=None):
    X_test = get_abnrm_ts(abnrm_ts_f_pth)

    for attri in ORIGIN_ATTRIS:
        df = pd.read_csv(pth.join(f_path, '{}_values.csv'.format(attri)), index_col='timestamp')
        for item in df.columns:
            clf = RandomForestClassifier(max_depth=15, n_estimators=10, max_features=1)
            item_df = df[item].dropna()
            X_train = item_df.index.values.reshape(-1, 1)
            y_train = item_df.values.ravel()
            try:
                clf.fit(X_train, y_train)
                X_test = X_train if not abnrm_ts_f_pth else X_test
                predictions = clf.predict(X_test)
                # df = df.append(pd.Series(predictions, index=X_test.ravel(), name='{}_prediction'.format(item)))
                df['{}_prediction'.format(item)] = pd.Series(predictions, index=X_test.ravel())
                # print df.head()
            except Exception, ex:
                print 'Error: %s' % ex.message
        if abnrm_ts_f_pth:
            df = df.loc[X_test.ravel()]
        df.to_csv(pth.join(f_path, '{}_values_with_pre.csv'.format(attri)))
        # break
    pass


def test_stationarity(ts):
    dftest = adfuller(ts)
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
    for key, value in dftest[4].items():
        dfoutput['Critical Value (%s)' % key] = value
    return dfoutput


def rmse(pre_ts, ts):
    return np.sqrt(sum((pre_ts - ts) ** 2) / ts.size)


def prediction_t_values(f_pth, abnrm_ts_f_pth):
    print 'do prediction t value in {}'.format(f_pth)
    try:
        origin_df = pd.read_csv(pth.join(f_pth, 'origin_t_values.csv'), index_col='timestamp')
        test_df = pd.read_csv(pth.join(f_pth, 'test_t_values.csv'), index_col='timestamp')
        anm_df = pd.read_csv(abnrm_ts_f_pth)
        df = test_df.loc[anm_df['timestamp'].tolist()]
        # df = origin_df
        # df = test_df

        # clf = RandomForestClassifier(max_depth=15, n_estimators=10, max_features=1)
        # X_train = origin_df.index.values.reshape(-1, 1)
        # y_train = origin_df['t_value'].values
        # clf.fit(X_train, y_train)
        # X_test = df.index
        # predictions = clf.predict(X_test.values.reshape(-1, 1))
        # print predictions
        # df['t_value_pre'] = pd.Series(predictions, index=X_test)

        dta = origin_df.append(test_df)
        # df = dta
        dta.index = pd.to_datetime(dta.index, unit='ms')
        ts = dta['t_value']
        print test_stationarity(ts)

        # ts = np.log(ts)

        # size = 12
        # size = 12 * 2
        # size = 12 * 3
        # size = 12 * 5
        size = 12 * 10
        ts = ts.rolling(window=size).mean()
        # ts = pd.ewma(ts, span=size)
        ts.dropna(inplace=True)

        arma_mod = sm.tsa.ARMA(ts, order=(1, 1)).fit(disp=-1, method='css')
        # df['t_value_pre'] = df.apply(lambda r: r[index], axis=1)
        predictions = arma_mod.predict()

        # predictions = np.exp(predictions)
        # predictions.dropna(inplace=True)

        ts = ts[predictions.index]
        print 'RMSE: {}'.format(rmse(predictions, ts))
        # print predictions
        # print df.head()

        df.index = pd.to_datetime(df.index, unit='ms')
        df['t_value_pre'] = predictions[df.index]
        df['t_value_pre_dev'] = df['t_value'] - df['t_value_pre']

        # print df.describe()
        df.to_csv(pth.join(f_pth, 't_values_with_pre.csv'))
        # print df.head(20)
        # print df.tail()
        # print df.describe()
    except Exception, ex:
        print 'Error: %s' % ex.message


def cluster_abnormal_ts():
    df = pd.read_csv(pth.join('rundata', 'abnormal_timestamp.csv'))
    K = range(2, 10)
    for k in K:
        clf = KMeans(n_clusters=k)
        print 'n_clusters: {}'.format(k)
        clf_pre = clf.fit_predict(df['timestamp'].reshape(-1, 1))
        print clf_pre
        # break
    pass


if __name__ == '__main__':
    # prediction_t_values()
    # prediction_l1_values()
    cluster_abnormal_ts()
    pass
