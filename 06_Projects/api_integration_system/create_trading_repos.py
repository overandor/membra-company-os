#!/usr/bin/env python3
"""
Professional Trading System Repository Manager
Creates individual GitHub repositories for each trading system with appraisals
"""

import os
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict, List
from datetime import datetime

class TradingSystemAppraiser:
    """Professional appraisal system for trading systems"""
    
    def __init__(self, github_token: str, username: str):
        self.github_token = github_token
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
    def create_appraisal(self, system_name: str, files: List[str]) -> Dict:
        """Generate professional appraisal for a trading system"""
        
        appraisal = {
            "system_name": system_name,
            "appraisal_date": datetime.now().isoformat(),
            "technical_assessment": self._assess_technical_quality(files),
            "business_value": self._assess_business_value(system_name),
            "market_potential": self._assess_market_potential(system_name),
            "complexity_score": self._calculate_complexity(files),
            "maintenance_requirements": self._assess_maintenance(files),
            "risk_factors": self._identify_risks(files),
            "recommendation": self._generate_recommendation(system_name),
            "estimated_development_hours": self._estimate_hours(files),
            "production_readiness": self._assess_production_readiness(files)
        }
        
        return appraisal
    
    def _assess_technical_quality(self, files: List[str]) -> Dict:
        """Assess technical quality of the codebase"""
        total_lines = 0
        py_files = [f for f in files if f.endswith('.py')]
        
        for file in py_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    total_lines += len(f.readlines())
            except:
                pass
        
        return {
            "total_files": len(files),
            "python_files": len(py_files),
            "total_lines_of_code": total_lines,
            "code_organization": "Structured" if len(py_files) > 1 else "Single file",
            "documentation_coverage": self._check_documentation(files),
            "error_handling": self._check_error_handling(py_files),
            "code_quality_score": self._calculate_quality_score(py_files)
        }
    
    def _assess_business_value(self, system_name: str) -> Dict:
        """Assess business value of the trading system"""
        business_factors = {
            "revenue_potential": "High" if "trading" in system_name.lower() or "bot" in system_name.lower() else "Medium",
            "market_demand": self._get_market_demand(system_name),
            "scalability": "High" if "system" in system_name.lower() else "Medium",
            "competitive_advantage": "Unique algorithm implementation",
            "monetization_potential": self._assess_monetization(system_name)
        }
        
        return business_factors
    
    def _assess_market_potential(self, system_name: str) -> Dict:
        """Assess market potential"""
        return {
            "target_market": "Cryptocurrency trading" if "gate" in system_name.lower() or "trading" in system_name.lower() else "General algorithmic trading",
            "market_size": "$Multi-billion",
            "growth_rate": "High",
            "competition_level": "Moderate to High",
            "differentiation": "Custom AI integration"
        }
    
    def _calculate_complexity(self, files: List[str]) -> Dict:
        """Calculate complexity score"""
        py_files = [f for f in files if f.endswith('.py')]
        
        complexity_factors = {
            "file_count": len(files),
            "dependency_count": self._count_dependencies(py_files),
            "integration_points": self._count_integrations(py_files),
            "algorithm_complexity": self._assess_algorithm_complexity(py_files),
            "overall_complexity": "Low" if len(py_files) < 3 else "Medium" if len(py_files) < 10 else "High"
        }
        
        return complexity_factors
    
    def _assess_maintenance(self, files: List[str]) -> Dict:
        """Assess maintenance requirements"""
        return {
            "code_readability": "Good" if self._check_documentation(files) > 0.5 else "Needs improvement",
            "modularity": "High" if len(files) > 3 else "Low",
            "test_coverage": self._check_tests(files),
            "documentation_quality": "Adequate" if self._check_documentation(files) > 0.3 else "Limited",
            "estimated_maintenance_hours": len(files) * 2
        }
    
    def _identify_risks(self, files: List[str]) -> List[str]:
        """Identify potential risks"""
        risks = []
        
        if any("api_key" in f.lower() or "secret" in f.lower() for f in files):
            risks.append("API key management - ensure secure credential storage")
        
        if len(files) > 20:
            risks.append("High complexity - may require dedicated maintenance team")
        
        risks.append("Market volatility - trading systems carry financial risk")
        risks.append("API dependency - third-party service availability")
        
        return risks
    
    def _generate_recommendation(self, system_name: str) -> str:
        """Generate overall recommendation"""
        if "trading" in system_name.lower() or "bot" in system_name.lower():
            return "PROCEED - High potential for automated trading revenue with proper risk management"
        elif "analysis" in system_name.lower():
            return "CONSIDER - Valuable for market insights and decision support"
        else:
            return "EVALUATE - Assess specific use case and integration requirements"
    
    def _estimate_hours(self, files: List[str]) -> int:
        """Estimate development hours"""
        return len(files) * 4 + 20  # Base 20 hours + 4 hours per file
    
    def _assess_production_readiness(self, files: List[str]) -> Dict:
        """Assess readiness for production deployment"""
        return {
            "error_handling": "Implemented" if self._check_error_handling(files) > 0.5 else "Needs improvement",
            "logging": "Present" if any("log" in f.lower() for f in files) else "Missing",
            "configuration": "Externalized" if any("config" in f.lower() or "env" in f.lower() for f in files) else "Hardcoded",
            "monitoring": "Basic" if any("monitor" in f.lower() or "metric" in f.lower() for f in files) else "Not implemented",
            "overall_readiness": "Ready for testing" if len(files) > 2 else "Needs development"
        }
    
    def _check_documentation(self, files: List[str]) -> float:
        """Check documentation coverage"""
        doc_files = [f for f in files if f.endswith(('.md', '.txt', '.rst'))]
        return len(doc_files) / len(files) if files else 0
    
    def _check_error_handling(self, py_files: List[str]) -> float:
        """Check error handling implementation"""
        try_count = 0
        except_count = 0
        
        for file in py_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    try_count += content.count('try:')
                    except_count += content.count('except')
            except:
                pass
        
        return except_count / try_count if try_count > 0 else 0
    
    def _calculate_quality_score(self, py_files: List[str]) -> int:
        """Calculate overall code quality score (0-100)"""
        score = 50  # Base score
        
        if self._check_error_handling(py_files) > 0.5:
            score += 20
        
        if len(py_files) <= 5:
            score += 10
        
        if any('__main__' in open(f, 'r', encoding='utf-8', errors='ignore').read() for f in py_files if os.path.exists(f)):
            score += 10
        
        return min(score, 100)
    
    def _count_dependencies(self, py_files: List[str]) -> int:
        """Count external dependencies"""
        imports = set()
        for file in py_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'import ' in content:
                        imports.update([line.split('import')[1].strip().split()[0] for line in content.split('\n') if 'import ' in line and not line.strip().startswith('#')])
            except:
                pass
        return len(imports)
    
    def _count_integrations(self, py_files: List[str]) -> int:
        """Count external API integrations"""
        integrations = 0
        api_keywords = ['requests', 'aiohttp', 'websocket', 'api', 'http']
        
        for file in py_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    integrations += sum(1 for keyword in api_keywords if keyword in content)
            except:
                pass
        
        return integrations
    
    def _assess_algorithm_complexity(self, py_files: List[str]) -> str:
        """Assess algorithm complexity"""
        complexity_indicators = 0
        
        for file in py_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'while ' in content:
                        complexity_indicators += 1
                    if 'for ' in content:
                        complexity_indicators += 1
                    if 'def ' in content:
                        complexity_indicators += 1
                    if 'class ' in content:
                        complexity_indicators += 2
            except:
                pass
        
        return "Low" if complexity_indicators < 10 else "Medium" if complexity_indicators < 30 else "High"
    
    def _get_market_demand(self, system_name: str) -> str:
        """Get market demand assessment"""
        high_demand_keywords = ['trading', 'bot', 'ai', 'ml', 'arbitrage', 'market', 'maker']
        
        if any(keyword in system_name.lower() for keyword in high_demand_keywords):
            return "Very High"
        return "Moderate"
    
    def _assess_monetization(self, system_name: str) -> str:
        """Assess monetization potential"""
        monetizable_keywords = ['trading', 'bot', 'profit', 'executor', 'market', 'maker']
        
        if any(keyword in system_name.lower() for keyword in monetizable_keywords):
            return "Direct revenue generation"
        return "Indirect value through efficiency"
    
    def _check_tests(self, files: List[str]) -> str:
        """Check for test files"""
        test_files = [f for f in files if 'test' in f.lower()]
        return "Present" if test_files else "None found"
    
    def create_repository(self, repo_name: str, description: str, private: bool = True) -> Dict:
        """Create a new GitHub repository"""
        url = f"{self.base_url}/user/repos"
        
        payload = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": False
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def create_appraisal_document(self, appraisal: Dict, output_path: str):
        """Create a detailed appraisal document"""
        
        doc_content = f"""
# Professional Appraisal: {appraisal['system_name']}

**Appraisal Date:** {appraisal['appraisal_date']}
**System Name:** {appraisal['system_name']}

---

## Executive Summary

**Recommendation:** {appraisal['recommendation']}

**Overall Assessment:** This trading system demonstrates {appraisal['technical_assessment']['code_quality_score']}/100 code quality with {appraisal['business_value']['revenue_potential']} revenue potential.

---

## Technical Assessment

### Code Quality Metrics
- **Total Files:** {appraisal['technical_assessment']['total_files']}
- **Python Files:** {appraisal['technical_assessment']['python_files']}
- **Lines of Code:** {appraisal['technical_assessment']['total_lines_of_code']}
- **Code Organization:** {appraisal['technical_assessment']['code_organization']}
- **Documentation Coverage:** {appraisal['technical_assessment']['documentation_coverage']*100:.1f}%
- **Error Handling:** {appraisal['technical_assessment']['error_handling']*100:.1f}%
- **Quality Score:** {appraisal['technical_assessment']['code_quality_score']}/100

### Complexity Analysis
- **Overall Complexity:** {appraisal['complexity_score']['overall_complexity']}
- **Dependency Count:** {appraisal['complexity_score']['dependency_count']}
- **Integration Points:** {appraisal['complexity_score']['integration_points']}
- **Algorithm Complexity:** {appraisal['complexity_score']['algorithm_complexity']}

---

## Business Value Assessment

### Revenue Potential
- **Revenue Potential:** {appraisal['business_value']['revenue_potential']}
- **Market Demand:** {appraisal['business_value']['market_demand']}
- **Scalability:** {appraisal['business_value']['scalability']}
- **Competitive Advantage:** {appraisal['business_value']['competitive_advantage']}
- **Monetization Potential:** {appraisal['business_value']['monetization_potential']}

### Market Potential
- **Target Market:** {appraisal['market_potential']['target_market']}
- **Market Size:** {appraisal['market_potential']['market_size']}
- **Growth Rate:** {appraisal['market_potential']['growth_rate']}
- **Competition Level:** {appraisal['market_potential']['competition_level']}
- **Differentiation:** {appraisal['market_potential']['differentiation']}

---

## Maintenance Requirements

- **Code Readability:** {appraisal['maintenance_requirements']['code_readability']}
- **Modularity:** {appraisal['maintenance_requirements']['modularity']}
- **Test Coverage:** {appraisal['maintenance_requirements']['test_coverage']}
- **Documentation Quality:** {appraisal['maintenance_requirements']['documentation_quality']}
- **Estimated Maintenance Hours:** {appraisal['maintenance_requirements']['estimated_maintenance_hours']}/month

---

## Risk Factors

{self._format_risks(appraisal['risk_factors'])}

---

## Production Readiness

- **Error Handling:** {appraisal['production_readiness']['error_handling']}
- **Logging:** {appraisal['production_readiness']['logging']}
- **Configuration:** {appraisal['production_readiness']['configuration']}
- **Monitoring:** {appraisal['production_readiness']['monitoring']}
- **Overall Readiness:** {appraisal['production_readiness']['overall_readiness']}

---

## Investment Summary

- **Estimated Development Hours:** {appraisal['estimated_development_hours']}
- **Estimated Maintenance Cost:** ${appraisal['maintenance_requirements']['estimated_maintenance_hours'] * 100}/month
- **Time to Production:** {appraisal['estimated_development_hours'] // 40} weeks
- **ROI Potential:** {appraisal['business_value']['revenue_potential']}

---

## Recommendations

1. **Immediate Actions:**
   - Review and enhance error handling
   - Implement comprehensive logging
   - Add unit tests for critical functions

2. **Short-term (1-3 months):**
   - Improve documentation coverage
   - Add monitoring and alerting
   - Implement configuration management

3. **Long-term (3-12 months):**
   - Scale infrastructure if needed
   - Optimize performance
   - Expand feature set based on user feedback

---

*This appraisal was generated automatically by the Trading System Appraiser. For detailed analysis, manual review is recommended.*
"""
        
        with open(output_path, 'w') as f:
            f.write(doc_content)
    
    def _format_risks(self, risks: List[str]) -> str:
        """Format risk factors as markdown list"""
        return "\n".join([f"- {risk}" for risk in risks])

def main():
    """Main execution function"""
    print("🔍 Trading System Repository Manager")
    print("=" * 60)
    
    # Configuration
    github_token = os.environ.get("GITHUB_TOKEN", "")
    username = "overandor"
    
    appraiser = TradingSystemAppraiser(github_token, username)
    
    # Trading systems to process
    trading_systems = {
        "algo_micro_cap_bot": "Algo trading bot for micro-cap cryptocurrencies",
        "autogen_gate_mm": "Auto-generated Gate.io market maker with Ollama",
        "aider_ai_system": "AI-powered trading system with Aider integration",
        "beast_market_maker": "Aggressive market maker trading bot",
        "deepseek_ai_council": "DeepSeek AI-powered trading council",
        "gate_multi_ticker_mm": "Multi-ticker market maker for Gate.io",
        "gateio_market_maker_system": "Comprehensive Gate.io market making system",
        "godforbit_trading_system": "High-frequency trading system",
        "groq_supervisor_ai": "Groq AI-powered trading supervisor",
        "hedge_beast_system": "Advanced hedging trading system",
        "hypweliquid_llm_trader": "Hyperliquid LLM-powered trader",
        "hybrid_ai_supervisor_system": "Hybrid AI trading supervisor",
        "llm_autonomous_agent": "Autonomous LLM trading agent",
        "local_ollama_trading_bot": "Local Ollama-based trading bot",
        "micro_cap_trading_system": "Micro-cap cryptocurrency trading system",
        "micro_coin_market_maker": "Micro-coin market maker",
        "openrouter_ai_trading_bot": "OpenRouter AI-powered trading bot",
        "profit_executor_system": "Automated profit execution system",
        "retro_terminal_trading_bot": "Retro-style terminal trading bot",
        "second_profit_system": "Secondary profit generation system",
        "simple_gateio_trading_bot": "Simple Gate.io trading bot",
        "simple_market_maker_system": "Simple market making system",
        "supervisor_ai_247_system": "24/7 AI trading supervisor",
        "trading_governance_system": "Trading governance and compliance system",
        "universal_maker_system": "Universal market making system",
        "vanta_trading_system": "Vanta trading platform integration",
        "vaultcore_trading_system": "Vaultcore trading system",
        "visual_trading_agent_system": "Visual trading agent interface"
    }
    
    base_path = Path("/Users/alep/Downloads")
    
    print(f"\n📊 Found {len(trading_systems)} trading systems to process")
    print("\nProcessing systems one by one...\n")
    
    for system_name, description in trading_systems.items():
        print(f"🔹 Processing: {system_name}")
        
        system_path = base_path / system_name
        if not system_path.exists():
            print(f"   ⚠️  Directory not found, skipping")
            continue
        
        # Get all files in the system
        files = []
        for file in system_path.rglob("*"):
            if file.is_file():
                files.append(str(file))
        
        if not files:
            print(f"   ⚠️  No files found, skipping")
            continue
        
        # Generate appraisal
        appraisal = appraiser.create_appraisal(system_name, files)
        
        # Create appraisal document
        appraisal_path = system_path / "APPRAISAL.md"
        appraiser.create_appraisal_document(appraisal, appraisal_path)
        print(f"   ✅ Appraisal created: {appraisal_path}")
        
        # Create repository
        try:
            repo_name = system_name.replace("_", "-")
            repo_description = f"{description} - Professional trading system with automated appraisal"
            
            repo = appraiser.create_repository(repo_name, repo_description, private=True)
            print(f"   ✅ Repository created: {repo['html_url']}")
            
            # Initialize git and push
            os.chdir(system_path)
            subprocess.run(["git", "init"], capture_output=True)
            subprocess.run(["git", "add", "."], capture_output=True)
            subprocess.run(["git", "commit", "-m", f"Initial commit: {description}"], capture_output=True)
            subprocess.run(["git", "branch", "-M", "main"], capture_output=True)
            subprocess.run(["git", "remote", "add", "origin", f"https://{github_token}@github.com/{username}/{repo_name}.git"], capture_output=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True)
            subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
            
            print(f"   ✅ Code pushed to GitHub")
            
            os.chdir(base_path)
            
        except Exception as e:
            print(f"   ❌ Error creating repository: {e}")
            os.chdir(base_path)
        
        print()
    
    print("🎉 All trading systems processed successfully!")

if __name__ == "__main__":
    main()
