"""
SMS Transaction Monitoring and Logging
Comprehensive monitoring system for SMS transactions with metrics, alerts, and logging.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import time
from pathlib import Path

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("sms_monitoring")


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    """Metric data point"""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Alert:
    """Alert data"""
    severity: AlertSeverity
    message: str
    source: str
    metric_name: str = ""
    threshold: float = 0
    current_value: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "message": self.message,
            "source": self.source,
            "metric_name": self.metric_name,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class TransactionLog:
    """Detailed transaction log entry"""
    transaction_id: str
    phone_number: str
    transaction_type: str
    amount: float
    status: str
    processing_time_ms: float
    error_message: str = ""
    steps: List[Dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "transaction_id": self.transaction_id,
            "phone_number": self.phone_number,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "status": self.status,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
            "steps": self.steps,
            "timestamp": self.timestamp.isoformat()
        }


class SMSMonitoringSystem:
    """Comprehensive monitoring system for SMS transactions"""
    
    def __init__(self, max_metrics: int = 10000, max_alerts: int = 1000, max_logs: int = 5000):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.alerts: List[Alert] = []
        self.transaction_logs: List[TransactionLog] = []
        
        self.max_metrics = max_metrics
        self.max_alerts = max_alerts
        self.max_logs = max_logs
        
        self.alert_handlers: List[Callable] = []
        self.metric_thresholds: Dict[str, Dict] = {}
        
        # Real-time counters
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Start monitoring loop
        self.monitoring_active = True
        self.monitoring_task = None
        
    def start_monitoring(self):
        """Start the monitoring loop"""
        if not self.monitoring_task:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("SMS monitoring system started")
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("SMS monitoring system stopped")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                await self._check_thresholds()
                await self._cleanup_old_data()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, labels: Dict = None):
        """Record a metric"""
        labels = labels or {}
        metric = Metric(name=name, type=metric_type, value=value, labels=labels)
        
        # Store in metrics history
        self.metrics[name].append(metric)
        if len(self.metrics[name]) > self.max_metrics:
            self.metrics[name] = self.metrics[name][-self.max_metrics:]
        
        # Update real-time counters
        if metric_type == MetricType.COUNTER:
            self.counters[name] += value
        elif metric_type == MetricType.GAUGE:
            self.gauges[name] = value
        elif metric_type == MetricType.HISTOGRAM:
            self.histograms[name].append(value)
        
        logger.debug(f"Recorded metric: {name}={value} ({metric_type.value})")
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict = None):
        """Increment a counter metric"""
        self.record_metric(name, value, MetricType.COUNTER, labels)
    
    def set_gauge(self, name: str, value: float, labels: Dict = None):
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, labels)
    
    def record_histogram(self, name: str, value: float, labels: Dict = None):
        """Record a histogram metric"""
        self.record_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def log_transaction(self, log: TransactionLog):
        """Log a transaction"""
        self.transaction_logs.append(log)
        
        # Keep only recent logs
        if len(self.transaction_logs) > self.max_logs:
            self.transaction_logs = self.transaction_logs[-self.max_logs:]
        
        # Record metrics
        self.increment_counter("sms_transactions_total", labels={"status": log.status})
        self.set_gauge("sms_processing_time_ms", log.processing_time_ms)
        
        if log.status == "completed":
            self.increment_counter("sms_transactions_completed")
            self.record_histogram("sms_completed_amount", log.amount)
        elif log.status == "failed":
            self.increment_counter("sms_transactions_failed")
        
        logger.info(f"Logged transaction: {log.transaction_id} - {log.status}")
    
    def set_metric_threshold(self, metric_name: str, threshold: float, operator: str = ">", severity: AlertSeverity = AlertSeverity.WARNING):
        """Set threshold for metric alerting"""
        self.metric_thresholds[metric_name] = {
            "threshold": threshold,
            "operator": operator,
            "severity": severity
        }
        logger.info(f"Set threshold for {metric_name}: {operator} {threshold} ({severity.value})")
    
    def add_alert_handler(self, handler: Callable):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
    
    async def _check_thresholds(self):
        """Check if any metrics exceed thresholds"""
        for metric_name, threshold_config in self.metric_thresholds.items():
            current_value = self.gauges.get(metric_name, 0)
            threshold = threshold_config["threshold"]
            operator = threshold_config["operator"]
            severity = threshold_config["severity"]
            
            triggered = False
            if operator == ">" and current_value > threshold:
                triggered = True
            elif operator == "<" and current_value < threshold:
                triggered = True
            elif operator == "==" and current_value == threshold:
                triggered = True
            elif operator == ">=" and current_value >= threshold:
                triggered = True
            elif operator == "<=" and current_value <= threshold:
                triggered = True
            
            if triggered:
                await self._trigger_alert(metric_name, current_value, threshold, severity)
    
    async def _trigger_alert(self, metric_name: str, current_value: float, threshold: float, severity: AlertSeverity):
        """Trigger an alert"""
        alert = Alert(
            severity=severity,
            message=f"Metric {metric_name} exceeded threshold: {current_value} {self.metric_thresholds[metric_name]['operator']} {threshold}",
            source="sms_monitoring",
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value
        )
        
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        logger.warning(f"Alert triggered: {alert.message}")
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Clean old metrics
        for metric_name in list(self.metrics.keys()):
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name] 
                if m.timestamp > cutoff_time
            ]
        
        # Clean old alerts
        self.alerts = [
            alert for alert in self.alerts 
            if alert.timestamp > cutoff_time or not alert.resolved
        ]
        
        # Clean old logs
        self.transaction_logs = [
            log for log in self.transaction_logs 
            if log.timestamp > cutoff_time
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {}
        }
        
        for name, values in self.histograms.items():
            if values:
                summary["histograms"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values)
                }
        
        return summary
    
    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        """Get recent alerts"""
        return [alert.to_dict() for alert in self.alerts[-limit:]]
    
    def get_transaction_logs(self, phone_number: str = None, status: str = None, limit: int = 100) -> List[Dict]:
        """Get transaction logs with optional filters"""
        logs = self.transaction_logs
        
        if phone_number:
            logs = [log for log in logs if log.phone_number == phone_number]
        
        if status:
            logs = [log for log in logs if log.status == status]
        
        # Sort by timestamp descending
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [log.to_dict() for log in logs[:limit]]
    
    def export_metrics(self, format: str = "prometheus") -> str:
        """Export metrics in specified format"""
        if format == "prometheus":
            return self._export_prometheus()
        elif format == "json":
            return json.dumps(self.get_metrics_summary(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Export counters
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # Export gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        # Export histograms
        for name, values in self.histograms.items():
            if values:
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{name}_count {len(values)}")
                lines.append(f"{name}_sum {sum(values)}")
                lines.append(f"{name}_bucket {{le=\"+Inf\"}} {len(values)}")
        
        return "\n".join(lines)
    
    def save_logs_to_file(self, filepath: str):
        """Save transaction logs to file"""
        logs_data = [log.to_dict() for log in self.transaction_logs]
        
        with open(filepath, 'w') as f:
            json.dump(logs_data, f, indent=2)
        
        logger.info(f"Saved {len(logs_data)} transaction logs to {filepath}")


# Global monitoring instance
sms_monitoring = SMSMonitoringSystem()

# Set up default thresholds
sms_monitoring.set_metric_threshold("sms_transactions_failed", 10, ">", AlertSeverity.ERROR)
sms_monitoring.set_metric_threshold("sms_processing_time_ms", 5000, ">", AlertSeverity.WARNING)