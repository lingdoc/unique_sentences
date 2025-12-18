# Are most sentences unique?

This repository contains code to get counts of unique sentences in English corpora,
based on corpora available in the NLTK library, as well as the well-known British
National Corpus and the CHILDES corpus. This code is used in the paper
["Are most sentences unique? An empirical examination of Chomskyan claims"](https://arxiv.org/abs/2509.19108).

The code automatically downloads the relevant corpora from NLTK, with the exception
of the BNC and CHILDES corpora, which can be downloaded from [HERE](http://corpora.lancs.ac.uk/bnc2014/)
and [HERE](https://talkbank.org/childes/) respectively. After downloading the
corpora and placing them in accessible locations (in XML format) the NLTK library
is used to read them in order to count the number of duplicate sentences.

The following corpora are examined:

`['brown', 'gutenberg', 'movie_reviews', 'webtext', 'inaugural', 'state_union', 'bnc', 'childes']`

The output of the code is released in this repository for ease of access. To re-run
analyses simply delete the json file. Additions (of languages, corpora) are welcome.

The excel spreadsheet contains basic stats related to the counts of sentences and
duplicates within texts in corpora, across texts in corpora, and between corpora.
In order to accurately compute the cross-corpora totals, the saved json file should
be deleted.
