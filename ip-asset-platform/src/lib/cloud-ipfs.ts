/**
 * Cloud IPFS Service
 * Provides integration with Pinata for IPFS pinning and management
 */

interface PinataResponse {
  IpfsHash: string;
  PinSize: number;
  Timestamp: string;
}

interface PinataMetadata {
  name: string;
  keyvalues?: Record<string, string>;
}

const PINATA_API_URL = 'https://api.pinata.cloud';

/**
 * Pin JSON metadata to Pinata
 */
export async function pinJSONToPinata(
  json: any,
  metadata?: PinataMetadata
): Promise<string> {
  const apiKey = process.env.PINATA_API_KEY;
  const secretKey = process.env.PINATA_SECRET_KEY;

  if (!apiKey || !secretKey) {
    throw new Error('PINATA_API_KEY and PINATA_SECRET_KEY environment variables must be set');
  }

  try {
    const response = await fetch(`${PINATA_API_URL}/pinning/pinJSONToIPFS`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'pinata_api_key': apiKey,
        'pinata_secret_api_key': secretKey,
      },
      body: JSON.stringify({
        pinataContent: json,
        pinataMetadata: metadata || {
          name: 'IP Asset Metadata'
        }
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Pinata API error: ${response.status} - ${error}`);
    }

    const data: PinataResponse = await response.json();
    return data.IpfsHash;
  } catch (error) {
    console.error('Error pinning to Pinata:', error);
    throw new Error(`Failed to pin to Pinata: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Pin file to Pinata
 */
export async function pinFileToPinata(
  file: Buffer,
  fileName: string,
  metadata?: PinataMetadata
): Promise<string> {
  const apiKey = process.env.PINATA_API_KEY;
  const secretKey = process.env.PINATA_SECRET_KEY;

  if (!apiKey || !secretKey) {
    throw new Error('PINATA_API_KEY and PINATA_SECRET_KEY environment variables must be set');
  }

  try {
    const formData = new FormData();
    const uint8Array = new Uint8Array(file);
    const blob = new Blob([uint8Array], { type: 'application/octet-stream' });
    formData.append('file', blob, fileName);
    
    if (metadata) {
      formData.append('pinataMetadata', JSON.stringify(metadata));
    }

    const response = await fetch(`${PINATA_API_URL}/pinning/pinFileToIPFS`, {
      method: 'POST',
      headers: {
        'pinata_api_key': apiKey,
        'pinata_secret_api_key': secretKey,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Pinata API error: ${response.status} - ${error}`);
    }

    const data: PinataResponse = await response.json();
    return data.IpfsHash;
  } catch (error) {
    console.error('Error pinning file to Pinata:', error);
    throw new Error(`Failed to pin file to Pinata: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get IPFS gateway URL from Pinata
 */
export function getPinataGatewayURL(cid: string): string {
  const gateway = process.env.PINATA_GATEWAY || 'https://gateway.pinata.cloud/ipfs';
  return `${gateway}/${cid}`;
}

/**
 * Create File DNA Passport using Pinata
 */
export async function createFileDNAPassportWithPinata(
  filePath: string,
  fileMetadata: any,
  appraisal: any
): Promise<{
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

    const ipfsCid = await pinJSONToPinata(passport, {
      name: `File DNA Passport: ${filePath}`,
      keyvalues: {
        type: 'FILE_DNA_PASSPORT',
        timestamp: new Date().toISOString(),
        filePath: filePath
      }
    });

    // Create passport ID from CID
    const crypto = require('crypto');
    const passportId = crypto.createHash('sha256').update(ipfsCid).digest('hex');

    return {
      passportId,
      ipfsCid,
      ipfsUrl: getPinataGatewayURL(ipfsCid),
      timestamp: passport.timestamp
    };
  } catch (error) {
    console.error('Error creating File DNA Passport with Pinata:', error);
    throw new Error(`Failed to create File DNA Passport: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Get Pinata service status
 */
export async function getPinataStatus(): Promise<{
  available: boolean;
  gateway: string;
}> {
  const apiKey = process.env.PINATA_API_KEY;
  const secretKey = process.env.PINATA_SECRET_KEY;
  const gateway = process.env.PINATA_GATEWAY || 'https://gateway.pinata.cloud/ipfs';

  return {
    available: !!(apiKey && secretKey),
    gateway
  };
}