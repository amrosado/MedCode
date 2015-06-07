__author__ = 'arosado'

import requests
import pymongo

class WikiMedIcdInfoExtend:
    mongoClient = None
    icdDataBase = None
    wikiMedInfoDataBase = None

    def 

    def processWikiInformationHtml(self, htmlsoup):

    def processWikiSearchHtml(self, htmlsoup):
        pass

    def __init__(self):
        self.ICD10Session = requests.Session()
        try:
            self.mongoClient = pymongo.MongoClient('localhost', 27017)
            self.icdDataBase = self.mongoClient.get_database('Icd10')
            self.wikiMedInfoDataBase = self.mongoClient.get_database('WikiMedInfo')
        except:
            print('Failed to initalize mongodb database connection')
