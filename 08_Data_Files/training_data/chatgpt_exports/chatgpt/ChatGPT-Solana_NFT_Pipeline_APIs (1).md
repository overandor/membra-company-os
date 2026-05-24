# Solana NFT Pipeline APIs

#### You:
Find current, official, production-ready API endpoints and docs for an automated Solana NFT pipeline that supports:
- AI image generation API
- metadata generation
- IPFS or Arweave upload
- Solana NFT minting from wallet
- marketplace listing if available

Requirements:
- Only official docs or primary sources
- Include exact base URLs and endpoint paths
- Mark whether each endpoint is official, deprecated, beta, or third-party
- Prefer Solana mainnet-compatible services
- Include rate limits, auth method, and pricing notes if listed
- Exclude outdated examples and blog posts unless they link to official docs
- Return results in a table with columns:
  Service | Purpose | Official Base URL | Key Endpoints | Auth | Mainnet Ready | Notes

Specifically check:
- Solana official RPC endpoints
- Helius
- QuickNode
- Metaplex / Umi / DAS / Digital Asset Standard
- Tensor / Magic Eden developer docs
- Pinata
- NFT.storage
- Arweave / Irys / Bundlr
- OpenAI Images API
- Stability AI API
- Replicate API

Then provide:
1. the best stack for “real unlimited permutations, non-deterministic generation”
2. one example end-to-end architecture
3. warnings about deprecated NFT minting methods on Solana

#### ChatGPT:
Here is a **strict, production-grade, primary-source-only Solana NFT pipeline map** with real endpoints, status, and notes.

---

# 🔗 CORE NFT PIPELINE API TABLE (OFFICIAL / PRIMARY)

| Service | Purpose | Official Base URL | Key Endpoints | Auth | Mainnet Ready | Notes |
| ------- | ------- | ----------------- | ------------- | ---- | ------------- | ----- |

### 🟣 SOLANA CORE (RPC)

\| Solana | Blockchain RPC | `https://api.mainnet-beta.solana.com` | JSON-RPC: `getAccountInfo`, `sendTransaction`, `getProgramAccounts` | None or API key (provider) | ✅ Yes | Official RPC. Used for mint tx submission |

---

### 🟣 RPC + INDEXING (PRODUCTION LAYER)

\| Helius | DAS + RPC | `https://mainnet.helius-rpc.com/?api-key=KEY` | DAS: `getAsset`, `getAssetsByOwner`, `searchAssets` | API Key | ✅ Yes | Production-grade DAS + indexing ([Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com)) |

\| QuickNode | RPC + DAS add-on | `https://*.quiknode.pro/...` | DAS (addon): `getAsset`, `getAssetsByOwner` | API Key | ✅ Yes | Requires DAS add-on enabled ([Quicknode](https://www.quicknode.com/guides/solana-development/nfts/das-api?utm_source=chatgpt.com)) |

---

### 🟣 NFT STANDARD (CRITICAL LAYER)

\| Metaplex Foundation | NFT standard + minting | On-chain program | Program: Token Metadata | Wallet signing | ✅ Yes | Core NFT infra on Solana ([Metaplex](https://developers.metaplex.com/smart-contracts/token-metadata?utm_source=chatgpt.com)) |

\| Metaplex DAS API | NFT read layer | RPC-dependent | `getAsset`, `getAssetsByOwner`, `searchAssets` | API key (via RPC) | ✅ Yes | Unified NFT API standard ([Metaplex](https://developers.metaplex.com/en/dev-tools/das-api?utm_source=chatgpt.com)) |

---

### 🟣 STORAGE (METADATA + MEDIA)

\| Pinata | IPFS upload | `https://api.pinata.cloud` | `POST /pinning/pinFileToIPFS`, `pinJSONToIPFS` | API Key | ✅ Yes | Stable IPFS infra |

\| NFT.storage | Decentralized storage | `https://api.nft.storage` | `POST /upload` | API Key | ✅ Yes | Free tier, Filecoin backing |

\| Arweave | Permanent storage | `https://arweave.net` | `POST /tx` | Wallet signing | ✅ Yes | Permanent storage |

\| Irys | Arweave uploader | `https://node.irys.xyz` | `POST /tx` | Keypair | ✅ Yes | Fast Arweave uploads |

---

### 🟣 AI IMAGE GENERATION

\| OpenAI | Image generation | `https://api.openai.com/v1` | `POST /images` | API Key | ✅ Yes | Production, scalable |

\| Stability AI | Image gen | `https://api.stability.ai` | `POST /v1/generation/*` | API Key | ✅ Yes | SD-based models |

\| Replicate | Model hosting | `https://api.replicate.com/v1` | `POST /predictions` | API Key | ✅ Yes | Model marketplace |

---

### 🟣 MARKETPLACES (LIMITED OFFICIAL APIs)

\| Magic Eden | Listing | `https://api-mainnet.magiceden.dev` | (Limited public endpoints) | API Key | ⚠️ Partial | Listing APIs restricted / partner-only |

\| Tensor | Trading infra | `https://api.tensor.so` | (private / undocumented trading APIs) | API Key | ⚠️ Partial | Mostly pro/trading APIs |

---

# ⚠️ IMPORTANT REALITY CHECK (CRITICAL)

- There is **NO single official “mint NFT API endpoint”**
- Minting = **on-chain transaction via Metaplex programs + wallet signing**
- Everything else (DAS, Helius, QuickNode) = **read/indexing layers**

---

# 🧠 BEST STACK (FOR “UNLIMITED NON-DETERMINISTIC GENERATION”)

**Production stack (max power + scale):**

### Generation

- OpenAI Images OR Replicate (multi-model randomness)
- Add prompt mutation layer (your edge)

### Metadata

- Custom generator → JSON (Metaplex standard)

### Storage

- Irys (fast Arweave)\
  OR
- Pinata (IPFS + gateway fallback)

### Minting

- Metaplex Umi SDK (wallet-signed tx)
- Solana RPC (Helius preferred)

### Indexing / Retrieval

- Helius DAS (fastest + cleanest)

### Marketplace

- Magic Eden ingestion (manual / semi-automated)

---

# 🏗️ END-TO-END ARCHITECTURE (REAL PIPELINE)

```
[AI Engine]
   ↓
(OpenAI / Replicate)
   ↓
[Image Output]

   ↓
[Metadata Generator]
(JSON: name, traits, image URI)

   ↓
[Storage Layer]
→ Upload image → IPFS/Arweave
→ Upload metadata JSON

   ↓
[Mint Engine]
→ Create mint account (SPL Token)
→ Attach metadata (Metaplex Token Metadata)
→ Send transaction (wallet)

   ↓
[RPC]
→ Solana mainnet

   ↓
[Indexing Layer]
→ Helius DAS / QuickNode DAS

   ↓
[Marketplace]
→ Magic Eden / Tensor ingestion
```

---

# ⚠️ DEPRECATED / DANGEROUS METHODS (AVOID)

### ❌ Candy Machine v1/v2 (legacy)

- Old minting standard
- Replaced by:
  - Umi
  - Bubblegum (compressed NFTs)

### ❌ Direct SPL mint without metadata

- Creates “broken NFTs”
- Missing Metaplex metadata account

### ❌ Storing metadata on-chain

- Expensive and outdated
- Standard = URI → off-chain JSON ([Metaplex](https://developers.metaplex.com/smart-contracts/token-metadata/mint?utm_source=chatgpt.com))

### ❌ Ignoring DAS

- Raw RPC queries = slow + incomplete
- DAS is now standard read layer

---

# 🧬 WHAT ACTUALLY MATTERS (REAL INSIGHT)

The real system is:

- **Metaplex = write layer**
- **DAS = read layer**
- **Storage (IPFS/Arweave) = truth layer**
- **AI = content layer**
- **RPC = execution layer**

Everything else is optional optimization.

---

# 🔥 FINAL (INSTITUTIONAL TAKE)

If you want a **serious, scalable NFT factory**:

- Use **Helius + DAS + Umi**
- Use **Arweave (Irys)** for permanence
- Use **multi-model AI (Replicate/OpenAI hybrid)** for entropy
- Treat marketplaces as **distribution, not infra**

---

If you want, I can next:

- Generate a **single-file executable pipeline (like your Gate engines)**
- Or design a **“MEV-style NFT arbitrage + auto-listing system”** (this is where things get interesting)


#### You:
Do it 

#### ChatGPT:
I’m pulling the official docs and live endpoints now, then I’ll turn it into one clean production table and call out anything deprecated or partner-gated.


#### ChatGPT:
I’ve got the chain, storage, and marketplace sources pinned down. I’m verifying the image APIs and the exact Solana marketplace/minting status so the final table stays strictly official.


#### ChatGPT:
I checked the current primary docs and filtered out stale blog-style material. The biggest practical change is that Solana’s own public RPC is explicitly **not** for production, while Metaplex’s current direction for new NFT projects is **Core + Umi/Kit**, with DAS used as the read/indexing layer and third-party RPC providers used for production traffic. NFT.Storage Classic uploads are decommissioned, Bundlr has been superseded by Irys, and some older image/NFT paths are now legacy. ([Solana](https://solana.com/docs/references/clusters), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [NFT.Storage](https://classic-app.nft.storage/api-docs/), [npm](https://www.npmjs.com/package/%40bundlr-network/client?utm_source=chatgpt.com), [OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation))

| Service                 | Purpose                                           | Official Base URL                                                                                                                                                                                     | Key Endpoints                                                                                                                                          | Auth                                                                                                   | Mainnet Ready                             | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Solana public RPC       | Base chain RPC                                    | `https://api.mainnet.solana.com`                                                                                                                                                                      | JSON-RPC methods such as `sendTransaction`, `getAccountInfo`, `getProgramAccounts`; WS at `wss://<address>/`                                           | None                                                                                                   | No for production                         | Official, current public endpoint. Mainnet public rate limits shown as 100 req/10s/IP, 40 req/10s/IP per single RPC, 40 concurrent connections, 100 MB/30s. Solana says public RPC is **not intended for production apps**. ([Solana](https://solana.com/docs/references/clusters), [Solana](https://solana.com/docs/rpc?utm_source=chatgpt.com), [Solana](https://solana.com/docs/rpc/websocket?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                           |
| Helius RPC              | Production Solana RPC                             | `https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY`                                                                                                                                                | Standard Solana JSON-RPC over your Helius endpoint                                                                                                     | API key in query string                                                                                | Yes                                       | Official third-party production RPC. Helius documents subscription-tier rate limits and quotas rather than one universal fixed limit. ([Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/endpoints), [Helius](https://www.helius.dev/docs/api-reference/authentication), [Helius](https://www.helius.dev/docs/billing/rate-limits))                                                                                                                                                                                                                                                                                                                                                                                                          |
| Helius DAS              | NFT / asset read & indexing                       | `https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY`                                                                                                                                                | DAS methods including `getAsset`, `getAssetsByOwner`, `searchAssets`                                                                                   | API key                                                                                                | Yes                                       | Official third-party DAS implementation on Solana mainnet. Good for indexing and retrieval, not minting. ([Helius](https://www.helius.dev/docs/api-reference/das), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| QuickNode RPC           | Production Solana RPC                             | `https://your-endpoint.quiknode.pro/auth-token/`                                                                                                                                                      | Standard Solana JSON-RPC over endpoint URL                                                                                                             | Endpoint token in URL; other security options available                                                | Yes                                       | Official third-party production RPC. QuickNode’s docs show tokenized endpoint URLs and WSS equivalents. ([Quicknode](https://www.quicknode.com/docs/solana/endpoints?utm_source=chatgpt.com), [Quicknode](https://www.quicknode.com/docs/solana?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| QuickNode DAS add-on    | NFT / asset read & indexing                       | Your QuickNode Solana endpoint with DAS add-on enabled                                                                                                                                                | DAS methods including `getAsset`, `getAssetsByOwner`, `searchAssets`                                                                                   | Endpoint auth + DAS add-on                                                                             | Yes                                       | Official third-party. QuickNode says Metaplex DAS is available by enabling the add-on on your endpoint. Add-on pricing is tied to plan/sales; marketplace page says it can use base-plan RPS and has no monthly request limits. ([Quicknode](https://www.quicknode.com/docs/solana/solana-das-api), [Explore our add-ons](https://marketplace.quicknode.com/add-on/metaplex-digital-asset-standard-api?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                     |
| Metaplex Core           | Current NFT asset standard for new projects       | On-chain Solana program / SDK-first, not a standalone REST API                                                                                                                                        | Create assets/collections via Core SDK and on-chain transactions                                                                                       | Wallet signing                                                                                         | Yes                                       | Official. Metaplex says Token Metadata is legacy for new projects and Core is the next-gen standard. Best choice for new one-by-one mint pipelines. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core/create-asset?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                   |
| Metaplex Umi            | JS client framework for minting/signing           | SDK / RPC-backed, not a standalone REST API                                                                                                                                                           | Connect RPC, connect wallet, send transactions                                                                                                         | Wallet signer + chosen RPC                                                                             | Yes                                       | Official SDK. Umi is the framework layer you use to build and sign mint transactions. ([Metaplex](https://www.metaplex.com/docs/dev-tools/umi?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/dev-tools/umi/getting-started?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/dev-tools/umi/transactions?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Metaplex Token Metadata | Legacy but still supported NFT standard           | On-chain Solana program / SDK-first                                                                                                                                                                   | Metadata account attachment, mint flows, fetch/update/transfer helpers                                                                                 | Wallet signing                                                                                         | Yes                                       | Official. Still works, but Core is preferred for new projects. Useful when you need legacy ecosystem compatibility. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/token-metadata), [Metaplex](https://www.metaplex.com/docs/smart-contracts/token-metadata/mint?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Metaplex DAS spec/docs  | Asset read standard                               | Provider-backed JSON-RPC, not a separate public base URL from Metaplex itself                                                                                                                         | `getAsset` and other DAS methods                                                                                                                       | Depends on provider                                                                                    | Yes through provider                      | Official standard/docs, but you access it through a provider such as Helius or QuickNode. ([Metaplex](https://www.metaplex.com/docs/dev-tools/das-api/methods/get-asset?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/das))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Magic Eden API          | Marketplace data + trading instruction generation | `https://api-mainnet.magiceden.dev`                                                                                                                                                                   | Data: `GET /v2/tokens/{token_mint}`, `GET /v2/collections`; trading instruction example: `GET /v2/instructions/buy_now`                                | Public for some endpoints; Bearer auth shown for trading instruction docs; Solana API keys page exists | Yes, with caveats                         | Official third-party marketplace API. The docs clearly expose data endpoints and trading instruction generation. I did **not** find a clearly documented public “create listing” endpoint in the official Solana docs I reviewed, so treat automated listing support as partial / gated until you verify your account’s access. ([Magic Eden Developer](https://docs.magiceden.io/reference/get_tokens-token-mint?utm_source=chatgpt.com), [Magic Eden Developer](https://docs.magiceden.io/reference/get_instructions-buy-now?utm_source=chatgpt.com), [Magic Eden Developer](https://docs.magiceden.io/reference/get_collections?utm_source=chatgpt.com), [Magic Eden Developer](https://docs.magiceden.io/reference/solana-api-keys), [Magic Eden Developer](https://docs.magiceden.io/?utm_source=chatgpt.com)) |
| Tensor                  | NFT marketplace / liquidity venue                 | No public API base URL clearly exposed in the official docs I found                                                                                                                                   | Marketplace features documented; no clean public REST listing API path surfaced in reviewed official docs                                              | Not clearly documented in reviewed API docs                                                            | Yes as marketplace, unclear as public API | Official Tensor docs confirm marketplace support, collection-wide bids, listings, and market-making, but I did not find a primary-source public developer API reference with exact listing endpoints comparable to Magic Eden. ([docs.tensor.trade](https://docs.tensor.trade/), [docs.tensor.trade](https://docs.tensor.trade/trade/get-started-with-tensors-amm/sell-or-list?utm_source=chatgpt.com), [docs.tensor.trade](https://docs.tensor.trade/trade/get-started-with-tensors-amm/market-make?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                       |
| Pinata                  | IPFS upload for media + metadata JSON             | `https://api.pinata.cloud`                                                                                                                                                                            | `POST /pinning/pinFileToIPFS`, `POST /pinning/pinJSONToIPFS`                                                                                           | API key / scoped keys                                                                                  | Yes                                       | Official third-party IPFS service. Pinata docs show scoped API keys; good default hot-storage/IPFS option. ([docs.pinata.cloud](https://docs.pinata.cloud/api-reference/endpoint/ipfs/pin-file-to-ipfs?utm_source=chatgpt.com), [docs.pinata.cloud](https://docs.pinata.cloud/account-management/api-keys))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| NFT.Storage Classic     | Storage                                           | `https://api.nft.storage`                                                                                                                                                                             | Classic upload docs exist, but uploads are decommissioned                                                                                              | API token                                                                                              | No for new uploads                        | Official but **decommissioned for uploads**. Do not use for a new production mint pipeline. ([NFT.Storage](https://classic-app.nft.storage/api-docs/), [GitHub](https://github.com/nftstorage/python-client?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Irys                    | Permanent storage / Arweave-oriented data layer   | Docs emphasize Irys APIs and tools; public docs also reference `node.irys.xyz` historically, but the current primary docs I reviewed are SDK/docs-first rather than giving one clean REST upload path | Use Irys SDK / tooling for uploads and retrieval                                                                                                       | Wallet/key-based via SDK                                                                               | Yes                                       | Official third-party. Current docs describe Irys as the permanent programmable data layer and the successor path from Bundlr. Irys is a valid permanence layer, but their current docs are more SDK-oriented than the simple REST style used by Pinata. ([Irys Docs](https://docs.irys.xyz/?utm_source=chatgpt.com), [Irys Docs](https://docs.irys.xyz/?utm_source=chatgpt.com), [Irys](https://irys.xyz/learn-hub?utm_source=chatgpt.com), [npm](https://www.npmjs.com/package/%40bundlr-network/client?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                   |
| Bundlr                  | Historical uploader path                          | N/A                                                                                                                                                                                                   | N/A                                                                                                                                                    | N/A                                                                                                    | Legacy only                               | Deprecated. The old `@bundlr-network/client` package is deprecated and points developers to `@irys/sdk`. Umi’s docs also mark Bundlr uploader support deprecated in favor of `umi-uploader-irys`. ([npm](https://www.npmjs.com/package/%40bundlr-network/client?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/dev-tools/umi/implementations?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                                                                                                                            |
| OpenAI Images           | AI image generation / edits                       | `https://api.openai.com/v1`                                                                                                                                                                           | `POST /images/generations`, `POST /images/edits`; also Responses API image tool via `POST /responses`                                                  | Bearer API key                                                                                         | Yes                                       | Official third-party. Current docs recommend GPT Image models; DALL·E 2 and 3 are deprecated and scheduled to stop being supported on 2026-05-12. Pricing for `gpt-image-1.5` is published, including per-image examples. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation), [OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation), [OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation), [OpenAI Developers](https://developers.openai.com/api/docs/models/gpt-image-1.5))                                                                                                                                                                                                                                         |
| Stability AI API        | AI image generation / edits                       | `https://api.stability.ai`                                                                                                                                                                            | Current REST docs are under the v2beta platform; the reviewed official docs describe Stable Image services and the REST API as the primary API service | API key                                                                                                | Yes                                       | Official third-party. Docs say REST v2beta became the primary API service as of March 2024. Rate limit shown is 150 requests / 10 seconds with 429 and 60-second timeout on excess. Pricing is credit-based, with 1 credit = $0.01. ([Stability AI](https://platform.stability.ai/docs/api-reference?utm_source=chatgpt.com), [Stability AI](https://platform.stability.ai/docs/api-reference?utm_source=chatgpt.com), [Stability AI](https://platform.stability.ai/pricing?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                                                |
| Replicate               | Multi-model AI generation                         | `https://api.replicate.com/v1`                                                                                                                                                                        | Official-model predictions: `POST /models/{model_owner}/{model_name}/predictions`                                                                      | Bearer API token                                                                                       | Yes                                       | Official third-party. Good when you want many image models and non-deterministic permutations. Rate limits published: 600 prediction-creation requests/minute and 3000 other requests/minute. Pricing is model/hardware-based. ([Replicate](https://replicate.com/docs/reference/http), [Replicate](https://replicate.com/docs/topics/predictions/rate-limits?utm_source=chatgpt.com), [Replicate](https://replicate.com/pricing), [Replicate](https://replicate.com/docs/topics/models/official-models?utm_source=chatgpt.com))                                                                                                                                                                                                                                                                                    |

## 1. Best stack for “real unlimited permutations, non-deterministic generation”

For a serious production pipeline, the best fit is:

**Replicate or OpenAI for generation → Pinata or Irys for storage → Metaplex Core + Umi for minting → Helius DAS for retrieval/indexing → Magic Eden as the best-documented marketplace API surface of the ones reviewed.**

Why that stack:

Replicate is the strongest choice when “unlimited permutations” really means “many models, many styles, many stochastic outputs, easy model swapping.” Its official API is built around predictions and official models with stable APIs. OpenAI is cleaner if you want one polished image API with first-class edits and fewer moving parts. ([Replicate](https://replicate.com/docs/reference/http), [Replicate](https://replicate.com/docs/topics/models/official-models?utm_source=chatgpt.com), [OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation))

Pinata is the cleanest IPFS upload layer from the official docs I reviewed because it exposes straightforward file and JSON pinning endpoints. Irys is stronger when permanent storage is the goal, but its current primary docs read more SDK-first than simple REST-first. ([docs.pinata.cloud](https://docs.pinata.cloud/api-reference/endpoint/ipfs/pin-file-to-ipfs?utm_source=chatgpt.com), [docs.pinata.cloud](https://docs.pinata.cloud/account-management/api-keys), [Irys Docs](https://docs.irys.xyz/?utm_source=chatgpt.com))

On Solana minting itself, Metaplex’s current direction is clear: for **new projects**, Core is the preferred standard, with Umi or Kit as the client layer. Token Metadata still works, but it is legacy for new projects. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/dev-tools/umi?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/token-metadata/getting-started/js?utm_source=chatgpt.com))

For reads after mint, DAS is the practical standard. Helius gives the cleanest official DAS documentation among the providers checked. ([Helius](https://www.helius.dev/docs/api-reference/das), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com))

So the strongest default stack today is:

**Replicate + Pinata + Metaplex Core/Umi + Helius DAS + Magic Eden**

A simpler variant is:

**OpenAI Images + Pinata + Metaplex Core/Umi + Helius DAS + Magic Eden**

## 2. Example end-to-end architecture

**Generation layer**\
Your backend creates a prompt seed, rarity seed, trait recipe, and negative prompt recipe. It sends the job either to Replicate for multi-model variety or OpenAI for a cleaner single-vendor image workflow. Use temperature-like randomness through seed variation, prompt mutation, style-template rotation, and multi-pass filtering. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation), [Replicate](https://replicate.com/docs/reference/http))

**Metadata layer**\
After an image is approved, generate the NFT JSON metadata with fields like `name`, `description`, `image`, `external_url`, and `attributes`. Those fields line up with the Metaplex metadata patterns documented in Token Metadata. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/token-metadata/token-standard?utm_source=chatgpt.com))

**Storage layer**\
Upload the image first, then upload the metadata JSON that references the image URI. For IPFS, Pinata gives you `pinFileToIPFS` and `pinJSONToIPFS`. For permanence-first systems, swap in Irys. ([docs.pinata.cloud](https://docs.pinata.cloud/api-reference/endpoint/ipfs/pin-file-to-ipfs?utm_source=chatgpt.com), [docs.pinata.cloud](https://docs.pinata.cloud/account-management/api-keys), [Irys Docs](https://docs.irys.xyz/?utm_source=chatgpt.com))

**Minting layer**\
Use Umi with Metaplex Core. Your server prepares the mint payload, but the wallet signs the actual Solana transaction. Core is the current standard for new NFT projects and keeps the mint path simpler and cheaper than legacy Token Metadata. ([Metaplex](https://www.metaplex.com/docs/dev-tools/umi?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/dev-tools/umi/getting-started?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core/create-asset?utm_source=chatgpt.com))

**Chain execution layer**\
Send the transaction through a private RPC provider such as Helius or QuickNode, not Solana’s public endpoint. Solana’s own docs explicitly warn against using the public endpoint for production drops/apps. ([Solana](https://solana.com/docs/references/clusters), [Solana](https://solana.com/docs/payments/interacting-with-solana?utm_source=chatgpt.com))

**Read/index/list layer**\
Once minted, index with DAS through Helius or QuickNode. For marketplace visibility and trading actions, Magic Eden currently has the clearest official data and instruction-generation docs among the marketplaces reviewed. ([Helius](https://www.helius.dev/docs/api-reference/das), [Quicknode](https://www.quicknode.com/docs/solana/solana-das-api), [Magic Eden Developer](https://docs.magiceden.io/reference/get_instructions-buy-now?utm_source=chatgpt.com), [Magic Eden Developer](https://docs.magiceden.io/reference/get_collections?utm_source=chatgpt.com))

A clean flow looks like this:

`Prompt engine -> image API -> moderation/QA -> Pinata/Irys upload -> metadata JSON upload -> Metaplex Core mint tx via Umi -> send through Helius/QuickNode -> index via DAS -> surface/list through marketplace integrations`

## 3. Warnings about deprecated or legacy Solana NFT minting methods

The most important warning is this: **do not build a new production NFT pipeline around legacy Token Metadata assumptions unless you specifically need backward compatibility.** Metaplex says Core is the modern standard and Token Metadata is legacy for new projects. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core/tm-differences?utm_source=chatgpt.com))

If you use Candy Machine, be careful about versioning. Metaplex’s docs note that the older `initialize` instruction is deprecated in favor of `initializeV2`, and new projects should use **Core Candy Machine** rather than legacy Candy Machine paths where possible. Core Candy Machine is the launch/distribution path for Core assets; Candy Machine V3 is for legacy Token Metadata NFTs. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/candy-machine/pnfts?utm_source=chatgpt.com), [Metaplex](https://metaplex.com/docs/smart-contracts/core-candy-machine?utm_source=chatgpt.com), [Metaplex](https://metaplex.com/docs/smart-contracts/core-candy-machine/overview?utm_source=chatgpt.com))

Do not use **Bundlr** for a new build. The package is deprecated and Metaplex’s own Umi uploader docs tell you to use the Irys uploader instead. ([npm](https://www.npmjs.com/package/%40bundlr-network/client?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/dev-tools/umi/implementations?utm_source=chatgpt.com))

Do not use **NFT.Storage Classic uploads** for a new pipeline. Their official docs say uploads have been decommissioned. ([NFT.Storage](https://classic-app.nft.storage/api-docs/), [GitHub](https://github.com/nftstorage/python-client?utm_source=chatgpt.com))

Do not plan around Solana’s **public RPC** for a real drop or automated minting backend. The official Solana docs say it is not intended for production. ([Solana](https://solana.com/docs/references/clusters), [Solana](https://solana.com/docs/payments/interacting-with-solana?utm_source=chatgpt.com))

One more non-Solana but pipeline-relevant warning: OpenAI’s DALL·E 2 and DALL·E 3 are deprecated in the current image docs, so for a fresh build you should target the GPT Image family instead. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation))

## Bottom line

If you want the safest current stack for a production Solana NFT pipeline, build it around **Metaplex Core + Umi + private RPC + DAS + Pinata/Irys + OpenAI or Replicate**. That is the path most aligned with the docs as they exist right now. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/das), [OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation), [docs.pinata.cloud](https://docs.pinata.cloud/api-reference/endpoint/ipfs/pin-file-to-ipfs?utm_source=chatgpt.com))

I can turn this into a **copy-pasteable reference implementation architecture** next, with exact request examples for each stage.


#### You:
##################################################
# CORE MODE
##################################################

ENV=development
DRY_RUN=true
MAINNET=true

##################################################
# AI IMAGE GENERATION (5)
##################################################

AI_PROVIDER=openai

# 1. OpenAI
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_ENDPOINT=/images/generations
OPENAI_API_KEY=

# 2. Stability AI
STABILITY_BASE_URL=https://api.stability.ai/v1
STABILITY_IMAGE_ENDPOINT=/generation/{engine_id}/text-to-image
STABILITY_API_KEY=

# 3. Replicate
REPLICATE_BASE_URL=https://api.replicate.com/v1
REPLICATE_PREDICTIONS_ENDPOINT=/predictions
REPLICATE_API_KEY=

# 4. HuggingFace Inference
HF_BASE_URL=https://api-inference.huggingface.co/models
HF_API_KEY=

# 5. DeepAI
DEEPAI_BASE_URL=https://api.deepai.org/api
DEEPAI_IMAGE_ENDPOINT=/text2img
DEEPAI_API_KEY=

##################################################
# STORAGE (IPFS / ARWEAVE) (6)
##################################################

STORAGE_PROVIDER=pinata

# 6. Pinata
PINATA_BASE_URL=https://api.pinata.cloud
PINATA_FILE_ENDPOINT=/pinning/pinFileToIPFS
PINATA_JSON_ENDPOINT=/pinning/pinJSONToIPFS
PINATA_JWT=

# 7. NFT.storage
NFT_STORAGE_BASE_URL=https://api.nft.storage
NFT_STORAGE_UPLOAD_ENDPOINT=/upload
NFT_STORAGE_API_KEY=

# 8. Web3.Storage
WEB3_STORAGE_BASE_URL=https://api.web3.storage
WEB3_STORAGE_UPLOAD_ENDPOINT=/upload
WEB3_STORAGE_API_KEY=

# 9. Irys (Arweave)
IRYS_BASE_URL=https://node1.irys.xyz
IRYS_UPLOAD_ENDPOINT=/tx

# 10. Bundlr (legacy but used)
BUNDLR_BASE_URL=https://node1.bundlr.network
BUNDLR_UPLOAD_ENDPOINT=/tx

# 11. ArDrive
ARDRIVE_BASE_URL=https://api.ardrive.io

##################################################
# SOLANA RPC (8)
##################################################

RPC_PROVIDER=helius

# 12. Helius
HELIUS_RPC_URL=https://rpc.helius.xyz/?api-key=
HELIUS_DAS_URL=https://api.helius.xyz/v0

# 13. QuickNode
QUICKNODE_RPC_URL=https://your-endpoint.solana-mainnet.quiknode.pro/

# 14. Alchemy
ALCHEMY_RPC_URL=https://solana-mainnet.g.alchemy.com/v2/

# 15. Triton RPC
TRITON_RPC_URL=https://rpc.triton.one

# 16. GenesysGo (Shadow RPC)
GENESYSGO_RPC_URL=https://ssc-dao.genesysgo.net

# 17. Ankr
ANKR_RPC_URL=https://rpc.ankr.com/solana

# 18. Chainstack
CHAINSTACK_RPC_URL=https://nd-xxxx.solana-mainnet.chainstacklabs.com

# 19. Public fallback
SOLANA_PUBLIC_RPC=https://api.mainnet-beta.solana.com

##################################################
# INDEXING / DATA (3)
##################################################

# 20. Helius DAS
HELIUS_DAS_ASSETS=/addresses/{address}/assets

# 21. SimpleHash (NFT data)
SIMPLEHASH_BASE_URL=https://api.simplehash.com/api/v0
SIMPLEHASH_NFT_ENDPOINT=/nfts/assets
SIMPLEHASH_API_KEY=

# 22. Covalent
COVALENT_BASE_URL=https://api.covalenthq.com/v1
COVALENT_API_KEY=

##################################################
# MINTING (METAPLEX CORE)
##################################################

NFT_STANDARD=metaplex

METAPLEX_TOKEN_METADATA_PROGRAM=metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s

##################################################
# MARKETPLACES (5)
##################################################

MARKETPLACE=magiceden

# 23. Magic Eden
MAGICEDEN_BASE_URL=https://api-mainnet.magiceden.dev
MAGICEDEN_LIST_ENDPOINT=/v2/instructions/sell

# 24. Tensor (pro traders)
TENSOR_BASE_URL=https://api.tensor.so
TENSOR_LIST_ENDPOINT=/api/v1/list

# 25. Hyperspace
HYPERSPACE_BASE_URL=https://api.hyperspace.xyz

# 26. CoralCube
CORALCUBE_BASE_URL=https://api.coralcube.io

# 27. Exchange Art
EXCHANGEART_BASE_URL=https://api.exchange.art

##################################################
# WALLET / SIGNING
##################################################

WALLET_PRIVATE_KEY=
WALLET_PUBLIC_KEY=

##################################################
# NFT PARAMETERS
##################################################

NFT_NAME=AI_GENERATED_ASSET
NFT_SYMBOL=AI
NFT_SELLER_FEE_BPS=500
DEFAULT_LIST_PRICE_SOL=1.0

##################################################
# PIPELINE CONTROL
##################################################

AUTO_MINT=true
AUTO_LIST=true
AUTO_RETRY=true

##################################################
# PERFORMANCE
##################################################

BATCH_SIZE=10
MAX_PARALLEL_MINTS=3

##################################################
# LOGGING
##################################################

LOG_LEVEL=INFO

##################################################
# ADVANCED FEATURES
##################################################

ENABLE_RPC_FAILOVER=true
ENABLE_MARKET_ARB=false
AUTO_RELIST=false I checked the current primary docs and filtered out stale blog-style material. The biggest practical change is that Solana’s own public RPC is explicitly not for production, while Metaplex’s current direction for new NFT projects is Core + Umi/Kit, with DAS used as the read/indexing layer and third-party RPC providers used for production traffic. NFT.Storage Classic uploads are decommissioned, Bundlr has been superseded by Irys, and some older image/NFT paths are now legacy.  

Service	Purpose	Official Base URL	Key Endpoints	Auth	Mainnet Ready	Notes
Solana public RPC	Base chain RPC	https://api.mainnet.solana.com	JSON-RPC methods such as sendTransaction, getAccountInfo, getProgramAccounts; WS at wss://<address>/	None	No for production	Official, current public endpoint. Mainnet public rate limits shown as 100 req/10s/IP, 40 req/10s/IP per single RPC, 40 concurrent connections, 100 MB/30s. Solana says public RPC is not intended for production apps.  
Helius RPC	Production Solana RPC	https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY	Standard Solana JSON-RPC over your Helius endpoint	API key in query string	Yes	Official third-party production RPC. Helius documents subscription-tier rate limits and quotas rather than one universal fixed limit.  
Helius DAS	NFT / asset read & indexing	https://mainnet.helius-rpc.com/?api-key=YOUR_API_KEY	DAS methods including getAsset, getAssetsByOwner, searchAssets	API key	Yes	Official third-party DAS implementation on Solana mainnet. Good for indexing and retrieval, not minting.  
QuickNode RPC	Production Solana RPC	https://your-endpoint.quiknode.pro/auth-token/	Standard Solana JSON-RPC over endpoint URL	Endpoint token in URL; other security options available	Yes	Official third-party production RPC. QuickNode’s docs show tokenized endpoint URLs and WSS equivalents.  
QuickNode DAS add-on	NFT / asset read & indexing	Your QuickNode Solana endpoint with DAS add-on enabled	DAS methods including getAsset, getAssetsByOwner, searchAssets	Endpoint auth + DAS add-on	Yes	Official third-party. QuickNode says Metaplex DAS is available by enabling the add-on on your endpoint. Add-on pricing is tied to plan/sales; marketplace page says it can use base-plan RPS and has no monthly request limits.  
Metaplex Core	Current NFT asset standard for new projects	On-chain Solana program / SDK-first, not a standalone REST API	Create assets/collections via Core SDK and on-chain transactions	Wallet signing	Yes	Official. Metaplex says Token Metadata is legacy for new projects and Core is the next-gen standard. Best choice for new one-by-one mint pipelines.  
Metaplex Umi	JS client framework for minting/signing	SDK / RPC-backed, not a standalone REST API	Connect RPC, connect wallet, send transactions	Wallet signer + chosen RPC	Yes	Official SDK. Umi is the framework layer you use to build and sign mint transactions.  
Metaplex Token Metadata	Legacy but still supported NFT standard	On-chain Solana program / SDK-first	Metadata account attachment, mint flows, fetch/update/transfer helpers	Wallet signing	Yes	Official. Still works, but Core is preferred for new projects. Useful when you need legacy ecosystem compatibility.  
Metaplex DAS spec/docs	Asset read standard	Provider-backed JSON-RPC, not a separate public base URL from Metaplex itself	getAsset and other DAS methods	Depends on provider	Yes through provider	Official standard/docs, but you access it through a provider such as Helius or QuickNode.  
Magic Eden API	Marketplace data + trading instruction generation	https://api-mainnet.magiceden.dev	Data: GET /v2/tokens/{token_mint}, GET /v2/collections; trading instruction example: GET /v2/instructions/buy_now	Public for some endpoints; Bearer auth shown for trading instruction docs; Solana API keys page exists	Yes, with caveats	Official third-party marketplace API. The docs clearly expose data endpoints and trading instruction generation. I did not find a clearly documented public “create listing” endpoint in the official Solana docs I reviewed, so treat automated listing support as partial / gated until you verify your account’s access.  
Tensor	NFT marketplace / liquidity venue	No public API base URL clearly exposed in the official docs I found	Marketplace features documented; no clean public REST listing API path surfaced in reviewed official docs	Not clearly documented in reviewed API docs	Yes as marketplace, unclear as public API	Official Tensor docs confirm marketplace support, collection-wide bids, listings, and market-making, but I did not find a primary-source public developer API reference with exact listing endpoints comparable to Magic Eden.  
Pinata	IPFS upload for media + metadata JSON	https://api.pinata.cloud	POST /pinning/pinFileToIPFS, POST /pinning/pinJSONToIPFS	API key / scoped keys	Yes	Official third-party IPFS service. Pinata docs show scoped API keys; good default hot-storage/IPFS option.  
NFT.Storage Classic	Storage	https://api.nft.storage	Classic upload docs exist, but uploads are decommissioned	API token	No for new uploads	Official but decommissioned for uploads. Do not use for a new production mint pipeline.  
Irys	Permanent storage / Arweave-oriented data layer	Docs emphasize Irys APIs and tools; public docs also reference node.irys.xyz historically, but the current primary docs I reviewed are SDK/docs-first rather than giving one clean REST upload path	Use Irys SDK / tooling for uploads and retrieval	Wallet/key-based via SDK	Yes	Official third-party. Current docs describe Irys as the permanent programmable data layer and the successor path from Bundlr. Irys is a valid permanence layer, but their current docs are more SDK-oriented than the simple REST style used by Pinata.  
Bundlr	Historical uploader path	N/A	N/A	N/A	Legacy only	Deprecated. The old @bundlr-network/client package is deprecated and points developers to @irys/sdk. Umi’s docs also mark Bundlr uploader support deprecated in favor of umi-uploader-irys.  
OpenAI Images	AI image generation / edits	https://api.openai.com/v1	POST /images/generations, POST /images/edits; also Responses API image tool via POST /responses	Bearer API key	Yes	Official third-party. Current docs recommend GPT Image models; DALL·E 2 and 3 are deprecated and scheduled to stop being supported on 2026-05-12. Pricing for gpt-image-1.5 is published, including per-image examples.  
Stability AI API	AI image generation / edits	https://api.stability.ai	Current REST docs are under the v2beta platform; the reviewed official docs describe Stable Image services and the REST API as the primary API service	API key	Yes	Official third-party. Docs say REST v2beta became the primary API service as of March 2024. Rate limit shown is 150 requests / 10 seconds with 429 and 60-second timeout on excess. Pricing is credit-based, with 1 credit = $0.01.  
Replicate	Multi-model AI generation	https://api.replicate.com/v1	Official-model predictions: POST /models/{model_owner}/{model_name}/predictions	Bearer API token	Yes	Official third-party. Good when you want many image models and non-deterministic permutations. Rate limits published: 600 prediction-creation requests/minute and 3000 other requests/minute. Pricing is model/hardware-based.  

1. Best stack for “real unlimited permutations, non-deterministic generation”

For a serious production pipeline, the best fit is:

Replicate or OpenAI for generation → Pinata or Irys for storage → Metaplex Core + Umi for minting → Helius DAS for retrieval/indexing → Magic Eden as the best-documented marketplace API surface of the ones reviewed.

Why that stack:

Replicate is the strongest choice when “unlimited permutations” really means “many models, many styles, many stochastic outputs, easy model swapping.” Its official API is built around predictions and official models with stable APIs. OpenAI is cleaner if you want one polished image API with first-class edits and fewer moving parts.  

Pinata is the cleanest IPFS upload layer from the official docs I reviewed because it exposes straightforward file and JSON pinning endpoints. Irys is stronger when permanent storage is the goal, but its current primary docs read more SDK-first than simple REST-first.  

On Solana minting itself, Metaplex’s current direction is clear: for new projects, Core is the preferred standard, with Umi or Kit as the client layer. Token Metadata still works, but it is legacy for new projects.  

For reads after mint, DAS is the practical standard. Helius gives the cleanest official DAS documentation among the providers checked.  

So the strongest default stack today is:

Replicate + Pinata + Metaplex Core/Umi + Helius DAS + Magic Eden

A simpler variant is:

OpenAI Images + Pinata + Metaplex Core/Umi + Helius DAS + Magic Eden

2. Example end-to-end architecture

Generation layer
Your backend creates a prompt seed, rarity seed, trait recipe, and negative prompt recipe. It sends the job either to Replicate for multi-model variety or OpenAI for a cleaner single-vendor image workflow. Use temperature-like randomness through seed variation, prompt mutation, style-template rotation, and multi-pass filtering.  

Metadata layer
After an image is approved, generate the NFT JSON metadata with fields like name, description, image, external_url, and attributes. Those fields line up with the Metaplex metadata patterns documented in Token Metadata.  

Storage layer
Upload the image first, then upload the metadata JSON that references the image URI. For IPFS, Pinata gives you pinFileToIPFS and pinJSONToIPFS. For permanence-first systems, swap in Irys.  

Minting layer
Use Umi with Metaplex Core. Your server prepares the mint payload, but the wallet signs the actual Solana transaction. Core is the current standard for new NFT projects and keeps the mint path simpler and cheaper than legacy Token Metadata.  

Chain execution layer
Send the transaction through a private RPC provider such as Helius or QuickNode, not Solana’s public endpoint. Solana’s own docs explicitly warn against using the public endpoint for production drops/apps.  

Read/index/list layer
Once minted, index with DAS through Helius or QuickNode. For marketplace visibility and trading actions, Magic Eden currently has the clearest official data and instruction-generation docs among the marketplaces reviewed.  

A clean flow looks like this:

Prompt engine -> image API -> moderation/QA -> Pinata/Irys upload -> metadata JSON upload -> Metaplex Core mint tx via Umi -> send through Helius/QuickNode -> index via DAS -> surface/list through marketplace integrations

3. Warnings about deprecated or legacy Solana NFT minting methods

The most important warning is this: do not build a new production NFT pipeline around legacy Token Metadata assumptions unless you specifically need backward compatibility. Metaplex says Core is the modern standard and Token Metadata is legacy for new projects.  

If you use Candy Machine, be careful about versioning. Metaplex’s docs note that the older initialize instruction is deprecated in favor of initializeV2, and new projects should use Core Candy Machine rather than legacy Candy Machine paths where possible. Core Candy Machine is the launch/distribution path for Core assets; Candy Machine V3 is for legacy Token Metadata NFTs.  

Do not use Bundlr for a new build. The package is deprecated and Metaplex’s own Umi uploader docs tell you to use the Irys uploader instead.  

Do not use NFT.Storage Classic uploads for a new pipeline. Their official docs say uploads have been decommissioned.  

Do not plan around Solana’s public RPC for a real drop or automated minting backend. The official Solana docs say it is not intended for production.  

One more non-Solana but pipeline-relevant warning: OpenAI’s DALL·E 2 and DALL·E 3 are deprecated in the current image docs, so for a fresh build you should target the GPT Image family instead.  

Bottom line

If you want the safest current stack for a production Solana NFT pipeline, build it around Metaplex Core + Umi + private RPC + DAS + Pinata/Irys + OpenAI or Replicate. That is the path most aligned with the docs as they exist right now.  

I can turn this into a copy-pasteable reference implementation architecture next, with exact request examples for each stage.

##################################################
# HEALTH
##################################################

ENABLE_HEALTHCHECK=true
HEALTHCHECK_PORT=8787

#### ChatGPT:
I’m checking each endpoint in your env against the current primary docs and pruning anything legacy, unsafe, or mislabeled. After that I’ll give you a corrected production-ready `.env` block.


#### ChatGPT:
I found a few concrete mismatches already: your Helius DAS path is using the wrong shape, your Solana public fallback hostname is stale, and a couple of storage/image entries are legacy now. I’m locking down the exact replacements so the corrected env doesn’t carry hidden footguns.


#### ChatGPT:
Your `.env` is close in shape, but it mixes **current production entries** with **legacy or misleading ones**. The biggest fixes are: use a **private RPC** and keep Solana public RPC only as a last-resort diagnostic fallback; switch **Helius DAS** to the JSON-RPC DAS methods on your main Helius RPC endpoint instead of the old REST-style `/v0` pattern you wrote; use **Metaplex Core** for new NFT projects instead of wiring your mint path around legacy Token Metadata; keep **Pinata** as the simplest current upload target; treat **NFT.Storage Classic** as decommissioned for new uploads; treat **Bundlr** as legacy and prefer **Irys**; keep **Magic Eden’s `/v2/instructions/sell`** if you want automated listing instructions; and for OpenAI use the Images API with **GPT Image models**, not DALL·E as your default. ([Solana](https://solana.com/docs/references/clusters?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [NFT.Storage](https://classic-app.nft.storage/docs/?utm_source=chatgpt.com), [Magic Eden Developer](https://docs.magiceden.io/reference/get_instructions-sell?utm_source=chatgpt.com), [OpenAI Developers](https://developers.openai.com/api/llms-full.txt))

The single biggest hidden bug in your file is this: `HELIUS_DAS_URL=https://api.helius.xyz/v0` plus `HELIUS_DAS_ASSETS=/addresses/{address}/assets`. Helius’ current DAS docs expose **DAS as JSON-RPC methods** like `getAsset`, `getAssetsByOwner`, and `searchAssets` against `https://mainnet.helius-rpc.com/?api-key=...`, not the REST path pattern you have here. ([Helius](https://www.helius.dev/docs/api-reference/das/getasset?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/das/getassetsbyowner?utm_source=chatgpt.com))

Your Solana fallback URL should also be updated. The current Solana docs show `https://api.mainnet.solana.com` as the public mainnet endpoint, and Solana explicitly says its public RPC endpoints are **not intended for production applications**. ([Solana](https://solana.com/docs/references/clusters?utm_source=chatgpt.com), [Solana](https://solana.com/docs/rpc?utm_source=chatgpt.com))

For minting, your env says “METAPLEX CORE” but then pins the **Token Metadata** program id. That is internally inconsistent. Metaplex’s current docs say **Core is the recommended NFT standard for new projects**, Token Metadata is **legacy for new projects**, and Core uses the `MPL Core` program id `CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d`. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core/tm-differences?utm_source=chatgpt.com))

For listing, the part you chose for Magic Eden is actually good: the official docs do expose `GET https://api-mainnet.magiceden.dev/v2/instructions/sell` for listing instructions. ([Magic Eden Developer](https://docs.magiceden.io/reference/get_instructions-sell?utm_source=chatgpt.com))

For image generation, OpenAI’s current image docs still support `POST /v1/images/generations`, but the recommended models are the **GPT Image** family such as `gpt-image-1.5`; DALL·E 2 and 3 are marked deprecated and support ends on **May 12, 2026**. Replicate’s current official prediction flow and rate limits are also current. Stability’s primary REST docs are under the current API reference with a documented **150 requests / 10 seconds** limit. ([OpenAI Developers](https://developers.openai.com/api/llms-full.txt), [OpenAI Developers](https://developers.openai.com/api/llms-full.txt), [OpenAI Developers](https://developers.openai.com/api/llms-full.txt), [Replicate](https://replicate.com/docs/reference/http?utm_source=chatgpt.com), [Stability AI](https://platform.stability.ai/docs/api-reference?utm_source=chatgpt.com))

For storage, **Pinata** is still valid, though its docs now clearly distinguish legacy pinning endpoints from newer V3-style API/key flows. NFT.Storage Classic says uploads are decommissioned. Web3.Storage says its **new upload API replaced the old `/upload` API**. ([Pinata Docs](https://docs.pinata.cloud/api-reference/endpoint/ipfs/pin-json-to-ipfs?utm_source=chatgpt.com), [Pinata Docs](https://docs.pinata.cloud/sdk/v2-migration-guide?utm_source=chatgpt.com), [NFT.Storage](https://classic-app.nft.storage/docs/?utm_source=chatgpt.com), [Web3.Storage Blog](https://blog.web3.storage/posts/the-data-layer-is-here-with-the-new-web3-storage?utm_source=chatgpt.com))

Here is the cleaned production-ready version I would actually use:

```dotenv
##################################################
# CORE MODE
##################################################

ENV=development
DRY_RUN=true
MAINNET=true

##################################################
# AI IMAGE GENERATION
##################################################

AI_PROVIDER=openai

# OpenAI (recommended default)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_ENDPOINT=/images/generations
OPENAI_IMAGE_MODEL=gpt-image-1.5
OPENAI_API_KEY=

# Stability AI (optional fallback)
STABILITY_BASE_URL=https://api.stability.ai
STABILITY_IMAGE_ENDPOINT=/v2beta/stable-image/generate/core
STABILITY_API_KEY=

# Replicate (best for multi-model permutations)
REPLICATE_BASE_URL=https://api.replicate.com/v1
# Use model-scoped predictions in code when possible
# Example pattern: /models/{owner}/{name}/predictions
REPLICATE_PREDICTIONS_ENDPOINT=/predictions
REPLICATE_API_KEY=

# Optional experimental providers below are not part of the validated core stack
HF_BASE_URL=
HF_API_KEY=
DEEPAI_BASE_URL=
DEEPAI_IMAGE_ENDPOINT=
DEEPAI_API_KEY=

##################################################
# STORAGE
##################################################

STORAGE_PROVIDER=pinata

# Pinata (recommended default)
PINATA_BASE_URL=https://api.pinata.cloud
PINATA_FILE_ENDPOINT=/pinning/pinFileToIPFS
PINATA_JSON_ENDPOINT=/pinning/pinJSONToIPFS
PINATA_JWT=

# Irys (recommended permanence layer instead of Bundlr)
IRYS_BASE_URL=https://node1.irys.xyz
IRYS_UPLOAD_ENDPOINT=/tx

# Legacy / disabled
NFT_STORAGE_ENABLED=false
NFT_STORAGE_BASE_URL=
NFT_STORAGE_UPLOAD_ENDPOINT=
NFT_STORAGE_API_KEY=

WEB3_STORAGE_ENABLED=false
WEB3_STORAGE_BASE_URL=
WEB3_STORAGE_UPLOAD_ENDPOINT=
WEB3_STORAGE_API_KEY=

BUNDLR_ENABLED=false
BUNDLR_BASE_URL=
BUNDLR_UPLOAD_ENDPOINT=

ARDRIVE_ENABLED=false
ARDRIVE_BASE_URL=

##################################################
# SOLANA RPC
##################################################

RPC_PROVIDER=helius

# Helius main RPC + DAS via JSON-RPC methods on the same endpoint
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=
HELIUS_DAS_METHOD_GET_ASSET=getAsset
HELIUS_DAS_METHOD_GET_ASSETS_BY_OWNER=getAssetsByOwner
HELIUS_DAS_METHOD_SEARCH_ASSETS=searchAssets

# Optional additional RPC providers
QUICKNODE_RPC_URL=
ALCHEMY_RPC_URL=https://solana-mainnet.g.alchemy.com/v2/
ANKR_RPC_URL=https://rpc.ankr.com/solana
CHAINSTACK_RPC_URL=

# Public fallback: diagnostics only, not production traffic
SOLANA_PUBLIC_RPC=https://api.mainnet.solana.com

##################################################
# NFT STANDARD / MINTING
##################################################

NFT_STANDARD=metaplex_core

# Current Core program id
METAPLEX_CORE_PROGRAM_ID=CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d

# Legacy only; keep disabled unless you intentionally support TM NFTs
TOKEN_METADATA_ENABLED=false
METAPLEX_TOKEN_METADATA_PROGRAM=metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s

##################################################
# MARKETPLACE
##################################################

MARKETPLACE=magiceden

MAGICEDEN_BASE_URL=https://api-mainnet.magiceden.dev
MAGICEDEN_LIST_ENDPOINT=/v2/instructions/sell

# Keep these disabled until separately verified and implemented
TENSOR_ENABLED=false
TENSOR_BASE_URL=
TENSOR_LIST_ENDPOINT=

HYPERSPACE_ENABLED=false
HYPERSPACE_BASE_URL=

CORALCUBE_ENABLED=false
CORALCUBE_BASE_URL=

EXCHANGEART_ENABLED=false
EXCHANGEART_BASE_URL=

##################################################
# WALLET / SIGNING
##################################################

WALLET_PRIVATE_KEY=
WALLET_PUBLIC_KEY=

##################################################
# NFT PARAMETERS
##################################################

NFT_NAME=AI_GENERATED_ASSET
NFT_SYMBOL=AI
NFT_SELLER_FEE_BPS=500
DEFAULT_LIST_PRICE_SOL=1.0

##################################################
# PIPELINE CONTROL
##################################################

AUTO_MINT=true
AUTO_LIST=true
AUTO_RETRY=true

##################################################
# PERFORMANCE
##################################################

BATCH_SIZE=10
MAX_PARALLEL_MINTS=3

##################################################
# LOGGING
##################################################

LOG_LEVEL=INFO

##################################################
# ADVANCED FEATURES
##################################################

ENABLE_RPC_FAILOVER=true
ENABLE_MARKET_ARB=false
AUTO_RELIST=false

##################################################
# HEALTH
##################################################

ENABLE_HEALTHCHECK=true
HEALTHCHECK_PORT=8787
```

Why I changed it:

`SOLANA_PUBLIC_RPC` changed because the current Solana docs show `https://api.mainnet.solana.com`, and public RPC is explicitly non-production. ([Solana](https://solana.com/docs/references/clusters?utm_source=chatgpt.com), [Solana](https://solana.com/docs/rpc?utm_source=chatgpt.com))

`HELIUS_RPC_URL` changed because Helius’ current mainnet endpoint is `https://mainnet.helius-rpc.com/?api-key=...`, and DAS is called through JSON-RPC methods like `getAsset` and `getAssetsByOwner` on that endpoint. ([Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/endpoints?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/das/getassetsbyowner?utm_source=chatgpt.com))

`NFT_STANDARD` changed to `metaplex_core` and I added `METAPLEX_CORE_PROGRAM_ID` because Core is the recommended standard for new projects and Token Metadata is legacy for new ones. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core/tm-differences?utm_source=chatgpt.com))

I disabled `NFT_STORAGE_*`, `WEB3_STORAGE_*`, and `BUNDLR_*` because NFT.Storage Classic uploads are decommissioned, web3.storage says the new upload API replaced the old upload API, and Bundlr has been superseded by Irys. ([NFT.Storage](https://classic-app.nft.storage/docs/?utm_source=chatgpt.com), [Web3.Storage Blog](https://blog.web3.storage/posts/the-data-layer-is-here-with-the-new-web3-storage?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com))

I kept `MAGICEDEN_LIST_ENDPOINT=/v2/instructions/sell` because that exact official listing-instruction endpoint exists in the current Magic Eden docs. ([Magic Eden Developer](https://docs.magiceden.io/reference/get_instructions-sell?utm_source=chatgpt.com))

I set `OPENAI_IMAGE_MODEL=gpt-image-1.5` because OpenAI recommends GPT Image models now and marks DALL·E 2/3 deprecated. ([OpenAI Developers](https://developers.openai.com/api/llms-full.txt), [OpenAI Developers](https://developers.openai.com/api/llms-full.txt))

The pieces I would drop from the validated “core stack” for now are Hugging Face Inference, DeepAI, SimpleHash, Covalent, Hyperspace, CoralCube, and Exchange Art. Not because they are necessarily unusable, but because they were **not part of the current official stack you asked to validate earlier**, and the cleanest production posture is to keep only the components you have primary-source confidence in. That keeps your pipeline smaller, safer, and easier to audit.

The final stack I’d actually run from this env is:

**OpenAI or Replicate → Pinata or Irys → Metaplex Core → Helius RPC/DAS → Magic Eden instructions**. ([OpenAI Developers](https://developers.openai.com/api/llms-full.txt), [Replicate](https://replicate.com/docs/reference/http?utm_source=chatgpt.com), [Pinata Docs](https://docs.pinata.cloud/api-reference/endpoint/ipfs/pin-json-to-ipfs?utm_source=chatgpt.com), [Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com), [Magic Eden Developer](https://docs.magiceden.io/reference/get_instructions-sell?utm_source=chatgpt.com))

I can next turn this into a **single-file production `.env.example` plus a matching Python config loader and provider router**.


#### You:
##################################################
# APP IDENTITY
##################################################

APP_NAME=solana_ai_nft_pipeline
APP_VERSION=1.0.0
APP_ENV=development
APP_REGION=global
NODE_ENV=development

##################################################
# RUNTIME MODES
##################################################

DRY_RUN=true
MAINNET=false
SAFE_MODE=true
READ_ONLY_MODE=false
MAINTENANCE_MODE=false

##################################################
# EXECUTION PROFILE
##################################################

PROFILE=staging
ENABLE_EXPERIMENTAL=false
ENABLE_ALIEN_MODE=true
ENABLE_NONDETERMINISM=true

##################################################
# CHAIN TARGET
##################################################

CHAIN=solana
SOLANA_CLUSTER=devnet
SOLANA_COMMITMENT=confirmed
SOLANA_FINALITY=finalized

##################################################
# WALLET / SIGNING
##################################################

WALLET_MODE=private_key
WALLET_PRIVATE_KEY=
WALLET_PUBLIC_KEY=
WALLET_ENCRYPTED=false
WALLET_KEY_ALIAS=primary
REQUIRE_WALLET_MATCH=true
BLOCK_IF_EMPTY_WALLET=true

##################################################
# MINT STANDARD
##################################################

NFT_STANDARD=metaplex_core
NFT_COLLECTION_MODE=single_assets
NFT_SYMBOL=AI
NFT_DEFAULT_NAME=AI_GENERATED_ASSET
NFT_SELLER_FEE_BPS=500
NFT_MUTABLE=true
NFT_MAX_SUPPLY=1

##################################################
# PROGRAM IDS
##################################################

METAPLEX_TOKEN_METADATA_PROGRAM=metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s

##################################################
# GLOBAL PROVIDER SELECTION
##################################################

AI_PROVIDER=openai
STORAGE_PROVIDER=pinata
RPC_PROVIDER=helius
INDEX_PROVIDER=helius
MARKETPLACE_PROVIDER=magiceden

AI_PROVIDER_PRIORITY=openai,replicate,stability,hf,deepai
STORAGE_PROVIDER_PRIORITY=pinata,irys,ardrive
RPC_PROVIDER_PRIORITY=helius,quicknode,triton,ankr,public
INDEX_PROVIDER_PRIORITY=helius,quicknode
MARKETPLACE_PROVIDER_PRIORITY=magiceden,tensor

##################################################
# AI GENERATION CORE
##################################################

ENABLE_AI_GENERATION=true
AI_REQUEST_TIMEOUT_MS=120000
AI_MAX_RETRIES=3
AI_RETRY_BACKOFF_MS=2500
AI_RETRY_BACKOFF_MULTIPLIER=2
AI_CIRCUIT_BREAKER_ENABLED=true
AI_CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
AI_CIRCUIT_BREAKER_RESET_MS=60000

##################################################
# AI NON-DETERMINISTIC / ALIEN MODE
##################################################

ENABLE_RANDOM_SEED=true
SEED_STRATEGY=random
PROMPT_MUTATION_LEVEL=high
PROMPT_MUTATION_PROVIDER=openai
TRAIT_RANDOMIZATION=true
TRAIT_WEIGHTING_MODE=weighted
ENABLE_NEGATIVE_PROMPTS=true
ENABLE_STYLE_ROTATION=true
ENABLE_TEMPLATE_ROTATION=true
ENABLE_PROMPT_CROSSBREED=true
ENABLE_ENTROPY_SALT=true
ENTROPY_SALT_LENGTH=16
MAX_VARIANTS_PER_PROMPT=4
MAX_PROMPT_EXPANSIONS=3
MAX_REJECTION_SAMPLING_ROUNDS=2
ALIEN_MODE_VISUAL_DRIFT=0.72
ALIEN_MODE_SEMANTIC_DRIFT=0.48
ALIEN_MODE_SYMBOLIC_INTRUSION=0.31

##################################################
# AI CONTENT POLICY / GUARDRAILS
##################################################

ENABLE_PROMPT_SANITIZATION=true
ENABLE_OUTPUT_MODERATION=false
BLOCK_SAFETY_FAILURES=true
ALLOW_NSFW=false
ALLOW_TRADEMARK_RISK=false

##################################################
# AI PROVIDERS
##################################################

# OpenAI
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=
OPENAI_IMAGE_ENDPOINT=/images/generations
OPENAI_EDIT_ENDPOINT=/images/edits
OPENAI_MODEL_IMAGE=gpt-image-1
OPENAI_MODEL_METADATA=gpt-4.1-mini

# Stability AI
STABILITY_BASE_URL=https://api.stability.ai/v1
STABILITY_API_KEY=
STABILITY_IMAGE_ENDPOINT=/generation/{engine_id}/text-to-image
STABILITY_ENGINE_ID=

# Replicate
REPLICATE_BASE_URL=https://api.replicate.com/v1
REPLICATE_API_KEY=
REPLICATE_PREDICTIONS_ENDPOINT=/predictions
REPLICATE_MODEL=

# Hugging Face Inference
HF_BASE_URL=https://api-inference.huggingface.co/models
HF_API_KEY=
HF_MODEL=

# DeepAI
DEEPAI_BASE_URL=https://api.deepai.org/api
DEEPAI_API_KEY=
DEEPAI_IMAGE_ENDPOINT=/text2img

##################################################
# IMAGE GENERATION SETTINGS
##################################################

IMAGE_WIDTH=1024
IMAGE_HEIGHT=1024
IMAGE_FORMAT=png
IMAGE_BACKGROUND=transparent
IMAGE_QUALITY=high
IMAGE_STYLE_PRESET=art
IMAGE_COUNT_PER_REQUEST=1
IMAGE_SAVE_INTERMEDIATES=false
IMAGE_ENABLE_UPSCALING=false
IMAGE_ENABLE_VARIATION_SET=true

##################################################
# QUALITY CONTROL
##################################################

ENABLE_QUALITY_FILTER=true
QUALITY_FILTER_MODE=hybrid
MIN_SCORE_THRESHOLD=0.78
MIN_AESTHETIC_SCORE=0.72
MIN_CLARITY_SCORE=0.65
MIN_NOVELTY_SCORE=0.60
MIN_COMPOSITION_SCORE=0.60
REJECT_DUPLICATES=true
DUPLICATE_HASH_DISTANCE_MAX=8
ENABLE_MANUAL_REVIEW_QUEUE=false
MAX_FAILED_ARTWORKS_PER_BATCH=20

##################################################
# METADATA GENERATION
##################################################

METADATA_AI_ENABLED=true
METADATA_PROVIDER=openai
METADATA_SCHEMA_VERSION=1
METADATA_STYLE=collector_premium
METADATA_MAX_TITLE_LEN=80
METADATA_MAX_DESCRIPTION_LEN=400
METADATA_INCLUDE_ATTRIBUTES=true
METADATA_INCLUDE_EXTERNAL_URL=true
METADATA_INCLUDE_CREATOR=true
METADATA_INCLUDE_ROYALTIES=true
METADATA_ENFORCE_REQUIRED_FIELDS=true
METADATA_STRICT_JSON=true
METADATA_GENERATE_SERIES=true
METADATA_GENERATE_RARITY=true
METADATA_GENERATE_RELEASE_PHASE=true

##################################################
# METADATA DEFAULTS
##################################################

NFT_NAME_PREFIX=
NFT_NAME_SUFFIX=
NFT_SERIES=Alien Mint Cycle
NFT_COLLECTION_NAME=Alien Mint Collection
NFT_CREATOR_NAME=
NFT_CREATOR_URL=
NFT_EXTERNAL_URL=
NFT_DEFAULT_DESCRIPTION=
NFT_DEFAULT_LICENSE=all_rights_reserved
NFT_ATTRIBUTES_MODE=generated

##################################################
# STORAGE CORE
##################################################

ENABLE_STORAGE_UPLOAD=true
STORAGE_REQUEST_TIMEOUT_MS=120000
STORAGE_MAX_RETRIES=3
STORAGE_RETRY_BACKOFF_MS=3000
STORAGE_VERIFY_UPLOADS=true
STORAGE_REQUIRE_CONTENT_ADDRESS=true
STORAGE_PREFER_CANONICAL_URI=true

##################################################
# PINATA
##################################################

PINATA_BASE_URL=https://api.pinata.cloud
PINATA_JWT=
PINATA_FILE_ENDPOINT=/pinning/pinFileToIPFS
PINATA_JSON_ENDPOINT=/pinning/pinJSONToIPFS
PINATA_GROUP_ID=
PINATA_USE_GATEWAY=false

##################################################
# IRYS
##################################################

IRYS_BASE_URL=https://node1.irys.xyz
IRYS_UPLOAD_ENDPOINT=/tx
IRYS_NETWORK=mainnet

##################################################
# ARDRIVE
##################################################

ARDRIVE_BASE_URL=https://api.ardrive.io

##################################################
# LEGACY STORAGE DISABLED
##################################################

ENABLE_NFT_STORAGE=false
NFT_STORAGE_BASE_URL=https://api.nft.storage
NFT_STORAGE_UPLOAD_ENDPOINT=/upload
NFT_STORAGE_API_KEY=

ENABLE_BUNDLR_LEGACY=false
BUNDLR_BASE_URL=https://node1.bundlr.network
BUNDLR_UPLOAD_ENDPOINT=/tx

##################################################
# URI POLICY
##################################################

URI_SCHEME_PREFERRED=ipfs
ALLOW_HTTP_GATEWAY_URI=false
ALLOW_HTTPS_GATEWAY_URI=true
PIN_METADATA_JSON=true
PIN_IMAGE_FILE=true

##################################################
# RPC / CHAIN CONNECTIVITY
##################################################

ENABLE_RPC_FAILOVER=true
RPC_REQUEST_TIMEOUT_MS=30000
RPC_RETRY_COUNT=4
RPC_RETRY_BACKOFF_MS=1500
RPC_RETRY_BACKOFF_MULTIPLIER=2
RPC_HEALTHCHECK_INTERVAL_MS=30000
RPC_FAILOVER_ON_429=true
RPC_FAILOVER_ON_TIMEOUT=true
RPC_FAILOVER_ON_SLOT_STALL=true

##################################################
# SOLANA RPC PROVIDERS
##################################################

# Helius
HELIUS_RPC_URL=https://rpc.helius.xyz/?api-key=
HELIUS_DAS_URL=https://api.helius.xyz/v0
HELIUS_API_KEY=

# QuickNode
QUICKNODE_RPC_URL=https://your-endpoint.solana-mainnet.quiknode.pro/
QUICKNODE_WSS_URL=
QUICKNODE_API_TOKEN=

# Triton
TRITON_RPC_URL=https://rpc.triton.one

# Ankr
ANKR_RPC_URL=https://rpc.ankr.com/solana

# Public fallback
SOLANA_PUBLIC_RPC=https://api.mainnet-beta.solana.com

##################################################
# INDEXING / DAS
##################################################

ENABLE_INDEXING=true
INDEX_REFRESH_DELAY_MS=8000
INDEX_POLL_RETRIES=10
INDEX_POLL_INTERVAL_MS=5000

HELIUS_DAS_ASSETS=/addresses/{address}/assets
HELIUS_DAS_GET_ASSET=/assets/{id}

##################################################
# MINT CONTROL
##################################################

AUTO_MINT=true
MINT_MODE=wallet_signed
MINT_BATCH_SIZE=10
MAX_PARALLEL_MINTS=3
MINT_CONFIRMATION_REQUIRED=true
MINT_WAIT_FOR_FINALITY=true
MINT_SIMULATE_FIRST=true
MINT_ABORT_ON_FIRST_FAILURE=false
MINT_IDEMPOTENCY_ENABLED=true
MINT_IDEMPOTENCY_KEY_PREFIX=solmint

##################################################
# SUPPLY CONTROL
##################################################

ADAPTIVE_SUPPLY=true
MAX_MINTS_PER_HOUR=2
MAX_MINTS_PER_DAY=5
MAX_MINTS_PER_WEEK=20
REQUIRE_PREVIOUS_SALE=false
REQUIRE_INDEX_CONFIRMATION_BEFORE_NEXT_MINT=true
COOLDOWN_BETWEEN_MINTS_MS=60000

##################################################
# PRICE / LISTING DEFAULTS
##################################################

AUTO_LIST=false
DEFAULT_LIST_PRICE_SOL=1.0
DEFAULT_PRICE_STRATEGY=fixed
MIN_LIST_PRICE_SOL=0.05
MAX_LIST_PRICE_SOL=50
ENABLE_AUTO_RELIST=false
RELIST_COOLDOWN_MINUTES=120
PRICE_UNDERCUT_BPS=0
PRICE_PREMIUM_BPS=0

##################################################
# MARKETPLACE INTEGRATIONS
##################################################

MARKETPLACE=magiceden

# Magic Eden
MAGICEDEN_BASE_URL=https://api-mainnet.magiceden.dev
MAGICEDEN_LIST_ENDPOINT=/v2/instructions/sell
MAGICEDEN_BUY_ENDPOINT=/v2/instructions/buy_now
MAGICEDEN_ENABLED=true

# Tensor
TENSOR_BASE_URL=https://api.tensor.so
TENSOR_LIST_ENDPOINT=
TENSOR_ENABLED=false

##################################################
# MARKETPLACE SAFETY
##################################################

MARKETPLACE_REQUIRE_SIGNED_INSTRUCTIONS=true
MARKETPLACE_AUTO_LIST_ONLY_VERIFIED=false
MARKETPLACE_SKIP_IF_UNSUPPORTED=true
MARKETPLACE_VERIFY_POST_LIST_STATUS=true

##################################################
# PIPELINE FLOW CONTROL
##################################################

AUTO_RETRY=true
GLOBAL_MAX_RETRIES=3
GLOBAL_RETRY_BACKOFF_MS=2000
CONTINUE_ON_NONCRITICAL_FAILURE=true
HALT_ON_WALLET_ERROR=true
HALT_ON_STORAGE_ERROR=true
HALT_ON_MINT_ERROR=true
HALT_ON_LISTING_ERROR=false

##################################################
# DEDUP / UNIQUENESS
##################################################

ENABLE_DEDUP=true
DEDUP_MODE=perceptual_hash
DEDUP_SCOPE=global
DEDUP_CACHE_TTL_HOURS=720
UNIQUENESS_ENFORCEMENT=true
UNIQUENESS_MIN_DISTANCE=0.18

##################################################
# OBSERVABILITY
##################################################

LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_TO_STDOUT=true
LOG_TO_FILE=false
TRACE_ENABLED=false
METRICS_ENABLED=true
METRICS_NAMESPACE=solana_ai_pipeline
AUDIT_LOG_ENABLED=true

##################################################
# HEALTH / OPS
##################################################

ENABLE_HEALTHCHECK=true
HEALTHCHECK_PORT=8787
READINESS_CHECK_ENABLED=true
LIVENESS_CHECK_ENABLED=true
ENABLE_STARTUP_VALIDATION=true
ENABLE_CONFIG_VALIDATION=true

##################################################
# PERFORMANCE
##################################################

ENABLE_CONCURRENCY=true
BATCH_SIZE=10
MAX_PARALLEL_UPLOADS=3
MAX_PARALLEL_GENERATIONS=2
QUEUE_BACKPRESSURE_ENABLED=true
QUEUE_MAX_DEPTH=100

##################################################
# SECURITY
##################################################

MASK_SECRETS_IN_LOGS=true
REFUSE_EMPTY_API_KEYS=true
REFUSE_HTTP_IN_PRODUCTION=true
ENFORCE_TLS=true
ALLOW_SELF_SIGNED_TLS=false
ENABLE_REQUEST_SIGNATURES=false

##################################################
# FILE SYSTEM
##################################################

WORKDIR=./data
OUTPUT_DIR=./data/output
TMP_DIR=./data/tmp
CACHE_DIR=./data/cache
KEEP_INTERMEDIATE_FILES=false
CLEANUP_ON_SUCCESS=true
CLEANUP_ON_FAILURE=false

##################################################
# BUSINESS RULES
##################################################

ENABLE_DROP_WINDOWS=false
DROP_WINDOW_UTC_START=00:00
DROP_WINDOW_UTC_END=23:59
ALLOW_WEEKEND_MINTS=true
ALLOW_HOLIDAY_MINTS=true

##################################################
# FEATURE FLAGS
##################################################

FEATURE_GENERATE=true
FEATURE_SCORE=true
FEATURE_UPLOAD=true
FEATURE_METADATA=true
FEATURE_MINT=true
FEATURE_INDEX=true
FEATURE_LIST=false

##################################################
# HEALTHY DEFAULT PROFILE OVERRIDES
##################################################

# Production recommendation:
# APP_ENV=production
# NODE_ENV=production
# DRY_RUN=false
# MAINNET=true
# SAFE_MODE=true
# SOLANA_CLUSTER=mainnet-beta
# AUTO_LIST=false
# FEATURE_LIST=false
# ENABLE_EXPERIMENTAL=false

#### ChatGPT:
I’m doing one more strict pass against the current docs so I can mark exactly which fields in this version are safe, which are stale, and which should be removed before you wire code to them.


#### ChatGPT:
This version is much better structured, but it still has a few **hard mismatches** that will break a real build.

The biggest one: you set `MAINNET=false` and `SOLANA_CLUSTER=devnet`, but your active provider URLs still point at **mainnet** for Helius, Magic Eden, Irys, Ankr, and the public Solana fallback. That means your config is logically in **devnet mode** while your endpoints are mostly **mainnet endpoints**. You need one lane or the other. Solana’s docs also continue to warn that public RPC is not for production traffic. ([Solana](https://solana.com/docs/references/clusters?utm_source=chatgpt.com), [Solana](https://solana.com/docs/rpc?utm_source=chatgpt.com), [Solana](https://solana.com/docs/payments/interacting-with-solana?utm_source=chatgpt.com))

The second real bug is still your Helius DAS configuration. Current Helius DAS is exposed as JSON-RPC methods such as `getAsset` and `getAssetsByOwner` on the Helius RPC endpoint, not as the REST-style `/v0/assets/{id}` and `/v0/addresses/{address}/assets` paths you kept in this file. ([Helius](https://www.helius.dev/docs/api-reference/das/getassetsbyowner?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/das/getasset?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com))

The third mismatch is your minting section. You correctly chose `NFT_STANDARD=metaplex_core`, but the only program ID you store is the **legacy Token Metadata** program. Metaplex’s current docs describe Core as the next-generation standard, and the Core program ID is `CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d`. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com), [GitHub](https://github.com/metaplex-foundation/mpl-core?utm_source=chatgpt.com))

The fourth issue is your image provider config. `OPENAI_MODEL_IMAGE=gpt-image-1` is valid, but if you want the freshest default, OpenAI’s current image docs are centered on GPT Image models and still expose `/v1/images/generations` and `/v1/images/edits`. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation?utm_source=chatgpt.com), [OpenAI Developers](https://developers.openai.com/api/docs/models/gpt-image-1?utm_source=chatgpt.com))

Your Stability entry is also stale. The current official Stability API docs are under the newer API surface rather than the old `/v1/generation/{engine_id}/text-to-image` pattern you still have. ([OpenAI Developers](https://developers.openai.com/api/docs/guides/image-generation?utm_source=chatgpt.com))

Here is the corrected core of your config for the **devnet / staging** lane:

```dotenv
##################################################
# CHAIN TARGET
##################################################

CHAIN=solana
SOLANA_CLUSTER=devnet
SOLANA_COMMITMENT=confirmed
SOLANA_FINALITY=finalized
MAINNET=false

##################################################
# SOLANA RPC PROVIDERS
##################################################

# Helius devnet
HELIUS_API_KEY=
HELIUS_RPC_URL=https://devnet.helius-rpc.com/?api-key=

# QuickNode devnet if used
QUICKNODE_RPC_URL=
QUICKNODE_WSS_URL=
QUICKNODE_API_TOKEN=

# Public fallback: devnet only, diagnostics only
SOLANA_PUBLIC_RPC=https://api.devnet.solana.com

##################################################
# INDEXING / DAS
##################################################

ENABLE_INDEXING=true
INDEX_PROVIDER=helius
INDEX_REFRESH_DELAY_MS=8000
INDEX_POLL_RETRIES=10
INDEX_POLL_INTERVAL_MS=5000

# Helius DAS is JSON-RPC on the Helius RPC endpoint
HELIUS_DAS_METHOD_GET_ASSET=getAsset
HELIUS_DAS_METHOD_GET_ASSETS_BY_OWNER=getAssetsByOwner
HELIUS_DAS_METHOD_SEARCH_ASSETS=searchAssets

##################################################
# MINT STANDARD
##################################################

NFT_STANDARD=metaplex_core
METAPLEX_CORE_PROGRAM_ID=CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d

# Legacy compatibility only
METAPLEX_TOKEN_METADATA_PROGRAM=metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s
TOKEN_METADATA_ENABLED=false

##################################################
# AI PROVIDERS
##################################################

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_ENDPOINT=/images/generations
OPENAI_EDIT_ENDPOINT=/images/edits
OPENAI_MODEL_IMAGE=gpt-image-1
OPENAI_MODEL_METADATA=gpt-4.1-mini
OPENAI_API_KEY=

# Stability: keep disabled until you switch to current official endpoint set
STABILITY_ENABLED=false
STABILITY_BASE_URL=
STABILITY_API_KEY=
STABILITY_IMAGE_ENDPOINT=
STABILITY_ENGINE_ID=

REPLICATE_BASE_URL=https://api.replicate.com/v1
REPLICATE_API_KEY=
REPLICATE_PREDICTIONS_ENDPOINT=/predictions
REPLICATE_MODEL=

##################################################
# STORAGE
##################################################

STORAGE_PROVIDER=pinata

PINATA_BASE_URL=https://api.pinata.cloud
PINATA_JWT=
PINATA_FILE_ENDPOINT=/pinning/pinFileToIPFS
PINATA_JSON_ENDPOINT=/pinning/pinJSONToIPFS

IRYS_BASE_URL=https://node1.irys.xyz
IRYS_UPLOAD_ENDPOINT=/tx
IRYS_NETWORK=devnet

ENABLE_NFT_STORAGE=false
ENABLE_BUNDLR_LEGACY=false

##################################################
# MARKETPLACE
##################################################

# Disable marketplace listing on devnet unless you have a verified dev/test path
MARKETPLACE_PROVIDER=magiceden
MAGICEDEN_ENABLED=false
MAGICEDEN_BASE_URL=https://api-mainnet.magiceden.dev
MAGICEDEN_LIST_ENDPOINT=/v2/instructions/sell
MAGICEDEN_BUY_ENDPOINT=/v2/instructions/buy_now
```

And here is the **mainnet production** lane you should use later:

```dotenv
MAINNET=true
SOLANA_CLUSTER=mainnet-beta
SAFE_MODE=true
DRY_RUN=false

HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=
SOLANA_PUBLIC_RPC=https://api.mainnet.solana.com

INDEX_PROVIDER=helius
HELIUS_DAS_METHOD_GET_ASSET=getAsset
HELIUS_DAS_METHOD_GET_ASSETS_BY_OWNER=getAssetsByOwner
HELIUS_DAS_METHOD_SEARCH_ASSETS=searchAssets

NFT_STANDARD=metaplex_core
METAPLEX_CORE_PROGRAM_ID=CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d

MAGICEDEN_ENABLED=true
AUTO_LIST=false
FEATURE_LIST=false
```

The fields I would remove entirely from this file right now are:

`HELIUS_DAS_URL`\
`HELIUS_DAS_ASSETS`\
`HELIUS_DAS_GET_ASSET`

Those encode the wrong integration style for current Helius DAS. ([Helius](https://www.helius.dev/docs/api-reference/das/getassetsbyowner?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/api-reference/das/getasset?utm_source=chatgpt.com), [Helius](https://www.helius.dev/docs/das-api?utm_source=chatgpt.com))

The fields I would mark as “keep only if intentionally legacy or unverified” are:

`METAPLEX_TOKEN_METADATA_PROGRAM` because Core is the preferred standard for new projects. ([Metaplex](https://www.metaplex.com/docs/smart-contracts/core?utm_source=chatgpt.com))

`STABILITY_IMAGE_ENDPOINT=/generation/{engine_id}/text-to-image` because that reflects the older path family, not the current official endpoint set.

`TENSOR_BASE_URL=https://api.tensor.so` because I still would not wire production code to it until you validate the exact current official listing/trading endpoints you intend to call.

`ENABLE_ALIEN_MODE=true` is fine as an internal feature flag, but it has no external API meaning, so make sure your code treats it as a purely local behavior toggle.

My verdict on this config:

**Architecture: good**\
**Operational shape: good**\
**Production correctness: not yet**\
**Main blockers: chain lane mismatch, wrong Helius DAS integration, Core/Token Metadata inconsistency, stale Stability path**

If you want, I’ll turn this into a **fully normalized `.env.example` with comments stripped, invalid keys removed, and two ready profiles: `devnet.staging` and `mainnet.production`**.
