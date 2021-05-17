from neural_net import nst_model

def background_task(base_image, style_reference_image, combination_image, result_photo_filename, img_nrows, img_ncols):
    def callback(progress):
        global model_progress
        model_progress = progress
        print(progress)
        
        
                
    model = nst_model(base_image, style_reference_image, combination_image, result_photo_filename, img_nrows, img_ncols)
    print('started function')
    fname = model.train_net(5, callback)
    return fname