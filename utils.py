import os
import numpy as np
import config
import pandas as pd
import pickle as pkl
import tensorflow as tf
from pathlib import Path

def create_directory_if_doesnt_exist(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def draw_subspectrogram(spectrogram,sub_len,seed=42) :
    """
    Draw a random subspectrogram of given time length from the given spectrogram
    """
    fft_rate = config.SAMPLING_RATE/config.FFT_HOP
    n_points = int(sub_len*fft_rate)
    np.random.seed(seed)
    offset = int(np.random.random()*(spectrogram.shape[1]/fft_rate-sub_len))
    return spectrogram[:,offset:offset+n_points]


def dump_elements(elements, dump_path):
    """
    Dumps all elements in the list to a binary file on the dump path
    """
    with open(dump_path, 'wb') as f:
        pkl.dump(elements, f)

def load_dump(dump_path):
    """
    Load the content of the file at dump path
    """
    with open(dump_path, "rb") as file:
        return pkl.load(file)

def load_labels(path):
    """
    Load a pickle file containing list of labels and return as pandas DataFrame
    """
    with open(path, "rb") as f:
        labels = pkl.load(f)

    # Transform labels to pandas DataFrame
    labels = pd.DataFrame(labels)
    labels.columns = config.EMOTIFY_EMOTIONS_ORDERED_LIST
    return labels

def save_model(model, epoch):
    create_directory_if_doesnt_exist(config.SAVED_MODELS_PATH)
    model.save_weights(os.path.join(
        config.SAVED_MODELS_PATH, '{}_{:06d}.h5'.format(model.name, epoch)))

def setup_checkpoints(model, optimizer):
    create_directory_if_doesnt_exist(config.CHECKPOINTS_PATH)
    checkpoint = tf.train.Checkpoint(
        epoch=tf.Variable(0),
        iteration=tf.Variable(0),
        model=model,
        optimizer=optimizer
    )
    checkpoint_manager = tf.train.CheckpointManager(
        checkpoint,
        config.CHECKPOINTS_PATH, 
        max_to_keep=1
    )
    return checkpoint, checkpoint_manager