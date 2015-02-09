Ander Nieuws API
================

In the Ander Nieuws project, 3 years (2011-2013) of daily news broadcasts were subjected to the following analysis work flow:
1) automatic speech recognition (yielding speech transcripts)
2) keyword detection, based on the speech transcripts (using statistical analysis, involving stopword removal and TF-IDF)
3) indexation of the speech transcripts and keywords in ElasticSearch

API
----------------

The API was built on top of the ElasticSearch index and supports the retrieval of certain keyword clusters based on:
- a search string
- a data range

The obtained clusters are retrieved as follows, given the search string and the date range:
- The index is searched for all occurances of the search string within the speech transcript
- For each hit, the keywords occuring in a radius of 5 seconds around the spoken word are retrieved
- Each retrieved cluster is grouped based on... TODO




