import { NextRequest, NextResponse } from 'next/server';
import { scanDirectory, computeFileDNAHash, extractFileMetadata, appraiseFile } from '@/lib/file-operations';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const directory = searchParams.get('directory') || '.';
    
    // Real file system scanning
    const filePaths = await scanDirectory(directory);
    
    // Process files with real DNA hashing
    const files = await Promise.all(
      filePaths.slice(0, 20).map(async (filePath) => {
        try {
          const dnaHash = await computeFileDNAHash(filePath);
          const metadata = await extractFileMetadata(filePath);
          const stats = await import('fs').then(fs => fs.promises.stat(filePath));
          
          return {
            id: Buffer.from(filePath).toString('base64'),
            fileName: filePath.split('/').pop() || 'unknown',
            filePath,
            fileSize: (await stats).size,
            fileType: metadata.fileType,
            mimeType: metadata.mimeType,
            dnaHash,
            createdAt: metadata.createdAt,
            lastAccessedAt: metadata.accessedAt
          };
        } catch (error) {
          console.error(`Error processing file ${filePath}:`, error);
          return null;
        }
      })
    );
    
    // Filter out failed files
    const validFiles = files.filter(f => f !== null);
    
    return NextResponse.json({ files: validFiles });
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to scan files: ${error}` },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filePath } = body;

    // Real file analysis using actual file operations
    const dnaHash = await computeFileDNAHash(filePath);
    const metadata = await extractFileMetadata(filePath);
    
    // Real LLM appraisal
    let appraisal;
    try {
      appraisal = await appraiseFile(filePath);
    } catch (error) {
      console.error('LLM appraisal failed, using fallback:', error);
      // Fallback to basic appraisal if LLM fails
      appraisal = {
        dnaHash,
        metadata,
        appraisal: {
          contentQualityScore: 0.5,
          marketDemandScore: 0.5,
          technicalMeritScore: 0.5,
          usageFrequencyScore: 0.5,
          overallScore: 0.5,
          estimatedValueUsd: metadata.fileSize * 0.01,
          llmModel: 'fallback',
          appraisalTimestamp: new Date().toISOString()
        }
      };
    }

    return NextResponse.json({ 
      success: true, 
      analysis: {
        dnaHash,
        contentHash: dnaHash,
        metadataHash: Buffer.from(JSON.stringify(metadata)).toString('hex'),
        fileType: metadata.fileType,
        fileSize: metadata.fileSize,
        appraisal: appraisal.appraisal
      }
    });
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to analyze file: ${error}` },
      { status: 500 }
    );
  }
}