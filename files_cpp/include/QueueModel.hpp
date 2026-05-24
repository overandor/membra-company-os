#pragma once

#include <string>
#include <cstdint>
#include <vector>

namespace depthos {

struct QueuePosition {
    double price;
    int64_t size;
    int rank;
    int64_t volume_ahead;
    int64_t volume_behind;
    int64_t time_in_queue_ms;
    
    QueuePosition() : price(0.0), size(0), rank(0), 
                     volume_ahead(0), volume_behind(0), time_in_queue_ms(0) {}
};

struct QueueMetrics {
    double trade_intensity;      // trades per second
    double cancel_rate;          // cancellations per second
    double toxicity_score;       // 0-1, higher = more toxic
    double insertion_rate;       // new orders per second
    double survival_probability; // probability queue survives
    
    QueueMetrics() : trade_intensity(0.0), cancel_rate(0.0),
                    toxicity_score(0.0), insertion_rate(0.0),
                    survival_probability(1.0) {}
};

struct FillProbabilityFactors {
    int queue_ahead;
    int queue_behind;
    double trade_intensity;
    double cancel_rate;
    double toxicity_score;
    double latency_ms;
    
    FillProbabilityFactors() : queue_ahead(0), queue_behind(0),
                             trade_intensity(0.0), cancel_rate(0.0),
                             toxicity_score(0.0), latency_ms(0.0) {}
};

class QueueModel {
public:
    QueueModel();
    ~QueueModel();
    
    // Calculate fill probability for a queue position
    double calculate_fill_probability(const FillProbabilityFactors& factors);
    
    // Simulate queue evolution over time horizon
    std::vector<QueuePosition> simulate_queue_evolution(
        const QueuePosition& initial,
        int64_t time_horizon_ms,
        const QueueMetrics& metrics);
    
    // Estimate hazard rate for queue depletion
    double hazard_rate(const QueuePosition& position, const QueueMetrics& metrics);
    
    // Calculate expected fills over time horizon
    int64_t expected_fills(const QueuePosition& position,
                         const QueueMetrics& metrics,
                         int64_t time_horizon_ms);
    
private:
    // Base fill probability without toxicity
    double base_fill_probability(int queue_ahead, double trade_intensity);
    
    // Toxicity adjustment factor
    double toxicity_adjustment(double toxicity_score);
    
    // Latency penalty factor
    double latency_penalty(double latency_ms);
};

} // namespace depthos
