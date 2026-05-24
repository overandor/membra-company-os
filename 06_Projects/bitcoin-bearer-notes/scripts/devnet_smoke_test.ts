/**
 * Devnet Smoke Test for Membra Money
 *
 * Prerequisites:
 *   - solana config set --url devnet
 *   - solana airdrop 2
 *   - anchor build && anchor deploy
 *   - npm install
 *
 * Run:
 *   npx ts-node scripts/devnet_smoke_test.ts
 */

import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { BitcoinBearerNotes } from "../target/types/bitcoin_bearer_notes";

async function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace
    .BitcoinBearerNotes as Program<BitcoinBearerNotes>;
  const wallet = provider.wallet as anchor.Wallet;

  const VAULT_SEED = Buffer.from("vault");
  const NOTE_SEED = Buffer.from("note");
  const CLAIM_SEED = Buffer.from("claim");
  const MINT_AUTHORITY_SEED = Buffer.from("mint_authority");

  console.log("=== Membra Money Devnet Smoke Test ===");
  console.log("Wallet:", wallet.publicKey.toString());

  // 1. Initialize vault
  const [vaultPDA] = anchor.web3.PublicKey.findProgramAddressSync(
    [VAULT_SEED],
    program.programId
  );
  console.log("\n[1/7] Initializing vault...");
  try {
    await program.methods
      .initialize()
      .accounts({
        vault: vaultPDA,
        authority: wallet.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();
    console.log("      OK — vault initialized");
  } catch (e: any) {
    if (e.toString().includes("already in use")) {
      console.log("      SKIP — vault already exists");
    } else {
      throw e;
    }
  }

  // 2. Mint a note
  const serial = Date.now(); // pseudo-unique for smoke test
  const denomination = new anchor.BN(1_000_000_000); // $10 in sats
  const metadataUri = "ipfs://smoke-test";

  const [notePDA] = anchor.web3.PublicKey.findProgramAddressSync(
    [NOTE_SEED, new anchor.BN(serial).toArrayLike(Buffer, "le", 8)],
    program.programId
  );
  const [mintAuthorityPDA] = anchor.web3.PublicKey.findProgramAddressSync(
    [MINT_AUTHORITY_SEED],
    program.programId
  );

  console.log("\n[2/7] Minting note #", serial, "...");
  await program.methods
    .mintNote(new anchor.BN(serial), denomination, metadataUri)
    .accounts({
      note: notePDA,
      vault: vaultPDA,
      mintAuthority: mintAuthorityPDA,
      holder: wallet.publicKey,
      authority: wallet.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .rpc();
  console.log("      OK — note minted");

  // 3. Transfer note with holder signature
  const newHolder = anchor.web3.Keypair.generate();
  console.log("\n[3/7] Transferring note to", newHolder.publicKey.toString(), "...");
  await program.methods
    .transferNote(new anchor.BN(serial))
    .accounts({
      note: notePDA,
      vault: vaultPDA,
      newHolder: newHolder.publicKey,
      holder: wallet.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .rpc();
  console.log("      OK — transferred");

  // Transfer back to original wallet for redemption
  await program.methods
    .transferNote(new anchor.BN(serial))
    .accounts({
      note: notePDA,
      vault: vaultPDA,
      newHolder: wallet.publicKey,
      holder: newHolder.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .signers([newHolder])
    .rpc();
  console.log("      OK — transferred back to original wallet");

  // 4. Create CoinPack
  const claimId = Buffer.alloc(32);
  crypto.getRandomValues(claimId);
  const pinHash = anchor.web3.sha256(Buffer.from("123456"));
  const [claimPDA] = anchor.web3.PublicKey.findProgramAddressSync(
    [CLAIM_SEED, claimId],
    program.programId
  );

  console.log("\n[4/7] Creating CoinPack...");
  await program.methods
    .createClaimBundle(
      Array.from(claimId),
      ["BTC", "USDC"],
      [new anchor.BN(100000), new anchor.BN(5000000)],
      new anchor.BN(Date.now() / 1000 + 86400),
      Array.from(pinHash)
    )
    .accounts({
      claimBundle: claimPDA,
      vault: vaultPDA,
      creator: wallet.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .rpc();
  console.log("      OK — CoinPack created");

  // 5. Claim CoinPack
  const claimer = anchor.web3.Keypair.generate();
  console.log("\n[5/7] Claiming CoinPack...");
  await program.methods
    .claimBundle(
      Array.from(claimId),
      "123456",
      "device-fingerprint-smoke-test"
    )
    .accounts({
      claimBundle: claimPDA,
      vault: vaultPDA,
      claimer: claimer.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .signers([claimer])
    .rpc();
  console.log("      OK — CoinPack claimed");

  // 6. Burn note to redemption
  console.log("\n[6/7] Burning note for redemption...");
  await program.methods
    .burnAndRedeem(new anchor.BN(serial), "bc1qdevnettestaddress")
    .accounts({
      note: notePDA,
      vault: vaultPDA,
      holder: wallet.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .rpc();
  console.log("      OK — note burned, redemption queued");

  // 7. Verify vault state
  console.log("\n[7/7] Verifying vault state...");
  const vault = await program.account.vault.fetch(vaultPDA);
  console.log("      total_notes_minted:", vault.totalNotesMinted.toNumber());
  console.log("      total_notes_redeemed:", vault.totalNotesRedeemed.toNumber());
  console.log("      paused:", vault.paused);

  if (vault.totalNotesMinted.toNumber() >= 1 && vault.totalNotesRedeemed.toNumber() >= 1) {
    console.log("\n=== ALL SMOKE TESTS PASSED ===");
  } else {
    console.log("\n=== SMOKE TEST FAILED ===");
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Smoke test failed:", err);
  process.exit(1);
});
