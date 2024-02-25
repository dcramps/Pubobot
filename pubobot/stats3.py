#!/usr/bin/python2
import sqlite3
from datetime import timedelta
from time import time
from os.path import isfile
from decimal import Decimal

from . import console

# INIT
version = 13


conn = None
c = None
last_match = -1


def init(db_file="database.sqlite3"):
    global conn, c, last_match
    dbexists = isfile(db_file)

    if conn:
        conn.close()

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if dbexists:
        try:
            check_db()
        except Exception as e:
            console.display(e)
            console.terminate()
            return
    else:
        console.display("DATATBASE| Creating new database...")
        create_tables()

    c.execute("SELECT pickup_id from pickups ORDER BY pickup_id DESC LIMIT 1")
    result = c.fetchone()
    if result:
        last_match = result[0]
    else:
        last_match = -1


def get_channels():
    l = []
    c.execute("SELECT * from channels")
    chans = c.fetchall()
    l = []
    for chan in chans:
        l.append(dict(chan))

    for i in l:
        i["channel_id"] = i["channel_id"]
        i["server_id"] = i["server_id"]

    return l


def get_pickups(channel_id):
    c.execute("SELECT * from pickup_configs WHERE channel_id = ?", (channel_id,))
    pickups = c.fetchall()
    l = []
    for pickup in pickups:
        l.append(dict(pickup))
    return l


def get_pickup_groups(channel_id):
    c.execute(
        "SELECT group_name, pickup_names FROM pickup_groups WHERE channel_id = ?",
        (channel_id,),
    )
    pg = c.fetchall()
    d = dict()
    for i in pg:
        d[i[0]] = i[1].split(" ")
    return d


def new_pickup_group(channel_id, group_name, pickup_names):
    c.execute(
        "INSERT OR REPLACE INTO pickup_groups (channel_id, group_name, pickup_names) VALUES (?, ?, ?)",
        (channel_id, group_name, " ".join(pickup_names)),
    )
    conn.commit()


def delete_pickup_group(channel_id, group_name):
    c.execute(
        "DELETE FROM pickup_groups WHERE channel_id = ? AND group_name = ?",
        (channel_id, group_name),
    )
    conn.commit()


def new_channel(server_id, server_name, channel_id, channel_name, admin_id):
    c.execute(
        "INSERT OR REPLACE INTO channels (server_id, server_name, channel_id, channel_name, first_init, admin_id) VALUES (?, ?, ?, ?, ?, ?)",
        (server_id, server_name, channel_id, channel_name, str(int(time())), admin_id),
    )
    conn.commit()
    c.execute("SELECT * from channels WHERE channel_id = ?", (channel_id,))
    chan = c.fetchone()
    return dict(chan)


def new_pickup(channel_id, pickup_name, maxplayers):
    c.execute(
        "INSERT INTO pickup_configs (channel_id, pickup_name, maxplayers) VALUES (?, ?, ?)",
        (channel_id, pickup_name, maxplayers),
    )
    conn.commit()
    c.execute(
        "SELECT * from pickup_configs WHERE channel_id = ? AND pickup_name = ?",
        (channel_id, pickup_name),
    )
    result = c.fetchone()
    return dict(result)


def delete_pickup(channel_id, pickup_name):
    c.execute(
        "DELETE FROM pickup_configs WHERE channel_id = ? AND pickup_name = ? COLLATE NOCASE",
        (channel_id, pickup_name),
    )
    conn.commit()


def delete_channel(channel_id):
    c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM channel_players WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM bans WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM pickup_configs WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM player_pickups WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM pickups WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM pickup_groups WHERE channel_id = ?", (channel_id,))
    conn.commit()


def reset_stats(channel_id):
    c.execute("DELETE FROM pickups WHERE channel_id = ?", (channel_id,))
    c.execute("DELETE FROM player_pickups WHERE channel_id = ?", (channel_id,))
    conn.commit()


def undo_ranks(channel_id, match_id):
    c.execute(
        "SELECT user_id, user_name, rank_change, is_winner FROM player_pickups WHERE channel_id = ? AND pickup_id = ? AND is_ranked = 1",
        (channel_id, match_id),
    )
    l = c.fetchall()
    if len(l):
        c.execute(
            "UPDATE player_pickups SET is_ranked = 0 WHERE channel_id = ? AND pickup_id = ?",
            (channel_id, match_id),
        )
        for user_id, user_name, rank_change, is_winner in l:
            c.execute(
                "UPDATE channel_players SET rank=rank-(?), wins=wins-?, loses=loses-? WHERE channel_id = ? AND user_id = ?",
                (rank_change, is_winner, 1 - is_winner, channel_id, user_id),
            )
        conn.commit()
        return "\n".join(["`{0}` - **{1:+}** points".format(i[1], 0 - i[2]) for i in l])
    else:
        return "No changes made."


def seed_player(channel_id, user_id, rating):
    c.execute(
        "SELECT user_id FROM channel_players WHERE channel_id = ? AND user_id = ?",
        (channel_id, user_id),
    )
    if c.fetchone():
        c.execute(
            "UPDATE channel_players SET rank = ?, is_seeded = ? WHERE channel_id = ? AND user_id = ?",
            (rating, True, channel_id, user_id),
        )
    else:
        c.execute(
            "INSERT INTO channel_players (channel_id, user_id, rank, is_seeded) VALUES (?, ?, ?, ?)",
            (channel_id, user_id, rating, True),
        )


def reset_ranks(channel_id):
    c.execute(
        "UPDATE channel_players SET rank = NULL, wins = NULL, loses = NULL, streak = NULL, is_seeded = NULL WHERE channel_id = ?",
        (channel_id,),
    )
    conn.commit()


def register_pickup(match):
    new_ranks = dict()
    at = int(time())
    match.ranks = get_ranks(
        match.pickup.channel, [i.id for i in match.players]
    )  # Update players ratings incase of changes

    playersstr = " " + " ".join([i.nick or i.name for i in match.players]) + " "
    if match.alpha_team and match.beta_team:
        alphastr = " ".join([i.nick or i.name for i in match.alpha_team])
        betastr = " ".join([i.nick or i.name for i in match.beta_team])
    else:
        betastr = None
        alphastr = None

    c.execute(
        "INSERT INTO pickups (pickup_id, channel_id, pickup_name, at, players, alpha_players, beta_players, is_ranked, winner_team) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            match.id,
            match.pickup.channel.id,
            match.pickup.name,
            at,
            playersstr,
            alphastr,
            betastr,
            match.ranked,
            match.winner,
        ),
    )

    if match.ranked and match.winner:
        alpha_rank = int(
            sum([match.ranks[player.id] for player in match.alpha_team])
            / len(match.alpha_team)
        )
        beta_rank = int(
            sum([match.ranks[player.id] for player in match.beta_team])
            / len(match.beta_team)
        )

        # [alpha, beta]
        expected_scores = [
            1 / (1 + 10 ** ((beta_rank - alpha_rank) / 400)),
            1 / (1 + 10 ** ((alpha_rank - beta_rank) / 400)),
        ]
        if match.winner == "alpha":
            scores = [1, 0]
        elif match.winner == "draw":
            scores = [0.5, 0.5]
        else:
            scores = [0, 1]

    for player in [
        player for player in match.players if player not in match.unpicked_pool
    ]:
        user_name = player.nick or player.name
        team = None
        is_lastpick = player == match.lastpick  # True or False
        if match.alpha_team and match.beta_team:
            if player in match.alpha_team:
                team_num = 0
                team = "alpha"
            elif player in match.beta_team:
                team_num = 1
                team = "beta"

        if match.ranked and match.winner and team:
            c.execute(
                "INSERT OR IGNORE INTO channel_players (channel_id, user_id, nick, rank, wins, loses, phrase) VALUES (?, ?, ?, ?, 0, 0, NULL)",
                (match.pickup.channel.id, player.id, user_name, match.ranks[player.id]),
            )

            # if we need to calibrate this player add additional rank gain/loss boost
            rank_k = match.pickup.channel.cfg["ranked_multiplayer"]
            c.execute(
                "SELECT wins, loses, streak, is_seeded FROM channel_players WHERE channel_id = ? AND user_id = ?",
                (match.pickup.channel.id, player.id),
            )
            result = c.fetchone()
            wins, loses, streak, is_seeded = [i or 0 for i in result]

            is_ranked = True
            rank_change = int(rank_k * (scores[team_num] - expected_scores[team_num]))
            if (
                match.pickup.channel.cfg["ranked_calibrate"]
                and wins + loses < 8
                and not is_seeded
            ):
                rank_change = int(rank_change * ((10 - (wins + loses)) / 2.0))

            if match.ranked_streaks:
                if streak.__gt__(0) != scores[team_num].__gt__(0):
                    streak = 0
                if scores[team_num] == 1:
                    streak += 1
                elif scores[team_num] == 0.5:
                    streak = 0
                else:
                    streak -= 1
                if abs(streak) > 2:
                    rank_change = int(rank_change * (min([abs(streak), 6]) / 2.0))
            else:
                streak = 0

            rank_after = match.ranks[player.id] + rank_change
            is_winner = scores[team_num]

            c.execute(
                "UPDATE channel_players SET nick = ?, rank = ?, wins=?, loses=?, streak=? WHERE channel_id = ? AND user_id = ?",
                (
                    user_name,
                    rank_after,
                    wins + scores[team_num],
                    loses + abs(scores[team_num] - 1),
                    streak,
                    match.pickup.channel.id,
                    player.id,
                ),
            )
            new_ranks[player.id] = [user_name, rank_after]

        else:
            is_ranked = False
            rank_change = None
            rank_after = None
            is_winner = None

        c.execute(
            "INSERT OR IGNORE INTO player_pickups (pickup_id, channel_id, user_id, user_name, pickup_name, at, team, is_ranked, is_winner, rank_after, rank_change, is_lastpick) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                match.id,
                match.pickup.channel.id,
                player.id,
                user_name,
                match.pickup.name,
                at,
                team,
                is_ranked,
                is_winner,
                rank_after,
                rank_change,
                is_lastpick,
            ),
        )

    conn.commit()
    return new_ranks


def lastgame(channel_id, text=False):  # [id, gametype, ago, [players], [caps]]
    if not text:  # return lastest game
        c.execute(
            "SELECT pickup_id, at, pickup_name, players, alpha_players, beta_players, winner_team FROM pickups WHERE channel_id = ? ORDER BY pickup_id DESC LIMIT 1",
            (channel_id,),
        )
        result = c.fetchone()
    else:
        # try to find last game by gametype
        c.execute(
            "SELECT pickup_id, at, pickup_name, players, alpha_players, beta_players, winner_team FROM pickups WHERE channel_id = ? and pickup_name = ? ORDER BY pickup_id DESC LIMIT 1 COLLATE NOCASE",
            (channel_id, text),
        )
        result = c.fetchone()
        if result == None:  # no results, try to find last game by player
            c.execute(
                "SELECT pickup_id, at, pickup_name, players, alpha_players, beta_players, winner_team FROM pickups WHERE channel_id = '{0}' and players LIKE '% {1} %' ORDER BY pickup_id DESC LIMIT 1".format(
                    channel_id, text
                )
            )
            result = c.fetchone()
    return result


def get_ranks(channel, user_ids):
    d = dict()
    c.execute(
        "SELECT user_id, rank FROM channel_players WHERE channel_id = ? AND user_id in ({seq})".format(
            seq=",".join(["?"] * len(user_ids))
        ),
        (channel.id, *user_ids),
    )
    results = c.fetchall()
    for user_id, rank in results:
        if rank:
            d[user_id] = rank
    for user_id in user_ids:
        if user_id not in d.keys():
            d[user_id] = channel.cfg["initial_rating"] or 1400
    return d


def get_rank_details(channel_id, user_id=False, nick=False):
    c.execute(
        "SELECT user_id, nick, rank, wins, loses FROM channel_players WHERE channel_id = ? AND rank IS NOT NULL ORDER BY rank DESC",
        (channel_id,),
    )
    lb = c.fetchall()
    for i in lb:
        if i[0] == user_id or i[1].lower() == nick:
            c.execute(
                "SELECT pickup_id, at, pickup_name, rank_change FROM player_pickups WHERE user_id = ? AND channel_id = ? AND is_ranked = 1 ORDER BY pickup_id DESC LIMIT 3",
                (i[0], channel_id),
            )
            matches = c.fetchall()
            place = lb.index(i) + 1
            i = list(i)
            i[0] = place  # replace user_id with ladder position
            print(i)
            return [i, matches]
    return [None, None]


def get_ladder(channel_id, page):
    c.execute(
        "SELECT rank, nick, wins, loses FROM channel_players WHERE channel_id = ? AND rank IS NOT NULL AND wins+loses > 0 ORDER BY rank desc LIMIT ?",
        (channel_id, (page + 1) * 10),
    )
    return c.fetchall()[page * 10 :]


def stats(channel_id, text=False):
    if not text:  # return overall stats
        c.execute(
            "SELECT pickup_name, count(pickup_name) FROM pickups WHERE channel_id = ? GROUP BY pickup_name",
            (channel_id,),
        )
        l = c.fetchall()
        if l != None:
            pickups = []
            total = 0
            for i in l:
                pickups.append("{0}: {1}".format(i[0], i[1]))
                total += i[1]
            return "Total pickups: {0} | {1}".format(total, ", ".join(pickups))
        else:
            return "No pickups played yet."  ###STOP###
    else:
        # get total pickups count
        c.execute(
            "SELECT count(channel_id) FROM pickups WHERE channel_id = ? GROUP BY channel_id",
            (channel_id,),
        )
        l = c.fetchone()
        if l != None:
            total = l[0]
        else:
            return "No pickups played yet."

        # try to find by pickup_name
        c.execute(
            "SELECT pickup_name, count(pickup_name) FROM pickups WHERE channel_id = ? AND pickup_name = ? COLLATE NOCASE GROUP BY pickup_name ",
            (channel_id, text),
        )
        l = c.fetchone()
        if l != None:
            percent = int((float(l[1]) / total) * 100)
            return "Stats for **{0}**. Played: {1} ({2}%).".format(l[0], l[1], percent)
        else:
            # try to find by user_name
            c.execute(
                "SELECT user_id, user_name FROM player_pickups WHERE channel_id = ? AND user_name = ? COLLATE NOCASE ORDER BY rowid DESC LIMIT 1",
                (channel_id, text),
            )
            l = c.fetchone()
            if l != None:
                user_id = l[0]
                user_name = l[1]
            else:
                return "Nothing found."

            c.execute(
                "SELECT pickup_name, count(pickup_name) FROM player_pickups WHERE channel_id = ? AND user_id = ? GROUP BY pickup_name",
                (channel_id, user_id),
            )
            l = c.fetchall()
            pickups = []
            user_total = 0
            for i in l:
                pickups.append("{0}: {1}".format(i[0], i[1]))
                user_total += i[1]
            percent = int((float(user_total) / total) * 100)
            return "Stats for **{0}**. Played {1} ({2}%): {3}".format(
                user_name, user_total, percent, ", ".join(pickups)
            )


def top(channel_id, timegap=False, pickup=False):
    if timegap and pickup:
        c.execute(
            "SELECT user_name, count(user_id) FROM player_pickups WHERE channel_id = ? and pickup_name = ? and at > ? GROUP BY user_id ORDER by count(user_id) DESC LIMIT 10",
            (channel_id, pickup, timegap),
        )
    elif timegap:
        c.execute(
            "SELECT user_name, count(user_id) FROM player_pickups WHERE channel_id = ? and at > ? GROUP BY user_id ORDER by count(user_id) DESC LIMIT 10",
            (channel_id, timegap),
        )
    elif pickup:
        c.execute(
            "SELECT user_name, count(user_id) FROM player_pickups WHERE channel_id = ? and pickup_name = ? GROUP BY user_id ORDER by count(user_id) DESC LIMIT 10",
            (channel_id, pickup),
        )
    else:
        c.execute(
            "SELECT user_name, count(user_id) FROM player_pickups WHERE channel_id = ? GROUP BY user_id ORDER by count(user_id) DESC LIMIT 10",
            (channel_id,),
        )

    l = c.fetchall()
    if len(l):
        top = ["{0}: {1}".format(i[0], i[1]) for i in l]
        return ", ".join(top)
    return None


def noadd(channel_id, user_id, user_name, duratation, author_name, reason=""):
    c.execute(
        "SELECT * FROM bans WHERE user_id = ? AND channel_id = ? AND active = 1",
        (user_id, channel_id),
    )
    ban = c.fetchone()
    if ban != None:
        c.execute(
            "UPDATE bans SET at=?, duratation=?, author_name=?, reason=? WHERE user_id = ? AND channel_id = ? AND active = 1",
            (int(time()), duratation, author_name, reason, user_id, channel_id),
        )
        conn.commit()
        return "Updated {0}'s noadd to {1} from now.".format(
            user_name, str(timedelta(seconds=duratation))
        )
    else:
        # add new ban
        c.execute(
            "INSERT INTO bans (channel_id, user_id, user_name, active, at, duratation, reason, author_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                channel_id,
                user_id,
                user_name,
                1,
                int(time()),
                duratation,
                reason,
                author_name,
            ),
        )
        conn.commit()
        # Get a quote!
        c.execute("SELECT * FROM nukem_quotes ORDER BY RANDOM() LIMIT 1")
        quote = c.fetchone()
        return "Banned {0} for {1}. {2}".format(
            user_name, str(timedelta(seconds=duratation)), quote[0]
        )


def forgive(channel_id, user_id, user_name, unban_author_name):
    c.execute(
        "SELECT * FROM bans WHERE user_id = ? AND channel_id = ? AND active = 1",
        (user_id, channel_id),
    )
    ban = c.fetchone()
    if ban != None:
        c.execute(
            "UPDATE bans SET active = 0, unban_author_name = ? WHERE user_id = ? AND channel_id = ? AND active = 1",
            (unban_author_name, user_id, channel_id),
        )
        conn.commit()
        return "{0} forgiven.".format(user_name)
    return "Ban not found!"


def noadds(channel_id, index=None):
    if index == None:
        c.execute(
            "SELECT user_name, active, at, duratation, reason, author_name, unban_author_name FROM bans WHERE channel_id = ? AND active = 1",
            (channel_id,),
        )
    else:
        c.execute(
            "SELECT user_name, active, at, duratation, reason, author_name, unban_author_name FROM bans WHERE channel_id = ? ORDER BY at DESC LIMIT ?",
            (channel_id, index + 10),
        )
    bans = c.fetchall()
    bans_str = []
    for ban in bans[0:10]:
        if ban[1] == 1:
            timeleft = timedelta(seconds=int(ban[3] - (time() - ban[2])))
            # user_name, timeleft, author: reason
            bans_str.append(
                "{0}, {1} left, by {2}: {3}".format(ban[0], timeleft, ban[5], ban[4])
            )
        else:
            ago = timedelta(seconds=int(time() - ban[2]))
            # user_name, ago, author (reason), unban_author
            bans_str.append(
                "{0}, {1} ago, by {2} ({3}), unbanned by {4}".format(
                    ban[0], ago, ban[5], ban[4], ban[6]
                )
            )
    return bans_str


def check_memberid(channel_id, user_id):  # check on bans and phrases
    # returns (bool is_banned, string phrase, int default_expire)

    # check if he is banned
    unbanned = False
    c.execute(
        "SELECT at, duratation, reason FROM bans WHERE user_id = ? AND channel_id = ? AND active = 1",
        (user_id, channel_id),
    )
    ban = c.fetchone()
    if ban:
        ban = list(ban)
        seconds_left = int(ban[1] - (time() - ban[0]))
        if seconds_left > 0:
            timeleft = timedelta(seconds=seconds_left)
            if ban[2] != "":
                ban[2] = " Reason : {0}".format(ban[2])
            return (
                True,
                "You have been banned. {0} time left.{1}".format(timeleft, ban[2]),
                None,
            )
        else:
            c.execute(
                "UPDATE bans SET active = 0, unban_author_name = ? WHERE user_id = ? AND channel_id = ? AND active = 1",
                ("time", user_id, channel_id),
            )
            conn.commit()
            return (False, "Be nice next time, please.", None)

    # no bans, find phrases!
    c.execute("SELECT default_expire FROM players WHERE user_id = ?", (user_id,))
    l = c.fetchone()
    if l:
        expire = l[0]
    else:
        expire = None
    c.execute(
        "SELECT phrase FROM channel_players WHERE user_id = ? AND channel_id = ?",
        (user_id, channel_id),
    )
    l = c.fetchone()
    if l:
        phrase = l[0]
    else:
        phrase = None

    return (False, phrase, expire)


# get default user !expire time
def get_expire(user_id):
    c.execute("SELECT default_expire FROM players WHERE user_id = ?", (user_id,))
    l = c.fetchone()
    if l:
        return l[0]
    else:
        return None


# set default user !expire time
def set_expire(user_id, seconds):
    # create user if not exists
    c.execute("INSERT OR IGNORE INTO players (user_id) VALUES (?)", (user_id,))
    c.execute(
        "UPDATE players SET default_expire = ? WHERE user_id = ?", (seconds, user_id)
    )
    conn.commit()


def set_phrase(channel_id, user_id, phrase):
    # create user if not exists
    c.execute(
        "INSERT OR IGNORE INTO channel_players (channel_id, user_id) VALUES (?, ?)",
        (channel_id, user_id),
    )
    c.execute(
        "UPDATE channel_players SET phrase = ? WHERE user_id = ? AND channel_id = ?",
        (phrase, user_id, channel_id),
    )
    conn.commit()


def save_config(channel_id, cfg, pickups):
    c.execute(
        "INSERT OR REPLACE INTO channels VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (*cfg.values(),),
    )
    for i in pickups:
        c.execute(
            "INSERT OR REPLACE INTO pickup_configs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                channel_id,
                i.name,
                i.maxplayers,
                i.minplayers,
                i.startmsg,
                i.maps,
                i.teams_pick_system,
                i.promotion_role,
                i.blacklist_role,
                i.whitelist_role,
            ),
        )
    conn.commit()


def update_channel_config(channel_id, variable, value):
    c.execute(
        'UPDATE OR IGNORE channels SET "{0}" = ? WHERE channel_id = ?'.format(variable),
        (value, channel_id),
    )
    conn.commit()


def update_pickup_config(channel_id, pickup_name, variable, value):
    c.execute(
        'UPDATE OR IGNORE pickup_configs SET "{0}" = ? WHERE channel_id = ? and pickup_name = ?'.format(
            variable
        ),
        (value, channel_id, pickup_name),
    )
    conn.commit()


def update_pickups(channel_id, pickups):
    for i in pickups:
        c.execute(
            "INSERT OR REPLACE INTO pickup_configs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                channel_id,
                i.name,
                i.maxplayers,
                i.minplayers,
                i.startmsg,
                i.maps,
                i.teams_pick_system,
                i.promotion_role,
                i.blacklist_role,
                i.whitelist_role,
            ),
        )
    conn.commit()


def check_db():
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [i[0] for i in c.fetchall()]

    if "utility" not in tables:
        c.execute(
            """CREATE TABLE `utility`
            ( `variable` TEXT,
            `value` TEXT,
            PRIMARY KEY(`variable`) )"""
        )

    c.execute("SELECT value FROM utility WHERE variable='version'")
    db_version = c.fetchone()
    if db_version:
        db_version = Decimal(db_version[0])
    else:
        db_version = -1

    if db_version < version:
        console.display(
            "DATABASE| Updating database from '{0}' to '{1}'...".format(
                db_version, version
            )
        )
        if db_version < 2:
            c.execute(
                """ALTER TABLE `pickup_configs`
            ADD COLUMN `allow_offline` INTEGER DEFAULT 0
            """
            )
        if db_version < 3:
            c.execute(
                """ALTER TABLE `pickup_configs`
            ADD COLUMN `promotemsg` TEXT
            """
            )
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `promotemsg` TEXT
            """
            )

        if db_version < 4:
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `ranked_multiplayer` INTEGER DEFAULT 32;
            """
            )
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `ranked_calibrate` INTEGER DEFAULT 1;
            """
            )

            c.execute(
                """ALTER TABLE `pickups`
            ADD COLUMN `is_ranked` BOOL"""
            )

            c.execute(
                """ALTER TABLE `player_pickups`
            ADD COLUMN `is_ranked` BOOL"""
            )
            c.execute(
                """ALTER TABLE `player_pickups`
            ADD COLUMN `rank_after` INTEGER"""
            )
            c.execute(
                """ALTER TABLE `player_pickups`
            ADD COLUMN `rank_change` INTEGER"""
            )

            # rename points to rank and add wins and loses counters
            c.executescript(
                """ALTER TABLE channel_players RENAME TO tmp_channel_players;
            CREATE TABLE channel_players(`channel_id` TEXT, `user_id` TEXT, `nick` TEXT, `rank` INTEGER, `wins` INTEGER, `loses` INTEGER, `phrase` TEXT, PRIMARY KEY(`channel_id`, `user_id`));
            INSERT INTO channel_players(channel_id, user_id, phrase) SELECT channel_id, user_id, phrase FROM tmp_channel_players;
            DROP TABLE tmp_channel_players"""
            )

        if db_version < 5:
            # got to change all the ID's to INTEGER from TEXT to migrate to discord.py 1.0+
            if db_version < 4:
                c.execute(
                    "INSERT OR REPLACE INTO utility (variable, value) VALUES ('version', ?)",
                    (str(version),),
                )
                conn.commit()

            raise (
                Exception(
                    "In order to migrate to discord.py 1.0+ database tables must be rebuilded. Please backup your database (database.sqlite3 file) and run updater.py."
                )
            )

        if db_version < 6:
            # add custom team emojis
            c.execute(
                """ALTER TABLE `pickup_configs`
            ADD COLUMN `team_emojis` TEXT
            """
            )
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `team_emojis` TEXT
            """
            )

        if db_version < 7:
            c.execute(
                """ALTER TABLE `channel_players`
            ADD COLUMN `streak` INTEGER
            """
            )
            c.execute(
                """ALTER TABLE `channel_players`
            ADD COLUMN `is_seeded` BLOB
            """
            )

        if db_version < 8:
            # add custom team names
            c.execute(
                """ALTER TABLE `pickup_configs`
            ADD COLUMN `team_names` TEXT
            """
            )
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `team_names` TEXT
            """
            )

        if db_version < 9:
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `global_expire` INTEGER
            """
            )
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `ranked_streaks` INTEGER DEFAULT 1
            """
            )

        if db_version < 10:
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `match_livetime` INTEGER
            """
            )

        if db_version < 11:
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `initial_rating` INTEGER
            """
            )

        if db_version < 12:
            c.execute(
                """ALTER TABLE `channels`
            ADD COLUMN `autostart` INTEGER DEFAULT 1
            """
            )
            c.execute(
                """ALTER TABLE `pickup_configs`
            ADD COLUMN `autostart` INTEGER
            """
            )

        if db_version < 13:
            c.execute(
                """ALTER TABLE `channels`
                ADD COLUMN `capfor_enabled` INT DEFAULT 1
                """
            )

        c.execute(
            "INSERT OR REPLACE INTO utility (variable, value) VALUES ('version', ?)",
            (str(version),),
        )
        conn.commit()


def create_tables():
    c.execute(
        """CREATE TABLE `utility`
        ( `variable` TEXT,
        `value` TEXT,
        PRIMARY KEY(`variable`) )"""
    )

    c.execute(
        """CREATE TABLE `bans`
        ( `channel_id` INTEGER,
        `user_id` INTEGER,
        `user_name` TEXT,
        `active` BLOB,
        `at` INTEGER,
        `duratation` INTEGER,
        `reason` TEXT,
        `author_name` TEXT,
        `unban_author_name` TEXT )"""
    )

    c.execute(
        """CREATE TABLE `channel_players`
        ( `channel_id` INTEGER,
        `user_id` INTEGER,
        `nick` TEXT,
        `rank` INTEGER,
        `wins` INTEGER,
        `loses` INTEGER,
        `streak` INTEGER,
        `is_seeded` BLOB,
        `phrase` TEXT,
        PRIMARY KEY(`channel_id`, `user_id`) )"""
    )

    c.execute(
        """CREATE TABLE `channels`
        ( `server_id` INTEGER,
        `server_name` TEXT,
        `channel_id` INTEGER,
        `channel_name` TEXT,
        `premium` BOOL,
        `first_init` INTEGER,
        `admin_id` INTEGER,
        `admin_role` INTEGER,
        `moderator_role` INTEGER,
        `captains_role` INTEGER,
        `noadd_role` INTEGER,
        `prefix` TEXT DEFAULT '!',
        `default_bantime` INTEGER DEFAULT 7200,
        `++_req_players` INTEGER DEFAULT 5,
        `startmsg` TEXT,
        `submsg` TEXT,
        `promotemsg` TEXT,
        `ip` TEXT,
        `password` TEXT,
        `maps` TEXT,
        `pick_captains` INTEGER,
        `team_emojis` TEXT,
        `team_names` TEXT,
        `pick_teams` TEXT DEFAULT 'no_teams',
        `pick_order` TEXT,
        `promotion_role` INTEGER,
        `promotion_delay` INTEGER DEFAULT 18000,
        `blacklist_role` INTEGER,
        `whitelist_role` INTEGER,
        `require_ready` INTEGER,
        `ranked` INTEGER,
        `ranked_multiplayer` INTEGER DEFAULT 32,
        `ranked_calibrate` INTEGER DEFAULT 1,
        `ranked_streaks` INTEGER DEFAULT 1,
        `initial_rating` INTEGER,
        `match_livetime` INTEGER,
        `global_expire` INTEGER,
        `autostart` INTEGER DEFAULT 1,
        `help_answer` TEXT,
        `start_pm_msg` TEXT DEFAULT '**%pickup_name%** pickup has been started @ %channel%.',
                `capfor_enabled` INTEGER DEFAULT 1,
        PRIMARY KEY(`channel_id`) )"""
    )

    c.execute(
        """CREATE TABLE `pickup_configs`
        ( `channel_id` INTEGER,
        `pickup_name` TEXT,
        `maxplayers` INTEGER,
        `minplayers` INTEGER,
        `startmsg` TEXT,
        `start_pm_msg` TEXT,
        `submsg` TEXT,
        `promotemsg` TEXT,
        `ip` TEXT,
        `password` TEXT,
        `maps` TEXT,
        `pick_captains` INTEGER,
        `captains_role` INTEGER,
        `team_emojis` TEXT,
        `team_names` TEXT,
        `pick_teams` TEXT,
        `pick_order` TEXT,
        `promotion_role` INTEGER,
        `blacklist_role` INTEGER,
        `whitelist_role` INTEGER,
        `captain_role` INTEGER,
        `require_ready` INTEGER,
        `ranked` INTEGER,
        `allow_offline` INTEGER DEFAULT 0,
        `autostart` INTEGER,
        `help_answer` TEXT,
        PRIMARY KEY(`channel_id`, `pickup_name`) )"""
    )

    c.execute(
        """CREATE TABLE `pickups`
        ( `pickup_id` INTEGER PRIMARY KEY,
        `channel_id` INTEGER,
        `pickup_name` TEXT,
        `at` INTEGER,
        `players` TEXT,
        `alpha_players` TEXT,
        `beta_players` TEXT,
        `is_ranked` BOOL,
        `winner_team` TEXT )"""
    )

    c.execute(
        """CREATE TABLE `player_pickups`
        ( `pickup_id` INTEGER,
        `channel_id` INTEGER,
        `user_id` INTEGER,
        `user_name` TEXT,
        `pickup_name` TEXT,
        `at` INTEGER,
        `team` TEXT,
        `is_ranked` BOOL,
        `is_winner` BLOB,
        `rank_after` INTEGER,
        `rank_change` INTEGER,
        `is_lastpick` BLOB)"""
    )

    c.execute(
        """CREATE TABLE `players`
        ( `user_id` INTEGER,
        `default_expire` INTEGER,
        `disable_pm` BLOB,
        PRIMARY KEY(`user_id`) )"""
    )

    c.execute(
        """CREATE TABLE `pickup_groups`
        ( `channel_id` INTEGER,
        `group_name` TEXT,
        `pickup_names` TEXT,
        PRIMARY KEY(`channel_id`, `group_name`) )"""
    )

    c.execute("""CREATE TABLE `nukem_quotes` ( `quote` TEXT )""")
    c.executemany(
        """INSERT INTO nukem_quotes ('quote') VALUES (?)""",
        [
            ["AAhhh... much better!"],
            ["Bitchin'!"],
            ["Come get some!"],
            ["Do, or do not, there is no try."],
            ["Eat shit and die."],
            ["Get that crap outta here!"],
            ["Go ahead, make my day."],
            ["Hail to the king, baby!"],
            ["Heh, heh, heh... what a mess!"],
            ["Holy cow!"],
            ["Holy shit!"],
            ["I'm gonna get medieval on your asses!"],
            ["I'm gonna kick your ass, bitch!"],
            ["Let God sort 'em out!"],
            ["Ooh, that's gotta hurt."],
            ["See you in Hell!"],
            ["Piece of Cake."],
            ["Suck it down!"],
            ["Terminated!"],
            ["Your face, your ass - what's the difference?"],
            ["Nobody fucks up our pickups... and lives!"],
            ["My boot, your face; the perfect couple."],
        ],
    )

    c.execute(
        "INSERT INTO utility (variable, value) VALUES ('version', ?)", (str(version),)
    )
    conn.commit()


def close():
    conn.commit()
    conn.close()
