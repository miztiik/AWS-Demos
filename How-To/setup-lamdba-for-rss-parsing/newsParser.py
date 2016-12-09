#!/usr/bin/python
# -*- coding: utf-8 -*-
import feedparser, json
import time
from datetime import datetime
import os.path
import pdb

rssUrlList = {
        "topstories": { 
            "googlenews"        : "https://news.google.co.in/news?cf=all&hl=en&pz=1&ned=in&output=rss",
            "economictimes"     : "http://economictimes.indiatimes.com/rssfeedstopstories.cms"
        },

        "india" : {
            "googlenews"        : "http://news.google.co.in/news?cf=all&hl=en&pz=1&ned=in&topic=n&output=rss",
            "bbc"               : "http://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
            "hindu"             : "http://www.thehindubusinessline.com/news/national/?service=rss"
        },

        "world" : {
            "googlenews"        : "https://news.google.co.in/news?cf=all&hl=en&pz=1&ned=in&topic=w&output=rss",
            "bbc"               : "http://feeds.bbci.co.uk/news/world/rss.xml",
            "hindu"             : "http://www.thehindubusinessline.com/news/national/?service=rss"
        },

        "business" : {
            "economictimes"     : "http://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "hindu"             : "http://www.thehindubusinessline.com/markets/?service=rss",
            "googlenews"        : "http://news.google.co.in/news?cf=all&hl=en&pz=1&ned=in&topic=b&output=rss"
        },

        "opinion" : {
            "hindu"             : "http://www.thehindubusinessline.com/opinion/?service=rss",
            "businessinsider"   : "http://www.businessinsider.in/rss_ptag_section_feeds.cms?query=indiainsider"
        }

    
}

rssUrlListTest = {
        "topstories": { 
            "googlenews"        : "https://news.google.co.in/news?cf=all&hl=en&pz=1&ned=in&output=rss",
            "economictimes"     : "http://economictimes.indiatimes.com/rssfeedstopstories.cms"
        }   
}


"""
Funtion to Iterate dictionary of dictionaries
@Arg - Takes one arugment of type dictionary
Checks if the value of a dictionary is a dictionary and call itself
If NOT dictionary calls the getNews Fuction
"""

def recurseDict(d,pk=None):
    pk = pk
    for k, v in d.items():
        if isinstance(v, dict):
            recurseDict( d[k], k )
        else:
            # print( "\n{0} : {1} : {2}".format(pk,k, v) )
            getNews( pk, k, v )


"""
Function to collect data from BBC RSS Feed for india
Get only the summary for articles which were published today
"""
def getNews(sectiontitle, mediagroup, url):

    newsFeed = {}
    articles = {}
    newsitems = []
    
    try:
        feed = feedparser.parse(url)
        if feed:
            for entry in feed['entries']:

                newsTxt = ''

                last_updated = time.mktime( entry['published_parsed'] )
                currLocalTime = time.mktime(time.localtime())

                publishedTime = str( entry['published_parsed'][3] ) + " hours ago."
                # 16 Hours ( 16 * 3600)
                cutOffTime = 57600

                # Check if the articles are lesser than a given time period
                if ( currLocalTime - last_updated )  < cutOffTime:
                    if ( mediagroup == "googlenews" ) or ( mediagroup == "businessinsider" ):
                        newsTxt = entry['title_detail']['value'] 
                    elif ( mediagroup == "economictimes" ):
                        newsTxt = entry['title']
                    else:
                        newsTxt = entry['summary_detail']['value']
                
                if newsTxt:
                    newsitems.append( newsTxt + ' , Reported at around ' + publishedTime  )

            articles[ 'newsitems' ] = newsitems
            articles[ 'sectiontitle' ] = sectiontitle
            articles[ 'mediagroup' ] = mediagroup

    except:
        print "Error in Section:{0} - {1}".format( sectiontitle, url )
        articles = { mediagroup : { "newsitems" : "Error in Section" + url }, "sectiontitle":sectiontitle}
    
    # Lets collate the news
    collateNews ( articles )
    return



"""
Funtion to write the data to file
"""
def writeToFile(dataDump):
    outputDir = os.path.abspath(__file__ + "/../../")
    tmpFileName = 'newsArticles-{0}'.format( datetime.now().strftime("%Y-%m-%d-%H-%M-%S") )
    outputFileName = os.path.join( outputDir, "output" , tmpFileName )

    # write to file only if the dictionary is not empty
    if dataDump:
        with open( outputFileName , 'w+') as f:
            json.dump( dataDump, f, indent=4,sort_keys=True)

"""
Merge same section titles together
"""
def collateNews( newsFeed ):
    #pdb.set_trace()
    # Check if the section title dictionary is already in the collacted news items,
    # If it is there, then add that dictionary to the existing one

    tempDict = {}
    tempDict[ newsFeed['mediagroup'] ] = newsFeed[ 'newsitems' ]

    if newsFeed['sectiontitle'] in collatedNews:
        # collatedNews[ newsFeed['sectiontitle'] ][  ].update( newsFeed[ 'newsitems' ] )
        collatedNews[ newsFeed['sectiontitle'] ].update( tempDict )
    
    # update the section if it is not there already
    else:
        # collatedNews.update ( newsFeed )

        collatedNews[ newsFeed['sectiontitle'] ] = tempDict

"""
Add custom acceptable elements so iframes and other potential video
elements will get synched.
"""
def add_custom_acceptable_elements(elements):

    elements += list(feedparser._HTMLSanitizer.acceptable_elements)
    feedparser._HTMLSanitizer.acceptable_elements = set(elements)
# feedparser._HTMLSanitizer.acceptable_elements.remove('p')
# custom_acceptable_elements = ['iframe', 'embed', 'object',]
# add_custom_acceptable_elements(custom_acceptable_elements)


# Lets collect some news
collatedNews = {}
recurseDict( rssUrlList )

# recurseDict( rssUrlListTest )
writeToFile( collatedNews )
