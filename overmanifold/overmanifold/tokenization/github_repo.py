"""
Overmanifold GitHub Repository Tokenization
Converts GitHub repositories into micro-companies with tokenized governance and value capture.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import re

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.types import Hash, EndpointID, StateTransition, StateTransitionType
from merkle.proof import MerkleTree, MerkleProof


class RepositoryType(Enum):
    """Types of repositories for classification."""
    LIBRARY = "library"
    APPLICATION = "application"
    FRAMEWORK = "framework"
    TOOL = "tool"
    DOCUMENTATION = "documentation"
    TEMPLATE = "template"
    RESEARCH = "research"


class ContributionType(Enum):
    """Types of contributions to repositories."""
    CODE_COMMIT = "code_commit"
    ISSUE_OPENED = "issue_opened"
    ISSUE_CLOSED = "issue_closed"
    PULL_REQUEST = "pull_request"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    TEST_COVERAGE = "test_coverage"
    DEPENDENCY_UPDATE = "dependency_update"


@dataclass
class Contributor:
    """Contributor to a repository."""
    contributor_id: str
    username: str
    contributions: int
    contribution_types: Dict[ContributionType, int]
    first_contribution: datetime
    last_contribution: datetime
    reputation_score: float = 0.0
    token_holdings: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert contributor to dictionary."""
        return {
            "contributor_id": self.contributor_id,
            "username": self.username,
            "contributions": self.contributions,
            "contribution_types": {ct.value: count for ct, count in self.contribution_types.items()},
            "first_contribution": self.first_contribution.isoformat(),
            "last_contribution": self.last_contribution.isoformat(),
            "reputation_score": self.reputation_score,
            "token_holdings": self.token_holdings
        }


@dataclass
class RepositoryMetrics:
    """Metrics for repository valuation."""
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    total_commits: int = 0
    total_contributors: int = 0
    code_coverage: float = 0.0
    test_pass_rate: float = 0.0
    documentation_score: float = 0.0
    dependency_health: float = 0.0
    community_engagement: float = 0.0
    technical_debt: float = 0.0
    
    def calculate_valuation_score(self) -> float:
        """Calculate overall valuation score."""
        # Weighted scoring system
        weights = {
            "community": 0.3,  # stars, forks, watchers
            "activity": 0.25,  # commits, issues
            "quality": 0.25,   # coverage, tests, docs
            "health": 0.2      # dependencies, technical debt
        }
        
        community_score = min(self.stars / 1000, 1.0) * 0.4 + \
                         min(self.forks / 100, 1.0) * 0.3 + \
                         min(self.watchers / 50, 1.0) * 0.3
        
        activity_score = min(self.total_commits / 1000, 1.0) * 0.5 + \
                        min(self.total_contributors / 50, 1.0) * 0.5
        
        quality_score = self.code_coverage * 0.3 + \
                       self.test_pass_rate * 0.3 + \
                       self.documentation_score * 0.4
        
        health_score = self.dependency_health * 0.5 + \
                      (1.0 - min(self.technical_debt, 1.0)) * 0.5
        
        total_score = (community_score * weights["community"] +
                      activity_score * weights["activity"] +
                      quality_score * weights["quality"] +
                      health_score * weights["health"])
        
        return total_score


@dataclass
class RepoToken:
    """Token representing a repository micro-company."""
    token_id: str
    repo_id: str
    token_name: str
    token_symbol: str
    total_supply: float
    circulating_supply: float
    price_per_token: float
    market_cap: float
    governance_rights: Dict[str, Any]
    dividend_yield: float = 0.0
    last_price_update: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_market_cap(self) -> float:
        """Calculate market capitalization."""
        return self.circulating_supply * self.price_per_token
    
    def to_dict(self) -> Dict:
        """Convert token to dictionary."""
        return {
            "token_id": self.token_id,
            "repo_id": self.repo_id,
            "token_name": self.token_name,
            "token_symbol": self.token_symbol,
            "total_supply": self.total_supply,
            "circulating_supply": self.circulating_supply,
            "price_per_token": self.price_per_token,
            "market_cap": self.market_cap,
            "governance_rights": self.governance_rights,
            "dividend_yield": self.dividend_yield,
            "last_price_update": self.last_price_update.isoformat()
        }


@dataclass
class RepositoryMicroCompany:
    """
    A GitHub repository tokenized as a micro-company.
    Includes governance, valuation, and economic mechanisms.
    """
    repo_id: str
    repo_name: str
    repo_url: str
    description: str
    repository_type: RepositoryType
    owner: str
    created_at: datetime
    token: RepoToken
    metrics: RepositoryMetrics
    contributors: Dict[str, Contributor]
    governance_config: Dict[str, Any]
    merkle_root: str = ""
    endpoint_id: Optional[EndpointID] = None
    valuation_usd: float = 0.0
    last_valuation_update: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert micro-company to dictionary."""
        return {
            "repo_id": self.repo_id,
            "repo_name": self.repo_name,
            "repo_url": self.repo_url,
            "description": self.description,
            "repository_type": self.repository_type.value,
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
            "token": self.token.to_dict(),
            "metrics": self.metrics.__dict__,
            "contributors": {k: v.to_dict() for k, v in self.contributors.items()},
            "governance_config": self.governance_config,
            "merkle_root": self.merkle_root,
            "endpoint_id": str(self.endpoint_id) if self.endpoint_id else None,
            "valuation_usd": self.valuation_usd,
            "last_valuation_update": self.last_valuation_update.isoformat() if self.last_valuation_update else None
        }


class GitHubRepoAnalyzer:
    """
    Analyzes GitHub repositories for tokenization potential.
    In production, this would use GitHub API.
    """
    
    def __init__(self):
        self.repo_cache: Dict[str, Dict] = {}
    
    def analyze_repository(self, repo_url: str) -> Dict:
        """
        Analyze repository and return metrics for tokenization.
        In production, this would make actual GitHub API calls.
        """
        # Extract repo info from URL
        repo_info = self._parse_repo_url(repo_url)
        repo_id = f"{repo_info['owner']}/{repo_info['repo']}"
        
        # Check cache
        if repo_id in self.repo_cache:
            return self.repo_cache[repo_id]
        
        # Simulated analysis (in production, use GitHub API)
        analysis = {
            "repo_id": repo_id,
            "owner": repo_info['owner'],
            "repo": repo_info['repo'],
            "description": "Repository description would come from GitHub API",
            "stars": 150 + hash(repo_id) % 1000,
            "forks": 20 + hash(repo_id) % 100,
            "watchers": 10 + hash(repo_id) % 50,
            "open_issues": 5 + hash(repo_id) % 50,
            "closed_issues": 100 + hash(repo_id) % 500,
            "total_commits": 200 + hash(repo_id) % 1000,
            "total_contributors": 5 + hash(repo_id) % 50,
            "languages": {"Python": 0.7, "JavaScript": 0.2, "HTML": 0.1},
            "topics": ["blockchain", "decentralization", "crypto"],
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.repo_cache[repo_id] = analysis
        return analysis
    
    def _parse_repo_url(self, repo_url: str) -> Dict:
        """Parse GitHub repository URL."""
        pattern = r'github\.com/([^/]+)/([^/]+)'
        match = re.search(pattern, repo_url)
        if match:
            return {"owner": match.group(1), "repo": match.group(2).replace('.git', '')}
        raise ValueError("Invalid GitHub repository URL")
    
    def classify_repository(self, analysis: Dict) -> RepositoryType:
        """Classify repository type based on analysis."""
        topics = analysis.get("topics", [])
        description = analysis.get("description", "").lower()
        
        if any(topic in ["framework", "sdk"] for topic in topics):
            return RepositoryType.FRAMEWORK
        elif any(topic in ["lib", "library"] for topic in topics):
            return RepositoryType.LIBRARY
        elif "app" in description or "application" in description:
            return RepositoryType.APPLICATION
        elif any(topic in ["tool", "utility"] for topic in topics):
            return RepositoryType.TOOL
        elif "docs" in description or "documentation" in description:
            return RepositoryType.DOCUMENTATION
        elif "template" in description or "boilerplate" in description:
            return RepositoryType.TEMPLATE
        else:
            return RepositoryType.RESEARCH


class RepoTokenizer:
    """
    Tokenizes GitHub repositories into micro-companies.
    Handles valuation, token generation, and governance setup.
    """
    
    def __init__(self):
        self.analyzer = GitHubRepoAnalyzer()
        self.tokenized_repos: Dict[str, RepositoryMicroCompany] = {}
        self.merkle_tree: Optional[MerkleTree] = None
    
    def tokenize_repository(self, repo_url: str, 
                           initial_valuation_usd: float = 100000.0,
                           token_supply: float = 1000000.0) -> RepositoryMicroCompany:
        """
        Tokenize a GitHub repository into a micro-company.
        """
        # Analyze repository
        analysis = self.analyzer.analyze_repository(repo_url)
        repo_type = self.analyzer.classify_repository(analysis)
        
        # Create metrics
        metrics = RepositoryMetrics(
            stars=analysis["stars"],
            forks=analysis["forks"],
            watchers=analysis["watchers"],
            open_issues=analysis["open_issues"],
            closed_issues=analysis["closed_issues"],
            total_commits=analysis["total_commits"],
            total_contributors=analysis["total_contributors"],
            code_coverage=0.8,  # Would come from analysis
            test_pass_rate=0.9,  # Would come from analysis
            documentation_score=0.7,  # Would come from analysis
            dependency_health=0.85,  # Would come from analysis
            community_engagement=0.6,  # Would calculate from activity patterns
            technical_debt=0.3  # Would come from analysis
        )
        
        # Calculate valuation
        valuation_score = metrics.calculate_valuation_score()
        actual_valuation = initial_valuation_usd * valuation_score
        
        # Create token
        token_symbol = f"{analysis['repo'][:3].upper()}"
        token = RepoToken(
            token_id=f"token_{analysis['repo_id'].replace('/', '_')}",
            repo_id=analysis['repo_id'],
            token_name=f"{analysis['repo']} Token",
            token_symbol=token_symbol,
            total_supply=token_supply,
            circulating_supply=token_supply * 0.8,  # 80% circulating
            price_per_token=actual_valuation / token_supply,
            market_cap=actual_valuation,
            governance_rights={
                "voting_power": True,
                "proposal_rights": True,
                "dividend_share": 0.6,
                "governance_quorum": 0.51
            }
        )
        
        # Create contributors (simplified)
        contributors = {}
        for i in range(min(analysis["total_contributors"], 10)):
            contributor_id = f"contributor_{i}"
            contributors[contributor_id] = Contributor(
                contributor_id=contributor_id,
                username=f"user_{i}",
                contributions=10 + i * 5,
                contribution_types={
                    ContributionType.CODE_COMMIT: 5 + i * 2,
                    ContributionType.ISSUE_CLOSED: 3 + i,
                    ContributionType.PULL_REQUEST: 2 + i
                },
                first_contribution=datetime.strptime(analysis["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                last_contribution=datetime.utcnow(),
                reputation_score=0.5 + (i * 0.05),
                token_holdings=token_supply * 0.1 / (i + 1)
            )
        
        # Create governance config
        governance_config = {
            "voting_period_days": 7,
            "proposal_threshold": 0.05,  # 5% of supply needed to propose
            "quorum_threshold": 0.51,  # 51% participation needed
            "execution_threshold": 0.67,  # 67% yes vote needed
            "voting_power": "proportional",
            "delegate_voting": True,
            "emergency_pause": True
        }
        
        # Create micro-company
        micro_company = RepositoryMicroCompany(
            repo_id=analysis['repo_id'],
            repo_name=analysis['repo'],
            repo_url=repo_url,
            description=analysis['description'],
            repository_type=repo_type,
            owner=analysis['owner'],
            created_at=datetime.strptime(analysis["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            token=token,
            metrics=metrics,
            contributors=contributors,
            governance_config=governance_config,
            valuation_usd=actual_valuation,
            last_valuation_update=datetime.utcnow()
        )
        
        # Generate endpoint ID
        micro_company.endpoint_id = EndpointID.generate(
            "github_repo", 
            analysis['repo_id'].replace('/', '_')
        )
        
        # Store and update Merkle tree
        self.tokenized_repos[analysis['repo_id']] = micro_company
        self._update_merkle_tree()
        
        return micro_company
    
    def _update_merkle_tree(self) -> None:
        """Update Merkle tree with all tokenized repositories."""
        leaves = []
        for repo_id, company in self.tokenized_repos.items():
            leaf_data = {
                "repo_id": repo_id,
                "token_id": company.token.token_id,
                "valuation": company.valuation_usd,
                "market_cap": company.token.market_cap,
                "contributor_count": len(company.contributors),
                "timestamp": datetime.utcnow().isoformat()
            }
            leaves.append(leaf_data)
        
        self.merkle_tree = MerkleTree()
        for leaf in leaves:
            self.merkle_tree.add_leaf(leaf)
        self.merkle_tree.build_tree()
        
        # Update all companies with new root
        root_hash = self.merkle_tree.get_root_hash()
        root = str(root_hash) if root_hash else ""
        for company in self.tokenized_repos.values():
            company.merkle_root = root
    
    def get_repo_company(self, repo_id: str) -> Optional[RepositoryMicroCompany]:
        """Get tokenized micro-company for repository."""
        return self.tokenized_repos.get(repo_id)
    
    def create_repo_proof(self, repo_id: str) -> Optional[MerkleProof]:
        """Create Merkle proof for repository."""
        if not self.merkle_tree:
            self._update_merkle_tree()
        
        if repo_id not in self.tokenized_repos:
            return None
        
        repo_ids = list(self.tokenized_repos.keys())
        leaf_index = repo_ids.index(repo_id)
        return self.merkle_tree.generate_proof(leaf_index)
    
    def update_contributor_tokens(self, repo_id: str, contributor_id: str, 
                                 token_amount: float) -> bool:
        """Update token holdings for a contributor."""
        company = self.get_repo_company(repo_id)
        if not company or contributor_id not in company.contributors:
            return False
        
        contributor = company.contributors[contributor_id]
        contributor.token_holdings += token_amount
        return True
    
    def calculate_contributor_rewards(self, repo_id: str, 
                                     total_reward: float) -> Dict[str, float]:
        """
        Calculate reward distribution based on contributor contributions.
        """
        company = self.get_repo_company(repo_id)
        if not company:
            return {}
        
        # Calculate total contribution score
        total_score = sum(
            c.contributions * c.reputation_score 
            for c in company.contributors.values()
        )
        
        if total_score == 0:
            return {}
        
        # Distribute rewards proportionally
        rewards = {}
        for contributor_id, contributor in company.contributors.items():
            contributor_score = contributor.contributions * contributor.reputation_score
            reward_share = contributor_score / total_score
            rewards[contributor_id] = total_reward * reward_share
        
        return rewards
    
    def propose_governance_action(self, repo_id: str, proposal: Dict) -> str:
        """
        Create a governance proposal for the micro-company.
        """
        company = self.get_repo_company(repo_id)
        if not company:
            raise ValueError("Repository not tokenized")
        
        proposal_id = f"proposal_{datetime.utcnow().timestamp()}"
        
        # In production, this would create an actual governance proposal
        # with voting mechanics and smart contract integration
        
        return proposal_id


class RepoGovernanceEngine:
    """
    Governance engine for repository micro-companies.
    Handles voting, proposals, and execution.
    """
    
    def __init__(self, tokenizer: RepoTokenizer):
        self.tokenizer = tokenizer
        self.proposals: Dict[str, Dict] = {}
        self.votes: Dict[str, Dict] = {}
    
    def create_proposal(self, repo_id: str, proposal_type: str, 
                       description: str, parameters: Dict) -> str:
        """Create a governance proposal."""
        company = self.tokenizer.get_repo_company(repo_id)
        if not company:
            raise ValueError("Repository not tokenized")
        
        proposal_id = f"prop_{repo_id.replace('/', '_')}_{int(datetime.utcnow().timestamp())}"
        
        proposal = {
            "proposal_id": proposal_id,
            "repo_id": repo_id,
            "type": proposal_type,
            "description": description,
            "parameters": parameters,
            "created_at": datetime.utcnow().isoformat(),
            "voting_deadline": (datetime.utcnow() + 
                              timedelta(days=company.governance_config["voting_period_days"])).isoformat(),
            "status": "active",
            "votes_for": 0,
            "votes_against": 0,
            "voters": []
        }
        
        self.proposals[proposal_id] = proposal
        return proposal_id
    
    def vote_on_proposal(self, proposal_id: str, contributor_id: str, 
                        vote: bool, voting_power: float) -> bool:
        """Cast vote on a proposal."""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        
        if contributor_id in proposal["voters"]:
            return False  # Already voted
        
        if vote:
            proposal["votes_for"] += voting_power
        else:
            proposal["votes_against"] += voting_power
        
        proposal["voters"].append(contributor_id)
        return True
    
    def execute_proposal(self, proposal_id: str) -> bool:
        """Execute a proposal if voting criteria are met."""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        
        # Check if voting deadline has passed
        deadline = datetime.fromisoformat(proposal["voting_deadline"])
        if datetime.utcnow() < deadline:
            return False
        
        # Check quorum
        company = self.tokenizer.get_repo_company(proposal["repo_id"])
        if not company:
            return False
        
        total_voting_power = sum(c.token_holdings for c in company.contributors.values())
        total_votes = proposal["votes_for"] + proposal["votes_against"]
        
        if total_votes / total_voting_power < company.governance_config["quorum_threshold"]:
            return False
        
        # Check execution threshold
        if proposal["votes_for"] / total_votes < company.governance_config["execution_threshold"]:
            proposal["status"] = "rejected"
            return False
        
        proposal["status"] = "executed"
        return True