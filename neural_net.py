import tensorflow as tf
from tensorflow import keras 
from tensorflow.keras.applications import vgg19
import numpy as np

class nst_model:   
    
    def __init__(self, base_image, style_image, result_name):
        self.base_image_path = base_image
        self.style_reference_image_path = style_image
        self.result_name = result_name
        self.setup_dimensions()
        self.make_model()
        
    result_prefix = "image_generated"
    # Weights of the different loss components
    total_variation_weight = 1e-6
    style_weight = 1e-6
    content_weight = 2.5e-8
    
    def setup_dimensions(self):
        # Dimensions of the generated picture.
        self.width, self.height = keras.preprocessing.image.load_img(self.base_image_path).size
        self.img_nrows = 400
        self.img_ncols = int(self.width * self.img_nrows / self.height)
    
    def preprocess_image(self, image_path):
        # Util function to open, resize and format pictures into appropriate tensors
        img = keras.preprocessing.image.load_img(image_path, target_size=(self.img_nrows, self.img_ncols))
        img = keras.preprocessing.image.img_to_array(img)
        img = np.expand_dims(img, axis=0)
        img = vgg19.preprocess_input(img)
        return tf.convert_to_tensor(img)

    def deprocess_image(self, x):
        # Util function to convert a tensor into a valid image
        x = x.reshape((self.img_nrows, self.img_ncols, 3))
        # Remove zero-center by mean pixel
        x[:, :, 0] += 103.939
        x[:, :, 1] += 116.779
        x[:, :, 2] += 123.68
        # 'BGR'->'RGB'
        x = x[:, :, ::-1]
        x = np.clip(x, 0, 255).astype("uint8")
        return x
    
    
    # The gram matrix of an image tensor (feature-wise outer product)
    def gram_matrix(self, x):
        x = tf.transpose(x, (2, 0, 1))
        features = tf.reshape(x, (tf.shape(x)[0], -1))
        gram = tf.matmul(features, tf.transpose(features))
        return gram
    
    # The "style loss" is designed to maintain the style of the reference image in the generated image.
    # It is based on the gram matrices (which capture style) of feature maps from the style reference image and from the generated image 
    
    def style_loss(self, style, combination):
        S = self.gram_matrix(style)
        C = self.gram_matrix(combination)
        channels = 3
        size = self.img_nrows * self.img_ncols
        return tf.reduce_sum(tf.square(S - C)) / (4.0 * (channels ** 2) * (size ** 2))
    
    # An auxiliary loss function designed to maintain the "content" of the base image in the generated image
    
    def content_loss(self, base, combination):
        return tf.reduce_sum(tf.square(combination - base))
    
    # The 3rd loss function, total variation loss, designed to keep the generated image locally coherent 
    
    def total_variation_loss(self, x):
        a = tf.square(x[:, : self.img_nrows - 1, : self.img_ncols - 1, :] - x[:, 1:, : self.img_ncols - 1, :])
        b = tf.square(x[:, : self.img_nrows - 1, : self.img_ncols - 1, :] - x[:, : self.img_nrows - 1, 1:, :])
        return tf.reduce_sum(tf.pow(a + b, 1.25))

    def make_model(self):
        # Build a VGG19 model loaded with pre-trained ImageNet weights
        self.model = vgg19.VGG19(weights="imagenet", include_top=False)

        # Get the symbolic outputs of each "key" layer (we gave them unique names).
        self.outputs_dict = dict([(layer.name, layer.output) for layer in self.model.layers])

        # Set up a model that returns the activation values for every layer in VGG19 (as a dict).
        self.feature_extractor = keras.Model(inputs=self.model.inputs, outputs=self.outputs_dict)
    
        # List of layers to use for the style loss.
        self.style_layer_names = [
            "block1_conv1",
            "block2_conv1",
            "block3_conv1",
            "block4_conv1",
            "block5_conv1",
         ]
    
        # The layer to use for the content loss.
        self.content_layer_name = "block5_conv2"
        
        self.optimizer = keras.optimizers.SGD(keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=100.0, decay_steps=100,decay_rate=0.96))

    def compute_loss(self, combination_image, base_image, style_reference_image):
        input_tensor = tf.concat([base_image, style_reference_image, combination_image], axis=0)
        features = self.feature_extractor(input_tensor)
        
        # Initialize the loss
        loss = tf.zeros(shape=())

        # Add content loss
        layer_features = features[self.content_layer_name]
        base_image_features = layer_features[0, :, :, :]
        combination_features = layer_features[2, :, :, :]
        loss = loss + self.content_weight * self.content_loss(base_image_features, combination_features)
        
        # Add style loss
        for layer_name in self.style_layer_names:
            layer_features = features[layer_name]
            style_reference_features = layer_features[1, :, :, :]
            combination_features = layer_features[2, :, :, :]
            sl = self.style_loss(style_reference_features, combination_features)
            loss += (self.style_weight / len(self.style_layer_names)) * sl

        # Add total variation loss
        loss += self.total_variation_weight * self.total_variation_loss(combination_image)
        return loss
            
    @tf.function
    def compute_loss_and_grads(self, combination_image, base_image, style_reference_image):
        with tf.GradientTape() as tape:
            loss = self.compute_loss(combination_image, base_image, style_reference_image)
        grads = tape.gradient(loss, combination_image)
        return loss, grads    

    def train_net(self, iterations, callback):
        self.make_model()
        base_image = self.preprocess_image(self.base_image_path)
        style_reference_image = self.preprocess_image(self.style_reference_image_path)
        combination_image = tf.Variable(self.preprocess_image(self.base_image_path))

        for i in range(1, iterations + 1):
            loss, grads = self.compute_loss_and_grads(combination_image, base_image, style_reference_image) 
            self.optimizer.apply_gradients([(grads, combination_image)])
            print("Iteration %d: loss=%.2f" % (i, loss))
            
            progress = (i / iterations) * 100
            callback(progress)
            
            if i == iterations:
                print('saved')
                img = self.deprocess_image(combination_image.numpy())
                dropped_name = self.result_name.rsplit( ".", 1 )[0]
                fname = "static/result_images/" + dropped_name + '.png'
                print(fname)
                keras.preprocessing.image.save_img(fname, img)
                return fname
    
    