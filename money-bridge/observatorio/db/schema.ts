import { sqliteTable, text, integer, real, index } from "drizzle-orm/sqlite-core";

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
