import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ─── CONFIG ────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
TICKET_CHANNEL_ID = 1507436725386084563
MAX_TICKETS_PER_USER = 5

CATEGORIES = {
    "ostatni": {
        "label": "Ostatní",
        "emoji": "❓",
        "category_id": 1507438549106950195,
        "role_ids": [
            1507408568989519923,  # Founder
            1507410297999069415,  # Managment
            1507415712346411079,  # Head of Developer
            1507415842458177566,  # Head of Staff
            1507416371456249938,  # Developer
            1507416351415734272,  # Trial Developer
            1507416733688791192,  # Senior Staff
            1507416840178241657,  # Staff
            1507416886113992974,  # Trial Staff
        ],
        "questions": [
            "S čím potřebuješ pomoci nebo jakou otázku máš?",
        ],
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

# ─── MODAL (formulář) ──────────────────────────────────────────────────────────
def build_modal(category_key: str):
    cat = CATEGORIES[category_key]
    questions = cat["questions"]

    class TicketModal(discord.ui.Modal, title=cat["label"]):
        def __init__(self):
            super().__init__()
            self.category_key = category_key
            for i, q in enumerate(questions[:5]):  # Discord max 5 polí
                self.add_item(
                    discord.ui.TextInput(
                        label=q[:45],
                        style=discord.TextStyle.paragraph,
                        required=True,
                        max_length=1000,
                    )
                )

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            cat = CATEGORIES[self.category_key]
            guild = interaction.guild
            member = interaction.user

            # Kontrola max ticketů
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

            # Vytvoř kanál
            category_obj = guild.get_channel(cat["category_id"])
            channel_name = f"{member.name}-{cat['label'].lower().replace(' ', '-').replace('/', '-')}"
            channel_name = channel_name[:100]

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            for role_id in cat["role_ids"]:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await guild.create_text_channel(
                name=channel_name,
                category=category_obj,
                overwrites=overwrites,
            )

            # Embed se shrnutím
            embed = discord.Embed(
                title=f"🎫 Ticket – {cat['label']}",
                color=0x2ECC71,
            )
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            for i, q in enumerate(questions[:5]):
                value = self.children[i].value if i < len(self.children) else "—"
                embed.add_field(name=q, value=value, inline=False)
            embed.set_footer(text="NovaX Roleplay • Ticket Systém")

            # Zmínky rolí
            mentions = " ".join(
                f"<@&{rid}>" for rid in cat["role_ids"]
            )
            close_view = CloseView()
            await channel.send(content=f"{member.mention} {mentions}", embed=embed, view=close_view)

            await interaction.followup.send(
                f"✅ Tvůj ticket byl vytvořen: {channel.mention}", ephemeral=True
            )

    return TicketModal()


# ─── TLAČÍTKO ZAVŘÍT ───────────────────────────────────────────────────────────
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Zavřít ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Ticket se zavírá...", ephemeral=True)
        await interaction.channel.delete()


# ─── DROPDOWN MENU ─────────────────────────────────────────────────────────────
class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=cat["label"],
                value=key,
                emoji=cat["emoji"],
            )
            for key, cat in CATEGORIES.items()
        ]
        super().__init__(
            placeholder="Vyber si kategorii...",
            options=options,
            custom_id="ticket_category_select",
        )

    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        modal = build_modal(category_key)
        await interaction.response.send_modal(modal)


class CategoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategorySelect())


# ─── PŘÍKAZ PRO SETUP ──────────────────────────────────────────────────────────
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    """Pošle embed s dropdown menu do ticket kanálu"""
    channel = bot.get_channel(TICKET_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Ticket kanál nenalezen!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎫 Ticket Systém",
        description=(
            "Potřebuješ pomoci? Vytvoř si ticket a my ti rádi pomůžeme!\n\n"
            "**PRACOVNÍ DOBA NAŠÍ PODPORY:**\n"
            "Pondělí – Čtvrtek: 16:00–21:00\n"
            "Pátek: 16:00–22:00\n"
            "Sobota: 13:00–22:00\n"
            "Neděle: 16:00–20:00"
        ),
        color=0x2ECC71,
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1123921380891709530/1507413657074663535/novayx.png?ex=6a11cfde&is=6a107e5e&hm=dfca305237d890930eeafd679bf41b86246fba6ecceb5bc7ec5c6852eb593ab8&")
    embed.set_footer(text="NovaX Roleplay • Ticket Systém")

    await channel.send(embed=embed, view=CategoryView())
    await ctx.send("✅ Ticket systém byl nastaven!", delete_after=5)


# ─── PERSISTENT VIEWS ──────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    bot.add_view(CategoryView())
    bot.add_view(CloseView())
    print(f"✅ Bot přihlášen jako {bot.user}")


bot.run(TOKEN)
