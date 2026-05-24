// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @title MembraBridge
/// @notice Cross-chain settlement bridge for Solana, Sui, Berachain
/// @dev Stores settlement proofs from other chains
contract MembraBridge is Ownable {
    
    enum Chain { Solana, Sui, Berachain }
    
    struct Settlement {
        bytes32 stateRoot;
        Chain sourceChain;
        bytes32 sourceTxHash;
        uint256 blockNumber;
        uint256 timestamp;
        bool verified;
    }
    
    // State roots that have been settled from each chain
    mapping(bytes32 => mapping(Chain => Settlement)) public settlements;
    mapping(bytes32 => uint256) public chainConfirmations;
    
    bytes32[] public settledRoots;
    uint256 public totalSettlements;
    
    // Authorized relayers (multi-sig oracle)
    mapping(address => bool) public relayers;
    uint256 public constant REQUIRED_CONFIRMATIONS = 2; // 2/3 chains
    
    event SettlementReceived(
        bytes32 indexed stateRoot,
        Chain indexed sourceChain,
        bytes32 sourceTxHash
    );
    event RelayerAdded(address relayer);
    event RelayerRemoved(address relayer);
    
    modifier onlyRelayer() {
        require(relayers[msg.sender], "Not authorized relayer");
        _;
    }
    
    function addRelayer(address relayer) external onlyOwner {
        relayers[relayer] = true;
        emit RelayerAdded(relayer);
    }
    
    function removeRelayer(address relayer) external onlyOwner {
        relayers[relayer] = false;
        emit RelayerRemoved(relayer);
    }
    
    /// @notice Record settlement from another chain
    /// @param stateRoot The L3 batch root
    /// @param sourceChain Which chain confirmed (0=Solana, 1=Sui, 2=Berachain)
    /// @param sourceTxHash Transaction hash on source chain
    function recordSettlement(
        bytes32 stateRoot,
        Chain sourceChain,
        bytes32 sourceTxHash
    ) external onlyRelayer {
        require(
            settlements[stateRoot][sourceChain].sourceTxHash == 0,
            "Already settled from this chain"
        );
        
        settlements[stateRoot][sourceChain] = Settlement({
            stateRoot: stateRoot,
            sourceChain: sourceChain,
            sourceTxHash: sourceTxHash,
            blockNumber: block.number,
            timestamp: block.timestamp,
            verified: true
        });
        
        chainConfirmations[stateRoot]++;
        totalSettlements++;
        
        emit SettlementReceived(stateRoot, sourceChain, sourceTxHash);
        
        // If 2/3 chains confirmed, finalize
        if (chainConfirmations[stateRoot] >= REQUIRED_CONFIRMATIONS) {
            settledRoots.push(stateRoot);
        }
    }
    
    /// @notice Check if a state root is fully settled (2/3 chains)
    function isSettled(bytes32 stateRoot) external view returns (bool) {
        return chainConfirmations[stateRoot] >= REQUIRED_CONFIRMATIONS;
    }
    
    /// @notice Get settlement details
    function getSettlement(bytes32 stateRoot, Chain chain) external view returns (
        bytes32 txHash,
        uint256 blockNum,
        uint256 ts,
        bool verified
    ) {
        Settlement storage s = settlements[stateRoot][chain];
        return (s.sourceTxHash, s.blockNumber, s.timestamp, s.verified);
    }
    
    /// @notice Batch record settlements (gas efficient)
    function batchRecordSettlement(
        bytes32[] calldata stateRoots,
        Chain[] calldata sourceChains,
        bytes32[] calldata sourceTxHashes
    ) external onlyRelayer {
        require(
            stateRoots.length == sourceChains.length &&
            sourceChains.length == sourceTxHashes.length,
            "Array length mismatch"
        );
        
        for (uint i = 0; i < stateRoots.length; i++) {
            if (settlements[stateRoots[i]][sourceChains[i]].sourceTxHash == 0) {
                settlements[stateRoots[i]][sourceChains[i]] = Settlement({
                    stateRoot: stateRoots[i],
                    sourceChain: sourceChains[i],
                    sourceTxHash: sourceTxHashes[i],
                    blockNumber: block.number,
                    timestamp: block.timestamp,
                    verified: true
                });
                
                chainConfirmations[stateRoots[i]]++;
                totalSettlements++;
                
                emit SettlementReceived(stateRoots[i], sourceChains[i], sourceTxHashes[i]);
            }
        }
    }
}
