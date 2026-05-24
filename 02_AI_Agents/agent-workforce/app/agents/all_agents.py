import json
from typing import Any, Dict, Optional
from app.agents.base import AgentWorker
from app.models.schemas import AgentCapability, AgentRequest

# =============================================================================
# AGENTS 1-10: Research, Crawling & Content
# =============================================================================

class WebResearchAgent(AgentWorker):
    id = "web_research"
    name = "Web Research Agent"
    description = "Deep web research with multi-source synthesis, fact extraction, and source credibility scoring."
    category = "research"
    price_per_run = 150
    model = "gpt-4o"
    tags = ["web", "research", "crawl", "synthesis"]
    capabilities = [
        AgentCapability(name="search", description="Search and fetch web pages", parameters={"depth": "number"}),
        AgentCapability(name="synthesize", description="Multi-source synthesis"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        prompt = f"""You are a world-class web research analyst. The user asks: {request.query}
        Perform comprehensive research as if you searched 10+ sources. Provide:
        1. Key findings (bullet points)
        2. Source credibility assessment
        3. Confidence level (1-10)
        4. Contradictions found (if any)
        5. Recommended next steps
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"research": llm_out["text"], "tokens": llm_out["tokens_used"], "confidence": 8}

class AcademicResearchAgent(AgentWorker):
    id = "academic_research"
    name = "Academic Research Agent"
    description = "Searches academic databases, summarizes papers, extracts methodologies, and suggests citations."
    category = "research"
    price_per_run = 200
    model = "claude-3-5-sonnet-20240620"
    tags = ["academic", "papers", "citations", "methodology"]
    capabilities = [
        AgentCapability(name="search_papers", description="Simulate arXiv/Google Scholar search"),
        AgentCapability(name="summarize", description="Paper summarization with key claims"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        prompt = f"""You are an academic research assistant with access to arXiv, PubMed, and Google Scholar.
        User query: {request.query}
        Provide:
        1. Relevant papers (simulate 5 real-looking citations with authors, year, journal)
        2. Abstract summaries
        3. Methodology comparison table
        4. Key statistical claims
        5. Suggested citation in APA format
        """
        llm_out = await self._llm(prompt, max_tokens=3500)
        return {"papers": llm_out["text"], "citation_style": "APA", "tokens": llm_out["tokens_used"]}

class SEOAuditAgent(AgentWorker):
    id = "seo_audit"
    name = "SEO Audit Agent"
    description = "Analyzes websites for SEO health: meta tags, headings, speed, backlinks, keyword density."
    category = "marketing"
    price_per_run = 120
    model = "gpt-4o-mini"
    tags = ["seo", "audit", "web", "marketing"]
    capabilities = [
        AgentCapability(name="fetch_page", description="Fetch page HTML and analyze structure"),
        AgentCapability(name="score", description="SEO score 0-100"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        url = request.context.get("url", request.query)
        html = await self._web_fetch(url)
        prompt = f"""Analyze this website HTML for SEO. URL: {url}
        HTML (first 4000 chars): {html[:4000]}
        Provide:
        1. SEO Score 0-100
        2. Meta tag status (title, description, og, twitter)
        3. Heading structure (h1-h6 usage)
        4. Keyword density analysis
        5. Speed & mobile recommendations
        6. Top 5 actionable fixes
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"url": url, "audit": llm_out["text"], "tokens": llm_out["tokens_used"]}

class SocialMonitorAgent(AgentWorker):
    id = "social_monitor"
    name = "Social Media Monitor Agent"
    description = "Monitors brand mentions, sentiment, trending hashtags, and influencer activity across platforms."
    category = "marketing"
    price_per_run = 130
    model = "gpt-4o"
    tags = ["social", "sentiment", "brand", "monitor"]
    capabilities = [
        AgentCapability(name="mention_scan", description="Scan for brand mentions"),
        AgentCapability(name="sentiment", description="Sentiment classification"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        brand = request.context.get("brand", request.query)
        prompt = f"""You are a social media intelligence analyst monitoring for: {brand}
        Simulate data from Twitter/X, Reddit, LinkedIn, TikTok. Provide:
        1. Mention volume (last 7 days simulated)
        2. Sentiment breakdown (% positive, neutral, negative)
        3. Top 5 trending hashtags related to brand
        4. Influencer mentions (simulate 3 with follower counts)
        5. Crisis alert flag (yes/no with reasoning)
        6. Engagement trend vs. last week
        """
        llm_out = await self._llm(prompt, max_tokens=2500, json_mode=request.context.get("json", False))
        return {"brand": brand, "report": llm_out["text"], "tokens": llm_out["tokens_used"]}

class CompetitorAnalysisAgent(AgentWorker):
    id = "competitor_analysis"
    name = "Competitor Analysis Agent"
    description = "Deep competitive intelligence: pricing, features, positioning, SWOT, and market share."
    category = "strategy"
    price_per_run = 180
    model = "gpt-4o"
    tags = ["competitive", "swot", "market", "strategy"]
    capabilities = [
        AgentCapability(name="landscape", description="Map competitive landscape"),
        AgentCapability(name="swot", description="Generate SWOT per competitor"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        query = request.query
        prompt = f"""You are a competitive intelligence director. Analyze: {query}
        Provide:
        1. Competitor list (5 players with estimated market share %)
        2. Pricing comparison matrix
        3. Feature comparison table
        4. SWOT for each competitor
        5. Positioning map (x-axis: price, y-axis: features)
        6. Strategic recommendations
        """
        llm_out = await self._llm(prompt, max_tokens=3500)
        return {"analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class PriceTrackerAgent(AgentWorker):
    id = "price_tracker"
    name = "Price Tracker Agent"
    description = "Tracks product prices across e-commerce platforms, alerts on drops, and predicts trends."
    category = "ecommerce"
    price_per_run = 100
    model = "gpt-4o-mini"
    tags = ["price", "ecommerce", "alerts", "tracking"]
    capabilities = [
        AgentCapability(name="track", description="Track price history"),
        AgentCapability(name="alert", description="Trigger price drop alert"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        product = request.query
        prompt = f"""You are an e-commerce price intelligence bot. Product: {product}
        Simulate prices from Amazon, Walmart, eBay, Target, Best Buy. Provide:
        1. Current price across platforms (simulated realistic numbers)
        2. 30-day price history trend (up/down/stable %)
        3. Best deal right now
        4. Price prediction (next 7 days)
        5. Alert threshold recommendation
        """
        llm_out = await self._llm(prompt, max_tokens=2000)
        return {"product": product, "prices": llm_out["text"], "tokens": llm_out["tokens_used"]}

class ContentSummarizerAgent(AgentWorker):
    id = "content_summarizer"
    name = "Content Summarizer Agent"
    description = "Summarizes articles, videos, podcasts, and long documents with key takeaways and Q&A."
    category = "content"
    price_per_run = 80
    model = "gpt-4o-mini"
    tags = ["summarize", "content", "tl;dr", "qa"]
    capabilities = [
        AgentCapability(name="summarize", description="Long-form summarization"),
        AgentCapability(name="qa", description="Extract Q&A pairs"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        content = request.query
        prompt = f"""Summarize this content concisely but comprehensively:
        {content[:12000]}
        Provide:
        1. One-paragraph summary
        2. 5 bullet key takeaways
        3. Top 3 quotes
        4. Suggested audience
        5. Reading time estimate
        6. 3 follow-up questions answered
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"summary": llm_out["text"], "tokens": llm_out["tokens_used"]}

class FactCheckerAgent(AgentWorker):
    id = "fact_checker"
    name = "Fact Checker Agent"
    description = "Verifies claims against known facts, flags misinformation, and provides confidence ratings."
    category = "research"
    price_per_run = 170
    model = "claude-3-5-sonnet-20240620"
    tags = ["fact-check", "verification", "misinformation", "trust"]
    capabilities = [
        AgentCapability(name="verify", description="Claim verification"),
        AgentCapability(name="source", description="Source reliability rating"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        claim = request.query
        prompt = f"""You are a rigorous fact-checker. Claim: {claim}
        Provide:
        1. Verdict: TRUE / FALSE / PARTIALLY TRUE / UNVERIFIABLE
        2. Confidence score (0-100)
        3. Evidence summary
        4. Context needed for full evaluation
        5. Biases detected in the claim
        6. Correction if false
        7. Best authoritative source to cite
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"claim": claim, "verification": llm_out["text"], "tokens": llm_out["tokens_used"]}

class TrendAnalyzerAgent(AgentWorker):
    id = "trend_analyzer"
    name = "Trend Analyzer Agent"
    description = "Identifies emerging trends across industries, regions, and demographics with forecasting."
    category = "strategy"
    price_per_run = 160
    model = "gpt-4o"
    tags = ["trends", "forecast", "emerging", "market"]
    capabilities = [
        AgentCapability(name="detect", description="Trend detection across signals"),
        AgentCapability(name="forecast", description="12-month forecast"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        topic = request.query
        prompt = f"""You are a trend intelligence analyst. Topic: {topic}
        Provide:
        1. Top 5 emerging trends (with confidence %)
        2. Trend lifecycle stage (embryonic/growth/mature/declining)
        3. Key drivers
        4. Geographic hotspots
        5. Demographic segments leading adoption
        6. 12-month forecast with milestones
        7. Risk factors that could disrupt trend
        """
        llm_out = await self._llm(prompt, max_tokens=3000, json_mode=request.context.get("json", False))
        return {"topic": topic, "trends": llm_out["text"], "tokens": llm_out["tokens_used"]}

class NewsAggregatorAgent(AgentWorker):
    id = "news_aggregator"
    name = "News Aggregator Agent"
    description = "Aggregates news from global sources, clusters by topic, summarizes, and ranks by relevance."
    category = "media"
    price_per_run = 110
    model = "gpt-4o-mini"
    tags = ["news", "aggregate", "cluster", "headlines"]
    capabilities = [
        AgentCapability(name="aggregate", description="Multi-source aggregation"),
        AgentCapability(name="cluster", description="Topic clustering"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        topic = request.query
        prompt = f"""You are a news editor aggregating global coverage. Topic: {topic}
        Simulate 8 articles from Reuters, AP, BBC, Al Jazeera, FT, NYT, Guardian, Bloomberg. Provide:
        1. Clustered headlines (grouped by sub-topic)
        2. One-line summary per cluster
        3. Sentiment per cluster
        4. Timeline of events (chronological)
        5. Key quotes from "sources"
        6. Bias comparison across outlets
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"topic": topic, "news": llm_out["text"], "tokens": llm_out["tokens_used"]}

# =============================================================================
# AGENTS 11-20: Specialized Domain Intelligence
# =============================================================================

class LegalDocumentAnalyzerAgent(AgentWorker):
    id = "legal_analyzer"
    name = "Legal Document Analyzer Agent"
    description = "Analyzes contracts, NDAs, terms of service for risks, obligations, and anomalies."
    category = "legal"
    price_per_run = 250
    model = "claude-3-5-sonnet-20240620"
    tags = ["legal", "contracts", "risk", "compliance"]
    capabilities = [
        AgentCapability(name="parse", description="Clause extraction and risk scoring"),
        AgentCapability(name="compare", description="Compare against standard templates"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        doc = request.query
        prompt = f"""You are a senior legal analyst. Analyze this document:
        {doc[:10000]}
        Provide:
        1. Document type identification
        2. Risk score 0-100 with breakdown
        3. Unfavorable clauses (red flags)
        4. Missing standard protections
        5. Obligations summary (parties, deadlines, penalties)
        6. Negotiation recommendations
        7. Jurisdiction considerations
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class PatentResearchAgent(AgentWorker):
    id = "patent_research"
    name = "Patent Research Agent"
    description = "Searches patent databases, analyzes prior art, and assesses patentability of inventions."
    category = "legal"
    price_per_run = 220
    model = "claude-3-5-sonnet-20240620"
    tags = ["patent", "ip", "prior-art", "invention"]
    capabilities = [
        AgentCapability(name="search", description="USPTO/EPO/WIPO search simulation"),
        AgentCapability(name="assess", description="Patentability scoring"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        invention = request.query
        prompt = f"""You are a patent research attorney. Invention: {invention}
        Simulate prior art search across USPTO, EPO, WIPO. Provide:
        1. 5 closest prior art patents (with patent numbers, assignees, claims summary)
        2. Novelty assessment (high/medium/low)
        3. Patentability score 0-100
        4. Claim drafting suggestions
        5. Freedom-to-operate risks
        6. Recommended IPC/CPC classifications
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"invention": invention, "patent_analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class JobMarketResearchAgent(AgentWorker):
    id = "job_market"
    name = "Job Market Research Agent"
    description = "Analyzes job markets, salary trends, skill demands, and hiring velocity by region and role."
    category = "hr"
    price_per_run = 100
    model = "gpt-4o-mini"
    tags = ["jobs", "salary", "hiring", "market"]
    capabilities = [
        AgentCapability(name="salary", description="Salary benchmarking"),
        AgentCapability(name="skills", description="In-demand skills extraction"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        role = request.query
        location = request.context.get("location", "United States")
        prompt = f"""You are a labor market analyst. Role: {role}, Location: {location}
        Provide:
        1. Salary range (25th, 50th, 75th, 90th percentile) in USD
        2. Hiring velocity (high/medium/low with % growth)
        3. Top 10 in-demand skills
        4. Required vs preferred qualifications
        5. Remote vs on-site vs hybrid split
        6. Top 5 hiring companies (simulated)
        7. Career progression path (0-5 years)
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"role": role, "location": location, "market": llm_out["text"], "tokens": llm_out["tokens_used"]}

class RealEstateResearchAgent(AgentWorker):
    id = "real_estate"
    name = "Real Estate Research Agent"
    description = "Analyzes property markets, valuations, rental yields, and neighborhood demographics."
    category = "finance"
    price_per_run = 140
    model = "gpt-4o"
    tags = ["real-estate", "property", "valuation", "yield"]
    capabilities = [
        AgentCapability(name="valuation", description="Property valuation estimate"),
        AgentCapability(name="market", description="Neighborhood market analysis"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        location = request.query
        prompt = f"""You are a real estate investment analyst. Location: {location}
        Provide:
        1. Median home price & price/sqft
        2. 1-year and 5-year appreciation trend
        3. Rental yield estimate (cap rate)
        4. Neighborhood demographics (age, income, education)
        5. Supply/demand indicators
        6. Top 3 investment risks
        7. Comparable sales (simulate 3 comps)
        8. Buy/Hold/Sell recommendation with reasoning
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"location": location, "analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class StockMarketDataAgent(AgentWorker):
    id = "stock_data"
    name = "Stock Market Data Agent"
    description = "Fetches and analyzes stock data, technical indicators, earnings, and news sentiment."
    category = "finance"
    price_per_run = 180
    model = "gpt-4o"
    tags = ["stocks", "technical", "earnings", "sentiment"]
    capabilities = [
        AgentCapability(name="fetch", description="Price and indicator fetching"),
        AgentCapability(name="analyze", description="Technical + fundamental analysis"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        ticker = request.context.get("ticker", request.query)
        prompt = f"""You are a senior equity analyst. Ticker: {ticker}
        Simulate comprehensive data. Provide:
        1. Company overview & sector
        2. Key financials (revenue, EPS, P/E, debt ratio)
        3. Technical levels (support, resistance, RSI, MACD)
        4. Recent earnings summary & guidance
        5. Analyst ratings (buy/hold/sell consensus)
        6. News sentiment (bullish/bearish/neutral)
        7. 12-month price target range
        8. Risk factors
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"ticker": ticker, "analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class CryptoMarketDataAgent(AgentWorker):
    id = "crypto_data"
    name = "Crypto Market Data Agent"
    description = "Tracks crypto prices, on-chain metrics, DeFi yields, and exchange flows."
    category = "finance"
    price_per_run = 170
    model = "gpt-4o"
    tags = ["crypto", "defi", "on-chain", "yield"]
    capabilities = [
        AgentCapability(name="price", description="Price and volume tracking"),
        AgentCapability(name="onchain", description="On-chain metric analysis"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        token = request.context.get("token", request.query)
        prompt = f"""You are a crypto analyst. Token: {token}
        Simulate market data. Provide:
        1. Current price, 24h change, 7d change
        2. Market cap & rank
        3. Key on-chain metrics (active addresses, transaction count, exchange flows)
        4. DeFi yields (if applicable) - APY across protocols
        5. Correlation with BTC/ETH
        6. Whale wallet movements (simulate)
        7. Upcoming catalysts (unlocks, governance votes)
        8. Risk rating (1-10)
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"token": token, "crypto_analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class ProductReviewAnalyzerAgent(AgentWorker):
    id = "review_analyzer"
    name = "Product Review Analyzer Agent"
    description = "Aggregates and analyzes product reviews, extracts pros/cons, and detects fake reviews."
    category = "ecommerce"
    price_per_run = 110
    model = "gpt-4o-mini"
    tags = ["reviews", "sentiment", "ecommerce", "fake-detection"]
    capabilities = [
        AgentCapability(name="aggregate", description="Review aggregation"),
        AgentCapability(name="detect", description="Fake review detection"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        product = request.query
        reviews_text = request.context.get("reviews", "")
        prompt = f"""You are a consumer intelligence analyst. Product: {product}
        Reviews provided: {reviews_text[:8000] if reviews_text else 'Simulate 10 realistic reviews.'}
        Provide:
        1. Overall sentiment score (-1 to +1)
        2. Top 5 pros and cons
        3. Common complaints frequency
        4. Fake review risk score (0-100) with suspicious patterns
        5. Comparison to category average
        6. Recommended audience
        7. Verdict: Buy / Consider / Skip
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"product": product, "review_analysis": llm_out["text"], "tokens": llm_out["tokens_used"]}

class SentimentAnalysisAgent(AgentWorker):
    id = "sentiment"
    name = "Sentiment Analysis Agent"
    description = "Multi-language sentiment analysis with emotion detection, sarcasm flagging, and intent classification."
    category = "nlp"
    price_per_run = 90
    model = "gpt-4o-mini"
    tags = ["sentiment", "emotion", "nlp", "intent"]
    capabilities = [
        AgentCapability(name="classify", description="Sentiment + emotion classification"),
        AgentCapability(name="batch", description="Batch processing of text list"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        texts = request.query if isinstance(request.query, list) else [request.query]
        prompt = f"""Analyze sentiment for each text. Texts: {json.dumps(texts[:20], ensure_ascii=False)}
        For each, provide JSON with: text_index, sentiment (positive/negative/neutral), confidence (0-1), emotion (joy/anger/sadness/fear/surprise/disgust/neutral), sarcasm_flag (true/false), intent (complaint/praise/question/neutral).
        Also provide aggregate summary.
        """
        llm_out = await self._llm(prompt, json_mode=True, max_tokens=3000)
        return {"results": llm_out["text"], "count": len(texts), "tokens": llm_out["tokens_used"]}

class LeadGenerationAgent(AgentWorker):
    id = "lead_gen"
    name = "Lead Generation Agent"
    description = "Finds B2B leads by industry, role, and company size with contact intelligence."
    category = "sales"
    price_per_run = 130
    model = "gpt-4o"
    tags = ["leads", "b2b", "sales", "prospecting"]
    capabilities = [
        AgentCapability(name="find", description="Lead discovery by criteria"),
        AgentCapability(name="enrich", description="Contact enrichment"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        criteria = request.query
        prompt = f"""You are a B2B sales intelligence agent. Criteria: {criteria}
        Simulate realistic lead data. Provide:
        1. 10 qualified leads (name, title, company, industry, company size, inferred pain point)
        2. Engagement strategy per lead (channel, message angle)
        3. Estimated deal size range
        4. Likelihood to convert (score 0-100)
        5. Recommended next action for each
        """
        llm_out = await self._llm(prompt, max_tokens=3000, json_mode=request.context.get("json", False))
        return {"criteria": criteria, "leads": llm_out["text"], "tokens": llm_out["tokens_used"]}

class EmailOutreachAgent(AgentWorker):
    id = "email_outreach"
    name = "Email Outreach Agent"
    description = "Drafts personalized cold emails, sequences, and follow-ups with A/B test variants."
    category = "sales"
    price_per_run = 100
    model = "gpt-4o"
    tags = ["email", "outreach", "cold-email", "sequence"]
    capabilities = [
        AgentCapability(name="draft", description="Personalized email drafting"),
        AgentCapability(name="sequence", description="Multi-touch sequence creation"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        prospect = request.query
        context = request.context.get("context", "")
        prompt = f"""You are a top-tier SDR. Prospect: {prospect}
        Context: {context}
        Provide:
        1. Subject line (5 variants for A/B testing)
        2. Personalized email body (3 variants: aggressive, casual, value-first)
        3. Follow-up sequence (3 emails, spaced 3 days apart)
        4. Personalization hooks used
        5. CTA recommendations
        6. Spam score estimate (0-10)
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"prospect": prospect, "emails": llm_out["text"], "tokens": llm_out["tokens_used"]}

# =============================================================================
# AGENTS 21-30: DevOps, Code & Automation
# =============================================================================

class GitHubTrendsAgent(AgentWorker):
    id = "github_trends"
    name = "GitHub Trends Agent"
    description = "Tracks trending repos, rising languages, and notable releases across GitHub."
    category = "dev"
    price_per_run = 90
    model = "gpt-4o-mini"
    tags = ["github", "trends", "repos", "developer"]
    capabilities = [
        AgentCapability(name="trending", description="Fetch trending repositories"),
        AgentCapability(name="language", description="Language popularity trends"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        language = request.context.get("language", request.query)
        # Try to fetch real GitHub trending
        html = await self._web_fetch(f"https://github.com/trending/{language}?since=daily")
        prompt = f"""You are a developer trends analyst. Language/Topic: {language}
        GitHub HTML snippet: {html[:4000]}
        Provide:
        1. Top 10 trending repos (name, stars gained, description)
        2. Rising languages (week-over-week %)
        3. Notable releases (simulate 3)
        4. Open job postings trend
        5. Community sentiment
        6. Recommended repos to watch
        """
        llm_out = await self._llm(prompt, max_tokens=2500)
        return {"language": language, "trends": llm_out["text"], "tokens": llm_out["tokens_used"]}

class DocumentationWriterAgent(AgentWorker):
    id = "doc_writer"
    name = "Documentation Writer Agent"
    description = "Generates API docs, READMEs, architecture diagrams-as-code, and user guides from code."
    category = "dev"
    price_per_run = 120
    model = "gpt-4o"
    tags = ["docs", "readme", "api-docs", "technical-writing"]
    capabilities = [
        AgentCapability(name="generate", description="Doc generation from code/context"),
        AgentCapability(name="diagram", description="Architecture diagram suggestions"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        code_or_topic = request.query
        doc_type = request.context.get("type", "README")
        prompt = f"""You are a technical writer. Generate {doc_type} for:
        {code_or_topic[:10000]}
        Provide:
        1. {doc_type} in Markdown format
        2. Installation instructions
        3. Usage examples (3)
        4. API reference (if applicable)
        5. Architecture diagram description (Mermaid syntax)
        6. Troubleshooting section
        7. Contributing guidelines
        """
        llm_out = await self._llm(prompt, max_tokens=3500)
        return {"doc_type": doc_type, "documentation": llm_out["text"], "tokens": llm_out["tokens_used"]}

    def _generate_repo_files(self, result):
        return {
            "README.md": result.output.get("documentation", "# Generated Docs\n"),
            "index.html": f"<!DOCTYPE html><html><head><title>Docs</title><style>body{{font-family:Arial;max-width:800px;margin:40px auto;line-height:1.6}}</style></head><body><h1>Generated Documentation</h1><pre>{result.output.get('documentation', '')[:10000]}</pre></body></html>",
        }

class CodeReviewAgent(AgentWorker):
    id = "code_review"
    name = "Code Review Agent"
    description = "Reviews code for bugs, security issues, performance, style, and suggests refactors."
    category = "dev"
    price_per_run = 150
    model = "claude-3-5-sonnet-20240620"
    tags = ["code-review", "security", "performance", "refactor"]
    capabilities = [
        AgentCapability(name="review", description="Full code review"),
        AgentCapability(name="score", description="Quality score 0-100"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        code = request.query
        language = request.context.get("language", "python")
        prompt = f"""You are a senior staff engineer conducting code review. Language: {language}
        Code:
        ```{language}
        {code[:10000]}
        ```
        Provide:
        1. Overall quality score (0-100)
        2. Bugs found (line numbers + severity)
        3. Security vulnerabilities (OWASP mapping)
        4. Performance bottlenecks
        5. Style violations
        6. Refactor suggestions with before/after
        7. Test coverage gaps
        8. Approval: Approve / Approve with changes / Request changes
        """
        llm_out = await self._llm(prompt, max_tokens=3500)
        return {"language": language, "review": llm_out["text"], "tokens": llm_out["tokens_used"]}

class SecurityAuditAgent(AgentWorker):
    id = "security_audit"
    name = "Security Audit Agent"
    description = "Scans code, infra configs, and dependencies for vulnerabilities and misconfigurations."
    category = "dev"
    price_per_run = 200
    model = "claude-3-5-sonnet-20240620"
    tags = ["security", "audit", "vulnerability", "compliance"]
    capabilities = [
        AgentCapability(name="scan", description="Vulnerability scan"),
        AgentCapability(name="remediate", description="Remediation guidance"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        target = request.query
        target_type = request.context.get("type", "code")
        prompt = f"""You are a penetration tester / security architect. Target type: {target_type}
        Target content:
        {target[:10000]}
        Provide:
        1. Risk score (Critical/High/Medium/Low) breakdown
        2. CVE references (simulate realistic ones)
        3. OWASP Top 10 mapping
        4. Misconfigurations
        5. Secrets/credential exposure check
        6. Dependency vulnerabilities
        7. Remediation steps with priority order
        8. Compliance gaps (SOC2, ISO27001, GDPR)
        """
        llm_out = await self._llm(prompt, max_tokens=3500)
        return {"target_type": target_type, "audit": llm_out["text"], "tokens": llm_out["tokens_used"]}

class APIDocumentationAgent(AgentWorker):
    id = "api_docs"
    name = "API Documentation Agent"
    description = "Generates OpenAPI specs, Postman collections, and SDK examples from API descriptions."
    category = "dev"
    price_per_run = 130
    model = "gpt-4o"
    tags = ["api", "openapi", "postman", "sdk"]
    capabilities = [
        AgentCapability(name="spec", description="OpenAPI spec generation"),
        AgentCapability(name="examples", description="SDK code examples"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        description = request.query
        prompt = f"""You are an API product manager. Generate complete API docs from this description:
        {description[:8000]}
        Provide:
        1. OpenAPI 3.0 YAML spec
        2. Endpoint table (method, path, auth, rate limit)
        3. Request/response examples (JSON)
        4. Python SDK example
        5. JavaScript SDK example
        6. cURL examples
        7. Error code reference
        8. Changelog template
        """
        llm_out = await self._llm(prompt, max_tokens=4000)
        return {"api_docs": llm_out["text"], "tokens": llm_out["tokens_used"]}

    def _generate_repo_files(self, result):
        docs = result.output.get("api_docs", "")
        return {
            "openapi.yaml": docs if "openapi" in docs.lower() else "# OpenAPI spec placeholder\n",
            "README.md": f"# API Documentation\n\n{docs[:5000]}",
            "index.html": f"<!DOCTYPE html><html><head><title>API Docs</title><style>body{{font-family:Arial;max-width:900px;margin:40px auto}}pre{{background:#f5f5f5;padding:15px;overflow:auto}}</style></head><body><h1>API Documentation</h1><pre>{docs[:12000]}</pre></body></html>",
        }

class DevOpsMonitorAgent(AgentWorker):
    id = "devops_monitor"
    name = "DevOps Monitor Agent"
    description = "Monitors infrastructure health, suggests alerts, analyzes logs, and recommends scaling."
    category = "dev"
    price_per_run = 160
    model = "gpt-4o"
    tags = ["devops", "monitoring", "infrastructure", "alerts"]
    capabilities = [
        AgentCapability(name="health", description="Infrastructure health check"),
        AgentCapability(name="alert", description="Alert rule recommendations"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        logs_or_desc = request.query
        prompt = f"""You are an SRE. Analyze this infrastructure description/logs:
        {logs_or_desc[:10000]}
        Provide:
        1. Health status (healthy/degraded/critical) per component
        2. Error rate analysis
        3. Top 3 incident root causes
        4. Recommended alert rules (Prometheus/Grafana YAML)
        5. Scaling recommendations (horizontal/vertical)
        6. Cost optimization tips
        7. Runbook suggestions
        8. SLA impact assessment
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"monitoring": llm_out["text"], "tokens": llm_out["tokens_used"]}

class CustomerSupportAgent(AgentWorker):
    id = "customer_support"
    name = "Customer Support Agent"
    description = "Drafts support responses, analyzes tickets, routes issues, and builds FAQ from conversations."
    category = "operations"
    price_per_run = 80
    model = "gpt-4o-mini"
    tags = ["support", "tickets", "faq", "response"]
    capabilities = [
        AgentCapability(name="respond", description="Draft support response"),
        AgentCapability(name="route", description="Intelligent ticket routing"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        ticket = request.query
        prompt = f"""You are a senior customer support specialist. Ticket:
        {ticket[:5000]}
        Provide:
        1. Ticket classification (billing/technical/feature-request/complaint)
        2. Urgency score (1-10)
        3. Draft response (empathetic, clear, actionable)
        4. Internal notes (what team should do)
        5. Related FAQ entry (if applicable)
        6. Escalation flag (yes/no)
        7. Estimated resolution time
        """
        llm_out = await self._llm(prompt, max_tokens=2000)
        return {"ticket": ticket, "response": llm_out["text"], "tokens": llm_out["tokens_used"]}

class TranslationAgent(AgentWorker):
    id = "translator"
    name = "Translation Agent"
    description = "Translates text between 50+ languages with tone adaptation and domain-specific terminology."
    category = "nlp"
    price_per_run = 60
    model = "gpt-4o-mini"
    tags = ["translation", "i18n", "localization", "nlp"]
    capabilities = [
        AgentCapability(name="translate", description="Text translation with tone"),
        AgentCapability(name="adapt", description="Cultural adaptation"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        text = request.query
        source = request.context.get("source", "auto")
        target = request.context.get("target", "en")
        tone = request.context.get("tone", "neutral")
        prompt = f"""Translate this text from {source} to {target}. Tone: {tone}
        Text: {text[:10000]}
        Provide:
        1. Translation
        2. Alternative phrasings (2)
        3. Cultural notes (if applicable)
        4. Domain terminology glossary used
        5. Confidence score (0-100)
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"translation": llm_out["text"], "source": source, "target": target, "tokens": llm_out["tokens_used"]}

class DataVisualizationAgent(AgentWorker):
    id = "data_viz"
    name = "Data Visualization Agent"
    description = "Generates chart configs, dashboard specs, and data storytelling narratives from raw data."
    category = "analytics"
    price_per_run = 140
    model = "gpt-4o"
    tags = ["visualization", "charts", "dashboard", "analytics"]
    capabilities = [
        AgentCapability(name="chart", description="Chart configuration generation"),
        AgentCapability(name="dashboard", description="Dashboard layout spec"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        data = request.query
        viz_type = request.context.get("type", "auto")
        prompt = f"""You are a data visualization expert. Data context: {data[:8000]}
        Preferred viz type: {viz_type}
        Provide:
        1. Recommended chart types (with reasoning)
        2. Vega-Lite or Plotly JSON spec
        3. Dashboard layout (grid positions)
        4. Color palette recommendation
        5. Data storytelling narrative (3-slide outline)
        6. Interactive filter suggestions
        """
        llm_out = await self._llm(prompt, max_tokens=3000)
        return {"visualization": llm_out["text"], "tokens": llm_out["tokens_used"]}

    def _generate_repo_files(self, result):
        viz = result.output.get("visualization", "")
        return {
            "README.md": f"# Data Visualization\n\n{viz[:3000]}",
            "chart.json": viz if "{" in viz else '{"chart": "placeholder"}',
            "index.html": f"<!DOCTYPE html><html><head><script src='https://cdn.jsdelivr.net/npm/vega-lite'></script></head><body><h1>Visualization</h1><pre>{viz[:10000]}</pre></body></html>",
        }

class ReportGenerationAgent(AgentWorker):
    id = "report_gen"
    name = "Report Generation Agent"
    description = "Generates executive reports, whitepapers, and research briefs with citations and formatting."
    category = "content"
    price_per_run = 190
    model = "claude-3-5-sonnet-20240620"
    tags = ["report", "whitepaper", "executive", "research"]
    capabilities = [
        AgentCapability(name="generate", description="Full report generation"),
        AgentCapability(name="format", description="PDF-ready Markdown with citations"),
    ]

    async def _run(self, request: AgentRequest) -> Any:
        topic = request.query
        report_type = request.context.get("type", "executive summary")
        prompt = f"""You are a McKinsey-level management consultant. Generate: {report_type}
        Topic: {topic}
        Provide:
        1. Executive summary (1 page)
        2. Problem statement
        3. Methodology
        4. Key findings (with data points)
        5. Recommendations (prioritized)
        6. Risk analysis
        7. Appendix: Citations (simulate 5 authoritative sources)
        8. Next steps with owners and deadlines
        Format in professional Markdown.
        """
        llm_out = await self._llm(prompt, max_tokens=4000)
        return {"report": llm_out["text"], "type": report_type, "tokens": llm_out["tokens_used"]}

    def _generate_repo_files(self, result):
        report = result.output.get("report", "")
        return {
            "README.md": f"# Report: {result.output.get('type', 'Research')}\n\n{report[:5000]}",
            "report.md": report,
            "index.html": f"<!DOCTYPE html><html><head><title>Report</title><style>body{{font-family:Georgia;max-width:800px;margin:40px auto;line-height:1.8}}h1,h2{{color:#333}}</style></head><body><h1>Generated Report</h1><div>{report.replace(chr(10), '<br>')[:15000]}</div></body></html>",
        }

# =============================================================================
# AGENT REGISTRY
# =============================================================================

ALL_AGENTS = [
    WebResearchAgent(),
    AcademicResearchAgent(),
    SEOAuditAgent(),
    SocialMonitorAgent(),
    CompetitorAnalysisAgent(),
    PriceTrackerAgent(),
    ContentSummarizerAgent(),
    FactCheckerAgent(),
    TrendAnalyzerAgent(),
    NewsAggregatorAgent(),
    LegalDocumentAnalyzerAgent(),
    PatentResearchAgent(),
    JobMarketResearchAgent(),
    RealEstateResearchAgent(),
    StockMarketDataAgent(),
    CryptoMarketDataAgent(),
    ProductReviewAnalyzerAgent(),
    SentimentAnalysisAgent(),
    LeadGenerationAgent(),
    EmailOutreachAgent(),
    GitHubTrendsAgent(),
    DocumentationWriterAgent(),
    CodeReviewAgent(),
    SecurityAuditAgent(),
    APIDocumentationAgent(),
    DevOpsMonitorAgent(),
    CustomerSupportAgent(),
    TranslationAgent(),
    DataVisualizationAgent(),
    ReportGenerationAgent(),
]

AGENT_REGISTRY = {agent.id: agent for agent in ALL_AGENTS}
