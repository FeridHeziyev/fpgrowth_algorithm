import operator
import itertools
import argparse
import time


class FPTree:
    def __init__(self, child):
        self.child = child

class FPNode:
    def __init__(self, parentNode, name):
        self.parentNode = parentNode
        self.name = name
        self.count = 1


def FindFrequentItems(transactions, minSup):
    counts = dict()
    freqItemList = dict()
    for liste in transactions:
        liste = set(liste)
        for x in liste:
            if x not in counts.keys():
                counts[x] = 0
            counts[x] += 1
    sorted_counts = sorted(counts.items(), key=operator.itemgetter(1), reverse = True)

    for item in sorted_counts:
        if item[1] >= minSup:
            freqItemList[item[0]] = item[1]
    return freqItemList

#order the fitered transactions(transactions that are in frequent items)
def OrderTransactions(transactions, frequentItems):
    orderedTransactions = []
    for transaction in transactions:
        if len(transaction) > 1:
            ordered = list(filter(lambda x: x in frequentItems, transaction))
            ordered = set(ordered)
            liste = sorted(ordered, key = lambda tran:frequentItems[tran], reverse = True)
            if len(liste) > 1:
                orderedTransactions.append(liste)
    return orderedTransactions

def ConstructFPTree(orderedTransactions, minSup):
    AllNodes = []
    NullNode = FPNode(None, "NullNode")
    NullNode.index = 0
    AllNodes.append(NullNode)
    #allTrees = []
    for transaction in orderedTransactions:
        nodes = []
        for x in range(0,len(transaction)):
            if x == 0:
                parent = NullNode
                curNode = FPNode(parent, transaction[x])
                nodeFromDb = [x for x in AllNodes if x.name == curNode.name and x.parentNode.name == "NullNode" and x.parentNode.parentNode == None]
                if len(nodeFromDb) != 0:
                    AllNodes[nodeFromDb[0].index].count += 1
                else:
                    curNode.index = len(AllNodes)
                    AllNodes.append(curNode)
                nodes.append(curNode)
                
            else:
                parent = nodes[x-1]
                curNode = FPNode(parent, transaction[x])
                nodeFromDb = [x for x in AllNodes if x.name == curNode.name and x.parentNode.name == parent.name and x.parentNode.parentNode.name == parent.parentNode.name]

                if len(nodeFromDb) != 0:
                    AllNodes[nodeFromDb[0].index].count += 1
                else:
                    curNode.index = len(AllNodes)
                    AllNodes.append(curNode)
                nodes.append(curNode)

    return AllNodes
           
                
def ConditionalPaternBaseCreate(allTrees, frequenItems, minSup):
    #AllNodes = ConstructFPTree(transactions, minSup)  
    #freq = FindFrequentItems(transactions,minSup)
    trees = []
    sorted_freqItems = sorted(frequenItems.items(), key=operator.itemgetter(1), reverse = True)

    for x in sorted_freqItems:
        transactionsOfItem = [item for item in allTrees if item.name == x[0]]
        for tr in transactionsOfItem:
            parent = tr.parentNode
            if parent.parentNode != None:
                itemFromTreeDb = [item for item in trees if item.child == tr.name]

                if len(itemFromTreeDb) == 0:
                    tree = FPTree(x[0])
                    tree.route = dict()
                parStr = ""
                while parent.parentNode != None:
                    if parStr == "":
                        parStr =  parStr
                    else:
                        parStr = "," + parStr
                    parStr = str(parent.name) + parStr
                    parent = parent.parentNode
            
                tree.route[parStr + "," + str(tr.name)] = tr.count

                if len(itemFromTreeDb) == 0:
                    trees.append(tree)

    return trees


def GenerateFrequentPatterns(conditionalPatternBases, frequentItems,minSup):
    items = dict()
    for x in conditionalPatternBases:
        for y,count in x.route.items():
            items[y] = count

    
    #frequent items are ordered
    orderedItems = {k: v for k,v in items.items() if v >= minSup }

    return orderedItems

def FindAssociationRules(transactions,frequentPatterns, minSup, minCon, fileToWrite):
    fileToWrite = open(fileToWrite, "w")
    #frequentPatterns = GenerateFrequentPatterns(transactions, minSup)
    rules = dict()
    for x,count in frequentPatterns.items():
        liste = x.split(",")
        liste = list(map(lambda x: int(x), liste))
        permutations = list(itertools.permutations(liste, len(liste)))
        pastbases = []
        for rule in permutations:
            exit = False
            rule = list(rule)
            base = rule[0:-1]
            for x in pastbases:
                if all(b in x for b in base):
                    exit = True
            if exit:
                continue
            pastbases.append(base)
            child = rule[-1]
            confidenceNom = 0
            confidenceDenum = 0
            for transaction in transactions:
                if all(b in transaction for b in base):
                    confidenceDenum += 1
                if child in transaction and all(b in transaction for b in base):
                    confidenceNom += 1
            confidence = confidenceNom/confidenceDenum
            if confidence >= minCon:
                print("Base: {" + ','.join(map(str,base))  + "} --- " + " child: (" + str(child) + ")     support: " + str(int(count)/len(transactions)) + "  confidence: " + str(confidence), file = fileToWrite)

def Main():
    starttime = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("-file", help = "input file", default = "msnbc_ready_data.tsv")
    parser.add_argument("-o", "--output", help = "output the result to a file",
                        default = "Output_FP.tsv")
    parser.add_argument("-delimiter", help = "decide the delimiter for the lines", 
                        default = " ")
    parser.add_argument("-s", "--support", help = "decide the support", 
                        default = 0.1, type = float)
    parser.add_argument("-c", "--confidence", help = "decide the confidence", 
                        default = 0.4, type = float)
    parser.add_argument("-d", "--delimiter", help = "decide the delimiter. how the words in the row are splitted",
                        default = " ")
    args = parser.parse_args()

    fileToRead = open(args.file, "r")
    minSupport = args.support 
    minCon = args.confidence
    fileToWrite = args.output
    delimiter = args.delimiter
    transactions = []

    for line in fileToRead:
        liste = line.split(delimiter)
        liste = list(map(lambda x: int(x), liste))

        transactions.append(liste)
    

    minSupport = minSupport * len(transactions)

    frequentItems = FindFrequentItems(transactions, minSupport)
    orderedTransactions = OrderTransactions(transactions, frequentItems)
    allTrees = ConstructFPTree(orderedTransactions, minSupport)
    conditionalPatternBases = ConditionalPaternBaseCreate(allTrees, frequentItems, minSupport)
    frequentPatterns = GenerateFrequentPatterns(conditionalPatternBases, frequentItems, minSupport)
     
    FindAssociationRules(transactions,frequentPatterns, minSupport, minCon, fileToWrite)

    endTime = time.time()
    print(endTime - starttime)

if __name__ == "__main__":
    Main()
