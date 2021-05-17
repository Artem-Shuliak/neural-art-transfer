from neural_net import nst_model

def background_task(base_photo_name, base_photo_url, style_photo_name, style_photo_url, result_name):
    def callback(progress):
        global model_progress
        model_progress = progress
        print(progress)
                
    model = nst_model(base_photo_name, base_photo_url, style_photo_name, style_photo_url, result_name)
    print('started function')
    fname = model.train_net(5, callback)
    return fname