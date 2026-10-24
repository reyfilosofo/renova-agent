CREATE TABLE `money_forecasts` (
	`id` text PRIMARY KEY NOT NULL,
	`asset` text NOT NULL,
	`horizon` integer NOT NULL,
	`source` text NOT NULL,
	`origin` integer NOT NULL,
	`target` integer NOT NULL,
	`reference` real NOT NULL,
	`probability` real NOT NULL,
	`created` integer NOT NULL,
	`payload` text NOT NULL,
	`outcome` text,
	`resolved` integer,
	`final_price` real
);
--> statement-breakpoint
CREATE TABLE `money_history_cache` (
	`asset` text PRIMARY KEY NOT NULL,
	`source` text NOT NULL,
	`updated` integer NOT NULL,
	`payload` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `money_observations` (
	`id` text PRIMARY KEY NOT NULL,
	`asset` text NOT NULL,
	`created` integer NOT NULL,
	`payload` text NOT NULL
);
