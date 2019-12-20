import numpy as np
import pandas as pd
from collections import Counter
import re
import csv

###Uses scraped data from earlier
fight = pd.read_csv('fight_data2.csv')
fighter = pd.read_csv('fighter_data2.csv')

fights = fight.iloc[:, 0:17]  # get rid of the white space columns...
fighters = fighter.iloc[:, 0:-1]  # same issue as above for no reason
fighters.isnull().values.ravel().sum()  # gives 836
fights.isnull().values.ravel().sum()  # gives 6646
###Fighters Headers
# ['First', 'Last', 'Height', 'Weight', 'Reach', 'Stance', 'Birth', 'SLpM','Str. Acc.', ' SApM', 'Str. Def.', 'TD Avg.', 'TD Acc.', 'TD Def.','Sub. Avg.', 'Wins', 'Losses', 'Draws', ' Last_3_W', ' Last_3_L',' W_Streak', ' L_Streak', ' KOs', ' Subs', ' UFC_Fights',' Fight_Time']

###Fights Headers
# ['Outcome', 'Fighter', 'Fightee', 'Str', 'TD', 'Sub', 'Pass', 'Str2','TD2', 'Sub2', 'Pass2', 'Name', 'Date', 'Method', 'Misc', 'Rounds','Time']

###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO
###TODO: Grabe Unique fighterID as url on UFCstats
###TODO: Functionalize the steps below for either fighter or fights to make it easier next time
###TODO: Change incorrect column names in scrape earlier
###TODO: Next iteration, add in rolling SLpM, etc instead of fixed values
###TODO: Next iteration count 5 round time and 3 round time
###TODO: Look at models for each weight class and/or championship fights
###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO###TODO

# Calculate average Passes and win/loss at which rounds
fights1 = fights.drop(['Name', 'Misc'], axis=1)  # no NaNs left
fights1 = fights1[(fights1.Outcome != 'draw') & (fights1.Outcome != 'nc')]
fighters1 = fighters.drop(['Draws'], axis=1)  # prolly dont need draws
fights1.columns = ['Outcome', 'Fighter', 'Fightee', 'Str1', 'Str2', 'TD1', 'TD2', 'Sub1', 'Sub2', 'Pass1', 'Pass2',
                   'Date', 'Method', 'Rounds', 'Time']

fighters2 = fighters1.dropna()  # should drop all rows that have nans in them

temphead = list(fighters2)  # remove all whitespace from column names...
for row, head in enumerate(temphead):
    temphead[row] = re.sub(r'\s+', "", head)
fighters2.columns = temphead
fighters2 = fighters2[fighters2.Birth != '--']  # Remove -- data (basically Na)
fighters2 = fighters2[fighters2.Fight_Time != 0]
fighters2 = fighters2[fighters2.Height != '--']
fighters2 = fighters2[fighters2.Reach != '--']
fighters2 = fighters2[fighters2.iloc[:, -2] != 0]

# Columns were labeled incorrectly
fighters2 = fighters2.rename(columns={"UFC_Fights": "Temp"})
fighters2 = fighters2.rename(columns={"Fight_Time": "UFC_Fights"})
fighters2 = fighters2.rename(columns={"Temp": "Fight_Time"})
### Use only fights which include the new list of fighters ###
fighter_names = pd.DataFrame(zip(fighters2["First"].str.cat(fighters2["Last"], sep=" "), fighters2["UFC_Fights"]))
fighter_names = fighter_names.rename(columns={0: "Fighter", 1: "UFC_Fights"})
fights2 = pd.merge(fights1, fighter_names, how='inner')
fighters_names_list = fighters2[fighters2.iloc[:, -2] != 0]  # make sure they have fight times
fighter_names_list = fighters_names_list["First"].str.cat(fighters_names_list["Last"], sep=" ")
fighters2['Name'] = fighters2.First.str.cat(fighters2.Last, sep=" ")
### Go thru the data and add in last 3 fights and streak data per fight
###TODO: Next iteration, add in rolling SLpM, etc instead of fixed values
###TODO: Next iteration count 5 round time and 3 round time
Win_Streak = []
Lose_Streak = []
Win3 = []
Loss3 = []
APasses = []
for f_name in fighter_names_list:
    W_str = 0
    L_str = 0
    Wins3 = 0
    Losses3 = 0
    wstreak = 0
    lstreak = 0
    counter = 0
    passes = 0
    temp = fights2[fights2.Fighter == f_name]
    temp = temp.iloc[::-1]
    for row, Bout in temp.iterrows():
        passes += Bout.Pass1
        if wstreak == 0:
            if Bout.Outcome == 'win':
                W_str += 1
                L_str = 0
                lstreak = 1
            if Bout.Outcome == 'loss':
                wstreak = 1
                W_str = 0
                lstreak = 0
        if lstreak == 0:
            if Bout.Outcome == 'loss':
                L_str += 1
                W_str = 0
                wstreak = 1
            if Bout.Outcome == 'win':
                lstreak = 1
                L_str = 0
                wstreak = 0
                W_str += 1
        if counter < 3:
            if Bout.Outcome == 'win':
                Wins3 += 1
            if Bout.Outcome == 'loss':
                Losses3 += 1
            counter += 1
        Win_Streak.append(W_str)
        Lose_Streak.append(L_str)
        Win3.append(Wins3)
        Loss3.append(Losses3)
    APasses.append(passes)
PassPF = APasses / (fighters2.UFC_Fights)

# date information (fights are most recent first) // Also Bool KO last fight? info
Months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10,
          'Nov': 11, 'Dec': 12}
date = []
for row, bout in fights2.iterrows():
    day = int(bout.Date[5:7])
    month = bout.Date[0:3]  # Should all be 3 letter abb
    year = int(bout.Date[-4:])  # Should get 4 digit year
    this_fight = 365 * (year - 1) + 30 * (Months[month] - 1) + (day)
    date.append(this_fight)

fights2['Date'] = date

###Go thru list of fights for unique fighter to add in fight time and other inter-fight deta
###TODO: Fix UFC_Fights to be rolling as well
###TODO: TEMP: fix what happens if fighters have the same name for Inter_time
name = fights2.Fighter[0]
Inter_time = []
Loss_Bool = []
KO_Bool = []
Last_time = []
mean_time = 295  # average time between fights (fix after removing outliers)
for row, fight in fights2.iterrows():
    if row == len(fights2) - 1:
        Inter_time.append(mean_time)
        KO_Bool.append(0)
        Loss_Bool.append(0)
        Last_time.append(0)
        break
    if fights2.iloc[row + 1].Fighter != name:
        name = fights2.iloc[row + 1].Fighter
        Inter_time.append(mean_time)
        KO_Bool.append(0)
        Loss_Bool.append(0)
        Last_time.append(0)
    else:
        Inter_time.append(fight.Date - fights2.iloc[row + 1].Date)
        mins = int(fights2.iloc[row + 1].Time[1])
        secs = int(fights2.iloc[row + 1].Time[3:5])
        Last_time.append((mins * 60 + secs) + (fights2.iloc[row + 1].Rounds - 1) * 5)
        if fights2.iloc[row + 1].Outcome == 'win':
            KO_Bool.append(0)
            Loss_Bool.append(0)
        if fights2.iloc[row + 1].Outcome == 'loss':
            Loss_Bool.append(1)
            if fights2.iloc[row + 1].Method == 'KO/TKO':
                KO_Bool.append(1)
            if fights2.iloc[row + 1].Method != 'KO/TKO':
                KO_Bool.append(0)

fights2['Inter_time'] = Inter_time
fights2['Loss_Bool'] = Loss_Bool
fights2['KO_Bool'] = KO_Bool
fights2['Last_time'] = Last_time

###TODO: Make sure first and last indicies work out well, they probably dont
CounterF = Counter(fights2.Fighter)
CounterW = Counter(fights2.Fighter)
CounterL = Counter(fights2.Fighter)
Fights = []  # actual ufc fights per bout up to that point, not total
Losses = []  # UFC losses
Wins = []  # UFC wins
wins1 = fights2.Wins.iloc[0]
losses1 = fights2.Losses.iloc[0]
fights = fights2.UFC_Fights.iloc[0]
name = fights2.Fighter.iloc[0]
i = 1
l = 1
w = 1
###TODO: Test to see if wins and losses is working correctly
numbers = CounterF[name]
for row, fight in fights2.iterrows():
    if row >= len(fights2) - 1:
        break
    Fights.append(numbers - i)
    i = i + 1
    if fight.Outcome == 'Win':
        Wins.append(wins1 - w)
        Losses.append(losses1)
        w = w + 1
    if fight.Outcome == 'Loss':
        Losses.append(losses1 - l)
        Wins.append(wins1)
        l = l + 1
    if fights2.Fighter.iloc[row + 1] != name:
        name = fights2.Fighter.iloc[row + 1]
        numbers = CounterF[name]
        i = 1
        l = 1
        w = 1

    # if fights2.iloc[row].Outcome == 'win':
    #  Wins.append(Wins[-1] -1)
    # if fights2.iloc[row].Outcome == 'loss':
    #  Losses.append(Losses[-1] -1)
Fights.append(0)
###remove name from fighters after this to preserve column indicies?###
fighters2 = fighters2.drop(columns='Name')

# Adding in age information age info is approx based on year only
fighters2['Age'] = fighters2['Birth'].str[-2:]  # Gives Ages if Current year is 2019
fighters2['Age'] = fighters2['Age'].apply(lambda x: 119 - int(x))

### Checking values in fighter features
Reaches = Counter(fighters2.loc[:, 'Reach']).keys()
Reach_Nums = Counter(fighters2.loc[:, 'Reach']).values()

Weights = Counter(fighters2.loc[:, 'Weight']).keys()
Weight_Nums = Counter(fighters2.loc[:, 'Weight']).values()

# Turns out stance doesnt matter, will remove as a feature
Stances = Counter(fighters2.loc[:, 'Stance']).keys()  # Ignore/Fix Open and Sideways (Switch?)
Stance_Nums = Counter(fighters2.loc[:, 'Stance']).values()

# Weight classes are: 115, 125, 135, 145, 155, 175, 185, 205, 225, 225+
# Be wary, womens classes are: 115, 125, 135, 145 and are mixed in

### Checking values in fights features###
Methods = Counter(fights1.loc[:, 'Method']).keys()  # Decision + U- + M- prolly, ignore CNC, DQ
Method_Nums = Counter(fights1.loc[:, 'Method']).values()

Outcomes = Counter(fights2.loc[:, 'Outcome']).keys()  # Decision + U- + M- prolly, ignore CNC, DQ
Outcome_Nums = Counter(fights2.loc[:, 'Outcome']).values()

Rounds0 = Counter(fights2.loc[:, 'Rounds']).keys()  # Decision + U- + M- prolly, ignore CNC, DQ
Round_Nums = Counter(fights2.loc[:, 'Rounds']).values()

# Remove fights with more than 5 rounds...
fights2 = fights2[fights2.Rounds != 6]

##Creating header list for new DF
headcopy = [column + str(2) for column in list(fighters2)]
headers = list(fighters2) + list(headcopy) + ['Method'] + ['Outcome'] + ['Rounds'] + ['Inter_time'] + ['Loss_Bool'] + [
    'KO_Bool'] + ['Last_time']
del headers[27]
del headers[26]
del headers[1]
del headers[0]
headers.insert(0, "Fighter")
headers.insert(25, "Fightee")
fight_train = pd.DataFrame(columns=headers)
templist = []
##Remove whitespace in header names
for row, head in enumerate(headers):
    headers[row] = re.sub(r'\s+', "", head)

##making a list with... Fighter, Fightee, Outcome, Method, General Stats to DF later
for row, bout in fights2.iloc[0:10].iterrows():
    df1 = fighters2[fighters2["First"].str.cat(fighters2["Last"], sep=" ") == bout.Fighter].values.tolist()
    if df1 == []:
        continue
    df1 = df1[0]
    df2 = fighters2[fighters2["First"].str.cat(fighters2["Last"], sep=" ") == bout.Fightee].values.tolist()
    if df2 == []:
        continue
    df2 = df2[0]

    # Add in results tofights2 predict ultimately
    newdf = df1 + df2
    newdf.append(bout.Method)
    newdf.append(bout.Outcome)
    newdf.append(bout.Rounds)
    newdf.append(bout.Inter_time)
    newdf.append(bout.Loss_Bool)
    newdf.append(bout.KO_Bool)
    newdf.append(bout.Last_time)
    year = int(Bout.Date[-4:])
    Age1 = year - int(newdf[6][-4:])
    Age2 = year - int(newdf[32][-4:])  ###I added one more column to fighters
    newdf[25] = Age1  # ATTN: These indicies work for the original 52 features
    newdf[51] = Age2  # ATTN: These indicies work for the original 52 features
    # fight_Date = Bout.
    # newdf[24] = #Age
    name1 = newdf[0] + ' ' + newdf[1]
    name2 = newdf[26] + ' ' + newdf[27]
    # these delete and then replace first last with name
    del newdf[27]
    del newdf[26]
    del newdf[1]
    del newdf[0]
    newdf.insert(0, name1)
    newdf.insert(25, name2)
    ###Changing all stats to just ints
    feet = int(newdf[1][0])
    inches = int(re.findall(r'\'(\d+)"', newdf[1])[0])
    newdf[1] = feet * 12 + inches
    feet = int(newdf[26][0])
    inches = int(re.findall(r'\'(\d+)"', newdf[26])[0])
    newdf[26] = feet * 12 + inches
    newdf[2] = re.sub(r'[^\d]', "", newdf[2])  # Weight1 in lbs
    newdf[3] = re.sub(r'[^\d]', "", newdf[3])  # Reach1 in inch
    newdf[27] = re.sub(r'[^\d]', "", newdf[27])  # Weight2 in lbs
    newdf[28] = re.sub(r'[^\d]', "", newdf[28])  # Reach2 in inch
    ### Changing stats to ints in here
    templist.append(newdf)
fight_train = fight_train.append(templist)
###Oddly making 106 columns, double but last half is just NA
fight_train = fight_train.iloc[:, 0:57]
fight_train.columns = headers
##Adding new features: Differentials
fight_train['Height_Dif'] = fight_train.apply(lambda row: row.Height - row.Height2, axis=1)
fight_train['Reach_Dif'] = fight_train.apply(lambda row: int(row.Reach) - int(row.Reach2), axis=1)
fight_train['Strike_Dif'] = fight_train.apply(lambda row: row.SApM - row.SApM2, axis=1)
fight_train['Age_Dif'] = fight_train.apply(lambda row: row.Age - row.Age2, axis=1)

###Add new features: height/weight ratio, Age/Age_dif function, time/fight?, reach/height ratio
fight_train['Height_Weight_ratio'] = fight_train.apply(lambda row: row.Height / int(row.Weight), axis=1)
fight_train['Height_Weight_ratio2'] = fight_train.apply(lambda row: row.Height2 / int(row.Weight2), axis=1)
fight_train['Ave_Time'] = fight_train.apply(lambda row: row.UFC_Fights / row.Fight_Time, axis=1)
fight_train['Ave_Time2'] = fight_train.apply(lambda row: row.UFC_Fights2 / row.Fight_Time2, axis=1)
fight_train['Reach_Height_ratio'] = fight_train.apply(lambda row: int(row.Reach) / row.Height, axis=1)
fight_train['Reach_Height_ratio2'] = fight_train.apply(lambda row: int(row.Reach2) / row.Height2, axis=1)
fight_train['Fight_Dif'] = fight_train.apply(lambda row: row.UFC_Fights - row.UFC_Fights2, axis=1)

###TODO: Add new features: Bool KO last bout?, days since last bout
# fight_train['UFC_Fight_Num'] = Fights ###undo this when I run all the data

###Remove names, birth and method, not needed for training (method maybe for later)
fight_train = fight_train.drop('Birth', 1)
fight_train = fight_train.drop('Birth2', 1)
fight_train = fight_train.drop('Fighter', 1)
fight_train = fight_train.drop('Fightee', 1)
fight_train = fight_train.drop('Method', 1)

###Make binary variables for Stance (1 and 2) and Result (Ortho, South, Switch) and (Win, Loss)
###Stance doesnt matter will remove as feature
fight_train['Stance_Ortho'] = fight_train.apply(lambda row: int(row.Stance == "Orthodox"), axis=1)
fight_train['Stance_South'] = fight_train.apply(lambda row: int(row.Stance == "Southpaw"), axis=1)
fight_train['Stance_Switch'] = fight_train.apply(lambda row: int(row.Stance == "Switch"), axis=1)

fight_train['Stance2_Ortho'] = fight_train.apply(lambda row: int(row.Stance2 == "Orthodox"), axis=1)
fight_train['Stance2_South'] = fight_train.apply(lambda row: int(row.Stance2 == "Southpaw"), axis=1)
fight_train['Stance2_Switch'] = fight_train.apply(lambda row: int(row.Stance2 == "Switch"), axis=1)

fight_train['Outcome'] = fight_train.apply(lambda row: int(row.Outcome == "win"), axis=1)

fight_train = fight_train.drop('Stance', 1)
fight_train = fight_train.drop('Stance2', 1)
###Output this as the training set for the fight data
fight_train.to_json('fight_train.json')

### Potentially wanna train per weight class, maybe not enough data?
###TODO: Change to weight classes by fights, not fighter
###TODO: Figure out what to do with championship rounds
Straw = fighters2[(fighters2['Weight'] <= '115lbs.')]  # these seem to be female
Fly = fighters2[(fighters2['Weight'] > '115lbs.') & (fighters2['Weight'] <= '125lbs.')]
Bantam = fighters2[(fighters2['Weight'] > '125lbs.') & (fighters2['Weight'] <= '135lbs.')]
Feather = fighters2[(fighters2['Weight'] > '135lbs.') & (fighters2['Weight'] <= '145lbs.')]
Light = fighters2[(fighters2['Weight'] > '145lbs.') & (fighters2['Weight'] <= '155lbs.')]
Welter = fighters2[(fighters2['Weight'] > '155lbs.') & (fighters2['Weight'] <= '170lbs.')]
Middle = fighters2[(fighters2['Weight'] > '170lbs.') & (fighters2['Weight'] <= '185lbs.')]
LightHeavy = fighters2[(fighters2['Weight'] > '185lbs.') & (fighters2['Weight'] <= '205lbs.')]
Heavy = fighters2[(fighters2['Weight'] > '205lbs.') & (fighters2['Weight'] <= '265lbs.')]
SuperHeavy = fighters2[(fighters2['Weight'] > '265lbs.')]