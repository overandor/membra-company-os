import { NextRequest, NextResponse } from 'next/server';
import { 
  pinJSONToPinata, 
  pinFileToPinata, 
  getPinataGatewayURL, 
  getPinataStatus,
  createFileDNAPassportWithPinata 
} from '@/lib/cloud-ipfs';
import { computeFileDNAHash } from '@/lib/cloud-storage';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, content, filePath, fileMetadata, appraisal, cid } = body;

    // Check Pinata status
    const pinataStatus = await getPinataStatus();
    if (!pinataStatus.available) {
      return NextResponse.json(
        { error: 'Pinata service is not configured. Please set PINATA_API_KEY and PINATA_SECRET_KEY environment variables.' },
        { status: 503 }
      );
    }

    if (action === 'add_metadata') {
      // Add metadata to Pinata
      const cid = await pinJSONToPinata(content, {
        name: body.fileName || 'IP Asset Metadata',
        keyvalues: {
          type: 'METADATA',
          timestamp: new Date().toISOString()
        }
      });
      
      return NextResponse.json({ 
        success: true, 
        ipfs: {
          cid,
          gatewayUrl: getPinataGatewayURL(cid)
        }
      });
    }

    if (action === 'add_file') {
      // Add file to Pinata
      if (!content || !body.fileName) {
        return NextResponse.json(
          { error: 'File content and file name are required' },
          { status: 400 }
        );
      }

      const fileBuffer = Buffer.from(content);
      const cid = await pinFileToPinata(fileBuffer, body.fileName, {
        name: body.fileName,
        keyvalues: {
          type: 'FILE',
          timestamp: new Date().toISOString(),
          fileName: body.fileName
        }
      });
      
      return NextResponse.json({ 
        success: true, 
        ipfs: {
          cid,
          gatewayUrl: getPinataGatewayURL(cid),
          fileName: body.fileName,
          fileSize: fileBuffer.length
        }
      });
    }

    if (action === 'create_passport') {
      // Create File DNA Passport and anchor to Pinata
      if (!filePath) {
        return NextResponse.json(
          { error: 'File path is required for passport creation' },
          { status: 400 }
        );
      }

      // Create passport with Pinata
      const passport = await createFileDNAPassportWithPinata(filePath, fileMetadata || {}, appraisal || {});
      
      return NextResponse.json({ 
        success: true, 
        passport 
      });
    }

    return NextResponse.json(
      { error: 'Invalid action' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to process IPFS request: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action');
    const cid = searchParams.get('cid');
    
    if (action === 'check_connection') {
      const pinataStatus = await getPinataStatus();
      return NextResponse.json({ 
        connected: pinataStatus.available,
        gateway: pinataStatus.gateway
      });
    }

    if (action === 'gateway_url' && cid) {
      // Get gateway URL for CID
      return NextResponse.json({ 
        gatewayUrl: getPinataGatewayURL(cid) 
      });
    }

    return NextResponse.json(
      { error: 'Invalid action or missing parameters' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to process IPFS request: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}