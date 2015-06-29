__author__ = 'arosado'

import requests
import pymongo
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlencode, urlunparse


class MedRequests:
    requestsSession = None
    mongoClient = None
    requestsDb = None

    def getSessionRequest(self, url, queryDic):
        try:
            #self.requestsDb.drop_collection('wikiRequests')
            if queryDic != None:
                encodedQuery = urlencode(queryDic)
                parsedUrl = urlparse(url+'?'+encodedQuery)
            else:
                parsedUrl = urlparse(url)

            if parsedUrl[1] == 'en.wikipedia.org':
                requestCollection = self.requestsDb.get_collection('wikiRequests')

                requestContent = self.findOrUpdateQueryRequestsDb(requestCollection, parsedUrl)
                return requestContent

        except:
            print('Failed to generate session request')

    def findOrUpdateQueryRequestsDb(self, requestCollection, parsedUrl):
        requestUrl = parsedUrl.geturl()
        urlLocation = parsedUrl[1]
        urlPath = parsedUrl[2]
        urlParams = parsedUrl[3]
        urlQuery = parsedUrl[4]
        urlFragment = parsedUrl[5]

        requestDbQuery = requestCollection.find_one({'urlQuery': urlQuery, 'urlPath': urlPath, 'urlParams': urlParams,\
                                                     'urlFragment':urlFragment, 'urlLocation': urlLocation})
        currentTime = datetime.utcnow()

        if requestDbQuery != None:
            if requestDbQuery['status_code'] == 200:
                requestDatetime = requestDbQuery['datetime']
                timeWeek = requestDatetime + timedelta(days=7)
                if timeWeek > currentTime:
                    return requestDbQuery['content']
                else:
                    sessionRequest = self.requestsSession.get(requestUrl)
                    if sessionRequest.status_code == 200:
                        requestCollection.replace_one({'urlQuery': urlQuery, 'urlPath': urlPath, 'urlParams': urlParams,\
                                'urlFragment':urlFragment, 'urlLocation': urlLocation}, {'urlQuery': urlQuery,\
                                'urlPath': urlPath, 'urlParams': urlParams, 'urlFragment':urlFragment,\
                                'urlLocation': urlLocation, 'content': sessionRequest.content,\
                                'status_code': sessionRequest.status_code, 'datetime': currentTime})
                        return sessionRequest.content
            else:
                sessionRequest = self.requestsSession.get(requestUrl)
                if sessionRequest.status_code == 200:
                    requestCollection.replace_one({'urlQuery': urlQuery, 'urlPath': urlPath, 'urlParams': urlParams,\
                        'urlFragment':urlFragment, 'urlLocation': urlLocation}, {'urlQuery': urlQuery,\
                        'urlPath': urlPath, 'urlParams': urlParams, 'urlFragment':urlFragment,\
                        'urlLocation': urlLocation, 'content': sessionRequest.content,\
                        'status_code': sessionRequest.status_code, 'datetime': currentTime})
                    return sessionRequest.content
                else:
                    raise Exception('Error with request')
        else:
            sessionRequest = self.requestsSession.get(requestUrl)
            requestCollection.insert({'urlQuery': urlQuery,\
                    'urlPath': urlPath, 'urlParams': urlParams, 'urlFragment':urlFragment,\
                    'urlLocation': urlLocation, 'content': sessionRequest.content,\
                    'status_code': sessionRequest.status_code, 'datetime': currentTime})
            if sessionRequest.status_code == 200:
                return sessionRequest.content
            else:
                raise Exception('Error with request')

    def saveSessionRequest(self, request):
        pass

    def __init__(self):
        try:
            self.requestsSession = requests.Session()

            self.mongoClient = pymongo.MongoClient()
            self.requestsDb = self.mongoClient.get_database('RequestsDatabase')

        except:
            print('Failed to initialize Med Requests object.  Check database connection')