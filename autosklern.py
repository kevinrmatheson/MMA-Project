from sklearn_pandas import DataFrameMapper, cross_val_score
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
import sklearn.preprocessing, sklearn.decomposition, sklearn.linear_model, sklearn.pipeline, sklearn.metrics
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import datasets, svm, metrics
from sklearn.inspection import permutation_importance
from sklearn.metrics import log_loss
###Import the fight data
#Original Fight data includes Championship (5 round) fights as womens
#Model2 will remove both of these to see effects
fight_train = pd.read_json('fight_train.json')
###Removing all fights with 4 or 5 rounds (best I can think of for now)
#fight_train = fight_train[fight_train.Rounds < 4]

fight_train = fight_train.drop('Rounds', axis = 1)#For predicting Outcome remove rounds!

#fight_train = fight_train.drop('Outcome', axis = 1)
### https://stackabuse.com/random-forest-algorithm-with-python-and-scikit-learn/
q = range(66)#56 for all features, 55 for no Outcome/Rounds 49 to ignore stances
temp = list(q[:44]) + list(q[45:])
X = fight_train.iloc[:, temp].values # this is gonna be everything else
y = fight_train.Outcome.values #this is gonna be win/loss and # of rounds
data = {'Wins':fight_train.Wins , 'Losses':fight_train.Losses}
X_base = pd.DataFrame(data)
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
#X_train, X_test, y_train, y_test = train_test_split(X_base, y, test_size=0.2, random_state=0) #Base model only using W/L record
from sklearn.preprocessing import StandardScaler

#sc = StandardScaler() #scaling might not be neccesary, as all values are like 0-40
#X_train = sc.fit_transform(X_train)
#X_test = sc.transform(X_test)

from sklearn.ensemble import RandomForestClassifier

regressor = RandomForestClassifier(n_estimators=1000, random_state=0, oob_score = True)# we'll likely do many more trees
regressor.fit(X_train, y_train)
y_pred = regressor.predict(X_test)
predictions = regressor.predict_proba(X_test)

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

print(confusion_matrix(y_test,y_pred))
print(classification_report(y_test,y_pred))
print(accuracy_score(y_test, y_pred))
print(log_loss(y_test, predictions))

importances = regressor.feature_importances_
std = np.std([tree.feature_importances_ for tree in regressor.estimators_],
             axis=0)
indices = np.argsort(importances)[::-1]

print("Feature ranking:")

for f in range(X.shape[1]):
    print(str(f), list(fight_train)[indices[f]], importances[indices[f]])

# Plot the feature importances of the forest
plt.figure()
plt.title("Feature importances")
plt.bar(importances[indices],range(X.shape[1]),
       color="r", xerr=std[indices], align="center")
plt.yticks(range(X.shape[1]), [list(fight_train)[i] for i in indices])
plt.ylim([-1, X.shape[1]])
plt.show()

result = permutation_importance(regressor, X_test, y_test, n_repeats=10,
                                random_state=42, n_jobs=2)
sorted_idx = result.importances_mean.argsort()

fig, ax = plt.subplots()
ax.boxplot(result.importances[sorted_idx].T,
           vert=False, labels=fight_train.iloc[:, temp].columns[sorted_idx])
ax.set_title("Permutation Importances (test set)")
fig.tight_layout()
plt.show()