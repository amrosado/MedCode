__author__ = 'arosado'

import re
import json
import types
import pymongo

class MedNaturalLanguageProcessing:
    mongoClient = None
    naturalLanguageDb = None
    wikiMedInfoDb = None
    icdDb = None

    def buildCodeWikiSesarch(self, code, codeData):
        searchData = {}
        searchWordHolder = []

        codeNameWordsRe = re.compile('\w+')

        excludedWordsList = ['and', 'fevers']

        codeNameWordsFindAll = codeNameWordsRe.findall(codeData['codeName'])

        for word in codeNameWordsFindAll:
            if word not in excludedWordsList:
                searchWordHolder.append(word)

        searchData['searchWords'] = searchWordHolder
        return searchData

    def breakdownCodeData(self, code, codeData):
        newData = {}
        billable = None

        notbillableRe = re.compile('(?<=(not[\s]a))[\s](billable)')
        billableRe = re.compile('(?<!(not[\s]a))[\s](billable)')

        sentenceRe = re.compile('[^.!?\s][^.!?]*(?:[.!?](?![\S]?\s|$)[^.!?]*)*[.!?]?[\S]?(?=\s|$)')

        clinicalData = None
        clinicalDataRe = re.compile('(Clinical[\s]Information[\s])')

        diagnosisRelatedGroupData = None
        diagnosisRelatedGroupDataRe = re.compile('(Diagnostic[\s]Related[\s]Group[(]s[)][:])')

        descriptiveSynonyms = None
        descriptiveSynonymsRe = re.compile('(Description Synonyms)')

        backReferencesData = None
        backReferencesDataRe = re.compile('(back-references)')

        applicableTo = None
        applicableToRe = re.compile('(Applicable To)')

        typeExcludesRe = re.compile('(Type\s[0-9]+\sExcludes)')

        try:
            sentenceHolder = []
            typeExcludesHolder = []

            if 'information' in codeData:
                for infoList in codeData['information']:
                    for infoSubList in infoList:
                        for info in infoSubList:
                            sentences = sentenceRe.findall(info)
                            typeExcludesFindAll = typeExcludesRe.findall(info)

                            if clinicalData == None:
                                clinicalDataFindAll = clinicalDataRe.findall(info)
                                if len(clinicalDataFindAll) > 0:
                                    newInfoList = infoList[1]
                                    newData['clinicalInformation'] = newInfoList
                            if diagnosisRelatedGroupData == None:
                                diagnosisRelatedGroupFindAll = diagnosisRelatedGroupDataRe.findall(info)
                                if len(diagnosisRelatedGroupFindAll) > 0:
                                    newSubInfo = infoSubList[1]
                                    newData['diagnosisRelatedGroups'] = newSubInfo
                            if backReferencesData == None:
                                backReferencesFindAll = backReferencesDataRe.findall(info)
                                if len(backReferencesFindAll) > 0:
                                    newInfoList = infoList[1]
                                    newData['backReferences'] = newInfoList
                            if descriptiveSynonyms == None:
                                descriptiveSynonymsFindAll = descriptiveSynonymsRe.findall(info)
                                if len(descriptiveSynonymsFindAll) > 0:
                                    newInfoList = infoList[1]
                                    newData['descriptiveSynonyms'] = newInfoList
                            if applicableTo == None:
                                applicableToFindAll = applicableToRe.findall(info)
                                if len(applicableToFindAll) > 0:
                                    newInfoList = infoList[1]
                                    newData['applicableTo'] = newInfoList
                            if len(typeExcludesFindAll) > 0:
                                newInfoList = infoList[1]
                                typeExcludesHolder.append([len(typeExcludesHolder)+1, newInfoList])
                            if billable == None:
                                notBillFindAll = notbillableRe.findall(info)
                                billableFindAll = billableRe.findall(info)
                                if (len(notBillFindAll) + len(billableFindAll)) > 0:
                                    if len(notBillFindAll) > 0:
                                        newInfoList = infoList[1]
                                        newData['icdInformation'] = newInfoList
                                        billable = False
                                    else:
                                        newInfoList = infoList[1]
                                        newData['icdInformation'] = newInfoList
                                        billable = True
                            for sentence in sentences:
                                sentenceHolder.append(sentence)

                newData['code'] = code['hierarchyGroup']
                if 'hierarchy' in codeData:
                    newData['hierarchy'] = codeData['hierarchy']
                #Every code's data does not include a code name.
                if 'codeName' in codeData:
                    newData['codeName'] = codeData['codeName']
                if 'codeIdentifier' in codeData:
                    newData['codeIdentifier'] = codeData['codeIdentifier']
                newData['sentences'] = sentenceHolder
                if billable != None:
                    newData['billable'] = billable
                if len(typeExcludesHolder) > 0:
                    newData['typeExcludes'] = typeExcludesHolder

            return newData

        except:
            print('Failed to breakdown medical code '+code['hierarchyGroup'] +'info list '+json.dumps(infoList))

    def breakdownWikiData(self, wikiData):
        if wikiData != None:
            pass

    def __init__(self):
        try:
            self.mongoClient = pymongo.MongoClient('localhost', 27017)
            self.naturalLanguageDb = self.mongoClient.get_database('MedNLP')
            self.icdDb = self.mongoClient.get_database('Icd10')
            self.wikiMedInfoDb = self.mongoClient.get_database('WikiMedInfo')
        except:
            print('Failed to init natural language processing')
