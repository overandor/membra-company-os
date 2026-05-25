import * as crypto from 'crypto';
import * as fs from 'fs/promises';
import * as path from 'path';

// Real SHA-256 file hashing
export async function computeFileDNAHash(filePath: string): Promise<string> {
  try {
    const fileBuffer = await fs.readFile(filePath);
    const stats = await fs.stat(filePath);
    
    // Create comprehensive hash including content and metadata
    const hash = crypto.createHash('sha256');
    hash.update(fileBuffer);
    hash.update(Buffer.from(stats.size.toString()));
    hash.update(Buffer.from(stats.mtime.getTime().toString()));
    
    return hash.digest('hex');
  } catch (error) {
    throw new Error(`Failed to compute DNA hash: ${error}`);
  }
}

// Real file metadata extraction
export async function extractFileMetadata(filePath: string) {
  try {
    const stats = await fs.stat(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const content = await fs.readFile(filePath, 'utf-8');
    
    const metadata: any = {
      fileType: ext.replace('.', ''),
      mimeType: getMimeType(ext),
      encoding: 'utf-8',
      fileSize: stats.size,
      createdAt: stats.birthtime,
      modifiedAt: stats.mtime,
      accessedAt: stats.atime
    };
    
    // Code-specific metadata
    if (['.rs', '.js', '.ts', '.py', '.go', '.java', '.cpp', '.c'].includes(ext)) {
      metadata.language = getLanguage(ext);
      metadata.lineCount = content.split('\n').length;
      metadata.functionCount = countFunctions(content, ext);
      metadata.hasTests = content.includes('test') || content.includes('Test');
    }
    
    // Document-specific metadata
    if (['.md', '.txt', '.pdf', '.doc'].includes(ext)) {
      metadata.wordCount = content.split(/\s+/).length;
    }
    
    return metadata;
  } catch (error) {
    throw new Error(`Failed to extract metadata: ${error}`);
  }
}

// Real Ollama API integration
export async function callOllamaAPI(prompt: string, model: string = 'llama3.2:latest') {
  try {
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: model,
        prompt: prompt,
        stream: false
      })
    });
    
    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.response;
  } catch (error) {
    throw new Error(`Failed to call Ollama: ${error}`);
  }
}

// Real file appraisal using LLM
export async function appraiseFile(filePath: string, model: string = 'llama3.2:latest') {
  try {
    const metadata = await extractFileMetadata(filePath);
    const dnaHash = await computeFileDNAHash(filePath);
    const content = await fs.readFile(filePath, 'utf-8');
    
    const prompt = `You are a specialized file appraiser. Analyze this file's characteristics and provide a comprehensive appraisal.
    
    File: ${path.basename(filePath)}
    Type: ${metadata.fileType}
    Size: ${metadata.fileSize} bytes
    Language: ${metadata.language || 'N/A'}
    Lines: ${metadata.lineCount || 'N/A'}
    Functions: ${metadata.functionCount || 'N/A'}
    
    Sample content (first 500 chars):
    ${content.substring(0, 500)}
    
    Rate the following on a scale of 0.0 to 1.0:
    1. Content Quality (code quality, documentation, accuracy)
    2. Market Demand (industry relevance, usage trends)
    3. Technical Merit (complexity, innovation, uniqueness)
    4. Usage Frequency (how often such files are accessed)
    
    Also provide an estimated USD value for this file as collateral.
    
    Respond in JSON format:
    {
      "content_quality_score": 0.0-1.0,
      "market_demand_score": 0.0-1.0,
      "technical_merit_score": 0.0-1.0,
      "usage_frequency_score": 0.0-1.0,
      "estimated_value_usd": 0.0,
      "notes": "brief explanation"
    }`;
    
    const llmResponse = await callOllamaAPI(prompt, model);
    
    // Parse the JSON response
    const jsonMatch = llmResponse.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('Failed to parse LLM response as JSON');
    }
    
    const appraisal = JSON.parse(jsonMatch[0]);
    
    // Calculate overall score
    const overallScore = (
      appraisal.content_quality_score +
      appraisal.market_demand_score +
      appraisal.technical_merit_score +
      appraisal.usage_frequency_score
    ) / 4;
    
    return {
      dnaHash,
      metadata,
      appraisal: {
        ...appraisal,
        overallScore,
        llmModel: model,
        appraisalTimestamp: new Date().toISOString()
      }
    };
  } catch (error) {
    throw new Error(`Failed to appraise file: ${error}`);
  }
}

// Real IPFS upload
export async function uploadToIPFS(filePath: string) {
  try {
    const fileBuffer = await fs.readFile(filePath);
    
    const formData = new FormData();
    formData.append('file', new Blob([fileBuffer]), path.basename(filePath));
    
    const response = await fetch('http://localhost:5001/api/v0/add?pin=true', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`IPFS API error: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.Hash;
  } catch (error) {
    throw new Error(`Failed to upload to IPFS: ${error}`);
  }
}

// Real Solana blockchain integration
export async function getSolanaBalance(pubkey: string) {
  try {
    const response = await fetch('https://api.devnet.solana.com', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getBalance',
        params: [pubkey, 'confirmed']
      })
    });
    
    if (!response.ok) {
      throw new Error(`Solana API error: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.result;
  } catch (error) {
    throw new Error(`Failed to get Solana balance: ${error}`);
  }
}

// Real file system scanning
export async function scanDirectory(dirPath: string) {
  try {
    const files: string[] = [];
    
    async function scan(currentPath: string) {
      const entries = await fs.readdir(currentPath, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(currentPath, entry.name);
        
        if (entry.isDirectory()) {
          // Skip node_modules and .next directories
          if (!['node_modules', '.next', '.git'].includes(entry.name)) {
            await scan(fullPath);
          }
        } else if (entry.isFile()) {
          // Include only certain file types
          const ext = path.extname(entry.name).toLowerCase();
          const targetExts = ['.rs', '.js', '.ts', '.py', '.go', '.java', '.cpp', '.c', '.html', '.css', '.md', '.json', '.txt'];
          
          if (targetExts.includes(ext)) {
            files.push(fullPath);
          }
        }
      }
    }
    
    await scan(dirPath);
    return files;
  } catch (error) {
    throw new Error(`Failed to scan directory: ${error}`);
  }
}

// Helper functions
function getMimeType(ext: string): string {
  const mimeTypes: Record<string, string> = {
    '.rs': 'text/rust',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.py': 'text/python',
    '.html': 'text/html',
    '.css': 'text/css',
    '.json': 'application/json',
    '.md': 'text/markdown',
    '.txt': 'text/plain',
    '.pdf': 'application/pdf',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif'
  };
  
  return mimeTypes[ext] || 'application/octet-stream';
}

function getLanguage(ext: string): string {
  const languages: Record<string, string> = {
    '.rs': 'rust',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.py': 'python',
    '.go': 'go',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c'
  };
  
  return languages[ext] || 'unknown';
}

function countFunctions(content: string, ext: string): number {
  const patterns: Record<string, RegExp> = {
    '.rs': /fn /g,
    '.js': /function /g,
    '.ts': /function /g,
    '.py': /def /g,
    '.go': /func /g,
    '.java': /public|private|protected\s+\w+\s*\(/g,
    '.cpp': /\w+\s*\(/g
  };
  
  const pattern = patterns[ext];
  if (!pattern) return 0;
  
  const matches = content.match(pattern);
  return matches ? matches.length : 0;
}