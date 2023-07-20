from flask import Flask, request,render_template, redirect, url_for,jsonify
import os
import zipfile
import uuid
from werkzeug.utils import secure_filename
import shutil
import sql_tunner

app = Flask(__name__)
tunner = sql_tunner.SqlTunner()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/tune', methods=['POST'])
def tune():
    original_sql = request.form['original_sql']
    schemas = request.form['schemas']
    if len(schemas) > 4000:
        schemas = None
    stats_info = request.form['stats_info']
    if len(stats_info) > 4000:
        stats_info = None

    try:
        result = tunner.tune(original_sql, schemas, stats_info)

        return jsonify({
            'tuned_sql': result['tuned_sql'],
            'what_changed': result['what_changed'],
            'index_suggestion': result['index_suggestion'],
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
        })

@app.route('/parse', methods=['POST'])
def parse():
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'error': 'No selected file',
        })
    filename = secure_filename(file.filename)
    unique_filename = str(uuid.uuid4()) + '-' + filename

    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    file.save(os.path.join('uploads', unique_filename))
    result = process_zip(os.path.join('uploads', unique_filename))

    orginal_sql, schemas, stats_info = result
    return jsonify({
        'original_sql': orginal_sql,
        'schemas': schemas,
        'stats_info': stats_info,
    })


def process_zip(zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        extracted_folder = zip_file_path.replace('.zip', '')
        zip_ref.extractall(extracted_folder)

    if os.path.exists(os.path.join(extracted_folder, 'sqls.sql')):
        with open(os.path.join(extracted_folder, 'sqls.sql')) as file:
            original_sql = file.read()
    else:
        with open(os.path.join(extracted_folder, 'sql','sql0.sql')) as file:
            original_sql = file.read()
    schemas = read_files_in_folder(os.path.join(extracted_folder, 'schema'))
    statics_info = read_files_in_folder(os.path.join(extracted_folder, 'stats'))

    os.remove(zip_file_path)
    shutil.rmtree(extracted_folder)

    return original_sql, schemas, statics_info

def read_files_in_folder(folder_path):
    combined_content = ""

    # Iterate through all files in the folder
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            # Open each file and read its content
            with open(file_path, "r") as file:
                file_content = file.read()

            # Append the file content to the combined_content string
            combined_content += file_content + "\n"

    return combined_content

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'zip'

if __name__ == '__main__':
    app.run(debug=True)
