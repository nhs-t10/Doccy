import pandas as pd
import nltk
import numpy as np
from nltk.tokenize import word_tokenize
from nltk import tokenize

csvdata = pd.read_csv(r'training_data.csv', skipinitialspace=True,delimiter=",")

#Convert data into a numpy array
csvdata1 = np.array(csvdata)
train = []

#Put contents of numpy array into empty list
train.extend(csvdata1)

######################################################################
# Search Path
######################################################################

def predict(line):
    try:

        wordlist = set(word.lower() for statement in train for word in word_tokenize(statement[0]))

        x = [({word: (word in word_tokenize(x[0])) for word in wordlist}, x[1]) for x in train]

        classifier = nltk.NaiveBayesClassifier.train(x)

        test_data = line
        if line.__len__() > 1:

            # If there is a string, return if string is labeled as positive or negative
            test_data_features = {word.lower(): (word in word_tokenize(test_data.lower())) for word in wordlist}
            label = (classifier.classify(test_data_features))
            print("label:",label)

    except:
        print("Failed.")

predict("I confirmed who will attend the FLL outreach, still need to confirm who will be able to go and get more specific response from Liquid Oxygen. The LO team wants to do some outreach events also, so we decided that they could do this event with us.")