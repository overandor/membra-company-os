import { NextRequest, NextResponse } from 'next/server';
import {
  getSolanaClusterInfo,
  getAccountInfo,
  getBalance,
  getRecentBlockhash,
  createFileDNATransaction,
  verifyFileDNAOnChain,
  getTransaction,
  checkSolanaConnection,
  createFileProvenanceRecord
} from '@/lib/solana-operations';
import { computeFileDNAHash, extractFileMetadata } from '@/lib/file-operations';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, publicKey, fileDNAHash, filePath, metadata, appraisal, ipfsCid } = body;

    // Check Solana connection
    const isConnected = await checkSolanaConnection();
    if (!isConnected) {
      return NextResponse.json(
        { error: 'Cannot connect to Solana network. Please check your RPC configuration.' },
        { status: 503 }
      );
    }

    if (action === 'create_dna_transaction') {
      // Create File DNA transaction on Solana
      if (!fileDNAHash || !filePath) {
        return NextResponse.json(
          { error: 'File DNA hash and file path are required' },
          { status: 400 }
        );
      }

      const transaction = await createFileDNATransaction(fileDNAHash, filePath, metadata || {});
      
      return NextResponse.json({ 
        success: true, 
        solana: {
          signature: transaction.signature,
          blockhash: transaction.blockhash,
          timestamp: new Date().toISOString()
        }
      });
    }

    if (action === 'create_provenance_record') {
      // Create comprehensive file provenance record
      if (!filePath) {
        return NextResponse.json(
          { error: 'File path is required for provenance record' },
          { status: 400 }
        );
      }

      // Get file DNA and metadata
      const dnaHash = await computeFileDNAHash(filePath);
      const fileMetadata = await extractFileMetadata(filePath);
      
      // Create provenance record
      const provenance = await createFileProvenanceRecord(
        filePath,
        dnaHash,
        ipfsCid || '',
        fileMetadata,
        appraisal || {}
      );
      
      return NextResponse.json({ 
        success: true, 
        provenance 
      });
    }

    return NextResponse.json(
      { error: 'Invalid action' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to process Solana request: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get('action');
    const publicKey = searchParams.get('publicKey');
    const signature = searchParams.get('signature');

    // Check Solana connection
    const isConnected = await checkSolanaConnection();

    if (action === 'check_connection') {
      return NextResponse.json({ 
        connected: isConnected,
        network: process.env.SOLANA_RPC_URL || 'https://api.devnet.solana.com'
      });
    }

    if (action === 'get_cluster_info') {
      const clusterInfo = await getSolanaClusterInfo();
      return NextResponse.json({ 
        success: true, 
        clusterInfo 
      });
    }

    if (action === 'get_account_info' && publicKey) {
      const accountInfo = await getAccountInfo(publicKey);
      return NextResponse.json({ 
        success: true, 
        accountInfo 
      });
    }

    if (action === 'get_balance' && publicKey) {
      const balance = await getBalance(publicKey);
      return NextResponse.json({ 
        success: true, 
        balance 
      });
    }

    if (action === 'get_recent_blockhash') {
      const blockhash = await getRecentBlockhash();
      return NextResponse.json({ 
        success: true, 
        blockhash 
      });
    }

    if (action === 'verify_dna' && signature) {
      // Verify file DNA on Solana blockchain
      const verification = await verifyFileDNAOnChain(signature);
      return NextResponse.json({ 
        success: true, 
        verification 
      });
    }

    if (action === 'get_transaction' && signature) {
      // Get transaction details
      const transaction = await getTransaction(signature);
      return NextResponse.json({ 
        success: true, 
        transaction 
      });
    }

    return NextResponse.json(
      { error: 'Invalid action or missing parameters' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: `Failed to process Solana request: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    );
  }
}