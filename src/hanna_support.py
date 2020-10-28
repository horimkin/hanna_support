import sys
import os
import re
import json
import click
from datetime import datetime
from dateutil.tz import gettz
import discord


def is_hanna(user):
    return user.name == "ハンナ" and user.bot


def get_left_hour():
    if now.day == date_end.day and 5 <= now.hour:
        total = 24
    elif 0 <= now.hour < 5:
        total = 5
    else:
        total = 24 + 5
    return total - now.hour


def create_remain_message(messages):
    # 日を跨いだり月を跨いだり年を跨いだりするとダメ、
    message = discord.utils.find(lambda m: is_hanna(
        m.author) and m.content.startswith("```md\n"), messages)
    condition = message.content

    left = re.findall(r" 残り.凸 \((\d)+名\)", condition, flags=re.MULTILINE)
    left.reverse()
    left_all = sum(int(x) for x in left[1:4])

    left_hour = get_left_hour()
    if left_all == 0:
        print("全員3凸済みの為スキップ")
        return

    send_message = now.strftime('%Y/%m/%d %H時') + "の残凸状況\n" + \
        "3凸：" + left[3] + "人\n" + \
        "2凸：" + left[2] + "人\n" + \
        "1凸：" + left[1] + "人\n" + \
        "あと" + str(left_hour) + "時間で" + str(left_all) + "凸\n" + \
        "1時間あたり" + str(round(left_all / left_hour, 2)) + "凸必要です"

    return send_message


def create_reinder_mesage(messages):
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

        if now <= date_start or date_end < now:
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

                send_message = create_reinder_mesage(await reserve.history(limit=1, oldest_first=True).flatten())
                if send_message:
                    await announce.send(send_message)

                break

            await client.close()

    token = os.environ["DISCORD_TOKEN"]
    client.run(token)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
