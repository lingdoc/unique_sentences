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

def get_percs(bsents, translator, fsents=[], full=False, msents=[], master=False, n=3):
    """
    Get percentages of exact matches from a list of sentences.
    `bsents`:       the list of sentences
    `translator`:   the punctuation remover
    `fsents`:       a list of final sentences to track cross-text matches
    `full`:         whether or not to track cross-text matches
    `msents`:       a master list of final sentences to track cross-corpora matches
    `master`:       whether or not to track cross-corpora matches
    """

    # bsents = [" ".join(x) for x in bsents] # uncomment to not lowercase or remove punctuation
    bsents = [" ".join(x).translate(translator).lower() for x in bsents] # remove punctuation and lowercase
    bsents = [x for x in bsents if len(x.split()) >= n] # only include sentences of n+ words

    bdict = Counter(bsents) # dict to store the unique sentences
    # print("Sentences in text:", len(bsents))
    # print("Length of counter:", len(bdict))
    xsums = sum([v for k, v in bdict.items() if v > 1]) # get the counts of non-unique sentences
    # print("Number of dups:", xsums)
    ysums = sum([v for k, v in bdict.items() if v == 1]) # get the counts of unique sentences
    # print("Number of nondups:", ysums)

    # add all sentences to a master list for this corpus if requested
    if full == True:
        fsents += [x.split() for x in bsents]
    if master == True:
        msents += [x.split() for x in bsents]

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
wordnum = 3 # the minimum number of words in a sentence for comparison
msents = [] # a master list of sentences in all corpora

# go through each of the corpora
for ccorp in tqdm(corplist):
    # check if the corpus has been analyzed previously
    # (delete the json file or remove the entry to re-run analyses)
    if ccorp not in corpcdict.keys():
        print(f'Now counting dups in the `{ccorp}` corpus..')
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
        # the `fileids` field accesses an individual text in a corpus
        for corp in tqdm(b.fileids()):
            bsents = b.sents(corp)
            # print(f"Checking the {corp} dataset:\n{bsents[:10]}")
            ## here we get counts within a text, storing sentences in larger lists
            allcounts.append(get_percs(bsents, translator, fsents=fsents, full=True, msents=msents, master=True, n=wordnum))

        print("Total texts:", len(allcounts))
        bcounts = [x for x in allcounts if x > 0]
        print("Total with dups:", len(bcounts))
        # print(f'{ccorp} total subcorpora: {len(bcounts)}')
        corpcdict[ccorp]['Number of Texts'] = len(allcounts)
        corpcdict[ccorp]['Texts with dups'] = len(bcounts)
        # print(f'{ccorp} highest percentage of dups in a text: {max(bcounts)}')
        try:
            corpcdict[ccorp]['Max dups per text'] = max(bcounts)
        except:
            corpcdict[ccorp]['Max dups per text'] = 0
        # print(f'{ccorp} average percentage of dups per text: {statistics.mean(bcounts)}')
        try:
            corpcdict[ccorp]['Avg dups per text'] = statistics.mean(allcounts)
        except:
            corpcdict[ccorp]['Avg dups per text'] = 0

        # print(f'{ccorp} corpus total sentences: {len(fsents)}')
        corpcdict[ccorp]['Number of sentences'] = len(fsents)
        # print(f'{ccorp} corpus average percent dups: {get_percs(fsents, translator)}')
        corpcdict[ccorp]['Avg dups per corpus'] = get_percs(fsents, translator)

# create a new dict to store totals - this can only be generated accurately by
# re-running all analyses (delete json), since it requires a master list of all
# sentences in order to id matching sentences across corpora
ndict = {"Totals": {}}
ndict["Totals"]['Number of Texts'] = sum([corpcdict[corp]['Number of Texts'] for corp in corpcdict.keys()])
ndict["Totals"]['Texts with dups'] = sum([corpcdict[corp]['Texts with dups'] for corp in corpcdict.keys()])
ndict["Totals"]['Max dups per text'] = max([corpcdict[corp]['Max dups per text'] for corp in corpcdict.keys()])
ndict["Totals"]['Avg dups per text'] = statistics.mean([corpcdict[corp]['Avg dups per text'] for corp in corpcdict.keys()])
ndict["Totals"]['Number of sentences'] = sum([corpcdict[corp]['Number of sentences'] for corp in corpcdict.keys()])
total = get_percs(msents, translator)
ndict["Totals"]['Avg dups per corpus'] = total

corpcdict['Totals'] = ndict['Totals'] # store the results in our combined dict
print(f"total percentage across corpora: {total}")
print(corpcdict) # print the results to terminal

# write the results to the json file
with open(filestr, 'w', encoding='utf-8') as f:
    json.dump(corpcdict, f, ensure_ascii=False, indent=4)

# store the results in a dataframe
df = pd.DataFrame.from_dict(corpcdict, orient='index').reset_index(names=f'Corpus ({wordnum}+ words)')
# convert the following columns to percentages
convert = ['Avg dups per text', 'Avg dups per corpus']
for col in convert:
    df[col+"_perc"] = df[col].round(decimals=4)*100
# write the results to an excel spreadsheet with the corpus names as index
df.to_excel(filen+'-'+str(wordnum)+'+words.xlsx', index=False)
