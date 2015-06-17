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

    medNLP = None

    wikiSearchUrl = 'https://en.wikipedia.org?search='
    wikiBaseUrl = 'https://en.wikipedia.org/'

    def reprocessIcdCodes(self):
        try:
            self.icdDatabase.drop_collection('processedDiagnosisCodes')
            processedCodeCollection = self.icdDatabase.get_collection('processedDiagnosisCodes')

            icdDatabaseCollections = self.icdDatabase.collection_names()
            if 'hierarchydiagnosisCodes' in icdDatabaseCollections:
                codeCollection = self.icdDatabase.get_collection('hierarchydiagnosisCodes')

                codeFullCursor = codeCollection.find()
                for code in codeFullCursor:
                    codeData = None
                    codeIdentifer = code['hierarchyGroup']
                    findProcessedCode = processedCodeCollection.find_one({'code': codeIdentifer})
                    if findProcessedCode == None:
                        codeData = json.loads(code['data'])
                        processedCodeInfo = self.medNLP.breakdownCodeData(code, codeData)
                        dump = json.dumps(processedCodeInfo)
                        if codeData != None:
                            processedCodeCollection.insert({'code': codeIdentifer, 'data': dump, 'codeName': codeData['codeName']})
                            codeData = processedCodeInfo
                            print('Reprocessed and inserted into database code: '+codeIdentifer)
                        else:
                            print('Could not insert reprocessed code... check program.')
        except:
            print('Failed to reprocess ICD 10 code information')

    def constructWikiInformationExtension(self):
        try:
            processedCodeCollection = self.icdDatabase.get_collection('processedDiagnosisCodes')
            wikiInfoCollection = self.wikiMedInfoDatabase.get_collection('wikiInfo')

            processedCodeFullCursor = processedCodeCollection.find()

            for code in processedCodeFullCursor:
                codeData = json.loads(code['data'])

                urlSearch = self.wikiSearchUrl + codeData['codeName']
                wikiRequest = self.wikiSession.get(urlSearch)
                wikiHtmlSoup = BeautifulSoup(wikiRequest.content)
                data = self.processWikiInformationHtml(wikiHtmlSoup)

                findWikiInfo = wikiInfoCollection.find_one({'code': codeData['data']})
                if findWikiInfo == None:
                    dump = json.dumps(data)
                    if codeData != None:
                        wikiInfoCollection.insert({'code': codeData['code'], 'data': dump, 'codeName': codeData['codeName']})
                        pass
        except:
            'Failed to extend medical code information from wikipedia data'

    def analyzeCodeInformation(self, code):
        pass

    def processWikiInformationHtml(self, htmlSoup):
        wikiInfos = htmlSoup.find_all('table', 'infobox')
        contentText = htmlSoup.find('div', id='mw-content-text')
        pageTitle = htmlSoup.find('h1', id='firstHeading')
        lastModified = htmlSoup.find('li', id='footer-info-lastmod')
        data = {}
        sectionData = {}
        sectionTextHolder = []
        sectionLinkHolder = []
        imageLinkHolder = []
        sectionDataHolder = []
        referenceHolder = []

        infoBoxHolder = []

        if len(wikiInfos) == 0:
            return None

        if lastModified != None:
            data['lastModified'] = lastModified.get_text()

        if wikiInfos != None:
            for wikiInfo in wikiInfos:
                infoBox = {}
                wikiInfoTbodies = wikiInfo.find_all('tbody')
                rowHolder = []
                for wikiInfoTBody in wikiInfoTbodies:
                    wikiInfoChildren = wikiInfoTBody.children
                    for wikiInfoChild in wikiInfoChildren:
                        if type(wikiInfoChild) == Tag:
                            if 'title' not in infoBox:
                                infoBox['title'] = wikiInfoChild.get_text()
                            else:
                                row = {}
                                wikiInfoChildChildren = wikiInfoChild.children
                                for wikiInfoChildChild in wikiInfoChildChildren:
                                    if type(wikiInfoChildChild) == Tag:
                                        infoImage = wikiInfoChildChild.find('img')
                                        infoLink = wikiInfoChildChild.find('a')
                                        if 'style' not in wikiInfoChildChild.attrs:
                                            info = wikiInfoChildChild.get_text()
                                            if infoLink != None:
                                                row['data'] = [info, infoLink['href']]
                                            else:
                                                row['data'] = [info]
                                        elif 'text-align:center' in wikiInfoChildChild.attrs['style']:
                                            infoText = wikiInfoChildChild.get_text()
                                            if infoLink != None:
                                                row['description'] = [infoText, infoLink['href']]
                                            else:
                                                row['description'] = [infoText]
                                        elif 'text-align:left' in wikiInfoChildChild.attrs['style']:
                                            infoName = wikiInfoChildChild.get_text()
                                            if infoLink != None:
                                                row['name'] = [infoName, infoLink['href']]
                                rowHolder.append(row)
                    infoBox['data'] = rowHolder
                    infoBoxHolder.append(infoBox)
                    infoBox = {}

        if contentText != None:
            mainContentChildren = contentText.children
            data['title'] = pageTitle.text
            sectionData['sectionName'] = 'summary'
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
            data['infoBoxes'] = infoBoxHolder

            return data

    def processWikiSearchHtml(self, htmlSoup):
        htmlSoup

    def __init__(self):
        self.wikiSession = requests.Session()
        try:
            self.mongoClient = pymongo.MongoClient('localhost', 27017)
            self.icdDatabase = self.mongoClient.get_database('Icd10')
            self.wikiMedInfoDatabase = self.mongoClient.get_database('WikiMedInfo')
            self.medNLP = MedNaturalLanguageProcessing(self.mongoClient)
        except:
            print('Failed to initalize mongodb database connection')

wikiExtend = WikiMedIcdInfoExtend()
wikiExtend.reprocessIcdCodes()
wikiExtend.constructWikiInformationExtension()
