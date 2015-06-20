__author__ = 'arosado'

import requests
import pymongo
import json
import html5lib
import types
from bs4 import NavigableString, Tag
from MedNaturalLanguageProcessing import MedNaturalLanguageProcessing
from MedRequests import MedRequests
from bs4 import BeautifulSoup

class WikiMedIcdInfoExtend:
    wikiSession = None
    mongoClient = None

    icdDatabase = None
    wikiMedInfoDatabase = None

    requestContentDatabase = None

    medNLP = None
    medRequests = None

    wikiSearchUrl = 'https://en.wikipedia.org?search='
    wikiBaseUrl = 'https://en.wikipedia.org/'

    def reprocessIcdCodes(self):
        try:
            #self.icdDatabase.drop_collection('processedDiagnosisCodes')
            processedCodeCollection = self.icdDatabase.get_collection('processedDiagnosisCodes')

            icdDatabaseCollections = self.icdDatabase.collection_names()
            if 'hierarchydiagnosisCodes' in icdDatabaseCollections:
                codeCollection = self.icdDatabase.get_collection('hierarchydiagnosisCodes')

                codeFullCursor = codeCollection.find()
                for code in codeFullCursor:
                    codeData = None
                    if 'hierarchyGroup' in code:
                        codeIdentifier = code['hierarchyGroup']
                        findProcessedCode = processedCodeCollection.find_one({'code': codeIdentifier})
                        if findProcessedCode == None:
                            codeData = json.loads(code['data'])
                            processedCodeInfo = self.medNLP.breakdownCodeData(code, codeData)
                            dump = json.dumps(processedCodeInfo)
                            if codeData != None:
                                if 'codeName' in codeData:
                                    processedCodeCollection.insert({'code': codeIdentifier, 'data': dump, 'codeName': codeData['codeName']})
                                    print('Reprocessed and inserted into database code: '+codeIdentifier)
                                else:
                                    processedCodeCollection.insert({'code': codeIdentifier, 'data': dump})
                                    print('Reprocessed and inserted into database code: '+codeIdentifier)
                            else:
                                print('Could not insert reprocessed code... check program.')
        except:
            print('Failed to reprocess ICD 10 code information')

    def constructWikiInformationExtension(self):
        try:
            processedCodeCollection = self.icdDatabase.get_collection('processedDiagnosisCodes')
            self.wikiMedInfoDatabase.drop_collection('wikiInfo')
            wikiInfoCollection = self.wikiMedInfoDatabase.get_collection('wikiInfo')

            processedCodeFullCursor = processedCodeCollection.find()

            wikiData = {}
            for code in processedCodeFullCursor:
                codeData = json.loads(code['data'])
                findWikiInfo = wikiInfoCollection.find_one({'code': codeData['code']})
                if findWikiInfo == None:
                    if 'codeName' in codeData:
                        wikiSearchTerms = self.medNLP.buildCodeWikiSesarch(codeData['code'], codeData=codeData)
                        for searchTerm in wikiSearchTerms['searchWords']:
                            queryParams = {'search': searchTerm}
                            wikiMedRequestContent = self.medRequests.getSessionRequest(self.wikiBaseUrl, queryParams)
                            wikiHtmlSoup = BeautifulSoup(wikiMedRequestContent)
                            searchTermData = self.processWikiInformationHtml(wikiHtmlSoup)
                            #dump = json.dumps(data)
                            if searchTermData != None:
                                wikiData[searchTerm] = searchTermData
                        wikiInfoCollection.insert({'code': codeData['code'], 'searchTerms': json.dumps(wikiSearchTerms), 'data': json.dumps(wikiData), 'codeName': codeData['codeName']})
                        wikiData = {}
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
        subSectionData = None
        sectionTextHolder = []
        sectionLinkHolder = []
        subSectionTextHolder = []
        subSectionLinkHolder = []
        subSectionDataHolder = []
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
                        if subSectionData != None:
                            if len(subSectionTextHolder) > 0:
                                subSectionData['text'] = subSectionTextHolder
                            if len(subSectionLinkHolder) > 0:
                                subSectionData['links'] = subSectionLinkHolder
                            subSectionDataHolder.append(subSectionData)
                            sectionData['subSectionData'] = subSectionDataHolder
                        subSectionDataHolder = []
                        subSectionData = None
                        if len(sectionTextHolder) > 0:
                            sectionData['text'] = sectionTextHolder
                        if len(sectionLinkHolder) > 0:
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
                        sectionHeader = contentChild.find('span', 'mw-headline')
                        if sectionHeader != None:
                            sectionData['sectionName'] = sectionHeader.text
                        else:
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
                        if subSectionData != None:
                            if contentLinks != None:
                                for link in contentLinks:
                                    subSectionLinkHolder.append([link.text, link['href']])
                            subSectionTextHolder.append(contentChild.get_text())
                        else:
                            if contentLinks != None:
                                for link in contentLinks:
                                    sectionLinkHolder.append([link.text, link['href']])
                            sectionTextHolder.append(contentChild.get_text())
                    elif contentChild.name == 'h3':
                        if subSectionData != None:
                            if len(subSectionLinkHolder) > 0:
                                subSectionData['links'] = subSectionLinkHolder
                            if len(subSectionTextHolder) > 0:
                                subSectionData['text'] = subSectionTextHolder
                            subSectionDataHolder.append(subSectionData)
                        subSectionData = {}
                        subSectionLinkHolder = []
                        subSectionTextHolder = []
                        subSectionHeader = contentChild.find('span', 'mw-headline')
                        if subSectionHeader != None:
                            subSectionData['subSectionName'] = subSectionHeader.get_text()
                        else:
                            subSectionData['subSectionName'] = contentChild.get_text()
                    elif contentChild.name == 'ul':
                        if subSectionData != None:
                            subSectionData['listData'] = self.listHandler(contentChild)
                        else:
                            sectionData['listData'] = self.listHandler(contentChild)
                    elif contentChild.name == 'dl':
                        sectionData['defListData'] = self.defListHandler(contentChild)
            data['sectionData'] = sectionDataHolder
            data['referenceInfo'] = referenceHolder
            data['infoBoxes'] = infoBoxHolder

            return data

    def defListHandler(self, defListSoup):
        defListData = {}
        defListLists = defListSoup.find_all('ul')

        defListElements = defListSoup.find_all('dd')
        contentLinks = defListSoup.find_all('a')
        defListLinkHolder = []
        defListDataHolder = []
        subDefListHolder = []
        defListListsHolder = []

        if contentLinks != None:
            for link in contentLinks:
                defListLinkHolder.append([link.text, link['href']])

        for listElement in defListElements:
            subDefLists = defListSoup.find_all('dl')
            defListData = {}
            defListData['text'] = listElement.get_text()
            subLists = listElement.find_all('ul')
            for subDefList in subDefLists:
                subDefListHolder.append(self.defListHandler(subDefList))
            for subList in subLists:
                defListListsHolder.append(self.listHandler(subList))
            if len(subDefListHolder) > 0:
                defListData['subDefList'] = subDefListHolder
            if len(defListListsHolder) > 0:
                defListData['defListLists'] = defListListsHolder
            defListDataHolder.append(defListData)

        for list in defListLists:
            defListListsHolder.append(self.listHandler(list))

        if len(defListLinkHolder) > 0:
            defListData['defListLinks'] = defListLinkHolder
        if len(defListDataHolder) > 0:
            defListData['defListData'] = defListDataHolder
        if len(defListListsHolder) > 0:
            defListData['defListLists'] = defListListsHolder

        return defListData

    def listHandler(self, listSoup):
        listData = {}

        listElements = listSoup.find_all('li')
        contentLinks = listSoup.find_all('a')
        listLinkHolder = []
        listDataHolder = []
        subListHolder = []

        if contentLinks != None:
            for link in contentLinks:
                listLinkHolder.append([link.text, link['href']])

        for listElement in listElements:
            listData = {}
            listData['text'] = listElement.get_text()
            subLists = listElement.find_all('ul')
            for subList in subLists:
                subListHolder.append(self.listHandler(subList))
            if len(subListHolder) > 0:
                listData['subList'] = subListHolder
            listDataHolder.append(listData)

        if len(listLinkHolder) > 0:
            listData['listLinks'] = listLinkHolder
        if len(listDataHolder) > 0:
            listData['listData'] = listDataHolder

        return listData

    def processWikiSearchHtml(self, htmlSoup):
        htmlSoup

    def __init__(self):
        self.wikiSession = requests.Session()
        try:
            self.mongoClient = pymongo.MongoClient('localhost', 27017)
            self.icdDatabase = self.mongoClient.get_database('Icd10')
            self.wikiMedInfoDatabase = self.mongoClient.get_database('WikiMedInfo')
            #self.requestContentDatabase = self.mongoClient.get_database('RequestContent')
            self.medNLP = MedNaturalLanguageProcessing()
            self.medRequests = MedRequests()
        except:
            print('Failed to initialize mongodb database connection')

wikiExtend = WikiMedIcdInfoExtend()
#wikiExtend.reprocessIcdCodes()
wikiExtend.constructWikiInformationExtension()
