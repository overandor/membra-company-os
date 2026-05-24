#!/bin/bash
set -e
cd programs/membra_qr_gateway
anchor build
anchor deploy --provider.cluster devnet
echo "Deployed to devnet"
