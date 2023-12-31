# -*- coding: utf-8 -*-
"""Model_Heart.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YAzKBb2ZSNxGal4MInGNEDX3ob0ofaK-
"""

import pandas as pd
import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import glob
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize
import warnings
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
import tensorflow
from tensorflow.keras.layers import LSTM, Dense
import IPython.display as ipd

from google.colab import drive
drive.mount('/content/drive')

audio_files_a = "/content/drive/MyDrive/IEEE/IoT Stethescope/heart_sounds/"
set_a_csv = pd.read_csv("/content/drive/MyDrive/IEEE/IoT Stethescope/heart_sounds/set_a.csv")
set_a_csv.head()

audio_files_b = "/content/drive/MyDrive/IEEE/IoT Stethescope/heart_sounds/set_b"
set_b_csv = pd.read_csv("/content/drive/MyDrive/IEEE/IoT Stethescope/heart_sounds/set_b.csv")
set_b_csv.head()

frames = [set_a_csv, set_b_csv]
train_ab=pd.concat(frames)
train_ab.describe()

nab_classes=train_ab.label.unique()

print("Number of training examples=", train_ab.shape[0], "  Number of classes=", len(nab_classes))
print (nab_classes)

na_classes = set_a_csv.label.unique()
print("Number of training examples=", set_a_csv.shape[0], "  Number of classes=", len(na_classes))
print (na_classes)

category_group = train_ab.groupby(['label','dataset']).count()
plot = category_group.unstack().reindex(category_group.unstack().sum(axis=1).sort_values().index)\
          .plot(kind='bar', stacked=True, title="Number of Audio Samples per Category", figsize=(16,5))
plot.set_xlabel("Category")
plot.set_ylabel("Samples Count");

print('Min samples per category = ', min(train_ab.label.value_counts()))
print('Max samples per category = ', max(train_ab.label.value_counts()))

audio1 = audio_files_a + "set_a/artifact__201012172012.wav"
y, t = librosa.load(audio1, sr = 22000)
librosa.display.waveplot(y, t, alpha=1)
plt.xlabel("Time (in seconds)")
plt.ylabel("Amplitude")
plt.title("Waveform")

ipd.Audio(audio1)

audio1_murmur = audio_files_a + "set_a/artifact__201012172012.wav"
y, t = librosa.load(audio1_murmur, sr = 22000)
librosa.display.waveplot(y, t, alpha=1)
plt.xlabel("Time (in seconds)")
plt.ylabel("Amplitude")
plt.title("Waveform")

import os
import wave
with wave.open("/content/drive/MyDrive/IEEE/IoT Stethescope/heart_sounds/set_a/Aunlabelledtest__201101152256.wav", "rb") as wave_file:
    frame_rate = wave_file.getframerate()
    print(frame_rate)

import wave
wav = wave.open(audio1)
print("Sampling (frame) rate = ", wav.getframerate())
print("Total samples (frames) = ", wav.getnframes())
print("Duration = ", wav.getnframes()/wav.getframerate())

"""MFCC"""

y, sr = librosa.load(audio1)
mfccs = librosa.feature.mfcc(y=y, sr=sr)
print (mfccs)

S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128,fmax=8000)
log_S=librosa.feature.mfcc(S=librosa.power_to_db(S))
print (log_S)

mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
plt.figure(figsize=(12, 3))
librosa.display.specshow(mfccs, x_axis='time')
plt.colorbar()
plt.title('Mel-frequency cepstral coefficients (MFCCs)')
plt.tight_layout()

onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
librosa.frames_to_time(onset_frames, sr=sr)

o_env = librosa.onset.onset_strength(y, sr=sr)
times = librosa.frames_to_time(np.arange(len(o_env)), sr=sr)
onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, sr=sr)

D = np.abs(librosa.stft(y))
plt.figure(figsize=(16, 6))
ax1 = plt.subplot(2, 1, 1)
librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max),x_axis='time', y_axis='log')
plt.title('Power spectrogram')
plt.subplot(2, 1, 2, sharex=ax1)

plt.plot(times, o_env, label='Onset strength')
plt.vlines(times[onset_frames], 0, o_env.max(), color='r', alpha=0.9,linestyle='--', label='Onsets')
plt.axis('tight')
plt.legend(frameon=True, framealpha=0.75)

"""#Loading The Data"""

print("Number of training examples=", train_ab.shape[0], "  Number of classes=", len(train_ab.label.unique()))

def audio_norm(data):
    max_data = np.max(data)
    min_data = np.min(data)
    data = (data-min_data)/(max_data-min_data+0.0001)
    return data-0.5

# get audio data without padding highest qualify audio
def load_file_data_without_change(folder,file_names, duration=3, sr=16000):
    input_length=sr*duration
    # function to load files and extract features
    # file_names = glob.glob(os.path.join(folder, '*.wav'))
    data = []
    for file_name in file_names:
        try:
            sound_file=folder+file_name
            print ("load file ",sound_file)
            # use kaiser_fast technique for faster extraction if not use 'kaiser_best' changed it here
            X, sr = librosa.load( sound_file, res_type='kaiser_best') 
            dur = librosa.get_duration(y=X, sr=sr)
            # extract normalized mfcc feature from data
            mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sr, n_mfcc=40).T,axis=0) 
        except Exception as e:
            print("Error encountered while parsing file: ", file)
        feature = np.array(mfccs).reshape([-1,1])
        data.append(feature)
    return data


# get audio data with a fix padding may also chop off some file
def load_file_data (folder,file_names, duration=12, sr=16000):
    input_length=sr*duration
    # function to load files and extract features
    # file_names = glob.glob(os.path.join(folder, '*.wav'))
    data = []
    for file_name in file_names:
        try:
            sound_file=folder+file_name
            print ("load file ",sound_file)
            # use kaiser_fast technique for faster extraction
            X, sr = librosa.load( sound_file, sr=sr, duration=duration,res_type='kaiser_fast') 
            dur = librosa.get_duration(y=X, sr=sr)
            # pad audio file same duration
            if (round(dur) < duration):
                print ("fixing audio lenght :", file_name)
                y = librosa.util.fix_length(X, input_length)                
            #normalized raw audio 
            # y = audio_norm(y)            
            # extract normalized mfcc feature from data
            mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sr, n_mfcc=40).T,axis=0)             
        except Exception as e:
            print("Error encountered while parsing file: ", file)        
        feature = np.array(mfccs).reshape([-1,1])
        data.append(feature)
    return data

from sklearn.model_selection import train_test_split
from sklearn import preprocessing

# Map label text to integer
CLASSES = ['artifact','murmur','normal']
# {'artifact': 0, 'murmur': 1, 'normal': 3}
NB_CLASSES=len(CLASSES)

# Map integer value to text labels
label_to_int = {k:v for v,k in enumerate(CLASSES)}
print (label_to_int)
print (" ")
# map integer to label text
int_to_label = {v:k for k,v in label_to_int.items()}
print(int_to_label)

import os, fnmatch

MAX_SOUND_CLIP_DURATION=12 
A_folder=audio_files_a+'/set_a/'
# set-a
A_artifact_files = fnmatch.filter(os.listdir(audio_files_a+'/set_a'), 'artifact*.wav')
A_artifact_sounds = load_file_data(folder=A_folder,file_names=A_artifact_files, duration=MAX_SOUND_CLIP_DURATION)
A_artifact_labels = [0 for items in A_artifact_files]

A_normal_files = fnmatch.filter(os.listdir(audio_files_a+'/set_a'), 'normal*.wav')
A_normal_sounds = load_file_data(folder=A_folder,file_names=A_normal_files, duration=MAX_SOUND_CLIP_DURATION)
A_normal_labels = [2 for items in A_normal_sounds]

A_extrahls_files = fnmatch.filter(os.listdir(audio_files_a+'/set_a'), 'extrahls*.wav')
A_extrahls_sounds = load_file_data(folder=A_folder,file_names=A_extrahls_files, duration=MAX_SOUND_CLIP_DURATION)
A_extrahls_labels = [1 for items in A_extrahls_sounds]

A_murmur_files = fnmatch.filter(os.listdir(audio_files_a+'/set_a'), 'murmur*.wav')
A_murmur_sounds = load_file_data(folder=A_folder,file_names=A_murmur_files, duration=MAX_SOUND_CLIP_DURATION)
A_murmur_labels = [1 for items in A_murmur_files]

# test files
A_unlabelledtest_files = fnmatch.filter(os.listdir(audio_files_a+'/set_a'), 'Aunlabelledtest*.wav')
A_unlabelledtest_sounds = load_file_data(folder=A_folder,file_names=A_unlabelledtest_files, duration=MAX_SOUND_CLIP_DURATION)
A_unlabelledtest_labels = [-1 for items in A_unlabelledtest_sounds]

print ("loaded dataset-a")

# Commented out IPython magic to ensure Python compatibility.
# %%time
# # load dataset-b, keep them separate for testing purpose 
# B_folder=audio_files_a+'/set_b/'
# # set-b
# B_normal_files = fnmatch.filter(os.listdir(audio_files_a+'/set_b'), 'normal*.wav')  # include noisy files
# B_normal_sounds = load_file_data(folder=B_folder,file_names=B_normal_files, duration=MAX_SOUND_CLIP_DURATION)
# B_normal_labels = [2 for items in B_normal_sounds]
# 
# B_murmur_files = fnmatch.filter(os.listdir(audio_files_a+'/set_b'), 'murmur*.wav')  # include noisy files
# B_murmur_sounds = load_file_data(folder=B_folder,file_names=B_murmur_files, duration=MAX_SOUND_CLIP_DURATION)
# B_murmur_labels = [1 for items in B_murmur_files]
# 
# B_extrastole_files = fnmatch.filter(os.listdir(audio_files_a+'/set_b'), 'extrastole*.wav')
# B_extrastole_sounds = load_file_data(folder=B_folder,file_names=B_extrastole_files, duration=MAX_SOUND_CLIP_DURATION)
# B_extrastole_labels = [1 for items in B_extrastole_files]
# 
# #test files
# B_unlabelledtest_files = fnmatch.filter(os.listdir(audio_files_a+'/set_b'), 'Bunlabelledtest*.wav')
# B_unlabelledtest_sounds = load_file_data(folder=B_folder,file_names=B_unlabelledtest_files, duration=MAX_SOUND_CLIP_DURATION)
# B_unlabelledtest_labels = [-1 for items in B_unlabelledtest_sounds]
# print ("loaded dataset-b")

x_data = np.concatenate((A_artifact_sounds, A_normal_sounds,A_extrahls_sounds,A_murmur_sounds, B_normal_sounds,B_murmur_sounds,B_extrastole_sounds))

y_data = np.concatenate((A_artifact_labels, A_normal_labels,A_extrahls_labels,A_murmur_labels,
                         B_normal_labels,B_murmur_labels,B_extrastole_labels))

test_x = np.concatenate((A_unlabelledtest_sounds,B_unlabelledtest_sounds))
test_y = np.concatenate((A_unlabelledtest_labels,B_unlabelledtest_labels))

print ("combined training data record: ",len(y_data), len(test_y))

import keras
seed = 1000
# split data into Train, Validation and Test
x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, train_size=0.9, random_state=seed, shuffle=True)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size=0.9, random_state=seed, shuffle=True)

# One-Hot encoding for classes
y_train = np.array(keras.utils.to_categorical(y_train, len(CLASSES)))
y_test = np.array(keras.utils.to_categorical(y_test, len(CLASSES)))
y_val = np.array(keras.utils.to_categorical(y_val, len(CLASSES)))
test_y=np.array(keras.utils.to_categorical(test_y, len(CLASSES)))

print ("label shape: ", y_data.shape)
print ("data size of the array: : %s" % y_data.size)
print ("length of one array element in bytes: ", y_data.itemsize)
print ("total bytes consumed by the elements of the array: ", y_data.nbytes)
print (y_data[1])
print ("")
print ("audio data shape: ", x_data.shape)
print ("data size of the array: : %s" % x_data.size)
print ("length of one array element in bytes: ", x_data.itemsize)
print ("total bytes consumed by the elements of the array: ", x_data.nbytes)
#print (x_data[1])
print ("")
print ("training data shape: ", x_train.shape)
print ("training label shape: ", y_train.shape)
print ("")
print ("validation data shape: ", x_val.shape)
print ("validation label shape: ", y_val.shape)
print ("")
print ("test data shape: ", x_test.shape)
print ("test label shape: ", y_test.shape)

"""#Model"""

from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, LSTM
from keras.layers import Convolution2D, MaxPooling2D
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping,ReduceLROnPlateau,ModelCheckpoint,TensorBoard,ProgbarLogger
from keras.utils import np_utils
from sklearn import metrics 
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import itertools

print('Build LSTM RNN model ...')
model = Sequential()
model.add(LSTM(units=64, activation='sigmoid',dropout=0.05, recurrent_dropout=0.20, return_sequences=True,input_shape = (40,1)))
model.add(LSTM(units=32, activation='tanh',dropout=0.05, recurrent_dropout=0.20, return_sequences=True))
model.add(LSTM(units=16, activation='tanh', dropout=0.05, recurrent_dropout=0.20, return_sequences=True))
model.add(LSTM(units=8, activation='tanh', dropout=0.05, recurrent_dropout=0.20, return_sequences=False))
model.add(Dense(len(CLASSES), activation='softmax'))
model.compile(loss='categorical_crossentropy', optimizer='Adamax', metrics=['acc','mse', 'mae', 'mape'])
model.summary()

# Commented out IPython magic to ensure Python compatibility.
# %%time
# # saved model checkpoint file
# best_model_file="./best_model_trained.hdf5"
# #train_model_file=file_path+"/checkpoints/weights.best_{epoch:02d}-{loss:.2f}.hdf5"
# MAX_PATIENT=12
# MAX_EPOCHS=70
# MAX_BATCH=32
# 
# # callbacks
# # removed EarlyStopping(patience=MAX_PATIENT)
# callback=[ReduceLROnPlateau(patience=MAX_PATIENT, verbose=1), ModelCheckpoint(filepath=best_model_file, monitor='loss', verbose=1, save_best_only=True)]
# 
# # training
# history=model.fit(x_train, y_train, 
#                   batch_size=MAX_BATCH, 
#                   epochs=MAX_EPOCHS,
#                   verbose=0,
#                   validation_data=(x_val, y_val),
#                   callbacks=callback)

