"""
HTML scrape a table, geocodes cities, creates csv
===

Takes a wikipedia article on the largest urban areas in the world,
html scrapes it using re, puts it into a pandas dataframe,
uses geopy to geocode lat/lon, and exports it to csv.

Data used in visual explorer: UrbanExplorer.ipynb

"""

import pandas as pd
import numpy as np
import re
from geopy.geocoders import Nominatim
from urllib.request import urlopen

"""Reads html into lines"""
response = urlopen("https://en.wikipedia.org/wiki/List_of_urban_areas_by_population")
html = response.read()
response.close()
html2 = html.decode("utf-8", "replace")
html3 = html2.splitlines()

"""Finds tables"""
html_tboo1 = [i for i, x in enumerate(html3) if re.search('<table', str(x)) is not None]
html_tboo2 = [i for i, x in enumerate(html3) if re.search('/table>', str(x)) is not None]

"""Creates list of list of table lines"""
html_tables = []
for i in range(0,len(html_tboo1)):
    html_tables.append(html3[html_tboo1[i]:html_tboo2[i]+1])

"""function to extract the headers from tables"""
def getHeaders(htmltable):
    html_boo1 = [i for i, x in enumerate(htmltable) if re.search('<th', str(x)) is not None]
    html_boo2 = [i for i, x in enumerate(htmltable) if re.search('/th>', str(x)) is not None]
    nh = len(html_boo1)
    h1 = [htmltable[html_boo1[i]:html_boo2[i]+1] for i in range(0,nh)]
    headers = []
    for i in range(0,nh):
        hs = ''
        for j in range(0, len(h1[i])):
            hs = hs + str(h1[i][j])
            if j != len(h1[i]) - 1:
                hs = hs + ' '
        headers.append(re.sub(r"<.*?>|b'|\\n'|\[.*\]",'',hs))
    return(headers)

html_boo1 = [i for i, x in enumerate(html_tables[1]) if re.search('<tr', str(x)) is not None]
html_boo2 = [i for i, x in enumerate(html_tables[1]) if re.search('/tr>', str(x)) is not None]

"""gets the second table in the page: the list of largest urban areas"""
h1 = [html_tables[1][html_boo1[i]+1:html_boo2[i]] for i in range(0,len(html_boo1))]

"""Fill in pandas dataframe line by line"""
biggercities = pd.DataFrame(columns=getHeaders(html_tables[1]))
htmlre = re.compile(r"<.*?>|\[.*\]")
countryre = re.compile(r"&#160;")
nonnumre = re.compile('[^-^[0-9]^%s^.]+' % ',')
for i in range(0,len(html_boo1)-1):
    firstlist = []
    for x in h1[i+1]:
        y = htmlre.sub('', str(x))
        if (not nonnumre.search(y.strip())):
            firstlist.append(y.replace(',',''))
        else:
            firstlist.append(y)
    firstlist[3] = countryre.sub('',firstlist[3])
    biggercities.loc[i] = firstlist

"""Now we want coordinates so we can map the cites.
   this makes geocode queries from city and country names"""
def makeGeoSearch(row):
    city = re.sub('–.*| \(.*\)|—.*| D.C.', '', row['City'])
    return(city + ', ' + row['Country'])
geosearch = biggercities.apply(makeGeoSearch, axis = 1)

"""Uses openstreetmap to find coordinates of each city.
   The longest stage of the process"""
lat = []
lon = []
geolocator = Nominatim()
print("Starting geocode...")
for i in range(len(geosearch)):
    try:
        location = geolocator.geocode(geosearch[i], timeout = 30)
        lat.append(location.latitude)
        lon.append(location.longitude)
    except:
        lat.append(None)
        lon.append(None)
        print(geosearch[i])
    if i % 100 == 0:
        print("%s left" % (len(geosearch) - i - 1))
        
biggercities['Search'] = geosearch
biggercities['Latitude'] = lat
biggercities['Longitude'] = lon

"""Renames columns, removing any non letter or integer
   and replacing spaces with underscores"""
newkeys = []
for x0 in biggercities.keys():
    x1 = re.sub('[^ ^a-z^A-Z^0-9]','',x0)
    x2 = re.sub(' ','_',x1)
    newkeys.append(x2)

columnchange = dict(zip(biggercities.keys(),newkeys))
biggercities = biggercities.rename(columns=columnchange)

"""export to csv"""
biggercities.to_csv('wikiurbancities.csv', index=False)