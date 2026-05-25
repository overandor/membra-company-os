'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [portfolioValue, setPortfolioValue] = useState(2456789.45);
  const [activeFiles, setActiveFiles] = useState(1234);
  const [dailyChange, setDailyChange] = useState(3.2);

  useEffect(() => {
    // Simulate initial data loading
    setTimeout(() => setIsLoading(false), 1500);
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      setPortfolioValue(prev => prev + (Math.random() - 0.5) * 1000);
      setDailyChange(prev => prev + (Math.random() - 0.5) * 0.1);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="neu-card p-8">
          <div className="neu-pulse text-xl font-semibold">Loading IP Asset Platform...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="neu-card m-4 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold neu-heading">IP Asset Platform</h1>
            <p className="neu-text">Comprehensive IP Management & Liquidity Derivation</p>
          </div>
          <div className="flex gap-4">
            <Link href="/dashboard">
              <button className="neu-button">Dashboard</button>
            </Link>
            <Link href="/files">
              <button className="neu-button">Files</button>
            </Link>
            <Link href="/analytics">
              <button className="neu-button">Analytics</button>
            </Link>
            <Link href="/billing">
              <button className="neu-button">Billing</button>
            </Link>
            <Link href="/settings">
              <button className="neu-button">Settings</button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="neu-container">
        {/* Portfolio Overview */}
        <section className="mb-8">
          <h2 className="text-xl font-bold neu-heading mb-4">Portfolio Overview</h2>
          <div className="neu-grid neu-grid-4">
            <div className="neu-stat-card neu-slide-in">
              <div className="neu-subheading text-sm">Total Portfolio Value</div>
              <div className="text-3xl font-bold neu-text-primary">
                ${portfolioValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className={`neu-badge ${dailyChange >= 0 ? 'success' : 'error'} mt-2`}>
                {dailyChange >= 0 ? '+' : ''}{dailyChange.toFixed(2)}%
              </div>
            </div>

            <div className="neu-stat-card neu-slide-in" style={{ animationDelay: '0.1s' }}>
              <div className="neu-subheading text-sm">Active IP Assets</div>
              <div className="text-3xl font-bold neu-text-primary">{activeFiles.toLocaleString()}</div>
              <div className="neu-badge success mt-2">+12 this week</div>
            </div>

            <div className="neu-stat-card neu-slide-in" style={{ animationDelay: '0.2s' }}>
              <div className="neu-subheading text-sm">Agent Work Hours</div>
              <div className="text-3xl font-bold neu-text-primary">1,234.5</div>
              <div className="neu-badge warning mt-2">This month</div>
            </div>

            <div className="neu-stat-card neu-slide-in" style={{ animationDelay: '0.3s' }}>
              <div className="neu-subheading text-sm">Liquidity Score</div>
              <div className="text-3xl font-bold neu-text-primary">78.4</div>
              <div className="neu-badge success mt-2">High liquidity</div>
            </div>
          </div>
        </section>

        {/* File Analysis & DNA System */}
        <section className="mb-8">
          <h2 className="text-xl font-bold neu-heading mb-4">File DNA Analysis</h2>
          <div className="neu-grid neu-grid-2">
            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Recent File Scans</h3>
              <div className="space-y-3">
                <div className="neu-card p-4 flex justify-between items-center">
                  <div>
                    <div className="font-semibold neu-text-primary">main.rs</div>
                    <div className="text-sm neu-text">SHA-256: 0x7f8c9d...3a2b1c</div>
                  </div>
                  <div className="neu-badge success">VERIFIED</div>
                </div>
                <div className="neu-card p-4 flex justify-between items-center">
                  <div>
                    <div className="font-semibold neu-text-primary">index.html</div>
                    <div className="text-sm neu-text">SHA-256: 0x4a5b6c...1d2e3f</div>
                  </div>
                  <div className="neu-badge success">VERIFIED</div>
                </div>
                <div className="neu-card p-4 flex justify-between items-center">
                  <div>
                    <div className="font-semibold neu-text-primary">Cargo.toml</div>
                    <div className="text-sm neu-text">SHA-256: 0x8a9b0c...4d5e6f</div>
                  </div>
                  <div className="neu-badge warning">PENDING</div>
                </div>
              </div>
              <button className="neu-button primary w-full mt-4">
                Scan All Files
              </button>
            </div>

            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Merkle Tree Verification</h3>
              <div className="neu-card p-4 mb-4">
                <div className="font-mono text-sm neu-text">
                  <div className="neu-text-primary font-bold">ROOT: 0x7f8c9d...3a2b1c</div>
                  <div className="ml-4">├── 0x4a5b6c...1d2e3f</div>
                  <div className="ml-8">├── 0x8a9b0c...4d5e6f (leaf: main.rs)</div>
                  <div className="ml-8">└── 0x2a3b4c...7d8e9f (leaf: index.html)</div>
                  <div className="ml-4">└── 0x5a6b7c...0a1b2c</div>
                  <div className="ml-8">├── 0x1a2b3c...5d6e7f (leaf: Cargo.toml)</div>
                  <div className="ml-8">└── 0x9a0b1c...3d4e5f (leaf: package.json)</div>
                </div>
              </div>
              <div className="neu-grid neu-grid-2 gap-4">
                <div className="neu-stat-card p-4">
                  <div className="neu-subheading text-xs">Tree Depth</div>
                  <div className="text-xl font-bold neu-text-primary">2</div>
                </div>
                <div className="neu-stat-card p-4">
                  <div className="neu-subheading text-xs">Leaf Nodes</div>
                  <div className="text-xl font-bold neu-text-primary">4</div>
                </div>
              </div>
              <button className="neu-button w-full mt-4">
                Generate New Tree
              </button>
            </div>
          </div>
        </section>

        {/* Agent Work & Documentation */}
        <section className="mb-8">
          <h2 className="text-xl font-bold neu-heading mb-4">Agent Work Tracking</h2>
          <div className="neu-grid neu-grid-3">
            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Active Agents</h3>
              <div className="space-y-3">
                <div className="neu-card p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold neu-text-primary">LLM Analyzer</span>
                    <span className="neu-badge success">ACTIVE</span>
                  </div>
                  <div className="neu-progress-bar">
                    <div className="neu-progress-fill" style={{ width: '67%' }}></div>
                  </div>
                  <div className="text-xs neu-text mt-1">67% complete</div>
                </div>
                <div className="neu-card p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold neu-text-primary">File Scanner</span>
                    <span className="neu-badge success">ACTIVE</span>
                  </div>
                  <div className="neu-progress-bar">
                    <div className="neu-progress-fill" style={{ width: '89%' }}></div>
                  </div>
                  <div className="text-xs neu-text mt-1">89% complete</div>
                </div>
                <div className="neu-card p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold neu-text-primary">Documentation</span>
                    <span className="neu-badge warning">IDLE</span>
                  </div>
                  <div className="neu-progress-bar">
                    <div className="neu-progress-fill" style={{ width: '23%' }}></div>
                  </div>
                  <div className="text-xs neu-text mt-1">23% complete</div>
                </div>
              </div>
            </div>

            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Work Documentation</h3>
              <div className="space-y-3">
                <div className="neu-card p-3">
                  <div className="font-semibold neu-text-primary mb-1">Code Analysis Report</div>
                  <div className="text-sm neu-text">Generated comprehensive analysis of main.rs</div>
                  <div className="flex gap-2 mt-2">
                    <span className="neu-badge success">COMPLETED</span>
                    <span className="text-xs neu-text">2 hours ago</span>
                  </div>
                </div>
                <div className="neu-card p-3">
                  <div className="font-semibold neu-text-primary mb-1">Security Audit</div>
                  <div className="text-sm neu-text">Security vulnerability assessment complete</div>
                  <div className="flex gap-2 mt-2">
                    <span className="neu-badge success">COMPLETED</span>
                    <span className="text-xs neu-text">5 hours ago</span>
                  </div>
                </div>
                <div className="neu-card p-3">
                  <div className="font-semibold neu-text-primary mb-1">Performance Optimization</div>
                  <div className="text-sm neu-text">System optimization recommendations</div>
                  <div className="flex gap-2 mt-2">
                    <span className="neu-badge warning">IN PROGRESS</span>
                    <span className="text-xs neu-text">1 day ago</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Billing Summary</h3>
              <div className="space-y-4">
                <div className="neu-card p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="neu-text">Current Period</span>
                    <span className="font-semibold neu-text-primary">$1,234.56</span>
                  </div>
                  <div className="neu-progress-bar">
                    <div className="neu-progress-fill" style={{ width: '45%' }}></div>
                  </div>
                  <div className="text-xs neu-text mt-1">45% of monthly budget</div>
                </div>
                <div className="neu-grid neu-grid-2 gap-3">
                  <div className="neu-stat-card p-3">
                    <div className="neu-subheading text-xs">Hours Billed</div>
                    <div className="text-lg font-bold neu-text-primary">127.5</div>
                  </div>
                  <div className="neu-stat-card p-3">
                    <div className="neu-subheading text-xs">Avg Rate</div>
                    <div className="text-lg font-bold neu-text-primary">$9.68/hr</div>
                  </div>
                </div>
                <button className="neu-button primary w-full">
                  View Full Invoice
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* LLM Appraisal & Pricing */}
        <section className="mb-8">
          <h2 className="text-xl font-bold neu-heading mb-4">LLM Appraisal & Price Discovery</h2>
          <div className="neu-grid neu-grid-2">
            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Recent Appraisals</h3>
              <div className="space-y-3">
                <div className="neu-card p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-semibold neu-text-primary">main.rs</div>
                      <div className="text-sm neu-text">Overall Score: 0.87</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold neu-text-primary">$12,450</div>
                      <div className="text-xs neu-text">Estimated Value</div>
                    </div>
                  </div>
                  <div className="neu-grid neu-grid-4 gap-2 mt-3">
                    <div className="text-center">
                      <div className="text-xs neu-text">Quality</div>
                      <div className="font-semibold neu-text-primary">0.92</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs neu-text">Market</div>
                      <div className="font-semibold neu-text-primary">0.85</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs neu-text">Technical</div>
                      <div className="font-semibold neu-text-primary">0.88</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs neu-text">Usage</div>
                      <div className="font-semibold neu-text-primary">0.82</div>
                    </div>
                  </div>
                </div>
                <div className="neu-card p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-semibold neu-text-primary">index.html</div>
                      <div className="text-sm neu-text">Overall Score: 0.78</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold neu-text-primary">$8,320</div>
                      <div className="text-xs neu-text">Estimated Value</div>
                    </div>
                  </div>
                  <div className="neu-grid neu-grid-4 gap-2 mt-3">
                    <div className="text-center">
                      <div className="text-xs neu-text">Quality</div>
                      <div className="font-semibold neu-text-primary">0.75</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs neu-text">Market</div>
                      <div className="font-semibold neu-text-primary">0.82</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs neu-text">Technical</div>
                      <div className="font-semibold neu-text-primary">0.76</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs neu-text">Usage</div>
                      <div className="font-semibold neu-text-primary">0.79</div>
                    </div>
                  </div>
                </div>
              </div>
              <button className="neu-button primary w-full mt-4">
                Run New Appraisal
              </button>
            </div>

            <div className="neu-card p-6">
              <h3 className="neu-heading mb-4">Liquidity & Price Discovery</h3>
              <div className="space-y-4">
                <div className="neu-card p-4">
                  <div className="neu-subheading mb-2">Current Market Prices</div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="neu-text">Code Assets</span>
                      <span className="font-semibold neu-text-primary">$1,234.56 avg</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="neu-text">Documentation</span>
                      <span className="font-semibold neu-text-primary">$456.78 avg</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="neu-text">Media Assets</span>
                      <span className="font-semibold neu-text-primary">$789.12 avg</span>
                    </div>
                  </div>
                </div>
                <div className="neu-card p-4">
                  <div className="neu-subheading mb-2">Liquidity Metrics</div>
                  <div className="neu-grid neu-grid-2 gap-3">
                    <div className="neu-stat-card p-3">
                      <div className="neu-subheading text-xs">Volume (24h)</div>
                      <div className="text-lg font-bold neu-text-primary">$45.6K</div>
                    </div>
                    <div className="neu-stat-card p-3">
                      <div className="neu-subheading text-xs">Market Depth</div>
                      <div className="text-lg font-bold neu-text-primary">$123.4K</div>
                    </div>
                    <div className="neu-stat-card p-3">
                      <div className="neu-subheading text-xs">Spread</div>
                      <div className="text-lg font-bold neu-text-primary">2.3%</div>
                    </div>
                    <div className="neu-stat-card p-3">
                      <div className="neu-subheading text-xs">Volatility</div>
                      <div className="text-lg font-bold neu-text-primary">15.3%</div>
                    </div>
                  </div>
                </div>
                <button className="neu-button primary w-full">
                  View Liquidity Pool
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Historical Data & Analytics */}
        <section className="mb-8">
          <h2 className="text-xl font-bold neu-heading mb-4">Historical Data Collection</h2>
          <div className="neu-card p-6">
            <div className="neu-grid neu-grid-4 gap-4 mb-6">
              <div className="neu-stat-card p-4">
                <div className="neu-subheading text-xs">Total Records</div>
                <div className="text-2xl font-bold neu-text-primary">1.2M</div>
              </div>
              <div className="neu-stat-card p-4">
                <div className="neu-subheading text-xs">Data Points/Day</div>
                <div className="text-2xl font-bold neu-text-primary">45.6K</div>
              </div>
              <div className="neu-stat-card p-4">
                <div className="neu-subheading text-xs">Storage Used</div>
                <div className="text-2xl font-bold neu-text-primary">2.4 TB</div>
              </div>
              <div className="neu-stat-card p-4">
                <div className="neu-subheading text-xs">Retention</div>
                <div className="text-2xl font-bold neu-text-primary">7 years</div>
              </div>
            </div>
            <div className="neu-grid neu-grid-3 gap-4">
              <div className="neu-card p-4">
                <h4 className="neu-heading mb-3">File Access History</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">Today</span>
                    <span className="neu-text-primary">234 accesses</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">This Week</span>
                    <span className="neu-text-primary">1,567 accesses</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">This Month</span>
                    <span className="neu-text-primary">6,789 accesses</span>
                  </div>
                </div>
              </div>
              <div className="neu-card p-4">
                <h4 className="neu-heading mb-3">Valuation History</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">30 Days Ago</span>
                    <span className="neu-text-primary">$2.1M</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">7 Days Ago</span>
                    <span className="neu-text-primary">$2.3M</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">Today</span>
                    <span className="neu-text-primary">$2.4M</span>
                  </div>
                </div>
              </div>
              <div className="neu-card p-4">
                <h4 className="neu-heading mb-3">Agent Performance</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">Tasks Completed</span>
                    <span className="neu-text-primary">12,345</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">Avg Duration</span>
                    <span className="neu-text-primary">2.3 min</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="neu-text">Success Rate</span>
                    <span className="neu-text-primary">98.7%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}