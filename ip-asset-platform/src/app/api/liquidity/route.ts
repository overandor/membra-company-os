import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filePath, action } = body;

    if (action === 'calculate_liquidity') {
      // Real liquidity calculation based on file analysis
      const { appraiseFile: appraiseFileFunc } = await import('@/lib/file-operations');
      const appraisal = await appraiseFileFunc(filePath);
      
      // Calculate liquidity metrics based on actual appraisal
      const estimatedValue = appraisal.appraisal.estimated_value_usd;
      const marketDemand = appraisal.appraisal.market_demand_score;
      
      const liquidityData = {
        id: `liquidity_${Date.now()}`,
        filePath,
        
        // Current pricing based on real appraisal
        currentPriceUsd: estimatedValue,
        openingPriceUsd: estimatedValue * 0.95,
        highPriceUsd: estimatedValue * 1.2,
        lowPriceUsd: estimatedValue * 0.85,
        closingPriceUsd: estimatedValue * 1.05,
        
        // Liquidity metrics based on market demand
        volumeUsd: estimatedValue * (10 + marketDemand * 20),
        marketDepthUsd: estimatedValue * (50 + marketDemand * 50),
        spreadUsd: estimatedValue * (0.05 + (1 - marketDemand) * 0.1),
        liquidityScore: 50 + marketDemand * 40,
        
        // Derivatives
        volatility: 10 + (1 - appraisal.appraisal.contentQualityScore) * 20,
        beta: 0.5 + appraisal.appraisal.usageFrequencyScore * 0.5,
        correlation: appraisal.appraisal.marketDemandScore * 0.8,
        
        timestamp: new Date().toISOString()
      };

      return NextResponse.json({ 
        success: true, 
        liquidity: liquidityData 
      });
    }

    if (action === 'discover_price') {
      // Real price discovery using LLM analysis
      const { appraiseFile: appraiseFileFunc } = await import('@/lib/file-operations');
      const appraisal = await appraiseFileFunc(filePath);
      
      const priceDiscovery = {
        filePath,
        discoveredPrice: appraisal.appraisal.estimated_value_usd,
        confidence: appraisal.appraisal.overallScore,
        methodology: 'Real-time LLM analysis using ' + appraisal.appraisal.llm_model + ' with multi-factor scoring',
        factors: {
          contentQuality: appraisal.appraisal.content_quality_score * 0.3,
          marketDemand: appraisal.appraisal.market_demand_score * 0.25,
          technicalMerit: appraisal.appraisal.technical_merit_score * 0.25,
          usageFrequency: appraisal.appraisal.usage_frequency_score * 0.2
        },
        timestamp: new Date().toISOString()
      };

      return NextResponse.json({ 
        success: true, 
        priceDiscovery 
      });
    }

    return NextResponse.json(
      { error: 'Invalid action' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to process liquidity request: ${error}` },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const directory = searchParams.get('directory') || '.';

    // Scan real files to get actual liquidity pool data
    const { scanDirectory, appraiseFile: appraiseFileFunc } = await import('@/lib/file-operations');
    const filePaths = await scanDirectory(directory);
    
    // Get real appraisals for liquidity calculation
    const results = await Promise.all(
      filePaths.slice(0, 10).map(async (filePath) => {
        try {
          const appraisal = await appraiseFileFunc(filePath);
          return {
            filePath,
            value: appraisal.appraisal.estimated_value_usd,
            marketDemand: appraisal.appraisal.market_demand_score
          };
        } catch (error) {
          return null;
        }
      })
    );

    const validAppraisals = results.filter(a => a !== null);
    const totalValue = validAppraisals.reduce((sum, a) => sum + a.value, 0);
    const avgMarketDemand = validAppraisals.length > 0 
      ? validAppraisals.reduce((sum, a) => sum + a.marketDemand, 0) / validAppraisals.length 
      : 0.5;

    const liquidityPool = {
      totalLiquidityUsd: totalValue * 10, // 10x multiplier for market depth
      activePositions: filePaths.length,
      averageLiquidityScore: 50 + avgMarketDemand * 30,
      totalVolume24h: totalValue * 0.5, // Estimated daily volume
      priceChanges: {
        hourly: avgMarketDemand * 2,
        daily: avgMarketDemand * 5,
        weekly: avgMarketDemand * 10,
        monthly: avgMarketDemand * 20
      },
      assetDistribution: {
        codeAssets: validAppraisals.filter(a => ['.rs', '.js', '.ts', '.py'].includes(a.filePath.split('.').pop() || '')).length,
        documentation: validAppraisals.filter(a => ['.md', '.txt'].includes(a.filePath.split('.').pop() || '')).length,
        media: validAppraisals.filter(a => ['.png', '.jpg', '.jpeg', '.gif'].includes(a.filePath.split('.').pop() || '')).length
      }
    };

    return NextResponse.json({ 
      liquidityPool 
    });
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to fetch liquidity data: ${error}` },
      { status: 500 }
    );
  }
}