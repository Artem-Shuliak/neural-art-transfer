from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os 
from werkzeug.utils import secure_filename
from rq import Queue
from worker import r
from neural_model_task import background_task
from PIL import Image
from tensorflow import keras 
import boto3

s3 = boto3.client('s3')
bucket_name = 'neural-art-transfer-image-uploads'


#where our images will go
upload_folder = 'image_uploads'
#what filetypes are allowed
allowed_extensions = {'png', 'jpg', 'jpeg'}

#create our ap
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
q = Queue(connection=r)

#load files to our upload folder
app.config['upload_folder'] = upload_folder

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

model_progress = 0
global job_id

@app.route('/', methods = ["POST", "GET"])
def home():
    
    # for file in os.scandir('image_uploads/'):
    #     if file.name != '.gitkeep':
    #         os.remove(file)

    # for file in os.scandir('static/result_images/'):
    #     if file.name != '.gitkeep':
    #         os.remove(file)
            
    return render_template('home.html')


@app.route('/progress')
def progres():
    
    # print(model_progress)
    global job_id 
    print(job_id)
    
    response = q.fetch_job(job_id)
    status = response.get_status
    status_string = f'{status}'
    
    if response.result == None: 
        return jsonify(response=response.result, status=status_string)
    
    if response.result != None:
        session['result_image'] = response.result
        return jsonify(response=response.result, redirect=url_for("result"), status=status_string)
     
     
@app.route('/result')
def result():
    response_image = session['result_image']
    return render_template('result.html', image_name = response_image)


@app.route('/upload', methods = ["POST", "GET"])
def upload():
    
    if request.method == "POST":
        
        base_photo = request.files['base_photo']
        style_photo = request.files['style_photo']
        
        base_photo_name = base_photo.filename
        style_photo_name = style_photo.filename
        
        if allowed_file(base_photo.filename) and allowed_file(style_photo.filename):
                
            s3.upload_fileobj(base_photo, bucket_name, base_photo_name, ExtraArgs={
                'ACL':'public-read', 
                'ContentType': base_photo.content_type
                }
            )
            
            s3.upload_fileobj(style_photo, bucket_name, style_photo_name, ExtraArgs={
                'ACL':'public-read',
                'ContentType': style_photo.content_type
                }
            )
            
            result_photo_filename = base_photo_name
            
            base_photo_url = f"http://{bucket_name}.s3.amazonaws.com/{base_photo_name}"
            style_photo_url = f"http://{bucket_name}.s3.amazonaws.com/{style_photo_name}"
           
            base_image_path = keras.utils.get_file(base_photo_name, base_photo_url)
            style_reference_image_path = keras.utils.get_file(style_photo_name, style_photo_url)
   
            job = q.enqueue(background_task, base_image_path, style_reference_image_path, result_photo_filename)
            global job_id
            job_id = job.id
            print(job_id)
            return jsonify(reponse='sucess') 

    return jsonify(reponse='no upload')
        
if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)
    
    
    