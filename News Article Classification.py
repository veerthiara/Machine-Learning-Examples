import urllib.request
import requests
from bs4 import BeautifulSoup
import ssl
import nltk
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords, wordnet
from string import punctuation
import collections
from collections import defaultdict
from heapq import nlargest
from math import log
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


class FrequencySummarizer:
    def __init__(self,min_cut=0.1,max_cut=0.9):
        self.min_cut=min_cut
        self.max_cut=max_cut
        self._stopwords=set(stopwords.words('english')+list(punctuation)+[u"'s",'"'] )

    def _compute_frequencies(self,word_sent,customstopwords=None):
        freq=defaultdict(int)
        if customstopwords is None:
            stopwords=set(self._stopwords)
        else:
            stopwords=set(customstopwords).union(self._stopwords)
        for sentence in word_sent:
            for word in sentence:
                if word not in stopwords:
                    freq[word]+=1
        m=float(max(freq.values()))
        for word in list(freq):
            freq[word]=freq[word]/m
            if freq[word]>=self.max_cut or freq[word]<=self.min_cut:
                del freq[word]
        return freq

    def extractfeatures(self,article,n,customstopwords=None):
        text=article[0]
        title=article[1]
        sent=sent_tokenize(text)
        word_sent=[word_tokenize(word.lower()) for word in sent]
        self._freq=self._compute_frequencies(word_sent,customstopwords)
        if n<0:
            return nlargest(len(self._freq.keys()),self._freq, key=self._freq.get)
        else:
            return nlargest(n,self._freq,key=self._freq.get)
    def extractrawfrequencies(self,article):
        text=article[0]
        title=article[1]
        sentences=sent_tokenize(text)
        word_sent=[word_tokenize(word.lower()) for word in sentences]
        freq=defaultdict(int)
        for s in word_sent:
            for word in s:
                if word not in self._stopwords:
                    freq[word]+=1
        return freq
    def summarize(self,article,n):
        text=article[0]
        ttitle=article[1]
        sentence=sent_tokenize(text)
        word_sent=[word_tokenize(word.lower()) for word in sentence]
        self._freq = self._compute_frequencies(word_sent)
        ranking = defaultdict(int)
        for i, sent in enumerate(word_sent):
            for word in sent:
                if word in self._freq:
                    ranking[i] += self._freq[word]
        sentences_index=nlargest(n,ranking,key=ranking.get)
        return[sentence[j] for j in sentences_index]



urlwashingtonpostnontech="https://www.washingtonpost.com/sports/"
urlnewyorktimesnontech="https://www.nytimes.com/section/sports?action=click&pgtype=Homepage&region=TopBar&module=HPMiniNav&contentCollection=Sports&WT.nav=page"
urlwashingtonposttech="https://www.washingtonpost.com/business/technology/"
urlnewyorktimestech="https://www.nytimes.com/section/technology?action=click&pgtype=Homepage&region=TopBar&module=HPMiniNav&contentCollection=Tech&WT.nav=page"
def getwashposttext(url,token):
    ssl._create_default_https_context = ssl._create_unverified_context
    response = requests.get(url)
    # THis is an alternative way to get the contents of a URL
    soup = BeautifulSoup(response.content,"lxml")
    text = ""
    if soup.find_all(token) is not None:
        text=''.join(map(lambda p:p.text, soup.find_all(token)))
        soup2=BeautifulSoup(text,"lxml")
        if soup2.find_all('p')!=[]:

            text=''.join(map(lambda p:p.text, soup2.find_all('p')))
    return text, soup.title.text

def getNYTText(url,token):
    response = requests.get(url)
    # THis is an alternative way to get the contents of a URL
    soup = BeautifulSoup(response.content,"lxml")
    page = str(soup)
    title = soup.find('title').text
    mydivs = soup.findAll("p", {"class":"story-body-text story-content"})
    text = ''.join(map(lambda p:p.text, mydivs))
    return text, title

def scrapesource(url,magicfrag='2017',scraperfunction=getNYTText,token='article'):
    urlbodies={}
    ssl._create_default_https_context = ssl._create_unverified_context
    request=urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response=urllib.request.urlopen(request)
    soup=BeautifulSoup(response,"lxml")

    numerrors=0
    for a in soup.find_all('a'):
        try:
            url = a['href']
            if ((url not in urlbodies) and
                    ((magicfrag is not None and magicfrag in url)
                     or magicfrag is None)):
                body= scraperfunction(url,token)
                if body and len(body)>0:
                    urlbodies[url]=body

        except:
            numerrors +=1
    return urlbodies
def scrapesourcex(url,magicfrag='2017',scraperfunction=getwashposttext,token='article'):
    urlbodies={}
    ssl._create_default_https_context = ssl._create_unverified_context
    request=urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response=urllib.request.urlopen(request)
    soup=BeautifulSoup(response,"lxml")

    numerrors=0
    for a in soup.find_all('a'):
        try:
            url = a['href']
            if ((url not in urlbodies) and
                    ((magicfrag is not None and magicfrag in url)
                     or magicfrag is None)):
                body= scraperfunction(url,token)
                if body and len(body)>0:
                    urlbodies[url]=body

        except:
            numerrors +=1
    return urlbodies

washingtonposttecharticles=scrapesource(urlwashingtonposttech,'2017',getwashposttext,'article')
washingtonpostnontecharticles=scrapesourcex(urlwashingtonpostnontech,'2017',getwashposttext,'article')
newyorktimestecharticles=scrapesource(urlnewyorktimestech,'2017',getNYTText,None)
newyorktimesnontecharticles=scrapesource(urlnewyorktimesnontech,'2017',getNYTText,None)

articlesummaries={}
print(len(washingtonposttecharticles))
print(len(newyorktimestecharticles))
print(len([newyorktimestecharticles,washingtonposttecharticles]))
# now getting the 25 most important word in each article and associating them with their url

for techurldictionary in [newyorktimestecharticles, washingtonposttecharticles]:
    for articleurl in techurldictionary:
        if len(techurldictionary[articleurl][0])>0:
            fs=FrequencySummarizer()
            summary=fs.extractfeatures(techurldictionary[articleurl],25)
            articlesummaries[articleurl]={'feature-vector':summary,'label':'Tech'}
for nontechurldictionary in [newyorktimesnontecharticles, washingtonpostnontecharticles]:
    for articleurl in nontechurldictionary:
        if len(nontechurldictionary[articleurl][0])>0:
            fs=FrequencySummarizer()
            summary=fs.extractfeatures(nontechurldictionary[articleurl],25)

            articlesummaries[articleurl]={'feature-vector': summary,'label':'Non-Tech'}
# function that gets link for the website to be tested
def getdoxydonkeytext(url,token):
    response=requests.get(url)
    soup=BeautifulSoup(response.content, "lxml")
    title=soup.find("title").text
    mydivs=soup.findAll("div",{"class":token})
    text=''.join(map(lambda p:p.text, mydivs))
    return text, title
# k nearest neighbor articles in our case we compare it with 5 most closest articles and then check if its tech of non tech
# we compare article summary of tech instance with the article summary of our train data
# we get which one aricle summary matches the most with our test data


testurl="http://doxydonkey.blogspot.in"
testarticle=getdoxydonkeytext(testurl,"post-body")
fs=FrequencySummarizer()
testarticlesummary=fs.extractfeatures(testarticle,25)
print(testarticlesummary)
#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
# now using KNN Classification
#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#

similarities={}
for articleurl in articlesummaries:
    onearticlesummary=articlesummaries[articleurl]['feature-vector']
    similarities[articleurl]=len(set(testarticlesummary).intersection(set(onearticlesummary)))
# using k nearest neighbor to classify if the article is Tech or not.
labels=defaultdict(int)
knn=nlargest(5,similarities,key=similarities.get)
print(knn)

for oneNeighbor in knn:
    print(labels[articlesummaries[oneNeighbor]['label']])
    labels[articlesummaries[oneNeighbor]['label']]+=1

nlargest(1,labels,key=labels.get)
print(nlargest(1,labels,key=labels.get))

#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#
# now using Naive Bayes Classification
#------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------#

cumulativerawfrequencies={'Tech':defaultdict(int),'Non-Tech':defaultdict(int)}
trainingdata={'Tech':newyorktimestecharticles,'Non-Tech':newyorktimesnontecharticles}
for label in trainingdata:
    for articleurl in trainingdata[label]:
        if len(trainingdata[label][articleurl][0])>0:
            fs=FrequencySummarizer
            rawfrequencies=fs.extractrawfrequencies(trainingdata[label][articleurl][0])
            for word in rawfrequencies:
                cumulativerawfrequencies[label][word] +=rawfrequencies[word]

techiness =1.0
nontechiness=1.0

for word in testarticlesummary:
    if word in cumulativerawfrequencies['Tech']:
        techiness *= 1e3*cumulativerawfrequencies['Tech'][word]/float(sum(cumulativerawfrequencies['Tech'].values()))
    else:
        techiness /= 1e3

    if word in cumulativerawfrequencies['Non-Tech']:
        nontechiness *= 1e3*cumulativerawfrequencies['Non-Tech'][word]/float(sum(cumulativerawfrequencies['Tech'].values()))
    else:
        nontechiness /= 1e3


# now we have to take each of these and scale according to overall techniess or non techiness

techiness=float(sum(cumulativerawfrequencies['Tech'].values()))/(float(sum(cumulativerawfrequencies['Tech'].values()))+ float(sum(cumulativerawfrequencies['Non-Tech'].values())))
nontechiness=float(sum(cumulativerawfrequencies['Non-Tech'].values()))/(float(sum(cumulativerawfrequencies['Tech'].values()))+ float(sum(cumulativerawfrequencies['Non-Tech'].values())))
if techiness>nontechiness:
    label='Tech'
else:
    label='Non-Tech'
print(label,techiness,nontechiness)