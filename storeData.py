import pandas as pd
import yfinance as yf
from dataScraper import dataObject
from datetime import timedelta, datetime

df = pd.DataFrame(columns=['index', 'open', 'close', 'high', 'low'])
file = 'data.csv'
df.to_csv(file)
candleInterval = 1
data = yf.download(tickers = 'SPY', period = '5d', interval = '1m')

newData = dataObject()

startTime = timedelta(hours = 9, minutes = 30)
endTimeToday = timedelta(hours = 16)
endMarketTime = timedelta(hours = 16)

numIndexMarket = (endMarketTime - startTime).seconds //  60 // candleInterval
numIndexToday = (((endTimeToday - startTime).seconds //  60) // candleInterval) % numIndexMarket


def calculateSize(data, candleInterval, upperTimeBound):
    dates = dict()
    for i in data.index:
        j = datetime(i.year, i.month, i.day)
        if j in dates:
            dates[j] += 1
        else:
            dates[j] = 1
    fullDaysIndexes = (len(dates.keys()) - 1) * 390 // candleInterval
    lastTime = upperTimeBound
    lastDayIndexes = (lastTime - timedelta(hours = 9, minutes = 30)).seconds // 60 // candleInterval
    return fullDaysIndexes + lastDayIndexes

# reset the index
size = calculateSize(data, candleInterval, datetime(datetime.now().year, datetime.now().month, datetime.now().day - 1) + timedelta(hours = 16))
numFullDays = size // numIndexMarket
# print(numFullDays)
for i in range(numFullDays):
    day = datetime(data.index[i * numIndexMarket].year,
            data.index[i * numIndexMarket].month,
            data.index[i * numIndexMarket].day)
    arr = [(day + startTime + timedelta(minutes = candleInterval * j)) for j in range(numIndexMarket)]
    newData.concatenateIndex(arr)


