import pandas as pd
import numpy as np
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
"""

计算移动平均策略交易信号
短期均线上穿长期均线时做多；
短期均线下穿长期均线时平仓；

"""

def get_moving_average_signal(df,para):
    ma_short = para[0]
    ma_long = para[1]
    
    #Calculate MA
    df['ma_short'] = df['收盘价'].rolling(ma_short,min_periods=1).mean()
    df['ma_long'] = df['收盘价'].rolling(ma_long,min_periods=1).mean()
    
    #Find signal open long
    condition1 = df['ma_short'] > df['ma_long']
    condition2 = df['ma_short'].shift() <= df['ma_long'].shift()
    df.loc[condition1 & condition2, 'signal'] = 1

    #Find signal close long
    condition1 = df['ma_short'] < df['ma_long']
    condition2 = df['ma_short'].shift() >= df['ma_long']
    df.loc[condition1 & condition2, 'signal'] = 0

    #Drop independent variable
    df.drop(['ma_short','ma_long'],axis=1,inplace=True)

    return df


#参数寻优
"""
寻找最优的策略参数

"""
def moving_average_para_list(ma_short=range(10, 200,2), ma_long=range(10, 250,2)):
    para_list = []
    for short in ma_short:
        for long in ma_long:
            if short >= long:
                continue
            else:
                para_list.append([short, long])
    
    return para_list

