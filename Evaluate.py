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
