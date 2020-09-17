import os.path
from urllib.request import urlopen
from bs4 import BeautifulSoup as bs4
import pandas as pd
from tabulate import tabulate
import numpy as np
from pathlib import Path
import time
 
# Main URL to visit
main_URL = 'https://handyanrufe.de/rufnummer/'
data_folder = Path(r'tmobile/')
start_time = time.time()

def get_carrier(soup):
    first_b = soup.find_all('b')[0] # find the first 'b' tag
    prefix = first_b.next_element
    carrier_string = str(prefix.next_element)
    carrier = carrier_string.partition("Anbieter")[2] # get carrier name alone
    carrier = carrier.replace(" ", "").replace(".", "") # clean-up carrier string
    return carrier

# turns a series of numbers into a compact
# shorthand representation of said series.
# e.g: [12,13,14,15] -> ['12 ... 15']
def detect_series(num_list):
    _list = []
    count = 0
    start_num = 0
    end_num = 0
    for i in range( 0,len(num_list) -1 ):
        num1 = int(num_list[i])
        num2 = int(num_list[i+1])
        if num1 == num2-1:
            if count==0:
                start_num = num1
                end_num = num2
                count=1
            else:
                count+=1
                end_num = num2
        else:
            if count>0:
                _list.append( str(start_num)+' ... '+str(end_num) )
            else:
                _list.append( num1 )
            count=0
    # still have streak?
    if count>0: _list.append( str(start_num)+' ... '+str(end_num) )
    return _list
    
# prefixes to visit

prefixes = []
tmobile = ['0151','01511','01512','01513','01514','01515','01516','01517','01518','01519','0160','0170','0171','0175']
#voda    = ['0152','01521','01522','01523','01524','01525','01526','01527','01528','01529','01520','0162','0172','0173','0174']
#eplus   = ['01571','01572','01573','01574','01575','01576','01577','01578','01579','0163','0177','0178']
#o2      = ['0159','01591','01592','01593','01594','01595','01596','01597','01598','01599','0176','0179']

prefixes.extend(tmobile)
#prefixes.extend(voda)
#prefixes.extend(eplus)
#prefixes.extend(o2)

# variable for the data we are scraping
data_array = []
cur_prefix = ''
csv_filepath = ""

# Find files we need to scrape
for prefix in prefixes:
    # set current prefix
    cur_prefix = prefix
    file = cur_prefix+'.csv'
    # build path...
    csv_filepath = Path.joinpath(data_folder, file)
    # if file does /not/ exist...
    if not os.path.isfile( csv_filepath ):
        print ('file non-existant: ' + str(csv_filepath))
        break # break out
    else:
        continue

# announce scraping
print('------------Now scraping into file: '+str(csv_filepath)+'------------')

# the scraped data as a list object
data = []
data_complete_set = []

# scrape all pages in suffix range
for suffix in range(999+1):
    data = [] # the data we want to extract 
    suffix_str = str(suffix).zfill(3) # turn suffix# into string and front-pad with zero
    
    # create URL to visit
    URL = main_URL + cur_prefix + '/' + suffix_str 
    print('Now scraping:' +" '"+ URL +"' ") # announce page being scraped
    
    # get the page
    raw_HTML = urlopen(URL) # request and get the page html
    soup = bs4(raw_HTML, features="lxml")  # 'soupify' the HTML
    
    # scraping data start
    # ---get carrier---
    carrier = get_carrier(soup)    
    data.append(carrier) # <-- add carrier to data
    # ---get subcarriers---
    subcarrier_table = soup.find_all('table')[0]
    trs = subcarrier_table.find_all('tr')
    subcarriers = []
    for tr in trs:
        subcarrier = tr.text
        subcarriers.append( subcarrier )
    data.append(subcarriers) # <-- add subcarriers to data
    # ---get prefix 1---
    data.append( prefix ) # <-- add subcarriers to data
    # ---get prefix 2---
    data.append( suffix_str ) # <-- add subcarriers to data
    # ---get the numbers availble for this prefix and suffix combo---
    # find the bottom div by trying locating it via its unique styling,
    # because it has no ID or class.
    # Then rigourously clean/massage the number data
    numbers_div = soup.find('div', attrs={ 'style':'border:1px solid;width:90%;height:250px;overflow:auto;' }  )
    numbers_str = numbers_div.text # remove all tags, leave only actual string data
    numbers_str = numbers_str.replace("/", "").replace(" ", "") # remove '/' and ' ' 
    numbers_str = numbers_str.split(',') # split into array using ','
    # dicts can't hold copies of keys in key<->value pairs, so we use it to eliminate copies of numbers...
    numbers_dict = list( dict.fromkeys( numbers_str ) ) 
    # start putting numbers back into a list
    numbers_list = []
    for number in numbers_dict:
        number_reduced = number[-4:] # cut all but the last 4 chars of the number
        if number != "": numbers_list.append(number_reduced) # if number not empty, append
    numbers_list = detect_series(numbers_list) # turn numbers into just a series
    data.append(numbers_list) # <-- add numbers to data
    data_complete_set.append( data ) # <-- add all our data to the entire set
    print( "   Data retrieved -->  " + str( data ) )
# end-of: for suffix in range(999+1)


# --Now finally save our entire dataset to CSV and also tabulate it--
# Turn into a Pandas dataframe from array...
df = pd.DataFrame(data_complete_set, columns=["Carrier", "Subs", "Prefix-1", "Prefix-2", "NumberRange"])
# Save to a CSV file without indexes
df.to_csv(csv_filepath, index = False)
# done
print("-------------------------------------------")
print("Scraping complete. Time taken: %.2f seconds" % (time.time() - start_time))
