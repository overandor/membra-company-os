"""
LLM Validator Network - Manages LLM inference as validator service
Coordinates LLM nodes for inference, validation, and oracle functions.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json
import hashlib
import subprocess
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMModel:
    """LLM model information"""
    model_id: str
    name: str
    provider: str  # 'ollama', 'openai', 'anthropic', 'local'
    parameters: Dict
    max_tokens: int
    context_window: int
    inference_cost_per_token: float
    is_available: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LLMInferenceRequest:
    """LLM inference request"""
    request_id: str
    prompt: str
    model_id: str
    temperature: float
    max_tokens: int
    context: Dict
    priority: int  # 1-10, higher is more important
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LLMInferenceResponse:
    """LLM inference response"""
    request_id: str
    model_id: str
    response: str
    tokens_used: int
    inference_time_ms: int
    cost: float
    confidence: float
    validator_id: str
    timestamp: str
    is_valid: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LLMValidatorNode:
    """LLM validator node information"""
    node_id: str
    model_id: str
    wallet_address: str
    stake_amount: int
    total_inferences: int
    successful_inferences: int
    average_inference_time_ms: float
    reputation_score: float
    last_active: str
    status: str  # 'active', 'inactive', 'slashed'
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_inference(self, prompt: str, model_params: Dict) -> Tuple[str, int, float]:
        """Generate inference and return (response, tokens_used, cost)"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.available_models = []
    
    async def generate_inference(self, prompt: str, model_params: Dict) -> Tuple[str, int, float]:
        """Generate inference using Ollama"""
        import aiohttp
        
        model = model_params.get('model', 'llama2')
        temperature = model_params.get('temperature', 0.7)
        
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", 
                                      json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', '')
                        # Ollama doesn't provide token count, estimate it
                        tokens_used = len(response_text.split()) * 1.3  # Rough estimate
                        cost = tokens_used * 0.0001  # Minimal cost for local inference
                        return response_text, int(tokens_used), cost
                    else:
                        raise Exception(f"Ollama API error: {response.status}")
        except Exception as e:
            logger.error(f"Ollama inference failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            import subprocess
            result = subprocess.run(['curl', f'{self.base_url}/api/tags'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate_inference(self, prompt: str, model_params: Dict) -> Tuple[str, int, float]:
        """Generate mock inference"""
        self.call_count += 1
        
        # Generate a deterministic response based on prompt
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        response = f"Mock LLM response #{self.call_count} for prompt hash: {prompt_hash[:8]}"
        
        tokens_used = len(response.split())
        cost = tokens_used * 0.001
        
        # Simulate inference delay
        await asyncio.sleep(0.1)
        
        return response, tokens_used, cost
    
    def is_available(self) -> bool:
        """Mock provider is always available"""
        return True


class LLMValidatorNetwork:
    """Network of LLM validator nodes"""
    
    def __init__(self):
        self.validators: Dict[str, LLMValidatorNode] = {}
        self.models: Dict[str, LLMModel] = {}
        self.providers: Dict[str, LLMProvider] = {}
        self.inference_queue: List[LLMInferenceRequest] = []
        self.inference_history: List[LLMInferenceResponse] = []
        
        self._initialize_providers()
        self._initialize_models()
    
    def _initialize_providers(self):
        """Initialize LLM providers"""
        # Try to initialize Ollama provider
        ollama_provider = OllamaProvider()
        if ollama_provider.is_available():
            self.providers['ollama'] = ollama_provider
            logger.info("Ollama provider initialized")
        else:
            logger.warning("Ollama not available, using mock provider")
        
        # Always add mock provider as fallback
        self.providers['mock'] = MockLLMProvider()
    
    def _initialize_models(self):
        """Initialize available LLM models"""
        models = [
            LLMModel(
                model_id='llama2-7b',
                name='Llama 2 7B',
                provider='ollama',
                parameters={'temperature': 0.7, 'top_p': 0.9},
                max_tokens=4096,
                context_window=4096,
                inference_cost_per_token=0.0001,
                is_available='ollama' in self.providers
            ),
            LLMModel(
                model_id='mock-gpt',
                name='Mock GPT',
                provider='mock',
                parameters={'temperature': 0.7},
                max_tokens=2048,
                context_window=2048,
                inference_cost_per_token=0.001,
                is_available=True
            )
        ]
        
        for model in models:
            self.models[model.model_id] = model
    
    def register_validator(self, model_id: str, wallet_address: str, 
                          stake_amount: int = 1000) -> LLMValidatorNode:
        """Register a new LLM validator"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        node_id = hashlib.sha256(
            f"{model_id}{wallet_address}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        validator = LLMValidatorNode(
            node_id=node_id,
            model_id=model_id,
            wallet_address=wallet_address,
            stake_amount=stake_amount,
            total_inferences=0,
            successful_inferences=0,
            average_inference_time_ms=0.0,
            reputation_score=1.0,
            last_active=datetime.now().isoformat(),
            status='active'
        )
        
        self.validators[node_id] = validator
        logger.info(f"Registered LLM validator {node_id} with model {model_id}")
        
        return validator
    
    async def submit_inference_request(
        self,
        prompt: str,
        model_id: str = 'mock-gpt',
        temperature: float = 0.7,
        max_tokens: int = 500,
        priority: int = 5,
        context: Dict = None
    ) -> LLMInferenceResponse:
        """Submit an inference request"""
        context = context or {}
        
        # Check if model is available
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        if not model.is_available:
            raise ValueError(f"Model {model_id} is not available")
        
        # Create request
        request_id = hashlib.sha256(
            f"{prompt}{model_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        request = LLMInferenceRequest(
            request_id=request_id,
            prompt=prompt,
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            context=context,
            priority=priority,
            timestamp=datetime.now().isoformat()
        )
        
        # Select validator
        validator = self._select_validator(model_id)
        if not validator:
            raise Exception("No available validators for this model")
        
        # Process inference
        start_time = datetime.now()
        
        try:
            provider = self.providers[model.provider]
            response_text, tokens_used, cost = await provider.generate_inference(
                prompt,
                {
                    'model': model_id,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            )
            
            inference_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Validate response
            is_valid = self._validate_response(response_text, prompt)
            
            # Create response
            inference_response = LLMInferenceResponse(
                request_id=request_id,
                model_id=model_id,
                response=response_text,
                tokens_used=tokens_used,
                inference_time_ms=inference_time_ms,
                cost=cost,
                confidence=0.8 if is_valid else 0.3,
                validator_id=validator.node_id,
                timestamp=datetime.now().isoformat(),
                is_valid=is_valid
            )
            
            # Update validator stats
            validator.total_inferences += 1
            if is_valid:
                validator.successful_inferences += 1
            
            # Update average inference time
            total_time = validator.average_inference_time_ms * (validator.total_inferences - 1)
            validator.average_inference_time_ms = (total_time + inference_time_ms) / validator.total_inferences
            
            validator.last_active = datetime.now().isoformat()
            
            # Update reputation
            self._update_validator_reputation(validator, is_valid)
            
            # Store history
            self.inference_history.append(inference_response)
            
            logger.info(f"Inference {request_id} completed in {inference_time_ms}ms")
            return inference_response
            
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise
    
    def _select_validator(self, model_id: str) -> Optional[LLMValidatorNode]:
        """Select a validator for the given model"""
        model_validators = [
            v for v in self.validators.values() 
            if v.model_id == model_id and v.status == 'active'
        ]
        
        if not model_validators:
            return None
        
        # Select validator with highest reputation
        return max(model_validators, key=lambda v: v.reputation_score)
    
    def _validate_response(self, response: str, prompt: str) -> bool:
        """Validate LLM response"""
        # Basic validation checks
        if not response or len(response) < 10:
            return False
        
        if len(response) > 10000:  # Prevent extremely long responses
            return False
        
        # Check for coherent response (simplified)
        words = response.split()
        if len(words) < 3:
            return False
        
        return True
    
    def _update_validator_reputation(self, validator: LLMValidatorNode, success: bool):
        """Update validator reputation"""
        if success:
            validator.reputation_score = min(1.0, validator.reputation_score + 0.01)
        else:
            validator.reputation_score = max(0.0, validator.reputation_score - 0.05)
            
            if validator.reputation_score < 0.3:
                validator.status = 'slashed'
                logger.warning(f"Validator {validator.node_id} slashed due to low reputation")
    
    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        total_inferences = sum(v.total_inferences for v in self.validators.values())
        successful_inferences = sum(v.successful_inferences for v in self.validators.values())
        
        total_cost = sum(r.cost for r in self.inference_history)
        total_tokens = sum(r.tokens_used for r in self.inference_history)
        
        avg_inference_time = (
            sum(r.inference_time_ms for r in self.inference_history) / len(self.inference_history)
            if self.inference_history else 0
        )
        
        return {
            'total_validators': len(self.validators),
            'active_validators': len([v for v in self.validators.values() if v.status == 'active']),
            'available_models': len([m for m in self.models.values() if m.is_available]),
            'total_inferences': total_inferences,
            'successful_inferences': successful_inferences,
            'success_rate': successful_inferences / total_inferences if total_inferences > 0 else 0.0,
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'average_inference_time_ms': avg_inference_time,
            'average_reputation': (
                sum(v.reputation_score for v in self.validators.values()) / len(self.validators)
                if self.validators else 0.0
            )
        }


class LLMOracle:
    """LLM-based oracle for advanced decision making"""
    
    def __init__(self, validator_network: LLMValidatorNetwork):
        self.validator_network = validator_network
    
    async def get_price_prediction(self, asset: str, context_data: Dict) -> Dict:
        """Get LLM-based price prediction"""
        prompt = f"""
        Analyze the following market data for {asset} and provide a price prediction:
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Provide:
        1. Predicted price direction (up/down/sideways)
        2. Confidence level (0-1)
        3. Key factors influencing your prediction
        4. Risk assessment (low/medium/high)
        """
        
        try:
            response = await self.validator_network.submit_inference_request(
                prompt=prompt,
                model_id='mock-gpt',
                max_tokens=300
            )
            
            return {
                'asset': asset,
                'prediction': response.response,
                'confidence': response.confidence,
                'validator_id': response.validator_id,
                'timestamp': response.timestamp
            }
        except Exception as e:
            logger.error(f"Price prediction failed: {e}")
            return {'error': str(e)}
    
    async def analyze_arbitrage_opportunity(self, opportunity_data: Dict) -> Dict:
        """Analyze arbitrage opportunity using LLM"""
        prompt = f"""
        Analyze this arbitrage opportunity:
        
        Opportunity Data:
        {json.dumps(opportunity_data, indent=2)}
        
        Provide:
        1. Viability assessment (high/medium/low)
        2. Risk factors
        3. Recommended action
        4. Optimal execution strategy
        """
        
        try:
            response = await self.validator_network.submit_inference_request(
                prompt=prompt,
                model_id='mock-gpt',
                max_tokens=400
            )
            
            return {
                'analysis': response.response,
                'confidence': response.confidence,
                'validator_id': response.validator_id,
                'timestamp': response.timestamp
            }
        except Exception as e:
            logger.error(f"Arbitrage analysis failed: {e}")
            return {'error': str(e)}


async def main():
    """Example usage"""
    # Initialize validator network
    network = LLMValidatorNetwork()
    
    # Register validators
    validator1 = network.register_validator('mock-gpt', 'wallet_1', stake_amount=1500)
    validator2 = network.register_validator('mock-gpt', 'wallet_2', stake_amount=1200)
    
    print(f"=== Registered Validators ===")
    print(f"Validator 1: {validator1.node_id}")
    print(f"Validator 2: {validator2.node_id}")
    
    # Submit inference request
    response = await network.submit_inference_request(
        prompt="Analyze the current market conditions for Solana",
        model_id='mock-gpt',
        temperature=0.7
    )
    
    print(f"\n=== Inference Response ===")
    print(f"Response: {response.response}")
    print(f"Tokens Used: {response.tokens_used}")
    print(f"Cost: ${response.cost:.6f}")
    print(f"Inference Time: {response.inference_time_ms}ms")
    
    # Get network stats
    stats = network.get_network_stats()
    print(f"\n=== Network Stats ===")
    print(json.dumps(stats, indent=2))
    
    # Test LLM Oracle
    oracle = LLMOracle(network)
    prediction = await oracle.get_price_prediction(
        'SOL',
        {'current_price': 150.0, 'volume': 1000000, 'sentiment': 'positive'}
    )
    
    print(f"\n=== Price Prediction ===")
    print(json.dumps(prediction, indent=2))


if __name__ == '__main__':
    asyncio.run(main())