import sys
import os
import re
import json
import click
from datetime import datetime, timedelta
from dateutil.tz import gettz
import discord


def is_hanna(user):
    return user.id == 664501882856931348


def get_left_hour():
    if now.day == date_end.day and 5 <= now.hour:
        total = 24
    elif 0 <= now.hour < 5:
        total = 5
    else:
        total = 24 + 5
    return total - now.hour


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


def create_remain_message(messages):
    message = discord.utils.find(lambda m: is_hanna(
        m.author) and m.content.startswith("```md\n"), messages)
    condition = message.content

    if not condition:
        # ガード
        return
    elif not is_today((condition.split())[1]):
        return

    left = re.findall(r" 残り.凸 \((\d+)+名\)", condition, flags=re.MULTILINE)
    left.reverse()
    left_all = sum([int(x) * i for i , x in enumerate(left)][1:4])
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
            os.environ["DATE_START"] + " 06+0900", "%Y/%m/%d %H%z")  # 初日5時は不要
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

            while True:
                if now.hour == 5:  # 5時は全員残3凸&ハンナの更新が間に合わないので出力しない
                    print("5時の為スキップ")
                else:
                    send_message = create_remain_message(await remain.history(limit=100).flatten())
                    if send_message:
                        await announce.send(send_message)
                    else:
                        # 全員3凸済の場合は催促不要
                        break

                send_message = create_reminder_mesage(await reserve.history(limit=1, oldest_first=True).flatten())
                if send_message:
                    await announce.send(send_message)

                break

            await client.close()

    token = os.environ["DISCORD_TOKEN"]
    client.run(token)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
