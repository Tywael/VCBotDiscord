import discord
import re
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True 

bot = commands.Bot(command_prefix='/', intents=intents)
slash = SlashCommand(bot, sync_commands=True)

register_channel_ids = []

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user}')

@bot.slash_command(name="autoChannel", description="Ajouter un channel de base")
async def auto_channel(ctx: discord.ApplicationContext, channel_id: int):
    if channel_id not in register_channel_ids:
        register_channel_ids.append(channel_id)
        await ctx.send(f'Channel de base ajouté : {channel_id}')
    else:
        await ctx.send(f'Channel {channel_id} est déjà un channel de base.')

@bot.slash_command(name="removeAutoChannel", description="Supprimer un channel de base")
async def remove_auto_channel(ctx: discord.ApplicationContext, channel_id: int):
    if channel_id in register_channel_ids:
        register_channel_ids.remove(channel_id)
        await ctx.send(f'Channel de base supprimé : {channel_id}')
    else:
        await ctx.send(f'Channel {channel_id} n\'est pas un channel de base.')

@bot.event
async def on_voice_state_update(member, before, after):
    if not register_channel_ids:
        return

    guild = member.guild
    if after.channel and after.channel.id in register_channel_ids:
        joined_channel = guild.get_channel(after.channel.id)
        if len(joined_channel.members) == 1:
            base_name_match = re.match(r"^(.*?)(?: #\d+)?$", joined_channel.name)
            base_name = base_name_match.group(1) if base_name_match else joined_channel.name
            existing_channels = [ch.name for ch in guild.voice_channels if ch.name.startswith(base_name)]
            next_number = 2
            while f"{base_name} #{next_number}" in existing_channels:
                next_number += 1
            new_channel = await joined_channel.clone(name=f"{base_name} #{next_number}")
            register_channel_ids.append(new_channel.id)
    elif before.channel and before.channel.id in register_channel_ids:
        left_channel = guild.get_channel(before.channel.id)
        base_name_match = re.match(r"^(.*?)(?: #\d+)?$", left_channel.name)
        base_name = base_name_match.group(1) if base_name_match else left_channel.name
        if len(left_channel.members) == 0:
            number_left = re.match(r".* #(\d+)$", left_channel.name)
            if number_left:
                next_number = int(number_left.group(1)) + 1
                next_channel_name = f"{base_name} #{next_number}"
                next_channel = discord.utils.get(guild.voice_channels, name=next_channel_name)
                if next_channel and len(next_channel.members) == 0:
                    await next_channel.delete()
                    register_channel_ids.remove(next_channel.id)
bot.run(TOKEN)