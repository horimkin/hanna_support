import sys
import os
import re
import json
import click
from datetime import datetime, timedelta
from dateutil.tz import gettz
import discord


def is_hanna(user):
    return user.id == 629495625284714506


def get_left_hour():
    if now.day == date_end.day and 5 <= now.hour:
        total = 24
    elif 0 <= now.hour < 5:
        total = 5
    else:
        total = 24 + 5
    return total - now.hour


def get_today():
    return now.day - 1 if 0 <= now.hour < 5 else now.day


def is_today(str_):
    """
    入力例)10月28日の凸状況です
    ハンナでは年まで表示されないので数値を取り出して比較する
    """
    month_day = re.findall(r"(\d+)月(\d+)日", str_)
    month_day = [int(i) for i in month_day[0]]
    today_m_d = [now.month, now.day]
    yesterday = now - timedelta(days=1)
    yesterday_m_d = [yesterday.month, yesterday.day]

    if month_day == today_m_d:
        # 5時〜23時
        return now
    elif month_day == yesterday_m_d and 0 <= now.hour < 5:
        # 0時〜4時
        return yesterday
    else:
        # 5時移行まだハンナが更新されていない or
        # しばらく起動していない
        print("ハンナ停止中")
        return


def is_first_time():
    return now.hour == 5 and now.day == date_start.day


def is_finished(user):
    mark = "# 残り0凸"
    index = progress.find(mark)
    if 0 < progress.find("- %s\t" % user.name, index + len(mark)):
        return True


def is_over(name):
    return re.search(r"^- %s\t.*持ち越し.*" % name, progress, flags=re.MULTILINE)


def create_remain_message():
    if not progress:
        # ガード
        return
    elif not is_today((progress.split())[1]):
        return

    left = re.findall(r" 残り.凸 \((\d+)+名\)", progress, flags=re.MULTILINE)
    left.reverse()
    left_all = sum([int(x) * i for i, x in enumerate(left)][1:4])
    if left_all == 0:
        print("全員3凸済みの為スキップ")
        return

    left_hour = get_left_hour()

    send_message = "%sの残凸状況\n" % now.strftime('%Y/%m/%d %H時') + \
        "3凸：%s人\n" % left[3] + \
        "2凸：%s人\n" % left[2] + \
        "1凸：%s人\n" % left[1] + \
        "あと%d時間で%d凸\n" % (left_hour, left_all) + \
        "1時間あたり%0.2f凸必要です" % round(left_all / left_hour, 2)

    return send_message


def create_reminder_mesage(messages):
    text = re.sub(
        r"^残HP.*\n", "", messages[0].content.replace("**", ""), flags=re.MULTILINE)
    group = re.findall(
        r".\ufe0f\u20e3 (.*)\n.*: (.*)万", text, flags=re.MULTILINE)
    for i in range(5):
        if group[i][1] != "0":
            send_message = "@everyone " + group[i][0] + "が" + group[i][1] + \
                "万足りていません、凸できる方はお願いします。"
            break
    return send_message


async def initialize(route, schedule, over):
    await route.purge(limit=100, check=init_route)
    await schedule.purge(limit=100, check=init_schedule)
    await over.purge(limit=100, check=init_over)


def init_route(message):
    if message.id == int(os.environ["ROUTE_MANUAL_ID"]):
        return False

    match = re.search(r"^(\d+)/(\d+)", message.content)
    if match and int(match.group(1)) >= now.month and int(match.group(2)) >= now.day:
        return False

    return True


def delete_route(message):
    if message.id == int(os.environ["ROUTE_MANUAL_ID"]):
        return False

    match = re.search(r"^(\d+)/(\d+)", message.content)
    # 翌日以降の日付
    if match and int(match.group(1)) >= now.month and int(match.group(2)) > get_today():
        return False

    if not is_finished(message.author):
        # 当日の日付
        if match and int(match.group(1)) >= now.month and int(match.group(2)) == get_today():
            return False
        # 日付なし
        elif not match:
            return False

    return True


def init_schedule(message):
    if message.id == int(os.environ["SCHEDULE_MANUAL_ID"]):
        return False

    match = re.search(r"^(\d+)/(\d+)", message.content)
    if match and int(match.group(1)) >= now.month and int(match.group(2)) >= now.day:
        return False

    return True


def delete_schedule(message):
    if message.id == int(os.environ["SCHEDULE_MANUAL_ID"]):
        return False

    match = re.search(r"^(\d+)/(\d+)", message.content)
    # 翌日以降の日付
    if match and int(match.group(1)) >= now.month and int(match.group(2)) > get_today():
        return False

    if not is_finished(message.author):
        # 当日の日付
        if match and int(match.group(1)) >= now.month and int(match.group(2)) == get_today():
            return False
        # 日付なし
        elif not match:
            return False

    return True


def init_over(message):
    """
    持ち越しは5時全消去
    """
    return message.id != int(os.environ["OVER_MANUAL_ID"])


def delete_over(message):
    if message.id == int(os.environ["OVER_MANUAL_ID"]):
        return False

    return not is_over(message.author.name)


client = discord.Client()
now = datetime.now(gettz("Asia/Tokyo"))

@ click.command()
@ click.option('--out', '-o', is_flag=True)
@ click.option('--purge', '-p', is_flag=True)
def main(out, purge):
    if out:
        # pylint: disable=unused-variable
        @ client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(client))
            guilds_info = {}
            for i, guild in enumerate(client.guilds):
                channels_info = {}
                for j, channel in enumerate(guild.text_channels):
                    channels_info["channel" + str(j)] = {
                        "name": channel.name, "id": channel.id, "category": channel.category.name}
                guilds_info["guild" + str(i)] = {"name": guild.name,
                                                 "id": guild.id, "channels": channels_info}
            await client.close()

            with open("./data/guilds.json", mode="w") as f:
                f.write(json.dumps(guilds_info, ensure_ascii=False, indent=4))
    elif purge:
        # pylint: disable=unused-variable
        @ client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(client))
            guild = discord.utils.get(
                client.guilds, id=int(os.environ["GUILD_ID"]))
            announce = discord.utils.get(
                guild.channels, id=int(os.environ["ANNOUNCE_CH_ID"]))

            def is_me(m):
                return m.author == client.user

            deleted = await announce.purge(limit=None, check=is_me)
            print("Deleted {} message(s)".format(len(deleted)))
            await client.close()
    else:
        global date_start
        date_start = datetime.strptime(
            os.environ["DATE_START"] + " 05+0900", "%Y/%m/%d %H%z")
        global date_end
        date_end = datetime.strptime(
            os.environ["DATE_END"] + " 23:59:59+0900", "%Y/%m/%d %H:%M:%S%z")

        if now < date_start or date_end < now:
            print("Outside the clan battle period")
            return

        # pylint: disable=unused-variable
        @ client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(client))
            guild = discord.utils.get(
                client.guilds, id=int(os.environ["GUILD_ID"]))
            reserve = discord.utils.get(
                guild.channels, id=int(os.environ["RESERVE_CH_ID"]))
            remain = discord.utils.get(
                guild.channels, id=int(os.environ["REMAIN_CH_ID"]))
            announce = discord.utils.get(
                guild.channels, id=int(os.environ["ANNOUNCE_CH_ID"]))
            route = discord.utils.get(
                guild.channels, id=int(os.environ["ROUTE_CH_ID"]))
            schedule = discord.utils.get(
                guild.channels, id=int(os.environ["SCHEDULE_CH_ID"]))
            over = discord.utils.get(
                guild.channels, id=int(os.environ["OVER_CH_ID"]))

            if is_first_time():
                print(now)
                print("clan battle start!")
                await initialize(route=route, schedule=schedule, over=over)
            elif now.hour == 5:
                print(now)
                # 5時は全員残3凸&ハンナの更新が間に合わないので残凸の集計はしない
                send_message = create_reminder_mesage(await reserve.history(limit=1, oldest_first=True).flatten())
                if send_message:
                    await announce.send(send_message)

                await route.purge(limit=100, check=init_route)
                await schedule.purge(limit=100, check=init_schedule)
                await over.purge(limit=100, check=init_over)
            else:
                print(now)
                global progress
                progress = await remain.history(limit=100).flatten()
                progress = discord.utils.find(lambda m: is_hanna(
                    m.author) and m.content.startswith("```md\n"), progress)
                progress = progress.content
                send_message = create_remain_message()
                if send_message:
                    await announce.send(send_message)
                    send_message = create_reminder_mesage(await reserve.history(limit=1, oldest_first=True).flatten())
                    if send_message:
                        await announce.send(send_message)

                await route.purge(limit=100, check=delete_route)
                await schedule.purge(limit=100, check=delete_schedule)
                await over.purge(limit=100, check=delete_over)

            await client.close()

    token = os.environ["DISCORD_TOKEN"]
    client.run(token)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
