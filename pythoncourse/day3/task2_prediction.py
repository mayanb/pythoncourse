"""Create a prediction model to help impute each user's PLUS status"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score


def predict_plus():
    """Try predicting PLUS using a Random Forest classifier."""
    df = pd.read_csv('../../data/JD_user_data.csv')

    # construct factors from categorical variables
    categorical = ['user_level', 'gender', 'education', 'purchase_power', 'city_level']
    X = np.column_stack([pd.get_dummies(df[k]) for k in categorical])

    # train the classifier and evaluate precision with 5-fold cross validation
    classifier = RandomForestClassifier(n_estimators=100, criterion='gini', random_state=0)
    cv_scores = cross_val_score(classifier, X, df['plus'], cv=5)
    print(f"Average precision using a Random Forest classifier: {cv_scores.mean()}.")

    # now just use a simple train/test split and evaluate performance with a confusion matrix
    X_train, X_test, y_train, y_test = train_test_split(X, df['plus'], test_size=0.25, random_state=0)
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)
    print(cm2df(cm, ["Not PLUS", "PLUS"]).to_string())


def cm2df(cm, labels):
    """Add labels to a scikit-learn confusion matrix"""
    df = pd.DataFrame()
    for i, row_label in enumerate(labels):
        row = {}
        for j, column_label in enumerate(labels):
            row[column_label] = cm[i, j]

        df = df.append(pd.DataFrame.from_dict({row_label: row}, orient='index'))

    return df[labels]


if __name__ == '__main__':
    predict_plus()
