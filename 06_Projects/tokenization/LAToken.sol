// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Laptop Asset Token ($LAT)
 * @notice ERC-20 token backed by verifiable software assets
 * @dev Total Supply: 9,251,500 LAT (1 LAT = $1 appraised value)
 * 
 * VERIFIABLE PROOFS:
 * - Merkle root of all system code hashes stored on-chain
 * - IPFS link to full appraisal document
 * - GitHub repository link
 * 
 * Valuation: $9,251,500 (File-Level Complexity-Adjusted, 1,123 files)
 * Total Code LOC: 427,227 across 100+ systems
 */

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";

contract LaptopAssetToken is ERC20, Ownable, ERC20Permit, ERC20Votes {
    
    // ============================================================
    // IMMUTABLE PROOF DATA (set at construction)
    // ============================================================
    
    /// @notice Merkle root of all system code SHA256 hashes
    bytes32 public immutable codeMerkleRoot;
    
    /// @notice SHA256 hash of the appraisal document
    bytes32 public immutable appraisalDocHash;
    
    /// @notice IPFS CID of the full appraisal document
    string public appraisalIpfsCid;
    
    /// @notice GitHub repository URL
    string public githubRepo;
    
    /// @notice Timestamp of token creation
    uint256 public immutable deployedAt;
    
    /// @notice Total appraised value in USD (cents precision)
    uint256 public constant APPRAISAL_VALUE_USD_CENTS = 925_150_000; // $9,251,500.00
    
    /// @notice Total code LOC backing this token
    uint256 public constant TOTAL_CODE_LOC = 427_227;
    
    /// @notice Number of systems backing this token
    uint256 public constant TOTAL_SYSTEMS = 100;
    
    // ============================================================
    // TOKENOMICS ADDRESSES
    // ============================================================
    
    address public treasury;
    address public liquidityPool;
    address public teamVesting;
    address public ecosystem;
    
    // ============================================================
    // EVENTS
    // ============================================================
    
    event ProofUpdated(string ipfsCid, string githubRepo);
    event TokenomicsSet(address treasury, address lp, address team, address eco);
    
    // ============================================================
    // CONSTRUCTOR
    // ============================================================
    
    constructor(
        bytes32 _codeMerkleRoot,
        bytes32 _appraisalDocHash,
        string memory _ipfsCid,
        string memory _githubRepo
    ) 
        ERC20("Laptop Asset Token", "LAT")
        Ownable(msg.sender)
        ERC20Permit("Laptop Asset Token")
    {
        codeMerkleRoot = _codeMerkleRoot;
        appraisalDocHash = _appraisalDocHash;
        appraisalIpfsCid = _ipfsCid;
        githubRepo = _githubRepo;
        deployedAt = block.timestamp;
        
        // Mint total supply: 9,251,500 tokens with 6 decimals
        _mint(msg.sender, 9_251_500 * 10**decimals());
    }
    
    // ============================================================
    // ADMIN FUNCTIONS
    // ============================================================
    
    /**
     * @notice Update IPFS and GitHub references
     */
    function updateProofs(
        string calldata _ipfsCid, 
        string calldata _githubRepo
    ) external onlyOwner {
        appraisalIpfsCid = _ipfsCid;
        githubRepo = _githubRepo;
        emit ProofUpdated(_ipfsCid, _githubRepo);
    }
    
    /**
     * @notice Set tokenomics distribution addresses
     */
    function setTokenomics(
        address _treasury,
        address _liquidityPool,
        address _teamVesting,
        address _ecosystem
    ) external onlyOwner {
        treasury = _treasury;
        liquidityPool = _liquidityPool;
        teamVesting = _teamVesting;
        ecosystem = _ecosystem;
        emit TokenomicsSet(_treasury, _liquidityPool, _teamVesting, _ecosystem);
    }
    
    // ============================================================
    // VIEW FUNCTIONS
    // ============================================================
    
    /**
     * @notice Returns all verifiable proof data
     */
    function getProofData() external view returns (
        bytes32 merkleRoot,
        bytes32 docHash,
        string memory ipfsCid,
        string memory repo,
        uint256 deployed,
        uint256 loc,
        uint256 systems,
        uint256 appraisalValue
    ) {
        return (
            codeMerkleRoot,
            appraisalDocHash,
            appraisalIpfsCid,
            githubRepo,
            deployedAt,
            TOTAL_CODE_LOC,
            TOTAL_SYSTEMS,
            APPRAISAL_VALUE_USD_CENTS
        );
    }
    
    // ============================================================
    // OVERRIDES
    // ============================================================
    
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Votes)
    {
        super._update(from, to, value);
    }
    
    function nonces(address owner)
        public
        view
        override(ERC20Permit, Nonces)
        returns (uint256)
    {
        return super.nonces(owner);
    }
}
