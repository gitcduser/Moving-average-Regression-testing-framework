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


