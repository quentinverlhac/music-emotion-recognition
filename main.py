import tensorflow as tf
import pickle as pkl
import config
import numpy as np
from utils import draw_subspectrogram

def main() :

    # import data
    with open(config.EMOTIFY_SPECTROGRAM_DUMP_PATH,"rb") as f:
        spectrograms = pkl.load(f)

    # import labels
    with open(config.EMOTIFY_LABELS_DUMP_PATH,"rb") as f:
        train_labels = pkl.load(f)

    # generate dataset
    def generate_subspectrogram():
        for i in range(len(train_labels)) :
            sub_spectro = draw_subspectrogram(spectrograms[i],5)
            tensor_spectro = tf.convert_to_tensor(sub_spectro)
            tensor_spectro = tf.reshape(tensor_spectro,(128,430,1))
            tensor_label = tf.convert_to_tensor(train_labels[i])
            yield tensor_spectro, tensor_label

    train_dataset = tf.data.Dataset.from_generator(generate_subspectrogram,(tf.float32,tf.float32))
    train_dataset = train_dataset.batch(config.BATCH_SIZE)

    # building the model
    from models.cnn import ConvModel as Model
    model = Model()
    model.build(input_shape=(config.BATCH_SIZE,128,430,1))
    model.summary()
    optimizer = tf.optimizers.Adam(config.LEARNING_RATE)

    #declaring forward pass and gradient descent
    @tf.function
    def forward_pass(inputs,labels):
        print("tracing forward graph")
        predictions = model.call(inputs)
        loss = tf.losses.categorical_crossentropy(
            y_true = labels,
            y_pred = predictions
        )
        return predictions, loss

    @tf.function
    def train_step(inputs,labels):
        print("tracing train graph")
        with tf.GradientTape() as tape:
            predictions, loss = forward_pass(inputs,labels)
        gradients = tape.gradient(loss,model.trainable_variables)
        optimizer.apply_gradients(zip(gradients,model.trainable_variables))
    
    # for test we iterate over samples one by one
    for epoch in range(config.NB_EPOCHS) :

        for iteration, (spectro, label) in enumerate(train_dataset) :
            train_step(spectro,label)

        

if __name__ == "__main__" :
    main()




