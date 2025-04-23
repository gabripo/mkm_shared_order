import os
import shutil
from flask import Flask, render_template, request, jsonify
from src.mkm_order_parser import find_shipping_by_list, list_check, total_cost_by_list
from src.read_cards import read_card_list
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

@app.route('/analyze_buyers', methods=['POST'])
def analyze_buyers():
    if not os.path.exists(txt_folder):
        return jsonify({'message': 'Buyers folder not found'}), 500
    
    data = request.json
    if not 'simpleCardsList' in data.keys():
        return jsonify({'message': 'Missing simple cards list'}), 500
    simple_cards_list = data['simpleCardsList']
    if not 'shipmentDetails' in data.keys():
        return jsonify({'message': 'Missing shipment details'}), 500
    shipment_details = data['shipmentDetails']

    not_found_cards = {}
    cards_per_buyer = {}
    costs_per_buyer = {}
    for filename in os.listdir(txt_folder):
        if filename.endswith('.txt') and filename != os.path.basename(email_content_txt_file):
            buyer_name = filename[:-4]
            buyer_txt_file = os.path.join(txt_folder, filename)
            buyer_list = read_card_list(buyer_txt_file)
            list_check(simple_cards_list, buyer_list, buyer_name, not_found_cards)

            involved_cards = find_shipping_by_list(shipment_details, buyer_list, buyer_name)
            cards_per_buyer[buyer_name] = involved_cards

            involved_costs = total_cost_by_list(shipment_details, involved_cards, buyer_name)
            costs_per_buyer[buyer_name] = involved_costs
    
    spare_cards = find_shipping_by_list(shipment_details, simple_cards_list) # simple_cards_list is reduced after each iteration, here the remaining cards are the spare ones
    
    return jsonify({
        'notFoundCards': not_found_cards,
        'cardsPerBuyer': cards_per_buyer,
        'costsPerBuyer': costs_per_buyer,
        'spareCards': spare_cards,
        }), 200

if __name__ == '__main__':
    app.run(debug=True)