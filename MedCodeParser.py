__author__ = 'arosado'

import requests
import bs4
import pymongo
import json
import bson

class MedCodeParser:
    data = []

    ICD10DataUrl = 'http://www.icd10data.com'
    ICD10DataDiagnosisCodes = 'http://www.icd10data.com/ICD10CM/Codes'
    ICD10DataProcedureCodes = 'http://www.icd10data.com/ICD10PCS/Codes'
    ICD10ConversionCodes = 'http://www.icd10data.com/Convert'
    ICD10AlphaIndex = 'http://www.icd10data.com/ICD10CM/Index'
    ICD10ExternalCauseAlphaIndex = 'http://www.icd10data.com/ICD10CM/EIndex'
    ICD10NeoplasmsIndex = 'http://www.icd10data.com/ICD10CM/Table_Of_Neoplasms'
    ICD10DrugsIndex = 'http://www.icd10data.com/ICD10CM/Table_Of_Drugs'
    ICD10MedicalDiagnosisRelated = 'http://www.icd10data.com/ICD10CM/DRG'
    ICD10NewbornOnly = 'http://www.icd10data.com/ICD10CM/Newborn_Codes'
    ICD10PediatricOnly = 'http://www.icd10data.com/ICD10CM/Pediatric_Codes'
    ICD10MaternityOnly = 'http://www.icd10data.com/ICD10CM/Maternity_Codes'
    ICD10AdultOnly = 'http://www.icd10data.com/ICD10CM/Adult_Codes'
    ICD10FemaleOnly = 'http://www.icd10data.com/ICD10CM/Female_Codes'
    ICD10MaleOnly = 'http://www.icd10data.com/ICD10CM/Male_Codes'
    ICD10Manifestation = 'http://www.icd10data.com/ICD10CM/Manifestation_Codes'
    ICD10PresentOnAdmission = 'http://www.icd10data.com/ICD10CM/Present_On_Admission_Exempt'
    ICD10QuestionableAdmission = 'http://www.icd10data.com/ICD10CM/Questionable_Dx_Codes'
    ICD10CodesUnacceptableAsPrincipleDiagnosis = 'http://www.icd10data.com/ICD10CM/Unacceptable_Principal_Dx_Codes'
    ICD10DuplicateCodes = 'http://www.icd10data.com/ICD10CM/Duplicate_Codes'

    diagnosisCodes = None
    procedureCodes = None
    conversionCodes = None
    AlphaIndex = None
    ExternalCauseAlphaIndex = None
    NeoplasmIndex = None
    DrugsIndex = None
    MedicalDiagnosisRelated = None
    NewbornOnly = None
    PediatricOnly = None
    MaternityOnly = None
    AdultOnly = None
    FemaleOnly = None
    MaleOnly = None
    Manifestation = None
    PresentOnAdmission = None
    QuestionableAdmission = None
    UnacceptableAsPrincipleDiagnosis = None
    DuplicateCodes = None

    ICD10Session = None
    ICD10Html = None

    mongoClient = None
    mongoDb = None

    def initialSetup(self):
        try:
            # diagnosisCodesRequest = self.ICD10Session.get(self.ICD10DataDiagnosisCodes)
            # diagnosisCodesHtmlSoup = bs4.BeautifulSoup(diagnosisCodesRequest.content)
            #
            # self.crawlICD('diagnosisCodes', diagnosisCodesHtmlSoup)
            # diagnosisCodeFile = open('icd10DiagnosisCodes.json', 'wb')
            # json.dump(diagnosisCodeData, diagnosisCodeFile)

            procedureCodesRequest = self.ICD10Session.get(self.ICD10DataProcedureCodes)
            procedureCodesHtmlSoup = bs4.BeautifulSoup(procedureCodesRequest.content)

            self.crawlICD('procedureCodes', procedureCodesHtmlSoup)
            # procedureCodesFile = open('icd10ProcedureCodes.json', 'wb')
            # json.dump(procedureCodeData, procedureCodesFile)

        except:
            'Failed to setup icd parsing'

    def processSubHtml(self, htmlSoup):

        defLists = htmlSoup.find_all('ul', 'definitionList')
        defListLinkLists = htmlSoup.find_all('ul', 'noTopPadding')

        defListLinks = None

        for defListLinkList in defListLinkLists:
            defListLinks = defListLinkList.find_all('a', 'identifier')

        infoHolder = []

        for defList in defLists:
            infoDescription = []
            infoList = []
            parent = defList.parent
            infoDescription.append(parent.text)
            listElements = defList.find_all('li')
            for listElement in listElements:
                infoList.append(listElement.text)
            infoHolder.append([infoDescription, infoList])

        linkHolder = []
        for defListLink in defListLinks:
            linkDescription = defListLink.parent.text
            linkUrl = defListLink['href']
            linkHolder.append([linkDescription, linkUrl])

        self.data['codeCategoryInformation'] = infoHolder
        self.data['codeGroupUrls'] = linkHolder

        for link in linkHolder:
            codeGroupRequest = self.ICD10Session.get(link[1])
            codeGroupHtmlSoup = bs4.BeautifulSoup(codeGroupRequest.content)
            self.processCodeGroupHtml(codeGroupHtmlSoup)

    def processCodeGroupHtml(self, htmlSoup):

        defListLinkLists = htmlSoup.find_all('ul', 'noTopPadding')

        defListLinks = None

        for defListLinkList in defListLinkLists:
            defListLinks = defListLinkList.find_all('a', 'identifier')

        linkHolder = []
        for defListLink in defListLinks:
            linkDescription = defListLink.parent.text
            linkUrl = defListLink['href']
            linkHolder.append([linkDescription, linkUrl])

        self.data['codeUrls']

        for link in linkHolder:
            codeRequest = self.ICD10Session.get(link[1])
            codeHtmlSoup = bs4.BeautifulSoup(codeRequest.content)
            self.processCodeHtml(codeHtmlSoup)

    def processCodeHtml(self, htmlSoup):
        defLists = htmlSoup.find_all('ul', 'definitionList')
        deepCodesList = htmlSoup.find_all('div', 'hierarchyMarginWrapper')

        infoHolder = []

        for defList in defLists:
            infoDescription = []
            infoList = []
            infoLinkList = []
            parent = defList.parent
            infoDescription.append(parent.text)
            listElements = defList.find_all('li')
            listLinks = defList.find_all('a')
            for listElement in listElements:
                infoList.append(listElement.text)
            for listLink in listLinks:
                infoLinkList.append(listLink['href'])
            infoHolder.append([infoDescription, infoList, infoLinkList])

        codeHierarchyIdentifierUrlSpans = deepCodesList.find_all('span', 'codeHierarchyIdentifier')
        codeHierarchyThreeDigitCodeDescription = deepCodesList.find_all('span', 'threeDigitCodeListDescription')

        hierarchyHolder = []
        hierarchyUrlHolder = []
        hierarchyThreeDigitCodeHolder = []
        hierarchyDescriptionHolder = []

        for codeHierarchyIdentifierSpan in codeHierarchyIdentifierUrlSpans:
            codeHierarchyIdentifierLinks = codeHierarchyIdentifierSpan.find_all('a')
            for codeHierarchyIdentifierLink in codeHierarchyIdentifierLinks:
                hierarchyUrlHolder.append(codeHierarchyIdentifierLink['href'])
                hierarchyThreeDigitCodeHolder.append(codeHierarchyIdentifierLink['name'])

        for threeDigitCodeDescription in codeHierarchyThreeDigitCodeDescription:
            hierarchyDescriptionHolder.append(threeDigitCodeDescription.text)

        for i in range(0, len(hierarchyUrlHolder)):
            hierarchyHolder.append([hierarchyThreeDigitCodeHolder[i], hierarchyUrlHolder[i], hierarchyDescriptionHolder[i]])

        # self.data['urls'] =
        self.data['codeInformation'] = infoHolder
        self.data['codeHierarchyUrls'] = hierarchyHolder

        for hierarchy in hierarchyHolder:
            hierarcyRequest = self.ICD10Session.get(hierarchy[2])
            hierarcyHtmlSoup = bs4.BeautifulSoup(hierarcyRequest)
            self.processHierarchyHtml(hierarcyHtmlSoup)

    def processHierarchyHtml(self, htmlSoup):
        defLists = htmlSoup.find_all('ul', 'definitionList')

        infoHolder = []

        for defList in defLists:
            infoDescription = []
            infoList = []
            parent = defList.parent
            infoDescription.append(parent.text)
            listElements = defList.find_all('li')
            for listElement in listElements:
                infoList.append(listElement.text)
            infoHolder.append([infoDescription, infoList])

    def crawlICD(self, dataCategory, htmlSoup):
        # self.mongoDb.drop_collection('group' + dataCategory)
        # self.mongoDb.drop_collection('subGroup' + dataCategory)
        # self.mongoDb.drop_collection('subSubSubGroup' + dataCategory)
        # self.mongoDb.drop_collection('subSubSubSubGroup' + dataCategory)

        hierarchyDataCollectionName = "hierarchy" + dataCategory
        hierarchyDataCollection = self.mongoDb.get_collection(hierarchyDataCollectionName)

        groupCollectionName = "group" + dataCategory
        groupCollection = self.mongoDb.get_collection(groupCollectionName)

        subGroupCollectionName = "subGroup" + dataCategory
        subGroupCollection = self.mongoDb.get_collection(subGroupCollectionName)

        subSubGroupCollectionName = "subSubGroup" + dataCategory
        subSubGroupCollection = self.mongoDb.get_collection(subSubGroupCollectionName)

        subSubSubGroupCollectionName = "subSubSubGroup" + dataCategory
        subSubSubGroupCollection = self.mongoDb.get_collection(subSubSubGroupCollectionName)

        subSubSubSubGroupCollectionName = "subSubSubSubGroup" + dataCategory
        subSubSubSubGroupCollection = self.mongoDb.get_collection(subSubSubSubGroupCollectionName)

        mainList = htmlSoup.find_all('div', 'col-md-10')[1]
        for mainListLink in mainList.find_all('a'):
            listName = mainListLink.text
            listUrl = mainListLink['href']
            fullUrl = self.ICD10DataUrl + listUrl
            groupQuery = groupCollection.find_one({'group': listName})
            data = None
            if groupQuery == None:
                print("Requesting data from " + fullUrl)
                groupRequest = self.ICD10Session.get(fullUrl, timeout=None)
                groupHtmlSoup = bs4.BeautifulSoup(groupRequest.content)
                data = self.processHtml(groupHtmlSoup)
                groupCollection.insert_one({'group': listName, 'data': json.dumps(data)})
            if groupQuery != None:
                data = json.loads(groupQuery['data'])
            for link in data['identifierUrls']:
                data2 = None
                fullUrl2 = self.ICD10DataUrl + link[1]
                subGroupQuery = subGroupCollection.find_one({'subGroup': link[0]})
                if subGroupQuery == None:
                    print("Requesting data from " + fullUrl2)
                    subGroupRequest = self.ICD10Session.get(fullUrl2, timeout=None)
                    subGroupHtmlSoup = bs4.BeautifulSoup(subGroupRequest.content)
                    data2 = self.processHtml(subGroupHtmlSoup)
                    subGroupCollection.insert_one({'subGroup': link[0], 'data': json.dumps(data2)})
                if subGroupQuery != None:
                    data2 = json.loads(subGroupQuery['data'])
                for link2 in data2['identifierUrls']:
                    data3 = None
                    fullUrl3 = self.ICD10DataUrl + link2[1]
                    subSubGroupQuery = subSubGroupCollection.find_one({'subSubGroup': link2[0]})
                    if subSubGroupQuery == None:
                        print('Requesting data from ' + fullUrl3)
                        subSubGroupRequest2 = self.ICD10Session.get(fullUrl3, timeout=None)
                        subSubGroupHtmlSoup2 = bs4.BeautifulSoup(subSubGroupRequest2.content)
                        data3 = self.processHtml(subSubGroupHtmlSoup2)
                        subSubGroupCollection.insert_one({'subSubGroup': link2[0], 'data': json.dumps(data3)})
                    if subSubGroupQuery != None:
                        data3 = json.loads(subSubGroupQuery['data'])
                    if 'hierarchy' in data3:
                        for link3 in data3['hierarchy']:
                            fullUrl4 = self.ICD10DataUrl + link3[1]
                            hierarchyQuery = hierarchyDataCollection.find_one({'hierarchyGroup': link3[0]})
                            if hierarchyQuery == None:
                                print('Requesting data from ' + fullUrl4)
                                identiferRequest3 = self.ICD10Session.get(fullUrl4, timeout=None)
                                identiferHtmlSoup3 = bs4.BeautifulSoup(identiferRequest3.content)
                                data4 = self.processHtml(identiferHtmlSoup3)
                                hierarchyDataCollection.insert_one({'hierarchyGroup': link3[0], 'data': json.dumps(data4)})
                            if hierarchyQuery != None:
                                break
                    else:
                        for link3 in data3['identifierUrls']:
                            data4 = None
                            fullUrl4 = self.ICD10DataUrl + link3[1]
                            subSubSubGroupQuery = subSubSubGroupCollection.find_one({'subSubSubGroup': link3[0]})
                            if subSubSubGroupQuery == None:
                                print('Requesting data from ' + fullUrl4)
                                subSubSubGroupRequest = self.ICD10Session.get(fullUrl4, timeout=None)
                                subSubSubGroupHtmlSoup = bs4.BeautifulSoup(subSubSubGroupRequest.content)
                                data4 = self.processHtml(subSubSubGroupHtmlSoup)
                                subSubSubGroupCollection.insert_one({'subSubSubGroup': link3[0], 'data': json.dumps(data4)})
                            if subSubSubGroupQuery != None:
                                data4 = json.loads(subSubSubGroupQuery['data'])
                            for link4 in data4['identifierUrls']:
                                fullUrl5 = self.ICD10DataUrl + link4[1]
                                subSubSubSubGroupQuery = subSubSubSubGroupCollection.find_one({'subSubSubSubGroup': link4[0]})
                                if subSubSubSubGroupQuery == None:
                                    print('Requesting data from ' + fullUrl5)
                                    subSubSubSubGroupRequest = self.ICD10Session.get(fullUrl5, timeout=None)
                                    subSubSubSubGroupHtmlSoup = bs4.BeautifulSoup(subSubSubSubGroupRequest.content)
                                    data5 = self.processHtml(subSubSubSubGroupHtmlSoup)
                                    subSubSubSubGroupCollection.insert_one({'subSubSubSubGroup': link4[0], 'data': json.dumps(data5)})
                                if subSubSubSubGroupQuery != None:
                                    break


    def processHtml(self, htmlSoup):
        data = {}
        defLists = htmlSoup.find_all('ul', 'definitionList')
        deepCodesLists = htmlSoup.find_all('div', 'hierarchyMarginWrapper')
        defListLinkLists = htmlSoup.find_all('ul', 'noTopPadding')
        contentBlurbList = htmlSoup.find_all('div', 'contentBlurb')

        defListLinksHolder = []

        if len(defListLinkLists) > 0:
            for defListLinkList in defListLinkLists:
                defListLinks = defListLinkList.find_all('a', 'identifier')
                if len(defListLinks) > 0:
                    defListLinksHolder.append(defListLinks)
                if len(defListLinks) == 0:
                    defListLinks2 = defListLinkList.find_all('a')
                    if len(defListLinks2) > 0:
                        defListLinksHolder.append(defListLinks2)

            linkHolder = []
            for defListLinks in defListLinksHolder:
                for defListLink in defListLinks:
                    linkDescription = defListLink.parent.text
                    linkUrl = defListLink['href']
                    linkHolder.append([linkDescription, linkUrl])

            data['identifierUrls'] = linkHolder

        infoHolder = []

        if len(defLists) > 0:
            for defList in defLists:
                infoDescription = []
                infoList = []
                infoLinkList = []
                parent = defList.parent
                infoDescription.append(parent.text)
                listElements = defList.find_all('li')
                listLinks = defList.find_all('a')
                if len(listElements) > 0:
                    for listElement in listElements:
                        infoList.append(listElement.text)
                if len(listLinks) > 0:
                    for listLink in listLinks:
                        if 'href' in listLink:
                            infoLinkList.append([listLink.text, listLink['href']])
                infoHolder.append([infoDescription, infoList, infoLinkList])
            data['information'] = infoHolder

        if len(deepCodesLists) > 0:
            for deepCodesList in deepCodesLists:
                codeHierarchyIdentifierUrlSpans = deepCodesList.find_all('span', 'codeHierarchyIdentifier')
                codeHierarchyThreeDigitCodeDescription = deepCodesList.find_all('span', 'threeDigitCodeListDescription')
                hierarchyHolder = []
                hierarchyUrlHolder = []
                hierarchyThreeDigitCodeHolder = []
                hierarchyDescriptionHolder = []
                for codeHierarchyIdentifierSpan in codeHierarchyIdentifierUrlSpans:
                    codeHierarchyIdentifierLinks = codeHierarchyIdentifierSpan.find_all('a')
                    for codeHierarchyIdentifierLink in codeHierarchyIdentifierLinks:
                        hierarchyUrlHolder.append(codeHierarchyIdentifierLink['href'])
                        hierarchyThreeDigitCodeHolder.append(codeHierarchyIdentifierLink['name'])
                for threeDigitCodeDescription in codeHierarchyThreeDigitCodeDescription:
                    hierarchyDescriptionHolder.append(threeDigitCodeDescription.text)
                for i in range(0, len(hierarchyUrlHolder)-1):
                    hierarchyHolder.append([hierarchyThreeDigitCodeHolder[i], hierarchyUrlHolder[i], hierarchyDescriptionHolder[i]])
                data['hierarchy'] = hierarchyHolder
        if ((len(deepCodesLists) == 0) and (len(defLists) == 0) and (len(defListLinkLists) == 0)):
            identifierHolder = []
            for contentBlurb in contentBlurbList:
                identifierSpans = contentBlurb.find_all('span', 'identifier')
                for identifierSpan in identifierSpans:
                    identifierInfo = []
                    identifierNumber = identifierSpan.text
                    identifierLink = identifierSpan.parent.find('a')
                    identifierName = identifierSpan.parent.text
                    identifierInfo.append(identifierNumber)
                    if identifierLink != None:
                        identifierUrl = identifierLink['href']
                        identifierInfo.append(identifierUrl)
                    identifierInfo.append(identifierName)
                    identifierHolder.append(identifierInfo)
            identifierUrls = []
            for identifier in identifierHolder:
                if len(identifier) > 2:
                    identifierUrls.append([identifier[0], identifier[1]])
            data['identifiers'] = identifierHolder
            data['identifierUrls'] = identifierUrls

        return data

    def urlGrabber(self, icdUrl):
        pass

    def informationGrabber(self, icdUrl):
        pass

    def __init__(self):
        self.ICD10Session = requests.Session()
        try:
            self.mongoClient = pymongo.MongoClient('localhost', 27017)
            self.mongoDb = self.mongoClient.get_database('Icd10')
        except:
            print('Failed to initalize mongodb database connection')


icdParser = MedCodeParser()
icdParser.initialSetup()
