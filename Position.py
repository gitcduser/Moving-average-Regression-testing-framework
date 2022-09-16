from cmath import nan
import pandas as pd
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
"""

由signal产生的信号进行持仓
避免未来函数
考虑涨跌停无法买入情况


"""

def get_position_close(df):
    #Find position
    df['signal'].fillna(method = 'ffill', inplace = True)
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




