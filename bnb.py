import logging
from telegram import Update
from web3 import Web3
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

bsc_rpc_url = 'https://bsc-mainnet.rpcfast.com?api_key=xbhWBI1Wkguk8SNMu1bvvLurPGLXmgwYeC4S6g2H7WdwFigZSmPWVZRxrskEQwIf'  # BSC Mainnet RPC URL
bsc_private_key =''  # Replace with your BSC private key
web3_bsc = Web3(Web3.HTTPProvider(bsc_rpc_url))

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    msg = (
        "This a blockchain payment bot use the following command /withdraw_bnb to perform your transaction"
    )

    await update.message.reply_text(msg)

async def start_with_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Sends an invoice with shipping-payment.
    chat_id = update.message.chat_id
    #title = "Payment Example"
    #description = "Payment Example using python-telegram-bot"
    # select a payload just for you to recognize its the donation from your bot

    
    await context.bot.send_invoice(
        chat_id,
    )

async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, max_length: int = 4096) -> None:
    """
    Sends a long message by splitting it into smaller chunks to avoid the "Text is too long" error.
    """
    for i in range(0, len(message), max_length):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message[i:i+max_length])
async def withdraw_bnb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_input = update.message.text
        args = user_input.split()[1:]
        
        if len(args) < 2:
            raise ValueError("Insufficient arguments. Usage: /withdraw_bnb <recipient_address> <amount>")
        
        to_address = args[0]
        amount = int(float(args[1]))

        # Estimate gas for the transaction
        gas_estimate = web3_bsc.eth.estimate_gas({
            'to': to_address,
            'value': amount,
        })

        # Get current gas price
        gas_price = web3_bsc.eth.gas_price
        sender_account = ''

        transaction = {
            'to': to_address,
            'value': amount,
            'nonce': web3_bsc.eth.get_transaction_count(sender_account),
            'gas': gas_estimate,  # Use estimated gas
            'gasPrice': gas_price,  # Set gas price
            'chainId': 56,
        }

        signed_tx = web3_bsc.eth.account.sign_transaction(transaction, private_key=bsc_private_key)

        tx_hash = web3_bsc.eth.send_raw_transaction(signed_tx.rawTransaction)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Withdrawal of bnb tokens initiated. Transaction hash: {tx_hash.hex()}")

        # Log the transaction hash
        logger.info(f"Transaction hash: {tx_hash.hex()}")

        # Add callback to check transaction status
        await check_transaction_status(update, context, tx_hash)

    except ValueError as ve:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(ve))
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {str(e)}")



async def check_transaction_status(update: Update, context: ContextTypes.DEFAULT_TYPE, tx_hash: str) -> None:
    try:
        # Wait for transaction to be mined
        receipt = web3_bsc.eth.wait_for_transaction_receipt(tx_hash)

        # Get transaction details
        block_number = receipt['blockNumber']
        block_hash = receipt['blockHash']

        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       text=f"Transaction mined in block: {block_number}\nBlock hash: {block_hash}")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, 
                                       text=f"Error checking transaction status: {str(e)}")


        # Log the transaction hash
        logger.info(f"Transaction hash: {tx_hash.hex()}")

    except ValueError as ve:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=str(ve))
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {str(e)}")






async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirms the successful payment."""
    # do something after successfully receiving payment?
    msg = ("Thank you for successful payment")
    
    await update.message.reply_text(msg)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("").build()

    # simple start function
    application.add_handler(CommandHandler("shipping", start_with_wallet_callback))
    application.add_handler(CommandHandler("start", start_callback))

    # Add command handler to start the payment invoice
    application.add_handler(CommandHandler("withdraw_cake", withdraw_bnb))

    # Success! Notify your user!
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
