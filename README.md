Ander Nieuws API
================

In the Ander Nieuws project, 3 years (2011-2013) of daily news broadcasts were subjected to the following analysis work flow:

1. automatic speech recognition (yielding speech transcripts)
2. keyword detection, based on the speech transcripts (see keyword detection)
3. indexation of the speech transcripts and keywords in ElasticSearch


Keyword detection
----------------
Keywords were detected based on the following (statistical) analysis techniques:
- Stopword removal
- TF-IDF


API
----------------

The API was built on top of the ElasticSearch index and supports the retrieval of certain keyword clusters based on:
- a search string
- a data range (period)

The obtained clusters are retrieved as follows, given the search string and the specified period:

1. The index is searched for all occurances the search word is mentioned in news videos (that were broadcast within the given period)
2. All hits are grouped per news video (it's possible that the search word occurs multiple times within the news vide)
3. For all of the found occurances per news show, the keywords occurring in a radius of 5 seconds around the occurance are retrieved
4. Finally based on the found keywords per news video, the data is grouped per keyword so that eventually the API returns instances as follows:



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

So for example to search for a term within a certain time range:

	http://andernieuws.rdlabs.beeldengeluid.nl/andernieuws/search?s=haven&sd=02-01-2013&ed=02-03-2013

Concerning searches within a certain period, it is possible to only supply a start date or an end date. In these cases the search will only search from or until a certain date.


Visualization prototype
--------------

It's possible to experiment with the Ander Nieuws data by using the following prototype that was built on top of the API:

	http://andernieuws.rdlabs.beeldengeluid.nl/andernieuws


