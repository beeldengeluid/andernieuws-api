Ander Nieuws API
================

In the Ander Nieuws project, 3 years (2011-2013) of daily news broadcasts were subjected to the following analysis work flow:

1. automatic speech recognition (yielding speech transcripts)
2. keyword detection, based on the speech transcripts (see keyword detection)
3. indexation of the speech transcripts and keywords in ElasticSearch


Keyword detection
----------------
Each speech transcript is segmented into blocks where (most likely) individual speakers are speaking. For each of these 'speech segments' keyword detection is done for building the ElasticSearch index (see next section).

Keywords were detected based on the following (statistical) analysis techniques:
- Stopword removal
- TF-IDF


ElasticSearch index
----------------

A document in the ElasticSearch index represents a speech segment and consists of the following data:

	_type: asr_chunk
	_id: df9ffb5e-fc6f-11e3-b11b-6c3be523cdb6
	_source: {
		wordTimes:  37.660 37.880 38.330 38.510 39.150 39.310 39.420
		end: 39780
		start: 37530
		words:  maar weigeren om verantwoording af te leggen
			keywords: [
			{
			freq: 1
			score: 13.9680332517108
			word: verantwoording
			times: 38.510
			}
			{
			freq: 1
			score: 8.499232866039245
			word: weigeren
			times: 37.880
			}
		]
		asr_file: 2012052421364640800790450790017A43C92F00000008524B00000D0F070190_243160_233040.xml
		metadata: {
			broadcast_date: 24-05-2012
			mp3: 2012052421364640800790450790017A43C92F00000008524B00000D0F070190_243160_233040.mp3
			video_data: {
				start: 72063120
				dragernummer: NOS_JOURNAAL_-WON00828745
				end: 72296160
			}
		}
	}


API
----------------

The API was built on top of the ElasticSearch index and supports the retrieval of certain keyword clusters based on:
- a search string
- a data range (period)

The obtained clusters are retrieved as follows, given the search string and the specified period:

1. The index is searched for all occurances the search word is mentioned in news videos (that were broadcast within the given period)
2. All hits are grouped per news video (it's possible that the search word occurs multiple times within the news video)
3. For all of the found occurances per news show, the keywords occurring in a radius of 5 seconds around the occurance are retrieved
4. Finally based on the found keywords per news video, the data is grouped per keyword so that eventually the API returns instances as follows:


Example

	topicData['KEYWORD'] = {
		mediaItems['NEWS_PROGRAM_ID'] = [
			{
				topic  : 'KEYWORD',
				videoUrl : 'URL TO NEWS VIDEO FILE',
				audioUrl : 'URL TO NEWS AUDIO FILE',
				date : 'DATE OF NEWS PROGRAM',
				spokenAt : 'TIMES WITHIN NEWS PROGRAM THE KEYWORD IS UTTERED'
			}
		]
	}


The currently still running API can be found here:

http://andernieuws.rdlabs.beeldengeluid.nl/andernieuws/search

As mentioned, the following parameters are supported:

* s: the search string
* sd: (optional) the start date (dd-mm-yyyy)
* ed: (optional) the end date (dd-mm-yyyy)

For example to search for a term within a certain time range:

http://andernieuws.rdlabs.beeldengeluid.nl/andernieuws/search?s=haven&sd=02-01-2013&ed=02-03-2013

Concerning searches within a certain period, it is possible to only supply a start date or an end date. In these cases the search will only search from or until a certain date.


Prototype
--------------

It's possible to experiment with the Ander Nieuws data by using the following prototype that was built on top of the API:

http://andernieuws.rdlabs.beeldengeluid.nl/andernieuws


Using the source
=================


The source consists of two things:
* The ASRIndexer.py and main.py (Python code) that enables the indexing of our ASR XMLs.
* The andernieuws-server.js (NodeJS) which runs the API

Indexing
---------------
The indexing script requires the following:

* Make sure to install  (https://www.elastic.co/products/elasticsearch)
* Before running the script, make sure to create an index that uses the provided mapping.json and setting.json (see the resource folder). You can create this index yourself or use the createIndex() function that is part of the ASRIndexer.py script
* Make sure that you have installed all the required Python libraries (check the imports at the top). Most likely you need to install lxml (http://lxml.de/) and elasticsearch (https://github.com/elastic/elasticsearch-py)
* Make sure to fill a directory with ASR transcripts (see ASR XML format)

Then make sure to uncomment the desired commands in main.py, depending what you want:

	""" uncomment the following to create an empty index on your local Elasticsearch"""
	#indexer.createIndex(es, indexName, '../resources/settings.json', '../resources/mapping.json')

	""" uncomment the following to index a directory with ASR files"""
	#x.indexASRDirectory('PATH TO YOUR DIRECTORY HOLDING ASR XML FILES', es, indexName)


Then you can run the indexer by:

	python main.py


To run the

Running the API
-----------------

TODO
