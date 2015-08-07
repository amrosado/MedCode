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

    def processWikiSearchInformation(self, searchTerm):
        #self.wikiMedInfoDatabase.drop_collection('wikiSearchTerms')
        #self.wikiMedInfoDatabase.drop_collection('wikiRequests')
        wikiSearchTermCollection = self.wikiMedInfoDatabase.get_collection('wikiSearchTerms')
        wikiSearchTermQuery = wikiSearchTermCollection.find_one({'searchTerm': searchTerm})

        if wikiSearchTermQuery == None:
            queryParams = {'search': searchTerm}
            wikiMedRequestContent = self.medRequests.getSessionRequest(self.wikiBaseUrl, queryParams)
            wikiHtmlSoup = BeautifulSoup(wikiMedRequestContent)
            searchTermData = self.processWikiInformationHtml(wikiHtmlSoup)
            searchTermDataBreakdown = self.medNLP.breakdownWikiData(searchTermData)

            dump = json.dumps(searchTermData)
            wikiSearchTermCollection.insert_one({'searchTerm': searchTerm, 'data': dump})
            #self.updateSearchTermAssociations(searchTerm)

            if 'sectionData' in searchTermData:
                for section in searchTermData['sectionData']:
                    if 'links' in section:
                        for link in section['links']:
                            if link[1][0] != '#':
                                linkWikiUrl = self.wikiBaseUrl+link[1][1:len(link[1])]
                                wikiLinkContent = self.medRequests.getSessionRequest(linkWikiUrl, None)
                                wikiLinkHtmlSoup = BeautifulSoup(wikiLinkContent)
                                wikiLinkData = self.processWikiInformationHtml(wikiLinkHtmlSoup)
                                wikiLinkDataDump = json.dumps(wikiLinkData)
                                wikiSearchTermCollection.insert_one({'searchTerm': link[1], 'data': wikiLinkDataDump})
                                pass

            return searchTermData

        else:
            searchTermData = json.loads(wikiSearchTermQuery['data'])
            return searchTermData

    def updateSearchTermAssociations(self, searchTerm):
        #wikiSearchTermCollection = self.wikiMedInfoDatabase.get_collection('wikiSearchTerms')
        wikiSearchTermAssociationsCollection = self.wikiMedInfoDatabase.get_collection('wikiSearchTermAssociations')

        wikiSearchTermAssociationQuery = wikiSearchTermAssociationsCollection.find_one({'searchTerm': searchTerm})

        if wikiSearchTermAssociationQuery == None:
            searchTermAssociationData = {'searchTerm': searchTerm, 'associations': None, 'associationIds': None, 'associationCount': 0}
            wikiSearchTermAssociationsCollection.insert_one(searchTermAssociationData)
            wikiSearchTermAssociations = wikiSearchTermAssociationsCollection.find()
            for searchTermAssociation in wikiSearchTermAssociations:
                associations = searchTermAssociation['associations']
                if associations != None:
                    for association in associations:
                        if association == searchTerm:
                            if searchTermAssociationData['associations'] == None:
                                searchTermAssociationData['associations'] = [searchTerm]
                                searchTermAssociationData['associationCount'] += 1
                                searchTermAssociationData['associationIds'] = [searchTermAssociation._id]
                                updateResult = wikiSearchTermAssociationsCollection.update_one({'searchTerm': searchTerm}, searchTermAssociationData)
                            else:
                                searchTermAssociationData['associations'].append(searchTerm)
                                searchTermAssociationData['associationIds'].append(searchTermAssociation._id)
                                searchTermAssociationData['associationCount'] += 1
                                updateResult = wikiSearchTermAssociationsCollection.update_one({'searchTerm': searchTerm}, searchTermAssociationData)
                        else:
                            self.updateSearchTermAssociations(association)
        else:
            searchTermAssociationData = {}
            searchTermAssociationData['associations'] = wikiSearchTermAssociationQuery['associations']
            searchTermAssociationData['associationIds'] = wikiSearchTermAssociationQuery['associationIds']
            searchTermAssociationData['associationCount'] = wikiSearchTermAssociationQuery['associationCount']

            if searchTermAssociationData['associations'] != None:
                for association in searchTermAssociationData['associations']:
                    updateAssociationQuery = wikiSearchTermAssociationsCollection.find_one({'searchTerm': association})
                    if updateAssociationQuery != None:
                        updateAssociationData = {'searchTerm': association}
                        if updateAssociationQuery['associations'] == None:
                            updateAssociationData['associations'] = [searchTerm]
                            updateAssociationData['associationCount'] += 1
                            updateAssociationData['associationIds'] = [updateAssociationQuery._id]
                            updateResult = wikiSearchTermAssociationsCollection.update_one({'searchTerm': association}, updateAssociationData)
                        else:
                            updateAssociationData['associations'].append(searchTerm)
                            updateAssociationData['associationIds'].append(updateAssociationQuery._id)
                            updateAssociationData['associationCount'] += 1
                            updateResult = wikiSearchTermAssociationsCollection.update_one({'searchTerm': association}, updateAssociationData)

    def constructWikiInformationExtension(self):
        processedCodeCollection = self.icdDatabase.get_collection('processedDiagnosisCodes')
        #self.wikiMedInfoDatabase.drop_collection('wikiInfo')
        wikiSearchTermsCollection = self.wikiMedInfoDatabase.get_collection('wikiCodeAssociations')

        processedCodeFullCursor = processedCodeCollection.find()

        wikiData = {}
        for code in processedCodeFullCursor:
            codeData = json.loads(code['data'])
            if 'codeName' in codeData:
                wikiSearchTerms = self.medNLP.buildCodeWikiSesarch(codeData['code'], codeData=codeData)
                for searchTerm in wikiSearchTerms['searchWords']:
                    searchTerm = searchTerm.lower()
                    searchTermData = self.processWikiSearchInformation(searchTerm)
                    pass

    def analyzeCodeInformation(self, code):
        pass

    def processWikiTableBody(self, tBodySoup):
        tableData = {}
        tableSections = []
        tableSection = {}
        tableTitle = True
        tableRows = tBodySoup.find_all('tr')
        for tableRow in tableRows:
            tableImages = tableRow.find_all('img')
            tableLinks = tableRow.find_all('a')
            tableHeadPresent = False
            tableCellsPresent = False
            tableListPresent = False

            tableCellCount = 0
            tableHeads = tableRow.find_all('th')
            tableCells = tableRow.find_all('td')
            for tableCell in tableCells:
                tableCellCount += 1
                tableCellsPresent = True
                tableLists = tableCell.find('ul')
                if tableLists != None:
                    tableListPresent = True
            for tableHead in tableHeads:
                tableCellCount += 1
                tableHeadPresent = True
            if tableTitle:
                tableData['title'] = tableHeads[0].get_text().strip('\n')
                tableSection['sectionName'] = tableHeads[0].get_text().strip('\n')
                tableTitle = False
            elif tableHeadPresent and (tableCellCount == 1):
                tableSections.append(tableSection)
                tableSection = {}
                tableSection['data'] = []
                if tableHeads[0].get_text().strip('\n:') != '':
                    tableSection['sectionName'] = tableHeads[0].get_text().strip('\n')
            elif (tableCellCount > 1) and tableCellsPresent:
                tableSection['data'].append([])
                for tableHead in tableHeads:
                    if tableHead.get_text().strip('\n:') != '':
                        tableSection['data'][len(tableSection['data'])-1].append(tableHead.get_text().strip('\n:'))
                for tableCell in tableCells:
                    if tableCell.get_text().strip('\n:') != '':
                        tableSection['data'][len(tableSection['data'])-1].append(tableCell.get_text().strip('\b:'))
            else:
                if 'data' not in tableSection:
                    tableSection['data'] = []
                for tableCell in tableCells:
                    tableCellLists = tableCell.find_all('ul')
                    if tableCellLists != None:
                        for tableCellList in tableCellLists:
                            tableSection['data'].append([])
                            tableCellListElements = tableCellList.find_all('li')
                            for tableCellListElement in tableCellListElements:
                                tableSection['data'][len(tableSection['data'])-1].append(tableCellListElement.get_text().strip('\n'))
                    elif tableCell.get_text().strip('\n:') != '':
                        tableSection['data'].append(tableCell.get_text().strip('\n'))
            if tableImages != None:
                if 'images' not in tableSection:
                    tableSection['images'] = []
                for tableImage in tableImages:
                    tableSection['images'].append([tableImage['alt'], tableImage['src']])
            if tableLinks != None:
                if 'links' not in tableSection:
                    tableSection['links'] = []
                for tableLink in tableLinks:
                    tableSection['links'].append([tableLink.get_text('\n'), tableLink['href']])
        tableSections.append(tableSection)
        tableData['sections'] = tableSections

        return tableData

    def handleWikiInfoBoxes(self, wikiInfoSoup):

        wikiInfoTbodies = wikiInfoSoup.find_all('tbody')
        infoBoxDataHolder = []

        for tableBody in wikiInfoTbodies:
            infoBoxDataHolder.append(self.processWikiTableBody(tableBody))

        return infoBoxDataHolder

    def handleWikiContentChildren(self, contentSoupChildren):
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

        sectionData['sectionName'] = 'summary'
        for contentChild in contentSoupChildren:
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

        return data

    def processWikiInformationHtml(self, htmlSoup):
        wikiInfos = htmlSoup.find_all('table', 'infobox')
        contentText = htmlSoup.find('div', id='mw-content-text')
        pageTitle = htmlSoup.find('h1', id='firstHeading')
        lastModified = htmlSoup.find('li', id='footer-info-lastmod')
        data = {}

        infoBoxHolder = []

        if len(wikiInfos) == 0:
            return None

        if lastModified != None:
            data['lastModified'] = lastModified.get_text()

        if wikiInfos != None:
            for wikiInfo in wikiInfos:
                wikiInfoData = self.handleWikiInfoBoxes(wikiInfo)
                infoBoxHolder.append(wikiInfoData)

        data['title'] = pageTitle.text

        if contentText != None:
            mainContentChildren = contentText.children
            subData = self.handleWikiContentChildren(mainContentChildren)

        data['infoBoxes'] = infoBoxHolder
        data['sectionData'] = subData['sectionData']
        data['referenceInfo'] = subData['referenceInfo']

        return data

    def defListHandler(self, defListSoup):
        defListData = {}
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

            data = {}
            data['text'] = listElement.get_text()
            subLists = listElement.find_all('ul')
            for subDefList in subDefLists:
                subDefListHolder.append(self.defListHandler(subDefList))
            for subList in subLists:
                defListListsHolder.append(self.listHandler(subList))
            if len(subDefListHolder) > 0:
                data['subDefList'] = subDefListHolder
            if len(defListListsHolder) > 0:
                data['defListLists'] = defListListsHolder
            defListDataHolder.append(data)

        # for list in defListLists:
        #     defListListsHolder.append(self.listHandler(list))

        if len(defListLinkHolder) > 0:
            defListData['links'] = defListLinkHolder
        if len(defListDataHolder) > 0:
            defListData['data'] = defListDataHolder

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
            data = {}
            data['text'] = listElement.get_text()
            subLists = listElement.find_all('ul')
            for subList in subLists:
                subListHolder.append(self.listHandler(subList))
            if len(subListHolder) > 0:
                data['subLists'] = subListHolder
            listDataHolder.append(data)

        if len(listLinkHolder) > 0:
            listData['links'] = listLinkHolder
        if len(listDataHolder) > 0:
            listData['data'] = listDataHolder

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
