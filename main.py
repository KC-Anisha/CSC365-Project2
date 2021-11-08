import copy
import json
import random
import sys
from functools import reduce

import pandas as pd
import math

depth = 1


class Node(object):
    # Node - can be either a regular node or a leaf node
    def __init__(self, degree):
        # The leaf value determines if this is a leaf node or just a parent node
        self.leaf = True
        self.degree = degree
        self.keys = []
        self.values = []

    def add(self, key, value):
        # Add a key value pair to the node
        # If this node is empty, let's just insert the key and value
        if not self.keys:
            self.keys.append(key)
            self.values.append([value])
            return None

        for i, existingKey in enumerate(self.keys):
            # If there is an existing key that matches the new one, just add to the list of values
            if key == existingKey:
                self.values[i].append(value)
                break
            # If the new key is smaller, insert it to the left
            elif key < existingKey:
                self.keys = self.keys[:i] + [key] + self.keys[i:]
                self.values = self.values[:i] + [[value]] + self.values[i:]
                break
            # If the new key is bigger, insert to the right of all keys
            elif i + 1 == len(self.keys):
                self.keys.append(key)
                self.values.append([value])

    # Need to be able to split the node into two and store them as child nodes
    def split(self):
        left = Node(self.degree)
        right = Node(self.degree)
        mid = self.degree // 2

        left.keys = self.keys[:mid]
        right.keys = self.keys[mid:]

        left.values = self.values[:mid]
        right.values = self.values[mid:]

        # After we split the node, we need to set the parent key to the most-left key of the right child
        self.keys = [right.keys[0]]
        self.values = [left, right]
        self.leaf = False

    # Check if the node is full (based on the degree)
    def isFull(self):
        return len(self.keys) == self.degree

    # To print - just for me to see
    def print(self, counter=0):
        # Print the key at each level :)
        print("level " + str(counter) + ": ", str(self.keys))

        # Also print the children
        if not self.leaf:
            for child in self.values:
                child.print(counter + 1)

    # Get the depth of the tree
    def getDepth(self, currentDepth):
        global depth
        if currentDepth >= depth:
            depth = currentDepth
        if not self.leaf:
            for child in self.values:
                child.getDepth(currentDepth + 1)

    # Only print certain levels of the tree
    def printLevels(self, levelsToPrint, currentLevel=0):
        if currentLevel in levelsToPrint:
            print("level " + str(currentLevel) + ": ", str(self.keys))

        if not self.leaf:
            for child in self.values:
                child.printLevels(levelsToPrint, currentLevel + 1)

    # Print the leaves of the tree
    def printLeaves(self):
        if self.leaf:
            print(self.values)
        else:
            for child in self.values:
                child.printLeaves()


class BPlusTree(object):
    # User gives the degree
    def __init__(self, degree):
        self.root = Node(degree)

    # Return where the given key should be inserted and the list of values at that index
    def find(self, node, key):
        for i, existingKey in enumerate(node.keys):
            if key < existingKey:
                return node.values[i], i
            return node.values[i + 1], i + 1

    # Merge - we need to get a pivot from the child that will be inserted in the keys of the parent
    # node. We also need to insert the values from the child into the values of the parent
    def merge(self, parent, child, index):
        parent.values.pop(index)
        pivot = child.keys[0]

        for i, parentKey in enumerate(parent.keys):
            if pivot < parentKey:
                parent.keys = parent.keys[:i] + [pivot] + parent.keys[i:]
                parent.values = parent.values[:i] + child.values
                break
            elif i + 1 == len(parent.keys):
                parent.keys += [pivot]
                parent.values += child.values
                break

    # Inserting a key and value pair
    # Need to traverse to a leaf node. If the leaf node is full, we need to split it
    def insert(self, key, value):
        parent = None
        child = self.root

        # Let's traverse the tree till we get to a leaf node
        while not child.leaf:
            parent = child
            child, index = self.find(child, key)

        child.add(key, value)

        # If the leaf node is full, we need to split it
        if child.isFull():
            child.split()

            # After splitting, we have an internal node and two leaf nodes. We need to put these back into the tree
            if parent and not parent.isFull():
                self.merge(parent, child, index)

    # Search for a key's value
    def search(self, key):
        child = self.root

        # All data is held at the leaf nodes
        while not child.leaf:
            child, index = self.find(child, key)

        for i, existingKey in enumerate(child.keys):
            if existingKey == key:
                return child.values[i]

        # If key doesn't exist, return None
        return None

    # Printing a B+ tree for me to see
    def printTree(self):
        self.root.print()

    # If you wanna see just the head
    def printHead(self):
        print(self.root.keys)

    # Get depth of tree
    def getDepth(self):
        self.root.getDepth(1)
        return depth

    # Print only certain levels
    def printLevels(self, levels):
        self.root.printLevels(levelsToPrint=levels)

    def printLeaves(self):
        self.root.printLeaves()


# Create a new dataset (unique VAERSID)
def createNewDataset():
    a = pd.read_csv("2021VAERSDataSeptember.csv", encoding="ISO-8859-1", engine='python')
    b = pd.read_csv("2021VAERSSYMPTOMSSeptember.csv", encoding="ISO-8859-1", engine='python')
    c = pd.read_csv("2021VAERSVAXSeptember.csv", encoding="ISO-8859-1", engine='python')
    c = c[c.VAX_TYPE.eq("COVID19")]
    # Combine all 3 datasets and Remove all non Covid rows
    NewData = reduce(lambda x, y: pd.merge(x, y, on='VAERS_ID', how='outer', sort=False),
                     [a, b, c])
    NewData = NewData[NewData.VAX_TYPE.eq("COVID19")]
    NewData = json.loads(pd.DataFrame.to_json(NewData, orient='records'))

    # Dictionary(HashMap) to store new data
    hashMap = {}

    # Loop through the new data and store it in a hashmap
    for row in NewData:
        vaersId = row["VAERS_ID"]
        # If ID is already in the HashMap, just update the symptoms for it
        if vaersId in hashMap.keys():
            # Update the existing object with the additional symptoms
            obj = hashMap[vaersId]
            finalSymptoms = obj["Symptoms"]
            # Go through all symptoms and create a new symptoms array
            newSymptoms = []
            for x in range(0, 5):
                if row["SYMPTOM%d" % (x + 1)] is not None:
                    newSymptoms.append(json.loads(
                        '{ "SymptomName": "%s", "SymptomVersion": "%s"}' % (
                            row["SYMPTOM%d" % (x + 1)], row["SYMPTOMVERSION%d" % (x + 1)])))
            # Append the arrays and update the hashmap
            finalSymptoms.extend(newSymptoms)
            obj["Symptoms"] = finalSymptoms
            hashMap[vaersId] = obj
        # If ID is not in Hashmap, create a new entry
        else:
            # Create an array of symptoms by going through all symptoms row
            newSymptoms = []
            for x in range(0, 5):
                if row["SYMPTOM%d" % (x + 1)] is not None:
                    newSymptoms.append(json.loads(
                        '{ "SymptomName": "%s", "SymptomVersion": "%s"}' % (
                            row["SYMPTOM%d" % (x + 1)], row["SYMPTOMVERSION%d" % (x + 1)])))
            # Create a Covid Object with all the data
            for x in range(0, 5):
                del row['SYMPTOM%d' % (x + 1)]
                del row['SYMPTOMVERSION%d' % (x + 1)]
            obj = row
            obj["Symptoms"] = newSymptoms
            hashMap[vaersId] = obj

    # JSON Objects
    hashMapCopy = copy.deepcopy(hashMap)
    NewJsonData = []
    for key in hashMapCopy:
        # For every JSON object, we want to loop through the symptoms and create a flattened JSON
        obj = hashMapCopy[key]
        for count, symptom in enumerate(obj["Symptoms"], start=1):
            obj["SYMPTOM%d" % (count)] = symptom['SymptomName']
            obj["SYMPTOMVERSION%d" % (count)] = symptom['SymptomVersion']
        del obj["Symptoms"]
        NewJsonData.append(obj)

    return NewJsonData


if __name__ == '__main__':
    #  Implement a B+ tree dynamic index structure (based on VAERSID as your index), where the actual data is located
    #  at the leaf nodes. The user should have a choice to input the maximum degree of a node. Create the B+ tree that
    #  stores the VAERS_COVID_DataAugust2021.csv data set.

    # Read the CSV file and store it as an array of JSON
    print("Reading Project 1 - Task 1 CSV file ...")
    df = pd.read_csv("VAERS_COVID_DataAugust2021.csv", encoding="ISO-8859-1", engine='python')
    # df = pd.read_csv("VAERS_COVID_DataAugust2021.csv", encoding="ISO-8859-1", engine='python', nrows=35)
    data = json.loads(pd.DataFrame.to_json(df, orient='records'))

    print('Initializing B+ tree...')
    givenDegree = input("Enter the maximum degree of a node: ")
    tree = BPlusTree(degree=int(givenDegree))

    print('Inserting into the B+ tree...')
    for item in data:
        tree.insert(item['VAERS_ID'], item)

    # tree.printTree()
    depth = tree.getDepth()
    print('\nDepth: ' + str(depth))

    # print('\nPrint level by level')
    # for i in range(depth):
    #     tree.printLevels([i])


    print('\nRetrieving values with key 902465')
    print(tree.search(902465))

    # The VAERS database added new data in September.The new updated files for 2021 are given below.Insert the new
    # COVID19 adverse events reports that are not already available in the B+ tree created on task 1.

    print('\nReading and Creating a new dataset with the September Excel files ...')
    # Create a dataset with all 3 files
    NewData = createNewDataset()

    print('\nAdding new data into the B+ tree ...')
    for item in NewData:
        if tree.search(item['VAERS_ID']) is None:
            tree.insert(item['VAERS_ID'], item)

    depth = tree.getDepth()
    print('\nDepth after adding new data: ' + str(depth))

    stdoutOrigin = sys.stdout
    sys.stdout = open("tree.txt", "w")
    tree.printTree()
    sys.stdout.close()
    sys.stdout = stdoutOrigin

    stdoutOrigin = sys.stdout
    sys.stdout = open("treebylevels.txt", "w")
    print('Print level by level')
    for i in range(depth):
        tree.printLevels([i])
    sys.stdout.close()
    sys.stdout = stdoutOrigin


    # print('\nJust the head')
    # tree.printHead()
    #
    # print('\nThe leaves')
    # tree.printLeaves()
