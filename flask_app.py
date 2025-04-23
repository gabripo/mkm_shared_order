import os
import shutil
import uuid
import tempfile
from flask import Flask, render_template, request, jsonify, session
from src.mkm_order_parser import find_shipping_by_list, list_check, total_cost_by_list
from src.read_cards import read_card_list
from src.parse_gmail_mkm import parse_mail_txt

def determine_flask_session_id():
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    return session_id

def determine_output_folder() -> str:
    if os.getenv("APP_IN_DOCKER") == "Yes":
        print("DOCKER EXECUTION DETECTED")
        session_id = determine_flask_session_id()
        output_dir = os.path.join(tempfile.gettempdir(), session_id)
        print(f"Txt files directory for session id {session_id} set as: {output_dir}")
    else:
        output_dir = os.path.abspath(os.path.join(os.getcwd(), 'txt_files'))
        print(f"Txt files directory set as: {output_dir}")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    return output_dir

txt_folder = determine_output_folder()
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
    if not 'totalCosts' in data.keys() or not 'totalCost' in data['totalCosts']:
        return jsonify({'message': 'Missing total costs'}), 500
    total_cost_from_email = data['totalCosts']['totalCost']
    if not 'buyers' in data.keys():
        return jsonify({'message': 'Missing buyers'}), 500
    buyers_names = {buyer_data['buyer'] for buyer_data in data['buyers']}

    not_found_cards = {}
    cards_per_buyer = {}
    costs_per_buyer = {}
    for filename in os.listdir(txt_folder):
        if filename.endswith('.txt') and filename != os.path.basename(email_content_txt_file):
            buyer_name = filename[:-4]
            buyer_txt_file = os.path.join(txt_folder, filename)
            if buyer_name not in buyers_names:
                print(f"Buyer {buyer_name} not in the list of buyers, even if file {buyer_txt_file} available (maybe an unexpected file?), skipping...")
                continue

            buyer_list = read_card_list(buyer_txt_file)
            list_check(simple_cards_list, buyer_list, buyer_name, not_found_cards)

            involved_cards = find_shipping_by_list(shipment_details, buyer_list, buyer_name)
            cards_per_buyer[buyer_name] = involved_cards

            involved_costs = total_cost_by_list(shipment_details, involved_cards, buyer_name)
            costs_per_buyer[buyer_name] = involved_costs
    
    spare_cards = find_shipping_by_list(shipment_details, simple_cards_list) # simple_cards_list is reduced after each iteration, here the remaining cards are the spare ones
    if spare_cards:
        costs_per_buyer["spare cards"] =  total_cost_by_list(shipment_details, spare_cards, "spare cards")

    total_cost_computed = round(sum(costs_per_buyer.values()), 2) # spare cards are included in the total cost, if any
    if (total_cost_computed - total_cost_from_email) > 0.01:
        # we test if the whole process was correct here!
        computation_was_correct = False
    else:
        computation_was_correct = True
    
    return jsonify({
        'notFoundCards': not_found_cards,
        'cardsPerBuyer': cards_per_buyer,
        'costsPerBuyer': costs_per_buyer,
        'spareCards': spare_cards,
        'computationWasCorrect': computation_was_correct,
        }), 200

if __name__ == '__main__':
    app.run(debug=True)