# Import datetime
from contextlib import nullcontext
from datetime import datetime, timedelta, date
import numpy as np

"""
How to:
1. Detect any red candles
1a. if in a sequence, only account for the first and last red candles in that sequence
2. connect lines from the top of the sequence to the bottom of the sequence
2a. connect the top of each sequence if the top of each sequence/one off has a open price less than the one before
3. clear the lines if plot breaks the resistance line

4? check for the slope of the long term SMA
"""

def isCandleRed(data):
    redList = []
    for i in range(len(data.index)):
        if data.close[i] - data.open[i] >= 0:
            redList.append(False)
        else:
            redList.append(True)
    return redList

"""
Purpose: form the array of values for the y and x values of the linear line.
"""
def plotLine(data, candleInterval, base, upperTimeBound, indexOne, indexTwo):
    # marketHourIndexes = timedelta(hours = 9, minutes = 30).seconds // 60 // candleInterval
    newTimeOne = base + timedelta(minutes = indexOne * candleInterval)
    newTimeTwo = base + timedelta(minutes = indexTwo * candleInterval)
    # number of candles between each time
    diffTimeSlope = ((newTimeTwo - newTimeOne).seconds // 60) // candleInterval
    diffTimeNow = ((upperTimeBound - newTimeOne).seconds // 60) // candleInterval

    # make slope
    slope = (data.open[indexTwo] - data.open[indexOne]) / diffTimeSlope

    x = np.array([newTimeOne + timedelta(minutes = candleInterval * i) for i in range(diffTimeNow)]).astype(np.datetime64)
    y = np.array([data.open[indexOne] + i * slope for i in range(diffTimeNow)])

    boolDecision = shouldPlot(data, indexOne, y)
    if boolDecision:
        return x, y, slope
    return 0, 0, 0

"""
Purpose: checks to see if resistance line has already been broken
Parameters: data, indexOne, resY
Output: boolean (should i plot this curve?)
"""
def shouldPlot(data, indexOne, resY):
    for i in range(len(resY)):
        if (i + indexOne) < len(data.close):
            if data.close[i + indexOne] > resY[i]:
                return False
    return True

"""
Purpose: checks to see if similar resistance line has already been plotted
Parameters: data, upperBoundTime, resistancePlot
Output: list of unique plots (refined resistancePlot)
"""
def uniquePlot(buffer, candleInterval, resistancePlot):
    # marketHourIndexes = timedelta(hours = 6, minutes = 30).seconds // 60 // candleInterval
    # for i in resistancePlot:
    #     for j in range(marketHourIndexes):
    #         np.insert(i['x'], 0, datetime(i['x'][0].year, i['x'][0].month, i['x'][0].day) + timedelta(hours = i['x'][0].hour, minutes = i['x'][0].minute) - timedelta(minutes = candleInterval))
    #         np.append(i['x'], datetime(i['x'][len(i['x']) - 1].year, i['x'][len(i['x']) - 1].month, i['x'][len(i['x']) - 1].minute) + timedelta(hours = i['x'][len(i['x']) - 1].hour, minutes = i['x'][len(i['x']) - 1].minute) + timedelta(minutes = candleInterval))
    #         np.insert(i['y'], 0, i['y'][0] - i['slope'])
    #         np.append(i['y'], i['y'][len(i['y']) - 1] + i['slope'])
    k = 200
    endResistancePlotIndex = len(resistancePlot) - 1
    if endResistancePlotIndex > 0:
        currSlope = resistancePlot[endResistancePlotIndex]['slope']
        currY = resistancePlot[endResistancePlotIndex]['y']
        for i in range(endResistancePlotIndex - 1, -1, -1):
            countRedundance = 0
            if abs(resistancePlot[i]['slope'] - currSlope) < (abs(min(currSlope, resistancePlot[i]['slope']) / 3)):
                sizeY = len(resistancePlot[i]['y'])
                for j in range(len(currY) + k):
                    slope1 = currY[len(currY) - 1] + currSlope * (k // 2) - (currSlope * j)
                    slope2 = resistancePlot[i]['y'][sizeY - 1] + resistancePlot[i]['slope'] * (k // 2) - (resistancePlot[i]['slope'] * j)
                    if abs( slope1 - slope2) <= buffer:
                        countRedundance += 1
                    if countRedundance >= (50 // candleInterval):
                        resistancePlot.pop(i + 1)
                        break                
                currSlope = resistancePlot[i]['slope']
                currY = resistancePlot[i]['y']
            else:
                currSlope = resistancePlot[i]['slope']
                currY = resistancePlot[i]['y']
    return resistancePlot

def mapResistancePoints(buffer, data, candleInterval, upperTimeBound):
    base = datetime(upperTimeBound.year, upperTimeBound.month, upperTimeBound.day) + timedelta(hours = 9, minutes = 30)
    count = 0
    resistanceLines = []
    redList = isCandleRed(data)
    for i in range(len(redList)):
        if (i > 0) and (redList[i] == True) and (redList[i - 1] == True):
            continue
        if redList[i] == True:
            for j in range(i + 1, len(redList)):
                if (redList[j] == True) and (data.open[i] - data.open[j]) > 0:
                    if j + 1 < len(redList) and redList[j + 1] == True and redList[j - 1] == True:
                        continue
                    else: 
                        test1, test2, testSlope = plotLine(data, candleInterval, base, upperTimeBound, i, j)
                        if test1 != 0:
                            resistanceLines.append(dict({'x':[], 'y':[], 'slope':[]}))
                            resistanceLines[count]['x'], resistanceLines[count]['y'], resistanceLines[count]['slope'] = test1, test2, testSlope
                            count += 1
                elif (redList[j] == True and data.open[j] >= data.open[i]) or (redList[j] == False and data.open[j] >= data.open[i]):
                    i = j
                    break
    # resistanceLines = uniquePlot(buffer, candleInterval, resistanceLines)
    return resistanceLines