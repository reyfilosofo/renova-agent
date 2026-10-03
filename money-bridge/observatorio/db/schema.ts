import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";

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
});

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
