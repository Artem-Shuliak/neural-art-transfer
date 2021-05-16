from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os 
from werkzeug.utils import secure_filename
from rq import Queue
from worker import r
from neural_model_task import background_task

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
    
    for file in os.scandir('image_uploads/'):
        if file.name != '.gitkeep':
            os.remove(file)

    for file in os.scandir('static/result_images/'):
        if file.name != '.gitkeep':
            os.remove(file)
            
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
   
        if allowed_file(base_photo.filename) and allowed_file(style_photo.filename):
            
            base_photo_filename = secure_filename(base_photo.filename) 
            base_photo.save(os.path.join(app.config['upload_folder'], base_photo_filename))
            base_photo_filepath = os.path.join(app.config['upload_folder'], base_photo_filename)
            result_photo_filename = base_photo_filename
            
            style_photo_filename = secure_filename(style_photo.filename) 
            style_photo.save(os.path.join(app.config['upload_folder'], style_photo_filename))
            style_photo_filepath = os.path.join(app.config['upload_folder'], style_photo_filename)
            job = q.enqueue(background_task, base_photo_filepath, style_photo_filepath, result_photo_filename)
            global job_id
            job_id = job.id
            print(job_id)
            return jsonify(reponse='sucess', job_id=job_id) 

    return jsonify(reponse='no upload')
        
if __name__ == '__main__':
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)
    
    
    