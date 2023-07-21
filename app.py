from flask import Flask, request,render_template, redirect, url_for,jsonify, abort
import os
import zipfile
import uuid
from werkzeug.utils import secure_filename
import shutil
import sql_tunner
import store
import atexit
import sqlparse

app = Flask(__name__)
tunner = sql_tunner.SqlTunner()
db = store.Store()
atexit.register(db.close)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/tune', methods=['POST'])
def tune():
    original_sql = request.form['original_sql']
    schemas = request.form['schemas']
    stats_info = request.form['stats_info']
    new_schemas = None if len(schemas) > 4000 else schemas
    new_stats_info = None if len(stats_info) > 4000 else stats_info
    gpt_version = request.form['gpt_version']

    try:
        result = tunner.tune(gpt_version, original_sql, new_schemas, new_stats_info)
        tuned_sql = result['tuned_sql']
        tuned_sql = sqlparse.format(tuned_sql, reindent=True, keyword_case='upper')
        id = db.insert_record(original_sql, schemas, stats_info, tuned_sql, result['what_changed'], result['index_suggestion'], gpt_version)

        return jsonify({
            'tuned_sql': tuned_sql,
            'what_changed': result['what_changed'],
            'index_suggestion': result['index_suggestion'],
            'id': id,
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

@app.route('/history/first', methods=['GET'])
def first():
    id = db.get_first()

    return redirect(url_for('history', id=id))

@app.route('/history/next/<int:id>', methods=['GET'])
def next(id):
    id = db.get_next(id)

    if id:
        return jsonify({
            'id': id,
        })
    else:
        abort(404)

@app.route('/history/prev/<int:id>', methods=['GET'])
def prev(id):
    id = db.get_prev(id)

    if id:
        return jsonify({
            'id': id,
        })
    else:
        abort(404)

@app.route('/history/<int:id>', methods=['GET'])
def history(id):
    record = db.get_record_by_id(id)

    if not record:
        abort(404)

    return render_template('history.html', record=record)

@app.route('/correct', methods=['POST'])
def correct():
    id = request.form['id']
    correct = request.form['correct']

    db.update_correct_field(id, correct)

    return jsonify({
        'id': id,
        'correct': correct,
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
    app.run(debug=True, host = '0.0.0.0', port=5001)
