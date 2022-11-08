#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import read_cards
import parse_gmail_mkm

def list_check(cardList, listToRemove, listOwner="", notFound={}):
    if listOwner:
        print(f"\nChecking list of {listOwner}...")
    for cardName, cardQuantity in listToRemove.items():
        if cardName in cardList:
            if cardList[cardName] < cardQuantity:
                cardsToRemove = cardList[cardName]
                missingCards = cardQuantity - cardsToRemove
                print(f"{missingCards} {cardName} missing, others in list were removed!")
                if cardName in notFound:
                    notFound[cardName] += missingCards    
                else:
                    notFound.update({cardName:missingCards})
            else:
                cardsToRemove = cardQuantity
            cardList[cardName] -= cardsToRemove
        else:
            print(f"{cardQuantity} {cardName} was not found in the input card list!")
            if cardName in notFound:
                notFound[cardName] += cardQuantity
            else:
                notFound.update({cardName:cardQuantity})
    cardList = list_clean(cardList)
    return cardList, notFound

def list_clean(cardList):
    invalidKeys = [key for key, val in cardList.items() if int(val) == 0]
    for keyToDelete in invalidKeys:
        del cardList[keyToDelete]
    return cardList

def find_shipping_by_list(shipments, listOfSomeone, listOwner=""):
    if listOwner:
        print(f"Checking list of {listOwner}")
    involvedShipments = {}
    for shipID, shipDetails in shipments.items():
        foundCardsCostThisShipm = []
        idxsCardToRemove = []
        for idx, card in enumerate(shipDetails['cardOrders']):
            simpleName = parse_gmail_mkm.simplify_card_name(card['cardName'])
            if simpleName in listOfSomeone:
                if listOfSomeone[simpleName] <= card['cardQuantity']:
                    del listOfSomeone[simpleName]
                else:
                    listOfSomeone[simpleName] -= card['cardQuantity']
                #print(f"{simpleName} found in shipment {shipID} {card['cardQuantity']} times")
                foundCardsCostThisShipm.append([simpleName, card['cardQuantity'], card['cardCost']*float(card['cardQuantity'])])
                idxsCardToRemove.append(idx)
        if foundCardsCostThisShipm:
            involvedShipments.update({shipID:foundCardsCostThisShipm})
            for idxCardToRemove in sorted(idxsCardToRemove, reverse=True):
                del shipments[shipID]['cardOrders'][idxCardToRemove]
    return shipments, involvedShipments

def total_cost_by_list(shipmentsDetails, involvedShipments, listOwner=""):
    if listOwner:
        print(f"\nChecking involved shipments of {listOwner}...")
    ordersCost = {}
    for shipID, cardCosts in involvedShipments.items():
        shippingCost = shipmentsDetails[shipID]['shippingCost'] + shipmentsDetails[shipID]['fee']
        totCardsInOrder = shipmentsDetails[shipID]['totCards']
        numCardsInOrder = sum([card[1] for card in cardCosts])
        involvedCostThisShipm = round(numCardsInOrder / totCardsInOrder * shippingCost, 2)
        costCardsInOrder = sum([card[2] for card in cardCosts])
        print(f"Order {shipID} - seller {shipmentsDetails[shipID]['sellerName']} : {involvedCostThisShipm} for shipping, {costCardsInOrder} for cards, {shipmentsDetails[shipID]['fee']} as fee")
        shipmentData = {'involvedCostThisShipm':involvedCostThisShipm, \
                        'costCardsInOrder':costCardsInOrder, \
                            'totalCost':involvedCostThisShipm+costCardsInOrder}
        ordersCost.update({shipID:shipmentData})
    totalCostCards = round(sum([cost['costCardsInOrder'] for cost in ordersCost.values()]), 2)
    print(f"Total cost of cards: {totalCostCards}")
    totalCostShipping = round(sum([cost['involvedCostThisShipm'] for cost in ordersCost.values()]), 2)
    print(f"Total cost of shippings: {totalCostShipping}")
    totalCostOrders = round(sum([cost['totalCost'] for cost in ordersCost.values()]), 2)
    print(f"Total cost of orders: {totalCostOrders}")
    return totalCostOrders

if __name__=="__main__":
    mkmMail = 'order_gmail.txt'
    shipmentsDetails, costs, cardsList, simpleCardsList = \
        parse_gmail_mkm.parse_mail_txt(mkmMail)
    print(f"\nNumber of different cards in list: {len(simpleCardsList)}")
    print(f"Number of cards in list: {sum(simpleCardsList.values())}")
    
    listGabFile = 'mkm_order_1_gabriele.txt'
    listGab = read_cards.read_card_list(listGabFile)
    simpleCardsList, notFound = list_check(simpleCardsList, listGab, "Gabriele")
    listFedFile = 'mkm_order_1_federico.txt'
    listFed = read_cards.read_card_list(listFedFile)
    simpleCardsList, notFound = list_check(simpleCardsList, listFed, "Federico", notFound)
    listAngFile = 'mkm_order_1_angelo.txt'
    listAng = read_cards.read_card_list(listAngFile)
    simpleCardsList, notFound = list_check(simpleCardsList, listAng, "Angelo", notFound)
    print("\nThe following cards were NOT found in the input card list:")
    for cardName, cardQuantity in notFound.items():
        print(f"{cardQuantity} {cardName}")
    print(f"\nNumber of cards NOT found: {sum(notFound.values())}")
    print(f"Number of different cards NOT found: {len(notFound)}")
    
    print("\nSpare cards in the input card list, if missing removed:")
    for cardName, cardQuantity in simpleCardsList.items():
        print(f"{cardQuantity} {cardName}")
    print("(The previous cards were not in the card lists but in the input card list)")
    
    shipmentsDetails, involvedGab = find_shipping_by_list(shipmentsDetails, listGab)
    shipmentsDetails, involvedFed = find_shipping_by_list(shipmentsDetails, listFed)
    shipmentsDetails, involvedAng = find_shipping_by_list(shipmentsDetails, listAng)
    print("\nThe previous list should be equal to the following:")
    spareCardsCost = 0
    for shipID, shipDetails in shipmentsDetails.items():
        if shipDetails['cardOrders']:
            for card in shipDetails['cardOrders']:
                print(f"{card['cardQuantity']} {card['cardName']} in shipment {shipID} (seller {shipDetails['sellerName']} is not in any list!")
                spareCardsCost += round(card['cardCost']*float(card['cardQuantity']), 2)
    print(f"\nTotal cost of spare cards (without shipping): {spareCardsCost}")
                
    totCostGab = total_cost_by_list(shipmentsDetails, involvedGab, "Gabriele")
    totCostFed = total_cost_by_list(shipmentsDetails, involvedFed, "Federico")
    totCostAng = total_cost_by_list(shipmentsDetails, involvedAng, "Angelo")
    shipmentsDetails, involvedSpareCards = find_shipping_by_list(shipmentsDetails, simpleCardsList)
    totCostSpareCards = total_cost_by_list(shipmentsDetails, involvedSpareCards, "spare cards")
    totCost = round(totCostGab+totCostFed+totCostAng+totCostSpareCards, 2)
    assert abs(totCost - costs['totalCost']) < 0.01, \
        "Total cost of cards does not match!"
    
    