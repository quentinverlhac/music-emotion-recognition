import tensorflow as tf 

from tensorflow.keras import Model
from tensorflow.keras.layers import Reshape, GRU, GRUCell, Dense, InputLayer

import config


class PianocktailGRU(Model):
    def __init__(self, name='pianocktail_gru', subspectrogram_points = config.SUBSPECTROGRAM_POINTS, mel_bins = config.MEL_BINS, number_of_emotions = config.NUMBER_OF_EMOTIONS, **kwargs):
        super(PianocktailGRU, self).__init__(name=name, **kwargs)

        self.input_layer = InputLayer((subspectrogram_points, mel_bins), name=f"{name}_input")
        
        self.gru = GRU(100, name=f"{name}_gru")

        self.dense = Dense(50, activation=tf.nn.relu, name=f"{name}_dense")

        self.output_layer = Dense(number_of_emotions, activation=tf.nn.sigmoid, name=f"{name}_output")

    def call(self, inputs, training=True):
        net = self.input_layer(inputs)
        net = self.gru(net, training=training)
        net = self.dense(net)
        net = self.output_layer(net)
        return net
