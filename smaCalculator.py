"""
Try and create a class that will create any sma line with any
amount of parameters easily
parameters: data (dictionary)
output: list of values for plotting \\ it might be worth making the keys the date time

-also will need a diff eq function to determine direction
-will need a sql function to consistently map results (can i scan historical data?)
-implement robinhood API
-think about buying and selling bounds
"""


"""
can make more efficient by implementing stacks instead of constantly rescanning datas
"""

import numpy as np
import pandas as pd
import math

# Import datetime
from datetime import datetime, timedelta

"""
Purpose: takes dictionary and determines the starting value.
parameter: dictionary
output: starting index
"""
def startSma(upperTimeBound, candleInterval, data):
    # if datetime.now() - (datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(hours = 16)) > timedelta(minutes = 0):
    #     upperTimeBound = datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(hours = 16)
    # elif datetime.now() - (datetime(datetime.now().year, datetime.now().month, datetime.now().day) + timedelta(hours = 9) + timedelta(minutes = 30)) < timedelta(minutes = 0):
    #     upperTimeBound = datetime(datetime.now().year, datetime.now().month, datetime.now().day) - timedelta(days = 1) + timedelta(hours = 16)
    # else:
    #     upperTimeBound = datetime.now()
    base = datetime(upperTimeBound.year, upperTimeBound.month, upperTimeBound.day) + timedelta(hours = 9) + timedelta(minutes = 30)
    rangeTime = upperTimeBound - base
    rangeMinutes = rangeTime.seconds//60
    rangeIntervals = rangeMinutes // candleInterval
    end = len(data.close)
    return end - rangeIntervals

"""
Purpose: uses an iteration to find the average at that interval
create an average for pre and post market values
parameter: dictionary, interval
output: float average
"""
def calcAverage(upperTimeBound, candleInterval, smaInterval, data):
    listAvg = []
    tot = 0
    startIndex = int(startSma(upperTimeBound, candleInterval, data))
    prepostIndexes = ((timedelta(hours = 17) + timedelta(minutes = 30)).seconds//60)//candleInterval
    base = datetime(upperTimeBound.year, upperTimeBound.month, upperTimeBound.day) + timedelta(hours = 9) + timedelta(minutes = 30)
    currMarketHourIndexes = ((upperTimeBound - base).seconds // 60) // candleInterval
    marketHourIndexes = (timedelta(hours = 6) + timedelta(minutes = 30)).seconds //60 // candleInterval
    # print(marketHourIndexes)
    endIndex = startIndex + currMarketHourIndexes - 1
    trueSmaInterval = smaInterval
    for j in range(startIndex, endIndex + 1):
        smaInterval = trueSmaInterval
        for i in range(smaInterval):
            if ((j - i) % marketHourIndexes) == 0:
                if (smaInterval - i) <= prepostIndexes:
                    for z in range (smaInterval - i):
                        val = data.open[j - i] - z * (data.open[j - i] - data.close[j - (i + 1)])/prepostIndexes
                        tot += val
                    # print(j - i, "\t", data.open[j - i])
                    # print(val)
                    break
                else:
                    tot += (data.open[j - i] + data.close[j - i - 1])/2 * prepostIndexes
                    smaInterval -= prepostIndexes
            else:
                tot += data.close[j - i]
        listAvg.append(tot / trueSmaInterval)
        tot = 0
    # for i in listAvg:
    #     print(i)
    # print(startIndex, "\t", endIndex, "\t", len(data.index))
    return listAvg

"""
Purpose: iterates calcAverage to create the list of average values
parameter: interval, data
output: list of averages
"""
def createList(upperTimeBound, candleInterval, smaInterval, data):
    listAvg = calcAverage(upperTimeBound, candleInterval, smaInterval, data)
    return listAvg