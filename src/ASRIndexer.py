from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient
from elasticsearch import helpers
import os
import codecs
from lxml import html
import lxml
import math
import simplejson
import uuid

class ASRIndexer():

    def __init__(self):
        self.stop = None
        self.idf = None
        self.allKeywords = {}
        self._stopWordsFile = '../resources/stoplist_tno.tab'
        self._IDFFile = '../resources/top.wfreq'

    def createIndex(self, es, indexName, settingsFile, mappingFile, delete = False):
        iclient = IndicesClient(es)

        """If specified, delete any existing index with the same name"""
        if delete:
            if iclient.exists(indexName):
                iclient.delete(indexName)

        """Load the settings and mapping"""
        f = open(settingsFile)
        settings = simplejson.load(f)
        f.close()
        f = open(mappingFile)
        mapping = simplejson.load(f)
        f.close()

        """Create the index with the settings and mapping"""
        iclient.create(indexName, {'settings' : settings, 'mappings' : mapping})

    def showIndexInfo(self, es, indexName):
        iclient = IndicesClient(es)
        """Test if the mapping & settings were properly set"""
        print iclient.get_mapping(indexName)
        print '\n\n\n'
        print iclient.get_settings(indexName)

    def setIndexMapping(self, es, indexName, mappingFile):
        iclient = IndicesClient(es)
        f = open(mappingFile)
        mapping = simplejson.load(f)
        print iclient.put_mapping('asr_transcript', mapping, indexName)

    """Make sure to close the index before adding these settings!"""
    def setIndexSettings(self, es, indexName, settingsFile):
        iclient = IndicesClient(es)
        f = open(settingsFile)
        settings = simplejson.load(f)
        print iclient.put_settings(settings, indexName)

    def indexASRDirectory(self, path, es, indexName):
        print 'Indexing %s into %s ' % (path, indexName)
        count = 0
        for dirpath, dirnames, filenames in os.walk(path):
            #only process sub directories if recursive is specified
            for f in filenames:
                fn = '%s/%s' % (dirpath, f)
                print fn
                if fn.find('.xml') != -1:
                    fd = codecs.open(fn, 'r', 'utf-8')
                    text = fd.read()
                    #text = text.replace('<EOS-score="0.00000"/>', '')
                    try:
                        xml = html.fromstring(text.encode('utf-8'))
                    except lxml.etree.XMLSyntaxError, e:
                        print 'Error'
                        print e
                    self.indexDocument(es, indexName, xml, text.encode('utf-8'), count, f)
                    count += 1
                    #if count == 15:
                        #break
        self.indexAllKeywords(es, indexName)

    def indexAllKeywords(self, es, indexName):
        es.index(indexName, "all_keywords", self.allKeywords, id=uuid.uuid1())

    def addToAllKeywords(self, keywords):
        if keywords:
            for k in keywords:
                w = k['word']
                if self.allKeywords.has_key(w):
                    self.allKeywords[w] += 1
                else:
                    self.allKeywords[w] = 1

    def indexDocument(self, es, indexName, xmlElm, xmlString, count, asrFile):
        xpath_query = 'segments/speech'
        speechTags = xmlElm.xpath(xpath_query)
        if not speechTags:
            xpath_query = 'segments/speaker/speech'
            speechTags = xmlElm.xpath(xpath_query)
        allWords = u''
        wordTimes = {}
        if speechTags and len(speechTags) > 0:
            res = self.getMetaData(asrFile)
            broadcastDate = res[0]
            videoData = res[1]
            mp3 = '%s%s' % (asrFile.split(".")[0],'.mp3')

            for st in speechTags:
                asrChunk = u''
                chunkWordTimes = []
                speechBeginTime = int(float(st.attrib['begintime'])*1000)
                speechEndTime = int(float(st.attrib['endtime'])*1000)
                words = st.xpath('wordsequence/word')
                for word in words:
                    wordID = unicode(self.prepareText(word.attrib['wordid']))
                    #TODO convert to milliseconds
                    beginTime = unicode(word.attrib['begintime'])
                    endTime = unicode(word.attrib['endtime'])
                    bms = self.toMillis(beginTime)
                    ems = self.toMillis(endTime)
                    if wordID != '[s]' and wordID != 'SIL':
                        asrChunk = '%s %s' % (asrChunk, wordID)
                        chunkWordTimes.append((bms, ems))

                    """ collect the timecodes of the word occurences """
                    if wordID not in wordTimes:
                        wordTimes[wordID] = [(bms, ems)]
                    else:
                        wordTimes[wordID].append((bms, ems))
                keywords = self.getMostImportantWords(asrChunk, wordTimes, 4, False)
                self.addToAllKeywords(keywords)
                data = {"asr_file" : asrFile,
                        "start" : speechBeginTime,
                        "end" : speechEndTime,
                        "words" : asrChunk,
                        "wordTimes" : chunkWordTimes,
                        "keywords" : keywords,
                        "metadata" : {"mp3" : mp3, "broadcast_date": broadcastDate, "video_data": videoData}
                        }
                es.index(indexName, "asr_chunk", data, id=uuid.uuid1())
                allWords = '%s %s' % (allWords, asrChunk)

            es.index(indexName, "asr_transcript", {"words" : allWords}, id=asrFile)#, "xml" : xmlString

    def getMetaData(self, asrFile):
        es_immix = Elasticsearch(hosts=[{
            'host' : 'ltes1.beeldengeluid.nl',
            'port' : 9200,
            'url_prefix' : '',
            'http_auth' : '%s:%s' % ('admin', 'yk4search')
        }])
        parts = asrFile.split("_")
        dmguid = parts[0]
        realBegin = parts[1]
        duration = (parts[2])[:-4]
        broadcastDate = None
        sorteerdatum = None
        videoData = None
        methodResults = []
        publicatieCount = 0
        query = {"query":{"bool":{"must":[{"query_string":{"default_field":"doc.expressie.posities.dmguid.raw","query":"\"%s\"" % dmguid}}],"must_not":[],"should":[]}}}
        response = es_immix.search(index = 'zoekflex_0.0.8-snapshot', doc_type = 'doc', body = query, timeout = "10s")
        result = response['hits']['hits'][0]

        if (result['_source']['expressie']).has_key('publicaties'):
            for publicatie in result['_source']['expressie']['publicaties']:
                publicatieCount += 1
                sorteerdatum = publicatie['sorteerdatum']
                if publicatie.has_key('indicatie_herhaling'):
                    if publicatie['indicatie_herhaling'] == False:
                        broadcastDate = publicatie['sorteerdatum']

        if broadcastDate is None and publicatieCount == 1:
            broadcastDate = sorteerdatum
        methodResults.append(broadcastDate)

        if result['_source']['selecties'] is not None:
            for selectie in result['_source']['selecties']:
                if selectie['posities'] is not None:
                    for positie in selectie['posities']:
                        if positie['dragertype'] == "media archive" and positie['dmguid'] == dmguid:
                            beginTime = positie['beginopdrager'] - int(positie['sof'])
                            tijdsduur = positie['eindeopdrager'] - positie['beginopdrager']
                            if beginTime == int(realBegin) and tijdsduur == int(duration):
                                videoData={'dragernummer': positie['dragernummer'],'end': positie['eindeopdrager'],'start': positie['beginopdrager']}
                                break
        methodResults.append(videoData)
        return methodResults

    def toMillis(self, sec):
        if sec.find(".") == -1:
            return int(sec) * 1000
        else:
            i = sec.find('.')
            return (int(sec[0: i]) * 1000) + int(sec[i + 1:])

    def queryASRIndex(self, phrase):
        es = Elasticsearch()
        query = {"query":{"bool":{"must":[{"query_string":{"default_field":"asr_chunk","query":"\"%s\"" % phrase}}],"must_not":[],"should":[]}}}#, "fields" : ["asr_chunk", "word_times"]
        resp = es.search(index="programmes", doc_type="asr_transcript", body=query, timeout="10s")
        print 'Number of hits: %s' % resp['hits']['total']
        if resp['hits']['total'] > 0:
            for hit in resp['hits']['hits']:
                print hit['_source']['asr_file']

    def readStopWordsFile(self, strStopFile):
        if not strStopFile:
            strStopFile = self._stopWordsFile
        """ read stopwords from file as dictionary. """
        stopWords = {}
        try:
            f = codecs.open(strStopFile,'rU','utf-8')  # NB. Use 'U'-mode for UniversalNewline Support
            for line in f.readlines():
                word = line.partition('::')[0].strip()#.decode('utf-8')
                stopWords[word] = 1
            f.close()
        except IOError, e:
            msg =  'Can\'t open stopfile %s for reading. %s' % (strStopFile, str(e))
            print msg
            return None
        return stopWords

    def readIDFFile(self, IDFFile):
        if not IDFFile:
            IDFFile = self._IDFFile
        """ read stopwords from file as dictionary. """
        wordFreqs = {}
        try:
            f = codecs.open(IDFFile,'rU')  # NB. Use 'U'-mode for UniversalNewline Support
            for line in f.readlines():
                parts = line.split(' ')
                if parts and len(parts) == 2:
                    wordFreqs[parts[0].strip()] = int(parts[1].strip())
            f.close()
        except IOError, e:
            msg =  'Can\'t open IDFFile %s for reading. %s' % (IDFFile, str(e))
            print msg
            return None
        return wordFreqs

    def prepareText(self, text):
        text = text.replace('\n', '')
        text = text.replace("'", '')
        return text

    def getMostImportantWords(self, text, wordTimes, minwordlength = 5, simpleList = True):
        if(text is None or text == ''):
            return None
        allwords = {}
        results = []
        totalWordCount = 0
        if self.stop == None:
            self.stop = self.readStopWordsFile(self._stopWordsFile)
        if self.idf == None:
            self.idf = self.readIDFFile(self._IDFFile)
            self.wordsGrandTotal = 0
            for key in self.idf:
                self.wordsGrandTotal += self.idf[key]
        """ process results. """
        text = self.prepareText(text)
        word_arr = text.split(' ')

        """ We assume that the frequencies in the top.wfreq file are just grand totals of a
            large corpus. We don't know the document count, so we assume that the total number
            of words counted in top.wfreq divided by the total number of words in our document
            equals the number of documents.
            This is a stupid assumption, but hey...
        """
        thisDocGrandTotal = len(word_arr)
        docCount = float(self.wordsGrandTotal/thisDocGrandTotal)


        for word in word_arr:
            totalWordCount += 1
            wordID = word

            """ collect overall word statistics """
            if allwords.has_key(wordID):
                allwords[wordID] += 1
            else:
                allwords[wordID] = 1
        idf = self.idf
        if not idf:
            idf = allwords

        for key in allwords.iterkeys():
            """ Check for stopwords and wordlength. """
            if key.lower() in self.stop:
                continue
            if len(key) <= minwordlength:
                continue
            """ term frequency-inverse document frequency.
                tfidf is actually just the term frequency. """
            key_freq = allwords[key]
            try:
                """ We will compute the numDocsContaining(our_word), by dividing the
                        the frequency in our document by the total frequency in wfreq, multiplied by
                        the docCount.
                    """
                numDocsContaining = (float(key_freq) / self.idf[key]) * docCount
            except KeyError, e:
                numDocsContaining = 1.0

            tf = float(key_freq) / thisDocGrandTotal # term frequency = term count document / total word count document
            idf = math.log(docCount/numDocsContaining)
            largedecision = tf * idf * len(key) # take wordlength into account

            wordTime = None
            if wordTimes.has_key(key):
                wordTime = wordTimes[key]
            else:
                wordTime = 0
            results.append({'word' : key, 'score' : largedecision, 'freq' : key_freq, 'times' : wordTime})

        results_sorted = sorted(results, key=lambda item: item['score'], reverse=True)
        """ By default, just return the most frequent words in a simple list without scores"""
        if(simpleList and results_sorted):
            fws = []
            for res in results_sorted:
                """ Just add the word """
                fws.append(res[0])
            return fws
        """ Otherwise return the list containing all information """
        return results_sorted

    """Use this to test whether the analyzer works"""
    def analyze(self, es, indexName, text, analyzer):
        iclient = IndicesClient(es)
        print iclient.analyze(indexName, text, analyzer=analyzer)

    def reindex(self, es, indexName):
        print helpers.reindex(es, indexName, '%s%s' % (indexName, '_2'))
