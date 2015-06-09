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

        if contentText != None:
            mainContentChildren = contentText.children
            for contentChildren in mainContentChildren:
                if type(contentChildren) is Tag:
                    if contentChildren.name == 'div':
                        pass
                    if contentChildren.name == 'p':
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
