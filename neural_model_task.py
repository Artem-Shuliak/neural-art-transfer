from neural_net import nst_model

def background_task(base_image_path, style_reference_image_path, result_photo_filename):
    def callback(progress):
        global model_progress
        model_progress = progress
        print(progress)
        
        
                
    model = nst_model(base_image_path, style_reference_image_path, result_photo_filename)
    print('started function')
    fname = model.train_net(5, callback)
    return fname