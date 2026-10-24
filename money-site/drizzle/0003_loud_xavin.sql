CREATE TABLE `money_earn_ledger` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`client_id` text NOT NULL,
	`payload_hash` text NOT NULL,
	`type` text NOT NULL,
	`amount_minor` integer NOT NULL,
	`currency` text NOT NULL,
	`occurred_on` text,
	`category` text NOT NULL,
	`receipt_ref` text,
	`evidence_status` text NOT NULL,
	`source` text NOT NULL,
	`minutes` real,
	`legacy_paid_flag` integer,
	`legacy_platform` text,
	`created_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `money_earn_ledger_user_client_idx` ON `money_earn_ledger` (`user_id`,`client_id`);--> statement-breakpoint
CREATE INDEX `money_earn_ledger_user_created_idx` ON `money_earn_ledger` (`user_id`,`created_at`,`id`);