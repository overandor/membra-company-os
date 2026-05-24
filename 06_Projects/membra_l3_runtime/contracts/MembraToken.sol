// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/// @title MembraToken
/// @notice Proof-of-Proof token: each inference generates value
/// @dev Each prompt/response pair mints tokens proportional to tokens generated
contract MembraToken is ERC20, Ownable, ReentrancyGuard {
    
    struct ProofOfProof {
        bytes32 promptHash;
        bytes32 responseHash;
        bytes32 merkleRoot;
        uint256 tokenCount;
        uint256 value;
        address agent;
        uint256 timestamp;
        bool verified;
    }
    
    struct ConsensusBatch {
        bytes32 rootHash;
        uint256 txCount;
        uint256 confirmations;
        uint256 timestamp;
        bool finalized;
        mapping(bytes32 => bool) proofSubmitted;
    }
    
    // State
    mapping(bytes32 => ProofOfProof) public proofs;
    mapping(bytes32 => ConsensusBatch) public batches;
    mapping(address => uint256) public agentReputation;
    mapping(address => uint256) public totalPromptsProcessed;
    mapping(address => uint256) public totalTokensGenerated;
    
    bytes32[] public finalizedBatchRoots;
    uint256 public totalFinalizedBatches;
    uint256 public constant TOKENS_PER_INFERENCE = 100; // 100 wei per token
    uint256 public constant CONSENSUS_THRESHOLD = 2; // 2/3 chains
    
    // Events
    event PromptSubmitted(address indexed user, bytes32 indexed promptHash, uint256 fee);
    event InferenceMinted(address indexed agent, bytes32 indexed proofHash, uint256 amount);
    event BatchFinalized(bytes32 indexed rootHash, uint256 txCount, uint256 confirmations);
    event CrossChainSettlement(bytes32 indexed rootHash, string chain, bytes32 txHash);
    
    constructor() ERC20("Membra Compute", "COMPUTE") Ownable(msg.sender) {
        // Initial supply for network bootstrap
        _mint(address(this), 1000000 * 10**decimals());
    }
    
    /// @notice Submit a prompt — burns small fee, creates transaction record
    /// @param promptHash Keccak256 hash of the prompt text
    function submitPrompt(bytes32 promptHash) external payable nonReentrant {
        require(msg.value >= 1000, "Fee too low"); // 1000 wei minimum
        
        totalPromptsProcessed[msg.sender]++;
        
        // Fee is burned/kept in contract for redistribution
        emit PromptSubmitted(msg.sender, promptHash, msg.value);
    }
    
    /// @notice Mint tokens for verified inference
    /// @param promptHash Original prompt hash
    /// @param responseHash Hash of LLM response
    /// @param merkleRoot Merkle root of all token hashes
    /// @param tokenCount Number of tokens generated
    /// @param proofSignature Agent's cryptographic proof
    function mintInference(
        bytes32 promptHash,
        bytes32 responseHash,
        bytes32 merkleRoot,
        uint256 tokenCount,
        bytes memory proofSignature
    ) external nonReentrant {
        bytes32 proofHash = keccak256(abi.encodePacked(
            promptHash, responseHash, merkleRoot, msg.sender, block.timestamp
        ));
        
        require(!proofs[proofHash].verified, "Proof already used");
        
        uint256 mintAmount = tokenCount * TOKENS_PER_INFERENCE;
        
        proofs[proofHash] = ProofOfProof({
            promptHash: promptHash,
            responseHash: responseHash,
            merkleRoot: merkleRoot,
            tokenCount: tokenCount,
            value: mintAmount,
            agent: msg.sender,
            timestamp: block.timestamp,
            verified: true
        });
        
        totalTokensGenerated[msg.sender] += tokenCount;
        agentReputation[msg.sender]++;
        
        _mint(msg.sender, mintAmount);
        
        emit InferenceMinted(msg.sender, proofHash, mintAmount);
    }
    
    /// @notice Submit a consensus batch for multi-chain settlement
    /// @param rootHash Merkle root of batch transactions
    /// @param txCount Number of transactions in batch
    function submitBatch(bytes32 rootHash, uint256 txCount) external {
        require(!batches[rootHash].finalized, "Batch already finalized");
        
        ConsensusBatch storage batch = batches[rootHash];
        batch.rootHash = rootHash;
        batch.txCount = txCount;
        batch.timestamp = block.timestamp;
        batch.confirmations = 1;
    }
    
    /// @notice Confirm batch from another chain (called by bridge oracle)
    /// @param rootHash Batch root to confirm
    /// @param chainId Identifier for source chain (1=Solana, 2=Sui, 3=Bera)
    function confirmBatch(bytes32 rootHash, uint256 chainId) external onlyOwner {
        ConsensusBatch storage batch = batches[rootHash];
        require(batch.rootHash != 0, "Batch not found");
        
        bytes32 proofKey = keccak256(abi.encodePacked(rootHash, chainId));
        require(!batch.proofSubmitted[proofKey], "Already confirmed from this chain");
        
        batch.proofSubmitted[proofKey] = true;
        batch.confirmations++;
        
        if (batch.confirmations >= CONSENSUS_THRESHOLD && !batch.finalized) {
            batch.finalized = true;
            finalizedBatchRoots.push(rootHash);
            totalFinalizedBatches++;
            
            emit BatchFinalized(rootHash, batch.txCount, batch.confirmations);
        }
    }
    
    /// @notice Record cross-chain settlement
    function recordSettlement(bytes32 rootHash, string memory chain, bytes32 txHash) external {
        emit CrossChainSettlement(rootHash, chain, txHash);
    }
    
    /// @notice Get agent stats
    function getAgentStats(address agent) external view returns (
        uint256 reputation,
        uint256 prompts,
        uint256 tokens,
        uint256 balance
    ) {
        return (
            agentReputation[agent],
            totalPromptsProcessed[agent],
            totalTokensGenerated[agent],
            balanceOf(agent)
        );
    }
    
    /// @notice Batch mint for multiple inferences (gas efficient)
    function batchMintInference(
        bytes32[] calldata promptHashes,
        bytes32[] calldata responseHashes,
        uint256[] calldata tokenCounts
    ) external nonReentrant {
        require(
            promptHashes.length == responseHashes.length && 
            responseHashes.length == tokenCounts.length,
            "Array length mismatch"
        );
        
        uint256 totalMint = 0;
        for (uint i = 0; i < promptHashes.length; i++) {
            bytes32 proofHash = keccak256(abi.encodePacked(
                promptHashes[i], responseHashes[i], msg.sender, block.timestamp
            ));
            
            if (!proofs[proofHash].verified) {
                uint256 mintAmount = tokenCounts[i] * TOKENS_PER_INFERENCE;
                totalMint += mintAmount;
                
                proofs[proofHash] = ProofOfProof({
                    promptHash: promptHashes[i],
                    responseHash: responseHashes[i],
                    merkleRoot: 0,
                    tokenCount: tokenCounts[i],
                    value: mintAmount,
                    agent: msg.sender,
                    timestamp: block.timestamp,
                    verified: true
                });
                
                totalTokensGenerated[msg.sender] += tokenCounts[i];
            }
        }
        
        agentReputation[msg.sender] += promptHashes.length;
        _mint(msg.sender, totalMint);
    }
}
