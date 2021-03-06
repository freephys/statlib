from datetime import datetime
import os
import re

import numpy as np
import pandas as pn

data_path = 'statlib/data'

def table_33():
    path = os.path.join(data_path, 'Table3.3.data.txt')
    sep = '\s+'

    lines = [re.split(sep, l.strip()) for l in open(path)]

    y_data = []
    f_data = []
    saw_f = False
    for line in lines:
        if line[0] == 'Y':
            continue
        elif line[0] == 'F':
            saw_f = True
            continue

        # drop year
        if saw_f:
            f_data.extend(line[1:])
        else:
            y_data.extend(line[1:])

    y_data = np.array(y_data, dtype=float)
    f_data = np.array(f_data, dtype=float)

    dates = pn.DateRange(datetime(1975, 1, 1), periods=len(y_data),
                         timeRule='Q@MAR')

    Y = pn.Series(y_data, index=dates)
    F = pn.Series(f_data, index=dates)

    return Y, F

def table_22():
    """
    Gas consumption data
    """
    path = os.path.join(data_path, 'table22.csv')
    return pn.read_csv(path, header=None)['X.2']

def table_81():
    """
    Gas consumption data
    """
    path = os.path.join(data_path, 'table81.csv')
    return pn.read_csv(path, header=None)['X.2']

def table_102():
    path = os.path.join(data_path, 'table102.csv')
    return pn.read_csv(path)

def table_111():
    path = os.path.join(data_path, 'table111.csv')
    return pn.read_csv(path)['CP6']

def foo():
    path = os.path.join(data_path, 'Table11.1.data.txt')
    sep = '\s+'

    lines = [re.split(sep, l.strip()) for l in open(path)]

    datad = {}
    for start in [0]:
        name = lines[start][0]
        time_rule = lines[start + 1][0]
        start_date = lines[start + 2][0]
        data = np.concatenate(lines[start + 3:start+9]).astype(float)
        dates = pn.DateRange(start_date, periods=len(data), timeRule=time_rule)
        datad[name] = pn.Series(data, index=dates)

    return pn.DataFrame(datad)

def eeg400_data():
    """
    Cz series, 400 data points
    """
    data = open(os.path.join(data_path, 'eeg.dat')).read().strip()
    data = re.sub('[\s\n]+', ' ', data).split()
    return np.array(data, dtype=float)

def eeg_Cz():
    """
    Cz series
    """
    data = open(os.path.join(data_path, 'eegCz.dat')).read().strip()
    data = re.sub('[\s\n]+', ' ', data).split()
    return np.array(data, dtype=float)

def eeg_data():
    """
    Cz series, 3600 data points
    """
    return np.loadtxt('statlib/data/eeg2.dat')

def parse_table_22():
    path = os.path.join(data_path, 'Table2.2.data.txt')
    sep = '\s+'

    lines = [re.split(sep, l.strip()) for l in open(path)]

    data = []
    for line in lines:
        # drop year
        data.extend(line[1:])

    data = np.array(data, dtype=float) / 100
    dates = pn.DateRange(datetime(1975, 1, 1), periods=len(data),
                         timeRule='EOM')

    return pn.Series(data, index=dates)

def fx_gbpusd():
    path = os.path.join(data_path, 'GBPUSD_FX.txt')
    return np.loadtxt(path, delimiter=',')

def fx_yenusd():
    path = os.path.join(data_path, 'YENUSD_FX.txt')
    return np.loadtxt(path, delimiter=',')

_rates_cols = ['AUD', 'BEF', 'CAD', 'FRF', 'DEM', 'JPY',
               'NLG', 'NZD', 'ESP', 'SEK', 'CHF', 'GBP']
_start_date = datetime(1986, 10, 1)

def fx_rates_spot():
    path = os.path.join(data_path, 'spot_exrates.dat')
    data = np.loadtxt(path)
    index = pn.DateRange(_start_date, periods=len(data))
    return pn.DataMatrix(data, index=index, columns=_rates_cols)

def fx_rates_returns():
    path = os.path.join(data_path, 'returns_exrates.dat')
    data = np.loadtxt(path)
    index = pn.DateRange(_start_date, periods=len(data))
    return pn.DataMatrix(data, index=index, columns=_rates_cols)

