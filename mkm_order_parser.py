#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import read_cards
import parse_gmail_mkm

def list_check(cardList, listToRemove, listOwner=""):
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
    return

def list_clean(cardList):
    invalidKeys = [key for key, val in cardList.items() if int(val) == 0]
    for keyToDelete in invalidKeys:
        del cardList[keyToDelete]
    return cardList

def print_list(cardList):
    for cardName, cardQuantity in cardList.items():
        print(f"{cardQuantity} {cardName}")
    return

def find_shipping_by_list(shipmentsDetails, listOfSomeone, listOwner=""):
    if listOwner:
        print(f"Checking involved shipments of {listOwner}...")
    involvedShipments = {}
    for shipID, shipDetails in shipmentsDetails.items():
        foundCardsCostThisShipm = {}
        for idx, card in enumerate(shipDetails['cardOrders']):
            simpleName = parse_gmail_mkm.simplify_card_name(card['cardName'])
            cardsInOrder = card['cardQuantity']
            if simpleName in listOfSomeone:
                if listOfSomeone[simpleName] <= cardsInOrder:
                    foundCards = listOfSomeone[simpleName]
                    del listOfSomeone[simpleName]
                else:
                    foundCards = cardsInOrder
                    listOfSomeone[simpleName] -= cardsInOrder
                assert foundCards <= cardsInOrder, \
                    f"Error while processing shipping {shipID}"
                shipDetails['cardOrders'][idx]['cardQuantity'] -= foundCards
                if simpleName in foundCardsCostThisShipm:
                    foundCardsCostThisShipm[simpleName][0] += foundCards
                    foundCardsCostThisShipm[simpleName][1] += card['cardCost']*float(foundCards)
                else:
                    foundCardsCostThisShipm.update({simpleName:[foundCards, card['cardCost']*float(foundCards)]})
        # Removing cards while looping not possible, doing it later
        if foundCardsCostThisShipm:
            involvedShipments.update({shipID:foundCardsCostThisShipm})
            shipDetails['cardOrders'] = [cardOrder for cardOrder in shipDetails['cardOrders'] if cardOrder['cardQuantity'] != 0]
    return involvedShipments

def total_cost_by_list(shipmentsDetails, involvedShipments, listOwner=""):
    if listOwner:
        print(f"\nChecking involved shipments of {listOwner}...")
        print("(Each card includes its cost per shipment plus its averaged share for the shipping+fees cost)")
    ordersCost = {}
    for shipID, cardCosts in involvedShipments.items():
        shippingCost = shipmentsDetails[shipID]['shippingCost'] + shipmentsDetails[shipID]['fee']
        totCardsInOrder = shipmentsDetails[shipID]['totCards']
        numCardsInOrder = sum([el[0] for el in cardCosts.values()])
        assert numCardsInOrder / totCardsInOrder <= 1, \
            f"Wrong number of cards in order {shipID}!"
        involvedCostThisShipm = round(numCardsInOrder / totCardsInOrder * shippingCost, 2)
        costCardsInOrder = sum([el[1] for el in cardCosts.values()])
        #print(f"Order {shipID} - seller {shipmentsDetails[shipID]['sellerName']} : {involvedCostThisShipm} for shipping, {costCardsInOrder} for cards, {shipmentsDetails[shipID]['fee']} as fee")
        shipmentData = {'involvedCostThisShipm':involvedCostThisShipm, \
                        'costCardsInOrder':costCardsInOrder, \
                            'totalCost':involvedCostThisShipm+costCardsInOrder}
        for cardName, cardDetails in cardCosts.items():
            numCardInOrder = cardDetails[0]
            shareCostCardInOrder = round(numCardInOrder / totCardsInOrder * shippingCost, 2)
            costCardInOrder = cardDetails[1]
            totCostCardInOrder = shareCostCardInOrder + costCardInOrder
            print(f"{numCardInOrder} {cardName} ({costCardInOrder} cards + {shareCostCardInOrder} shipping = {totCostCardInOrder}) for order {shipID} - seller {shipmentsDetails[shipID]['sellerName']}")
        print(f"= TOT: {involvedCostThisShipm} shipping + {costCardsInOrder} cards ({shipmentsDetails[shipID]['fee']} fee) = {shipmentData['totalCost']}")
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
    
    notFound = {}
    listGabFile = 'mkm_order_1_gabriele.txt'
    listGab = read_cards.read_card_list(listGabFile)
    list_check(simpleCardsList, listGab, "Gabriele")
    listFedFile = 'mkm_order_1_federico.txt'
    listFed = read_cards.read_card_list(listFedFile)
    list_check(simpleCardsList, listFed, "Federico")
    listAngFile = 'mkm_order_1_angelo.txt'
    listAng = read_cards.read_card_list(listAngFile)
    list_check(simpleCardsList, listAng, "Angelo")
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
    del card, shipID, shipDetails, numSpareCards
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
    
    