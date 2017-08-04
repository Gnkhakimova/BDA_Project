
from urllib.request import urlretrieve
from os.path import isfile, isdir

import inline as inline
from IPython.kernel.zmq.pylab.backend_inline import InlineBackend
from tqdm import tqdm
import problem_unittests as tests
import tarfile

cifar10_dataset_folder_path = 'cifar-10-batches-py'

class DLProgress(tqdm):
    last_block = 0

    def hook(self, block_num=1, block_size=1, total_size=None):
        self.total = total_size
        self.update((block_num - self.last_block) * block_size)
        self.last_block = block_num

if not isfile('cifar-10-python.tar.gz'):
    with DLProgress(unit='B', unit_scale=True, miniters=1, desc='CIFAR-10 Dataset') as pbar:
        urlretrieve(
            'https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz',
            'cifar-10-python.tar.gz',
            pbar.hook)

if not isdir(cifar10_dataset_folder_path):
    with tarfile.open('cifar-10-python.tar.gz') as tar:
        tar.extractall()
        tar.close()


tests.test_folder_path(cifar10_dataset_folder_path)

%matplotlib inline
%config InlineBackend.figure_format = 'retina'

import helper
import numpy as np

# Explore the dataset
batch_id = 2
sample_id = 4
helper.display_stats(cifar10_dataset_folder_path, batch_id, sample_id)

def normalize(x):
    """
    Normalize a list of sample image data in the range of 0 to 1
    : x: List of image data.  The image shape is (32, 32, 3)
    : return: Numpy array of normalize data
    """
    maximum = np.max(x)
    minimum = np.min(x)
    return (x - minimum) / (maximum - minimum)



tests.test_normalize(normalize)

def one_hot_encode(x):
    """
    One hot encode a list of sample labels. Return a one-hot encoded vector for each label.
    : x: List of sample Labels
    : return: Numpy array of one-hot encoded labels
    """
    nx = np.max(x) + 1
    return np.eye(nx)[x]


tests.test_one_hot_encode(one_hot_encode)

# Preprocess Training, Validation, and Testing Data
helper.preprocess_and_save_data(cifar10_dataset_folder_path, normalize, one_hot_encode)

import pickle
import problem_unittests as tests
import helper

# Load the Preprocessed Validation data
valid_features, valid_labels = pickle.load(open('preprocess_validation.p', mode='rb'))

import tensorflow as tf

def neural_net_image_input(image_shape):
    """
    Return a Tensor for a bach of image input
    : image_shape: Shape of the images
    : return: Tensor for image input.
    """
    return tf.placeholder(
        tf.float32,
        [None, image_shape[0], image_shape[1], 3],
        name='x'
    )


def neural_net_label_input(n_classes):
    """
    Return a Tensor for a batch of label input
    : n_classes: Number of classes
    : return: Tensor for label input.
    """
    return tf.placeholder(
        tf.float32,
        [None, n_classes],
        name='y'
    )


def neural_net_keep_prob_input():
    """
    Return a Tensor for keep probability
    : return: Tensor for keep probability.
    """
    return tf.placeholder(tf.float32, name='keep_prob')


tf.reset_default_graph()
tests.test_nn_image_inputs(neural_net_image_input)
tests.test_nn_label_inputs(neural_net_label_input)
tests.test_nn_keep_prob_inputs(neural_net_keep_prob_input)

def conv2d_maxpool(x_tensor, conv_num_outputs, conv_ksize, conv_strides, pool_ksize, pool_strides):
    """
    Apply convolution then max pooling to x_tensor
    :param x_tensor: TensorFlow Tensor
    :param conv_num_outputs: Number of outputs for the convolutional layer
    :param conv_strides: Stride 2-D Tuple for convolution
    :param pool_ksize: kernal size 2-D Tuple for pool
    :param pool_strides: Stride 2-D Tuple for pool
    : return: A tensor that represents convolution and max pooling of x_tensor
    """
    # Tensorflow API
    input_depth = x_tensor.get_shape().as_list()[-1]
    W = tf.Variable(tf.random_normal(
        [conv_ksize[0], conv_ksize[1], input_depth, conv_num_outputs],
        stddev=0.1
    ))
    b = tf.Variable(tf.zeros(conv_num_outputs))
    conv = tf.nn.conv2d(x_tensor, W, [1, conv_strides[0], conv_strides[1], 1], 'SAME') + b
    conv = tf.nn.relu(conv)
    return tf.nn.max_pool(
        conv,
        [1, pool_ksize[0], pool_ksize[1], 1],
        [1, pool_strides[0], pool_strides[1], 1],
        'SAME'
    )


tests.test_con_pool(conv2d_maxpool)

def flatten(x_tensor):
    """
    Flatten x_tensor to (Batch Size, Flattened Image Size)
    : x_tensor: A tensor of size (Batch Size, ...), where ... are the image dimensions.
    : return: A tensor of size (Batch Size, Flattened Image Size).
    """
    shape = x_tensor.get_shape().as_list()
    return tf.reshape(x_tensor, [-1, np.prod(shape[1:])])


tests.test_flatten(flatten)

def fully_conn(x_tensor, num_outputs):
    """
    Apply a fully connected layer to x_tensor using weight and bias
    : x_tensor: A 2-D tensor where the first dimension is batch size.
    : num_outputs: The number of output that the new tensor should be.
    : return: A 2-D tensor where the second dimension is num_outputs.
    """
    shape = x_tensor.get_shape().as_list()
    W = tf.Variable(tf.random_normal([shape[-1], num_outputs], stddev=0.1))
    b = tf.Variable(tf.zeros(num_outputs)) + 0.11
    return tf.nn.relu(tf.add(tf.matmul(x_tensor, W), b))


tests.test_fully_conn(fully_conn)

def output(x_tensor, num_outputs):
    """
    Apply a output layer to x_tensor using weight and bias
    : x_tensor: A 2-D tensor where the first dimension is batch size.
    : num_outputs: The number of output that the new tensor should be.
    : return: A 2-D tensor where the second dimension is num_outputs.
    """
    shape = x_tensor.get_shape().as_list()
    W = tf.Variable(tf.random_normal([shape[-1], num_outputs]))
    b = tf.Variable(tf.zeros(num_outputs))
    return tf.add(tf.matmul(x_tensor, W), b)


tests.test_output(output)


def conv_net(x, keep_prob):
    """
    Create a convolutional neural network model
    : x: Placeholder tensor that holds image data.
    : keep_prob: Placeholder tensor that hold dropout keep probability.
    : return: Tensor that represents logits
    """

    # TODO: Apply 1, 2, or 3 Convolution and Max Pool layers
    #    Play around with different number of outputs, kernel size and stride
    # Function Definition from Above:
    #    conv2d_maxpool(x_tensor, conv_num_outputs, conv_ksize, conv_strides, pool_ksize, pool_strides)
    tmp = conv2d_maxpool(x, 64, [3, 3], [1, 1], [3, 3], [2, 2])
    tf.nn.dropout(tmp, keep_prob=keep_prob)
    # tmp = conv2d_maxpool(tmp, 64, [5, 5], [1, 1], [3, 3], [2, 2])
    # tf.nn.dropout(tmp, keep_prob=keep_prob)
    # tmp = conv2d_maxpool(tmp, 64, [3, 3], [1, 1], [2, 2], [2, 2])
    # tf.nn.dropout(tmp, keep_prob=keep_prob)

    # TODO: Apply a Flatten Layer
    # Function Definition from Above:
    tmp = flatten(tmp)

    # TODO: Apply 1, 2, or 3 Fully Connected Layers
    #    Play around with different number of outputs
    # Function Definition from Above:
    #   fully_conn(x_tensor, num_outputs)
    tmp = fully_conn(tmp, 384)
    tf.nn.dropout(tmp, keep_prob=keep_prob)
    tmp = fully_conn(tmp, 192)
    tf.nn.dropout(tmp, keep_prob=keep_prob)
    # tmp = fully_conn(tmp, 256)
    # tf.nn.dropout(tmp, keep_prob=keep_prob)


    # TODO: Apply an Output Layer
    #    Set this to the number of classes
    # Function Definition from Above:
    #   output(x_tensor, num_outputs)


    # TODO: return output
    return output(tmp, 10)


##############################
## Build the Neural Network ##
##############################

# Remove previous weights, bias, inputs, etc..
tf.reset_default_graph()

# Inputs
x = neural_net_image_input((32, 32, 3))
y = neural_net_label_input(10)
keep_prob = neural_net_keep_prob_input()

# Model
logits = conv_net(x, keep_prob)

# Name logits Tensor, so that is can be loaded from disk after training
logits = tf.identity(logits, name='logits')

# Loss and Optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=y))
optimizer = tf.train.AdamOptimizer().minimize(cost)

# Accuracy
correct_pred = tf.equal(tf.argmax(logits, 1), tf.argmax(y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32), name='accuracy')

tests.test_conv_net(conv_net)

def train_neural_network(session, optimizer, keep_probability, feature_batch, label_batch):
    """
    Optimize the session on a batch of images and labels
    : session: Current TensorFlow session
    : optimizer: TensorFlow optimizer function
    : keep_probability: keep probability
    : feature_batch: Batch of Numpy image data
    : label_batch: Batch of Numpy label data
    """
    session.run(optimizer, feed_dict={x: feature_batch, y: label_batch, keep_prob: keep_probability})


tests.test_train_nn(train_neural_network)

def print_stats(session, feature_batch, label_batch, cost, accuracy):
    """
    Print information about loss and validation accuracy
    : session: Current TensorFlow session
    : feature_batch: Batch of Numpy image data
    : label_batch: Batch of Numpy label data
    : cost: TensorFlow cost function
    : accuracy: TensorFlow accuracy function
    """
    global valid_features, valid_labels
    validation_accuracy = session.run(
        accuracy,
        feed_dict={
            x: valid_features,
            y: valid_labels,
            keep_prob: 1.0,
        }
    )
    cost = session.run(
        cost,
        feed_dict={
            x: feature_batch,
            y: label_batch,
            keep_prob: 1.0,
        }
    )
    print('Cost = {0} - Validation Accuracy = {1}'.format(cost, validation_accuracy))

    # TODO: Tune Parameters
    epochs = 50
    batch_size = 1024
    keep_probability = 0.5

    print('Checking the Training on a Single Batch...')
    with tf.Session() as sess:
        # Initializing the variables
        sess.run(tf.global_variables_initializer())

        # Training cycle
        for epoch in range(epochs):
            batch_i = 1
            for batch_features, batch_labels in helper.load_preprocess_training_batch(batch_i, batch_size):
                train_neural_network(sess, optimizer, keep_probability, batch_features, batch_labels)
            print('Epoch {:>2}, CIFAR-10 Batch {}:  '.format(epoch + 1, batch_i), end='')
            print_stats(sess, batch_features, batch_labels, cost, accuracy)

            save_model_path = './image_classification'

            print('Training...')
            with tf.Session() as sess:
                # Initializing the variables
                sess.run(tf.global_variables_initializer())

                # Training cycle
                for epoch in range(epochs):
                    # Loop over all batches
                    n_batches = 5
                    for batch_i in range(1, n_batches + 1):
                        for batch_features, batch_labels in helper.load_preprocess_training_batch(batch_i, batch_size):
                            train_neural_network(sess, optimizer, keep_probability, batch_features, batch_labels)
                        print('Epoch {:>2}, CIFAR-10 Batch {}:  '.format(epoch + 1, batch_i), end='')
                        print_stats(sess, batch_features, batch_labels, cost, accuracy)

                # Save Model
                saver = tf.train.Saver()
                save_path = saver.save(sess, save_model_path)

                #% matplotlib
                #inline
                #% config
                #InlineBackend.figure_format = 'retina'

                import tensorflow as tf
                import pickle
                import helper
                import random

                # Set batch size if not already set
                try:
                    if batch_size:
                        pass
                except NameError:
                    batch_size = 64

                save_model_path = './image_classification'
                n_samples = 4
                top_n_predictions = 3

                def test_model():
                    """
                    Test the saved model against the test dataset
                    """

                    test_features, test_labels = pickle.load(open('preprocess_training.p', mode='rb'))
                    loaded_graph = tf.Graph()

                    with tf.Session(graph=loaded_graph) as sess:
                        # Load model
                        loader = tf.train.import_meta_graph(save_model_path + '.meta')
                        loader.restore(sess, save_model_path)

                        # Get Tensors from loaded model
                        loaded_x = loaded_graph.get_tensor_by_name('x:0')
                        loaded_y = loaded_graph.get_tensor_by_name('y:0')
                        loaded_keep_prob = loaded_graph.get_tensor_by_name('keep_prob:0')
                        loaded_logits = loaded_graph.get_tensor_by_name('logits:0')
                        loaded_acc = loaded_graph.get_tensor_by_name('accuracy:0')

                        # Get accuracy in batches for memory limitations
                        test_batch_acc_total = 0
                        test_batch_count = 0

                        for train_feature_batch, train_label_batch in helper.batch_features_labels(test_features,
                                                                                                   test_labels,
                                                                                                   batch_size):
                            test_batch_acc_total += sess.run(
                                loaded_acc,
                                feed_dict={loaded_x: train_feature_batch, loaded_y: train_label_batch,
                                           loaded_keep_prob: 1.0})
                            test_batch_count += 1

                        print('Testing Accuracy: {}\n'.format(test_batch_acc_total / test_batch_count))

                        # Print Random Samples
                        random_test_features, random_test_labels = tuple(
                            zip(*random.sample(list(zip(test_features, test_labels)), n_samples)))
                        random_test_predictions = sess.run(
                            tf.nn.top_k(tf.nn.softmax(loaded_logits), top_n_predictions),
                            feed_dict={loaded_x: random_test_features, loaded_y: random_test_labels,
                                       loaded_keep_prob: 1.0})
                        helper.display_image_predictions(random_test_features, random_test_labels,
                                                         random_test_predictions)

                test_model()
