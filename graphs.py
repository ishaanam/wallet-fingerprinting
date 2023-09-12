import matplotlib.pyplot as plt
import numpy as np

from fingerprinting import analyze_block
from mempool_space import getblocks

def create_graph(block_height):
    wallet_info = None

    blocks = getblocks(block_height)

    for block in blocks:
        block = blocks
        print(block)
        block_wallet_info = analyze_block(block)
        if not wallet_info:
            wallet_info = block_wallet_info
        else:
            for key in list(wallet_info.keys()):
                wallet_info[key] += block_wallet_info[key]

    print(wallet_info)
 
    wallets = list(wallet_info.keys())
    numbers = list(wallet_info.values())

    fig = plt.figure(figsize=(10, 5))

    plt.bar(wallets, numbers, color="purple", width=0.5)

    plt.xlabel("Wallets")
    plt.ylabel("Number of Transactions")
    plt.show()

if __name__ == "__main__":
    create_graph(807038)
