# This class is meant to make the GUI_APP class cleaner
# "Utilities" will not be instantiated. All methods are
# static

tutorial_msg = """
This tool is designed to aid in the analysis of interviews. The tools provided are geared towards 
computer algorithm analysis.

Layout:
    -Atop the window, you will see dropdown menus. All of the functionality
     of the tool is accessible here, though there are several applicable
     buttons above interview slots.

    -Interview boxes (either 1 or 2) will take up most of the screen.
     These can contain interview text to be navigated and analyzed 
     after being imported with the 'import interview' button.

    -Interview box buttons appear above each interview and are a way to 
    run algorithms easier. 

    -Running each tool will open a pop-up window from which the algorithm
     will run. Several windows can be opened at once to run, though 
     your computer will be slowed down for each algorithm running 
     at one time.

Key Steps for Success:
    -Before running algorithms, load at least 1 interview in with the 
     edit -> 'import interview' button. Several interviews are required
     for some. For best results, load all available interviews.

    -Ensure that several interviews are loaded before proceeding. 
     Having too few will cause a poor result from the algorithms.

    -Give time for the algorithms to run since many of them take 
     a lot of computational power.
"""







import os                                           # allows access to filepath
import tkinter
from tkinter.filedialog import askopenfiles         # allows for file interaction
from tkinter.filedialog import askopenfile          # allows for file interaction
from tkinter.filedialog import askdirectory         # allows for file interaction

from scipy.sparse import lil_matrix  # , save_npz, load_npz
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
import fire
import json
import numpy as np
import tensorflow.compat.v1 as tf

import model, sample, encoder
import pandas as pd

# NEEDED FOR MODELS
import csv
import re
import pickle
from transformers import BertTokenizer, BertModel, BertConfig #need install transformers
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer #need install vaderSentiment
import math
import nltk
from nltk.corpus import stopwords
from itertools import product
from string import ascii_lowercase
from scipy.sparse import coo_matrix
import lda # had to pip install
import matplotlib.pyplot as plt   # we had this one before
import gensim
import gensim.corpora as corpora
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from transformers import logging
from sentence_transformers import SentenceTransformer
import threading
from tkinter.scrolledtext import *
import speech_recognition as sr ##
from pydub import AudioSegment ##
from pydub.silence import split_on_silence ##

logging.set_verbosity_warning()

nlp  = spacy.load('en_core_web_sm')

# A clean container for imported files
class ImportedFile:
    def __init__(self,filepath,contents_as_rb,txt=None):
        self.filepath = filepath
        if not txt is None:
            self.contents_as_rb = contents_as_rb
            self.contents_as_text = txt
        else:
            self.contents_as_rb = contents_as_rb
            self.contents_as_text = contents_as_rb.decode()

        self.lines = [l for l in self.contents_as_text.split('\n') if not l == '' and not l == '\n']
        self.words = [w for w in self.contents_as_text.split(' ')  if not w == '']
        self.chars = [c for c in self.contents_as_text  if not c == ' ' or not c =='']


    #def __dict__(self):
    #    return {'fp' : self.filepath,'rb' : self.contents_as_rb,'txt':self.contents_as_text,
    #            'lines':self.lines,'words':self.words,'chars' : self.chars}
    def __repr__(self):
        return 'new_imported_file\n\t' + str(self.filepath) + '\n\t' + str(self.contents_as_rb) + '\n'


class Utilities:
    supported_types =   (       ("text files", "*.txt"),\
                                ("word files", "*.docx"),\
                                ("pdf files", "*.pdf"),\
                                # Probably will not include in final version
                                ("all files", "*.*")  )

    @staticmethod
    def get_os_root_filepath():
        return os.getcwd()


    @staticmethod
    def get_window_size_as_text(APP_REFERENCE):
        text = str(APP_REFERENCE.settings['init_width'])
        text += 'x'
        text += str(APP_REFERENCE.settings['init_height'])
        return text


    # Upload multiple files to app
    @staticmethod
    def import_files(APP_REFERENCE):

        # Opens blocking tkinter file dialog
        file_list = askopenfiles(mode='rb',filetypes=Utilities.supported_types)

        for file in file_list:
            if not file is None:

                # Add the ImportedFile object to the loaded_files list
                file_object = ImportedFile(file.name,file.raw.read())

                if not file_object in APP_REFERENCE.data['loaded_files']:
                    APP_REFERENCE.data['loaded_files'].append(file_object)

                if not file.name in APP_REFERENCE.data['file_paths']:
                    APP_REFERENCE.data['file_paths'].append(file.name)



        Utilities.save_session(APP_REFERENCE)


    # Upload single file to app
    @staticmethod
    def import_file(APP_REFERENCE,work_block=None):

        file = askopenfile(mode='rb',filetypes=Utilities.supported_types)

        # Add file to the GUI
        if not file is None:
            file_object = ImportedFile(file.name,file.raw.read())

            if not file_object in APP_REFERENCE.data['loaded_files']:
                APP_REFERENCE.data['loaded_files'].append(file_object)

            if not file.name in APP_REFERENCE.data['file_paths']:
                APP_REFERENCE.data['file_paths'].append(file.name)

        else:
            print("File did not load correctly")
            return

        # Open the file in the view container if it exists
        if not work_block.interview_container is None:
            work_block.interview_container.configure(state="normal")
            work_block.interview_container.delete('0.0',tkinter.END)
            text = APP_REFERENCE.data['loaded_files'][-1].contents_as_rb.decode()
            work_block.interview_container.insert(tkinter.END,f"{text}\n")
            work_block.interview_container.configure(state="disabled")


    # this method will be used to export the
    # results of our NLP magic post-processing
    # of the data
    @staticmethod
    def export_file(APP_REFERENCE):
        # method currently does nothing...
        print("exporting! - (nothing to export yet....)")


    # Save the file dictionary to a file that
    # can be imported at a later time into the
    # GUI APP
    @staticmethod
    def save_session(APP_REFERENCE):

        # Keep track of the filepaths and rawbyte contents
        # Thereof
        filepaths = []

        # Save all filepaths and raw bytes
        for f in APP_REFERENCE.data['loaded_files']:
            filepaths.append(f.filepath)

        # Create 1 dictionary to store everything in
        save_dump = {   'settings'  : APP_REFERENCE.settings,
                    }

        # Serialize this dictionary and save to file
        save = open('session.tmp','w')
        save.write(json.dumps(save_dump))


    # Recover the file dictionary to rebuild
    # the most recent file dictionary for the
    # GUI APP. Will always look for 'gui_sess.tmp'
    @staticmethod
    def load_session(APP_REFERENCE):
        saved_state = open('session.tmp','r').read()
        save_data = json.loads(saved_state)

        fp = save_data['fp']
        rb = save_data['rb']

        for f,r in zip(fp,rb):
            APP_REFERENCE.data['loaded_files'].append(ImportedFile(f,None,txt=r))
        APP_REFERENCE.settings = save_data['settings']


    @staticmethod
    def display_help(APP_REFERENCE):
        pop_up = tkinter.Tk()
        pop_up.title("QuaRT Tutorial")

        # Create tutorial
        mainframe       = tkinter.Frame(pop_up)
        output_container = tkinter.scrolledtext.ScrolledText(mainframe, font=(APP_REFERENCE.settings['font'],APP_REFERENCE.settings['text_size']))
        output_container.pack(expand=True,fill=tkinter.BOTH)
        mainframe.pack(expand=True,fill=tkinter.BOTH)
        output_container.insert(tkinter.END,tutorial_msg)
        output_container.configure(state="disabled")

class Algorithms:


    @staticmethod
    def run_alg_in_window(APP_REF,model):

        # Algorithms
        algorithms = {  "Doc Cluster"   : Algorithms.DocClusterer(APP_REF),
                        "Topic Model"   : Algorithms.TopicModeler(None),
                        "LDADedicated"  : Algorithms.TopicModeler("Dedicated"),
                        "Classifier"    : Algorithms.Classifier(APP_REF),
                        "GPT"           : Algorithms.gpt(),
                        "Transcription" : Algorithms.Transcriber(APP_REF) ##
                        }

        #Create a window from which the model will be controlled from
        pop_up = tkinter.Tk()
        pop_up.title(model)

        # Create interactable modules
        mainframe       = tkinter.Frame(pop_up)
        output_container = tkinter.scrolledtext.ScrolledText(mainframe, font=(APP_REF.settings['font'],APP_REF.settings['text_size']))

        #Create a thread to do the algorithm computation on
        exec_thread = None

        # Create model specific buttons
        model_params = {}

        if model == "Doc Cluster":
            exec_thread = threading.Thread(target=algorithms[model].run_model,args=[])

            # number category param
            model_params["cat text"]    = tkinter.Label(mainframe,text="Clusters:",width=12,height=2)
            model_params['cat num']     = tkinter.Entry(mainframe)
            model_params['execute']     = tkinter.Button(mainframe,text="run model",command = lambda : exec_thread.run(),width=12,height=2)

            # Set object vars
            algorithms['Doc Cluster'].output_container = output_container
            algorithms["Doc Cluster"].cluster_val = model_params['cat num']

        elif model == "Topic Model":
            algorithms["Topic Model"].output_container = output_container

            # Chose n topics
            model_params["cat text"]        = tkinter.Label(mainframe,text="Clusters:",width=12,height=2)
            model_params['cat num']         = tkinter.Entry(mainframe)

            Gensim_thread                   = threading.Thread(target=algorithms[model].run,args=[APP_REF,"Gensim",model_params['cat num']])
            Lda_thread                      = threading.Thread(target=algorithms[model].run,args=[APP_REF,"Dedicated",model_params['cat num']])

            model_params['execute Gensim']  = tkinter.Button(mainframe,text="run Gensim",command = lambda : Gensim_thread.start(),width=12,height=2)
            model_params['execute LDA']     = tkinter.Button(mainframe,text="run LDA",command = lambda : Lda_thread.start(),width=12,height=2)

        elif model == "Classifier":

            # Choose model
            model_params["cat text"]        = tkinter.Label(mainframe,text="Num Categories:",width=12,height=2)
            model_params['cat num']         = tkinter.Entry(mainframe)

        elif model == "GPT":
            algorithms["GPT"].output_container = output_container

            GPT_thread                      = threading.Thread(target=algorithms[model].interact_model,args=[])
            model_params['run gpt']         = tkinter.Button(mainframe,text="run GPT",command = lambda : GPT_thread.start(),width=12,height=2)

        elif model == "Transcription":
            exec_thread = threading.Thread(target=algorithms[model].run_model,args=[])

            # number category param
            model_params['cat text']    = tkinter.Label(mainframe,text="Audio Transcription:",width=16,height=3)
            model_params['filename']     = tkinter.Button(mainframe,text="Choose file",command= lambda:algorithms["Transcription"].get_auidio_file(),width=16,height=3)
            model_params['execute']     = tkinter.Button(mainframe,text="run model",command = lambda : exec_thread.start(),width=16,height=3)

            # Set object vars
            algorithms['Transcription'].output_container = output_container
            algorithms['Transcription'].filename = model_params['filename']


        for item in model_params:
            model_params[item].pack()

        output_container.pack(expand=True,fill=tkinter.BOTH)
        mainframe.pack(expand=True,fill=tkinter.BOTH)
        pop_up.mainloop()


    @staticmethod
    def remove_stopwords(sentence, pos_tag_list):
        stop_words = stopwords.words('english')
        addl_stopwords = [
                        "unintelligible","yeah","okay","yes","right","interviewer",
                        "interview","record","participant","really","think","well",
                        "around","also","like", "recording"
        ]
        stop_words = stop_words + addl_stopwords


        word_list = []
        if pos_tag_list != []:
            for token in nlp(sentence):
                if token.pos_ in pos_tag_list:
                    word_list.append(token.text)
        else:
            word_list = sentence.split()

        new_word_list = word_list.copy()
        for word in list(word_list):
            word_lower = word.lower()
            if word_lower in stop_words or len(word) < 4 or '’' in word:
                new_word_list = list(filter((word).__ne__, new_word_list))
        new_sentence = " ".join(word for word in new_word_list)
        return new_sentence


    # Takes a string and returns an cleansed string
    @staticmethod
    def cleantextstring(text, pos_tag_list=[]):
        text = text.lower()
        punc = '''!()-[]\{\};:'"\,<>./?@#$%^&*_~''''”''“''…'
        for char in text:
            if char in punc:
                text = text.replace(char, "")
        text = Algorithms.remove_stopwords(text, pos_tag_list)
        return text

    # JENNY'S EMBEDDINGS
    class BertEmbed:
        def __init__(self):
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            self.config = BertConfig.from_pretrained('bert-base-uncased', output_hidden_states=True)
            self.model = BertModel.from_pretrained('bert-base-uncased', config=self.config)


        #returns bert embeddings of a sentence
        def sentenceEmbedding(self,sentence):
            inputs = self.tokenizer(sentence, return_tensors = 'pt')
            outputs = self.model(**inputs)
            last_hidden_states = outputs.last_hidden_state
            return list(last_hidden_states[0][0])

        #param=[[home/file1,home/file2],[home/file3,home/file4]] where it has category 1 and 2
        #these have list of full filepaths
        def dataExtract(self,filepathlist_list):
            nltk.download('stopwords')
            dataDict = {}
            for i, filepathlist in enumerate(filepathlist_list):
                dataDict["category"+str(i+1)] = []
                for filepath in filepathlist:

                    with open(filepath,'rb') as f:
                        f_info = f.read().decode().split("\n")
                        f_info = list(filter(None, f_info))
                        #<add processing here>
                        for line in f_info:
                            dataDict["category"+str(i+1)].append(Algorithms.cleantextstring(line))
            return dataDict

        def makeFeature(self,line):
            line = re.sub(r"\#|\?|\*|\\n|\,|\.", "", line)
            tensors = self.sentenceEmbedding(line) #embed the paragraph

            #Make features for line
            features = []
            for t in tensors:
                features.append(float(t))
            if len(features)!=768:
                print('bad embedding')
                return -1
            x = self.sentiment_scores(Algorithms.cleantextstring(line)) #add vader sentiments
            y = [float(x['neg']), float(x['neu']), float(x['pos'])]
            features = features+y

            if len(features) == 771:
                return features
            else:
                print("vader error")
                return -1

        #takes the dictionary of our data and then vectorizes them using a transformer
        def bertFromDict(self,category_line_list):
            featuresList = []
            for line in category_line_list:
                line_length = len(line)
                if line_length>512: #in case the sentence is too long
                    list_len = math.ceil(line_length / 512.0)
                    lines = []
                    for i in range(list_len):
                        shortline = line[:512]
                        if len(line) > 512: #long section still
                            if not line[512] == " ":
                                shortline = shortline.rsplit(' ', 1)[0]
                        last_char_index = len(shortline)
                        line = line[last_char_index+1:]
                        lines.append(shortline[:last_char_index])
                    for line in lines:
                        features = self.makeFeature(line)
                        if not features == -1:
                            featuresList.append(features)
                else:
                    features = self.makeFeature(line)
                    if not features == -1:
                        featuresList.append(features)

            #store results of the embeddings into a file corresponding to the category
            filename = self.category +"embeddings.txt"
            with open(filename, "w") as f:
                wr = csv.writer(f)
                wr.writerows(featuresList)

        #this function takes a sentence and then performs a sentiment analysis using a twitter vader sentiment tool
        def sentiment_scores(self,sentence):
            #create a SentimentIntensityAnalyzer object.
            sid_obj = SentimentIntensityAnalyzer()

            #the SentimentIntensityAnalyzer object method gives a sentiment dictionary
            #which contains pos, neg, neu, and compound scores.
            sentiment_dict = sid_obj.polarity_scores(sentence)
            return sentiment_dict

        def run(self,APP_REF):
            pop_up = tkinter.Tk()
            text = tkinter.Label(pop_up,text="Num Categories:",width=12,height=2)
            text.pack()
            val = tkinter.Entry(pop_up)
            val.pack()
            submit = tkinter.Button(pop_up,text="ok",command = lambda : self.import_val(val.get(),pop_up),width=12,height=2)
            file_select = tkinter.Button(pop_up,text='File To Classify',command = lambda : self.get_file_to_classify(),width=12,height=2)
            file_select.pack()
            submit.pack()
            pop_up.mainloop()


            self.file_paths= []
            #popus to get all info
            for i in range(self.BERT_categories):
                self.category_files = []
                pop_up = tkinter.Tk()
                submit = tkinter.Button(pop_up,text=f"select category{i+1} files",command = lambda : self.get_cat_files(i,pop_up),width=12,height=2)
                submit.pack()
                pop_up.mainloop()
                self.file_paths.append(self.category_files)
            dataDict = APP_REF.data['models']['bert'].dataExtract(self.file_paths)

            for i in range(self.BERT_categories):
                APP_REF.data['models']['bert'].category = str(i+1)
                APP_REF.data['models']['bert'].bertFromDict(dataDict[f"category{i+1}"])
            print('DONE RUNNING')

        def import_val(self,n,pop_up):
            self.BERT_categories = int(n)
            pop_up.destroy()
            pop_up.quit()
            print(self.BERT_categories)

        def get_file_to_classify(self):
            file = askopenfile(mode='rb',filetypes=Utilities.supported_types)
            self.file_to_classify = ImportedFile(file.name,file.raw.read())

        def get_cat_files(self,i,pop_up):
            files = askopenfiles(mode='rb',filetypes=Utilities.supported_types)
            i_files = []
            for f in files:
                i_files.append(f.name)
            print(i_files)
            self.category_files = i_files
            pop_up.destroy()
            pop_up.quit()


    # JENNY'S CLASSIFIER
    class Classifier:

        def __init__(self,APP_REF):
            self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
            self.config = BertConfig.from_pretrained('bert-base-uncased', output_hidden_states=True)
            self.model = BertModel.from_pretrained('bert-base-uncased', config=self.config)
            self.app    = APP_REF

        def readFileSimple(self,filepath_list):
            featureList_list = []
            for filepath in filepath_list:
                with open(filepath, 'r') as read:
                    readerStore = csv.reader(read)
                    featureList = list(readerStore)
                    featureList_list.append(featureList)
            return featureList_list

        #trains the model via a logistic regression
        def logReg(self,featureList_list): #takes in list of BERT embeddings of suicidal and non suicidal
            #citation: code below is mostly from https://www.marktechpost.com/2021/02/12/logistic-regression-with-a-real-world-example-in-python/
            X = []
            y = []
            category_num = len(featureList_list)
            for num, featureList in enumerate(featureList_list):
                for i in range(len(featureList)):
                    if not len(featureList[i]) == 0:
                        X.append(featureList[i])
                        y.append(num+1) #1 is passed, 2 is not passed
            classifier = None
            if category_num == 2:
                classifier = LogisticRegression(random_state = 0, max_iter=5000)
            else:
                classifier = LogisticRegression(multi_class='multinomial', solver='lbfgs', random_state = 0, max_iter=5000)

            classifier.fit(X, y)

            #save model below into a .sav file
            #citation: https://machinelearningmastery.com/save-load-machine-learning-models-python-scikit-learn/
            filename = 'classify_classifier.sav'
            pickle.dump(classifier, open(filename, 'wb'))

            # #using hold out data, predict suicisuicidetestde or non-suicide
            # y_pred = classifier.predict(X_test)
            #
            # #confusion tables
            # confusion = confusion_matrix(y_test, y_pred)
            # print('Confusion:',confusion)

        #this function below is for use in classify
        def bertFromLine(self,line):
            tensors = self.app.data['models']['bert'].sentenceEmbedding(line)
            features = []
            for t in tensors:
                features.append(float(t))
            if len(features)!=768:
                print('bad embedding')
                return
            #x = sentiment_scores(clean(i))
            x = self.app.data['models']['bert'].sentiment_scores(line)
            y = [float(x['neg']), float(x['neu']), float(x['pos'])]
            features = features+y
            return features

        def classify_predictforline(self,line, category_num_index, filewriter, classifier, flag): #categorynum is indexed at 0 so category 1 is 0
            features = self.bertFromLine(line)
            if len(features)!=771:
                print('ERROR: Bad embedding, len not 771:', len(features))
                return -1
            else:
                features = [features]
                pred = classifier.predict_proba(features)
                predlist = (pred[0]).tolist()
                category_weight = predlist[category_num_index]

            #write line to file
            filewriter.write(str(category_weight) + " " + line + "\n")

            #return probability
            if flag == "":
                return category_weight
            elif flag == "v":
                return predlist
            return -1


        # Filepath: file we want to classify
        # Category_num: The cat that we want to check against -- but if verbose: this doesnt makee
        def classify(self,filepath, category_num=1, outfile_path="classify_highprobabilitylines.txt", flag=""):
            category_num_index = category_num - 1
            classifier = pickle.load(open('classify_classifier.sav', 'rb'))


            #remove file if exists
            if os.path.exists(outfile_path):
                os.remove(outfile_path)

            #open file to append
            filewriter = open(outfile_path, "a")

            with open(filepath,encoding="utf_8") as f:
                num_valid_lines = 0
                probability_sum = 0
                probability_sum_list = [] #used only when flag == "v"
                f_info = f.read().split("\n")

                for line in f_info:
                    if line == "\n" or line == " ":
                        continue
                    line_length = len(line)
                    if line_length>512:
                        list_len = math.ceil(line_length / 512.0)
                        lines = []

                        for i in range(list_len):
                            shortline = line[:512]
                            if len(line) > 512: #long section still
                                if not line[512] == " ":
                                    shortline = shortline.rsplit(' ', 1)[0]
                            last_char_index = len(shortline)
                            line = line[last_char_index+1:]
                            lines.append(shortline[:last_char_index])

                        for line in lines:
                            probability = self.classify_predictforline(line, category_num_index, filewriter, classifier, flag)
                            if not probability == -1:
                                num_valid_lines = num_valid_lines + 1
                                if flag == "":
                                    probability_sum = probability_sum + probability

                                if flag == "v":
                                    if probability_sum_list == []:
                                        probability_sum_list = probability
                                    else:
                                        for index, prob in enumerate(probability):
                                            probability_sum_list[index] = probability_sum_list[index] + prob
                    else:
                        probability = self.classify_predictforline(line, category_num_index, filewriter, classifier, flag)
                        if not probability == -1:
                            num_valid_lines = num_valid_lines + 1
                            if flag == "":
                                probability_sum = probability_sum + probability

                            if flag == "v":
                                if probability_sum_list == []:
                                    probability_sum_list = probability
                                else:
                                    for index, prob in enumerate(probability):
                                        probability_sum_list[index] = probability_sum_list[index] + prob
            if flag == "":
                print(f"This file is {probability_sum/num_valid_lines}% category {category_num}")
            elif flag == "v":
                for index, prob in enumerate(probability_sum_list):
                    print(f"This file is {probability_sum_list[index]/num_valid_lines}% category {index+1}")
            filewriter.close()

        def run(self,APP_REF):
            # Bert is run
            APP_REF.data['models']['bert'].run(APP_REF)

            # classify
            basepath = os.getcwd()
            numdirs = 2

            #run logistic regression tests for evaluation, does not have to run right after bertDicSimpler
            embeddingspaths = []
            for i in range(numdirs):
                embeddingspaths.append(str(i+1)+"embeddings.txt")
            featureList_list = self.readFileSimple(embeddingspaths)
            self.logReg(featureList_list)
            filepath = APP_REF.data['models']['bert'].file_to_classify.filepath
            tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            config = BertConfig.from_pretrained('bert-base-uncased', output_hidden_states=True)
            model = BertModel.from_pretrained('bert-base-uncased', config=config)
            category_num = 2 #which category do you want to look at?
            #optional if set flag to "v" then print out all categories
            self.classify(filepath, category_num, flag="v")



        def import_val(self,n,pop_up):
            self.BERT_categories = int(n)
            pop_up.destroy()
            pop_up.quit()
            print(self.BERT_categories)

        def get_file_to_classify(self):
            file = askopenfile(mode='rb',filetypes=Utilities.supported_types)
            self.file_to_classify = ImportedFile(file.name,file.raw.read())

        def get_cat_files(self,i,pop_up):
            files = askopenfiles(mode='rb',filetypes=Utilities.supported_types)
            i_files = []
            for f in files:
                i_files.append(f.name)
            self.category_files = i_files
            pop_up.destroy()
            pop_up.quit()

    # JENNY'S TM
    class TopicModeler:
        def __init__(self,output_container):
            self.n_topics = 2
            self.output_container = output_container


        #Updated on 21MAR
        def DedicatedLDA(self,filepath_list, num_topics, outfilename="sparseldamatrix_topics.txt", pos_tag_list=["NOUN","ADJ"], data_words=[]):
            self.output_container.insert(tkinter.END,f"Starting LDA Computation\n")

            #Create a dicitonary that maps the document name to the list of important words
            file_dict = {}

            if data_words == []:
                for filepath in filepath_list:
                    with open(filepath,'r',encoding="utf_8") as f:
                        list_of_sentences = f.readlines()
                        #new_list_of_sentences = [] #remove
                        word_list = []
                        for sentence in list_of_sentences:
                            if sentence == "\n":
                                continue
                            new_sentence = Algorithms.cleantextstring(sentence, pos_tag_list)
                            new_sentence = re.sub("\n", " ", new_sentence)
                            if new_sentence != "" and new_sentence != " ":
                                #new_list_of_sentences.append(new_sentence) #remove
                                small_word_list = new_sentence.split()
                                for word in small_word_list:
                                    word_list.append(word)
                        #file_dict[file] = new_list_of_sentences
                        file_dict[filepath] = word_list
            else:
                for index in range(len(data_words)):
                    file_dict[f"question{index}"] = data_words[index]

            # Convert data in dictionary of key: filenames, values: list of words
            filenames = list(file_dict.keys()) # Make array of file names to be the rows of the DTM
            filenames = np.array(filenames) # Convert to NumPy array

            # Make set of unique vocab over all the interviews
            num_unique_vocab = 0 #to help create matrix
            vocab = set()
            for words in file_dict.values():
                unique_words = set(words)    # all unique terms of this file
                vocab |= unique_words           # set union: add unique terms of this file
                num_unique_vocab += len(unique_words)  # add count of unique terms in this file
            vocab = np.array(list(vocab)) # Convert vocab to NumPy array

            # Create array to hold indices that sort vocab and help count the terms
            vocab_sorter = np.argsort(vocab)

            # Dimensions of DTM
            num_files = len(filenames)
            num_vocab = len(vocab)

            '''
            Create three arrays for the scipy.sparse.coo_matrix (COOrdinate format), which
            takes 3 parameters: data (entries), row indices of matrix, col indices of matrix

            Specify the data type to C integer (32 bit), which is less than the default np
            64 bit float, which takes a lot of memory
            '''
            data = np.empty(num_unique_vocab, dtype=np.intc)
            rows = np.empty(num_unique_vocab, dtype=np.intc)
            cols = np.empty(num_unique_vocab, dtype=np.intc)

            # Loop through the documents to fill the 3 above arrays for the matrix
            index = 0 # current index in the sparse matrix data
            for filename, word_list in file_dict.items():
                insert_points = np.searchsorted(vocab, word_list, sorter=vocab_sorter)
                word_indices = vocab_sorter[insert_points]

                # Count the unique terms of the document and get their vocab indices
                unique_index_list, unique_word_count_list = np.unique(word_indices,return_counts=True)
                num_unique_indices = len(unique_index_list)
                index_fill_end = index + num_unique_indices

                data[index:index_fill_end] = unique_word_count_list
                cols[index:index_fill_end] = unique_index_list
                index_file = np.where(filenames == filename) #index_file is the index of the particular file
                rows[index:index_fill_end] = np.repeat(index_file, num_unique_indices)

                index = index_fill_end # counter continues into next file to add more

            # Create the coo_matrix
            dtm = coo_matrix((data, (rows,cols)), shape=(num_files, num_vocab), dtype=np.intc)

            model = lda.LDA(n_topics=num_topics, n_iter=50  , random_state=1)
            model.fit(dtm)
            topic_word = model.topic_word_

            if os.path.exists(outfilename):
                os.remove(outfilename)

            with open (outfilename, "w") as writer:
                for i, topic_dist in enumerate(topic_word):
                    topic_words = np.array(vocab)[np.argsort(topic_dist)][:-(num_topics+1):-1]

                    writer.write(f"Topic {i}:\n")
                    self.output_container.insert(tkinter.END,f"Topic {i}:\n")
                    self.output_container.insert(tkinter.END,f"{str(topic_words)}:\n")

                    writer.write(str(topic_words) + "\n")

        #Uses LDA Multi-Core Topic Modeling to print out specified topics and a specific number of words from that topic to a specifiable file
        #Updated to unigrams on 21MAR
        def GensimLDA(self,filepath_list, num_topics=10, num_words=3, outfile_path="ldamulticoretopics_out.txt", pos_tag_list=["NOUN","ADJ"], data_words=[]):
            self.output_container.insert(tkinter.END,"Starting Gensim model...")

            if data_words == []:
                whole_text = ""
                try:
                    for filepath in filepath_list:
                        with open(filepath,"r",encoding="utf_8") as f:
                            whole_text = whole_text + " " + f.read()
                except Exception as e :
                    print(e)
                    self.output_container.insert(tkinter.END,f"Error running Gensim model LDA")
                    exit(2)
                #split by end punctuation into sentences
                sentences_list = re.split('[\.\?\!\\n]\s*', whole_text)

                #create list of word lists
                for sentence in sentences_list:
                    sentence = Algorithms.cleantextstring(sentence, pos_tag_list)
                    word_list = sentence.split()
                    if sentence != "":
                        data_words.append(word_list)

            # Create dictionary
            data_dict = corpora.Dictionary(data_words)

            # Create corpus
            texts = data_words

            # Term Document Frequency
            corpus = [data_dict.doc2bow(text) for text in texts]

            # Build LDA model
            lda_model = gensim.models.LdaMulticore(corpus=corpus,
                                                   id2word=data_dict,
                                                   num_topics=num_topics)

            topics = lda_model.show_topics(num_topics, num_words)
            if os.path.exists(outfile_path):
                os.remove(outfile_path)
            for tuple in topics:
                with open(outfile_path, "a") as w:
                    print(f"Category {str(tuple[0])}: {tuple[1]}\n\n")
                    self.output_container.insert(tkinter.END,f"Category {str(tuple[0])}: {tuple[1]}\n\n")
                    w.write(f"Category {str(tuple[0])}: {tuple[1]}\n\n")

        def run(self,APP_REF,model,entry_text):
            topics = int(entry_text.get())
            if model == 'Dedicated':
                filepath_list = APP_REF.data['file_paths']
                self.DedicatedLDA(filepath_list, num_topics=topics, outfilename="ldamulticoretopics_out.txt")

            elif model == 'Gensim':
                filepath_list = [f.filepath for f in APP_REF.data['loaded_files']]
                self.GensimLDA(filepath_list, num_topics=topics,pos_tag_list=["NOUN","ADJ"])

        def import_val(self,n,pop_up):
            self.topics = int(n)
            pop_up.destroy()
            pop_up.quit()
            print(self.BERT_categories)

        def get_file_to_classify(self):
            file = askopenfile(mode='rb',filetypes=Utilities.supported_types)
            self.file_to_classify = ImportedFile(file.name,file.raw.read())

        def get_cat_files(self,i,pop_up):
            files = APP_REF.data['loaded_files']
            i_files = []
            for f in files:
                i_files.append(f.name)
            print(i_files)
            self.category_files = i_files
            pop_up.destroy()
            pop_up.quit()

    class DocClusterer:
        def __init__(self,APP_REF):
            self.n_clusters = 2
            self.output_container = None
            self.cluster_val = None
            self.APP_REF = APP_REF

        def run_model(self):
            self.n_clusters = int(self.cluster_val.get())
            self.output_container.insert(tkinter.END,f"running with {self.n_clusters} clusters\n")


            stopwords = ["ledford","luning","cdr","deirdre","celeste","dr","dixon","ya","unintelligible"]
            stopwords += ["patti","hmm","mm","umm","uh","interviewer","uhh","participant","um","ok","uhm"]

            # Creat the vocabs and docwords
            vectorizer = CountVectorizer(strip_accents="unicode",max_df =.5,stop_words = stopwords,ngram_range = (1,1))
            tfidfer = TfidfTransformer(sublinear_tf=True)

            raw_text = [ re.sub(r"[0-9]|[']","", open(f,'r',encoding="utf_8").read()) for f in self.APP_REF.data['file_paths']]


            dword_matrix = vectorizer.fit_transform(raw_text)
            dword_matrix = tfidfer.fit_transform(dword_matrix)

            vocab = vectorizer.get_feature_names_out()
            self.dword_matrix = dword_matrix.tocsr()

            # make K means model - default value should be 2
            self.kmeansModel = KMeans(n_clusters=self.n_clusters)

            # Run the model on the data
            self.output_container.insert(tkinter.END,f"fitting model\n")

            self.kmeansModel.fit(self.dword_matrix)

            self.output_container.insert(tkinter.END,f"predicting model\n")
            self.clusters = self.kmeansModel.predict(self.dword_matrix)
            self.cluster_centers = self.kmeansModel.cluster_centers_


            # Show info from the model
            for i, doc in enumerate(self.cluster_centers):
                # grab top 10 word IDs
                top10_wid = sorted(range(len(doc)), key=lambda sub: doc[sub])[-10:]

                # map wid to actual words
                comn_word_list = []
                for wid in top10_wid:
                    comn_word_list.append(vocab[wid])

                # **** PRINTING THE TOP 10 WORDS IN THE CLUSTER ****
                self.output_container.insert(tkinter.END,f"Cluster {i}: {comn_word_list}\n")


        # MAKE A STATIC METHOD AND PASS IN SCRIOLLED TEXST AND VAL FOR CLUSTER NUMS
        def run(self,APP_REF):
            self.run_thread = threading.Thread(target=self.model_run,args=[])

            pop_up = tkinter.Tk()
            pop_up.title("DocClustering")


            # Create interactable modules
            mainframe = tkinter.Frame(pop_up)

            self.text = tkinter.Label(mainframe,text="Num Categories:",width=12,height=2)
            self.cluster_val = tkinter.Entry(mainframe)
            self.interview_container = tkinter.scrolledtext.ScrolledText(mainframe, font=(APP_REF.settings['font'],APP_REF.settings['text_size']))
            submit = tkinter.Button(mainframe,text="run model",command = lambda : self.run_thread.run(),width=12,height=2)




            self.text.pack()
            self.cluster_val.pack()
            submit.pack()
            self.interview_container.pack(expand=True,fill=tkinter.BOTH)
            mainframe.pack(expand=True,fill=tkinter.BOTH)
            pop_up.mainloop()

    class gpt:
        def __init__(self):
            self.output_container = None
            pass

        def interact_model(self,
            model_name='data',
            seed=None,
            nsamples=1,
            batch_size=1,
            length=100,
            temperature=.8,
            top_k=40,
            top_p=1,
            models_dir='models'):

            models_dir = os.path.expanduser(os.path.expandvars(models_dir))
            if batch_size is None:
                batch_size = 1
            assert nsamples % batch_size == 0

            enc = encoder.get_encoder(model_name, models_dir)
            hparams = model.default_hparams()

            input(f"dir: {models_dir} type: {type(models_dir)}")
            input(f"name: {model_name} t : {type(model_name)}")
            with open(os.path.join(models_dir, model_name, 'hparams.json')) as f:
                hparams.override_from_dict(json.load(f))

            if length is None:
                length = hparams.n_ctx // 2
            elif length > hparams.n_ctx:
                raise ValueError("Can't get samples longer than window size: %s" % hparams.n_ctx)

            with tf.Session(graph=tf.Graph()) as sess:
                context = tf.placeholder(tf.int32, [batch_size, None])
                np.random.seed(seed)
                tf.set_random_seed(seed)
                output = sample.sample_sequence(
                    hparams=hparams, length=length,
                    context=context,
                    batch_size=batch_size,
                    temperature=temperature, top_k=top_k, top_p=top_p
                )

                saver = tf.train.Saver()
                ckpt = tf.train.latest_checkpoint(os.path.join(models_dir, model_name))
                saver.restore(sess, ckpt)

                while True:

                    raw_text = input("Model prompt >>> ")
                    while not raw_text:
                        print('Prompt should not be empty!')
                        raw_text = input("Model prompt >>> ")
                    context_tokens = enc.encode(raw_text)
                    generated = 0
                    for _ in range(nsamples // batch_size):
                        out = sess.run(output, feed_dict={
                            context: [context_tokens for _ in range(batch_size)]
                        })[:, len(context_tokens):]
                        for i in range(batch_size):
                            generated += 1
                            text = enc.decode(out[i])
                            print("=" * 40 + " SAMPLE " + str(generated) + " " + "=" * 40)
                            print(text)
                    print("=" * 80)

        def run(self,APP_REF):
            APP_REF.data['models']['gpt'].interact_model()

    class Transcriber:
        def __init__(self,APP_REF):
            self.output_container = None
            self.APP_REF = APP_REF

        def get_auidio_file(self):
            self.file = askopenfile(mode='rb',filetypes=Utilities.supported_types)

        def run_model(self):
            self.output_container.insert(tkinter.END,f"transcribing {self.file.name}\n")
            #Create a speech recognition object
            r = sr.Recognizer()

            fname = self.file.name
            print(f"using {fname}.txt")
            f = open(f"{fname}.txt", "a")

            try:
                #Open the audio file using pydub
                self.output_container.insert(tkinter.END,f"\tLoading Audio\n")

                if self.file.name[-3:] in ["MP3", "mp3"]:
                    sound = AudioSegment.from_mp3(self.file.name) 
                elif self.file.name[-3:] in ["WAV","wav"]:
                    sound = AudioSegment.from_wav(self.file)
                else:
                    self.output_container.insert(tkinter.END,f"\tfound {self.file.name[-3:]}\n")
                #Split audio sound where silence is 700 ms+ and get chunks
                self.output_container.insert(tkinter.END,f"\tSplitting file\n")
                chunks = split_on_silence(sound, min_silence_len = 500, silence_thresh = sound.dBFS-14, keep_silence=500)

                folder_name = "audio-chunks"
                #Create a directory to store the audio chunks
                if not os.path.isdir(folder_name):
                    os.mkdir(folder_name)
                whole_text = ""
                #Process each chunk
                for i, audio_chunk in enumerate(chunks, start=1):
                    #Export audio chunk and save in 'folder_name' directory
                    chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
                    audio_chunk.export(chunk_filename, format="wav")
                    #Recognize the chunk
                    with sr.AudioFile(chunk_filename) as source:
                        audio_listened = r.record(source)
                        #Convert to text
                        try:
                            text = r.recognize_google(audio_listened)
                        except sr.UnknownValueError as e:
                            info = "...\n"
                            f.write(info)
                        else:
                            text = f"{text.capitalize()}.\n "
                            info = chunk_filename + ":" + text
                            f.write(info)
                            whole_text += text
            except Exception as e:
                self.output_container.insert(tkinter.END,f"ERROR: {e[:100]}\n- aborting\n")
                whole_text = "Transcription Failed"

            f.close()
            self.output_container.insert(tkinter.END,f"Finished Transcription of {self.file.name}\n")

            return whole_text

        # MAKE A STATIC METHOD AND PASS IN SCRIOLLED TEXST AND VAL FOR CLUSTER NUMS
        def run(self,APP_REF):
            self.run_thread = threading.Thread(target=self.model_run,args=[])

            pop_up = tkinter.Tk()
            pop_up.title("Audio Transcription")

            path = APP_REF.data['file_paths'][0] # I only want to grab one file??
            self.run_model(path, outfilename=path+".txt")



            self.text.pack()
            self.cluster_val.pack()
            submit.pack()
            self.interview_container.pack(expand=True,fill=tkinter.BOTH)
            mainframe.pack(expand=True,fill=tkinter.BOTH)
            pop_up.mainloop()
