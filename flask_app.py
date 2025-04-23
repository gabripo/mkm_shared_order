import os
import shutil
from flask import Flask, render_template, request, jsonify
from src.parse_gmail_mkm import parse_mail_txt

txt_folder = os.path.join(os.getcwd(), 'txt_files')
if os.path.exists(txt_folder):
    shutil.rmtree(txt_folder)
os.makedirs(txt_folder)
print(f"Folder where the txt files will be stored: {txt_folder}")

email_content_txt_file = os.path.join(txt_folder, 'email_content.txt')

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
        with open(email_content_txt_file, 'w') as f:
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
    
@app.route('/analyze_email', methods=['POST'])
def analyze_email():
    if not os.path.exists(email_content_txt_file):
        return jsonify({'message': 'Email content file not found'}), 500
    
    shipment_details, costs, cards_list, simple_cards_list = \
        parse_mail_txt(email_content_txt_file)
    print(f"Content of e-mail in {email_content_txt_file} analyzed")
    return jsonify({
        'shipmentDetails': shipment_details,
        'costs': costs,
        'cardsList': cards_list,
        'simpleCardsList': simple_cards_list
    }), 200

if __name__ == '__main__':
    app.run(debug=True)