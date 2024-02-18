## Avaible commands:
### ACTONS:
!add <i>pickup</i>[ <i>pickup</i> ..]] or +<u>pickup</u>[ <i>pickup</i> ..]] - adds you to specified pickups.   
!add or ++ - adds you to all active pickups.    
!remove <i>pickup</i>[ <i>pickup</i> ...] or -[<i>pickup</i>[ <i>pickup</i> ..]] - removes you from specified pickups.   
!remove or -- - removes you from all pickups.   
!expire <i>time</i> - Sets new time delay after you will be removed from all pickups, example: '!expire 1h 2m 3s'.   
!default_expire <i>time</i>, 'afk' or 'none' - Set your personal default !expire time or set autoremove on afk status.   
!sub - request sub for last game.   
!allowoffline or !ao - gives you immune from getting removed by offline or afk statuses until a pickup with you starts. (done for mobile devices users).   
!subscribe <i>pickup</i>[ <i>pickup</i> ..]] - adds the promotion role of specified pickup(s) to you.   
!unsubscribe <i>pickup</i>[ <i>pickup</i> ..]] - removes the promotion role of specified pickup(s) from you.   

### INFO:
!who [<i>pickup</i>[ <i>pickup</i> ...]] - list of users added to a pickups.   
!pickups - list of all pickups on the channel.   
!pickup_groups - list of pickup groups configured on the channel.   
!expire - shows you how much time left before you will be removed from all pickups.   
!lastgame [<i>@nick</i> or <i>pickup</i>] - show last pickup, or last pickup by specified argument.   
!top [<i>pickup<i>] [weekly or monthly or yearly] - shows you most active players.   
!stats [<i>nick</i> or <i>pickup</i>] - shows you overall stats or stats for specified argument.   
!ip [<i>pickup</i> or default] - shows you ip of last pickup or specified pickup.   
!map <i>pickup</i> - print a random map for specified pickup.   
!maps <i>pickup</i> - show all maps for specified pickup.   

### TEAMS PICKING:
!cointoss or !ct [heads or tails] - toss a coin.   
!pick <i>@nick</i> - pick a user to your team.   
!put <i>@nick</i> alpha or beta - put player in specified team (availible only for users with moderator or admin rights).   
!subfor <i>@nick</i> - become a substitute for specified player.   
!capfor alpha or beta - become a captain of specified team.   
!teams - show teams for current pickup.   

### RANKING
!leaderboard [page] or !lb [page] - show top players by rating.   
!rank - show your rating stats.   
!reportlose or !rl - report loss on your current match (avalible for captains only).  
!reportdraw !draw or !rd - report draw on your current match (avalible for captains only, captain of other team has to confirm).  
!reportcancel or !rc - report cancel on your current match (avalible for captains only, captain of other team has to confirm).  
!matches - show all active matches on the channel.   
!ranks_table - show rank to rating table.   
##### For moderators and above:
!reportwin or !rw <i>match_id</i> alpha or beta - report win on specified match for specified team.   
!undo_ranks <i>match_id</i> - undo all rating changes for a previously reported match.   
!seed <i>@nick</i> <i>rating</i> - set specified player's rating points, also this will disable initial rating calibration for this user.    
##### For admins:
!reset_ranks - reset all rating data on the channel. <b>Warning, this action is irreversible!</b>   

### MODERATION:
!noadd <i>@nick</i> [<i>time</i>] [<i>reason</i>] - disallow user to play pickups.   
!noadds - show list of users who are disallowed to play pickups.   
!forgive <i>@nick</i> - allow user from noadds list to play pickups.   
!phrase <i>@nick</i> <i>text</i> - set specified reply for specified user after !add command.   
!remove_player <i>@nick</i> - remove specified players from all pickups.   
!reset - removes all players from all pickups.   
!start <i>pickup</i> - force a pickup to start with deficient players count.   
!cancel_match <i>match_id</i> - cancel an active match, match_id can be found at the beginning of pickup start message.   

### CONFIGURATION:
!enable_pickups - turn on the pickup bot on the channel.   
!disable_pickups - turn off the bot and delete all configurations/stats on the channel. <b>Warning, this action is irreversible!</b>   
!add_pickups <i>name</i>:<i>players</i>[ <i>name</i>:<i>players</i> ...] - create new pickups.   
!remove_pickups <i>pickup</i>[ <i>pickup</i> ...] - delete specified pickups.   
!add_pickup_group <i>group_name</i> <i>pickup</i>[ <i>pickup</i>...] - create a pickup group wich will contain specified pickups.
!remove_pickup_group <i>group_name</i> - delete specified pickup group.   
!reset_stats - delete all channel statistics.   
!cfg - show global channel configuration variables.   
!pickup_cfg <i>pickup</i> - show specified pickup configuration variables.   
!set_ao_for_all <i>name</i> 0|1 - allow/disallow offline for all users of specific pickup kind.

!set_default variable value - set a global variable value. Availible variables: admin_role, moderator_role, captains_role, prefix, default_bantime, ++_req_players, startmsg, submsg, ip, password, maps, pick_captains, pick_teams, promotion_role, promotion_delay, blacklist_role, whitelist_role, require_ready, ranked, ranked_calibrate, ranked_multiplayer, help_answer.   

!set_pickups <i>pickup</i>[ <i>pickup</i>...] variable value - set variables for specified pickups. Availible variables: maxplayers, startmsg, submsg, ip, password, maps, pick_captains, pick_teams, pick_order, promotion_role, blacklist_role, whitelist_role, captains_role, require_ready, ranked, help_answer.   

##### CONFIGURATION VARIABLES:
* For any variable set 'none' value to disable.
* admin_role <i>role_name</i> - users with this role will have access to configuration and moderation commands.
* moderator_role <i>role_name</i> - users with this role will have access to moderation commands.
* captains_role <i>role_name</i> - random captains will be preffered to this role, also '!capfor' command will be only availible for users with this role if its set.
* prefix <i>symbol</i> - set prefix before all bot's commands, default '!'.
* default_bantime <i>time</i> - set default time for !noadd command.
* ++_req_players <i>number</i> - set minimum pickup required players amount for '++' command or '!add' command without argument, so users wont add to 1v1/2v2 pickups unintentionally. Default value: 5.
* startmsg <i>text</i> - set message on a pickup start. Use %ip% and %password% in <i>text</i> to represent ip and password.
* start_pm_msg <i>text</i> - set private message on a pickup start. Use %pickup_name%, %ip%, %password% and %channel% to represent its values.
* submsg <i>text</i> - set message on !sub command. Use %pickup_name%, %ip%, %password% and %promotion_role% to represent its values.
* promotemsg <i>text</i> - set message on !promote command. Use %promotion_role%, %pickup_name% and %required_players% to represent its values.
* ip <i>text</i> - set ip wich will be shown in startmsg, submsg and on !ip command.
* password <i>text</i> - set password wich will be shown in startmsg, submsg and on !ip command.
* maps <i>map_name</i>[, <i>map_name</i>...] - set maps.
* pick_captains 0, 1, 2 or 3 - set if bot should suggest captains.
  * if variable ranked is 0:
    * 0 - doesn't suggest captains
    * 1 - picks captains randomly but with preference of player having captain role
    * 2 - picks captains randomly
  * if variable ranked is 1:
    * 0 - doesn't suggest captains
    * 1 - sorts players by player having captain role and player rank and picks two players from top
    * 2 - sorts players by player rank and picks random pair of adjacent players
    * 3 - picks captains randomly
* pick_teams <i>value</i> -  set teams pick system the bot should use. Value must be in 'no_teams', 'auto' or 'manual'.
  * no_teams - bot will only print players list and captains if needed.
  * auto - bot will print teams balanced by rating on ranked pickups or random teams.
  * manual - users will have to pick teams using teams picking commands.
* team_emojis <i>emoji</i> <i>emoji</i> - set custom team emojis.
* team_names <i>alpha_name</i> <i>beta_name</i> - set custom team names (commands with team names will change accordingly).
* pick_order <i>order</i> - force specified teams picking order. Example value: 'abababba'.
* promotion_role <i>role_name</i> - set promotion_role to highlight on !promote and !sub commands.
* promotion_delay <i>time</i> - set time delay between !promote and !sub commands can be used.
* blacklist_role <i>role_name</i> - users with this role will not be able to add to specified pickups.
* whitelist_role <i>role_name</i> - only users with this role will be able to add to specified pickups.
* require_ready none or <i>time</i> - if set users will have to confirm themselves using '!ready' command.
* ranked 0 or 1 - set pickup(s) to have rating system and make players have to report their matches.
* ranked_calibrate 0 or 1 - set to enable rating boost on first 10 user's matches, default on. Only for 'set_default'.
* ranked_multiplayer 8 to 256 - change rating K-factor (gain/loss multiplyer), default 32. Only for 'set_default'.
* ranked_streaks 1 or 0 - set to enable ranked streaks (starting from x1.5 for (3 wins/loses in a row) to x3.0 (6+ wins/loses in a row))
* initial_rating <i>integer</i> - set starting rating for new players (default is 1400).
* global_expire <i>time</i>, afk or none - set default_expire value for users without personal settings.
* match_livetime <i>time</i> - set a timelimit before a match gets aborted as timed out.
* help_answer <i>text</i> - set an answer on !help command.
