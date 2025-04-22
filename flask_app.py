import os
import shutil
from flask import Flask, render_template, request, jsonify

txt_folder = os.path.join(os.getcwd(), 'txt_files')
if os.path.exists(txt_folder):
    shutil.rmtree(txt_folder)
os.makedirs(txt_folder)
print(f"Folder where the txt files will be stored: {txt_folder}")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template(
        'index.html',
    )

@app.route('/save_fields', methods=['POST'])
def save_fields():
    data = request.json
    if not 'emailContent' in data.keys():
        return jsonify({'message': 'Missing email content'}), 500
    email_content = data['emailContent']
    if not 'buyers' in data.keys():
        return jsonify({'message': 'Missing buyers'}), 500
    buyers_data = data['buyers']

    try:
        email_txt_file = os.path.join(txt_folder, 'email_content.txt')
        with open(email_txt_file, 'w') as f:
            f.write(email_content)
        
        for buyer_data in buyers_data:
            buyer_name = buyer_data['buyer']
            buyer_cards = buyer_data['content']
            buyer_txt_file = os.path.join(txt_folder, f'{buyer_name}.txt')
            with open(buyer_txt_file, 'w') as f:
                f.write(buyer_cards)

        return jsonify({'message': 'Fields saved successfully!'}), 200
    except Exception as e:
        return jsonify({'message': f'Error writing to file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)