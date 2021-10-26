import json
import pandas as pd
import math


if __name__ == '__main__':
    # Read the CSV file and store it as an array of JSON
    print("Reading Project 1 - Task 1 CSV file ...")
    df = pd.read_csv("VAERS_COVID_DataAugust2021.csv", encoding="ISO-8859-1", engine='python')
    data = json.loads(pd.DataFrame.to_json(df, orient='records'))
    print("Read and converted Task 1 CSV file to array of JSON")

    #  Implement a B+ tree dynamic index structure (based on VAERSID as your index), where the actual data is located
    #  at the leaf nodes. The user should have a choice to input the maximum degree of a node. Create the B+ tree that
    #  stores the VAERS_COVID_DataAugust2021.csv data set.
