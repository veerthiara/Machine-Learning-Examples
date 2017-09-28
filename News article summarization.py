import urllib.request
from bs4 import BeautifulSoup
import ssl
import nltk
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords, wordnet
from string import punctuation
import collections
from collections import defaultdict
from heapq import nlargest
url='https://blogs.scientificamerican.com/observations/states-can-lead-the-way-on-climate-change/'
#url='https://www.washingtonpost.com/news/innovations/wp/2017/09/25/teenage-suicide-is-extremely-difficult-to-predict-thats-why-some-experts-are-turning-to-machines-for-help/'
def getwashposttext(url):
    ssl._create_default_https_context = ssl._create_unverified_context
    page=urllib.request.urlopen(url).read().decode('utf8')
    soup=BeautifulSoup(page,"lxml")
    text=""

    if soup.find_all('p') is not None:
        text=''.join(map(lambda p: p.text, soup.find_all('p')))
    return text

class FrequencySummarizer:
    def __init__(self,min_cut=0.1,max_cut=0.9):
        self.min_cut=min_cut
        self.max_cut=max_cut
        self._stopwords=set(stopwords.words('english')+list(punctuation))
    def _compute_frequencies(self,word_sent):
        freq=defaultdict(int)
        for sentence in word_sent:
            for word in sentence:
                if word not in self._stopwords:
                    freq[word] +=1
        # normalizing the frequencies because then all frequencies between 0 and 1.
        max_freq=float(max(freq.values()))
        for word in list(freq):
            freq[word]=freq[word]/max_freq
            if freq[word]>=self.max_cut or freq[word]<=self.min_cut:
                del freq[word]
        return freq
    # now we make a function that checks the number of times the most occuring words comes in a sentence and then rank according to that
    def summarize(self, text,n):
        sents=sent_tokenize(text)
        assert n <= len(sents)
        word_sent=[word_tokenize(s.lower()) for s in sents]
        self._freq=self._compute_frequencies(word_sent)
        ranking = defaultdict(int)
        for i,sent  in enumerate(word_sent):
            for word in sent:
                if word in self._freq:
                    ranking[i] += self._freq[word]
        print(ranking)
        print(len(ranking))
        print(len(sents))
        sents_idx = nlargest(n,ranking,key=ranking.get)
        return [sents[j] for j in sents_idx]




textreturn=getwashposttext(url)
fs= FrequencySummarizer()
x= fs.summarize(textreturn,2)
for i in x:
    print(i)