import os
import secrets
from flask import Flask, render_template, request, jsonify
from src.flask_helpers import determine_output_folder, EMAIL_CONTENT_TXT_FILE
from src.mkm_order_parser import find_shipping_by_list, list_check, total_cost_by_list
from src.read_cards import read_card_list
from src.parse_gmail_mkm import parse_mail_txt

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) # needed for sessions management

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
        txt_folder = determine_output_folder(clear_folder=True)
        email_content_txt_file = os.path.join(txt_folder, EMAIL_CONTENT_TXT_FILE)
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
    txt_folder = determine_output_folder()
    email_content_txt_file = os.path.join(txt_folder, EMAIL_CONTENT_TXT_FILE)
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
    txt_folder = determine_output_folder()
    email_content_txt_file = os.path.join(txt_folder, EMAIL_CONTENT_TXT_FILE)
    if not os.path.exists(txt_folder):
        return jsonify({'message': 'Buyers folder not found'}), 500
    
    data = request.json
    if not 'simpleCardsList' in data.keys():
        return jsonify({'message': 'Missing simple cards list'}), 500
    simple_cards_list = data['simpleCardsList']
    if not 'shipmentDetails' in data.keys():
        return jsonify({'message': 'Missing shipment details'}), 500
    shipment_details = data['shipmentDetails']
    if not 'totalCosts' in data.keys() or not 'totalCost' in data['totalCosts']:
        return jsonify({'message': 'Missing total costs'}), 500
    total_cost_from_email = data['totalCosts']['totalCost']
    if not 'buyers' in data.keys():
        return jsonify({'message': 'Missing buyers'}), 500
    buyers_names = [buyer_data['buyer'] for buyer_data in data['buyers']]

    buyers_txt_files = [
        filename
        for filename in os.listdir(txt_folder)
        if filename.endswith('.txt')
        and
        filename != os.path.basename(email_content_txt_file)
        and
        filename[:-4] in set(buyers_names) # remove the .txt extension with the :-4
    ]
    buyers_txt_files.sort(key=lambda name: buyers_names.index(name[:-4])) # preserve the same order of the buyers in the input form
    buyers_txt_files[:] = [os.path.join(txt_folder, filename) for filename in buyers_txt_files] # add absolute path to the file names

    not_found_cards = {}
    cards_per_buyer = {}
    costs_per_buyer = {}
    for buyer_name, buyer_txt_file in zip(buyers_names, buyers_txt_files):
        buyer_list = read_card_list(buyer_txt_file)
        simple_cards_list = list_check(simple_cards_list, buyer_list, buyer_name, not_found_cards)

        involved_cards = find_shipping_by_list(shipment_details, buyer_list, buyer_name)
        cards_per_buyer[buyer_name] = involved_cards

        involved_costs = total_cost_by_list(shipment_details, involved_cards, buyer_name)
        costs_per_buyer[buyer_name] = involved_costs
    
    spare_cards = find_shipping_by_list(shipment_details, simple_cards_list) # simple_cards_list is reduced after each iteration, here the remaining cards are the spare ones
    if spare_cards:
        costs_per_buyer["spare cards"] =  total_cost_by_list(shipment_details, spare_cards, "spare cards")

    total_cost_computed = round(sum(costs_per_buyer.values()), 2) # spare cards are included in the total cost, if any
    computation_error = abs(total_cost_computed - total_cost_from_email)
    
    return jsonify({
        'notFoundCards': not_found_cards,
        'cardsPerBuyer': cards_per_buyer,
        'costsPerBuyer': costs_per_buyer,
        'spareCards': spare_cards,
        'computationError': computation_error,
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)