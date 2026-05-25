import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
import io
import asyncio
import chat_exporter

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

# ─── TRANSCRIPT (chat-exporter) ────────────────────────────────────────────────
async def send_transcript(channel: discord.TextChannel, closer: discord.Member):
    """Vygeneruje HTML transcript přes chat-exporter a pošle do transcript kanálu."""
    transcript = await chat_exporter.export(
        channel=channel,
        limit=None,
        tz_info="Europe/Prague",
        military_time=True,
        bot=bot,
    )

    if transcript is None:
        return

    transcript_channel = bot.get_channel(TRANSCRIPT_CHANNEL_ID)
    if transcript_channel:
        file = discord.File(
            fp=io.BytesIO(transcript.encode("utf-8")),
            filename=f"transcript-{channel.name}.html",
        )
        embed = discord.Embed(
            title="📋 Ticket uzavřen",
            color=0xE74C3C,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.add_field(name="📁 Kanál", value=channel.name, inline=True)
        embed.add_field(name="🔒 Uzavřel", value=closer.mention, inline=True)
        embed.set_footer(text="NovaX Roleplay • Ticket Systém")
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
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="✅ Uzavření zrušeno.",
            embed=None,
            view=self
        )
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass
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
        await interaction.response.send_message(embed=embed, view=ConfirmCloseView())

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
