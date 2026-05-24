import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import io
import asyncio
import aiohttp
import base64

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
TICKET_CHANNEL_ID = 1507436725386084563
TRANSCRIPT_CHANNEL_ID = 1507765178152780027
MAX_TICKETS_PER_USER = 5

CATEGORIES = {
    "ostatni": {
        "label": "Ostatní",
        "emoji": "❓",
        "category_id": 1507438549106950195,
        "role_ids": [
            1507408568989519923,
            1507410297999069415,
            1507415712346411079,
            1507415842458177566,
            1507416371456249938,
            1507416351415734272,
            1507416733688791192,
            1507416840178241657,
            1507416886113992974,
        ],
        "questions": ["S čím potřebuješ pomoci nebo jakou otázku máš?"],
    },
    "zadost_frakci": {
        "label": "Žádost o frakci",
        "emoji": "🏛️",
        "category_id": 1507440236249223189,
        "role_ids": [
            1507408568989519923,
            1507410297999069415,
            1507415712346411079,
            1507415842458177566,
            1507416371456249938,
            1507416351415734272,
            1507416733688791192,
            1507416840178241657,
            1507416886113992974,
        ],
        "questions": [
            "O jakou frakci žádáš?",
            "Lore postavy",
            "Lore frakce",
            "Kolik lidí do začátku frakce máš?",
            "Váš frakční server (pozvánka na server)",
            "Jaké máš dev požadavky?",
        ],
    },
    "bugy": {
        "label": "Bugy/Herní chyby",
        "emoji": "🐛",
        "category_id": 1507438647081701406,
        "role_ids": [
            1507408568989519923,
            1507410297999069415,
            1507415712346411079,
            1507416371456249938,
            1507416351415734272,
        ],
        "questions": [
            "Kdy a kde se chyba stala?",
            "Popiš bug/chybu co nejpodrobněji",
            "Máš screenshot nebo video důkaz? (Ano/Ne)",
        ],
    },
    "stiznost_staff": {
        "label": "Stížnost na člena Staff Teamu",
        "emoji": "⚠️",
        "category_id": 1507584924667088956,
        "role_ids": [
            1507408568989519923,
            1507410297999069415,
        ],
        "questions": [
            "Na koho si stěžuješ? (nickname člena ST)",
            "Co se stalo? Popiš situaci podrobně",
            "Máš důkaz? (screenshot/video)",
        ],
    },
    "nahlasenihrace": {
        "label": "Nahlášení hráče",
        "emoji": "🚨",
        "category_id": 1507585077616316606,
        "role_ids": [
            1507408568989519923,
            1507410297999069415,
            1507415842458177566,
            1507416733688791192,
            1507416840178241657,
            1507416886113992974,
        ],
        "questions": [
            "Čas kdy se to stalo?",
            "Čeho se hráč dopustil?",
            "Máš důkaz? (screenshot/video)",
        ],
    },
}

# ─── BOT SETUP ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── STAŽENÍ OBRÁZKU JAKO BASE64 ───────────────────────────────────────────────
async def url_to_base64(url: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    ct = resp.content_type or "image/png"
                    b64 = base64.b64encode(data).decode("utf-8")
                    return f"data:{ct};base64,{b64}"
    except:
        pass
    return None

# ─── TRANSCRIPT ────────────────────────────────────────────────────────────────
import re

URL_REGEX = re.compile(r'(https?://[^\s<>"\']+)')
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".avi", ".mkv")

def linkify(text: str) -> str:
    """Obalí URL adresy v textu klikatelným odkazem."""
    def replace(m):
        url = m.group(1)
        display = url if len(url) <= 60 else url[:57] + "..."
        return f'<a href="{url}" style="color:#7289da;" target="_blank">{display}</a>'
    return URL_REGEX.sub(replace, text)

async def send_transcript(channel: discord.TextChannel, closer: discord.Member):
    messages_html = ""
    async for msg in channel.history(limit=1000, oldest_first=True):
        time = msg.created_at.strftime("%d.%m.%Y %H:%M")
        author = msg.author.display_name
        avatar_b64 = await url_to_base64(str(msg.author.display_avatar.url))
        avatar_src = avatar_b64 or str(msg.author.display_avatar.url)
        content = msg.content or ""
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = linkify(content)  # klikatelné URL v textu

        # Přílohy
        attachments_html = ""
        for att in msg.attachments:
            fname_lower = att.filename.lower()
            is_image = (att.content_type and att.content_type.startswith("image")) or any(fname_lower.endswith(ext) for ext in IMAGE_EXTENSIONS)
            is_video = (att.content_type and att.content_type.startswith("video")) or any(fname_lower.endswith(ext) for ext in VIDEO_EXTENSIONS)

            if is_image:
                img_b64 = await url_to_base64(att.url)
                if img_b64:
                    attachments_html += (
                        f'<div style="margin-top:6px;">'
                        f'<img src="{img_b64}" style="max-width:400px;max-height:300px;border-radius:6px;display:block;">'
                        f'<div style="font-size:0.75em;color:#72767d;margin-top:2px;">🖼️ <a href="{att.url}" style="color:#7289da;" target="_blank">{att.filename}</a></div>'
                        f'</div>'
                    )
                else:
                    attachments_html += f'<div style="margin-top:4px;">🖼️ <a href="{att.url}" style="color:#7289da;" target="_blank">{att.filename}</a></div>'
            elif is_video:
                # Videa jako klikatelný odkaz (Discord CDN linky expirují, video tag nefunguje spolehlivě)
                attachments_html += (
                    f'<div style="margin-top:6px;background:#2f3136;border-radius:6px;padding:8px;display:inline-block;">'
                    f'🎥 <a href="{att.url}" style="color:#7289da;font-weight:bold;" target="_blank">{att.filename}</a>'
                    f'<span style="color:#72767d;font-size:0.8em;margin-left:8px;">({round(att.size/1024, 1)} KB)</span>'
                    f'</div>'
                )
            else:
                # Ostatní soubory jako odkaz
                attachments_html += (
                    f'<div style="margin-top:6px;background:#2f3136;border-radius:6px;padding:8px;display:inline-block;">'
                    f'📎 <a href="{att.url}" style="color:#7289da;font-weight:bold;" target="_blank">{att.filename}</a>'
                    f'<span style="color:#72767d;font-size:0.8em;margin-left:8px;">({round(att.size/1024, 1)} KB)</span>'
                    f'</div>'
                )

        # Embedy
        embeds_html = ""
        for e in msg.embeds:
            embeds_html += '<div style="border-left:4px solid #7289da;padding:8px;margin:4px 0;background:#2f3136;border-radius:0 4px 4px 0;">'
            if e.title:
                title_text = e.title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if e.url:
                    embeds_html += f'<div style="font-weight:bold;"><a href="{e.url}" style="color:#7289da;" target="_blank">{title_text}</a></div>'
                else:
                    embeds_html += f'<div style="font-weight:bold;color:#7289da;">{title_text}</div>'
            if e.description:
                desc = e.description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                desc = linkify(desc)
                embeds_html += f'<div style="color:#dcddde;margin-top:4px;">{desc}</div>'
            for field in e.fields:
                fname = field.name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                fval = field.value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                fval = linkify(fval)
                embeds_html += f'<div style="margin-top:6px;"><b style="color:#b9bbbe;">{fname}</b><br><span style="color:#dcddde;">{fval}</span></div>'
            if e.image:
                img_b64 = await url_to_base64(e.image.url)
                src = img_b64 or e.image.url
                embeds_html += f'<div style="margin-top:6px;"><img src="{src}" style="max-width:400px;border-radius:4px;display:block;"></div>'
            if e.thumbnail:
                thumb_b64 = await url_to_base64(e.thumbnail.url)
                tsrc = thumb_b64 or e.thumbnail.url
                embeds_html += f'<div style="margin-top:6px;"><img src="{tsrc}" style="max-width:160px;border-radius:4px;display:block;"></div>'
            embeds_html += '</div>'

        # Reakce
        reactions_html = ""
        if msg.reactions:
            reactions_html = '<div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:4px;">'
            for r in msg.reactions:
                emoji_str = str(r.emoji) if not hasattr(r.emoji, "url") else f'<img src="{r.emoji.url}" style="width:16px;height:16px;vertical-align:middle;">'
                reactions_html += f'<span style="background:#40444b;border-radius:4px;padding:2px 6px;font-size:0.85em;">{emoji_str} {r.count}</span>'
            reactions_html += '</div>'

        messages_html += f'''
        <div style="display:flex;padding:8px 0;border-bottom:1px solid #40444b;">
            <img src="{avatar_src}" style="width:40px;height:40px;border-radius:50%;margin-right:12px;flex-shrink:0;">
            <div style="flex:1;min-width:0;">
                <span style="color:#7289da;font-weight:bold;">{author}</span>
                <span style="color:#72767d;font-size:0.8em;margin-left:8px;">{time}</span>
                <div style="color:#dcddde;margin-top:2px;word-break:break-word;">{content}</div>
                {attachments_html}
                {embeds_html}
                {reactions_html}
            </div>
        </div>'''

    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Transcript – #{channel.name}</title>
<style>body{{background:#36393f;color:#dcddde;font-family:Arial,sans-serif;padding:20px;max-width:900px;margin:0 auto;}}h2{{color:#7289da;}}hr{{border-color:#40444b;}}</style>
</head><body>
<h2>📋 Transcript – #{channel.name}</h2>
<p>Uzavřel: <b>{closer.display_name}</b> | {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}</p>
<hr>{messages_html}</body></html>'''

    transcript_channel = bot.get_channel(TRANSCRIPT_CHANNEL_ID)
    if transcript_channel:
        file = discord.File(fp=io.BytesIO(html.encode("utf-8")), filename=f"transcript-{channel.name}.html")
        embed = discord.Embed(title="📋 Ticket uzavřen", color=0xE74C3C)
        embed.add_field(name="Kanál", value=channel.name, inline=True)
        embed.add_field(name="Uzavřel", value=closer.mention, inline=True)
        embed.set_footer(text=f"NovaX Roleplay • {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
        await transcript_channel.send(embed=embed, file=file)

# ─── MODAL (formulář) ──────────────────────────────────────────────────────────
def build_modal(category_key: str):
    cat = CATEGORIES[category_key]
    questions = cat["questions"]

    class TicketModal(discord.ui.Modal, title=cat["label"]):
        def __init__(self):
            super().__init__()
            self.category_key = category_key
            for i, q in enumerate(questions[:5]):
                self.add_item(discord.ui.TextInput(
                    label=q[:45],
                    style=discord.TextStyle.paragraph,
                    required=True,
                    max_length=1000,
                ))

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            cat = CATEGORIES[self.category_key]
            guild = interaction.guild
            member = interaction.user

            open_tickets = [
                ch for ch in guild.channels
                if isinstance(ch, discord.TextChannel)
                and ch.name.startswith(member.name.lower().replace(" ", "-"))
            ]
            if len(open_tickets) >= MAX_TICKETS_PER_USER:
                await interaction.followup.send(
                    f"❌ Máš již **{MAX_TICKETS_PER_USER}** otevřených ticketů. Nejdřív uzavři existující.",
                    ephemeral=True,
                )
                return

            category_obj = guild.get_channel(cat["category_id"])
            channel_name = f"{member.name}-{cat['label'].lower().replace(' ', '-').replace('/', '-')}"[:100]

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            for role_id in cat["role_ids"]:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await guild.create_text_channel(name=channel_name, category=category_obj, overwrites=overwrites)

            embed = discord.Embed(title=f"🎫 Ticket – {cat['label']}", color=0x2ECC71)
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            for i, q in enumerate(questions[:5]):
                value = self.children[i].value if i < len(self.children) else "—"
                embed.add_field(name=q, value=value, inline=False)
            embed.set_footer(text="NovaX Roleplay • Ticket Systém")

            await channel.send(
                content=member.mention,
                embed=embed,
                view=CloseView(),
                allowed_mentions=discord.AllowedMentions(users=True, roles=False)
            )
            await interaction.followup.send(f"✅ Tvůj ticket byl vytvořen: {channel.mention}", ephemeral=True)

    return TicketModal()

# ─── POTVRZENÍ ZAVŘENÍ ─────────────────────────────────────────────────────────
class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        # Bez custom_id - tato view není persistent, generuje se vždy nová
        super().__init__(timeout=60)

    @discord.ui.button(label="Uzavřít", style=discord.ButtonStyle.danger, emoji="🔒")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="🔒 Ticket se uzavře za **10 sekund**...",
            embed=None,
            view=self
        )
        await send_transcript(interaction.channel, interaction.user)
        await asyncio.sleep(10)
        await interaction.channel.delete()

    @discord.ui.button(label="Zrušit", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

# ─── TLAČÍTKO ZAVŘÍT ───────────────────────────────────────────────────────────
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Zavřít ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚠️ Uzavřít ticket?",
            description="Opravdu chcete tento ticket uzavřít?\nPo uzavření bude ticket **nenávratně smazán**.",
            color=0xE74C3C
        )
        # ephemeral=False → zpráva viditelná pro všechny v kanálu
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmCloseView(),
            ephemeral=False
        )

# ─── BUTTON MENU ───────────────────────────────────────────────────────────────
class CategoryButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        for key, cat in CATEGORIES.items():
            button = discord.ui.Button(
                label=cat["label"],
                emoji=cat["emoji"],
                style=discord.ButtonStyle.secondary,
                custom_id=f"ticket_{key}"
            )

            async def callback(interaction: discord.Interaction, category_key=key):
                modal = build_modal(category_key)
                await interaction.response.send_modal(modal)

            button.callback = callback
            self.add_item(button)

# ─── SLASH PŘÍKAZY ─────────────────────────────────────────────────────────────
@bot.tree.command(name="ticket-add", description="Přidá uživatele do ticket kanálu")
@app_commands.describe(user="Uživatel kterého chceš přidat")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_add(interaction: discord.Interaction, user: discord.Member):
    await interaction.channel.set_permissions(user, read_messages=True, send_messages=True)
    await interaction.response.send_message(f"✅ {user.mention} byl přidán do ticketu.", ephemeral=True)

@bot.tree.command(name="ticket-remove", description="Odebere uživatele z ticket kanálu")
@app_commands.describe(user="Uživatel kterého chceš odebrat")
@app_commands.checks.has_permissions(manage_channels=True)
async def ticket_remove(interaction: discord.Interaction, user: discord.Member):
    await interaction.channel.set_permissions(user, read_messages=False, send_messages=False)
    await interaction.response.send_message(f"✅ {user.mention} byl odebrán z ticketu.", ephemeral=True)

# ─── PŘÍKAZY ───────────────────────────────────────────────────────────────────
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ticket kanál nenalezen!")
        return
    embed = discord.Embed(
        title="🎫 Ticket Systém",
        description=(
            "Potřebuješ pomoci? Vytvoř si ticket a my ti rádi pomůžeme!\n\n"
            "**PRACOVNÍ DOBA NAŠÍ PODPORY:**\n"
            "Pondělí – Pátek: 16:00–21:00\n"
            "Sobota - Neděle: 15:30–22:00\n"
        ),
        color=0x2ECC71,
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1123921380891709530/1507413657074663535/novayx.png?ex=6a11cfde&is=6a107e5e&hm=dfca305237d890930eeafd679bf41b86246fba6ecceb5bc7ec5c6852eb593ab8&")
    embed.set_footer(text="NovaX Roleplay • Ticket Systém")
    await channel.send(embed=embed, view=CategoryButtons())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Slash příkazy synchronizovány!", delete_after=5)

# ─── PERSISTENT VIEWS ──────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    bot.add_view(CategoryButtons())
    bot.add_view(CloseView())
    await bot.tree.sync()
    print(f"✅ Bot přihlášen jako {bot.user}")

bot.run(TOKEN)
