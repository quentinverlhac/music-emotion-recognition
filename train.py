import tensorflow as tf

import config
from models.basic_cnn import BasicCNN
from models.pianocktail_gru import PianocktailGRU
import utils


def train():
    # import data and labels
    train_spectrograms = utils.load_dump(config.DEV_DATA_PATH if config.IS_DEV_MODE else config.TRAIN_DATA_PATH)
    train_labels = utils.load_dump(config.DEV_LABELS_PATH if config.IS_DEV_MODE else config.TRAIN_LABELS_PATH)

    # generate datasets
    def generate_subspectrogram(duration_s=config.SUBSPECTROGRAM_DURATION_S, fft_rate=config.FFT_RATE):
        spectrograms = train_spectrograms
        labels_ = train_labels

        for i in range(len(labels_)):
            sub_spectro = utils.draw_subspectrogram(spectrograms[i], duration_s, fft_rate,
                                                    random_pick=config.RANDOM_PICK)
            tensor_spectro = tf.convert_to_tensor(sub_spectro)
            tensor_spectro = tf.transpose(tensor_spectro)
            tensor_label = tf.convert_to_tensor(labels_[i])
            yield tensor_spectro, tensor_label

    train_dataset = tf.data.Dataset.from_generator(generate_subspectrogram, (tf.float32, tf.float32))
    train_dataset = train_dataset.batch(config.BATCH_SIZE)

    # building the model
    if config.MODEL == config.ModelEnum.PIANOCKTAIL_GRU:
        model = PianocktailGRU()
    elif config.MODEL == config.ModelEnum.BASIC_CNN:
        model = BasicCNN()
    model.build(input_shape=(config.BATCH_SIZE, config.SUBSPECTROGRAM_POINTS, config.MEL_BINS))
    model.summary()
    optimizer = tf.optimizers.Adam(config.LEARNING_RATE)

    # define metrics
    train_loss = tf.keras.metrics.Mean(name='train_loss')
    train_accuracy = tf.keras.metrics.BinaryAccuracy(name='train_accuracy')

    checkpoint, checkpoint_manager = utils.setup_checkpoints(model, optimizer)

    # declaring forward pass and gradient descent
    @tf.function
    def forward_pass(inputs, labels_, model_):
        print("tracing forward graph")
        predictions_ = model_.call(inputs)
        loss = tf.keras.losses.binary_crossentropy(
            y_true=labels_,
            y_pred=predictions_
        )
        return predictions_, loss

    @tf.function
    def train_step(inputs, labels_, model_):
        print("tracing train graph")
        with tf.GradientTape() as tape:
            predictions_, loss = forward_pass(inputs, labels_, model_)
        gradients = tape.gradient(loss, model_.trainable_variables)
        optimizer.apply_gradients(zip(gradients, model_.trainable_variables))

        # compute metrics
        train_loss.update_state(loss)
        train_accuracy.update_state(labels_, predictions_)

        return predictions_, labels_

    # restore checkpoint
    if config.RESTORE_CHECKPOINT:
        checkpoint.restore(checkpoint_manager.latest_checkpoint)
        print(
            f"Restored checkpoint. Model {checkpoint.model.name} - epoch {checkpoint.epoch.value()} - iteration {checkpoint.iteration.value()}")

    # for test we iterate over samples one by one
    for epoch in range(config.NB_EPOCHS):

        print(f"============================ epoch {epoch} =============================")
        checkpoint.epoch.assign(epoch)

        for iteration, (spectro, label) in enumerate(train_dataset):
            predictions, labels = train_step(spectro, label, model)

            # display metrics
            if iteration % 10 == 0:
                utils.display_and_reset_metrics(train_loss, train_accuracy, predictions, labels, iteration=iteration)

            # manage checkpoint
            checkpoint.iteration.assign(iteration)
            if iteration % config.SAVE_PERIOD == 0:
                checkpoint_manager.save()

    utils.save_model(model, epoch)





def generate_randomized_batched_dataset(use_test_dataset=False, duration_s=config.SUBSPECTROGRAM_DURATION_S,
                                        fft_rate=config.FFT_RATE, mel_bins=config.MEL_BINS):
    dataset = tf.data.Dataset.from_generator(generate_subspectrogram, (tf.float32, tf.float32),
                                             args=[use_test_dataset, duration_s, fft_rate, mel_bins])
    return dataset.batch(config.BATCH_SIZE)


if __name__ == '__main__':
    train()
