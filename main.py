import csv
from typing import KeysView
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
 
file = 'existing_data_1.csv'
xAxis = 'timeActive'

def analyzeList(key):
    results = []
    with open(file) as File:
        reader = csv.DictReader(File)
        data = dict()
        for row in reader:
            results.append(row)
        for j in list(results[0].keys())[1:]:
            if j != 'call or put':
                data[j] = []
        for i in range(len(results)):
            for j in data.keys():
                data[j].append(results[i][j])
        # print(data[key])
        for i in range(len(data[key])):
            data[key][i] = data[key][i].strip("[").strip("]").split(",")
        # print(data[key])
        for i in range(len(data[key])):
            for j in range(len(data[key][i])):
                if data[key][i][j] != '':
                    # print((data[key][i][j]))
                    data[key][i][j] = float(data[key][i][j])
                else:
                    data[key][i] = []
                    break
        for i in range(len(data[key])):
            for j in range(len(data[key][i])):
                data[key][i].sort()
        yList = []
        xList = []
        timeList = []
        for i in range(len(data[key])):
            if data[key][i] != []:
                yList.append(float(data[key][i][len(data[key][i]) - 1]))
                xList.append(float(data['price change'][i]))

                exitTime = timedelta(hours = int(data['exit time'][i].split()[1].split(":")[0]), minutes = int(data['exit time'][i].split()[1].split(":")[1])).seconds // 60
                time = timedelta(hours = int(data['time'][i].split()[1].split(":")[0]), minutes = int(data['time'][i].split()[1].split(":")[1])).seconds // 60
                timeList.append(exitTime - time)
        plt.scatter(xList, yList)
        plt.ylabel(key + " - smallest")
        plt.xlabel(xAxis)
        plt.show()

        yList = []
        xList = []
        timeList = []
        for i in range(len(data[key])):
            if data[key][i] != []:
                yList.append(float(data[key][i][0]))
                xList.append(float(data['price change'][i]))
                
                exitTime = timedelta(hours = int(data['exit time'][i].split()[1].split(":")[0]), minutes = int(data['exit time'][i].split()[1].split(":")[1])).seconds // 60
                time = timedelta(hours = int(data['time'][i].split()[1].split(":")[0]), minutes = int(data['time'][i].split()[1].split(":")[1])).seconds // 60
                timeList.append(exitTime - time)
        # print("x - ", xList)
        # print("y - ", yList)
        plt.scatter(xList, yList)
        plt.ylabel(key + " - largest")
        plt.xlabel(xAxis)
        plt.show()

def analyzeValue(key):
    results = []
    with open(file) as File:
        reader = csv.DictReader(File)
        data = dict()
        for row in reader:
            results.append(row)
        for j in list(results[0].keys())[1:]:
            if j != 'call or put':
                data[j] = []
        for i in range(len(results)):
            for j in data.keys():
                data[j].append(results[i][j])
        for i in range(len(data[key])):
            if data[key][i] != '':
                data[key][i] = float(data[key][i])
            else:
                data[key][i] = []
                break
        yList = []
        xList = []
        timeList = []
        for i in range(len(data[key])):
            if data[key][i] != []:
                yList.append(float(data[key][i]))
                xList.append(float(data['price change'][i]))

                exitTime = timedelta(hours = int(data['exit time'][i].split()[1].split(":")[0]), minutes = int(data['exit time'][i].split()[1].split(":")[1])).seconds // 60
                time = timedelta(hours = int(data['time'][i].split()[1].split(":")[0]), minutes = int(data['time'][i].split()[1].split(":")[1])).seconds // 60
                timeList.append(exitTime - time)
        
        # print("x - ", xList)
        # print("y - ", yList)
        plt.scatter(xList, yList)
        plt.ylabel(key)
        plt.xlabel(xAxis)
        plt.show()

def main():
    keysVal = ['resistance lines', 'resistance lines diff', 'resistance lines broke', 'enter short sma slope','enter long sma slope','short long sma difference', 'enter RSI', 'positive RSI momentum', 'negative RSI momentum', 'RSI change', 'exit short sma slope', 'exit long sma slope', 'exit short long sma difference', 'exit RSI', 'exit positive RSI momentum', 'exit negative RSI momentum', 'exit RSI short change', 'exit RSI overall change']
    keysList = ['resistance lines slopes', 'resistance lines diff slopes', 'resistance lines broke slopes','resistance lines broke slopes']
    for key in keysVal:
        analyzeValue(key)
    for key in keysList:
        analyzeList(key)

if __name__ == '__main__':
    main()