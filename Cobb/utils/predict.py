import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from Cobb import Cobb_bot
from sklearn.model_selection import train_test_split

class SClassifier:
    def __init__(self, model_path='./Cobb/dataset/classify_model.csv') -> None:
        self.model_path = model_path
        self.cv = None
        self.X = None
        self.Y = None
        
    def load_model(self):
        df = pd.read_csv(self.model_path, encoding="latin-1", low_memory=False)
        df['label'] = df['type'].map({'ham': 0, 'spam': 1})
        X = df['text']
        Y = df['label']
        self.X = X
        self.Y = Y
        self.df = df
    
    def cv_and_train(self):
        X = self.X
        Y = self.Y
        cv = CountVectorizer()
        X = cv.fit_transform(X) 
        XTrain, XTest, YTrain, YTest = train_test_split(X, Y, test_size=0.3, random_state=42)
        mnb = MultinomialNB()
        mnb.fit(XTrain, YTrain)
        self.score = mnb.score(XTest, YTest)
        self.cv = cv
        self.mnb = mnb
    
    @Cobb_bot.run_in_exc
    def predict(self, text):
        cv = self.cv
        mnb = self.mnb
        if isinstance(text, str):
            text = [text]
        vect_array = cv.transform(text).toarray()
        ham_per, spam_per = mnb.predict_proba(vect_array)[0]
        ham_per = round(ham_per * 100, 2)
        spam_per = round(spam_per * 100, 2)
        return (mnb.predict(vect_array)[0] != 0, ham_per, spam_per)
    