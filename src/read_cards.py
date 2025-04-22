#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def read_card_list(filename):
    cardList = {}
    with open(filename, 'r') as file:
        for line in file:
            if line and line.strip():
                value, key = line.rstrip().split(" ", 1)
                cardList[key] = int(value)
    return cardList

if __name__=="__main__":
    gab = read_card_list('mkm_order_1_gabriele.txt')
    fed = read_card_list('mkm_order_1_federico.txt')
    ang = read_card_list('mkm_order_1_angelo.txt')