from Function import get_zhangdieting_price ,get_data_from_akshare
from Signal import get_moving_average_signal
from Position import get_position
from Evaluate import equity_curve_close
import pandas as pd
import tushare as ts
import akshare as ak
import datetime
import time
from time import strftime

pd.set_option('expand_frame_repr', False)   #列太多时不换行
pd.set_option('display.max_rows', 5000)     #显示5000行

#准备基本参数 
para = [40,82]
symbol = '002131'
start_date = '20170101'
end_date = time.strftime("%Y%m%d")
#Get data
df = get_data_from_akshare(symbol,start_date,end_date)
df = get_zhangdieting_price(df)

#Get Signal
df = get_moving_average_signal(df,para=para)
#print(df[df['signal']==1])
#print(df[df['signal']==0])
#print(df['signal'].value_counts())

#Get position
df = get_position(df)

#Get equity curve
df = equity_curve_close(df, c_rate=2.5/10000, t_rate=1.0/1000,slippage=0.01)
print(df)
equity_curve = df.iloc[-1]['equity_curve']
equity_curve_base = df.iloc[-1]['equity_curve_base']
print(para, '策略最终收益：', equity_curve)




#Function

import akshare as ak
import pandas as pd
import numpy as np
import datetime
from decimal import Decimal, ROUND_HALF_UP
def get_data_from_akshare(symbol,start_date,end_date,):
    df= ak.stock_zh_a_hist(symbol, period="daily",start_date = start_date ,end_date= end_date, adjust="")
    df.rename(columns = {'日期':'交易日期','开盘':'开盘价','最高':'最高价','最低':'最低价','收盘':'收盘价'},inplace=True)
    df=df[['交易日期','开盘价','最高价','最低价','收盘价']]
    df['前收盘价']=df['收盘价'].shift()
    df.dropna(inplace=True)                       
    df.reset_index(inplace=True, drop=True)   

    return df


def get_zhangdieting_price(df):
    """
    计算股票涨跌停价格，在计算的时候应按照严格的四舍五入。
    计算涨跌停价格可以帮助我们排除不能开平仓的情况。
    
    """
    #计算涨跌停价格
    df['涨停价'] = df['前收盘价'] * 1.1
    df['跌停价'] = df['前收盘价'] * 0.9
    df['涨停价'] = df['涨停价'].apply(lambda x: float(Decimal(x * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 100))
    df['跌停价'] = df['跌停价'].apply(lambda x: float(Decimal(x * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 100))

    return df


#Signal

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
    condition2 = df['ma_short'].shift(1) <= df['ma_long'].shift(1)
    df.loc[condition1 & condition2, 'signal'] = 1

    #Find signal close long
    condition1 = df['ma_short'] < df['ma_long']
    condition2 = df['ma_short'].shift() >= df['ma_long'].shift(1)
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


  
 
 #Position
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
"""

由signal产生的信号进行持仓
避免未来函数
考虑涨跌停无法买入情况


"""

def get_position(df):
    #Find position
    df['signal'].fillna(method='ffill', inplace = True)
    df['signal'].fillna(value = 0, inplace= True)
    df['pos'] = df['signal'].shift()                
    df['pos'].fillna(value = 0, inplace = True)
   
    #Can not buy condition
    cannot_buy_condition = df['收盘价'] >=  df['涨停价'] 
    df.loc[cannot_buy_condition.shift() & (df['signal'].shift() == 1), 'pos'] = None

    #can not sell condition
    cannot_sell_condition = df['收盘价'] <= df['跌停价']
    df.loc[cannot_sell_condition.shift() & (df['signal'].shift() == 0), 'pos'] = None
 
    #当pos为None时不能买卖，保持上一周期一致
    df['pos'].fillna(method='ffill',inplace= True)
    
    #删除无关变量
    df.drop(['signal'], axis=1, inplace=True)

    return df


#Evaluate

import pandas as pd
import numpy as np
pd.set_option('display.max_rows',5000)
pd.set_option('expand_frame_repr',False)
"""
交易以当天收盘价为准 
设置滑点slippage
股票数量以手为单位
c_rate:手续费 commission fees 默认万2.5
t_rate:印花税 默认千分之一
slippage:滑点 股票默认0.01 ;etf默认0.001
"""
#股票资金曲线
def equity_curve_close(df, c_rate=2.5/10000, t_rate=1.0/1000,slippage=0.01):
    #找出开仓条件
    condition1 = df['pos'] != 0
    condition2 = df['pos'] != df['pos'].shift()
    open_condition = condition1 & condition2
    #找出平仓条件
    condition1 = df['pos'] != 0
    condition2 = df['pos'] != df['pos'].shift(-1)
    close_condition = condition1 & condition2

    #对每次交易进行分组
    df.loc[open_condition, 'start_time'] = df['交易日期']
    df['start_time'].fillna(method='ffill', inplace = True)
    df.loc[df['pos'] == 0, 'start_time'] = pd.NaT

    #基本参数
    initial_cash = 1000000   
    
    #发出信号以收盘价买入
    df.loc[open_condition,'stock_num'] = initial_cash * (1-c_rate)/(df['前收盘价'] + slippage)

    #实际买入数量
    df['stock_num'] = np.floor(df['stock_num'] / 100) * 100

    #买入后剩余的cash 扣除手续费
    df['cash'] = initial_cash - df['stock_num'] * (df['前收盘价'] + slippage) * (1 + c_rate)
    
    #收盘时的个票净值
    df['stock_value'] = df['stock_num'] * df['收盘价']

    #买入之后现金不在发生变化
    df['cash'].fillna(method= 'ffill', inplace =True)
    df.loc[df['pos'] == 0,['cash']] = None

    #股票净值随着涨幅波动
    group_num = len(df.groupby('start_time'))
    if group_num > 1:
        t = df.groupby('start_time').apply(lambda x:x['收盘价'] / x.iloc[0]['收盘价'] * x.iloc[0]['stock_value'])
        t = t.reset_index(level=[0])
        df['stock_value'] = t['收盘价']
    elif group_num == 1:
        t = df.groupby('start_time')[['收盘价','stock_value']].apply(lambda x:x['收盘价']/x.iloc[0]['收盘价'] * x.iloc[0]['stock_value'])
        df['stock_value'] = t.T.iloc[:,0]

    #卖出时股票数量的变动
    df.loc[close_condition,'stock_num'] = df['stock_value'] / df['收盘价']

    #现金变动
    df.loc[close_condition,'cash'] += df.loc[close_condition,'stock_num'] * (df['收盘价'] - slippage) * (1 - c_rate - t_rate)

    #股票价值变动
    df.loc[close_condition,'stock_value'] = 0

    #账户净值
    df['net_value'] = df['stock_value'] + df['cash']

    #计算资金曲线
    df['equity_change'] = df['net_value'].pct_change(fill_method = None)
    df.loc[open_condition,'equity_change'] = df.loc[open_condition,'net_value'] / initial_cash - 1
    df['equity_change'].fillna(value = 0, inplace=True)
    df['equity_curve'] = (1 + df['equity_change']).cumprod() 
    df['equity_curve_base'] = (df['收盘价'] / df['前收盘价']).cumprod()
    
    #删除不相关数据
    df.drop(['start_time', 'stock_num', 'cash', 'stock_value', 'net_value'], axis=1, inplace=True)

    return df


#参数寻优

from Function import get_zhangdieting_price ,get_data_from_akshare
from Signal import get_moving_average_signal, moving_average_para_list
from Position import get_position
from Evaluate import equity_curve_close
from Sheet import save_data_to_csv
import pandas as pd
import akshare as ak
import time
import json
from time import strftime

#准备基本参数 
symbol = 'hd300'
stock_name = '沪深300'
start_date = '20180101'
end_date = time.strftime("%Y%m%d") #运行当天

#获取数据
df = get_data_from_akshare(symbol,start_date,end_date)
df = get_zhangdieting_price(df)

# 构建策略参数遍历范围
para_list = moving_average_para_list(ma_short=range(10,200,2), ma_long=range(10,200,2))

#遍历参数
rtn= pd.DataFrame()
for para in para_list:
    # 计算策略交易信号，此处df需要copy
    temp_df = get_moving_average_signal(df.copy(), para=para)
     # 计算实际持仓
    temp_df = get_position(temp_df)
    # 计算资金曲线
    temp_df = equity_curve_close(temp_df, c_rate=2.5/10000, t_rate=1.0/1000, slippage=0.01)
    # 计算收益
    equity_curve = temp_df.iloc[-1]['equity_curve']
    equity_curve_base = temp_df.iloc[-1]['equity_curve_base']
    #print(para, '策略最终收益：', equity_curve)
    
    rtn.loc[str(para), 'equity_curve'] = equity_curve
    rtn.loc[str(para), 'equity_curve_base'] = equity_curve_base

#print(rtn.sort_values(by='equity_curve', ascending=True))
rtn_list = rtn.sort_values(by='equity_curve', ascending=True)
opt_para = str(rtn_list.index[-1])
startegy_rtn = float(rtn_list.values[-1][0].round(3))
stock_rtn = float(rtn_list.values[-1][1].round(3))
#fin_rtn = rtn_list.values[-1].round(3)
print(rtn_list)
print(f'\n*********************\n{symbol}:{stock_name}\n股票收益: {stock_rtn}\n\
策略收益: {startegy_rtn}\n最优参数为: {opt_para}\n*********************')
