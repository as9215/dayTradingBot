from time import time
import numpy as np
import pandas as pd
import math

#Data Source
import yfinance as yf

#Data viz
import plotly.graph_objs as go

# Import datetime
from datetime import datetime, timedelta, date


def timeToX(X):
    finList = []
    for x in X:
        finList.append(timedelta(hours = x.hour, minutes = x.minute).seconds // 60)
    return finList

def bestFitSlope(X, Y):
    X = timeToX(X)
    xbar = sum(X)/len(X)
    ybar = sum(Y)/len(Y)
    n = len(X) # or len(Y)

    numer = sum([xi*yi for xi,yi in zip(X, Y)]) - n * xbar * ybar
    denum = sum([xi**2 for xi in X]) - n * xbar**2

    b = numer / denum

    return b

def shouldEnter(currentlyIn, shortSmaValues, closeValues, candleInterval):
    if len(closeValues) % (timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval) != 0:
        if not currentlyIn:
            if closeValues[len(closeValues) - 1] > shortSmaValues[len(shortSmaValues) - 1]:
                    return True
    return False

def shouldExit(currentlyIn, shortValues, closeValues, candleInterval):
    if currentlyIn:
        if closeValues[len(closeValues) - 1] < shortValues[len(shortValues) - 1]:
            return True
        elif len(closeValues) % (timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval) == 0:#timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval - 1:
            return True
    return False

def rsi(df, periods = 14, ema = True):
    """
    Returns a pd.Series with the relative strength index.
    """
    x = pd.Series(df.close)
    close_delta = x.diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    if ema == True:
	    # Use exponential moving average
        ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
        ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window = periods, adjust=False).mean()
        ma_down = down.rolling(window = periods, adjust=False).mean()
        
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi

def evaluator(objSql, currentlyIn, data, shortSma, longSma, resY, candleInterval, shortSmaInterval, longSmaInterval, resYList, upperDateTime):
    marketHourIndexes = timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval
    premarketHourIndexes = timedelta(hours = 17, minutes = 30).seconds // 60 // candleInterval
    slopeDiff = 5
    if shouldEnter(currentlyIn, shortSma, data.close, candleInterval):
        objSql.enter = data.close[len(data.close) - 1]
        objSql.candleInterval = candleInterval

        slopeList = []
        for i in resY:
            slopeList.append(i['slope'])
        # return slope list
        objSql.resistanceLinesSlopes = sorted(slopeList)
        objSql.resistanceLines = len(resY)


        # resistanceLinesDiff
        resistanceSlopesDict = dict()
        resistanceSlopesDict.clear()
        resistancePeriod = 10
        lim = resistancePeriod // candleInterval
        if len(resYList) < lim:
            lim = len(resYList)
        diff = 0
        temp = len(resYList[len(resYList) - lim])
        for i in resYList[len(resYList) - lim]:
            resistanceSlopesDict[str(i['slope'])] = 0
        for i in range(len(resYList) - lim + 1, len(resYList)):
            if len(resYList[i]) < temp:
                diff += temp - len(resYList[i])
                temp = len(resYList[i])
                for j in resistanceSlopesDict.keys():
                    resistanceSlopesDict[j] = 0
            if len(resYList[i]) > temp:
                temp = len(resYList[i])
            for k in resYList[i]:
                resistanceSlopesDict[str(k['slope'])] = 1
            # return slopes with value 0
        for i in resistanceSlopesDict.keys():
            if resistanceSlopesDict[i] == 0:
                objSql.resistanceLinesDiffSlopes.append(float(i))
        if diff == 0:
            objSql.resistanceLinesDiffSlopes = []
        else:
            objSql.resistanceLinesDiffSlopes = sorted(objSql.resistanceLinesDiffSlopes[len(objSql.resistanceLinesDiffSlopes) - diff: len(objSql.resistanceLinesDiffSlopes)])

        if len(data.index) % marketHourIndexes < slopeDiff and len(data.index) % marketHourIndexes > 0:
            slopeDiff = len(data.index) % marketHourIndexes

        objSql.resistanceLinesDiff = diff
        objSql.time = data.index[len(data.index) - 1]
        objSql.intervalShortSma = shortSmaInterval
        objSql.intervalLongSma = longSmaInterval
        if len(data.index) % marketHourIndexes != 1:
            objSql.enterShortSmaSlope = bestFitSlope(data.index[len(data.index) - slopeDiff:], shortSma[len(shortSma) - slopeDiff:])
            objSql.enterLongSmaSlope = bestFitSlope(data.index[len(data.index) - slopeDiff:], longSma[len(longSma) - slopeDiff:])
        else:
            objSql.enterShortSmaSlope = (shortSma[len(shortSma) - 1] - shortSma[len(shortSma) - 2]) / (premarketHourIndexes)
            objSql.enterLongSmaSlope = (longSma[len(longSma) - 1] - longSma[len(longSma) - 2]) / (premarketHourIndexes)
        objSql.deltaShortSmaLongSma = shortSma[len(shortSma) - 1] - longSma[len(longSma) - 1]
        objSql.callPut = 'c'
        rsiData = rsi(data)
        objSql.enterRSI = rsiData[len(rsiData) - 1]

        # rsi period
        rsiPeriod = 10
        lim = rsiPeriod // candleInterval
        if (len(rsiData) % marketHourIndexes) < lim:
            lim = len(rsiData)
        posDiff = 0
        negDiff = 0
        # print(len(rsiData))
        # print(lim)
        temp = rsiData[len(rsiData) - lim]
        for i in range(len(rsiData) - lim, len(rsiData)):
            if rsiData[i] > temp:
                posDiff += rsiData[i] - temp
                temp = rsiData[i]
            elif rsiData[i] <= temp:
                negDiff += temp - rsiData[i]
                temp = rsiData[i]
        if len(rsiData) == 1:
            posDiff = 0
            negDiff = 0
        objSql.RSIposMomentum = posDiff
        objSql.RSInegMomentum = negDiff

        currentlyIn = True
    elif shouldExit(currentlyIn, shortSma, data.close, candleInterval):
        objSql.exit = data.close[len(data.close) - 1]
        objSql.priceChange = objSql.exit - objSql.enter
        objSql.exitTime = upperDateTime

        # resistanceLinesDiff
        lim = timedelta(hours = objSql.exitTime.hour, minutes = objSql.exitTime.minute).seconds // 60
        lim = lim - timedelta(hours = objSql.time.hour, minutes = objSql.time.minute).seconds // 60
        lim = lim // candleInterval
        diff = 0
        print("resy len: ", len(resYList), "\t", "lim: ", lim, "\t", "data.close:", len(data.close))
        resistanceSlopesDict = dict()
        resistanceSlopesDict.clear()
        temp = len(resYList[len(resYList) - lim])
        for i in resYList[len(resYList) - lim]:
            resistanceSlopesDict[str(i['slope'])] = 0
        for i in range(len(resYList) - lim + 1, len(resYList)):
            if len(resYList[i]) < temp:
                diff += temp - len(resYList[i])
                temp = len(resYList[i])
                for j in resistanceSlopesDict.keys():
                    resistanceSlopesDict[j] = 0
                for k in resYList[i]:
                    resistanceSlopesDict[str(k['slope'])] = 1
            if len(resYList[i]) > temp:
                temp = len(resYList[i])
                for k in resYList[i]:
                    resistanceSlopesDict[str(k['slope'])] = 1
            # return slopes with value 0
        for i in resistanceSlopesDict.keys():
            if resistanceSlopesDict[i] == 0:
                objSql.resistanceLinesBrokeSlopes.append(float(i))
        if diff == 0:
            objSql.resistanceLinesBrokeSlopes = []
        else:
            objSql.resistanceLinesBrokeSlopes = sorted(objSql.resistanceLinesBrokeSlopes[len(objSql.resistanceLinesBrokeSlopes) - diff: len(objSql.resistanceLinesBrokeSlopes)])
        
        objSql.resistanceLinesBroke = diff
        if len(data.index) % marketHourIndexes != 1:
            objSql.exitShortSmaSlope = bestFitSlope(data.index[len(data.index) - slopeDiff:], shortSma[len(shortSma) - slopeDiff:])
            objSql.exitLongSmaSlope = bestFitSlope(data.index[len(data.index) - slopeDiff:], longSma[len(longSma) - slopeDiff:])
        else:
            objSql.exitShortSmaSlope = (shortSma[len(shortSma) - 1] - shortSma[len(shortSma) - 2]) / (premarketHourIndexes)
            objSql.exitLongSmaSlope = (longSma[len(longSma) - 1] - longSma[len(longSma) - 2]) / (premarketHourIndexes)
        objSql.exitShortLongSmaDiff = objSql.exitShortSmaSlope - objSql.exitLongSmaSlope
        rsiData = rsi(data)
        objSql.exitRsi = rsiData[len(rsiData) - 1]

        # rsi period
        rsiPeriod = 10
        lim = rsiPeriod // candleInterval
        if (len(rsiData) % marketHourIndexes) < lim:
            lim = len(rsiData)
        posDiff = 0
        negDiff = 0
        # print(len(rsiData))
        # print(lim)
        temp = rsiData[len(rsiData) - lim]
        for i in range(len(rsiData) - lim, len(rsiData)):
            if rsiData[i] > temp:
                posDiff += rsiData[i] - temp
                temp = rsiData[i]
            elif rsiData[i] <= temp:
                negDiff += temp - rsiData[i]
                temp = rsiData[i]
        if len(rsiData) == 1:
            posDiff = 0
            negDiff = 0
        objSql.exitShortPositiveRsiMomentum = posDiff
        objSql.exitShortNegativeRsiMomentum = negDiff
        objSql.exitRsiShortChange = posDiff - negDiff

        lim = timedelta(hours = objSql.exitTime.hour, minutes = objSql.exitTime.minute).seconds // 60
        lim = lim - timedelta(hours = objSql.time.hour, minutes = objSql.time.minute).seconds // 60
        lim = lim // candleInterval
        temp = rsiData[len(rsiData) - lim]
        posDiff = 0
        negDiff = 0
        for i in range(len(rsiData) - lim, len(rsiData)):
            if rsiData[i] > temp:
                posDiff += rsiData[i] - temp
                temp = rsiData[i]
            elif rsiData[i] <= temp:
                negDiff += temp - rsiData[i]
                temp = rsiData[i]
        if len(rsiData) == 1:
            posDiff = 0
            negDiff = 0
        objSql.exitPositiveRsiMomentum = posDiff
        objSql.exitNegativeRsiMomentum = negDiff
        objSql.exitRsiOverallChange = posDiff - negDiff

        currentlyIn = False
    return objSql, currentlyIn