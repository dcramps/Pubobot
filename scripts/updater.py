#!/usr/bin/python3
# encoding: utf-8
import sqlite3

conn = sqlite3.connect("database.sqlite3")
conn.row_factory = sqlite3.Row
c = conn.cursor()

db_version = c.execute("SELECT value FROM utility WHERE variable='version'").fetchone()[0]
if db_version != '4':
	print("Incorrect database version (must be 4, but got {0}).".format(db_version))
	raise SystemExit(1)

#bans
print("Rebuilding bans table...")
c.execute("SELECT `channel_id`, `user_id`, `user_name`, `active`, `at`, `duratation`, `reason`, `author_name`, `unban_author_name` FROM `bans`")
data = c.fetchall()
c.execute("DROP TABLE `bans`")
c.execute("CREATE TABLE `bans` ( `channel_id` INTEGER, `user_id` INTEGER, `user_name` TEXT, `active` BLOB, `at` INTEGER, `duratation` INTEGER, `reason` TEXT, `author_name` TEXT, `unban_author_name` TEXT )")
c.executemany("INSERT INTO `bans` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
conn.commit()

#channel_players
print("Rebuilding channel_players table...")
c.execute("SELECT `channel_id`, `user_id`, `nick`, `rank`, `wins`, `loses`, `phrase` FROM `channel_players`")
data = c.fetchall()
c.execute("DROP TABLE `channel_players`")
c.execute("CREATE TABLE `channel_players` ( `channel_id` INTEGER, `user_id` INTEGER, `nick` TEXT, `rank` INTEGER, `wins` INTEGER, `loses` INTEGER, `phrase` TEXT, PRIMARY KEY(`channel_id`, `user_id`) )")
c.executemany("INSERT INTO `channel_players` VALUES (?, ?, ?, ?, ?, ?, ?)", data)
conn.commit()

#channels
print("Rebuilding channels table...")
c.execute("SELECT `server_id`, `server_name`, `channel_id`, `channel_name`, `premium`, `first_init`, `admin_id`, `admin_role`, `moderator_role`, `captains_role`, `noadd_role`, `prefix`, `default_bantime`, `++_req_players`, `startmsg` TEXT, `submsg` TEXT, `promotemsg`, `ip`, `password`, `maps`, `pick_captains`, `pick_teams`, `pick_order`, `promotion_role`, `promotion_delay`, `blacklist_role`, `whitelist_role`, `require_ready`, `ranked`, `ranked_multiplayer`,`ranked_calibrate`, `start_pm_msg` FROM `channels`")
data = c.fetchall()
c.execute("DROP TABLE `channels`")
c.execute("CREATE TABLE `channels` ( `server_id` INTEGER, `server_name` TEXT, `channel_id` INTEGER, `channel_name` TEXT, `premium` BOOL, `first_init` INTEGER, `admin_id` INTEGER, `admin_role` INTEGER, `moderator_role` INTEGER, `captains_role` INTEGER, `noadd_role` INTEGER, `prefix` TEXT DEFAULT '!', `default_bantime` INTEGER DEFAULT 7200, `++_req_players` INTEGER DEFAULT 5, `startmsg` TEXT, `submsg` TEXT, `promotemsg` TEXT, `ip` TEXT, `password` TEXT, `maps` TEXT, `pick_captains` INTEGER, `pick_teams` TEXT DEFAULT 'no_teams', `pick_order` TEXT, `promotion_role` INTEGER, `promotion_delay` INTEGER DEFAULT 18000, `blacklist_role` INTEGER, `whitelist_role` INTEGER, `require_ready` INTEGER, `ranked` INTEGER, `ranked_multiplayer` INTEGER DEFAULT 32, `ranked_calibrate` INTEGER DEFAULT 1, `start_pm_msg` TEXT DEFAULT '**%pickup_name%** pickup has been started @ %channel%.', PRIMARY KEY(`channel_id`) )")
c.executemany("INSERT INTO `channels` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
conn.commit()

#pickup_configs
print("Rebuilding pickup_configs table...")
c.execute("SELECT `channel_id`, `pickup_name`, `maxplayers`, `minplayers`, `startmsg`, `start_pm_msg`, `submsg`, `promotemsg`, `ip`, `password`, `maps`, `pick_captains`, `captains_role`, `pick_teams`, `pick_order`, `promotion_role`, `blacklist_role`, `whitelist_role`, `captain_role`, `require_ready`, `ranked`, `allow_offline` FROM `pickup_configs`")
data = c.fetchall()
c.execute("DROP TABLE `pickup_configs`")
c.execute("CREATE TABLE `pickup_configs` ( `channel_id` INTEGER, `pickup_name` TEXT, `maxplayers` INTEGER, `minplayers` INTEGER, `startmsg` TEXT, `start_pm_msg` TEXT, `submsg` TEXT, `promotemsg` TEXT, `ip` TEXT, `password` TEXT, `maps` TEXT, `pick_captains` INTEGER, `captains_role` INTEGER, `pick_teams` TEXT, `pick_order` TEXT, `promotion_role` INTEGER, `blacklist_role` INTEGER, `whitelist_role` INTEGER, `captain_role` INTEGER, `require_ready` INTEGER, `ranked` INTEGER, `allow_offline` INTEGER DEFAULT 0, PRIMARY KEY(`channel_id`, `pickup_name`) )")
c.executemany("INSERT INTO `pickup_configs` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
conn.commit()

#pickup_groups
print("Rebuilding pickup_groups table...")
c.execute("SELECT `channel_id`, `group_name`, `pickup_names` FROM `pickup_groups`")
data = c.fetchall()
c.execute("DROP TABLE `pickup_groups`")
c.execute("CREATE TABLE `pickup_groups` ( `channel_id` INTEGER, `group_name` TEXT, `pickup_names` TEXT, PRIMARY KEY(`channel_id`, `group_name`) )")
c.executemany("INSERT INTO `pickup_groups` VALUES (?, ?, ?)", data)
conn.commit()

#pickups
print("Rebuilding pickups table...")
c.execute("SELECT `pickup_id`, `channel_id`, `pickup_name`, `at`, `players`, `alpha_players`, `beta_players`, `is_ranked`, `winner_team` FROM pickups")
data = c.fetchall()
c.execute("DROP TABLE pickups")
c.execute("CREATE TABLE `pickups` ( `pickup_id` INTEGER PRIMARY KEY, `channel_id` INTEGER, `pickup_name` TEXT, `at` INTEGER, `players` TEXT, `alpha_players` TEXT, `beta_players` TEXT, `is_ranked` BOOL, `winner_team` TEXT )")
c.executemany("INSERT INTO `pickups` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
conn.commit()

#player_pickups
print("Rebuilding player_pickups table...")
c.execute("SELECT `pickup_id`, `channel_id`, `user_id`, `user_name`, `pickup_name`, `at`, `team`, `is_ranked`, `is_winner`, `rank_after`, `rank_change`, `is_lastpick` FROM player_pickups")
data = c.fetchall()
c.execute("DROP TABLE player_pickups")
c.execute("CREATE TABLE `player_pickups` ( `pickup_id` INTEGER, `channel_id` INTEGER, `user_id` INTEGER, `user_name` TEXT, `pickup_name` TEXT, `at` INTEGER, `team` TEXT, `is_ranked` BOOL, `is_winner` BLOB, `rank_after` INTEGER, `rank_change` INTEGER, `is_lastpick` BLOB)")
c.executemany("INSERT INTO `player_pickups` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
conn.commit()

#bans
print("Rebuilding players table...")
c.execute("SELECT `user_id`, `default_expire`, `disable_pm` FROM `players`")
data = c.fetchall()
c.execute("DROP TABLE `players`")
c.execute("CREATE TABLE `players` ( `user_id` INTEGER, `default_expire` INTEGER, `disable_pm` BLOB, PRIMARY KEY(`user_id`) )")
c.executemany("INSERT INTO `players` VALUES (?, ?, ?)", data)
conn.commit()

print("Updating database version...")
c.execute("INSERT OR REPLACE INTO utility (variable, value) VALUES ('version', ?)", ('5', ))
conn.commit()

print("Database successfully updated!")
conn.close()
