import os
import discord
from discord.ext import commands

# ─────────────── Config ───────────────
GUILD_ID = 876528050081251379
LOG_CHANNEL_ID = 1399088859245051954

# messages in these categories won't trigger mention DMs
EXCLUDED_CATEGORY_IDS = {
    1215316814469533696,
    1387520841704673360,
}

WATCHED_ROLE_IDS = {
    1139627400901169212,
    1139627559710113852,
    1139627974518394961,
    1360336184781570271,
    1139628044865245195,
    1139628310440190076,
    1248054118371819571,
    1295530560990613535,
    1139628383853101166,
    1364296112965681233,
    1227638634870734979,
    1227638886788759612,
    1227647933579526144,
    876569612085518376,  # tracked
}

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")

# ─────────────── Intents / Bot ───────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ─────────────── Helpers ───────────────
def _first_image_from_message(message: discord.Message) -> str | None:
    for att in message.attachments:
        if (att.content_type and att.content_type.startswith("image/")) or att.filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp")
        ):
            return att.url
    for e in message.embeds:
        if e.image and e.image.url:
            return e.image.url
        if e.type == "image" and e.url:
            return e.url
    return None


async def _log_role_mention(message: discord.Message) -> None:
    mentioned_role_ids = {r.id for r in message.role_mentions}
    if not (mentioned_role_ids & WATCHED_ROLE_IDS):
        return

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not isinstance(log_channel, discord.TextChannel):
        print("⚠️ Log channel not found or not a text channel.")
        return

    embed = discord.Embed(
        title="🔔 Role Mentioned",
        description=message.content or "[No text content]",
        color=discord.Color.blue(),
        timestamp=message.created_at,
    )
    embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    embed.add_field(name="Jump to Message", value=f"[Click here]({message.jump_url})", inline=False)

    img = _first_image_from_message(message)
    if img:
        embed.set_image(url=img)

    await log_channel.send(embed=embed)


async def _dm_mentioned_users(message: discord.Message) -> None:
    if message.channel.category and message.channel.category.id in EXCLUDED_CATEGORY_IDS:
        return

    unique_users = {u for u in message.mentions if not u.bot}
    if not unique_users:
        return

    for user in unique_users:
        try:
            dm_text = f"{message.author.mention} mentioned you {message.jump_url}"
            await user.send(dm_text)
            print(f"✅ Sent mention DM to {user} ({user.id})")
        except Exception as e:
            print(f"❌ Couldn’t DM {user} ({user.id}): {e}")


# ─────────────── Events ───────────────
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return
    if message.guild.id != GUILD_ID:
        return

    try:
        await _log_role_mention(message)
    except Exception as e:
        print(f"⚠️ Error logging role mention: {e}")

    try:
        await _dm_mentioned_users(message)
    except Exception as e:
        print(f"⚠️ Error DMing mentioned users: {e}")

    await bot.process_commands(message)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN (or DISCORD_BOT_TOKEN) in your environment.")
    bot.run(TOKEN)
