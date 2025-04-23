import os
from src.mkm_order_parser import find_shipping_by_list, list_check, print_list, total_cost_by_list
from src.read_cards import read_card_list
from src.parse_gmail_mkm import parse_mail_txt

if __name__ == "__main__":
    txt_folder = os.path.join(os.getcwd(), 'example')

    shipmentsDetails, costs, cardsList, simpleCardsList = \
        parse_mail_txt(os.path.join(txt_folder, 'order_gmail.txt'))
    
    print(f"\nNumber of different cards in list: {len(simpleCardsList)}")
    print(f"Number of cards in list: {sum(simpleCardsList.values())}")
    
    notFound = {}
    listGab = read_card_list(os.path.join(txt_folder, 'mkm_order_1_gabriele.txt'))
    simpleCardsList = list_check(simpleCardsList, listGab, "Gabriele", notFound)

    listFed = read_card_list(os.path.join(txt_folder, 'mkm_order_1_federico.txt'))
    simpleCardsList = list_check(simpleCardsList, listFed, "Federico", notFound)

    listAng = read_card_list(os.path.join(txt_folder, 'mkm_order_1_angelo.txt'))
    simpleCardsList = list_check(simpleCardsList, listAng, "Angelo", notFound)
    
    print("\nThe following cards were NOT found in the input card list:")
    print_list(notFound)
    print(f"\nNumber of cards NOT found: {sum(notFound.values())}")
    print(f"Number of different cards NOT found: {len(notFound)}")
    del notFound
    
    print("\nSpare cards in the input card list, if missing removed:")
    print_list(simpleCardsList)
    print("(The previous cards were not in the card lists but in the input card list)")
    
    involvedGab = find_shipping_by_list(shipmentsDetails, listGab, "Gabriele")
    involvedFed = find_shipping_by_list(shipmentsDetails, listFed, "Federico")
    involvedAng = find_shipping_by_list(shipmentsDetails, listAng, "Angelo")
    print("\nThe previous list should be equal to the following:")
    spareCardsQuantity = 0
    for shipID, shipDetails in shipmentsDetails.items():
        if shipDetails['cardOrders']:
            for card in shipDetails['cardOrders']:
                numSpareCards = card['cardQuantity']
                spareCardsQuantity += numSpareCards
                print(f"{numSpareCards} {card['cardName']} in shipment {shipID} (seller {shipDetails['sellerName']} is not in any list!")
            del card, numSpareCards
    del shipID, shipDetails
    assert sum(simpleCardsList.values()) == spareCardsQuantity, \
        "Number of spare cards does not match!"
    del spareCardsQuantity
                
    totCostGab = total_cost_by_list(shipmentsDetails, involvedGab, "Gabriele")
    totCostFed = total_cost_by_list(shipmentsDetails, involvedFed, "Federico")
    totCostAng = total_cost_by_list(shipmentsDetails, involvedAng, "Angelo")
    involvedSpareCards = find_shipping_by_list(shipmentsDetails, simpleCardsList)
    assert len([el for el in shipmentsDetails.values() if el['cardOrders']]) == 0, \
        "Some shipments have not been processed - shipment details not empty!"
    assert len(simpleCardsList) == 0, \
        "Some shipments have not been processed - resulting cards list not empty!"
    del simpleCardsList
    
    totCostSpareCards = total_cost_by_list(shipmentsDetails, involvedSpareCards, "spare cards")
    totCost = round(totCostGab+totCostFed+totCostAng+totCostSpareCards, 2)
    assert abs(totCost - costs['totalCost']) < 0.01, \
        "Total cost of cards does not match!"