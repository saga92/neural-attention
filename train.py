"""
training script
"""

from batch import Batcher
from model import BaselineLSTM
import tensorflow as tf
from tqdm import tqdm
import os

N_EPOCH = 100
SAVE_DIR = './models'

def train():
    train_batch = Batcher(data_type = 'train')
    dev_batch = Batcher(data_type='dev')

    # baseline graph
    tf.reset_default_graph()
    baseline = BaselineLSTM()
    saver = tf.train.Saver()
    best_val_acc = 0
    # record training loss & accuracy
    train_losses = []
    train_accuracies = []

    init = tf.global_variables_initializer()

    with tf.Session() as sess:
        sess.run(init)
        for ep in tqdm(range(N_EPOCH)):
            tr_loss, tr_acc = 0, 0

            for itr in tqdm(range(train_batch.n_batches)):
                batch = train_batch.next_batch()
                feed_dict = {baseline.premise_inputs: batch["premise"],
                              baseline.p_input_lengths: batch["premise_length"],
                              baseline.hypothesis_inputs: batch["hypothesis"],
                              baseline.h_input_lengths: batch["hypothesis_length"],
                              baseline.output: batch["target"]}
                fc1, loss, acc, _ = sess.run([baseline.hypothesis_embed, baseline.loss, baseline.accuracy, baseline.opt], feed_dict=feed_dict)
                tr_loss += loss
                tr_acc += acc

            train_losses.append(tr_loss / train_batch.n_batches)
            train_accuracies.append(tr_acc / train_batch.n_batches)

            # check validation accuracy every 10 epochs
            if ep % 2 == 0:
                val_acc = 0

                for itr in range(dev_batch.n_batches):
                    batch = dev_batch.next_batch()
                    feed_dict = {baseline.premise_inputs: batch["premise"],
                                  baseline.p_input_lengths: batch["premise_length"],
                                  baseline.hypothesis_inputs: batch["hypothesis"],
                                  baseline.h_input_lengths: batch["hypothesis_length"],
                                  baseline.output: batch["target"]}
                    val_acc += sess.run(baseline.accuracy, feed_dict=feed_dict)
                val_acc = val_acc / dev_batch.n_batches

                print('epoch {:3d}, loss={:.2f}'.format(ep, tr_loss / dev_batch.n_batches))
                print('Train EM: {:.2f}, Validation EM: {:.2f}'.format(tr_acc / dev_batch.n_batches, val_acc))

                # save model
                if val_acc >= best_val_acc:
                    print('Validation accuracy increased. Saving model.')
                    saver.save(sess, os.path.join(SAVE_DIR, 'baseline.ckpt'))
                    best_val_acc = val_acc
                else:
                    print('Validation accuracy decreased. Restoring model.')
                    saver.restore(sess, os.path.join(SAVE_DIR, 'baseline.ckpt'))
                    train_batch.build_batch()
                    dev_batch.build_batch()

        print('Training complete.')
        print("Best Validation EM: {:.2f}".format(best_val_acc))


if __name__ == '__main__':
    train()