import { sqliteTable, text, integer, real, index, uniqueIndex } from "drizzle-orm/sqlite-core";

export const forecasts = sqliteTable("money_forecasts", {
  id: text("id").primaryKey(),
  asset: text("asset").notNull(),
  horizon: integer("horizon").notNull(),
  source: text("source").notNull(),
  origin: integer("origin").notNull(),
  target: integer("target").notNull(),
  reference: real("reference").notNull(),
  probability: real("probability").notNull(),
  created: integer("created").notNull(),
  payload: text("payload").notNull(),
  outcome: text("outcome"),
  resolved: integer("resolved"),
  finalPrice: real("final_price"),
}, table => [index('money_forecasts_daily_idx').on(table.horizon,table.origin,table.created)]);

export const observations = sqliteTable("money_observations", {
  id: text("id").primaryKey(),
  asset: text("asset").notNull(),
  created: integer("created").notNull(),
  payload: text("payload").notNull(),
});

export const historyCache = sqliteTable("money_history_cache", {
  asset: text("asset").primaryKey(),
  source: text("source").notNull(),
  updated: integer("updated").notNull(),
  payload: text("payload").notNull(),
});

export const comparatorCache = sqliteTable("money_comparator_cache", {
  id: text("id").primaryKey(),
  updated: integer("updated").notNull(),
  payload: text("payload").notNull(),
});

export const marketSnapshots = sqliteTable("money_market_snapshots", {
  id: text("id").primaryKey(),
  asset: text("asset").notNull(),
  horizon: integer("horizon").notNull(),
  windowStart: integer("window_start").notNull(),
  windowEnd: integer("window_end").notNull(),
  created: integer("created").notNull(),
  payload: text("payload").notNull(),
}, table => [index('money_market_snapshots_daily_idx').on(table.horizon,table.windowStart,table.created)]);

// Private, append-only operator reports. These are not reconciled account truth.
export const earnLedger = sqliteTable("money_earn_ledger", {
  id: text("id").primaryKey(),
  userId: text("user_id").notNull(),
  clientId: text("client_id").notNull(),
  payloadHash: text("payload_hash").notNull(),
  type: text("type").notNull(),
  amountMinor: integer("amount_minor").notNull(),
  currency: text("currency").notNull(),
  occurredOn: text("occurred_on"),
  category: text("category").notNull(),
  receiptRef: text("receipt_ref"),
  evidenceStatus: text("evidence_status").notNull(),
  source: text("source").notNull(),
  minutes: real("minutes"),
  legacyPaidFlag: integer("legacy_paid_flag", { mode: 'boolean' }),
  legacyPlatform: text("legacy_platform"),
  createdAt: integer("created_at").notNull(),
}, table => [
  uniqueIndex("money_earn_ledger_user_client_idx").on(table.userId, table.clientId),
  index("money_earn_ledger_user_created_idx").on(table.userId, table.createdAt, table.id),
]);
