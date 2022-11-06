#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def parse_mail_txt(txtfilename):
    shipments, filepos = parse_shipments(txtfilename)
    
    numShipments, costs, filepos = parse_shipment_data(txtfilename, filepos)
    assert len(shipments) == numShipments, \
        "Read number of shipments does not match!"
        
    shipmentsDetails, filepos = parse_shipment_details(txtfilename, filepos)
    assert len(shipmentsDetails) == numShipments, \
        "Read number of shipments does not match!"
    assert shipments.keys() == shipmentsDetails.keys(), \
        "Read shipments IDs differ among parsed data!"
    
    totalCardsCost = round(sum([cards_cost_tot(el['cardOrdersCurrShipm']) \
                 for el in shipmentsDetails.values()]), 2)
    assert totalCardsCost == costs['cardsCost'], "Wrong cards cost!"
    totalShippingsCost = round(sum([el['shippingCost'] \
                                    for el in shipmentsDetails.values()]), 2)
    assert totalShippingsCost == costs['shippingCost']
    totalFees = round(sum([el['fee'] for el in shipmentsDetails.values()]), 2)
    assert totalFees == costs['fees'], "Wrong fees!"
    
    cardsList = cards_list(shipmentsDetails)
    simpleCardsList = simplify_cards_list(cardsList)
    assert sum(cardsList.values()) == sum(simpleCardsList.values()), \
        "Simplifying card names did not work!"
        
    return shipmentsDetails, costs, cardsList, simpleCardsList
            
def parse_shipments(txtfilename, filepos=0):
    shipments = {}
    with open(txtfilename, 'r') as file:
        line = file.readline()
        while line:
            if "Shipment" in line:
                while split_string_value(line, 0) == "Shipment":
                    shipmentID, sellerName = parse_shipping_line(line)
                    shipments.update({shipmentID:sellerName})
                    line = file.readline()
                filepos = file.tell()
                break
            line = file.readline()
    return shipments, filepos

def parse_shipping_line(line):
    shippingID, sellerName = split_string_value(line, [1, 3])
    return shippingID, sellerName

def parse_shipment_data(txtfilename, filepos=0):
    numShipmentsFound = False
    cardsCostFound = False
    shippingCostFound = False
    feesFound = False
    totalCostFound = False
    with open(txtfilename, 'r') as file:
        file.seek(filepos)
        line = file.readline()
        while line:
            if not numShipmentsFound and "Number of shipments:" in line:
                numShipments = int(split_string_value(line, 3))
                numShipmentsFound = True
            elif not cardsCostFound and "Merchandise value:" in line:
                cardsCost = cast_float(split_string_value(line, 2))
                cardsCostFound =True
            elif not shippingCostFound and "Shipping costs:" in line:
                shippingCost = cast_float(split_string_value(line, 2))
                shippingCostFound = True
            elif not feesFound and "Fees:" in line:
                fees = cast_float(split_string_value(line, 1))
                feesFound = True
            elif not totalCostFound and "Total cost:" in line:
                totalCost = cast_float(split_string_value(line, 2))
                totalCostFound = True
            elif numShipmentsFound and cardsCostFound and shippingCostFound \
                and feesFound and totalCostFound:
                    filepos = file.tell()
                    break
            line = file.readline()
    assert numShipmentsFound, "Number of shipments not found!"
    assert cardsCostFound, "Cards' cost not found!"
    assert shippingCostFound, "Shipping cost not found!"
    assert feesFound, "Fees not found!"
    assert totalCostFound, "Total cost not found!"
    assert (cardsCost+shippingCost+fees) == totalCost, \
        "Total cost does not match with others!"
    costs = {'cardsCost':cardsCost, 'shippingCost':shippingCost, \
             'fees':fees, 'totalCost':totalCost}
    return numShipments, costs, filepos
        
def split_string_value(line, idxListToReturn=0, separator=" "):
    splitLine = line.rstrip().split(separator)
    if isinstance(idxListToReturn, int):
        return splitLine[idxListToReturn]
    else:
        return [splitLine[i] for i in idxListToReturn]
    
def cast_float(numericString):
    return float(numericString.replace(",", "."))

def parse_shipment_details(txtfilename, filepos):
    shipmentsDetails = {}
    with open(txtfilename, 'r') as file:
        file.seek(filepos)
        line = file.readline()
        while "Shipment details:" not in line:
            line = file.readline()
        line = file.readline()
        while line:
            if "Shipment " in line:
                shipmentID = split_string_value(line, 1)
                line = file.readline()
                sellerNameFound = False
                shipmentPriceFound = False
                while mkm_cards_separator() not in line:
                    if not sellerNameFound and "Seller:" in line:
                        sellerName = split_string_value(line, 1)
                        sellerNameFound = True
                    elif not shipmentPriceFound and "Shipment price:" in line:
                        shipmentPrice = cast_float(split_string_value(line, 2))
                        shipmentPriceFound = True
                    elif sellerNameFound and shipmentPriceFound:
                        break
                    line = file.readline()
                line = file.readline()
                
                cardOrdersCurrShipm = []
                while "Shipping" not in line:
                    if "x" in line:
                        cardOrdersCurrShipm.append(parse_card_order(line))
                    line = file.readline()
                shippingCost = cast_float(split_string_value(line, 1))
                if round(shipmentPrice, 2) != \
                    round(shippingCost+cards_cost_tot(cardOrdersCurrShipm),2):
                        fee = round(shipmentPrice - \
                            (shippingCost+cards_cost_tot(cardOrdersCurrShipm)), 2)
                        print(f"Shipment {shipmentID} with seller {sellerName} has a fee of {fee}")
                else:
                    fee = 0
                totCards = sum([card['cardQuantity'] for card in cardOrdersCurrShipm])
                shipmentData = {'sellerName':sellerName, \
                                'shippingCost':shippingCost, \
                                    'cardOrdersCurrShipm':cardOrdersCurrShipm,\
                                        'fee':fee,\
                                            'totCards':totCards}
                shipmentsDetails.update({shipmentID:shipmentData})
            line = file.readline()
        filepos = file.tell()
    return shipmentsDetails, filepos

def mkm_cards_separator():
    return "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

def parse_card_order(line):
    splitLine = line.rstrip().split(" ")
    cardQuantity = int(splitLine[0].replace("x",""))
    cardName = " ".join(splitLine[1:-2])
    cardCost = cast_float(splitLine[-2])
    cardOrder = {'cardQuantity':cardQuantity, 'cardName':cardName, \
                 'cardCost':cardCost}
    return cardOrder

def cards_cost_tot(cardOrders):
    return sum([el['cardCost']*el['cardQuantity'] for el in cardOrders])

def cards_list(shipments):
    cardsList = {}
    allCards = [el['cardOrdersCurrShipm'] for el in shipments.values()]
    for ship in allCards:
        for card in ship:
            if card['cardName'] in cardsList:
                cardsList[card['cardName']] += card['cardQuantity']
            else:
                cardsList.update({card['cardName']:card['cardQuantity']})
    return cardsList

def simplify_cards_list(cardsList):
    simplifiedCardsList = {}
    for cardName, cardQuantity in cardsList.items():
        simpleName = simplify_card_name(cardName)
        if simpleName in simplifiedCardsList:
            simplifiedCardsList[simpleName] += cardQuantity
        else:
            simplifiedCardsList[simpleName] = cardQuantity
    return simplifiedCardsList

def simplify_card_name(cardName):
    return split_string_value(cardName, 0, "(").rstrip()

if __name__=="__main__":
    shipmentsDetails, costs, cardsList, simpleCardsList = \
        parse_mail_txt('order_gmail.txt')