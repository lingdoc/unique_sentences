import nltk, os, string, statistics, json, glob
from tqdm import tqdm
from collections import Counter
import pandas as pd

def check_and_download_nltk_corpus(corpus_name):
    """Check if corpus exists and download if not"""
    try:
        nltk.data.find(f'corpora/{corpus_name}') # see if corpus exists
    except nltk.downloader.LookupError:
        print(f"'{corpus_name}' corpus not found. Downloading now...")
        nltk.download(corpus_name) # Automatically download the missing corpus
        print(f"'{corpus_name}' download complete.")

# a filter for punctuation
translator = str.maketrans('', '', string.punctuation+"，。")

def get_percs(bsents, translator, fsents=[], full=False):
    """
    Get percentages of exact matches from a list of sentences.
    `bsents`:       the list of sentences
    `translator`:   the punctuation remover
    `fsents`:       a list of final sentences to track cross-corpora matches
    `full`:         whether or not to track cross-corpora matches
    """
    # remove punctuation and lowercase
    bsents = [" ".join(x).translate(translator).lower() for x in bsents]
    # bsents = [" ".join(x) for x in bsents] # uncomment to not lowercase or remove punctuation
    
    bdict = Counter(bsents) # dict to store the unique sentences
    # print("Sentences in text:", len(bsents))
    # print("Length of counter:", len(bdict))
    xsums = sum([v for k, v in bdict.items() if v > 1]) # get the counts of non-unique sentences
    # print("Number of dups:", xsums)
    ysums = sum([v for k, v in bdict.items() if v == 1]) # get the counts of unique sentences
    # print("Number of nondups:", ysums)

    # add all sentences to a master list for this corpus if requested
    if full == True:
        fsents += bsents

    if ysums > 0:
        result = xsums/(xsums+ysums)
    else:
        if xsums > 0:
            result = xsums/xsums
        else:
            result = 0

    return result

filen = 'corpus_counts' # this is the name of the files we will generate
filestr = filen+'.json' # this is the json file where we store the counts

# check if the json file exists and load it (so we can update the file in future)
if os.path.exists(filestr):
    with open(filestr, 'r', encoding='utf-8') as f:
        corpcdict = json.load(f)
else:
    corpcdict = {}

# this is the list of corpora that we want to access
corplist = ['brown', 'gutenberg', 'movie_reviews', 'webtext', 'inaugural',
            'state_union', 'bnc', 'childes']

# go through each of the corpora
for ccorp in tqdm(corplist):
    # check if the corpus has been analyzed previously
    # (delete the json file or remove the entry to re-run analyses)
    if ccorp not in corpcdict.keys():
        print(f'Now counting duplicates in the `{ccorp}` corpus..')
        corpcdict[ccorp] = {} # the corpus key to store info
        fsents = [] # a list to keep track of sentences
        allcounts = [] # list to keep track of the counts
        # the BNC corpus needs to be downloaded separately in xml format and placed here
        bncpath = 'corpora/bnc/download/Texts/' # Adjust path as needed
        # the CHILDES corpus needs to be downloaded separately in XML format and placed here
        childespath = 'corpora/CHILDES/data-xml/Eng-NA-xml/' # Adjust path as needed
        if ccorp == 'bnc':
            # we use the NLTK corpus reader to access the files
            from nltk.corpus.reader import BNCCorpusReader
            corpus_root = nltk.data.find(bncpath)
            b = BNCCorpusReader(root=corpus_root, fileids=r'[A-K]/\w*/\w*\.xml')
        elif ccorp == 'childes':
            # the NLTK corpus reader has a CHILDES module as well
            from nltk.corpus.reader import CHILDESCorpusReader
            corpus_root = nltk.data.find(childespath)
            b = CHILDESCorpusReader(corpus_root, '.*.xml') # Reads all XML files in the specified root
        # all other corpora need to be downloaded as well, but this can be done via NLTK
        else:
            check_and_download_nltk_corpus(ccorp) # check/download corpus
            exec(f'from nltk.corpus import {ccorp} as b') # then import it

        # once the respective corpus has been imported, we can access the sentences programmatically
        for corp in tqdm(b.fileids()):
            bsents = b.sents(corp)
            allcounts.append(get_percs(bsents, translator, fsents, full=True))

        print("Total texts:", len(allcounts))
        bcounts = [x for x in allcounts if x > 0]
        print("Total with dups:", len(bcounts))
        # print(f'{ccorp} total subcorpora: {len(bcounts)}')
        corpcdict[ccorp]['numtexts'] = len(allcounts)
        corpcdict[ccorp]['percdups'] = len(bcounts)
        # print(f'{ccorp} highest percentage of dups in a text: {max(bcounts)}')
        try:
            corpcdict[ccorp]['maxdupstx'] = max(bcounts)
        except:
            corpcdict[ccorp]['percdupstx'] = 0
        # print(f'{ccorp} average percentage of dups per text: {statistics.mean(bcounts)}')
        try:
            corpcdict[ccorp]['avgdupstx'] = statistics.mean(bcounts)
        except:
            corpcdict[ccorp]['avgdupstx'] = 0

        # print(f'{ccorp} corpus total sentences: {len(fsents)}')
        corpcdict[ccorp]['numsents'] = len(fsents)
        # print(f'{ccorp} corpus average percent dups: {get_percs(fsents, translator)}')
        corpcdict[ccorp]['avgdups'] = get_percs(fsents, translator)

print(corpcdict) # print the results to terminal

# write the results to the json file
with open(filestr, 'w', encoding='utf-8') as f:
    json.dump(corpcdict, f, ensure_ascii=False, indent=4)

# write the results to an excel spreadsheet with the corpus names as index
df = pd.DataFrame.from_dict(corpcdict, orient='index')
df.to_excel(filen+'.xlsx')
