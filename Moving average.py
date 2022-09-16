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
