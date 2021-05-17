import tensorflow as tf
from tensorflow import keras 
from tensorflow.keras.applications import vgg19
import numpy as np
from background_task import background_task

global img_nrows
global img_ncols

def pre_proces(q, base_image_path, style_reference_image_path, result_photo_filename):
    
    global img_nrows
    global img_ncols
    width, height = keras.preprocessing.image.load_img(base_image_path).size
    img_nrows = 400
    img_ncols = int(width * img_nrows / height)
    
    
    base_image = preprocess_image(base_image_path)
    style_reference_image = preprocess_image(style_reference_image_path)
    combination_image = tf.Variable(preprocess_image(base_image_path))
    
    
    job = q.enqueue(background_task, base_image, style_reference_image, combination_image, result_photo_filename, img_nrows, img_ncols)
    job_id = job.id
    print(job_id)
    return job_id
    
def preprocess_image(image_path):
    global img_nrows
    global img_ncols

    # Util function to open, resize and format pictures into appropriate tensors
    img = keras.preprocessing.image.load_img(image_path, target_size=(img_nrows, img_ncols))
    img = keras.preprocessing.image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = vgg19.preprocess_input(img)
    return tf.convert_to_tensor(img)
    
    