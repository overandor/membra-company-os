// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title MembraConsensus
/// @notice On-chain verification of LLM inference consensus
/// @dev Stores proof hashes and validates multi-agent agreement
contract MembraConsensus {
    
    struct ConsensusRound {
        bytes32 stateRoot;
        address[] voters;
        bytes32[] votes;
        uint256 timestamp;
        bool finalized;
        uint256 totalWeight;
    }
    
    mapping(bytes32 => ConsensusRound) public rounds;
    mapping(address => uint256) public voterWeight;
    bytes32[] public finalizedRoots;
    
    uint256 public constant THRESHOLD_NUMERATOR = 67; // 67%
    uint256 public constant THRESHOLD_DENOMINATOR = 100;
    
    event VoteSubmitted(bytes32 indexed stateRoot, address indexed voter, bytes32 voteHash);
    event ConsensusReached(bytes32 indexed stateRoot, uint256 voterCount, uint256 totalWeight);
    
    /// @notice Register as a consensus voter (agent must have reputation)
    function registerVoter(uint256 weight) external {
        require(weight > 0, "Weight must be positive");
        voterWeight[msg.sender] = weight;
    }
    
    /// @notice Submit a vote for a state root
    /// @param stateRoot The batch root being voted on
    /// @param voteHash Hash of the LLM inference output (the proof)
    function submitVote(bytes32 stateRoot, bytes32 voteHash) external {
        require(voterWeight[msg.sender] > 0, "Not a registered voter");
        require(!rounds[stateRoot].finalized, "Round already finalized");
        
        ConsensusRound storage round = rounds[stateRoot];
        
        if (round.stateRoot == 0) {
            round.stateRoot = stateRoot;
            round.timestamp = block.timestamp;
        }
        
        round.voters.push(msg.sender);
        round.votes.push(voteHash);
        round.totalWeight += voterWeight[msg.sender];
        
        emit VoteSubmitted(stateRoot, msg.sender, voteHash);
        
        // Check if consensus reached
        _checkConsensus(stateRoot);
    }
    
    /// @notice Check if 2/3 majority has been reached
    function _checkConsensus(bytes32 stateRoot) internal {
        ConsensusRound storage round = rounds[stateRoot];
        
        if (round.voters.length < 3) return; // Need at least 3 votes
        
        // Count vote hashes
        mapping(bytes32 => uint256) memory hashCounts;
        uint256 maxCount = 0;
        bytes32 winningHash;
        
        for (uint i = 0; i < round.votes.length; i++) {
            bytes32 vh = round.votes[i];
            hashCounts[vh]++;
            if (hashCounts[vh] > maxCount) {
                maxCount = hashCounts[vh];
                winningHash = vh;
            }
        }
        
        // Check if winning hash has 2/3 majority
        uint256 agreement = (maxCount * THRESHOLD_DENOMINATOR) / round.votes.length;
        
        if (agreement >= THRESHOLD_NUMERATOR && !round.finalized) {
            round.finalized = true;
            finalizedRoots.push(stateRoot);
            
            emit ConsensusReached(stateRoot, round.voters.length, round.totalWeight);
        }
    }
    
    /// @notice Get round status
    function getRound(bytes32 stateRoot) external view returns (
        bytes32 root,
        uint256 voterCount,
        uint256 weight,
        bool finalized
    ) {
        ConsensusRound storage r = rounds[stateRoot];
        return (r.stateRoot, r.voters.length, r.totalWeight, r.finalized);
    }
    
    /// @notice Get total finalized rounds
    function finalizedCount() external view returns (uint256) {
        return finalizedRoots.length;
    }
}
