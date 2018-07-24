# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging

import numpy as np
import tensorflow as tf

logger = logging.getLogger('app')


def load_graph(model_file):
  graph = tf.Graph()
  graph_def = tf.GraphDef()

  with open(model_file, "rb") as f:
    graph_def.ParseFromString(f.read())
  with graph.as_default():
    tf.import_graph_def(graph_def)

  return graph


def read_tensor_from_image_file(file_names,
                                input_height=299,
                                input_width=299,
                                input_mean=0,
                                input_std=255):
  input_name = "file_reader"
  output_name = "normalized"

  resized_images = []
  for file_name in file_names:
    file_reader = tf.read_file(file_name, input_name)
    if file_name.endswith(".png"):
      image_reader = tf.image.decode_png(
          file_reader, channels=3, name="png_reader")
    elif file_name.endswith(".gif"):
      image_reader = tf.squeeze(
          tf.image.decode_gif(file_reader, name="gif_reader"))
    elif file_name.endswith(".bmp"):
      image_reader = tf.image.decode_bmp(file_reader, name="bmp_reader")
    else:
      image_reader = tf.image.decode_jpeg(
          file_reader, channels=3, name="jpeg_reader")

    float_caster = tf.cast(image_reader, tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0)
    resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])

    resized_images.append(resized[0])

  resized_images = tf.stack(resized_images)
  normalized = tf.divide(tf.subtract(resized_images, [input_mean]), [input_std])
  sess = tf.Session()
  result = sess.run(normalized)

  return result


def load_labels(label_file):
  label = []
  proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
  for l in proto_as_ascii_lines:
    label.append(l.rstrip())
  return label


def classify_images(file_names):
  model_file = 'out/graph.pb'
  label_file = 'out/labels.txt'
  input_layer = 'Placeholder'
  output_layer = 'final_result'

  input_width, input_height, input_mean, input_std = 299, 299, 0, 255

  logger.info('Loading graph...')
  graph = load_graph(model_file)
  logger.info('Reading tensors from images')
  t = read_tensor_from_image_file(
      file_names,
      input_height=input_height,
      input_width=input_width,
      input_mean=input_mean,
      input_std=input_std)

  input_name = "import/" + input_layer
  output_name = "import/" + output_layer
  input_operation = graph.get_operation_by_name(input_name)
  output_operation = graph.get_operation_by_name(output_name)

  with tf.Session(graph=graph) as sess:
    logger.info('Classifying...')
    batch_results = sess.run(output_operation.outputs[0], {
        input_operation.outputs[0]: t
    })

  batch_size = len(batch_results)

  labels = load_labels(label_file)
  indices = batch_results.argsort()

  labels = np.repeat([labels], batch_size, axis=0)
  sorted_labels = labels[:, indices][np.eye(batch_size, batch_size, dtype=bool)][:, ::-1]
  sorted_batch_results = batch_results[:, indices][np.eye(batch_size, batch_size, dtype=bool)][:, ::-1]
  zipped_result = zip(file_names, sorted_labels, sorted_batch_results)
  return [e for e in zipped_result]


if __name__ == "__main__":
  file_names = ['resources/1.jpg', 'resources/14.jpg']
  results = classify_images(file_names)
  for result in results:
    print(result)
