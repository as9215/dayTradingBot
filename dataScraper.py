"""
Purpose:
Scrapes the data from the yahoo finance package and plots it as a candlestick graph. Rectifies
and alters the data as needed. This is the main class so it will call from other classes to 
establish the sma and resistance lines, along with the sql function and the boolean decision 
whether to buy or sell
"""

"""
IDEAS / TO-DO:
alter for calls and puts
maybe look at best times of day to invest ???
(prob not) maybe look at how long to stay in a trade for
if there is a good strategy for one week, how does that relate to the week after that
or check the month by month
"""

# Raw Package
from time import time
import numpy as np
import pandas as pd
import math
from sqlalchemy import create_engine
from EnterExitEval import bestFitSlope

#Data Source
import yfinance as yf

#Data viz
import plotly.graph_objs as go

# Import datetime
from datetime import datetime, timedelta, date

# Import separate classes
import smaCalculator
import trendLineGen
from EnterExitEval import evaluator

class sqlObject:
    enter = 0
    exit = 0
    priceChange = 0
    candleInterval = 0
    resistanceLines = 0
    resistanceLinesSlopes = []
    resistanceLinesDiff = 0
    resistanceLinesDiffSlopes = []
    resistanceLinesBroke = 0
    resistanceLinesBrokeSlopes = []
    time = datetime(2000,2,2) + timedelta(hours = 0, minutes = 0)
    exitTime = datetime(2000,2,2) + timedelta(hours = 0, minutes = 0)
    intervalShortSma = 0
    intervalLongSma = 0
    deltaShortSmaLongSma = 0
    enterShortSmaSlope = 0
    enterLongSmaSlope = 0
    enterRSI = 0
    RSIposMomentum = 0
    RSInegMomentum = 0
    callPut = 'c'
    exitShortSmaSlope = 0
    exitLongSmaSlope = 0
    exitShortLongSmaDiff = 0
    exitRsi = 0
    exitShortPositiveRsiMomentum = 0
    exitShortNegativeRsiMomentum = 0
    exitPositiveRsiMomentum = 0
    exitNegativeRsiMomentum = 0
    exitRsiShortChange = 0
    exitRsiOverallChange = 0
    percentGreen = 0
    averageGain = 0
    numEntries = 1

class dataObject:
    index = []
    high = []
    low = []
    open = []
    close = []

    def concatenateIndex(self, indexList):
        self.index = self.index + indexList

    def concatenateHigh(self, highList):
        self.high = self.high + highList

    def concatenateLow(self, lowList):
        self.low = self.low + lowList

    def concatenateOpen(self, openList):
        self.open = self.open + openList

    def concatenateClose(self, closeList):
        self.close = self.close + closeList

def upperTimeBoundGen(date1):
    today = date(date1.year, date1.month, date1.day)
    time = timedelta(hours = date1.hour, minutes = date1.minute)
    if time < timedelta(hours = 9):
        date1 = date1 - timedelta(hours = 24)
        today = date(date1.year, date1.month, date1.day)
        time = timedelta(hours = 16)
    while today.weekday() > 4:
        date1 = date1 - timedelta(hours = 24)
        today = date(date1.year, date1.month, date1.day)
    if time > timedelta(hours = 16):
        time = timedelta(hours = 16)
    today = datetime(today.year, today.month, today.day) + time
    return today

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

def customCandleInterval(data, candleInterval):
    newData = dataObject()
    for i in range(len(data.index) // candleInterval):
        high = 0
        low = 1000
        newData.concatenateIndex([data.index[i * candleInterval]])
        for j in range(candleInterval):
            if high < data.high[i * candleInterval + j]:
                high = data.high[i * candleInterval + j]
            if low > data.low[i * candleInterval + j]:
                low = data.low[i * candleInterval + j]
            if j == 0:
                newData.concatenateOpen([data.open[i * candleInterval + j]])
            if j == candleInterval - 1:
                newData.concatenateClose([data.close[i * candleInterval + j]])
        newData.concatenateHigh([high])
        newData.concatenateLow([low])
    return newData

def rectifyData(data, candleInterval, upperTimeBound):
    newData = dataObject()

    startTime = timedelta(hours = 9, minutes = 30)
    endTimeToday = upperTimeBound
    endMarketTime = timedelta(hours = 16)

    numIndexMarket = (endMarketTime - startTime).seconds //  60 // candleInterval
    numIndexToday = (((endTimeToday - startTime).seconds //  60) // candleInterval) % numIndexMarket

    # reset the index
    size = calculateSize(data, candleInterval, upperTimeBound)
    numFullDays = size // numIndexMarket
    # print(numFullDays)
    for i in range(numFullDays):
        day = datetime(data.index[i * numIndexMarket].year,
                data.index[i * numIndexMarket].month,
                data.index[i * numIndexMarket].day)
        arr = [(day + startTime + timedelta(minutes = candleInterval * j)) for j in range(numIndexMarket)]
        newData.concatenateIndex(arr)
    
    startIndex = numFullDays * numIndexMarket
    # print(len(data.index), "\t", startIndex + numIndexToday, "\n\n\n")
    for i in range(numIndexToday):
        day = datetime(data.index[startIndex].year,
                data.index[startIndex].month,
                data.index[startIndex].day)
        arr = [day + startTime + timedelta(minutes = candleInterval * i)]
        newData.concatenateIndex(arr)
    
    # reset the high/low/open/close
    j = 0
    for i in range(len(newData.index)):
        # repeat = False
        if len(data.index) > (i - j):
            curr = datetime(data.index[i - j].year, data.index[i - j].month, data.index[i - j].day) + timedelta(hours = data.index[i - j].hour, minutes = data.index[i - j].minute)
            # repeat = True
        if (newData.index[i] != curr):
            j += 1
        newData.concatenateHigh([data['High'][i - j]])
        newData.concatenateLow([data['Low'][i - j]])
        newData.concatenateOpen([data['Open'][i - j]])
        newData.concatenateClose([data['Close'][i - j]])
    return newData

def adjustData(data, cutLength):
    data.open = data.open[:len(data.open) - cutLength]
    data.close = data.close[:len(data.close) - cutLength]
    data.high = data.high[:len(data.high) - cutLength]
    data.low = data.low[:len(data.low) - cutLength]
    data.index = data.index[:len(data.index) - cutLength]

    marketHourIndexes = (timedelta(hours = 6, minutes = 30)).seconds // 60
    fullDays = len(data.index) // marketHourIndexes
    partialDays = 0
    if (len(data.index) % marketHourIndexes) != 0:
        partialDays = 1
    days = fullDays + partialDays
    startIndex = (days - 1) * marketHourIndexes
    dataShort = dataObject()
    dataShort.open = data.open[startIndex:len(data.open)]
    dataShort.close = data.close[startIndex:len(data.close)]
    dataShort.high = data.high[startIndex:len(data.high)]
    dataShort.low = data.low[startIndex:len(data.low)]
    dataShort.index = data.index[startIndex:len(data.index)]

    return data, dataShort

def createLongSma(dataSma, intervalSma2, upperDateTime, candleInterval):
    valSma2 = smaCalculator.createList(upperDateTime, candleInterval, intervalSma2, dataSma)
    return valSma2

# might add data, uppertimebound, interval sma, and upperDateTime into para. also the object to be changed
def createPlot(dataSma, dataVisual, intervalSma1, intervalSma2, upperDateTime, candleInterval, buffer):
    # candleInterval = 3
    dataSma = customCandleInterval(dataSma, candleInterval)
    dataVisual = customCandleInterval(dataVisual, candleInterval)

    # initialize the data figure
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(x=dataVisual.index,
                    open=dataVisual.open,
                    high=dataVisual.high,
                    low=dataVisual.low,
                    close=dataVisual.close, 
                    name = 'market data'))

    # Add titles
    fig.update_layout(
        title = 'SPY live data',
        yaxis_title ='Stock Price (USD per Shares)')

    # X-Axes
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=15, label="15m", step="minute", stepmode="backward"),
                dict(count=45, label="45m", step="minute", stepmode="backward"),
                dict(count=1, label="HTD", step="hour", stepmode="todate"),
                dict(count=3, label="3h", step="hour", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    valSma1 = smaCalculator.createList(upperDateTime, candleInterval, intervalSma1, dataSma)
    valSma2 = smaCalculator.createList(upperDateTime, candleInterval, intervalSma2, dataSma)

    fig.add_trace(go.Scatter(x = dataVisual.index, y = valSma1, mode = 'lines', name = "sma " + str(intervalSma1)))
    fig.add_trace(go.Scatter(x = dataVisual.index, y = valSma2, mode = 'lines', name = "sma " + str(intervalSma2)))

    resistancePlot = trendLineGen.mapResistancePoints(buffer, dataVisual, candleInterval, upperDateTime)
    for i in resistancePlot:
        fig.add_trace(go.Scatter(x = i['x'], y = i['y'], mode = 'lines', name = "resistance Line"))
    # show the graph
    # fig.show()
    return dataSma, valSma1, valSma2, resistancePlot

def alterPut(data):
    for i in range(len(data.index)):
        data.high[i] = 1000 - data.high[i]
        data.low[i] = 1000 - data.low[i]
        data.open[i] = 1000 - data.open[i]
        data.close[i] = 1000 - data.close[i]
    return data

def exec():
    # parameters
    # currTimeIteration = datetime.now()
    database_username = 'root'
    database_password = 'February2001!'
    database_ip       = 'localhost'
    database_name     = 'stockanalysis'
    database_connection = create_engine('mysql+mysqlconnector://{0}:{1}@{2}/{3}'.
    format(database_username, database_password, database_ip, database_name))

    # c = mydb.cursor()
    # c.execute("USE STOCKANALYSIS;")
    indexProg = []
    currentlyIn = False
    candleIntervalOrig = 1
    candleInterval = 3
    buffer = 0.0100
    df = pd.DataFrame(columns=['enter',
'candle interval',
'resistance lines',
'resistance lines slopes',
'resistance lines diff',
'resistance lines diff slopes',
'resistance lines broke',
'resistance lines broke slopes',
'time',
'exit time',
'interval short sma',
'interval long sma',
'enter short sma slope',
'enter long sma slope',
'short long sma difference',
'enter RSI',
'positive RSI momentum',
'negative RSI momentum',
'RSI change',
'call or put',
'exit',
'price change',
'exit short sma slope',
'exit long sma slope',
'exit short long sma difference',
'exit RSI',
'exit short positive RSI momentum',
'exit short negative RSI momentum',
'exit positive RSI momentum',
'exit negative RSI momentum',
'exit RSI short change',
'exit RSI overall change',
'percent green',
'average gain',
'number of entries'])
    file = 'existing_data.csv'
    df.to_csv(file, index = False)
    # df.to_sql(con=database_connection, name = 'analysis',if_exists='replace', index=False)

    resYList = []
    # timeNow = upperTimeBoundGen(datetime.now())
    # time = timedelta(hours = timeNow.hour, minutes = timeNow.minute)
    # Object to be managed
    objManaged = sqlObject()

    indexesToday = (timedelta(hours = 16) - timedelta(hours = 9, minutes = 30)).seconds//60//candleInterval
    dataSmaOrig = yf.download(tickers = 'SPY', period = '5d', interval = str(candleIntervalOrig) + "m")
    upperDateTimeOrig = datetime(dataSmaOrig.index[len(dataSmaOrig.index) - 1].year, dataSmaOrig.index[len(dataSmaOrig.index) - 1].month, dataSmaOrig.index[len(dataSmaOrig.index) - 1].day) + timedelta(hours = 16)
    k = timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval

    continueAlter = False
    for i in range(k*4 - 1, -1, -1):
        dataSma = dataSmaOrig
        # upperDateTime = datetime(lastLogTime.year, lastLogTime.month, lastLogTime.day) + timedelta(hours = 16) - timedelta(minutes = candleInterval * i)
        upperDateTime = upperDateTimeOrig
        
        # upperDateTime = dataSma.index[len(dataSma.index) - 1 - candleInterval * i] # + timedelta(minutes = 2)
        dataSma = rectifyData(dataSma, candleIntervalOrig, timedelta(hours = upperDateTime.hour, minutes = upperDateTime.minute))

        dataSma, dataVisual = adjustData(dataSma, candleInterval * i)

        upperDateTime = dataSma.index[len(dataSma.index) - 1] + timedelta(minutes = candleInterval)
        # upperDateTime = upperDateTimeOrig - timedelta(minutes = candleInterval* i)

        intervalSmaShort = 27 // candleInterval
        intervalSmaLong = 540 // candleInterval

        # create plot has a parameter of the candle Interval

        # Have this return all the parameters for should enter and should exit, and the values to insert to the object
        # store all the dataobj in a dictionary with the candleinterval, and short and long sma as the primary keys
        # dont update sql until data close is filled
        longDataCopy = dataSma
        shortDataCopy = dataVisual
        longSma = createLongSma(longDataCopy, intervalSmaLong, upperDateTime, candleInterval)
        
        # alter data if lining up for a put
        slopeDiff = 30 // candleInterval
        slope = bestFitSlope(dataSma.index[len(dataSma.index) - slopeDiff:], longSma[len(longSma) - slopeDiff:])
        if (slope < 0 and not currentlyIn) or (continueAlter == True and currentlyIn):
            dataSma = alterPut(dataSma)
            dataVisual = alterPut(dataVisual)
            objManaged.callPut = 'p'
            continueAlter = True
            
        longDataCopy = dataSma
        shortDataCopy = dataVisual
        data, shortSma, longSma, resY = createPlot(longDataCopy, shortDataCopy, intervalSmaShort, intervalSmaLong, upperDateTime, candleInterval, buffer)
        
        resYList.append(resY)
        print("time:", data.index[len(data.index) - 1], "\t", "upperDateTime:", upperDateTime)

        objManaged, currentlyIn = evaluator(objManaged, currentlyIn, data, shortSma, longSma, resY, candleInterval, intervalSmaShort, intervalSmaLong, resYList, upperDateTime)
        print("currentlyIn:", currentlyIn, "\t", "data.close:", len(data.close) % (timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval))
        if objManaged.exit != 0 and not currentlyIn:
            data1 = {'enter': objManaged.enter,
            'candle interval': objManaged.candleInterval,
            'resistance lines': objManaged.resistanceLines,
            'resistance lines slopes': objManaged.resistanceLinesSlopes,
            'resistance lines diff': objManaged.resistanceLinesDiff, 
            'resistance lines diff slopes': objManaged.resistanceLinesDiffSlopes,
            'resistance lines broke': objManaged.resistanceLinesBroke,
            'resistance lines broke slopes': objManaged.resistanceLinesBrokeSlopes,
            'time': objManaged.time,
            'exit time': objManaged.exitTime,
            'interval short sma': objManaged.intervalShortSma,
            'interval long sma': objManaged.intervalLongSma,
            'enter short sma slope': objManaged.enterShortSmaSlope,
            'enter long sma slope': objManaged.enterLongSmaSlope,
            'short long sma difference': objManaged.deltaShortSmaLongSma,
            'enter RSI': objManaged.enterRSI,
            'positive RSI momentum': objManaged.RSIposMomentum,
            'negative RSI momentum': objManaged.RSInegMomentum,
            'RSI change': objManaged.RSIposMomentum - objManaged.RSInegMomentum,
            'call or put': objManaged.callPut,
            'exit': objManaged.exit, 
            'price change': objManaged.priceChange,
            'exit short sma slope': objManaged.exitShortSmaSlope,
            'exit long sma slope': objManaged.exitLongSmaSlope,
            'exit short long sma difference': objManaged.exitShortLongSmaDiff,
            'exit RSI': objManaged.exitRsi,
            'exit short positive RSI momentum': objManaged.exitShortPositiveRsiMomentum,
            'exit short negative RSI momentum': objManaged.exitShortNegativeRsiMomentum,
            'exit positive RSI momentum': objManaged.exitPositiveRsiMomentum,
            'exit negative RSI momentum': objManaged.exitNegativeRsiMomentum,
            'exit RSI short change': objManaged.exitRsiShortChange,
            'exit RSI overall change': objManaged.exitRsiOverallChange,
            'percent green': objManaged.percentGreen,
            'average gain': objManaged.averageGain,
            'number of entries': objManaged.numEntries}
            for i in list(data1.keys()):
                data1[i] = [data1[i]]
            # print(list(data.keys()))
            indexProg.append(len(indexProg) + 1)
            # df = pd.DataFrame(data, index = [indexProg], columns = list(data.keys()))
            df = pd.DataFrame(data = data1, index = pd.Index(indexProg))
            # df = pd.DataFrame([data], columns = list(data.keys()))
            print('exit:', df['exit'])
            # df.to_csv(file, header = df.columns, mode = 'w')
            
            # need to write sql code
            df.to_sql(con=database_connection, name = 'analysis',if_exists='replace')

            # df.to_excel(file, header = None)
            objManaged = sqlObject()
            continueAlter = False
            

def main():
    exec()

if __name__ == '__main__':
    main()