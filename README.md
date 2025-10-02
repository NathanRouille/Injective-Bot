# Injective On-Chain Trading Bot 

## Overview

This project is the first and fastest on-chain trading bot designed for the Injective blockchain. It efficiently detects opportunities such as new token creations and liquidity provisioning, leveraging advanced multi-threading to manage and monitor multiple tokens concurrently. By executing the first transaction in a liquidity pool, the bot guarantees no financial loss under normal conditions, as the price of tokens is directly tied to the pool's balance ratio. This strategy allows for significant profit potential with high multipliers, while the only notable risk is a liquidity removal (rug pull) by the pool creator.
Built with Python and powered by the [pyinjective SDK](https://github.com/InjectiveLabs/sdk-python).

## Key Features

- **Real-Time Blockchain Scanning**: Continuously monitors all transactions on Injective, fetching data directly from nodes.
- **New Token Detection**: Automatically identifies transactions that create new tokens and begins monitoring them.
- **Liquidity Provision Monitoring**: Executes trades within milliseconds of liquidity being added to a pool.
- **Automatic Buy and Sell**: Executes purchases as soon as liquidity is provided and sells tokens based on user-defined multipliers.
- **Multi-Threading**: Handles multiple tokens simultaneously, ensuring seamless and efficient trading across numerous opportunities.
- **Discord Integration**: Notifies users in real-time of important events (e.g., token detection, purchase, or sale).
- **Comprehensive Logging**: Captures detailed logs of operations and errors for transparency and debugging.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NathanRouille/Injective-Bot.git
   cd Injective-Bot
   ```

2. Install the required dependencies:
- `injective-py==1.0`
- `python-dotenv`
- `aiologger`
- `requests`

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and populate it with the following:
   ```env
   PRIVATE_KEY=<your_injective_private_key>
   DISCORD_AUTH=<your_discord_auth_token>
   DISCORD_CHANNEL=<your_discord_channel_id>
   DISCORD_MENTION=<optional_discord_mention>
   ```

## Usage

1. Run the bot by executing:
   ```bash
   python main.py
   ```

2. Provide the following inputs when prompted:
   - Quantity of INJ you want to use to buy factory tokens
   - Quantity of INJ you want to use to buy CW20 tokens
   - Sale ratio (in percentage) : The percentage of the purchased tokens that you want to sell automatically when the selling conditions are met.
   - Multipliers for factory and CW20 tokens : The target price multiplier at which the bot should begin selling your tokens automatically.


## Challenges Overcome

- **Undocumented Node Requests**: Significant effort was spent analyzing Injective's node interactions to craft precise requests.
- **Efficient Multi-Threading**: Managing simultaneous trades and blockchain scans posed unique challenges, resolved with careful design.
  

## Contributions

Contributions are welcome! Please submit a pull request or open an issue for suggestions and bug reports.
