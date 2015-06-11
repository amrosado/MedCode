__author__ = 'arosado'

import requests
import pymongo
import json
import html5lib
import types
from bs4 import NavigableString, Tag
from MedNaturalLanguageProcessing import MedNaturalLanguageProcessing
from bs4 import BeautifulSoup

class WikiMedIcdInfoExtend:
    wikiSession = None
    mongoClient = None
    icdDatabase = None
    wikiMedInfoDatabase = None

    wikiSearchUrl = 'https://en.wikipedia.org?search='
    wikiBaseUrl = 'https://en.wikipedia.org/'

    def constructWikiInformationExtension(self):
        try:
            mainCodeCollection = None
            icdDatabaseCollections = self.icdDatabase.collection_names()
            if 'hierarchydiagnosisCodes' in icdDatabaseCollections:
                mainCodeCollection = self.icdDatabase.get_collection('hierarchydiagnosisCodes')
                mainCodeFullCursor = mainCodeCollection.find()
                for code in mainCodeFullCursor:
                    codeName = code['hierarchyGroup']
                    codeData = json.loads(code['data'])
                    urlSearch = self.wikiSearchUrl + codeData['codeName']
                    wikiRequest = self.wikiSession.get(urlSearch)
                    wikiHtmlSoup = BeautifulSoup(wikiRequest.content)
                    data = self.processWikiInformationHtml(wikiHtmlSoup)
        except:
            'Failed to extend medical code information from wikipedia data'

    def analyzeCodeInformation(self, code):
        pass

    def processWikiInformationHtml(self, htmlSoup):
        wikiInfo = htmlSoup.find('table', id='infobox')
        contentText = htmlSoup.find('div', id='mw-content-text')
        pageTitle = htmlSoup.find('h1', id='firstHeading')
        data = {}
        sectionData = {}
        sectionTextHolder = []
        sectionLinkHolder = []
        imageLinkHolder = []
        sectionDataHolder = []
        referenceHolder = []
        if contentText != None:
            mainContentChildren = contentText.children
            data['title'] = pageTitle.text
            sectionData['name'] = 'summary'
            for contentChild in mainContentChildren:
                if type(contentChild) is Tag:
                    if contentChild.name == 'h2':
                        sectionData['text'] = sectionTextHolder
                        sectionData['links'] = sectionLinkHolder
                        if len(sectionLinkHolder) > 0:
                            sectionData['links'] = sectionLinkHolder
                        if len(imageLinkHolder) > 0:
                            sectionData['imageLinks'] = imageLinkHolder
                        sectionDataHolder.append(sectionData)
                        sectionData = {}
                        sectionLinkHolder = []
                        imageLinkHolder = []
                        sectionTextHolder = []
                        sectionData['sectionName'] = contentChild.text
                    elif contentChild.name == 'div':
                        imageLinks = contentChild.find_all('a', 'image')
                        articleLinks = contentChild.find_all('a', 'hatnote')
                        referenceSpans = contentChild.find_all('span', 'reference-text')
                        if referenceSpans != None:
                            for referenceSpan in referenceSpans:
                                referenceLinks = referenceSpan.find_all('a')
                                if referenceLinks != None:
                                    referenceText = referenceSpan.get_text()
                                    referenceLinkHolder = []
                                    for referenceLink in referenceLinks:
                                        referenceLinkHolder.append([referenceText, referenceLink.text, referenceLink['href']])
                                    referenceHolder.append({'text': referenceText, 'links': referenceLinkHolder})
                                else:
                                    referenceHolder.append([referenceText])
                        if imageLinks != None:
                            for imageLink in imageLinks:
                                imageLinkHolder.append(imageLink['href'])
                        if articleLinks != None:
                            for articleLink in articleLinks:
                                sectionLinkHolder.append([articleLink['title'], articleLink['href']])
                    elif contentChild.name == 'p':
                        contentLinks = contentChild.find_all('a')
                        if contentLinks != None:
                            for link in contentLinks:
                                sectionLinkHolder.append([link.text, link['href']])
                        sectionTextHolder.append(contentChild.get_text())
            data['sectionData'] = sectionDataHolder
            data['referenceInfo'] = referenceHolder
            pass



    def processWikiSearchHtml(self, htmlSoup):
        htmlSoup

    def __init__(self):
        self.wikiSession = requests.Session()
        try:
            self.mongoClient = pymongo.MongoClient('localhost', 27017)
            self.icdDatabase = self.mongoClient.get_database('Icd10')
            self.wikiMedInfoDataBase = self.mongoClient.get_database('WikiMedInfo')
        except:
            print('Failed to initalize mongodb database connection')

wikiExtend = WikiMedIcdInfoExtend()
wikiExtend.constructWikiInformationExtension()
