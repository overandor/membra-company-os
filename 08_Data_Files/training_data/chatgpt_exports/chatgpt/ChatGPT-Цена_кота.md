# Цена кота

#### You:
Сколько вот такой кот стоит, если его продать взять и в другие руки передать?

#### You:
// drift_tiny_real_bot.ts
//
// npm i @drift-labs/sdk @coral-xyz/anchor @solana/web3.js dotenv
//
// .env example:
// ANCHOR_WALLET=/absolute/path/to/id.json
// ANCHOR_PROVIDER_URL=https://your-dedicated-solana-rpc
// DRIFT_ENV=mainnet-beta
// DRY_RUN=true
// MARKET_SYMBOL=SOL
// ORDER_SIZE_BASE=0.02
// LOOP_MS=15000
// FAST_EMA=9
// SLOW_EMA=21
// RSI_PERIOD=14
// RSI_LONG_MAX=65
// RSI_SHORT_MIN=35
// TREND_MIN=0.0005
// TP_PCT=0.008
// SL_PCT=0.005
// MAX_HISTORY=300
// MAX_DAILY_LOSS_USD=2
// MAX_TRADES_PER_DAY=8
// REDUCE_ON_REVERSE=true
// USE_POST_ONLY=false
//
// Notes:
// - Start with DRY_RUN=true
// - Create and fund your Drift user account before live trading
// - This is intentionally a one-position directional bot for tiny balances

import 'dotenv/config';
import * as anchor from '@coral-xyz/anchor';
import {
  BulkAccountLoader,
  DriftClient,
  User,
  Wallet,
  initialize,
  PerpMarkets,
  PositionDirection,
  PRICE_PRECISION,
  BASE_PRECISION,
  QUOTE_PRECISION,
  convertToNumber,
  getMarketOrderParams,
  getLimitOrderParams,
  OrderType,
  PostOnlyParams,
} from '@drift-labs/sdk';

type BotSide = 'flat' | 'long' | 'short';

type StatusSnapshot = {
  ts: string;
  price: number;
  emaFast: number;
  emaSlow: number;
  rsi: number;
  signal: 'long' | 'short' | null;
  side: BotSide;
  size: number;
  entry: number | null;
  pnlPct: number;
  realizedTodayUsd: number;
  tradesToday: number;
};

const CFG = {
  env: (process.env.DRIFT_ENV || 'mainnet-beta') as 'devnet' | 'mainnet-beta',
  dryRun: String(process.env.DRY_RUN || 'true').toLowerCase() === 'true',
  marketSymbol: (process.env.MARKET_SYMBOL || 'SOL').toUpperCase(),
  orderSizeBase: Number(process.env.ORDER_SIZE_BASE || '0.02'),
  loopMs: Number(process.env.LOOP_MS || '15000'),
  fastEma: Number(process.env.FAST_EMA || '9'),
  slowEma: Number(process.env.SLOW_EMA || '21'),
  rsiPeriod: Number(process.env.RSI_PERIOD || '14'),
  rsiLongMax: Number(process.env.RSI_LONG_MAX || '65'),
  rsiShortMin: Number(process.env.RSI_SHORT_MIN || '35'),
  trendMin: Number(process.env.TREND_MIN || '0.0005'),
  tpPct: Number(process.env.TP_PCT || '0.008'),
  slPct: Number(process.env.SL_PCT || '0.005'),
  maxHistory: Number(process.env.MAX_HISTORY || '300'),
  maxDailyLossUsd: Number(process.env.MAX_DAILY_LOSS_USD || '2'),
  maxTradesPerDay: Number(process.env.MAX_TRADES_PER_DAY || '8'),
  reduceOnReverse: String(process.env.REDUCE_ON_REVERSE || 'true').toLowerCase() === 'true',
  usePostOnly: String(process.env.USE_POST_ONLY || 'false').toLowerCase() === 'true',
};

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function nowIso(): string {
  return new Date().toISOString();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function floorTo(x: number, decimals: number): number {
  const p = Math.pow(10, decimals);
  return Math.floor(x * p) / p;
}

function ema(values: number[], span: number): number {
  if (values.length === 0) return 0;
  const alpha = 2 / (span + 1);
  let out = values[0];
  for (let i = 1; i < values.length; i++) {
    out = alpha * values[i] + (1 - alpha) * out;
  }
  return out;
}

function computeRsi(values: number[], period: number): number {
  if (values.length < period + 1) return 50;

  let gains = 0;
  let losses = 0;
  const start = values.length - period;

  for (let i = start; i < values.length; i++) {
    const d = values[i] - values[i - 1];
    if (d > 0) gains += d;
    else losses += -d;
  }

  const avgGain = gains / period;
  const avgLoss = losses / period;

  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function generateSignal(
  mid: number,
  emaFast: number,
  emaSlow: number,
  rsi: number
): 'long' | 'short' | null {
  const trendStrength = Math.abs(emaFast - emaSlow) / mid;

  if (trendStrength < CFG.trendMin) return null;

  if (emaFast > emaSlow && rsi < CFG.rsiLongMax) return 'long';
  if (emaFast < emaSlow && rsi > CFG.rsiShortMin) return 'short';

  return null;
}

function currentUtcDayKey(): string {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(
    d.getUTCDate()
  ).padStart(2, '0')}`;
}

class DailyRiskLimiter {
  private dayKey: string = currentUtcDayKey();
  private realizedTodayUsd = 0;
  private tradesToday = 0;
  private blocked = false;

  syncDay(): void {
    const k = currentUtcDayKey();
    if (k !== this.dayKey) {
      this.dayKey = k;
      this.realizedTodayUsd = 0;
      this.tradesToday = 0;
      this.blocked = false;
    }
  }

  addRealizedPnl(deltaUsd: number): void {
    this.syncDay();
    this.realizedTodayUsd += deltaUsd;
    if (this.realizedTodayUsd <= -Math.abs(CFG.maxDailyLossUsd)) {
      this.blocked = true;
    }
  }

  addTrade(): void {
    this.syncDay();
    this.tradesToday += 1;
    if (this.tradesToday >= CFG.maxTradesPerDay) {
      this.blocked = true;
    }
  }

  canTrade(): boolean {
    this.syncDay();
    return !this.blocked;
  }

  snapshot() {
    this.syncDay();
    return {
      realizedTodayUsd: this.realizedTodayUsd,
      tradesToday: this.tradesToday,
      blocked: this.blocked,
    };
  }
}

class TinyDriftRealBot {
  private provider!: anchor.AnchorProvider;
  private driftClient!: DriftClient;
  private user!: User;
  private marketIndex!: number;
  private history: number[] = [];
  private running = true;
  private risk = new DailyRiskLimiter();

  async init(): Promise<void> {
    const rpc = required('ANCHOR_PROVIDER_URL');
    required('ANCHOR_WALLET');

    const sdkConfig = initialize({ env: CFG.env });

    this.provider = anchor.AnchorProvider.local(rpc, {
      commitment: 'confirmed',
      preflightCommitment: 'confirmed',
      skipPreflight: false,
    });

    const bulkAccountLoader = new BulkAccountLoader(
      this.provider.connection,
      'confirmed',
      1000
    );

    this.driftClient = new DriftClient({
      connection: this.provider.connection,
      wallet: this.provider.wallet as Wallet,
      programID: sdkConfig.DRIFT_PROGRAM_ID,
      accountSubscription: {
        type: 'polling',
        accountLoader: bulkAccountLoader,
      },
    });

    await this.driftClient.subscribe();

    this.user = new User({
      driftClient: this.driftClient,
      userAccountPublicKey: await this.driftClient.getUserAccountPublicKey(),
      accountSubscription: {
        type: 'polling',
        accountLoader: bulkAccountLoader,
      },
    });

    const exists = await this.user.exists();
    if (!exists) {
      throw new Error(
        'Drift user account not found. Create and fund it first in Drift UI or a setup script.'
      );
    }

    await this.user.subscribe();

    const market = PerpMarkets[CFG.env].find(
      (m: any) => String(m.baseAssetSymbol).toUpperCase() === CFG.marketSymbol
    );

    if (!market) {
      throw new Error(`Market ${CFG.marketSymbol}-PERP not found in ${CFG.env}`);
    }

    this.marketIndex = market.marketIndex;

    console.log(`[${nowIso()}] init ok env=${CFG.env} market=${CFG.marketSymbol}-PERP idx=${this.marketIndex} dryRun=${CFG.dryRun}`);
  }

  private getOraclePrice(): number {
    const oracle = this.driftClient.getOracleDataForPerpMarket(this.marketIndex);
    return convertToNumber(oracle.price, PRICE_PRECISION);
  }

  private pushPrice(px: number): void {
    this.history.push(px);
    if (this.history.length > CFG.maxHistory) {
      this.history = this.history.slice(-CFG.maxHistory);
    }
  }

  private getPosition(): { side: BotSide; sizeBase: number } {
    const p = this.user.getPerpPosition(this.marketIndex);
    if (!p) return { side: 'flat', sizeBase: 0 };

    const base = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    if (Math.abs(base) < 1e-10) return { side: 'flat', sizeBase: 0 };

    return {
      side: base > 0 ? 'long' : 'short',
      sizeBase: Math.abs(base),
    };
  }

  private getApproxEntryPrice(): number | null {
    const p = this.user.getPerpPosition(this.marketIndex);
    if (!p) return null;

    const base = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    if (Math.abs(base) < 1e-10) return null;

    const qea: any = (p as any).quoteEntryAmount;
    if (!qea) return null;

    const quoteEntry = Math.abs(convertToNumber(qea, QUOTE_PRECISION));
    return quoteEntry / Math.abs(base);
  }

  private getUnrealizedPnlUsd(markPrice: number): number {
    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    if (pos.side === 'flat' || !entry) return 0;

    if (pos.side === 'long') {
      return (markPrice - entry) * pos.sizeBase;
    } else {
      return (entry - markPrice) * pos.sizeBase;
    }
  }

  private getPnlPct(markPrice: number): number {
    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    if (pos.side === 'flat' || !entry) return 0;

    if (pos.side === 'long') {
      return (markPrice - entry) / entry;
    } else {
      return (entry - markPrice) / entry;
    }
  }

  private async placeMarket(direction: PositionDirection, sizeBase: number, reduceOnly = false) {
    if (sizeBase <= 0) return null;

    if (CFG.dryRun) {
      console.log(
        `[${nowIso()}] DRY market ${direction === PositionDirection.LONG ? 'LONG' : 'SHORT'} size=${sizeBase} reduceOnly=${reduceOnly}`
      );
      return 'dry-run';
    }

    const tx = await this.driftClient.placePerpOrder(
      getMarketOrderParams({
        marketIndex: this.marketIndex,
        direction,
        baseAssetAmount: this.driftClient.convertToPerpPrecision(sizeBase),
        reduceOnly,
      })
    );

    console.log(`[${nowIso()}] sent market order tx=${tx}`);
    return tx;
  }

  private async placePostOnly(direction: PositionDirection, sizeBase: number, oraclePrice: number) {
    if (sizeBase <= 0) return null;

    const pxOffsetBps = 5;
    const limitPx =
      direction === PositionDirection.LONG
        ? oraclePrice * (1 - pxOffsetBps / 10000)
        : oraclePrice * (1 + pxOffsetBps / 10000);

    if (CFG.dryRun) {
      console.log(
        `[${nowIso()}] DRY post-only ${direction === PositionDirection.LONG ? 'LONG' : 'SHORT'} size=${sizeBase} px=${limitPx.toFixed(4)}`
      );
      return 'dry-run';
    }

    const tx = await this.driftClient.placePerpOrder(
      getLimitOrderParams({
        marketIndex: this.marketIndex,
        direction,
        baseAssetAmount: this.driftClient.convertToPerpPrecision(sizeBase),
        price: this.driftClient.convertToPricePrecision(limitPx),
        orderType: OrderType.LIMIT,
        postOnly: PostOnlyParams.MUST_POST_ONLY,
      })
    );

    console.log(`[${nowIso()}] sent post-only order tx=${tx}`);
    return tx;
  }

  private async enter(signal: 'long' | 'short', price: number): Promise<void> {
    const direction =
      signal === 'long' ? PositionDirection.LONG : PositionDirection.SHORT;

    if (CFG.usePostOnly) {
      await this.placePostOnly(direction, CFG.orderSizeBase, price);
    } else {
      await this.placeMarket(direction, CFG.orderSizeBase, false);
    }

    this.risk.addTrade();
  }

  private async exitCurrent(side: BotSide, sizeBase: number): Promise<void> {
    if (side === 'flat' || sizeBase <= 0) return;

    const direction =
      side === 'long' ? PositionDirection.SHORT : PositionDirection.LONG;

    await this.placeMarket(direction, sizeBase, true);
    this.risk.addTrade();
  }

  private logStatus(s: StatusSnapshot): void {
    console.log(
      [
        `[${s.ts}]`,
        `px=${s.price.toFixed(4)}`,
        `emaF=${s.emaFast.toFixed(4)}`,
        `emaS=${s.emaSlow.toFixed(4)}`,
        `rsi=${s.rsi.toFixed(2)}`,
        `sig=${s.signal ?? 'none'}`,
        `pos=${s.side}`,
        `size=${s.size.toFixed(6)}`,
        `entry=${s.entry ? s.entry.toFixed(4) : 'n/a'}`,
        `pnlPct=${(s.pnlPct * 100).toFixed(3)}%`,
        `realDay=${s.realizedTodayUsd.toFixed(2)}`,
        `tradesDay=${s.tradesToday}`,
      ].join(' ')
    );
  }

  private async maybeRecordRealizedExit(markPrice: number, sideBefore: BotSide, sizeBefore: number) {
    const entry = this.getApproxEntryPrice();
    if (!entry || sideBefore === 'flat' || sizeBefore <= 0) return;

    const realizedUsd =
      sideBefore === 'long'
        ? (markPrice - entry) * sizeBefore
        : (entry - markPrice) * sizeBefore;

    this.risk.addRealizedPnl(realizedUsd);
  }

  private enoughHistory(): boolean {
    return this.history.length >= Math.max(CFG.slowEma + 5, CFG.rsiPeriod + 5);
  }

  private computeIndicators() {
    const price = this.history[this.history.length - 1];
    const emaFast = ema(this.history, CFG.fastEma);
    const emaSlow = ema(this.history, CFG.slowEma);
    const rsi = computeRsi(this.history, CFG.rsiPeriod);
    const signal = generateSignal(price, emaFast, emaSlow, rsi);
    return { price, emaFast, emaSlow, rsi, signal };
  }

  async tick(): Promise<void> {
    this.risk.syncDay();

    const price = this.getOraclePrice();
    this.pushPrice(price);

    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    const pnlPct = this.getPnlPct(price);

    if (!this.enoughHistory()) {
      console.log(`[${nowIso()}] warming up history=${this.history.length} px=${price.toFixed(4)}`);
      return;
    }

    const { emaFast, emaSlow, rsi, signal } = this.computeIndicators();
    const riskSnap = this.risk.snapshot();

    this.logStatus({
      ts: nowIso(),
      price,
      emaFast,
      emaSlow,
      rsi,
      signal,
      side: pos.side,
      size: pos.sizeBase,
      entry,
      pnlPct,
      realizedTodayUsd: riskSnap.realizedTodayUsd,
      tradesToday: riskSnap.tradesToday,
    });

    if (!this.risk.canTrade()) {
      console.log(`[${nowIso()}] blocked by daily risk limits`);
      return;
    }

    if (pos.side === 'flat' && signal) {
      await this.enter(signal, price);
      return;
    }

    if (pos.side !== 'flat') {
      if (pnlPct <= -CFG.slPct) {
        console.log(`[${nowIso()}] stop loss hit`);
        await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
        await this.exitCurrent(pos.side, pos.sizeBase);
        return;
      }

      if (pnlPct >= CFG.tpPct) {
        console.log(`[${nowIso()}] take profit hit`);
        await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
        await this.exitCurrent(pos.side, pos.sizeBase);
        return;
      }

      if (CFG.reduceOnReverse) {
        if ((pos.side === 'long' && signal === 'short') || (pos.side === 'short' && signal === 'long')) {
          console.log(`[${nowIso()}] reverse signal exit`);
          await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
          await this.exitCurrent(pos.side, pos.sizeBase);
          return;
        }
      }
    }
  }

  async printBalances(): Promise<void> {
    const sol = await this.provider.connection.getBalance(this.provider.wallet.publicKey);
    console.log(`[${nowIso()}] wallet=${this.provider.wallet.publicKey.toString()} SOL=${sol / 1e9}`);
  }

  async run(): Promise<void> {
    process.on('SIGINT', async () => {
      console.log(`[${nowIso()}] SIGINT, shutting down`);
      this.running = false;
      try {
        await this.user.unsubscribe();
      } catch {}
      try {
        await this.driftClient.unsubscribe();
      } catch {}
      process.exit(0);
    });

    await this.printBalances();

    while (this.running) {
      try {
        await this.tick();
      } catch (err) {
        console.error(`[${nowIso()}] tick error`, err);
      }
      await sleep(CFG.loopMs);
    }
  }
}

async function main() {
  const bot = new TinyDriftRealBot();
  await bot.init();
  await bot.run();
}

main().catch((e) => {
  console.error(`[${nowIso()}] fatal`, e);
  process.exit(1);
});

#### ChatGPT:


#### You:
// drift_tiny_real_bot.ts
//
// npm i @drift-labs/sdk @coral-xyz/anchor @solana/web3.js dotenv
//
// .env example:
// ANCHOR_WALLET=/absolute/path/to/id.json
// ANCHOR_PROVIDER_URL=https://your-dedicated-solana-rpc
// DRIFT_ENV=mainnet-beta
// DRY_RUN=true
// MARKET_SYMBOL=SOL
// ORDER_SIZE_BASE=0.02
// LOOP_MS=15000
// FAST_EMA=9
// SLOW_EMA=21
// RSI_PERIOD=14
// RSI_LONG_MAX=65
// RSI_SHORT_MIN=35
// TREND_MIN=0.0005
// TP_PCT=0.008
// SL_PCT=0.005
// MAX_HISTORY=300
// MAX_DAILY_LOSS_USD=2
// MAX_TRADES_PER_DAY=8
// REDUCE_ON_REVERSE=true
// USE_POST_ONLY=false
//
// Notes:
// - Start with DRY_RUN=true
// - Create and fund your Drift user account before live trading
// - This is intentionally a one-position directional bot for tiny balances

import 'dotenv/config';
import * as anchor from '@coral-xyz/anchor';
import {
  BulkAccountLoader,
  DriftClient,
  User,
  Wallet,
  initialize,
  PerpMarkets,
  PositionDirection,
  PRICE_PRECISION,
  BASE_PRECISION,
  QUOTE_PRECISION,
  convertToNumber,
  getMarketOrderParams,
  getLimitOrderParams,
  OrderType,
  PostOnlyParams,
} from '@drift-labs/sdk';

type BotSide = 'flat' | 'long' | 'short';

type StatusSnapshot = {
  ts: string;
  price: number;
  emaFast: number;
  emaSlow: number;
  rsi: number;
  signal: 'long' | 'short' | null;
  side: BotSide;
  size: number;
  entry: number | null;
  pnlPct: number;
  realizedTodayUsd: number;
  tradesToday: number;
};

const CFG = {
  env: (process.env.DRIFT_ENV || 'mainnet-beta') as 'devnet' | 'mainnet-beta',
  dryRun: String(process.env.DRY_RUN || 'true').toLowerCase() === 'true',
  marketSymbol: (process.env.MARKET_SYMBOL || 'SOL').toUpperCase(),
  orderSizeBase: Number(process.env.ORDER_SIZE_BASE || '0.02'),
  loopMs: Number(process.env.LOOP_MS || '15000'),
  fastEma: Number(process.env.FAST_EMA || '9'),
  slowEma: Number(process.env.SLOW_EMA || '21'),
  rsiPeriod: Number(process.env.RSI_PERIOD || '14'),
  rsiLongMax: Number(process.env.RSI_LONG_MAX || '65'),
  rsiShortMin: Number(process.env.RSI_SHORT_MIN || '35'),
  trendMin: Number(process.env.TREND_MIN || '0.0005'),
  tpPct: Number(process.env.TP_PCT || '0.008'),
  slPct: Number(process.env.SL_PCT || '0.005'),
  maxHistory: Number(process.env.MAX_HISTORY || '300'),
  maxDailyLossUsd: Number(process.env.MAX_DAILY_LOSS_USD || '2'),
  maxTradesPerDay: Number(process.env.MAX_TRADES_PER_DAY || '8'),
  reduceOnReverse: String(process.env.REDUCE_ON_REVERSE || 'true').toLowerCase() === 'true',
  usePostOnly: String(process.env.USE_POST_ONLY || 'false').toLowerCase() === 'true',
};

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function nowIso(): string {
  return new Date().toISOString();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function floorTo(x: number, decimals: number): number {
  const p = Math.pow(10, decimals);
  return Math.floor(x * p) / p;
}

function ema(values: number[], span: number): number {
  if (values.length === 0) return 0;
  const alpha = 2 / (span + 1);
  let out = values[0];
  for (let i = 1; i < values.length; i++) {
    out = alpha * values[i] + (1 - alpha) * out;
  }
  return out;
}

function computeRsi(values: number[], period: number): number {
  if (values.length < period + 1) return 50;

  let gains = 0;
  let losses = 0;
  const start = values.length - period;

  for (let i = start; i < values.length; i++) {
    const d = values[i] - values[i - 1];
    if (d > 0) gains += d;
    else losses += -d;
  }

  const avgGain = gains / period;
  const avgLoss = losses / period;

  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function generateSignal(
  mid: number,
  emaFast: number,
  emaSlow: number,
  rsi: number
): 'long' | 'short' | null {
  const trendStrength = Math.abs(emaFast - emaSlow) / mid;

  if (trendStrength < CFG.trendMin) return null;

  if (emaFast > emaSlow && rsi < CFG.rsiLongMax) return 'long';
  if (emaFast < emaSlow && rsi > CFG.rsiShortMin) return 'short';

  return null;
}

function currentUtcDayKey(): string {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(
    d.getUTCDate()
  ).padStart(2, '0')}`;
}

class DailyRiskLimiter {
  private dayKey: string = currentUtcDayKey();
  private realizedTodayUsd = 0;
  private tradesToday = 0;
  private blocked = false;

  syncDay(): void {
    const k = currentUtcDayKey();
    if (k !== this.dayKey) {
      this.dayKey = k;
      this.realizedTodayUsd = 0;
      this.tradesToday = 0;
      this.blocked = false;
    }
  }

  addRealizedPnl(deltaUsd: number): void {
    this.syncDay();
    this.realizedTodayUsd += deltaUsd;
    if (this.realizedTodayUsd <= -Math.abs(CFG.maxDailyLossUsd)) {
      this.blocked = true;
    }
  }

  addTrade(): void {
    this.syncDay();
    this.tradesToday += 1;
    if (this.tradesToday >= CFG.maxTradesPerDay) {
      this.blocked = true;
    }
  }

  canTrade(): boolean {
    this.syncDay();
    return !this.blocked;
  }

  snapshot() {
    this.syncDay();
    return {
      realizedTodayUsd: this.realizedTodayUsd,
      tradesToday: this.tradesToday,
      blocked: this.blocked,
    };
  }
}

class TinyDriftRealBot {
  private provider!: anchor.AnchorProvider;
  private driftClient!: DriftClient;
  private user!: User;
  private marketIndex!: number;
  private history: number[] = [];
  private running = true;
  private risk = new DailyRiskLimiter();

  async init(): Promise<void> {
    const rpc = required('ANCHOR_PROVIDER_URL');
    required('ANCHOR_WALLET');

    const sdkConfig = initialize({ env: CFG.env });

    this.provider = anchor.AnchorProvider.local(rpc, {
      commitment: 'confirmed',
      preflightCommitment: 'confirmed',
      skipPreflight: false,
    });

    const bulkAccountLoader = new BulkAccountLoader(
      this.provider.connection,
      'confirmed',
      1000
    );

    this.driftClient = new DriftClient({
      connection: this.provider.connection,
      wallet: this.provider.wallet as Wallet,
      programID: sdkConfig.DRIFT_PROGRAM_ID,
      accountSubscription: {
        type: 'polling',
        accountLoader: bulkAccountLoader,
      },
    });

    await this.driftClient.subscribe();

    this.user = new User({
      driftClient: this.driftClient,
      userAccountPublicKey: await this.driftClient.getUserAccountPublicKey(),
      accountSubscription: {
        type: 'polling',
        accountLoader: bulkAccountLoader,
      },
    });

    const exists = await this.user.exists();
    if (!exists) {
      throw new Error(
        'Drift user account not found. Create and fund it first in Drift UI or a setup script.'
      );
    }

    await this.user.subscribe();

    const market = PerpMarkets[CFG.env].find(
      (m: any) => String(m.baseAssetSymbol).toUpperCase() === CFG.marketSymbol
    );

    if (!market) {
      throw new Error(`Market ${CFG.marketSymbol}-PERP not found in ${CFG.env}`);
    }

    this.marketIndex = market.marketIndex;

    console.log(`[${nowIso()}] init ok env=${CFG.env} market=${CFG.marketSymbol}-PERP idx=${this.marketIndex} dryRun=${CFG.dryRun}`);
  }

  private getOraclePrice(): number {
    const oracle = this.driftClient.getOracleDataForPerpMarket(this.marketIndex);
    return convertToNumber(oracle.price, PRICE_PRECISION);
  }

  private pushPrice(px: number): void {
    this.history.push(px);
    if (this.history.length > CFG.maxHistory) {
      this.history = this.history.slice(-CFG.maxHistory);
    }
  }

  private getPosition(): { side: BotSide; sizeBase: number } {
    const p = this.user.getPerpPosition(this.marketIndex);
    if (!p) return { side: 'flat', sizeBase: 0 };

    const base = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    if (Math.abs(base) < 1e-10) return { side: 'flat', sizeBase: 0 };

    return {
      side: base > 0 ? 'long' : 'short',
      sizeBase: Math.abs(base),
    };
  }

  private getApproxEntryPrice(): number | null {
    const p = this.user.getPerpPosition(this.marketIndex);
    if (!p) return null;

    const base = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    if (Math.abs(base) < 1e-10) return null;

    const qea: any = (p as any).quoteEntryAmount;
    if (!qea) return null;

    const quoteEntry = Math.abs(convertToNumber(qea, QUOTE_PRECISION));
    return quoteEntry / Math.abs(base);
  }

  private getUnrealizedPnlUsd(markPrice: number): number {
    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    if (pos.side === 'flat' || !entry) return 0;

    if (pos.side === 'long') {
      return (markPrice - entry) * pos.sizeBase;
    } else {
      return (entry - markPrice) * pos.sizeBase;
    }
  }

  private getPnlPct(markPrice: number): number {
    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    if (pos.side === 'flat' || !entry) return 0;

    if (pos.side === 'long') {
      return (markPrice - entry) / entry;
    } else {
      return (entry - markPrice) / entry;
    }
  }

  private async placeMarket(direction: PositionDirection, sizeBase: number, reduceOnly = false) {
    if (sizeBase <= 0) return null;

    if (CFG.dryRun) {
      console.log(
        `[${nowIso()}] DRY market ${direction === PositionDirection.LONG ? 'LONG' : 'SHORT'} size=${sizeBase} reduceOnly=${reduceOnly}`
      );
      return 'dry-run';
    }

    const tx = await this.driftClient.placePerpOrder(
      getMarketOrderParams({
        marketIndex: this.marketIndex,
        direction,
        baseAssetAmount: this.driftClient.convertToPerpPrecision(sizeBase),
        reduceOnly,
      })
    );

    console.log(`[${nowIso()}] sent market order tx=${tx}`);
    return tx;
  }

  private async placePostOnly(direction: PositionDirection, sizeBase: number, oraclePrice: number) {
    if (sizeBase <= 0) return null;

    const pxOffsetBps = 5;
    const limitPx =
      direction === PositionDirection.LONG
        ? oraclePrice * (1 - pxOffsetBps / 10000)
        : oraclePrice * (1 + pxOffsetBps / 10000);

    if (CFG.dryRun) {
      console.log(
        `[${nowIso()}] DRY post-only ${direction === PositionDirection.LONG ? 'LONG' : 'SHORT'} size=${sizeBase} px=${limitPx.toFixed(4)}`
      );
      return 'dry-run';
    }

    const tx = await this.driftClient.placePerpOrder(
      getLimitOrderParams({
        marketIndex: this.marketIndex,
        direction,
        baseAssetAmount: this.driftClient.convertToPerpPrecision(sizeBase),
        price: this.driftClient.convertToPricePrecision(limitPx),
        orderType: OrderType.LIMIT,
        postOnly: PostOnlyParams.MUST_POST_ONLY,
      })
    );

    console.log(`[${nowIso()}] sent post-only order tx=${tx}`);
    return tx;
  }

  private async enter(signal: 'long' | 'short', price: number): Promise<void> {
    const direction =
      signal === 'long' ? PositionDirection.LONG : PositionDirection.SHORT;

    if (CFG.usePostOnly) {
      await this.placePostOnly(direction, CFG.orderSizeBase, price);
    } else {
      await this.placeMarket(direction, CFG.orderSizeBase, false);
    }

    this.risk.addTrade();
  }

  private async exitCurrent(side: BotSide, sizeBase: number): Promise<void> {
    if (side === 'flat' || sizeBase <= 0) return;

    const direction =
      side === 'long' ? PositionDirection.SHORT : PositionDirection.LONG;

    await this.placeMarket(direction, sizeBase, true);
    this.risk.addTrade();
  }

  private logStatus(s: StatusSnapshot): void {
    console.log(
      [
        `[${s.ts}]`,
        `px=${s.price.toFixed(4)}`,
        `emaF=${s.emaFast.toFixed(4)}`,
        `emaS=${s.emaSlow.toFixed(4)}`,
        `rsi=${s.rsi.toFixed(2)}`,
        `sig=${s.signal ?? 'none'}`,
        `pos=${s.side}`,
        `size=${s.size.toFixed(6)}`,
        `entry=${s.entry ? s.entry.toFixed(4) : 'n/a'}`,
        `pnlPct=${(s.pnlPct * 100).toFixed(3)}%`,
        `realDay=${s.realizedTodayUsd.toFixed(2)}`,
        `tradesDay=${s.tradesToday}`,
      ].join(' ')
    );
  }

  private async maybeRecordRealizedExit(markPrice: number, sideBefore: BotSide, sizeBefore: number) {
    const entry = this.getApproxEntryPrice();
    if (!entry || sideBefore === 'flat' || sizeBefore <= 0) return;

    const realizedUsd =
      sideBefore === 'long'
        ? (markPrice - entry) * sizeBefore
        : (entry - markPrice) * sizeBefore;

    this.risk.addRealizedPnl(realizedUsd);
  }

  private enoughHistory(): boolean {
    return this.history.length >= Math.max(CFG.slowEma + 5, CFG.rsiPeriod + 5);
  }

  private computeIndicators() {
    const price = this.history[this.history.length - 1];
    const emaFast = ema(this.history, CFG.fastEma);
    const emaSlow = ema(this.history, CFG.slowEma);
    const rsi = computeRsi(this.history, CFG.rsiPeriod);
    const signal = generateSignal(price, emaFast, emaSlow, rsi);
    return { price, emaFast, emaSlow, rsi, signal };
  }

  async tick(): Promise<void> {
    this.risk.syncDay();

    const price = this.getOraclePrice();
    this.pushPrice(price);

    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    const pnlPct = this.getPnlPct(price);

    if (!this.enoughHistory()) {
      console.log(`[${nowIso()}] warming up history=${this.history.length} px=${price.toFixed(4)}`);
      return;
    }

    const { emaFast, emaSlow, rsi, signal } = this.computeIndicators();
    const riskSnap = this.risk.snapshot();

    this.logStatus({
      ts: nowIso(),
      price,
      emaFast,
      emaSlow,
      rsi,
      signal,
      side: pos.side,
      size: pos.sizeBase,
      entry,
      pnlPct,
      realizedTodayUsd: riskSnap.realizedTodayUsd,
      tradesToday: riskSnap.tradesToday,
    });

    if (!this.risk.canTrade()) {
      console.log(`[${nowIso()}] blocked by daily risk limits`);
      return;
    }

    if (pos.side === 'flat' && signal) {
      await this.enter(signal, price);
      return;
    }

    if (pos.side !== 'flat') {
      if (pnlPct <= -CFG.slPct) {
        console.log(`[${nowIso()}] stop loss hit`);
        await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
        await this.exitCurrent(pos.side, pos.sizeBase);
        return;
      }

      if (pnlPct >= CFG.tpPct) {
        console.log(`[${nowIso()}] take profit hit`);
        await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
        await this.exitCurrent(pos.side, pos.sizeBase);
        return;
      }

      if (CFG.reduceOnReverse) {
        if ((pos.side === 'long' && signal === 'short') || (pos.side === 'short' && signal === 'long')) {
          console.log(`[${nowIso()}] reverse signal exit`);
          await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
          await this.exitCurrent(pos.side, pos.sizeBase);
          return;
        }
      }
    }
  }

  async printBalances(): Promise<void> {
    const sol = await this.provider.connection.getBalance(this.provider.wallet.publicKey);
    console.log(`[${nowIso()}] wallet=${this.provider.wallet.publicKey.toString()} SOL=${sol / 1e9}`);
  }

  async run(): Promise<void> {
    process.on('SIGINT', async () => {
      console.log(`[${nowIso()}] SIGINT, shutting down`);
      this.running = false;
      try {
        await this.user.unsubscribe();
      } catch {}
      try {
        await this.driftClient.unsubscribe();
      } catch {}
      process.exit(0);
    });

    await this.printBalances();

    while (this.running) {
      try {
        await this.tick();
      } catch (err) {
        console.error(`[${nowIso()}] tick error`, err);
      }
      await sleep(CFG.loopMs);
    }
  }
}

async function main() {
  const bot = new TinyDriftRealBot();
  await bot.init();
  await bot.run();
}

main().catch((e) => {
  console.error(`[${nowIso()}] fatal`, e);
  process.exit(1);
});

#### ChatGPT:
Похоже, ты скинул код бота для Drift на Solana. По структуре это **маленький directional perp-бот**: он берет цену из оракула, считает **EMA fast/slow + RSI**, открывает **long/short**, держит **только одну позицию**, закрывает по **take profit / stop loss / reverse signal**, и еще ограничивает **дневной убыток** и **число сделок в день**. Такой паттерн действительно соответствует тому, как это описано в текущем SDK Drift: `DriftClient`, `User`, `BulkAccountLoader`, `PerpMarkets`, `placePerpOrder`, `getMarketOrderParams`, `getLimitOrderParams` и работа с precision-константами есть в официальной документации SDK. ([Drift Labs](https://drift-labs.github.io/protocol-v2/sdk/?utm_source=chatgpt.com))

Если тебе нужен быстрый ревью, то по идее код **в целом рабоче выглядящий**, но я бы очень осторожно относился к запуску даже с `DRY_RUN=false`, потому что тут есть несколько практических рисков.

Самое важное: бот принимает решение по **oracle price**, а не по реальной исполняемой цене. Для сигналов это нормально, но для TP/SL и учета realized PnL это может заметно врать на волатильном рынке или при тонкой ликвидности. В коде `maybeRecordRealizedExit()` realized PnL считается по текущему `markPrice`, а не по фактическому fill, поэтому дневной лимит убытка может блокировать торговлю не по реальному результату сделки, а по приблизительной оценке. Drift SDK вообще показывает, что числа и позиции живут в точных BN-значениях и требуют аккуратной обработки, так что здесь приближение реально может иметь значение. ([Drift Labs](https://drift-labs.github.io/protocol-v2/sdk/?utm_source=chatgpt.com))

Вторая большая проблема: при `USE_POST_ONLY=true` бот умеет **ставить post-only лимитку**, но у него нет логики **проверки, исполнилась ли она**, **отмены старой заявки**, **защиты от накопления нескольких заявок**. В итоге на реверсах или повторных сигналах он может насоздавать висящие ордера. Для реального запуска это уже опасно.

Еще один важный момент: на reverse signal бот делает только **exit**, но не делает **immediate flip** в противоположную сторону. То есть `reduceOnReverse` у тебя сейчас по факту означает “закройся на развороте”, а не “перевернись”. Это не баг, если так и задумано, но многие ждут другого поведения.

Есть и менее критичные вещи:

- `floorTo()` не используется.
- `getUnrealizedPnlUsd()` нигде не используется.
- Нет проверки на уже существующие открытые ордера.
- Нет cooldown после выхода, так что на шумном рынке бот может часто перезаходить.
- Нет учета комиссий, funding и проскальзывания в логике TP/SL.
- `MAX_TRADES_PER_DAY` блокирует торговлю после достижения лимита, но считает и входы, и выходы; это может неожиданно быстро стопнуть бота.
- История цен строится только из последовательных сэмплов оракула раз в `LOOP_MS`, то есть это не свечи и не нормальный candle feed; EMA/RSI на таком потоке будут сильно зависеть от интервала опроса.

Что бы я поправил первым делом перед реальным запуском:

1. Добавил бы контроль **open orders**: не ставить новый ордер, пока не обработан старый.
2. Для `post-only` добавил бы **cancel/replace**.
3. Разделил бы **estimated PnL** и **realized PnL from fills**.
4. Добавил бы учет **fees + funding**.
5. Сделал бы простой state machine: `flat / entering / open / exiting`.
6. Оставил бы только `DRY_RUN=true`, пока не появится лог с реальными сценариями на нескольких днях.

Если хочешь, я могу сразу сделать тебе **жесткий production-review по строкам** и показать, где именно код может сломаться, либо дать **улучшенную версию этого бота** с защитой от висящих ордеров и более безопасной логикой входа/выхода.


#### You:
In dollars

#### ChatGPT:
Понял тебя 🙂 Ты про кота спрашивал - «сколько стоит, если продать», но теперь уточнил «в долларах».

Без фото и породы можно только дать **примерный диапазон**, потому что цена кота сильно зависит от типа:

### 🐱 Обычный домашний кот (без породы)

![Image](https://d3544la1u8djza.cloudfront.net/APHI/Blog/2022/02-11/gray%2Bstripe%2Bdomestic%2Bshortahair%2Btabby%2Bcat%2Bresting%2Bin%2Ba%2Bmaroon%2Bcat%2Btree%2Bbed-min.jpg)

![Image](https://d3544la1u8djza.cloudfront.net/APHI/Blog/2020/11-09/All%2BAbout%2BMixed%2BBreed%2BCats%2B_%2BWhat%2BMix%2BIs%2BYours%2B_%2BASPCA%2BPet%2BHealth%2BInsurance%2B_%2Bgreen%2Beyed%2Bmixed%2Bbreed%2Bcat%2Blooking%2Bout%2Bfrom%2Ba%2Bcat%2Btower-min.jpg)

![Image](https://upload.wikimedia.org/wikipedia/commons/4/4d/Cat_November_2010-1a.jpg)

![Image](https://www.thesprucepets.com/thmb/uQnGtOt9VQiML2oG2YzAmPErrHo%3D/5441x0/filters%3Ano_upscale%28%29%3Astrip_icc%28%29/all-about-tabby-cats-552489-hero-a23a9118af8c477b914a0a1570d4f787.jpg)

- Обычно: **$0 - $50**
- Иногда бесплатно (через объявления / приют)
- Максимум - символическая цена за «переуступку»

👉 По факту: чаще не продают, а **отдают в хорошие руки**

---

### 🐾 Породистый кот (с документами)

![Image](https://www.omlet.us/images/cache/1024/682/British-shorthair-self-cat-lying-on-floor.jpg)

![Image](https://images.ctfassets.net/nx3pzsky0bc9/4I6Zj66MudGo0u52Vjl5pv/f7c08c17af585b012549ec4748b26e2c/Untitled_design__32_.png?q=65\&w=804)

![Image](https://cdn.shopify.com/s/files/1/0765/3946/1913/files/Scottish_Fold_on_the_Table.jpg?v=1738746295)

![Image](https://images.ctfassets.net/440y9b545yd9/3mXEPSN2Ap12wAnFz8dVm2/f4ef7266f4ec59220df70833b2749f25/Scottish_fold_5_things_hero850.jpg)

- Бюджетные породы: **$200 - $800**
- Популярные: **$800 - $2,000**
- Топ/редкие: **$2,000 - $5,000+**

---

### 💡 Если коротко

- «Обычный кот» → почти **бесплатно**
- «Красивый/породистый» → от **нескольких сотен до тысяч долларов**

---

Если хочешь - скинь фото кота 🐱\
Я скажу **реальную цену намного точнее**, иногда можно попасть в очень разный диапазон (вплоть до x10 разницы).


#### You:
Code 

#### ChatGPT:
А, ты про **код**, понял 👍\
Давай по делу: сколько стоит такой бот в долларах.

## 💻 Примерная стоимость такого кода

### 🧠 Уровень: как у тебя (маленький trading bot)

То, что ты скинул - это:

- EMA + RSI стратегия
- работа с Drift SDK
- risk management (дневной лимит, TP/SL)
- один рынок, одна позиция

👉 На рынке фриланса:

- 💸 **$150 - $400** - если просто «как есть»
- 💸 **$400 - $800** - если стабильно работает + норм логика
- 💸 **$800 - $1500** - если довести до production (очень важно)

---

## 🚨 Почему не дороже

Потому что:

- стратегия **простая (EMA + RSI)**
- нет:
  - order management (cancel/replace)
  - защиты от багов
  - работы с ликвидностью
  - multi-market
  - backtesting системы

👉 Это больше **MVP / pet project**, чем полноценный трейдинг-бот

---

## 💰 Когда такой код стоит $2000+

Если добавить:

- авто-отмену ордеров
- слежение за fill'ами
- funding / fee учёт
- WebSocket вместо polling
- backtesting
- UI / dashboard

👉 Тогда уже:

- **$2000 - $5000+**

---

## ⚠️ Самое честное

Твой код:
👉 хороший старт\
👉 но **не готов для реальных денег**

И на рынке это чувствуется - поэтому цена пока в диапазоне **до \~$500**

---

Если хочешь, могу:

- оценить как **покупатель (жёстко, как на рынке)**
- или прокачать его до уровня, где он реально будет стоить **$2-3k+**


#### You:
// drift_tiny_real_bot.ts
//
// npm i @drift-labs/sdk @coral-xyz/anchor @solana/web3.js dotenv
//
// .env example:
// ANCHOR_WALLET=/absolute/path/to/id.json
// ANCHOR_PROVIDER_URL=https://your-dedicated-solana-rpc
// DRIFT_ENV=mainnet-beta
// DRY_RUN=true
// MARKET_SYMBOL=SOL
// ORDER_SIZE_BASE=0.02
// LOOP_MS=15000
// FAST_EMA=9
// SLOW_EMA=21
// RSI_PERIOD=14
// RSI_LONG_MAX=65
// RSI_SHORT_MIN=35
// TREND_MIN=0.0005
// TP_PCT=0.008
// SL_PCT=0.005
// MAX_HISTORY=300
// MAX_DAILY_LOSS_USD=2
// MAX_TRADES_PER_DAY=8
// REDUCE_ON_REVERSE=true
// USE_POST_ONLY=false
//
// Notes:
// - Start with DRY_RUN=true
// - Create and fund your Drift user account before live trading
// - This is intentionally a one-position directional bot for tiny balances

import 'dotenv/config';
import * as anchor from '@coral-xyz/anchor';
import {
  BulkAccountLoader,
  DriftClient,
  User,
  Wallet,
  initialize,
  PerpMarkets,
  PositionDirection,
  PRICE_PRECISION,
  BASE_PRECISION,
  QUOTE_PRECISION,
  convertToNumber,
  getMarketOrderParams,
  getLimitOrderParams,
  OrderType,
  PostOnlyParams,
} from '@drift-labs/sdk';

type BotSide = 'flat' | 'long' | 'short';

type StatusSnapshot = {
  ts: string;
  price: number;
  emaFast: number;
  emaSlow: number;
  rsi: number;
  signal: 'long' | 'short' | null;
  side: BotSide;
  size: number;
  entry: number | null;
  pnlPct: number;
  realizedTodayUsd: number;
  tradesToday: number;
};

const CFG = {
  env: (process.env.DRIFT_ENV || 'mainnet-beta') as 'devnet' | 'mainnet-beta',
  dryRun: String(process.env.DRY_RUN || 'true').toLowerCase() === 'true',
  marketSymbol: (process.env.MARKET_SYMBOL || 'SOL').toUpperCase(),
  orderSizeBase: Number(process.env.ORDER_SIZE_BASE || '0.02'),
  loopMs: Number(process.env.LOOP_MS || '15000'),
  fastEma: Number(process.env.FAST_EMA || '9'),
  slowEma: Number(process.env.SLOW_EMA || '21'),
  rsiPeriod: Number(process.env.RSI_PERIOD || '14'),
  rsiLongMax: Number(process.env.RSI_LONG_MAX || '65'),
  rsiShortMin: Number(process.env.RSI_SHORT_MIN || '35'),
  trendMin: Number(process.env.TREND_MIN || '0.0005'),
  tpPct: Number(process.env.TP_PCT || '0.008'),
  slPct: Number(process.env.SL_PCT || '0.005'),
  maxHistory: Number(process.env.MAX_HISTORY || '300'),
  maxDailyLossUsd: Number(process.env.MAX_DAILY_LOSS_USD || '2'),
  maxTradesPerDay: Number(process.env.MAX_TRADES_PER_DAY || '8'),
  reduceOnReverse: String(process.env.REDUCE_ON_REVERSE || 'true').toLowerCase() === 'true',
  usePostOnly: String(process.env.USE_POST_ONLY || 'false').toLowerCase() === 'true',
};

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function nowIso(): string {
  return new Date().toISOString();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function floorTo(x: number, decimals: number): number {
  const p = Math.pow(10, decimals);
  return Math.floor(x * p) / p;
}

function ema(values: number[], span: number): number {
  if (values.length === 0) return 0;
  const alpha = 2 / (span + 1);
  let out = values[0];
  for (let i = 1; i < values.length; i++) {
    out = alpha * values[i] + (1 - alpha) * out;
  }
  return out;
}

function computeRsi(values: number[], period: number): number {
  if (values.length < period + 1) return 50;

  let gains = 0;
  let losses = 0;
  const start = values.length - period;

  for (let i = start; i < values.length; i++) {
    const d = values[i] - values[i - 1];
    if (d > 0) gains += d;
    else losses += -d;
  }

  const avgGain = gains / period;
  const avgLoss = losses / period;

  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function generateSignal(
  mid: number,
  emaFast: number,
  emaSlow: number,
  rsi: number
): 'long' | 'short' | null {
  const trendStrength = Math.abs(emaFast - emaSlow) / mid;

  if (trendStrength < CFG.trendMin) return null;

  if (emaFast > emaSlow && rsi < CFG.rsiLongMax) return 'long';
  if (emaFast < emaSlow && rsi > CFG.rsiShortMin) return 'short';

  return null;
}

function currentUtcDayKey(): string {
  const d = new Date();
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(
    d.getUTCDate()
  ).padStart(2, '0')}`;
}

class DailyRiskLimiter {
  private dayKey: string = currentUtcDayKey();
  private realizedTodayUsd = 0;
  private tradesToday = 0;
  private blocked = false;

  syncDay(): void {
    const k = currentUtcDayKey();
    if (k !== this.dayKey) {
      this.dayKey = k;
      this.realizedTodayUsd = 0;
      this.tradesToday = 0;
      this.blocked = false;
    }
  }

  addRealizedPnl(deltaUsd: number): void {
    this.syncDay();
    this.realizedTodayUsd += deltaUsd;
    if (this.realizedTodayUsd <= -Math.abs(CFG.maxDailyLossUsd)) {
      this.blocked = true;
    }
  }

  addTrade(): void {
    this.syncDay();
    this.tradesToday += 1;
    if (this.tradesToday >= CFG.maxTradesPerDay) {
      this.blocked = true;
    }
  }

  canTrade(): boolean {
    this.syncDay();
    return !this.blocked;
  }

  snapshot() {
    this.syncDay();
    return {
      realizedTodayUsd: this.realizedTodayUsd,
      tradesToday: this.tradesToday,
      blocked: this.blocked,
    };
  }
}

class TinyDriftRealBot {
  private provider!: anchor.AnchorProvider;
  private driftClient!: DriftClient;
  private user!: User;
  private marketIndex!: number;
  private history: number[] = [];
  private running = true;
  private risk = new DailyRiskLimiter();

  async init(): Promise<void> {
    const rpc = required('ANCHOR_PROVIDER_URL');
    required('ANCHOR_WALLET');

    const sdkConfig = initialize({ env: CFG.env });

    this.provider = anchor.AnchorProvider.local(rpc, {
      commitment: 'confirmed',
      preflightCommitment: 'confirmed',
      skipPreflight: false,
    });

    const bulkAccountLoader = new BulkAccountLoader(
      this.provider.connection,
      'confirmed',
      1000
    );

    this.driftClient = new DriftClient({
      connection: this.provider.connection,
      wallet: this.provider.wallet as Wallet,
      programID: sdkConfig.DRIFT_PROGRAM_ID,
      accountSubscription: {
        type: 'polling',
        accountLoader: bulkAccountLoader,
      },
    });

    await this.driftClient.subscribe();

    this.user = new User({
      driftClient: this.driftClient,
      userAccountPublicKey: await this.driftClient.getUserAccountPublicKey(),
      accountSubscription: {
        type: 'polling',
        accountLoader: bulkAccountLoader,
      },
    });

    const exists = await this.user.exists();
    if (!exists) {
      throw new Error(
        'Drift user account not found. Create and fund it first in Drift UI or a setup script.'
      );
    }

    await this.user.subscribe();

    const market = PerpMarkets[CFG.env].find(
      (m: any) => String(m.baseAssetSymbol).toUpperCase() === CFG.marketSymbol
    );

    if (!market) {
      throw new Error(`Market ${CFG.marketSymbol}-PERP not found in ${CFG.env}`);
    }

    this.marketIndex = market.marketIndex;

    console.log(`[${nowIso()}] init ok env=${CFG.env} market=${CFG.marketSymbol}-PERP idx=${this.marketIndex} dryRun=${CFG.dryRun}`);
  }

  private getOraclePrice(): number {
    const oracle = this.driftClient.getOracleDataForPerpMarket(this.marketIndex);
    return convertToNumber(oracle.price, PRICE_PRECISION);
  }

  private pushPrice(px: number): void {
    this.history.push(px);
    if (this.history.length > CFG.maxHistory) {
      this.history = this.history.slice(-CFG.maxHistory);
    }
  }

  private getPosition(): { side: BotSide; sizeBase: number } {
    const p = this.user.getPerpPosition(this.marketIndex);
    if (!p) return { side: 'flat', sizeBase: 0 };

    const base = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    if (Math.abs(base) < 1e-10) return { side: 'flat', sizeBase: 0 };

    return {
      side: base > 0 ? 'long' : 'short',
      sizeBase: Math.abs(base),
    };
  }

  private getApproxEntryPrice(): number | null {
    const p = this.user.getPerpPosition(this.marketIndex);
    if (!p) return null;

    const base = convertToNumber(p.baseAssetAmount, BASE_PRECISION);
    if (Math.abs(base) < 1e-10) return null;

    const qea: any = (p as any).quoteEntryAmount;
    if (!qea) return null;

    const quoteEntry = Math.abs(convertToNumber(qea, QUOTE_PRECISION));
    return quoteEntry / Math.abs(base);
  }

  private getUnrealizedPnlUsd(markPrice: number): number {
    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    if (pos.side === 'flat' || !entry) return 0;

    if (pos.side === 'long') {
      return (markPrice - entry) * pos.sizeBase;
    } else {
      return (entry - markPrice) * pos.sizeBase;
    }
  }

  private getPnlPct(markPrice: number): number {
    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    if (pos.side === 'flat' || !entry) return 0;

    if (pos.side === 'long') {
      return (markPrice - entry) / entry;
    } else {
      return (entry - markPrice) / entry;
    }
  }

  private async placeMarket(direction: PositionDirection, sizeBase: number, reduceOnly = false) {
    if (sizeBase <= 0) return null;

    if (CFG.dryRun) {
      console.log(
        `[${nowIso()}] DRY market ${direction === PositionDirection.LONG ? 'LONG' : 'SHORT'} size=${sizeBase} reduceOnly=${reduceOnly}`
      );
      return 'dry-run';
    }

    const tx = await this.driftClient.placePerpOrder(
      getMarketOrderParams({
        marketIndex: this.marketIndex,
        direction,
        baseAssetAmount: this.driftClient.convertToPerpPrecision(sizeBase),
        reduceOnly,
      })
    );

    console.log(`[${nowIso()}] sent market order tx=${tx}`);
    return tx;
  }

  private async placePostOnly(direction: PositionDirection, sizeBase: number, oraclePrice: number) {
    if (sizeBase <= 0) return null;

    const pxOffsetBps = 5;
    const limitPx =
      direction === PositionDirection.LONG
        ? oraclePrice * (1 - pxOffsetBps / 10000)
        : oraclePrice * (1 + pxOffsetBps / 10000);

    if (CFG.dryRun) {
      console.log(
        `[${nowIso()}] DRY post-only ${direction === PositionDirection.LONG ? 'LONG' : 'SHORT'} size=${sizeBase} px=${limitPx.toFixed(4)}`
      );
      return 'dry-run';
    }

    const tx = await this.driftClient.placePerpOrder(
      getLimitOrderParams({
        marketIndex: this.marketIndex,
        direction,
        baseAssetAmount: this.driftClient.convertToPerpPrecision(sizeBase),
        price: this.driftClient.convertToPricePrecision(limitPx),
        orderType: OrderType.LIMIT,
        postOnly: PostOnlyParams.MUST_POST_ONLY,
      })
    );

    console.log(`[${nowIso()}] sent post-only order tx=${tx}`);
    return tx;
  }

  private async enter(signal: 'long' | 'short', price: number): Promise<void> {
    const direction =
      signal === 'long' ? PositionDirection.LONG : PositionDirection.SHORT;

    if (CFG.usePostOnly) {
      await this.placePostOnly(direction, CFG.orderSizeBase, price);
    } else {
      await this.placeMarket(direction, CFG.orderSizeBase, false);
    }

    this.risk.addTrade();
  }

  private async exitCurrent(side: BotSide, sizeBase: number): Promise<void> {
    if (side === 'flat' || sizeBase <= 0) return;

    const direction =
      side === 'long' ? PositionDirection.SHORT : PositionDirection.LONG;

    await this.placeMarket(direction, sizeBase, true);
    this.risk.addTrade();
  }

  private logStatus(s: StatusSnapshot): void {
    console.log(
      [
        `[${s.ts}]`,
        `px=${s.price.toFixed(4)}`,
        `emaF=${s.emaFast.toFixed(4)}`,
        `emaS=${s.emaSlow.toFixed(4)}`,
        `rsi=${s.rsi.toFixed(2)}`,
        `sig=${s.signal ?? 'none'}`,
        `pos=${s.side}`,
        `size=${s.size.toFixed(6)}`,
        `entry=${s.entry ? s.entry.toFixed(4) : 'n/a'}`,
        `pnlPct=${(s.pnlPct * 100).toFixed(3)}%`,
        `realDay=${s.realizedTodayUsd.toFixed(2)}`,
        `tradesDay=${s.tradesToday}`,
      ].join(' ')
    );
  }

  private async maybeRecordRealizedExit(markPrice: number, sideBefore: BotSide, sizeBefore: number) {
    const entry = this.getApproxEntryPrice();
    if (!entry || sideBefore === 'flat' || sizeBefore <= 0) return;

    const realizedUsd =
      sideBefore === 'long'
        ? (markPrice - entry) * sizeBefore
        : (entry - markPrice) * sizeBefore;

    this.risk.addRealizedPnl(realizedUsd);
  }

  private enoughHistory(): boolean {
    return this.history.length >= Math.max(CFG.slowEma + 5, CFG.rsiPeriod + 5);
  }

  private computeIndicators() {
    const price = this.history[this.history.length - 1];
    const emaFast = ema(this.history, CFG.fastEma);
    const emaSlow = ema(this.history, CFG.slowEma);
    const rsi = computeRsi(this.history, CFG.rsiPeriod);
    const signal = generateSignal(price, emaFast, emaSlow, rsi);
    return { price, emaFast, emaSlow, rsi, signal };
  }

  async tick(): Promise<void> {
    this.risk.syncDay();

    const price = this.getOraclePrice();
    this.pushPrice(price);

    const pos = this.getPosition();
    const entry = this.getApproxEntryPrice();
    const pnlPct = this.getPnlPct(price);

    if (!this.enoughHistory()) {
      console.log(`[${nowIso()}] warming up history=${this.history.length} px=${price.toFixed(4)}`);
      return;
    }

    const { emaFast, emaSlow, rsi, signal } = this.computeIndicators();
    const riskSnap = this.risk.snapshot();

    this.logStatus({
      ts: nowIso(),
      price,
      emaFast,
      emaSlow,
      rsi,
      signal,
      side: pos.side,
      size: pos.sizeBase,
      entry,
      pnlPct,
      realizedTodayUsd: riskSnap.realizedTodayUsd,
      tradesToday: riskSnap.tradesToday,
    });

    if (!this.risk.canTrade()) {
      console.log(`[${nowIso()}] blocked by daily risk limits`);
      return;
    }

    if (pos.side === 'flat' && signal) {
      await this.enter(signal, price);
      return;
    }

    if (pos.side !== 'flat') {
      if (pnlPct <= -CFG.slPct) {
        console.log(`[${nowIso()}] stop loss hit`);
        await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
        await this.exitCurrent(pos.side, pos.sizeBase);
        return;
      }

      if (pnlPct >= CFG.tpPct) {
        console.log(`[${nowIso()}] take profit hit`);
        await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
        await this.exitCurrent(pos.side, pos.sizeBase);
        return;
      }

      if (CFG.reduceOnReverse) {
        if ((pos.side === 'long' && signal === 'short') || (pos.side === 'short' && signal === 'long')) {
          console.log(`[${nowIso()}] reverse signal exit`);
          await this.maybeRecordRealizedExit(price, pos.side, pos.sizeBase);
          await this.exitCurrent(pos.side, pos.sizeBase);
          return;
        }
      }
    }
  }

  async printBalances(): Promise<void> {
    const sol = await this.provider.connection.getBalance(this.provider.wallet.publicKey);
    console.log(`[${nowIso()}] wallet=${this.provider.wallet.publicKey.toString()} SOL=${sol / 1e9}`);
  }

  async run(): Promise<void> {
    process.on('SIGINT', async () => {
      console.log(`[${nowIso()}] SIGINT, shutting down`);
      this.running = false;
      try {
        await this.user.unsubscribe();
      } catch {}
      try {
        await this.driftClient.unsubscribe();
      } catch {}
      process.exit(0);
    });

    await this.printBalances();

    while (this.running) {
      try {
        await this.tick();
      } catch (err) {
        console.error(`[${nowIso()}] tick error`, err);
      }
      await sleep(CFG.loopMs);
    }
  }
}

async function main() {
  const bot = new TinyDriftRealBot();
  await bot.init();
  await bot.run();
}

main().catch((e) => {
  console.error(`[${nowIso()}] fatal`, e);
  process.exit(1);
});

#### ChatGPT:
За **этот код как есть** я бы оценил примерно так:

**$100–300** — если просто продать исходник\
**$300–700** — если он у тебя реально запускается, настроен и ты можешь показать логи/демо\
**$800+** — только если довести до более надежного состояния

Почему не сильно дороже:

- стратегия очень простая: **EMA + RSI**
- один рынок, одна позиция
- нет нормального управления ордерами
- нет backtest/reporting
- нет работы с fill-ами, fee, funding
- `post-only` логика сырая
- для real money он пока рискованный

По сути это:

- **не мусор**, потому что код структурный и читаемый
- но и **не production bot**, поэтому цена умеренная

Если совсем по-честному, как покупатель:

- **$150–250** за “бот как шаблон”
- **$400–500** максимум, если продаешь с помощью в установке
- **$1k+** только после серьезной доработки

Если хочешь, я могу прямо по этому файлу дать **жесткую рыночную оценку по 10-балльной шкале**: качество кода, надежность, коммерческая ценность и сколько за него реально просить.
