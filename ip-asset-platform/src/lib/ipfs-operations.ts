import { createHash } from 'crypto';

interface IPFSAddResult {
  Name: string;
  Hash: string;
  Size: string;
}

interface IPFSPinResult {
  Pins: string[];
  Status: string;
}

interface IPFSGatewayResult {
  path: string;
}

/**
 * IPFS Operations Utility
 * Provides real integration with IPFS for decentralized file storage
 */

const IPFS_API_URL = process.env.IPFS_API_URL || 'http://localhost:5001/api/v0';
const IPFS_GATEWAY_URL = process.env.IPFS_GATEWAY_URL || 'https://ipfs.io/ipfs';

/**
 * Add a file to IPFS
 */
export async function addToIPFS(content: string | Buffer): Promise<IPFSAddResult> {
  try {
    const formData = new FormData();
    let blob: Blob;
    
    if (content instanceof Buffer) {
      const uint8Array = new Uint8Array(content);
      blob = new Blob([uint8Array]);
    } else if (typeof content === 'string') {
      blob = new Blob([content], { type: 'text/plain' });
    } else {
      blob = new Blob([String(content)], { type: 'text/plain' });
    }
    
    formData.append('file', blob, 'file');

    const response = await fetch(`${IPFS_API_URL}/add`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`IPFS add failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error adding to IPFS:', error);
    throw new Error(`Failed to add to IPFS: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Add JSON metadata to IPFS
 */
export async function addMetadataToIPFS(metadata: any): Promise<string> {
  try {
    const metadataString = JSON.stringify(metadata, null, 2);
    const result = await addToIPFS(metadataString);
    return result.Hash;
  } catch (error) {
    console.error('Error adding metadata to IPFS:', error);
    throw new Error(`Failed to add metadata to IPFS: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Pin a CID to ensure it's not garbage collected
 */
export async function pinToIPFS(cid: string): Promise<IPFSPinResult> {
  try {
    const response = await fetch(`${IPFS_API_URL}/pin/add?arg=${cid}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`IPFS pin failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error pinning to IPFS:', error);
    throw new Error(`Failed to pin to IPFS: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get content from IPFS by CID
 */
export async function getFromIPFS(cid: string): Promise<string> {
  try {
    const response = await fetch(`${IPFS_GATEWAY_URL}/${cid}`);
    
    if (!response.ok) {
      throw new Error(`IPFS get failed: ${response.statusText}`);
    }

    const content = await response.text();
    return content;
  } catch (error) {
    console.error('Error getting from IPFS:', error);
    throw new Error(`Failed to get from IPFS: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get IPFS gateway URL for a CID
 */
export function getIPFSGatewayURL(cid: string): string {
  return `${IPFS_GATEWAY_URL}/${cid}`;
}

/**
 * Check if IPFS daemon is running
 */
export async function checkIPFSConnection(): Promise<boolean> {
  try {
    const response = await fetch(`${IPFS_API_URL}/version`, {
      method: 'POST',
    });

    return response.ok;
  } catch (error) {
    console.error('IPFS connection check failed:', error);
    return false;
  }
}

/**
 * Create File DNA Passport and anchor to IPFS
 */
export async function createFileDNAPassport(filePath: string, fileMetadata: any, appraisal: any): Promise<{
  passportId: string;
  ipfsCid: string;
  ipfsUrl: string;
  timestamp: string;
}> {
  try {
    const passport = {
      filePath,
      fileMetadata,
      appraisal,
      timestamp: new Date().toISOString(),
      version: '1.0',
      type: 'FILE_DNA_PASSPORT'
    };

    const ipfsCid = await addMetadataToIPFS(passport);
    await pinToIPFS(ipfsCid);

    return {
      passportId: createHash('sha256').update(ipfsCid).digest('hex'),
      ipfsCid,
      ipfsUrl: getIPFSGatewayURL(ipfsCid),
      timestamp: passport.timestamp
    };
  } catch (error) {
    console.error('Error creating File DNA Passport:', error);
    throw new Error(`Failed to create File DNA Passport: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Verify File DNA Passport from IPFS
 */
export async function verifyFileDNAPassport(ipfsCid: string): Promise<any> {
  try {
    const content = await getFromIPFS(ipfsCid);
    const passport = JSON.parse(content);
    
    // Verify passport structure
    if (!passport.type || passport.type !== 'FILE_DNA_PASSPORT') {
      throw new Error('Invalid passport type');
    }

    return passport;
  } catch (error) {
    console.error('Error verifying File DNA Passport:', error);
    throw new Error(`Failed to verify File DNA Passport: ${error instanceof Error ? error.message : String(error)}`);
  }
}