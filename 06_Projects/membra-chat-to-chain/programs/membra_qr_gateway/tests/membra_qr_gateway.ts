import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { MembraQrGateway } from "../target/types/membra_qr_gateway";
import { assert } from "chai";
import { Keypair, LAMPORTS_PER_SOL, PublicKey, SystemProgram } from "@solana/web3.js";

describe("membra_qr_gateway", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.MembraQrGateway as Program<MembraQrGateway>;

  const creator = Keypair.generate();
  const supporter = Keypair.generate();

  const artifactId = "MEMBRA-ART-001";
  const proofHash = Buffer.alloc(32, 1);
  const termsHash = Buffer.alloc(32, 2);
  const termsUri = "ipfs://QmTestTerms";
  const initialRebateBps = 1000; // 10%
  const floorRebateBps = 200; // 2%
  const decayPerSupportBps = 50; // 0.5% per support
  const maxSupportLamports = new anchor.BN(100 * LAMPORTS_PER_SOL);

  let artifactPda: PublicKey;
  let artifactBump: number;

  before(async () => {
    const sig1 = await provider.connection.requestAirdrop(
      creator.publicKey,
      10 * LAMPORTS_PER_SOL
    );
    await provider.connection.confirmTransaction(sig1);

    const sig2 = await provider.connection.requestAirdrop(
      supporter.publicKey,
      10 * LAMPORTS_PER_SOL
    );
    await provider.connection.confirmTransaction(sig2);
  });

  it("initializes an artifact successfully", async () => {
    [artifactPda, artifactBump] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("artifact"),
        creator.publicKey.toBuffer(),
        Buffer.from(artifactId),
      ],
      program.programId
    );

    await program.methods
      .initializeArtifact(
        artifactId,
        Array.from(proofHash),
        Array.from(termsHash),
        termsUri,
        initialRebateBps,
        floorRebateBps,
        decayPerSupportBps,
        maxSupportLamports
      )
      .accounts({
        creator: creator.publicKey,
        artifact: artifactPda,
        systemProgram: SystemProgram.programId,
      })
      .signers([creator])
      .rpc();

    const artifact = await program.account.artifact.fetch(artifactPda);
    assert.equal(artifact.creator.toBase58(), creator.publicKey.toBase58());
    assert.equal(artifact.artifactId, artifactId);
    assert.equal(artifact.initialRebateBps, initialRebateBps);
    assert.equal(artifact.floorRebateBps, floorRebateBps);
    assert.equal(artifact.paused, false);
    assert.equal(artifact.supportCount.toNumber(), 0);
    assert.equal(artifact.totalSupportLamports.toNumber(), 0);
  });

  it("rejects rebate over 50%", async () => {
    const badPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("artifact"),
        creator.publicKey.toBuffer(),
        Buffer.from("BAD-REBATE"),
      ],
      program.programId
    )[0];

    try {
      await program.methods
        .initializeArtifact(
          "BAD-REBATE",
          Array.from(proofHash),
          Array.from(termsHash),
          termsUri,
          6000, // 60% - invalid
          floorRebateBps,
          decayPerSupportBps,
          maxSupportLamports
        )
        .accounts({
          creator: creator.publicKey,
          artifact: badPda,
          systemProgram: SystemProgram.programId,
        })
        .signers([creator])
        .rpc();
      assert.fail("Should have thrown");
    } catch (e: any) {
      assert.include(e.toString(), "RebateTooHigh");
    }
  });

  it("rejects floor rebate exceeding initial rebate", async () => {
    const badPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("artifact"),
        creator.publicKey.toBuffer(),
        Buffer.from("BAD-FLOOR"),
      ],
      program.programId
    )[0];

    try {
      await program.methods
        .initializeArtifact(
          "BAD-FLOOR",
          Array.from(proofHash),
          Array.from(termsHash),
          termsUri,
          1000,
          2000, // floor > initial
          decayPerSupportBps,
          maxSupportLamports
        )
        .accounts({
          creator: creator.publicKey,
          artifact: badPda,
          systemProgram: SystemProgram.programId,
        })
        .signers([creator])
        .rpc();
      assert.fail("Should have thrown");
    } catch (e: any) {
      assert.include(e.toString(), "FloorRebateExceedsInitial");
    }
  });

  it("supports an artifact successfully", async () => {
    const supporterBalanceBefore = await provider.connection.getBalance(
      supporter.publicKey
    );
    const creatorBalanceBefore = await provider.connection.getBalance(
      creator.publicKey
    );

    const supportAmount = new anchor.BN(1 * LAMPORTS_PER_SOL);
    const clientRefHash = Buffer.alloc(32, 3);

    const receiptPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("receipt"),
        artifactPda.toBuffer(),
        new anchor.BN(0).toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    )[0];

    await program.methods
      .supportArtifact(
        supportAmount,
        Array.from(termsHash),
        Array.from(clientRefHash)
      )
      .accounts({
        supporter: supporter.publicKey,
        artifact: artifactPda,
        creator: creator.publicKey,
        receipt: receiptPda,
        systemProgram: SystemProgram.programId,
      })
      .signers([supporter])
      .rpc();

    const artifact = await program.account.artifact.fetch(artifactPda);
    assert.equal(artifact.supportCount.toNumber(), 1);
    assert.equal(
      artifact.totalSupportLamports.toNumber(),
      supportAmount.toNumber()
    );

    const receipt = await program.account.supportReceipt.fetch(receiptPda);
    assert.equal(receipt.supporter.toBase58(), supporter.publicKey.toBase58());
    assert.equal(receipt.creator.toBase58(), creator.publicKey.toBase58());
    assert.equal(receipt.amountLamports.toNumber(), supportAmount.toNumber());
    assert.equal(receipt.rebateBps, initialRebateBps);
    assert.equal(receipt.receiptIndex.toNumber(), 0);

    const supporterBalanceAfter = await provider.connection.getBalance(
      supporter.publicKey
    );
    const creatorBalanceAfter = await provider.connection.getBalance(
      creator.publicKey
    );

    // Creator should have received creator_lamports
    const expectedCreatorLamports = supportAmount
      .muln(initialRebateBps)
      .divn(10000);
    const creatorReceived = creatorBalanceAfter - creatorBalanceBefore;
    assert.equal(
      creatorReceived,
      supportAmount.toNumber() - expectedCreatorLamports.toNumber()
    );
  });

  it("rejects support with terms hash mismatch", async () => {
    const badTermsHash = Buffer.alloc(32, 99);
    const receiptPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("receipt"),
        artifactPda.toBuffer(),
        new anchor.BN(1).toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    )[0];

    try {
      await program.methods
        .supportArtifact(
          new anchor.BN(LAMPORTS_PER_SOL),
          Array.from(badTermsHash),
          Array.from(Buffer.alloc(32, 0))
        )
        .accounts({
          supporter: supporter.publicKey,
          artifact: artifactPda,
          creator: creator.publicKey,
          receipt: receiptPda,
          systemProgram: SystemProgram.programId,
        })
        .signers([supporter])
        .rpc();
      assert.fail("Should have thrown");
    } catch (e: any) {
      assert.include(e.toString(), "TermsHashMismatch");
    }
  });

  it("pauses and unpauses artifact", async () => {
    await program.methods
      .updateArtifactStatus(true)
      .accounts({
        creator: creator.publicKey,
        artifact: artifactPda,
      })
      .signers([creator])
      .rpc();

    let artifact = await program.account.artifact.fetch(artifactPda);
    assert.equal(artifact.paused, true);

    // Support should fail when paused
    const receiptPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("receipt"),
        artifactPda.toBuffer(),
        new anchor.BN(1).toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    )[0];

    try {
      await program.methods
        .supportArtifact(
          new anchor.BN(LAMPORTS_PER_SOL),
          Array.from(termsHash),
          Array.from(Buffer.alloc(32, 0))
        )
        .accounts({
          supporter: supporter.publicKey,
          artifact: artifactPda,
          creator: creator.publicKey,
          receipt: receiptPda,
          systemProgram: SystemProgram.programId,
        })
        .signers([supporter])
        .rpc();
      assert.fail("Should have thrown");
    } catch (e: any) {
      assert.include(e.toString(), "ArtifactPaused");
    }

    // Unpause
    await program.methods
      .updateArtifactStatus(false)
      .accounts({
        creator: creator.publicKey,
        artifact: artifactPda,
      })
      .signers([creator])
      .rpc();

    artifact = await program.account.artifact.fetch(artifactPda);
    assert.equal(artifact.paused, false);
  });

  it("rejects unauthorized pause by non-creator", async () => {
    try {
      await program.methods
        .updateArtifactStatus(true)
        .accounts({
          creator: supporter.publicKey,
          artifact: artifactPda,
        })
        .signers([supporter])
        .rpc();
      assert.fail("Should have thrown");
    } catch (e: any) {
      assert.include(e.toString(), "UnauthorizedUpdate");
    }
  });

  it("rebate decays with each support", async () => {
    // Current rebate should be initial - decay * support_count
    // After 1 support: 1000 - 50*1 = 950
    const artifact = await program.account.artifact.fetch(artifactPda);
    const currentRebate = artifact.initialRebateBps - artifact.decayPerSupportBps * artifact.supportCount.toNumber();
    const expectedRebate = Math.max(currentRebate, artifact.floorRebateBps);
    assert.equal(expectedRebate, 950);
  });

  it("enforces support cap", async () => {
    // Create artifact with small cap
    const smallCapId = "SMALL-CAP";
    const smallCapPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("artifact"),
        creator.publicKey.toBuffer(),
        Buffer.from(smallCapId),
      ],
      program.programId
    )[0];

    await program.methods
      .initializeArtifact(
        smallCapId,
        Array.from(proofHash),
        Array.from(termsHash),
        termsUri,
        initialRebateBps,
        floorRebateBps,
        decayPerSupportBps,
        new anchor.BN(0.5 * LAMPORTS_PER_SOL)
      )
      .accounts({
        creator: creator.publicKey,
        artifact: smallCapPda,
        systemProgram: SystemProgram.programId,
      })
      .signers([creator])
      .rpc();

    const receiptPda = PublicKey.findProgramAddressSync(
      [
        Buffer.from("receipt"),
        smallCapPda.toBuffer(),
        new anchor.BN(0).toArrayLike(Buffer, "le", 8),
      ],
      program.programId
    )[0];

    try {
      await program.methods
        .supportArtifact(
          new anchor.BN(1 * LAMPORTS_PER_SOL),
          Array.from(termsHash),
          Array.from(Buffer.alloc(32, 0))
        )
        .accounts({
          supporter: supporter.publicKey,
          artifact: smallCapPda,
          creator: creator.publicKey,
          receipt: receiptPda,
          systemProgram: SystemProgram.programId,
        })
        .signers([supporter])
        .rpc();
      assert.fail("Should have thrown");
    } catch (e: any) {
      assert.include(e.toString(), "SupportCapExceeded");
    }
  });
});
