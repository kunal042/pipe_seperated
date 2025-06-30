from flask import Flask, request, send_file, jsonify, send_from_directory
from asgiref.wsgi import WsgiToAsgi
import pandas as pd
import os
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
from flask_cors import CORS
# from utils.excel1 import Process_excel_to_csv
from utils.excel2 import ExcelToCSVConverter
import threading
import time
import logging


app = Flask(__name__)
CORS(app)


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Define an explicit folder within your app
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')  # Output folder

ALLOW_EXTENSIONS = {'xlsx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Create the directory if it doesn't exist

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# ExcelToCSVConverter.process_excel_to_csv()

# print("Upload folder:", UPLOAD_FOLDER)
# print("Output folder:", OUTPUT_FOLDER)

# print("Allowed Extension:", ALLOW_EXTENSIONS)



def allowed_file(filename):
    return "." in filename and  filename.rsplit('.',1)[1].lower() in ALLOW_EXTENSIONS



# Set up basic logging
logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

@app.route('/login' )
def login():
    logger.info("Welcome to flask!!")
    return "Check your server logs for the greeting!", 200


@app.route('/upload', methods=['POST'])
def upload_file():
    Process = ExcelToCSVConverter()

    if "file" not in request.files:
        return jsonify({'error' : 'Not File Found'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No Selected File'}), 400
    
    if file and allowed_file(file.filename):
        # Secure the file
        filename = secure_filename(file.filename)
        # print("File Name :",filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(input_path)

        # Create output filename with timestamp

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{filename}_Pip_Sep_{current_time}.csv"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)  # Save to output folder


        success, output_file, input_path = Process.process_excel_to_csv(input_path, output_path)

        print("sucesss" ,success)
        print("output_file", output_file)

        try :
            os.remove(input_path)
        except:
            pass

        if success :
            return jsonify({
                'success' : True,
                'output' : output_file,
                'input' : input_path,
                'message': "file Converted Sucsessfully!!"

            })
        else :
            return jsonify({'error' : output_file}), 500
    else :
        return jsonify({'error' : 'Invalid file type. Only .xlsx files are allowed'}), 400


 


@app.route('/cleanup', methods=['DELETE'])
def manual_cleanup():
    now = time.time()
    cutoff = now - 0.5 * 60  # 30 minutes in seconds
    deleted_files = []

    for folder in [ OUTPUT_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                if os.path.getmtime(file_path) < cutoff:
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                    except Exception as e:
                        return jsonify({'error': f"Error deleting {file_path}: {str(e)}"}), 500

    return jsonify({
        'success': True,
        'deleted_files': deleted_files,
        'message': f"Cleanup completed. {len(deleted_files)} files deleted."
    })



# Wrap Flask app with ASGI adapter
asgi_app = WsgiToAsgi(app)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)