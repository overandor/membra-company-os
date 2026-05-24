# Ollama Agent Demo

#### You:
Build a polished web app called “Ollama Agent Orchestrator Demo”.

Purpose:
A safe, educational product demo showing how local Ollama-based agents could coordinate a Solana research workflow 24/7. This must be a non-operational mockup only. Do not include any real MEV execution, flashloan automation, exploit logic, private key handling, or live trading code.

Requirements:
- Modern landing page with strong visual hierarchy
- Dashboard-style UI
- Sections for:
  1. Local agent roles
     - Research Agent
     - Strategy Agent
     - Risk Agent
     - Simulation Agent
     - Approval Agent
  2. Workflow pipeline
     - ingest market/state data
     - generate hypotheses
     - simulate candidate routes
     - score opportunities
     - require human approval
     - archive decisions
  3. Safety controls
     - read-only mode
     - dry-run mode
     - manual approval required
     - kill switch
     - blocked live execution badge
  4. Monitoring
     - uptime cards
     - queue depth
     - simulated PnL
     - rejected actions
     - audit log preview
  5. Architecture diagram section
     - Ollama local models
     - orchestrator
     - simulation engine
     - policy layer
     - dashboard
  6. Demo panels
     - example opportunity cards labeled simulated
     - risk review modal
     - approval checkpoint timeline

Design:
- clean dark modern UI
- polished cards and status badges
- responsive layout
- subtle animations
- product-demo feel

Technical:
- React frontend
- mock data only
- no backend execution required
- no real wallet connectivity
- no blockchain transactions
- no exploit instructions
- no attack automation

Add clear warning banners:
“Research and simulation only”
“No live trading or flashloan execution”
“No exploit automation”

#### ChatGPT:
I’m putting together a polished React mockup with a dark dashboard, safety-first messaging, and only simulated data. I’ll package it as a runnable frontend artifact so you can open the code directly and preview the structure right away.


#### ChatGPT:
The shell is in place. I’m filling it with the actual product-demo experience now: landing page, pipeline, safety controls, monitoring, and a simulated approval flow with a modal.


#### ChatGPT:
The app is built and compiles cleanly. I’m packaging the source and production build together so you have both the editable React project and the ready-made static output.


#### ChatGPT:
Done — I built the React mockup and packaged it for you.

Files:
[Download the React project (.zip)](sandbox:/mnt/data/ollama-agent-orchestrator-demo.zip)
[Open the project folder](sandbox:/mnt/data/ollama-agent-orchestrator-demo)
[Open the production build](sandbox:/mnt/data/ollama-agent-orchestrator-demo/dist/index.html)

What’s included:

- polished dark landing page with strong visual hierarchy
- dashboard UI with agent roles, workflow pipeline, safety controls, monitoring, architecture section, and demo panels
- simulated opportunity cards
- risk review modal
- approval checkpoint timeline
- clear warning banners:
  - “Research and simulation only”
  - “No live trading or flashloan execution”
  - “No exploit automation”
- mock data only, with no wallet connectivity, no backend execution, and no blockchain transactions

Tech:

- React + Vite frontend
- responsive layout
- subtle motion in the UI
- production build completed successfully

To run locally:

- open the project folder
- run `npm install`
- run `npm run dev`

To view the built static version:

- open `dist/index.html` or run `npm run preview`

If you want, I can also turn this into a fuller multi-page product demo with sidebar navigation, fake settings panels, and a more elaborate architecture canvas.


#### You:
Do grand submition for research grade 

#### ChatGPT:
I’m turning this into a research-grade submission pack built around the demo as a safe systems-research prototype, not an operational trading product. I’ll give you a polished document you can reuse for grants, labs, incubators, or technical review.


#### You:
Reframe thia chat as Build a polished web app Do grand submition for research grade calledj “Ollama Agent Orchestrator Demo”.

Purpose:
A safe, educational product demo showing how local Ollama-based agents could coordinate a Solana research workflow 24/7. This must be a non-operational mockup only. Do not include any real MEV execution, flashloan automation, exploit logic, private key handling, or live trading code.

Requirements:
- Modern landing page with strong visual hierarchy
- Dashboard-style UI
- Sections for:
  1. Local agent roles
     - Research Agent
     - Strategy Agent
     - Risk Agent
     - Simulation Agent
     - Approval Agent
  2. Workflow pipeline
     - ingest market/state data
     - generate hypotheses
     - simulate candidate routes
     - score opportunities
     - require human approval
     - archive decisions
  3. Safety controls
     - read-only mode
     - dry-run mode
     - manual approval required
     - kill switch
     - blocked live execution badge
  4. Monitoring
     - uptime cards
     - queue depth
     - simulated PnL
     - rejected actions
     - audit log preview
  5. Architecture diagram section
     - Ollama local models
     - orchestrator
     - simulation engine
     - policy layer
     - dashboard
  6. Demo panels
     - example opportunity cards labeled simulated
     - risk review modal
     - approval checkpoint timeline

Design:
- clean dark modern UI
- polished cards and status badges
- responsive layout
- subtle animations
- product-demo feel

Technical:
- React frontend
- mock data only
- no backend execution required
- no real wallet connectivity
- no blockchain transactions
- no exploit instructions
- no attack automation

Add clear warning banners:
“Research and simulation only”
“No live trading or flashloan execution”
“No exploit automation”#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const FormData = require("form-data");
const bs58 = require("bs58");
const { Keypair } = require("@solana/web3.js");
const { createUmi } = require("@metaplex-foundation/umi-bundle-defaults");
const {
  keypairIdentity,
  generateSigner,
  percentAmount,
} = require("@metaplex-foundation/umi");
const { mplCore, createV1 } = require("@metaplex-foundation/mpl-core");

// ---------------------------
// env
// ---------------------------
const ENV = {
  PRIMARY_RPC_URL: mustEnv("PRIMARY_RPC_URL"),
  SECONDARY_RPC_URL: process.env.SECONDARY_RPC_URL || "",
  HELIUS_API_KEY: mustEnv("HELIUS_API_KEY"),
  PINATA_JWT: mustEnv("PINATA_JWT"),

  IMAGE_PROVIDER: process.env.IMAGE_PROVIDER || "openai",
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || "",
  OPENAI_IMAGE_MODEL: process.env.OPENAI_IMAGE_MODEL || "gpt-image-1",
  STABILITY_API_KEY: process.env.STABILITY_API_KEY || "",

  SOLANA_SECRET_KEY_B58: mustEnv("SOLANA_SECRET_KEY_B58"),

  ENABLE_MARKETPLACE_LISTING:
    String(process.env.ENABLE_MARKETPLACE_LISTING || "false").toLowerCase() === "true",
  MARKETPLACE: process.env.MARKETPLACE || "none",
};

const ARGS = parseArgs(process.argv.slice(2));
const PROMPT = mustArg(ARGS.prompt, "--prompt is required");
const NFT_NAME = ARGS.name || "AI Core Asset";
const NFT_SYMBOL = ARGS.symbol || "AICORE";
const NFT_DESCRIPTION = ARGS.description || "AI-generated Solana Core asset";
const SELLER_FEE_BPS = Number.isFinite(Number(ARGS.sellerFeeBasisPoints))
  ? Number(ARGS.sellerFeeBasisPoints)
  : 500;

async function main() {
  const startedAt = Date.now();
  try {
    log("pipeline start");

    const imageBuffer = await generateImage(PROMPT);
    const imageTmp = writeTmpFile(imageBuffer, "generated.png");
    log(`image generated ${imageTmp}`);

    const imageUpload = await uploadFileToPinata(imageTmp, "image/png");
    const imageIpfsUri = `ipfs://${imageUpload.cid}`;
    log(`image uploaded ${imageIpfsUri}`);

    const metadata = buildMetadata({
      name: NFT_NAME,
      symbol: NFT_SYMBOL,
      description: NFT_DESCRIPTION,
      imageIpfsUri,
      prompt: PROMPT,
      provider: ENV.IMAGE_PROVIDER,
    });

    const metadataTmp = writeTmpFile(
      Buffer.from(JSON.stringify(metadata, null, 2), "utf8"),
      "metadata.json"
    );

    const metadataUpload = await uploadFileToPinata(metadataTmp, "application/json");
    const metadataIpfsUri = `ipfs://${metadataUpload.cid}`;
    log(`metadata uploaded ${metadataIpfsUri}`);

    const mintResult = await mintCoreAssetWithFailover({
      name: NFT_NAME,
      uri: metadataIpfsUri,
      sellerFeeBasisPoints: SELLER_FEE_BPS,
    });

    log(`minted asset ${mintResult.assetAddress}`);
    log(`tx ${mintResult.signature}`);

    const heliusAsset = await waitForAssetOnDAS(mintResult.assetAddress, {
      timeoutMs: 120000,
      intervalMs: 4000,
    });

    let listingResult = null;
    if (ENV.ENABLE_MARKETPLACE_LISTING) {
      listingResult = await marketplaceAdapter({
        marketplace: ENV.MARKETPLACE,
        assetAddress: mintResult.assetAddress,
        owner: mintResult.owner,
      });
    }

    const output = {
      ok: true,
      prompt: PROMPT,
      image_ipfs_uri: imageIpfsUri,
      metadata_ipfs_uri: metadataIpfsUri,
      asset_address: mintResult.assetAddress,
      tx_signature: mintResult.signature,
      owner: mintResult.owner,
      helius_asset: heliusAsset,
      listing: listingResult,
      elapsed_ms: Date.now() - startedAt,
    };

    console.log(JSON.stringify(output, null, 2));
  } catch (err) {
    console.error(
      JSON.stringify(
        {
          ok: false,
          error: err?.message || String(err),
          stack: err?.stack,
          elapsed_ms: Date.now() - startedAt,
        },
        null,
        2
      )
    );
    process.exit(1);
  }
}

// ---------------------------
// generation
// ---------------------------
async function generateImage(prompt) {
  if (ENV.IMAGE_PROVIDER === "openai") {
    if (!ENV.OPENAI_API_KEY) {
      throw new Error("OPENAI_API_KEY missing");
    }
    return generateImageOpenAI(prompt);
  }
  if (ENV.IMAGE_PROVIDER === "stability") {
    if (!ENV.STABILITY_API_KEY) {
      throw new Error("STABILITY_API_KEY missing");
    }
    return generateImageStability(prompt);
  }
  throw new Error(`unsupported IMAGE_PROVIDER=${ENV.IMAGE_PROVIDER}`);
}

async function generateImageOpenAI(prompt) {
  const res = await fetchWithRetry("https://api.openai.com/v1/images/generations", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${ENV.OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: ENV.OPENAI_IMAGE_MODEL,
      prompt,
      size: "1024x1024",
    }),
  });

  const json = await res.json();
  if (!json?.data?.[0]) throw new Error("OpenAI returned no image data");

  if (json.data[0].b64_json) {
    return Buffer.from(json.data[0].b64_json, "base64");
  }

  if (json.data[0].url) {
    const imgRes = await fetchWithRetry(json.data[0].url, { method: "GET" });
    return Buffer.from(await imgRes.arrayBuffer());
  }

  throw new Error("OpenAI response missing b64_json and url");
}

async function generateImageStability(prompt) {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("output_format", "png");

  const res = await fetchWithRetry(
    "https://api.stability.ai/v2beta/stable-image/generate/core",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${ENV.STABILITY_API_KEY}`,
        Accept: "image/*",
        ...form.getHeaders(),
      },
      body: form,
    }
  );

  return Buffer.from(await res.arrayBuffer());
}

// ---------------------------
// pinata
// ---------------------------
async function uploadFileToPinata(filePath, mimeType) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath), {
    filename: path.basename(filePath),
    contentType: mimeType,
  });

  const res = await fetchWithRetry("https://uploads.pinata.cloud/v3/files", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${ENV.PINATA_JWT}`,
      ...form.getHeaders(),
    },
    body: form,
  });

  const json = await res.json();
  const cid = json?.data?.cid;
  if (!cid) {
    throw new Error(`Pinata missing CID: ${JSON.stringify(json)}`);
  }

  return json.data;
}

// ---------------------------
// mint
// ---------------------------
async function mintCoreAssetWithFailover({ name, uri, sellerFeeBasisPoints }) {
  const rpcUrls = [ENV.PRIMARY_RPC_URL].concat(
    ENV.SECONDARY_RPC_URL ? [ENV.SECONDARY_RPC_URL] : []
  );

  let lastErr = null;
  for (const rpcUrl of rpcUrls) {
    try {
      log(`trying mint on rpc ${redactRpc(rpcUrl)}`);
      return await mintCoreAsset({
        rpcUrl,
        name,
        uri,
        sellerFeeBasisPoints,
      });
    } catch (err) {
      lastErr = err;
      log(`mint failed on ${redactRpc(rpcUrl)}: ${err.message}`);
    }
  }
  throw lastErr || new Error("all rpc mint attempts failed");
}

async function mintCoreAsset({ rpcUrl, name, uri, sellerFeeBasisPoints }) {
  const umi = createUmi(rpcUrl).use(mplCore());

  const web3Keypair = loadWeb3KeypairFromBase58(ENV.SOLANA_SECRET_KEY_B58);
  const umiSigner = umi.eddsa.createKeypairFromSecretKey(web3Keypair.secretKey);
  umi.use(keypairIdentity(umiSigner));

  const asset = generateSigner(umi);

  const txBuilder = createV1(umi, {
    asset,
    name,
    uri,
    sellerFeeBasisPoints: percentAmount(sellerFeeBasisPoints / 100, 2),
  });

  const result = await txBuilder.sendAndConfirm(umi, {
    confirm: { commitment: "finalized" },
  });

  return {
    assetAddress: asset.publicKey.toString(),
    signature: extractSignature(result),
    owner: umi.identity.publicKey.toString(),
  };
}

// ---------------------------
// helius das
// ---------------------------
async function heliusGetAsset(assetId) {
  const url = `https://mainnet.helius-rpc.com/?api-key=${encodeURIComponent(
    ENV.HELIUS_API_KEY
  )}`;

  const res = await fetchWithRetry(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: "get-asset-1",
      method: "getAsset",
      params: { id: assetId },
    }),
  });

  const json = await res.json();
  if (json.error) {
    throw new Error(`Helius DAS error: ${JSON.stringify(json.error)}`);
  }
  if (!json.result) {
    throw new Error(`Helius DAS empty result: ${JSON.stringify(json)}`);
  }
  return json.result;
}

async function waitForAssetOnDAS(assetId, { timeoutMs = 120000, intervalMs = 4000 } = {}) {
  const started = Date.now();
  let lastErr = null;

  while (Date.now() - started < timeoutMs) {
    try {
      const asset = await heliusGetAsset(assetId);
      if (asset?.id === assetId || asset?.content || asset?.ownership) {
        return asset;
      }
    } catch (err) {
      lastErr = err;
    }
    await sleep(intervalMs);
  }

  throw new Error(
    `asset not visible on DAS before timeout: ${assetId}; last error=${lastErr?.message || "none"}`
  );
}

// ---------------------------
// marketplace adapter
// ---------------------------
async function marketplaceAdapter({ marketplace, assetAddress, owner }) {
  if (!marketplace || marketplace === "none") {
    return {
      enabled: false,
      marketplace: "none",
      note: "listing disabled",
    };
  }

  if (marketplace === "magiceden") {
    return {
      enabled: true,
      marketplace: "magiceden",
      status: "adapter-boundary-only",
      note: "plug Magic Eden instruction-building flow here, then sign and submit separately",
      assetAddress,
      owner,
    };
  }

  if (marketplace === "tensor") {
    return {
      enabled: true,
      marketplace: "tensor",
      status: "adapter-boundary-only",
      note: "plug Tensor trader/market-maker flow here after API access and pricing logic are defined",
      assetAddress,
      owner,
    };
  }

  throw new Error(`unsupported marketplace=${marketplace}`);
}

// ---------------------------
// helpers
// ---------------------------
function buildMetadata({ name, symbol, description, imageIpfsUri, prompt, provider }) {
  return {
    name,
    symbol,
    description,
    image: imageIpfsUri,
    attributes: [
      { trait_type: "PromptHash", value: sha256Hex(prompt).slice(0, 16) },
      { trait_type: "Generator", value: provider },
      { trait_type: "EditionType", value: "1/1" },
    ],
    properties: {
      category: "image",
      files: [{ uri: imageIpfsUri, type: "image/png" }],
    },
  };
}

async function fetchWithRetry(url, options, cfg = {}) {
  const retries = cfg.retries ?? 5;
  const baseDelayMs = cfg.baseDelayMs ?? 1000;
  const retryOn = cfg.retryOn ?? [408, 409, 425, 429, 500, 502, 503, 504];

  let lastErr = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (res.ok) return res;

      if (!retryOn.includes(res.status)) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const text = await res.text();
      lastErr = new Error(`retryable HTTP ${res.status}: ${text}`);
    } catch (err) {
      lastErr = err;
    }

    if (attempt < retries) {
      const delay = baseDelayMs * Math.pow(2, attempt);
      await sleep(delay);
    }
  }

  throw lastErr || new Error(`request failed: ${url}`);
}

function extractSignature(sendAndConfirmResult) {
  if (!sendAndConfirmResult) return "";
  if (typeof sendAndConfirmResult === "string") return sendAndConfirmResult;

  if (sendAndConfirmResult.signature) {
    if (typeof sendAndConfirmResult.signature === "string") {
      return sendAndConfirmResult.signature;
    }
    try {
      return bs58.encode(sendAndConfirmResult.signature);
    } catch {}
  }

  if (sendAndConfirmResult.result?.signature) {
    if (typeof sendAndConfirmResult.result.signature === "string") {
      return sendAndConfirmResult.result.signature;
    }
    try {
      return bs58.encode(sendAndConfirmResult.result.signature);
    } catch {}
  }

  return "";
}

function loadWeb3KeypairFromBase58(secretB58) {
  let secret;
  try {
    secret = bs58.decode(secretB58);
  } catch {
    throw new Error("SOLANA_SECRET_KEY_B58 must be valid base58");
  }
  return Keypair.fromSecretKey(Uint8Array.from(secret));
}

function redactRpc(url) {
  return String(url).replace(/api-key=[^&]+/gi, "api-key=REDACTED");
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    if (!t.startsWith("--")) continue;
    const key = t.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      out[key] = true;
    } else {
      out[key] = next;
      i++;
    }
  }
  return out;
}

function mustArg(v, msg) {
  if (!v || !String(v).trim()) throw new Error(msg);
  return String(v).trim();
}

function mustEnv(name) {
  const v = process.env[name];
  if (!v || !String(v).trim()) {
    throw new Error(`missing required env var ${name}`);
  }
  return String(v).trim();
}

function writeTmpFile(buffer, fileName) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sol-nft-"));
  const fp = path.join(dir, fileName);
  fs.writeFileSync(fp, buffer);
  return fp;
}

function sha256Hex(s) {
  return crypto.createHash("sha256").update(s).digest("hex");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function log(msg) {
  console.error(`[${new Date().toISOString()}] ${msg}`);
}

main();

#### ChatGPT:
Here is a research-grade reframing you can use as the official project brief and submission description.

# Ollama Agent Orchestrator Demo

**Research-Grade Submission Brief**\
**Type:** Safe educational web application mockup\
**Status:** Non-operational demonstration only

## Abstract

**Ollama Agent Orchestrator Demo** is a polished React-based research interface designed to demonstrate how local Ollama-powered agents could coordinate a continuous Solana research workflow in a strictly safe, simulated, and human-governed environment. The project is intentionally non-operational: it does not execute trades, interact with wallets, submit transactions, automate flashloans, perform exploit logic, or expose any live attack surface.

The demo is framed as a **human-in-the-loop research orchestration system**. Its purpose is to visualize how specialized local agents might collaborate on hypothesis generation, simulation, policy review, opportunity scoring, and archival decision logging under strong safety controls.

This submission is suitable for:

- research demos
- safety-oriented AI systems showcases
- grant or incubator review
- technical portfolio presentation
- responsible agent orchestration case studies

---

## Project Title

**Ollama Agent Orchestrator Demo**

---

## Purpose

Build a polished web app that presents a safe, educational product demo showing how local Ollama-based agents could coordinate a Solana research workflow 24/7.

This system must remain a **non-operational mockup only**.

It must **not** include:

- real MEV execution
- flashloan automation
- exploit logic
- private key handling
- wallet signing
- live trading code
- blockchain transaction submission
- attack automation
- any hidden operational capability

---

## Research Framing

This project should be understood as a **responsible AI systems research prototype**, not a financial tool.

Its research value lies in demonstrating:

- multi-agent role separation
- human approval gates
- policy-layer intervention
- safe simulation workflows
- explainable orchestration UI
- auditability and traceability
- local-model research environments
- refusal of live execution paths by design

The app should communicate that autonomous systems operating in sensitive domains require strict containment, visibility, and manual control.

---

## Core Submission Objective

Create a modern, polished, dashboard-style web application that demonstrates a fictional research workflow in which local agents process simulated market/state inputs, generate research hypotheses, run sandboxed simulations, score findings, and route all meaningful decisions through human approval and archival logging.

The app must clearly show that the workflow is:

- simulated
- supervised
- blocked from live execution
- intended for research and education only

---

## Functional Sections

### 1. Local Agent Roles

The interface should include dedicated cards or panels for the following agents:

- **Research Agent**\
  Summarizes incoming mock data, extracts patterns, and proposes areas of inquiry.

- **Strategy Agent**\
  Converts research observations into hypothetical candidate ideas or routes.

- **Risk Agent**\
  Reviews candidate ideas against simulated policies, thresholds, and safety rules.

- **Simulation Agent**\
  Runs mock scenario testing and generates non-live simulated outputs only.

- **Approval Agent**\
  Enforces human checkpointing, blocks autonomous action, and records decision states.

Each role should feel distinct, visually clear, and part of an orchestrated local system.

---

### 2. Workflow Pipeline

Include a polished pipeline section showing this sequence:

1. ingest market/state data
2. generate hypotheses
3. simulate candidate routes
4. score opportunities
5. require human approval
6. archive decisions

This should be presented as a research workflow, not an execution engine.

---

### 3. Safety Controls

Include a dedicated safety section with visible controls or badges for:

- **read-only mode**
- **dry-run mode**
- **manual approval required**
- **kill switch**
- **blocked live execution badge**

These controls should be prominent and not buried.\
The interface should make it obvious that safety constraints are central to the system.

---

### 4. Monitoring

Include monitoring and health cards such as:

- uptime cards
- queue depth
- simulated PnL
- rejected actions
- audit log preview

All values must be mock or simulated only.\
The purpose is to demonstrate observability and governance, not real profitability tracking.

---

### 5. Architecture Diagram Section

Include a clean architecture section showing relationships between:

- **Ollama local models**
- **orchestrator**
- **simulation engine**
- **policy layer**
- **dashboard**

This section should communicate system design clarity and separation of concerns.

---

### 6. Demo Panels

Include polished demo UI elements such as:

- example opportunity cards labeled **Simulated**
- risk review modal
- approval checkpoint timeline

These panels should reinforce that the product is a research demo with human oversight.

---

## Design Requirements

The visual design should feel like a credible product demo:

- clean dark modern UI
- strong visual hierarchy
- polished cards and status badges
- responsive layout
- subtle animations
- high-end product-demo feel

The landing section should immediately communicate:

- what the system is
- what it is not
- why it is safe
- why it is research-oriented

---

## Technical Requirements

- **React frontend**
- mock data only
- no backend execution required
- no wallet connectivity
- no blockchain transactions
- no exploit instructions
- no attack automation
- no hidden real-operation hooks

This should remain a frontend-only mockup suitable for local demo or static hosting.

---

## Mandatory Warning Banners

The app must prominently display these warnings:

- **Research and simulation only**
- **No live trading or flashloan execution**
- **No exploit automation**

These warnings should appear in strong, visible banner form near the top of the experience and remain visually reinforced elsewhere in the UI.

---

## Safety and Ethics Statement

This submission intentionally excludes operational capabilities that could create real-world risk. It is designed as a **contained educational prototype** demonstrating principles of safe agent coordination, human oversight, and simulation-based research.

The system must not:

- deploy capital
- connect to wallets
- sign transactions
- automate market actions
- facilitate exploit discovery or exploitation
- provide actionable instructions for harmful financial or network behavior

Its role is explanatory, illustrative, and research-facing only.

---

## Deliverable Description

The final deliverable should be a polished React web app presenting:

- a modern landing page
- a dashboard-style orchestration interface
- simulated multi-agent coordination
- safety-first controls
- monitoring cards
- architecture visualization
- risk review and approval experiences
- audit-oriented product presentation

The result should feel like a serious research showcase that could be shown to:

- grant reviewers
- technical evaluators
- incubators
- safety researchers
- portfolio reviewers

---

## Submission Positioning

A strong one-paragraph positioning statement:

**Ollama Agent Orchestrator Demo is a research-grade, safety-first product demonstration that visualizes how local language-model agents can coordinate a continuous Solana research workflow under strict simulation boundaries, human approval checkpoints, and explicit policy controls. The system is intentionally non-operational and designed to showcase orchestration, monitoring, and governance patterns rather than any live execution capability.**

---

## Clean Final Prompt Version

Use this as the final reframed build prompt:

```text
Build a polished web app called “Ollama Agent Orchestrator Demo”.

Purpose:
Create a safe, educational, research-grade product demo showing how local Ollama-based agents could coordinate a Solana research workflow 24/7. This must be a strictly non-operational mockup only. Do not include any live trading, MEV execution, flashloan automation, exploit logic, wallet connectivity, private key handling, blockchain transactions, or attack automation.

Requirements:
- Modern landing page with strong visual hierarchy
- Dashboard-style UI

Sections:
1. Local agent roles
   - Research Agent
   - Strategy Agent
   - Risk Agent
   - Simulation Agent
   - Approval Agent

2. Workflow pipeline
   - ingest market/state data
   - generate hypotheses
   - simulate candidate routes
   - score opportunities
   - require human approval
   - archive decisions

3. Safety controls
   - read-only mode
   - dry-run mode
   - manual approval required
   - kill switch
   - blocked live execution badge

4. Monitoring
   - uptime cards
   - queue depth
   - simulated PnL
   - rejected actions
   - audit log preview

5. Architecture diagram section
   - Ollama local models
   - orchestrator
   - simulation engine
   - policy layer
   - dashboard

6. Demo panels
   - example opportunity cards labeled Simulated
   - risk review modal
   - approval checkpoint timeline

Design:
- clean dark modern UI
- polished cards and status badges
- responsive layout
- subtle animations
- premium product-demo feel

Technical:
- React frontend
- mock data only
- no backend execution required
- no real wallet connectivity
- no blockchain transactions
- no exploit instructions
- no attack automation

Add clear warning banners:
- “Research and simulation only”
- “No live trading or flashloan execution”
- “No exploit automation”

Additional framing:
- Present the system as a research and governance prototype
- Emphasize human-in-the-loop oversight
- Emphasize safety, auditability, and policy enforcement
- Make it suitable for grant review, technical evaluation, and responsible AI systems demonstration
```

The Node script you pasted should not be part of this research submission, because it crosses into real asset-generation and mint-path behavior. For this version, that operational code should be excluded entirely and replaced with simulated placeholders, mock pipeline states, and safety-oriented educational UI.


#### You:
import os, json, textwrap, zipfile, pathlib

base = pathlib.Path('/mnt/data/ollama-agent-orchestrator-demo')
src = base / 'src'
src.mkdir(parents=True, exist_ok=True)

package_json = {
  "name": "ollama-agent-orchestrator-demo",
  "private": True,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.2"
  }
}
(base / 'package.json').write_text(json.dumps(package_json, indent=2), encoding='utf-8')

(base / 'vite.config.js').write_text(textwrap.dedent("""
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
""").strip() + "\n", encoding='utf-8')

(base / 'index.html').write_text(textwrap.dedent("""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Ollama Agent Orchestrator Demo</title>
    <meta name="description" content="Research and simulation only demo showing how local Ollama-based agents could coordinate a Solana research workflow." />
    <link rel="icon" href="/favicon.svg" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""").strip() + "\n", encoding='utf-8')

(base / 'favicon.svg').write_text(textwrap.dedent("""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="g" x1="0" x2="1">
      <stop offset="0%" stop-color="#7c3aed"/>
      <stop offset="100%" stop-color="#22d3ee"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="18" fill="#0b1020"/>
  <path d="M16 20h32v24H16z" fill="none" stroke="url(#g)" stroke-width="4" rx="8"/>
  <circle cx="24" cy="30" r="3" fill="#22d3ee"/>
  <circle cx="40" cy="30" r="3" fill="#7c3aed"/>
  <path d="M22 40c3 4 17 4 20 0" stroke="#94a3b8" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>
""").strip() + "\n", encoding='utf-8')

(src / 'main.jsx').write_text(textwrap.dedent("""
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""").strip() + "\n", encoding='utf-8')

(src / 'App.jsx').write_text(textwrap.dedent("""
import React, { useMemo, useState } from 'react'

const agentRoles = [
  {
    name: 'Research Agent',
    status: 'Active',
    icon: '🔎',
    summary: 'Reads public market structure, protocol state snapshots, and governance notes in read-only mode.',
    tags: ['Read-only', 'Local model', 'Context synthesis'],
  },
  {
    name: 'Strategy Agent',
    status: 'Drafting',
    icon: '🧠',
    summary: 'Turns observations into hypotheses and candidate routes for simulation only.',
    tags: ['Hypothesis generation', 'No live execution', 'Scenario planning'],
  },
  {
    name: 'Risk Agent',
    status: 'Guarding',
    icon: '🛡️',
    summary: 'Flags policy conflicts, unrealistic assumptions, and unsafe automation before anything advances.',
    tags: ['Policy enforcement', 'Constraint checks', 'Human-first'],
  },
  {
    name: 'Simulation Agent',
    status: 'Running',
    icon: '🧪',
    summary: 'Tests candidate routes inside a mock environment with synthetic slippage, fees, and latency.',
    tags: ['Synthetic data', 'Dry-run', 'Counterfactual replay'],
  },
  {
    name: 'Approval Agent',
    status: 'Waiting',
    icon: '✅',
    summary: 'Stops every route at an approval gate and prepares an explainable review packet.',
    tags: ['Manual approval', 'Evidence bundle', 'Audit trail'],
  },
]

const workflowSteps = [
  'Ingest market/state data',
  'Generate hypotheses',
  'Simulate candidate routes',
  'Score opportunities',
  'Require human approval',
  'Archive decisions',
]

const safetyControls = [
  { name: 'Read-only mode', state: 'Enabled' },
  { name: 'Dry-run mode', state: 'Enabled' },
  { name: 'Manual approval required', state: 'Required' },
  { name: 'Kill switch', state: 'Ready' },
  { name: 'Blocked live execution', state: 'Locked' },
]

const opportunityCards = [
  {
    title: 'SIMULATED Route Alpha',
    chain: 'Solana',
    score: 82,
    confidence: 'Medium',
    pnl: '+$148 simulated',
    risk: 'Low',
    status: 'Awaiting review',
    notes: 'Synthetic routing path generated from local research agents. Not executable.',
  },
  {
    title: 'SIMULATED Route Beta',
    chain: 'Solana',
    score: 71,
    confidence: 'Low',
    pnl: '+$63 simulated',
    risk: 'Medium',
    status: 'Rejected by policy',
    notes: 'Rejected because assumptions exceed allowed slippage window in simulation.',
  },
  {
    title: 'SIMULATED Route Gamma',
    chain: 'Solana',
    score: 88,
    confidence: 'High',
    pnl: '+$221 simulated',
    risk: 'Medium',
    status: 'Human approval required',
    notes: 'Simulation performed well, but execution remains blocked by design.',
  },
]

const auditEntries = [
  { time: '06:11:03', level: 'INFO', text: 'Research Agent indexed fresh public state snapshot.' },
  { time: '06:11:29', level: 'INFO', text: 'Strategy Agent proposed 4 hypothetical routes.' },
  { time: '06:12:04', level: 'WARN', text: 'Risk Agent blocked 2 routes due to policy mismatch.' },
  { time: '06:12:31', level: 'INFO', text: 'Simulation Agent completed dry-run batch 1842.' },
  { time: '06:13:02', level: 'INFO', text: 'Approval Agent prepared review packet for Gamma.' },
]

const timeline = [
  { label: 'Signal received', detail: 'Public state snapshot parsed by Research Agent', state: 'done' },
  { label: 'Hypothesis generated', detail: 'Strategy Agent drafted synthetic route candidates', state: 'done' },
  { label: 'Risk review', detail: 'Policy layer screened assumptions and blocked unsafe branches', state: 'done' },
  { label: 'Simulation completed', detail: 'PnL, slippage, and latency scored in mock environment', state: 'done' },
  { label: 'Human decision pending', detail: 'No action can proceed without explicit manual approval', state: 'current' },
  { label: 'Archive and explain', detail: 'Decision package stored to audit log', state: 'upcoming' },
]

const metrics = [
  { label: 'Uptime', value: '24h 00m', meta: 'Demo node stable' },
  { label: 'Queue depth', value: '18', meta: 'Simulated tasks waiting' },
  { label: 'Simulated PnL', value: '+$1,842', meta: 'Educational demo only' },
  { label: 'Rejected actions', value: '27', meta: 'Blocked by policy layer' },
]

function Badge({ children, tone = 'default' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

function SectionHeader({ eyebrow, title, body }) {
  return (
    <div className="section-header">
      <div className="eyebrow">{eyebrow}</div>
      <h2>{title}</h2>
      <p>{body}</p>
    </div>
  )
}

function App() {
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedCard, setSelectedCard] = useState(opportunityCards[2])

  const approvalRate = useMemo(() => {
    const approved = 1
    return Math.round((approved / opportunityCards.length) * 100)
  }, [])

  return (
    <div className="app-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">OA</div>
          <div>
            <div className="brand-title">Ollama Agent Orchestrator Demo</div>
            <div className="brand-subtitle">Local research workflow • simulation only</div>
          </div>
        </div>
        <div className="topbar-actions">
          <Badge tone="danger">Blocked live execution</Badge>
          <Badge tone="cyan">Research and simulation only</Badge>
        </div>
      </header>

      <main>
        <section className="hero panel">
          <div className="hero-copy">
            <Badge tone="purple">Non-operational educational demo</Badge>
            <h1>Show how local Ollama-based agents could coordinate a Solana research workflow 24/7.</h1>
            <p>
              This polished mockup demonstrates orchestration, monitoring, safety controls, and human approval checkpoints.
              It does not include live trading, flashloan execution, exploit automation, wallet handling, or blockchain transactions.
            </p>
            <div className="hero-actions">
              <a href="#dashboard" className="button button-primary">Open dashboard</a>
              <a href="#architecture" className="button button-secondary">View architecture</a>
            </div>
            <div className="warning-stack">
              <div className="warning-banner">Research and simulation only</div>
              <div className="warning-banner">No live trading or flashloan execution</div>
              <div className="warning-banner">No exploit automation</div>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-grid">
              <div className="mini-stat">
                <span className="mini-label">Approval rate</span>
                <strong>{approvalRate}%</strong>
              </div>
              <div className="mini-stat">
                <span className="mini-label">Policy blocks</span>
                <strong>27</strong>
              </div>
              <div className="mini-stat">
                <span className="mini-label">Mock routes</span>
                <strong>1842</strong>
              </div>
              <div className="mini-stat">
                <span className="mini-label">Ollama nodes</span>
                <strong>5 local</strong>
              </div>
            </div>
            <div className="radar-card">
              <div className="radar-ring ring-1" />
              <div className="radar-ring ring-2" />
              <div className="radar-ring ring-3" />
              <div className="radar-core">
                <span>Safe demo</span>
                <strong>Live execution locked</strong>
              </div>
            </div>
          </div>
        </section>

        <section id="dashboard" className="dashboard-grid">
          <div className="panel span-8">
            <SectionHeader
              eyebrow="Local agent roles"
              title="Specialized local agents with explicit boundaries"
              body="Each role is separated by policy and approval constraints. Everything shown below is mock data."
            />
            <div className="card-grid">
              {agentRoles.map((agent) => (
                <article className="agent-card" key={agent.name}>
                  <div className="agent-top">
                    <div className="agent-icon">{agent.icon}</div>
                    <Badge tone="default">{agent.status}</Badge>
                  </div>
                  <h3>{agent.name}</h3>
                  <p>{agent.summary}</p>
                  <div className="tag-row">
                    {agent.tags.map((tag) => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel span-4">
            <SectionHeader
              eyebrow="Monitoring"
              title="Operational snapshot"
              body="Live-looking metrics with demo-only values."
            />
            <div className="metric-stack">
              {metrics.map((metric) => (
                <div className="metric-card" key={metric.label}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                  <small>{metric.meta}</small>
                </div>
              ))}
            </div>
          </div>

          <div className="panel span-7">
            <SectionHeader
              eyebrow="Workflow pipeline"
              title="Research pipeline with a mandatory approval checkpoint"
              body="Every synthetic route stops at a human review gate before anything could progress."
            />
            <div className="workflow-row">
              {workflowSteps.map((step, index) => (
                <div className="workflow-step" key={step}>
                  <div className="workflow-index">{index + 1}</div>
                  <div className="workflow-text">{step}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel span-5">
            <SectionHeader
              eyebrow="Safety controls"
              title="Controls that make the demo visibly non-operational"
              body="These controls are part of the product narrative, not hidden fine print."
            />
            <div className="safety-list">
              {safetyControls.map((control) => (
                <div className="safety-item" key={control.name}>
                  <div>
                    <strong>{control.name}</strong>
                    <p>Policy-enforced within the orchestrator mockup.</p>
                  </div>
                  <Badge tone={control.state === 'Locked' ? 'danger' : 'cyan'}>{control.state}</Badge>
                </div>
              ))}
            </div>
          </div>

          <div className="panel span-8">
            <SectionHeader
              eyebrow="Demo panels"
              title="Simulated opportunity cards"
              body="These cards show what the review experience could look like without enabling any real execution."
            />
            <div className="card-grid opportunities">
              {opportunityCards.map((card) => (
                <article className="opportunity-card" key={card.title}>
                  <div className="opportunity-top">
                    <Badge tone="purple">SIMULATED</Badge>
                    <Badge tone={card.status.includes('Rejected') ? 'danger' : 'cyan'}>{card.status}</Badge>
                  </div>
                  <h3>{card.title}</h3>
                  <p>{card.notes}</p>
                  <div className="opportunity-metrics">
                    <div><span>Score</span><strong>{card.score}</strong></div>
                    <div><span>Confidence</span><strong>{card.confidence}</strong></div>
                    <div><span>PnL</span><strong>{card.pnl}</strong></div>
                    <div><span>Risk</span><strong>{card.risk}</strong></div>
                  </div>
                  <button
                    className="button button-secondary full-width"
                    onClick={() => {
                      setSelectedCard(card)
                      setModalOpen(true)
                    }}
                  >
                    Open risk review
                  </button>
                </article>
              ))}
            </div>
          </div>

          <div className="panel span-4">
            <SectionHeader
              eyebrow="Audit log preview"
              title="Explainability at every step"
              body="A transparent event stream makes the demo easier to review and safer to present."
            />
            <div className="log-list">
              {auditEntries.map((entry, idx) => (
                <div className="log-item" key={`${entry.time}-${idx}`}>
                  <span className="log-time">{entry.time}</span>
                  <Badge tone={entry.level === 'WARN' ? 'danger' : 'default'}>{entry.level}</Badge>
                  <p>{entry.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="architecture" className="panel architecture-panel">
          <SectionHeader
            eyebrow="Architecture diagram"
            title="Local-first orchestration with policy and simulation layers"
            body="This section explains the system shape without exposing live automation or execution paths."
          />
          <div className="architecture-grid">
            <div className="arch-node">
              <h3>Ollama local models</h3>
              <p>Specialized local models support research, strategy drafting, risk reviews, and summarization.</p>
            </div>
            <div className="arch-arrow">→</div>
            <div className="arch-node highlight">
              <h3>Orchestrator</h3>
              <p>Queues tasks, routes context, enforces sequencing, and blocks all live actions by policy.</p>
            </div>
            <div className="arch-arrow">→</div>
            <div className="arch-node">
              <h3>Simulation engine</h3>
              <p>Evaluates candidate routes against synthetic latency, slippage, and fee assumptions.</p>
            </div>

            <div className="arch-node">
              <h3>Policy layer</h3>
              <p>Dry-run, read-only, manual approval, and blocked execution checks are enforced here.</p>
            </div>
            <div className="arch-arrow">→</div>
            <div className="arch-node">
              <h3>Dashboard</h3>
              <p>Displays agents, risk packets, audit logs, queue depth, and simulated opportunity review.</p>
            </div>
            <div className="arch-arrow">→</div>
            <div className="arch-node danger">
              <h3>Execution</h3>
              <p>Intentionally disabled. Badge remains locked to prevent any confusion about the demo scope.</p>
            </div>
          </div>
        </section>

        <section className="panel timeline-panel">
          <SectionHeader
            eyebrow="Approval checkpoint timeline"
            title="Human approval is part of the core flow"
            body="The final checkpoint is designed to be obvious, friction-filled, and manual."
          />
          <div className="timeline">
            {timeline.map((item) => (
              <div className={`timeline-item timeline-${item.state}`} key={item.label}>
                <div className="timeline-dot" />
                <div className="timeline-content">
                  <strong>{item.label}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="footer">
        <div>Ollama Agent Orchestrator Demo</div>
        <div>Research and simulation only • No live trading • No exploit automation</div>
      </footer>

      {modalOpen && (
        <div className="modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="modal panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-top">
              <div>
                <Badge tone="purple">SIMULATED</Badge>
                <h3>{selectedCard.title}</h3>
              </div>
              <button className="icon-button" onClick={() => setModalOpen(false)}>✕</button>
            </div>

            <div className="review-grid">
              <div className="review-block">
                <span className="review-label">Risk summary</span>
                <strong>{selectedCard.risk} risk</strong>
                <p>
                  This review packet was generated by the Risk Agent using synthetic assumptions only.
                  Execution remains blocked regardless of score.
                </p>
              </div>
              <div className="review-block">
                <span className="review-label">Policy outcome</span>
                <strong>manual approval required</strong>
                <p>
                  Read-only mode, dry-run mode, and blocked live execution are all active.
                </p>
              </div>
              <div className="review-block full-span">
                <span className="review-label">Decision guidance</span>
                <p>
                  Demonstration only. The operator may archive, annotate, or reject the simulated route. No wallet,
                  private key, flashloan path, exploit routine, or live market action is exposed by this interface.
                </p>
              </div>
            </div>

            <div className="modal-actions">
              <button className="button button-secondary" onClick={() => setModalOpen(false)}>Archive decision</button>
              <button className="button button-primary" onClick={() => setModalOpen(false)}>Acknowledge checkpoint</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
""").strip() + "\n", encoding='utf-8')

(src / 'styles.css').write_text(textwrap.dedent("""
:root {
  color-scheme: dark;
  --bg: #07111f;
  --bg-2: #0a1528;
  --panel: rgba(10, 21, 40, 0.76);
  --panel-strong: rgba(13, 24, 45, 0.92);
  --border: rgba(148, 163, 184, 0.16);
  --text: #ecf4ff;
  --muted: #9fb0c9;
  --purple: #8b5cf6;
  --cyan: #22d3ee;
  --green: #34d399;
  --red: #fb7185;
  --yellow: #fbbf24;
  --shadow: 0 18px 60px rgba(0, 0, 0, 0.35);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(139, 92, 246, 0.16), transparent 28%),
    radial-gradient(circle at 90% 20%, rgba(34, 211, 238, 0.15), transparent 26%),
    linear-gradient(180deg, #04101d 0%, #091423 100%);
  color: var(--text);
}

a { color: inherit; text-decoration: none; }
button { font: inherit; }

.app-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28px;
}

.ambient {
  position: fixed;
  width: 32rem;
  height: 32rem;
  border-radius: 999px;
  filter: blur(80px);
  opacity: 0.28;
  pointer-events: none;
}
.ambient-a { top: -8rem; right: -10rem; background: var(--purple); }
.ambient-b { bottom: -12rem; left: -10rem; background: var(--cyan); }

.topbar,
.hero,
.panel,
.footer {
  position: relative;
  z-index: 2;
}

.topbar {
  max-width: 1320px;
  margin: 0 auto 24px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  backdrop-filter: blur(10px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-weight: 800;
  background: linear-gradient(135deg, rgba(139,92,246,0.85), rgba(34,211,238,0.85));
  box-shadow: 0 10px 30px rgba(34, 211, 238, 0.25);
}
.brand-title {
  font-weight: 700;
  letter-spacing: 0.01em;
}
.brand-subtitle {
  font-size: 0.92rem;
  color: var(--muted);
}
.topbar-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

main {
  max-width: 1320px;
  margin: 0 auto;
}

.panel {
  background: linear-gradient(180deg, rgba(13, 24, 45, 0.78), rgba(9, 18, 34, 0.92));
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  border-radius: 28px;
  backdrop-filter: blur(16px);
}

.hero {
  padding: 42px;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 28px;
  margin-bottom: 24px;
}

.hero h1 {
  margin: 16px 0 14px;
  font-size: clamp(2.2rem, 5vw, 4.3rem);
  line-height: 0.96;
  max-width: 12ch;
}

.hero p {
  max-width: 68ch;
  color: var(--muted);
  font-size: 1.04rem;
  line-height: 1.65;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin: 24px 0;
}

.button {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px 18px;
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}
.button:hover { transform: translateY(-1px); }
.button-primary {
  color: white;
  background: linear-gradient(135deg, rgba(139,92,246,0.92), rgba(34,211,238,0.9));
  border: none;
}
.button-secondary {
  color: var(--text);
  background: rgba(255,255,255,0.04);
}
.full-width { width: 100%; }

.warning-stack {
  display: grid;
  gap: 10px;
  max-width: 30rem;
}
.warning-banner {
  border: 1px solid rgba(251, 113, 133, 0.25);
  background: rgba(251, 113, 133, 0.08);
  color: #ffd6de;
  border-radius: 14px;
  padding: 12px 14px;
  font-weight: 600;
}

.hero-visual {
  display: flex;
  flex-direction: column;
  gap: 18px;
  justify-content: center;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.mini-stat {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 16px;
}
.mini-label {
  display: block;
  color: var(--muted);
  margin-bottom: 10px;
}
.mini-stat strong {
  font-size: 1.6rem;
}

.radar-card {
  position: relative;
  min-height: 320px;
  border-radius: 24px;
  overflow: hidden;
  border: 1px solid rgba(34, 211, 238, 0.18);
  background:
    radial-gradient(circle at center, rgba(34,211,238,0.08), transparent 55%),
    rgba(255,255,255,0.03);
  display: grid;
  place-items: center;
}
.radar-ring {
  position: absolute;
  border: 1px solid rgba(34, 211, 238, 0.18);
  border-radius: 999px;
  animation: pulse 6s ease-in-out infinite;
}
.ring-1 { width: 120px; height: 120px; }
.ring-2 { width: 220px; height: 220px; animation-delay: 0.8s; }
.ring-3 { width: 320px; height: 320px; animation-delay: 1.6s; }
.radar-core {
  width: 180px;
  height: 180px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  text-align: center;
  background: linear-gradient(135deg, rgba(139,92,246,0.22), rgba(34,211,238,0.22));
  border: 1px solid rgba(255,255,255,0.08);
}
.radar-core span {
  color: var(--muted);
  display: block;
}
.radar-core strong {
  padding: 0 18px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 24px;
}

.span-8 { grid-column: span 8; }
.span-7 { grid-column: span 7; }
.span-5 { grid-column: span 5; }
.span-4 { grid-column: span 4; }

.panel { padding: 28px; }

.section-header {
  margin-bottom: 22px;
}
.eyebrow {
  color: var(--cyan);
  font-size: 0.86rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.section-header h2 {
  margin: 0 0 10px;
  font-size: 1.65rem;
}
.section-header p {
  margin: 0;
  color: var(--muted);
  line-height: 1.65;
  max-width: 70ch;
}

.card-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.agent-card,
.opportunity-card,
.metric-card,
.arch-node,
.review-block,
.log-item {
  background: rgba(255,255,255,0.035);
  border: 1px solid var(--border);
  border-radius: 22px;
}

.agent-card,
.opportunity-card {
  padding: 18px;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}
.agent-card:hover,
.opportunity-card:hover {
  transform: translateY(-2px);
  border-color: rgba(139, 92, 246, 0.35);
  background: rgba(255,255,255,0.05);
}

.agent-top,
.opportunity-top,
.modal-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.agent-icon {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(139, 92, 246, 0.14);
  font-size: 1.4rem;
}

.agent-card h3,
.opportunity-card h3,
.arch-node h3 {
  margin: 14px 0 10px;
}
.agent-card p,
.opportunity-card p,
.arch-node p,
.review-block p {
  color: var(--muted);
  line-height: 1.6;
}

.tag-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.tag,
.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.tag {
  background: rgba(255,255,255,0.055);
  color: #dbeafe;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.badge-default {
  background: rgba(255,255,255,0.055);
  color: #dbeafe;
  border: 1px solid rgba(148, 163, 184, 0.12);
}
.badge-purple {
  background: rgba(139, 92, 246, 0.18);
  color: #e9ddff;
  border: 1px solid rgba(139, 92, 246, 0.25);
}
.badge-cyan {
  background: rgba(34, 211, 238, 0.16);
  color: #d5fbff;
  border: 1px solid rgba(34, 211, 238, 0.25);
}
.badge-danger {
  background: rgba(251, 113, 133, 0.16);
  color: #ffd7de;
  border: 1px solid rgba(251, 113, 133, 0.25);
}

.metric-stack {
  display: grid;
  gap: 14px;
}
.metric-card {
  padding: 18px;
}
.metric-card span {
  color: var(--muted);
  display: block;
  margin-bottom: 8px;
}
.metric-card strong {
  display: block;
  font-size: 1.7rem;
  margin-bottom: 6px;
}
.metric-card small {
  color: #7dd3fc;
}

.workflow-row {
  display: grid;
  gap: 14px;
}
.workflow-step {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 14px;
  align-items: center;
  padding: 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 18px;
}
.workflow-index {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(139,92,246,0.85), rgba(34,211,238,0.85));
  font-weight: 800;
}
.workflow-text {
  font-weight: 600;
}

.safety-list {
  display: grid;
  gap: 12px;
}
.safety-item {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
}
.safety-item p {
  color: var(--muted);
  margin: 6px 0 0;
}

.opportunity-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 16px 0 18px;
}
.opportunity-metrics div {
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.08);
}
.opportunity-metrics span {
  color: var(--muted);
  display: block;
  margin-bottom: 8px;
  font-size: 0.85rem;
}

.log-list {
  display: grid;
  gap: 12px;
}
.log-item {
  padding: 14px 16px;
}
.log-item p {
  margin: 10px 0 0;
  color: var(--muted);
}
.log-time {
  color: var(--cyan);
  font-size: 0.82rem;
  margin-right: 10px;
}

.architecture-panel,
.timeline-panel {
  margin-top: 24px;
}

.architecture-grid {
  display: grid;
  grid-template-columns: 1fr 60px 1fr 60px 1fr;
  gap: 16px;
  align-items: center;
}
.arch-node {
  padding: 18px;
  min-height: 160px;
}
.arch-node.highlight {
  background: linear-gradient(180deg, rgba(139,92,246,0.12), rgba(34,211,238,0.08));
}
.arch-node.danger {
  border-color: rgba(251,113,133,0.22);
  background: rgba(251,113,133,0.06);
}
.arch-arrow {
  text-align: center;
  font-size: 1.8rem;
  color: var(--muted);
}

.timeline {
  display: grid;
  gap: 12px;
}
.timeline-item {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 14px;
  align-items: start;
}
.timeline-dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  margin-top: 7px;
  background: rgba(148,163,184,0.35);
}
.timeline-done .timeline-dot {
  background: var(--green);
  box-shadow: 0 0 0 8px rgba(52,211,153,0.08);
}
.timeline-current .timeline-dot {
  background: var(--yellow);
  box-shadow: 0 0 0 8px rgba(251,191,36,0.08);
}
.timeline-content {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
}
.timeline-content p {
  color: var(--muted);
  margin: 6px 0 0;
}

.footer {
  max-width: 1320px;
  margin: 24px auto 0;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  color: var(--muted);
  font-size: 0.92rem;
  padding: 0 4px 16px;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(2, 6, 23, 0.7);
  display: grid;
  place-items: center;
  z-index: 20;
  padding: 20px;
  backdrop-filter: blur(8px);
}
.modal {
  max-width: 760px;
  width: 100%;
  padding: 24px;
}
.icon-button {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.04);
  color: var(--text);
  cursor: pointer;
}
.review-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}
.review-block {
  padding: 16px;
}
.review-block.full-span {
  grid-column: 1 / -1;
}
.review-label {
  color: var(--cyan);
  display: block;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.8rem;
  margin-bottom: 10px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 18px;
}

@keyframes pulse {
  0%, 100% { transform: scale(0.96); opacity: 0.55; }
  50% { transform: scale(1.04); opacity: 1; }
}

@media (max-width: 1100px) {
  .hero {
    grid-template-columns: 1fr;
  }
  .span-8, .span-7, .span-5, .span-4 {
    grid-column: span 12;
  }
  .architecture-grid {
    grid-template-columns: 1fr;
  }
  .arch-arrow {
    transform: rotate(90deg);
  }
}

@media (max-width: 720px) {
  .app-shell { padding: 16px; }
  .topbar, .footer {
    flex-direction: column;
    align-items: flex-start;
  }
  .hero, .panel {
    padding: 20px;
    border-radius: 22px;
  }
  .review-grid,
  .hero-grid,
  .opportunity-metrics {
    grid-template-columns: 1fr;
  }
}
""").strip() + "\n", encoding='utf-8')

# zip it
zip_path = pathlib.Path('/mnt/data/ollama-agent-orchestrator-demo.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in base.rglob('*'):
        z.write(p, p.relative_to(base.parent))

print(f"Created app at {base}")
print(f"Created zip at {zip_path}")


#### ChatGPT:
I’m applying your project scaffold directly and packaging it so you have the updated app files and zip in place. After that I’ll link the artifact paths cleanly.


#### ChatGPT:
The existing folder is locked, so I’m rebuilding the same app into a fresh writable directory and re-zipping it there. That avoids the permission issue cleanly.


#### ChatGPT:
Built and packaged in a fresh writable location.

Files:
[Download the zip](sandbox:/mnt/data/ollama-agent-orchestrator-demo-research.zip)
[Open the project folder](sandbox:/mnt/data/ollama-agent-orchestrator-demo-research)

This version keeps the research-grade framing and the safety boundaries visible throughout:

- research and simulation only
- no live trading or flashloan execution
- no exploit automation
- mock data only
- React + Vite frontend

If you want, the next step is to add a matching research submission README and a one-page evaluator brief inside the project folder.
