import requests
from bs4 import BeautifulSoup
import re
import time

def scrapeFighterPage(link, fighter_data, fight_file, fighter_file):
  white = re.compile(r'\s+')
  fighter_soup = BeautifulSoup(requests.get(link).text, features="html.parser")
  try:
    fighter_details = fighter_soup.find_all('div', {'class': "b-fight-details"})[0]
  except:
    import time
    time.sleep(1)
    fighter_details = fighter_soup.find_all('div', {'class': "b-fight-details"})[0]

  basic_info = fighter_details.find_all('div')[0]

  stats = basic_info.find_all('li')

  for stat in stats:
      text = stat.text
      text = re.sub(white, '', text)
      stat = text.split(':')[1]
      fighter_data.append(stat.replace(',', ' '))

  career_stats = fighter_soup.find_all('div', {'class': "b-list__info-box-left"})[0]

  stats = career_stats.find_all('li')

  for stat in stats:
      text = stat.text
      text = re.sub(white, '', text)
      if text == "":
          continue
      stat = text.split(':')[1].replace('%', '')
      fighter_data.append(stat)

  record = \
  fighter_soup.find_all('span', {'class': "b-content__title-record"})[0].text.strip().split(': ')[
      1].split('-')
  fighter_data += record

  fight_details = fighter_soup.find_all('table', {'class': "b-fight-details__table"})[0]
  fights = fight_details.find_all('tr', {'class': "b-fight-details__table-row"})[1:]
  last_3_wins = 0
  last_3_loss = 0
  w_streak = 0
  l_streak = 0
  counter = 0
  wstreak = 0
  lstreak = 0
  kos = 0
  subs = 0
  UFC_fights = 0
  tot_UFC_fight_time = 0
  for fight in fights:
      UFC_fights += 1
      try:
          outcome = fight.find_all('i', {'class': "b-flag__text"})[0].text
      except Exception:
          outcome = 'next'
      if outcome == 'next':
          continue

      if wstreak == 0:
          if outcome == 'win':
              w_streak += 1
          if outcome == 'loss':
              wstreak = 1
      if lstreak == 0:
          if outcome == 'loss':
              l_streak += 1
          if outcome == 'win':
              lstreak = 1
      if counter < 3:
          if outcome == 'win':
              last_3_wins += 1
          if outcome == 'loss':
              last_3_loss += 1
          counter += 1

      fighters = [elem.text.strip() for elem in fight.find_all('td')[1].find_all('a')]

      str_data = []
      for str_info in fight.find_all('td')[2:6]:
          str_data += [elem.text.strip() for elem in str_info.find_all('p')]

      date_data = fight.find_all('td')[6]
      event_name = date_data.find_all('a')[0].text.strip()
      event_date = date_data.find_all('p')[1].text.strip().replace(',', ' ')

      method_data = fight.find_all('td')[7]
      method = method_data.find_all('p')[0].text.strip()
      method_extra = method_data.find_all('p')[1].text.strip()
      if method == 'KO/TKO':
          kos += 1
      if method == 'SUB':
          subs += 1
      rounds = fight.find_all('td')[8].find_all('p')[0].text.strip()
      tot_UFC_fight_time += (float(rounds) - 1) * 5
      time = fight.find_all('td')[9].find_all('p')[0].text.strip()
      tot_UFC_fight_time += int(time[0]) + float(time[-2:])/60

      fight_data = [outcome] + fighters + str_data + [event_name, event_date, method, method_extra,
                                                      rounds, time]

      fight_file.write(','.join(fight_data) + '\n')
  tot_UFC_fight_time = round(tot_UFC_fight_time, 2)
  #print(tot_UFC_fight_time, UFC_fights)
  fighter_data.append(str(last_3_wins))
  fighter_data.append(str(last_3_loss))
  fighter_data.append(str(w_streak))
  fighter_data.append(str(l_streak))
  fighter_data.append(str(kos))
  fighter_data.append(str(subs))
  fighter_data.append(str(tot_UFC_fight_time))
  fighter_data.append(str(UFC_fights))
  #print(fighter_data)
  fighter_file.write(','.join(fighter_data) + '\n')

def scrapeLetterPage(char, fight_file, fighter_file):
  soup = BeautifulSoup(requests.get(f"http://ufcstats.com/statistics/fighters?char={char}&page=all").text, features="html.parser")
  for row in soup.find_all('tr', {'class': "b-statistics__table-row"})[2:]:

      fighter_data = []
      cols = row.find_all('td', {'class': "b-statistics__table-col"})

      link = cols[0].find_all('a')[0]["href"]

      first_name = cols[0].find_all('a')[0].text
      last_name = cols[1].find_all('a')[0].text

      fighter_data = [first_name, last_name]
      try:
        scrapeFighterPage(link, fighter_data, fight_file, fighter_file)
      except:
        time.sleep(1)
        scrapeFighterPage(link, fighter_data, fight_file, fighter_file)

def scrape():
    with open("fighter_data.csv", 'w') as fighter_file:
        fighter_file.write(
            "First,Last,Height,Weight,Reach,Stance,Birth,SLpM,Str. Acc., SApM,Str. Def.,TD Avg.,TD Acc.,TD Def.,Sub. Avg.,Wins,Losses,Draws, Last_3_W, Last_3_L, W_Streak, L_Streak, KOs, Subs, UFC_Fights, Fight_Time, \n")
        with open("fight_data.csv", 'w') as fight_file:
            fight_file.write(
                "Outcome,Fighter,Fightee,Str,TD,Sub,Pass,Str2,TD2,Sub2,Pass2,Name,Date,Method,Misc,Rounds,Time\n")
            for char in 'abcdefghijklmnopqrstuvwxyz':
                print(f"Searching names starting with {char}")
                try:
                  scrapeLetterPage(char, fight_file, fighter_file)
                except:
                  time.sleep(1)
                  scrapeLetterPage(char, fight_file, fighter_file)

#if __name__ == '__main__':
 #   scrape()
  #  print("Done")