import { NextRequest, NextResponse } from 'next/server';
import {
  deployArtifactToCloud,
  deployInferencePipeline,
  createDeploymentManifest,
  predefinedPipelines,
  deployPredefinedPipelines
} from '@/lib/cloud-deploy';

/**
 * Deployment Management API
 * Deploy inference artifacts and pipelines to cloud storage
 */

export const runtime = 'edge';
export const maxDuration = 60;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, artifact, pipeline, pipelineKey } = body;

    switch (action) {
      case 'deploy-artifact':
        if (!artifact) {
          return NextResponse.json(
            { error: 'Artifact is required for deploy-artifact action' },
            { status: 400 }
          );
        }
        const artifactResult = await deployArtifactToCloud(artifact);
        return NextResponse.json({ success: true, deployment: artifactResult });

      case 'deploy-pipeline':
        if (!pipeline) {
          return NextResponse.json(
            { error: 'Pipeline is required for deploy-pipeline action' },
            { status: 400 }
          );
        }
        const pipelineResult = await deployInferencePipeline(pipeline);
        return NextResponse.json({ success: true, deployment: pipelineResult });

      case 'deploy-predefined':
        if (!pipelineKey || !predefinedPipelines[pipelineKey]) {
          return NextResponse.json(
            { error: `Invalid pipeline key. Available: ${Object.keys(predefinedPipelines).join(', ')}` },
            { status: 400 }
          );
        }
        const predefinedPipeline = predefinedPipelines[pipelineKey];
        const predefinedResult = await deployInferencePipeline(predefinedPipeline);
        return NextResponse.json({ success: true, deployment: predefinedResult });

      case 'deploy-all-pipelines':
        const allPipelinesResult = await deployPredefinedPipelines();
        return NextResponse.json({ success: true, deployment: allPipelinesResult });

      case 'create-manifest':
        if (!body.artifacts || !Array.isArray(body.artifacts)) {
          return NextResponse.json(
            { error: 'Artifacts array is required for create-manifest action' },
            { status: 400 }
          );
        }
        const manifestCid = await createDeploymentManifest(body.artifacts);
        return NextResponse.json({ 
          success: true, 
          manifest: {
            cid: manifestCid,
            gatewayUrl: `https://gateway.pinata.cloud/ipfs/${manifestCid}`
          }
        });

      default:
        return NextResponse.json(
          { error: `Invalid action: ${action}. Available: deploy-artifact, deploy-pipeline, deploy-predefined, deploy-all-pipelines, create-manifest` },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('Deployment error:', error);
    return NextResponse.json(
      { error: `Deployment failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action');

    if (action === 'list-pipelines') {
      return NextResponse.json({ 
        pipelines: Object.keys(predefinedPipelines),
        details: predefinedPipelines
      });
    }

    if (action === 'status') {
      return NextResponse.json({ 
        status: 'operational',
        service: 'deployment',
        capabilities: {
          canDeployArtifacts: true,
          canDeployPipelines: true,
          predefinedPipelines: Object.keys(predefinedPipelines),
          supportsManifests: true
        },
        timestamp: new Date().toISOString()
      });
    }

    return NextResponse.json(
      { error: 'Invalid action. Available: list-pipelines, status' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: `Status check failed: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}