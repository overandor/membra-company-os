#!/usr/bin/env python3
"""
Free SMS/Email Payment Demo
Demonstrates Overmanifold's integration with membra bridge ecosystem for free money transfers.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from overmanifold.membra_integration.unified_free_payment_api import (
    UnifiedFreePaymentAPI, PaymentMethod, FreePaymentRequest, FreePaymentResponse
)


async def demo_free_sms_payment():
    """Demonstrate free SMS payment"""
    print("\n📱 FREE SMS PAYMENT DEMONSTRATION")
    print("="*80 + "\n")
    
    # Initialize API
    api = UnifiedFreePaymentAPI(membra_api_url="http://localhost:8000")
    
    print("Step 1: Check system status")
    print("-" * 40)
    status = api.get_system_status()
    print(f"✓ Membra Bridge Status: {status['membra_bridge_status'].get('status', 'unknown')}")
    print(f"✓ Available Sponsors: {status['available_sponsors']}")
    print(f"✓ Total Sponsor Budget: {status['total_sponsor_budget']:,} tokens")
    print()
    
    print("Step 2: Register sender wallet")
    print("-" * 40)
    sender_phone = "+1234567890"
    sender_balance = api.get_user_balance(sender_phone)
    print(f"✓ Sender Phone: {sender_phone}")
    print(f"✓ Wallet Address: {sender_balance.get('wallet_address', 'N/A')}")
    print(f"✓ Balance: {sender_balance.get('balance', 0):,} tokens")
    print()
    
    print("Step 3: Register recipient wallet")
    print("-" * 40)
    recipient_phone = "+1987654321"
    recipient_balance = api.get_user_balance(recipient_phone)
    print(f"✓ Recipient Phone: {recipient_phone}")
    print(f"✓ Wallet Address: {recipient_balance.get('wallet_address', 'N/A')}")
    print(f"✓ Balance: {recipient_balance.get('balance', 0):,} tokens")
    print()
    
    print("Step 4: Send free SMS payment")
    print("-" * 40)
    amount = 100
    message = "Here's 100 USDC for your help with the project!"
    
    print(f"✓ Amount: {amount} USDC")
    print(f"✓ Message: {message}")
    
    response = await api.send_free_sms_payment(
        sender_phone=sender_phone,
        recipient_phone=recipient_phone,
        amount=amount,
        message=message
    )
    
    print()
    print("Step 5: Payment Result")
    print("-" * 40)
    print(f"✓ Success: {response.success}")
    print(f"✓ Transaction ID: {response.transaction_id}")
    print(f"✓ Amount Transferred: {response.amount_transferred} USDC")
    print(f"✓ Transaction Cost: {response.transaction_cost / 100:.2f} USD")
    print(f"✓ Mining Reward: {response.mining_reward} tokens")
    print(f"✓ Sponsor Bonus: {response.sponsor_bonus} tokens")
    print(f"✓ Net Cost to User: {response.net_cost_to_user / 100:.2f} USD")
    print(f"✓ Sponsor: {response.sponsor_id}")
    print()
    
    print("Step 6: Updated Balances")
    print("-" * 40)
    updated_sender = api.get_user_balance(sender_phone)
    updated_recipient = api.get_user_balance(recipient_phone)
    print(f"✓ Sender Balance: {updated_sender.get('balance', 0):,} tokens")
    print(f"✓ Recipient Balance: {updated_recipient.get('balance', 0):,} tokens")
    print()
    
    print("✅ FREE SMS PAYMENT DEMONSTRATION COMPLETE")
    print(f"User saved {(response.transaction_cost - response.net_cost_to_user) / 100:.2f} USD through sponsorship!")
    print()


async def demo_free_email_payment():
    """Demonstrate free email payment"""
    print("\n📧 FREE EMAIL PAYMENT DEMONSTRATION")
    print("="*80 + "\n")
    
    # Initialize API
    api = UnifiedFreePaymentAPI(membra_api_url="http://localhost:8000")
    
    print("Step 1: Check system status")
    print("-" * 40)
    status = api.get_system_status()
    print(f"✓ Membra Bridge Status: {status['membra_bridge_status'].get('status', 'unknown')}")
    print(f"✓ Available Sponsors: {status['available_sponsors']}")
    print(f"✓ Total Sponsor Budget: {status['total_sponsor_budget']:,} tokens")
    print()
    
    print("Step 2: Register sender email wallet")
    print("-" * 40)
    sender_email = "alice@example.com"
    sender_balance = api.get_user_balance(sender_email)
    print(f"✓ Sender Email: {sender_email}")
    print(f"✓ Wallet Address: {sender_balance.get('wallet_address', 'N/A')}")
    print(f"✓ Balance: {sender_balance.get('balance', 0):,} tokens")
    print()
    
    print("Step 3: Register recipient email wallet")
    print("-" * 40)
    recipient_email = "bob@example.com"
    recipient_balance = api.get_user_balance(recipient_email)
    print(f"✓ Recipient Email: {recipient_email}")
    print(f"✓ Wallet Address: {recipient_balance.get('wallet_address', 'N/A')}")
    print(f"✓ Balance: {recipient_balance.get('balance', 0):,} tokens")
    print()
    
    print("Step 4: Send free email payment")
    print("-" * 40)
    amount = 50
    subject = "Payment from Overmanifold Protocol"
    message = "Here's 50 USDC for your contribution!"
    
    print(f"✓ Amount: {amount} USDC")
    print(f"✓ Subject: {subject}")
    print(f"✓ Message: {message}")
    
    response = await api.send_free_email_payment(
        sender_email=sender_email,
        recipient_email=recipient_email,
        amount=amount,
        subject=subject,
        message=message
    )
    
    print()
    print("Step 5: Payment Result")
    print("-" * 40)
    print(f"✓ Success: {response.success}")
    print(f"✓ Transaction ID: {response.transaction_id}")
    print(f"✓ Amount Transferred: {response.amount_transferred} USDC")
    print(f"✓ Transaction Cost: {response.transaction_cost / 100:.2f} USD")
    print(f"✓ Mining Reward: {response.mining_reward} tokens")
    print(f"✓ Sponsor Bonus: {response.sponsor_bonus} tokens")
    print(f"✓ Net Cost to User: {response.net_cost_to_user / 100:.2f} USD")
    print(f"✓ Sponsor: {response.sponsor_id}")
    print()
    
    print("Step 6: Updated Balances")
    print("-" * 40)
    updated_sender = api.get_user_balance(sender_email)
    updated_recipient = api.get_user_balance(recipient_email)
    print(f"✓ Sender Balance: {updated_sender.get('balance', 0):,} methods")
    print(f"✓ Recipient Balance: {updated_recipient.get('balance', 0):,} tokens")
    print()
    
    print("✅ FREE EMAIL PAYMENT DEMONSTRATION COMPLETE")
    print(f"User saved {(response.transaction_cost - response.net_cost_to_user) / 100:.2f} USD through sponsorship!")
    print()


async def demo_sponsor_system():
    """Demonstrate sponsor system"""
    print("\n💰 SPONSOR SYSTEM DEMONSTRATION")
    print("="*80 + "\n")
    
    # Initialize API
    api = UnifiedFreePaymentAPI(membra_api_url="http://localhost:8000")
    
    print("Step 1: Current sponsor statistics")
    print("-" * 40)
    stats = api.get_payment_statistics()
    sponsor_stats = stats["sponsor_statistics"]
    print(f"✓ Active Sponsors: {sponsor_stats['active_sponsors']}")
    print(f"✓ Total Daily Budget: {sponsor_stats['total_daily_budget']:,} tokens")
    print(f"✓ Total Remaining Budget: {sponsor_stats['total_remaining_budget']:,} tokens")
    print(f"✓ Transactions Sponsored: {sponsor_stats['total_transactions_sponsored']}")
    print()
    
    print("Step 2: Register new corporate sponsor")
    print("-" * 40)
    sponsor_info = api.register_sponsor(
        sponsor_address="0x1234567890abcdef1234567890abcdef12345678",
        sponsor_name="TechCorp Inc",
        sponsor_type="corporate",
        sponsor_level="gold",
        custom_budget=50000
    )
    
    print(f"✓ Sponsor ID: {sponsor_info['sponsor_id']}")
    print(f"✓ Sponsor Name: {sponsor_info['sponsor_name']}")
    print(f"✓ Sponsor Type: {sponsor_info['sponsor_type']}")
    print(f"✓ Sponsor Level: {sponsor_info['sponsor_level']}")
    print(f"✓ Daily Budget: {sponsor_info['daily_budget']:,} tokens")
    print(f"✓ Remaining Budget: {sponsor_info['remaining_budget']:,} tokens")
    print()
    
    print("Step 3: Updated sponsor statistics")
    print("-" * 40)
    updated_stats = api.get_payment_statistics()
    updated_sponsor_stats = updated_stats["sponsor_statistics"]
    print(f"✓ Active Sponsors: {updated_sponsor_stats['active_sponsors']}")
    print(f"✓ Total Daily Budget: {updated_sponsor_stats['total_daily_budget']:,} tokens")
    print(f"✓ Total Remaining Budget: {updated_sponsor_stats['total_remaining_budget']:,} tokens")
    print()
    
    print("✅ SPONSOR SYSTEM DEMONSTRATION COMPLETE")
    print("New sponsor can now fund free transactions for users!")
    print()


async def main():
    """Main demonstration function"""
    print("\n🌐 OVERMANIFOLD FREE SMS/EMAIL PAYMENT DEMONSTRATION")
    print("="*80 + "\n")
    
    print("This demonstration shows how Overmanifold integrates with the membra bridge")
    print("ecosystem to enable free money transfers via SMS or email.\n")
    
    print("Key Features:")
    print("• Free transactions sponsored by protocol treasury or external sponsors")
    print("• Users earn mining rewards for sending SMS/emails")
    • "• Phone numbers and email addresses map to wallet addresses")
    print("• Premined tokens for each user enable instant transfers")
    print("• Merkle tree derivation ensures cryptographic security")
    print()
    
    print("Demonstrations:")
    print("1. Free SMS Payment Demo")
    print("2. Free Email Payment Demo")
    print("3. Sponsor System Demo")
    print("4. Combined Demo")
    print("0. Exit")
    print()
    
    while True:
        try:
            choice = input("Select demonstration (0-4): ").strip()
            
            if choice == "0":
                print("\n👋 Exiting demonstration. Goodbye!\n")
                break
            elif choice == "1":
                await demo_free_sms_payment()
            elif choice == "2":
                await demo_free_email_payment()
            elif choice == "3":
                await demo_sponsor_system()
            elif choice == "4":
                print("\n🚀 Running all demonstrations...\n")
                await demo_free_sms_payment()
                await demo_free_email_payment()
                await demo_sponsor_system()
                print("\n✅ ALL DEMONSTRATIONS COMPLETE\n")
            else:
                print("❌ Invalid choice. Please select 0-4.\n")
            
            print("="*80)
            input("Press Enter to continue...")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demonstration interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or select a different demonstration.\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demonstration interrupted. Goodbye!\n")