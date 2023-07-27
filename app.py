from flask import Flask, request,render_template, redirect, url_for,jsonify, abort
import os
import zipfile
import uuid
from werkzeug.utils import secure_filename
import shutil
import sql_tunner
import store
import sqlparse

app = Flask(__name__)
tunner = sql_tunner.SqlTunner()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', prompt=tunner.get_prompt())

@app.route('/tune', methods=['POST'])
def tune():
    original_sql = request.form['original_sql']
    schemas = request.form['schemas']
    execution_plan = request.form['execution_plan']
    gpt_version = request.form['gpt_version']
    prompt = request.form['prompt']
    if not prompt:
        prompt = tunner.get_prompt()

    try:
        result, input, output = tunner.tune(gpt_version, prompt, original_sql, schemas, execution_plan)
        tuned_sql = result['tuned_sql']
        tuned_sql = sqlparse.format(tuned_sql, reindent=True, keyword_case='upper')
        db = store.Store()
        id = db.insert_record(original_sql, schemas, execution_plan, tuned_sql, result['what_changed'], result['index_suggestion'], gpt_version, input, output)
        db.close()

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

    orginal_sql, schemas, execution_plan = result
    return jsonify({
        'original_sql': orginal_sql,
        'schemas': schemas,
        'execution_plan': execution_plan,
    })

@app.route('/histories', methods=['GET'])
def histories():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    db = store.Store()
    histories, count = db.get_histories_with_page(page, per_page)
    db.close()
    total_pages = (count - 1) // per_page + 1

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    return render_template('histories.html', histories=histories, page=page, total_pages=total_pages, total_items=count)

@app.route('/histories/delete/<int:id>', methods=['POST'])
def delete_history(id):
    db = store.Store()
    db.delete_history(id)
    db.close()

    return {}, 200


@app.route('/history/<int:id>', methods=['GET'])
def history(id):
    db = store.Store()
    record = db.get_record_by_id(id)
    db.close()

    if not record:
        abort(404)

    return render_template('history.html', record=record)

@app.route('/correct', methods=['POST'])
def correct():
    id = request.form['id']
    correct = request.form['correct']

    db = store.Store()
    db.update_correct_field(id, correct)
    db.close()

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
    execution_plan = read_files_in_folder(os.path.join(extracted_folder, 'explain'))

    os.remove(zip_file_path)
    shutil.rmtree(extracted_folder)

    return original_sql, schemas, execution_plan

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
