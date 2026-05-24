import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { BitcoinBearerNotes } from "../target/types/bitcoin_bearer_notes";
import { expect } from "chai";
import * as crypto from "crypto";

describe("bitcoin-bearer-notes", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.BitcoinBearerNotes as Program<BitcoinBearerNotes>;
  const authority = provider.wallet as anchor.Wallet;

  const VAULT_SEED = Buffer.from("vault");
  const NOTE_SEED = Buffer.from("note");
  const CLAIM_SEED = Buffer.from("claim");
  const MINT_AUTHORITY_SEED = Buffer.from("mint_authority");

  let vaultPDA: anchor.web3.PublicKey;
  let vaultBump: number;

  before(async () => {
    [vaultPDA, vaultBump] = anchor.web3.PublicKey.findProgramAddressSync(
      [VAULT_SEED],
      program.programId
    );
  });

  it("Initializes the vault", async () => {
    await program.methods
      .initialize()
      .accounts({
        vault: vaultPDA,
        authority: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const vault = await program.account.vault.fetch(vaultPDA);
    expect(vault.authority.toString()).to.equal(authority.publicKey.toString());
    expect(vault.totalNotesMinted.toNumber()).to.equal(0);
    expect(vault.totalNotesRedeemed.toNumber()).to.equal(0);
    expect(vault.paused).to.be.false;
  });

  it("Mints a $10 note", async () => {
    const serial = 1;
    const denomination = new anchor.BN(1_000_000_000); // $10 in sats (at $65k/BTC)
    const metadataUri = "ipfs://QmTest123";

    const [notePDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [NOTE_SEED, new anchor.BN(serial).toArrayLike(Buffer, "le", 8)],
      program.programId
    );

    const [mintAuthorityPDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [MINT_AUTHORITY_SEED],
      program.programId
    );

    await program.methods
      .mintNote(new anchor.BN(serial), denomination, metadataUri)
      .accounts({
        note: notePDA,
        vault: vaultPDA,
        mintAuthority: mintAuthorityPDA,
        holder: authority.publicKey,
        authority: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const note = await program.account.note.fetch(notePDA);
    expect(note.serialNumber.toNumber()).to.equal(serial);
    expect(note.denomination.toNumber()).to.equal(denomination.toNumber());
    expect(note.currentHolder.toString()).to.equal(authority.publicKey.toString());
    expect(note.redeemed).to.be.false;
  });

  it("Transfers note with holder signature", async () => {
    const serial = 1;
    const [notePDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [NOTE_SEED, new anchor.BN(serial).toArrayLike(Buffer, "le", 8)],
      program.programId
    );

    const newHolder = anchor.web3.Keypair.generate();

    await program.methods
      .transferNote(new anchor.BN(serial))
      .accounts({
        note: notePDA,
        vault: vaultPDA,
        newHolder: newHolder.publicKey,
        holder: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const note = await program.account.note.fetch(notePDA);
    expect(note.currentHolder.toString()).to.equal(newHolder.publicKey.toString());
  });

  it("Fails to redeem with wrong holder", async () => {
    const serial = 1;
    const [notePDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [NOTE_SEED, new anchor.BN(serial).toArrayLike(Buffer, "le", 8)],
      program.programId
    );

    const wrongHolder = anchor.web3.Keypair.generate();

    try {
      await program.methods
        .burnAndRedeem(new anchor.BN(serial), "bc1qtestaddress123")
        .accounts({
          note: notePDA,
          vault: vaultPDA,
          holder: wrongHolder.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .signers([wrongHolder])
        .rpc();
      expect.fail("Should have thrown");
    } catch (e: any) {
      expect(e.toString()).to.include("NotNoteHolder");
    }
  });

  it("Redeems note to BTC address", async () => {
    // Transfer back to authority first
    const serial = 1;
    const [notePDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [NOTE_SEED, new anchor.BN(serial).toArrayLike(Buffer, "le", 8)],
      program.programId
    );

    await program.methods
      .transferNote(new anchor.BN(serial))
      .accounts({
        note: notePDA,
        vault: vaultPDA,
        newHolder: authority.publicKey,
        holder: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    await program.methods
      .burnAndRedeem(new anchor.BN(serial), "bc1qredeemaddress456")
      .accounts({
        note: notePDA,
        vault: vaultPDA,
        holder: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const note = await program.account.note.fetch(notePDA);
    expect(note.redeemed).to.be.true;
    expect(note.btcReceivingAddress).to.equal("bc1qredeemaddress456");

    const vault = await program.account.vault.fetch(vaultPDA);
    expect(vault.totalNotesRedeemed.toNumber()).to.equal(1);
  });

  it("Fails double-spend attempt", async () => {
    const serial = 1;
    const [notePDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [NOTE_SEED, new anchor.BN(serial).toArrayLike(Buffer, "le", 8)],
      program.programId
    );

    try {
      await program.methods
        .burnAndRedeem(new anchor.BN(serial), "bc1qanotheraddress789")
        .accounts({
          note: notePDA,
          vault: vaultPDA,
          holder: authority.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .rpc();
      expect.fail("Should have thrown");
    } catch (e: any) {
      expect(e.toString()).to.include("NoteAlreadyRedeemed");
    }
  });

  it("Creates and claims a CoinPack bundle", async () => {
    const claimId = crypto.randomBytes(32);
    const pinHash = anchor.web3.sha256(Buffer.from("123456"));

    const [claimPDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [CLAIM_SEED, claimId],
      program.programId
    );

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
        creator: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const claim = await program.account.claimBundle.fetch(claimPDA);
    expect(claim.creator.toString()).to.equal(authority.publicKey.toString());
    expect(claim.claimed).to.be.false;
    expect(claim.assetTypes).to.deep.equal(["BTC", "USDC"]);

    // Claim it
    const claimer = anchor.web3.Keypair.generate();

    await program.methods
      .claimBundle(
        Array.from(claimId),
        "123456",
        "device-fingerprint-abc123"
      )
      .accounts({
        claimBundle: claimPDA,
        vault: vaultPDA,
        claimer: claimer.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .signers([claimer])
      .rpc();

    const claimed = await program.account.claimBundle.fetch(claimPDA);
    expect(claimed.claimed).to.be.true;
  });

  it("Fails to claim with wrong PIN", async () => {
    const claimId = crypto.randomBytes(32);
    const pinHash = anchor.web3.sha256(Buffer.from("999999"));

    const [claimPDA] = anchor.web3.PublicKey.findProgramAddressSync(
      [CLAIM_SEED, claimId],
      program.programId
    );

    await program.methods
      .createClaimBundle(
        Array.from(claimId),
        ["SOL"],
        [new anchor.BN(100000000)],
        new anchor.BN(Date.now() / 1000 + 86400),
        Array.from(pinHash)
      )
      .accounts({
        claimBundle: claimPDA,
        vault: vaultPDA,
        creator: authority.publicKey,
        systemProgram: anchor.web3.SystemProgram.programId,
      })
      .rpc();

    const claimer = anchor.web3.Keypair.generate();

    try {
      await program.methods
        .claimBundle(
          Array.from(claimId),
          "wrongpin",
          "device-fingerprint-xyz789"
        )
        .accounts({
          claimBundle: claimPDA,
          claimer: claimer.publicKey,
          systemProgram: anchor.web3.SystemProgram.programId,
        })
        .signers([claimer])
        .rpc();
      expect.fail("Should have thrown");
    } catch (e: any) {
      expect(e.toString()).to.include("InvalidPin");
    }
  });
});
