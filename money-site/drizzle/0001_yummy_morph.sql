CREATE TABLE `money_comparator_cache` (
	`id` text PRIMARY KEY NOT NULL,
	`updated` integer NOT NULL,
	`payload` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `money_market_snapshots` (
	`id` text PRIMARY KEY NOT NULL,
	`asset` text NOT NULL,
	`horizon` integer NOT NULL,
	`window_start` integer NOT NULL,
	`window_end` integer NOT NULL,
	`created` integer NOT NULL,
	`payload` text NOT NULL
);
