#include "QueueModel.hpp"
#include <cmath>
#include <algorithm>

namespace depthos {

QueueModel::QueueModel() {}

QueueModel::~QueueModel() {}

double QueueModel::calculate_fill_probability(const FillProbabilityFactors& factors) {
    // Base probability from queue position and trade intensity
    double base_prob = base_fill_probability(factors.queue_ahead, factors.trade_intensity);
    
    // Apply adjustments
    double toxicity_adj = toxicity_adjustment(factors.toxicity_score);
    double latency_adj = latency_penalty(factors.latency_ms);
    
    // Combine factors
    double fill_prob = base_prob * toxicity_adj * latency_adj;
    
    // Clamp to [0, 1]
    return std::max(0.0, std::min(1.0, fill_prob));
}

std::vector<QueuePosition> QueueModel::simulate_queue_evolution(
    const QueuePosition& initial,
    int64_t time_horizon_ms,
    const QueueMetrics& metrics)
{
    std::vector<QueuePosition> evolution;
    
    QueuePosition current = initial;
    int64_t time_step_ms = 100;  // 100ms steps
    int64_t steps = time_horizon_ms / time_step_ms;
    
    for (int64_t i = 0; i < steps; ++i) {
        // Simulate queue depletion
        double trades_per_step = metrics.trade_intensity * (time_step_ms / 1000.0);
        double cancels_per_step = metrics.cancel_rate * (time_step_ms / 1000.0);
        double insertions_per_step = metrics.insertion_rate * (time_step_ms / 1000.0);
        
        // Update queue position
        current.volume_ahead -= static_cast<int64_t>(trades_per_step + cancels_per_step);
        current.volume_ahead += static_cast<int64_t>(insertions_per_step);
        current.volume_ahead = std::max(0LL, current.volume_ahead);
        
        current.time_in_queue_ms += time_step_ms;
        
        evolution.push_back(current);
        
        // Stop if queue is depleted
        if (current.volume_ahead <= 0) break;
    }
    
    return evolution;
}

double QueueModel::hazard_rate(const QueuePosition& position, const QueueMetrics& metrics) {
    // Hazard rate = rate of queue depletion
    // Higher trade intensity and cancel rate = higher hazard rate
    
    double depletion_rate = metrics.trade_intensity + metrics.cancel_rate;
    
    // Normalize by queue position
    if (position.volume_ahead <= 0) return 0.0;
    
    double hazard = depletion_rate / position.volume_ahead;
    
    // Adjust for toxicity (toxic flow depletes queue faster)
    hazard *= (1.0 + metrics.toxicity_score);
    
    return hazard;
}

int64_t QueueModel::expected_fills(
    const QueuePosition& position,
    const QueueMetrics& metrics,
    int64_t time_horizon_ms)
{
    FillProbabilityFactors factors;
    factors.queue_ahead = position.volume_ahead;
    factors.queue_behind = position.volume_behind;
    factors.trade_intensity = metrics.trade_intensity;
    factors.cancel_rate = metrics.cancel_rate;
    factors.toxicity_score = metrics.toxicity_score;
    factors.latency_ms = 0;  // Assume instantaneous for expected fills
    
    double fill_prob = calculate_fill_probability(factors);
    
    // Expected fills = fill_prob * size
    return static_cast<int64_t>(fill_prob * position.size);
}

double QueueModel::base_fill_probability(int queue_ahead, double trade_intensity) {
    // Base fill probability decreases with queue position
    // Increases with trade intensity
    
    if (queue_ahead <= 0) return 1.0;  // At front of queue
    
    // Exponential decay based on queue position
    double queue_decay = std::exp(-queue_ahead / 1000.0);
    
    // Linear increase with trade intensity
    double intensity_factor = std::min(1.0, trade_intensity / 10.0);
    
    return queue_decay * (0.5 + 0.5 * intensity_factor);
}

double QueueModel::toxicity_adjustment(double toxicity_score) {
    // Toxicity reduces fill probability
    // Score 0-1, where 1 = highly toxic
    
    // Linear reduction: 1.0 at toxicity 0, 0.5 at toxicity 1
    return 1.0 - 0.5 * toxicity_score;
}

double QueueModel::latency_penalty(double latency_ms) {
    // Latency reduces fill probability
    // Higher latency = lower fill probability
    
    // Assume 100ms latency = 10% reduction
    double latency_factor = latency_ms / 1000.0;
    return std::max(0.5, 1.0 - latency_factor);
}

} // namespace depthos
