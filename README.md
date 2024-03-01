# Wallet Fingerprinting

Welcome to the Wallet Fingerprinting repository! This tool is designed to analyze blockchain transactions and deduce potential wallet software fingerprints. By examining specific characteristics and patterns within transactions, it can suggest which wallet software might have been used to initiate them. This tool covers a range of well-known wallets, including Bitcoin Core, Electrum, Blue Wallet, Trezor, Ledger, Exodus, Trust Wallet, and Coinbase Wallet.

## Important Disclaimer

Please approach the results with a critical mind:

- The identification provided by this tool is not absolute. It's based on patterns and characteristics that are common to transactions created by specific wallets. However, these patterns can overlap across different wallet software, or a wallet might update its transaction patterns over time.
- There is always a possibility that a transaction identified as being created by one of the recognized wallets was, in fact, created by a different wallet software or a customized script.

## Usage Options

You can use the Wallet Fingerprinting in two main ways:

### Google Colab

For ease of use and quick access, a pre-configured Google Colab notebook is available. This option is perfect for those who prefer an online environment without the need for local setup. Access the notebook [here](https://colab.research.google.com/drive/1hWVe9U-r5np_QiGNtM6qaapXq8YwQ1FX?usp=sharing). The Colab environment is configured to use mempool.space by default for fetching transaction data.

### Local Setup

#### Bitcoin Core Configuration

If you have a Bitcoin Core node, you can leverage it for fetching transaction information by configuring the RPC settings in `rpc_config.ini`. This allows for direct interaction with your node, providing more control and privacy over the data retrieval process.

1. Configure your Bitcoin node's RPC settings in `rpc_config.ini`.

#### Jupyter Notebook

For a more hands-on approach, you can run the Jupyter notebook locally. This requires having Jupyter installed on your machine.

1. **Install Jupyter** (if not already installed):

   ```sh
   pip install jupyter
   ```

2. **Launch Jupyter Notebook**:

   ```sh
   jupyter notebook
   ```

This will start a local Jupyter server and open the notebook interface in your default web browser. From here, you can navigate to and open the provided notebook file to start analyzing transaction fingerprints.

## Data Sources

- **Bitcoin Core**: If configured, the tool will use your local Bitcoin Core node to fetch transaction data. This method is recommended for users with privacy concerns or those needing access to real-time blockchain data.
- **Mempool.space API**: By default, and always in the Google Colab environment, the tool uses mempool.space to retrieve transaction information, including confirmation heights. This public API is a convenient way to access blockchain data without running a full node.

## Getting Started

To begin using the Wallet Fingerprinting, choose your preferred usage option above and follow the setup instructions provided. Whether you're exploring blockchain transactions for research, development, or curiosity, this tool offers valuable insights into the origins of blockchain transactions.

## Develop and Contribute

This guide will help you set up the virtual environment and install the
necessary dependencies for the project.

### Dev Prerequisites

- Python >=3.9 installed on your machine

### Dev Setup Instructions

#### Create and Activate the Virtual Environment (optional)

Navigate to the project's root directory. Create a virtual environment
named `.venv` using Python 3.12:

```bash
python3.12 -m venv .venv
```

Activate the virtual environment:

- On Unix or MacOS:

  ```bash
  source .venv/bin/activate
  ```

- On Windows (using Command Prompt):

  ```bash
  .\.venv\Scripts\activate.bat
  ```

#### Install Dependencies

With the virtual environment activated, install the project dependencies
using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### Running the Project

With the virtual environment set up and dependencies installed, you're
now ready to run the project according to the project's run
instructions.

### Troubleshooting

If you encounter any issues during the setup, ensure you have the
correct version of Python installed, and the virtual environment is
activated before installing dependencies.
