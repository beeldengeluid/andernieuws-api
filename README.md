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
- a data range

The obtained clusters are retrieved as follows, given the search string and the date range:

1. The index is searched for all occurances of the search string within the speech transcript
2. All hits are grouped per news video (it's possible that the search word occurs multiple times within the news vide)
3. For all of the found occurances per news show, the keywords occurring in a radius of 5 seconds around the occurance are retrieved
4. Finally based on the found keywords per news video, the data is grouped per keyword so that eventually the API returns instances as follows:

t

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
