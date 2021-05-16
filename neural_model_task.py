from neural_net import nst_model

def background_task(base_photo_filepath, style_photo_filepath, result_photo_filename):
    def callback(progress):
        global model_progress
        model_progress = progress
        print(progress)
                
    model = nst_model(base_photo_filepath, style_photo_filepath, result_photo_filename)
    print('started function')
    fname = model.train_net(5, callback)
    return fname