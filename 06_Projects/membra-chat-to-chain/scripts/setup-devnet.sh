#!/bin/bash
set -e
solana config set --url devnet
echo "Devnet configured"
solana address
echo "Balance:"
solana balance
echo "Request airdrop if needed: solana airdrop 2"
