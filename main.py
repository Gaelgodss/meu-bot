import discord
from discord.ext import commands
from discord.ui import Button, View
import socket
import os

def bind_dummy_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 10000))  # Porta arbitrária
    s.listen(1)
    print("Porta 10000 aberta (dummy).")
    s.accept() 
    
TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
intents.members = True
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.reactions = True

class GeneroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="♂️ Homem", style=discord.ButtonStyle.primary, custom_id="Boy")
    async def homem(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Boy")
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("✅ Você escolheu **Homem**. Agora selecione sua idade:", ephemeral=True)
        await self.perguntar_idade(interaction)

    @discord.ui.button(label="♀️ Mulher", style=discord.ButtonStyle.primary, custom_id="Girl")
    async def mulher(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Girl")
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("✅ Você escolheu **Mulher**. Agora selecione sua idade:", ephemeral=True)
        await self.perguntar_idade(interaction)

    async def perguntar_idade(self, interaction):
        embed_idade = discord.Embed(
            title="🎂 Verificação - Sua Idade",
            description="Clique abaixo para escolher:\n\n🔞 **+18**\n🍼 **-18**",
            color=discord.Color.purple()
        )
        embed_idade.set_footer(text="Cyber Void © Todos os direitos reservados.")

        view = IdadeView()
        await interaction.followup.send(embed=embed_idade, view=view, ephemeral=True)

class IdadeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔞 +18", style=discord.ButtonStyle.success, custom_id="maior")
    async def maior(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalizar_verificacao(interaction, "+18")

    @discord.ui.button(label="🍼 -18", style=discord.ButtonStyle.danger, custom_id="menor")
    async def menor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalizar_verificacao(interaction, "-18")

    async def finalizar_verificacao(self, interaction, idade_role_name):
        # Adiciona cargo de idade
        idade_role = discord.utils.get(interaction.guild.roles, name=idade_role_name)
        if idade_role:
            await interaction.user.add_roles(idade_role)

        # Remove cargo "Não verificado"
        nao_verificado = discord.utils.get(interaction.guild.roles, name="Não verificado")
        if nao_verificado and nao_verificado in interaction.user.roles:
            await interaction.user.remove_roles(nao_verificado)

        await interaction.response.send_message("✅ Verificação concluída! Agora você tem acesso ao servidor completo.", ephemeral=True)


async def criar_canal_compra(interaction, produto_nome):
    guild = interaction.guild
    comprador = interaction.user

    # Cria ou pega a categoria "🛒・Compras"
    categoria = discord.utils.get(guild.categories, name="🛒・Compras")
    if categoria is None:
        categoria = await guild.create_category("🛒・Compras")

    # Permissões
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        comprador: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    canal = await guild.create_text_channel(
        name=f"compra-{comprador.name}",
        overwrites=overwrites,
        category=categoria,
        reason="Nova compra"
    )

    # Botão fechar
    close_button = Button(label="Fechar Compra", style=discord.ButtonStyle.red, emoji="🔒")

    async def close_callback(close_interaction):
        if close_interaction.user == comprador:
            await canal.delete(reason="Compra finalizada")
        else:
            await close_interaction.response.send_message("❌ Só o comprador pode fechar.", ephemeral=True)

    close_button.callback = close_callback

    close_view = View()
    close_view.add_item(close_button)

    await canal.send(
        f"🛒 Olá {comprador.mention}, obrigado por comprar **{produto_nome}**!\n"
        "Aguarde que um vendedor vai te atender aqui.\n\n"
        "Quando finalizar, clique no botão abaixo para fechar o canal.",
        view=close_view
    )

    await interaction.response.send_message(f"✅ Canal criado: {canal.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ Bot está online como {bot.user}!')

@bot.event
async def on_member_join(member):

    nome_do_cargo = "Não verificado"

    role = discord.utils.get(member.guild.roles, name=nome_do_cargo)

    if role:
        await member.add_roles(role)
        print(f"Cargo '{nome_do_cargo}' adicionado para {member.name}")
    else:
        print(f"Cargo '{nome_do_cargo}' não encontrado no servidor!")

@bot.command()
async def privar(ctx):
    guild = ctx.guild

    # Pegar a categoria chamada "Calls cargos"
    categoria = discord.utils.get(guild.categories, name="🧧・Moderação")
    if not categoria:
        await ctx.send("❌ Categoria 'Calls cargos' não encontrada.")
        return

    # Pegar o cargo chamado "Não verificado"
    cargo = discord.utils.get(guild.roles, name="Não verificado")
    if not cargo:
        await ctx.send("❌ Cargo 'Não verificado' não encontrado.")
        return

    # Alterar permissões em todos os canais da categoria
    for canal in categoria.channels:
        await canal.set_permissions(cargo, view_channel=False)

    await ctx.send("✅ Todos os canais da categoria 'Calls cargos' foram privados para o cargo 'Não verificado'.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    guild = ctx.guild

    # Cria ou pega o cargo "Não verificado"
    role_nao_verificado = discord.utils.get(guild.roles, name="Não verificado")
    if not role_nao_verificado:
        role_nao_verificado = await guild.create_role(name="Não verificado")

    # Cria ou pega o cargo "Vip"
    vip = discord.utils.get(guild.roles, name="Vip")
    if not vip:
        vip = await guild.create_role(name="Vip")

    # Canal registrar-se
    overwrites_registrar = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role_nao_verificado: discord.PermissionOverwrite(view_channel=True)
    }
    canal_registrar = await guild.create_text_channel(name="📒・registrar-se", overwrites=overwrites_registrar)
    await limpar_mensagem_automatica(canal_registrar)
    canal_sobre = await guild.create_text_channel(name="🎭︎・O que somos?", overwrites=overwrites_registrar)
    await limpar_mensagem_automatica(canal_sobre)

    # Estrutura do servidor
    structure = {
        "🌟 START HERE 🌟": ["👋・bem-vindo", "📜・regras"],
        "📢・ANÚNCIOS 📌": ["『🎇』・comissões", "『🎮』・Promoções"],
        "🛒・LOJA": ["『💰』・Rat 🐭","『💰』・Riader-Discord ⚙"],
        "🌟・ AREA VIP": ["👑・bate-papo Gold", "💎・Loja-Vip"],
        "💎・SEJA VIP": ["🏷️・comprar-vip", "🎁・benefícios-vip", "🔥・vip-deals"],
        "🌸・ BOOST 🌸": ["🌸・seja-booster"],
        "📍・SUPORTE": ["🟥・ticket", "💭・sugestões"],
        "💬・COMMUNITY 💬": ["🏆・rank", "💬・bate-papo", "📸・mídias"],
    }

    # Criar categorias e canais
    for category_name, channels in structure.items():
        lista_publica = ["🛒・LOJA", "📢・ANÚNCIOS 📌", "🌟 START HERE 🌟"]

        if category_name in lista_publica:
            category = await guild.create_category(name=category_name)
            for channel_name in channels:
                canal = await guild.create_text_channel(name=channel_name, category=category)
                await limpar_mensagem_automatica(canal)
                print(f"✅ Canal {channel_name} criado na categoria {category_name}")

        else:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True),
                role_nao_verificado: discord.PermissionOverwrite(view_channel=False)
            }
            category = await guild.create_category(name=category_name, overwrites=overwrites)
            for channel_name in channels:
                canal = await guild.create_text_channel(name=channel_name, category=category)
                await limpar_mensagem_automatica(canal)
                print(f"✅ Canal {channel_name} criado na categoria {category_name}")

            # Criar as calls SOMENTE na categoria SUPORTE
            if category_name == "📍・SUPORTE":
                suporte = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
                    role_nao_verificado: discord.PermissionOverwrite(view_channel=False)
                }

                suporte_vip = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    role_nao_verificado: discord.PermissionOverwrite(view_channel=False),
                    vip: discord.PermissionOverwrite(view_channel=True, connect=True),
                }

                await guild.create_voice_channel(name="🆘 Support", overwrites=suporte, category=category)
                await guild.create_voice_channel(name="🎧 Support Vip", overwrites=suporte_vip, category=category)
                print("✅ Calls de suporte criadas!")

    await ctx.send("✅ Estrutura criada com sucesso!")


async def limpar_mensagem_automatica(channel):
    await channel.purge(limit=1)

@bot.command()
@commands.has_permissions(administrator=True)
async def loja(ctx):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name="🛒・LOJA")

    adicional = [
        "『💰』・Ransomware 💻",
        "『💰』・Keylloger 🎯",
        "『💰』・Minerador (BTC/MNR)💳",
        "『💰』・Killers 💀",
        "『💰』・Jogos Steam 🎮",
        "『💰』・Personalizado 🔐"
    ]

    for atualizar in adicional:
        # Verifica se já existe um canal com o mesmo nome
        existente = discord.utils.get(guild.text_channels, name=atualizar)
        if existente is None:
            await guild.create_text_channel(name=atualizar, category=category)

@bot.command()
@commands.has_permissions(administrator=True)
async def cargo(ctx):
    cargos = [
        "Booster", "House Family", "Boy", "+18",
        "Married", "Puro Veneno", "amo franjudinhas", "Manager", "Support", "Real Family", "magnata",
        "Verificado", "Girl", "-18", "Namorando", "I'm really abuser", "sexo, drogas e minecraft",
        "Vendedor", "Comprador", "Leader", "Supervisor", "Amo peitudas", "Pigga", "golem", "Daniel Fraga", "Staff",
        "Mov. Call", "Bluzão"
    ]

    guild = ctx.guild

    # Mapeamento de emojis
    emojis = {
        "Booster": "🌸",
        "House Family": "🏠",
        "Boy": "👦",
        "+18": "🔞",
        "Married": "💍",
        "Puro Veneno": "🐍",
        "amo franjudinhas": "🥰",
        "Manager": "🗂️",
        "Real Family": "👪",
        "magnata": "💰",
        "Verificado": "✅",
        "Não Verificado": "❌",
        "Girl": "👧",
        "-18": "🍼",
        "Namorando": "💑",
        "I'm really abuser": "😈",
        "sexo, drogas e minecraft": "🌿",
        "Vendedor": "🛒",
        "Comprador": "💳",
        "Leader": "👑",
        "Amo peitudas": "🍒",
        "Pigga": "🐷",
        "golem": "🗿",
        "Daniel Fraga": "🎭",
        "Vip": "💎",
        "Bluzão": "🎸"
    }

    cu = {
        "Mov. Call": "🎤",
        "Supervisor": "🕵️",
        "Staff": "🛡️",
    }

    # Cargo que NÃO pode ver nada
    role_nao_verificado = discord.utils.get(guild.roles, name="Não Verificado")
    if not role_nao_verificado:
        role_nao_verificado = await guild.create_role(name="Não Verificado")
        print("✅ Cargo 'Não Verificado' criado!")

    for nome in cargos:
        existing_role = discord.utils.get(guild.roles, name=nome)
        if not existing_role:
            if nome in ["Staff", "Mov. Call", "Manager", "Leader", "Supervisor", "Support"]:
                permissions = discord.Permissions()
                permissions.update(
                    manage_channels=True,
                    kick_members=True,
                    move_members=True,
                    manage_messages=True
                )
                await guild.create_role(name=nome, permissions=permissions)
                print(f"✅ Cargo Staff criado: {nome}")
            else:
                await guild.create_role(name=nome)
                print(f"✅ Cargo normal criado: {nome}")
        else:
            print(f"⚠️ Cargo já existe: {nome}")

    await ctx.send("✅ Cargos configurados!")

    # Criar categoria Privados
    overwrites_cat = {
        role_nao_verificado: discord.PermissionOverwrite(view_channel=False),
        guild.default_role: discord.PermissionOverwrite(view_channel=True)
    }
    categoria = await guild.create_category("🔊・Calls", overwrites=overwrites_cat)
    print("✅ Categoria Privados criada!")
    supervisao = await guild.create_category("🧧・Moderação", overwrites=overwrites_cat)

    for nome in cargos:
        role = discord.utils.get(guild.roles, name=nome)
        if role:
            overwrites_voice = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False),
                role: discord.PermissionOverwrite(connect=True, speak=True),
                role_nao_verificado: discord.PermissionOverwrite(view_channel=False)
            }

            # Pega o emoji ou usa uma "🔊" padrão
            emoji = emojis.get(nome, "🔊")

            await guild.create_voice_channel(f"{emoji} {nome}", overwrites=overwrites_voice, category=categoria)
            print(f"✅ Canal privado criado para: {nome}")

    for d in cu:
        role = discord.utils.get(guild.roles, name=d)
        if role:
            overwrites_voice = {
                guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False),
                role: discord.PermissionOverwrite(connect=True, speak=True),
                role_nao_verificado: discord.PermissionOverwrite(view_channel=False)
            }

            # Pega o emoji ou usa uma "🔊" padrão
            emoji = emojis.get(d, "🔊")

            await guild.create_voice_channel(f"{emoji} {d}", overwrites=overwrites_voice, category=supervisao)
            print(f"✅ Canal privado criado para: {d}")

    await ctx.send("✅ Todos os canais privados foram criados!")

@bot.command()
@commands.has_permissions(administrator=True)
async def regras(ctx):
    embed = discord.Embed(
        title="📜 Regras",
        description="Seja bem vindo à **Cyber Void**.\nDesejamos ser a maior comunidade de hacker independente brasileira.\nPara manter uma relação saudável, siga as regras.",
        color=0x7289DA
    )
    embed.add_field(
        name="**Regras para canais de voz:**",
        value=(
            "1️⃣ Utilize-os para conversar e fazer amizades ou compras;\n"
            "2️⃣ Não compartilhe conteúdo adulto em live;\n"
            "3️⃣ Evite qualquer poluição sonora;\n"
            "4️⃣ Não utilize modificadores de voz;\n"
            "5️⃣ Não incentive ou participe de brigas;\n"
        ),
        inline=False
    )

    embed.add_field(
        name="**Regras de comportamento:**",
        value=(
            "6️⃣ Respeite todos os membros do servidor;\n"
            "7️ Não pratique nenhum tipo de divulgação;\n"
            ":eight: Não compartilhe qualquer conteúdo adulto;\n"
            "9️⃣ Use o bom senso ao interpretar as regras;\n"
        ),
        inline=False
    )

    embed.add_field(
        name="**Regras para canais de texto:**",
        value=(
            "🔟 Não envie nenhum tipo de spam;\n"
            "0️⃣ Evite marcar os admins e moderadores;\n"
            "9️⃣ Qualquer discriminação resultará em ban;\n"
            "🔟 Não pratique nenhum tipo de comércio."
        ),
        inline=False
    )

    embed.set_footer(text="Todos os direitos reservados. © Cyber Void")

    file = discord.File("logo.png", filename="logo.png")
    embed.set_image(url="attachment://logo.png")

    await ctx.send(file=file, embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def booster(ctx):
    embed = discord.Embed(
        title="Seja Booster",
        description=(
            "**Vantagens:**\n"
            "1️⃣ Cargo destacado no servidor: **@Booster**\n"
            "2️⃣ Enviar **imagens** no #📸・chat-geral;\n"
            "3️⃣ Permissão de entrar na call **Booster**\n"
            "4️⃣ Desconto no **Vip!!**"
        ),
    )
    embed.set_footer(text="Todos os direitos reservados. © Cyber Void")

    file = discord.File("banner.PNG", filename="banner.PNG")
    embed.set_image(url="attachment://banner.PNG")
    await ctx.send(file=file, embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def promocao(ctx):
    embed = discord.Embed(
        title="🧨・PROMOÇÃO",
        description="Seja bem-vindo ao sistema de Promoção da **Cyber Void**!",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="\n💰・STEAM\n",
        value=(
            "\n**Qualquer** jogo da **steam** por 5 reais"
            "você poderá Comprar até **5 jogos!!**\n"
        ),
        inline=False
    )

    embed.add_field(
        name="Regras e Condições:",
        value=(
            "\n1️⃣ Se comprar os 5 jogos de uma vez ira ter um desconto de um jogo dado de **graça**!\n"
            "\n2️⃣ Promoção válida para qualquer um!\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🎯",
        value="Traga amigos, ganhe recompensas e aproveite!",
        inline=False
    )

    embed.set_footer(text="Todos os direitos reservados. © Cyber Void")

    file = discord.File("banner.PNG", filename="banner.PNG")
    embed.set_image(url="attachment://banner.PNG")
    await ctx.send(file=file, embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def comissao(ctx):
    embed = discord.Embed(
        title="📢・COMISSÃO",
        description="Seja bem-vindo ao sistema de comissão da **Cyber Void**!",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="\n💰・Como funciona?\n",
        value=(
            "\nSe **duas pessoas** que você trouxe para o servidor **comprarem algo**, "
            "você poderá **escolher qualquer item** no valor que elas gastaram!\n"
            "Sem limite: o que elas gastarem é o que você pode pegar!"
        ),
        inline=False
    )

    embed.add_field(
        name="📜 Regras da Comissão:",
        value=(
            "\n1️⃣ As duas pessoas precisam informar que vieram por você;\n"
            "\n2️⃣ As compras devem ser confirmadas pelos admins;\n"
            "\n3️⃣ O valor total é baseado no que **ambas gastarem somado**;\n"
            "\n4️⃣ Comissão válida apenas para membros ativos."
        ),
        inline=False
    )

    embed.add_field(
        name="🎯",
        value="Traga amigos, ganhe recompensas e aproveite!",
        inline=False
    )

    embed.set_footer(text="Todos os direitos reservados. © Cyber Void")

    file = discord.File("banner.PNG", filename="banner.PNG")
    embed.set_image(url="attachment://banner.PNG")
    await ctx.send(file=file, embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def sobre(ctx):
    embed = discord.Embed(
        title="🎩 Bem-vindo ao Cyber Void. 🎭",
        description="""Somos um grupo que decidiu mudar o mercado de hackers e malwares, mas além de tudo expalhar a verdade e conhecimento. 
Se não estiver interessado em comprar algo pode se juntar a comunidade, participar de eventos, juntar-se a moderação e etc!\n\n\n"""  ,
        color=0x7289DA
    )

    embed.add_field(
        name="🔥・**O Que Oferecemos?:**",
        value=(
            "\n**Malwares Customizados**: Não vendemos scripts básicos. Nossas criações são obras de arte digitais, projetadas para eficiência máxima e evasão avançada.\n\n"
            "**Hacks & Exploits**: De game cheats a invasões estratégicas, tudo é desenvolvido com precisão cirúrgica.\n\n"
            "**Cursos Exclusivos**: Aprenda com os melhores. Ensinamos o que realmente funciona.\n\n"
            "**Contas Premium e Dados**: Steam, Netflix, Spotify.\n\n"
            "**Jogos**: Liberação do jogo na sua biblioteca steam oficial, com manifest e etc.\n\n"
        ),
        inline=False
    )
    embed.add_field(
        name="📢・**Comunidade ativa:**\n",
        value=(
            "🎉・**Sorteios & Eventos**: De giveaways de ferramentas a desafios de hacking, sempre tem algo rolando.\n\n"
            "💬・**Discussões & Networking**: Troque ideias com outros players, compartilhe técnicas ou apenas relaxe no chat.\n\n"
            "🛡️・**Suporte & Privacidade**: Anonimato é lei. Ninguém vaza, ninguém trai.\n\n"
        ),
        inline=False
    )

    embed.set_footer(text="Todos os direitos reservados. © Cyber Void")

    file = discord.File("logo.jpg", filename="logo.jpg")
    embed.set_image(url="attachment://logo.jpg")

    await ctx.send(file=file, embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def verificar(ctx):
    embed_genero = discord.Embed(
        title="🆔 Verificação - Escolha seu Gênero",
        description="Clique abaixo para escolher:\n\n♂️ **Homem**\n♀️ **Mulher**",
        color=discord.Color.blurple()
    )
    embed_genero.set_footer(text="Cyber Void © Todos os direitos reservados.")

    view = GeneroView()
    await ctx.send(embed=embed_genero, view=view)

@bot.event
async def on_member_update(before, after):
    # Pega o cargo "Não verificado"
    role_nao_verificado = discord.utils.get(after.guild.roles, name="Não verificado")

    # Verifica se o cargo foi ADICIONADO agora (não tinha antes e agora tem)
    if role_nao_verificado and role_nao_verificado not in before.roles and role_nao_verificado in after.roles:
        canal = discord.utils.get(after.guild.text_channels, name='👋・bem-vindo')  # Troque para o canal correto
        if canal:
            await canal.send(f"**Bem-vindo(a), {after.mention}!**\nPara acessar o servidor, complete sua verificação clicando nos botões acima!")


# =====================================================
# sobre o Vip
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def sobre_vip(ctx):
    embed = discord.Embed(
        title="🏆・***VIP***",
        description="💎 Torne-se ***VIP*** agora e desbloqueie ***vantagens exclusivas!***\n",
        color=0x7289DA
    )
    embed.add_field(
        name="Beneficios De Compras\n",
        value=(
            "1️⃣ **20% de desconto** em **qualquer compra**!\n"
            "2️⃣ **promoções especiais** para **VIPS**!\n"
            "3️⃣ Compras acima de **20 R$** ganha **qualquer produto** de **graça**\n"
        ),
        inline=False
    )

    embed.add_field(
        name="Beneficios Da Comunidade\n",
        value=(
            "4️⃣ Acesso a **chat Privado** para **Vips**\n"
            "5️⃣ **Call privada** para **VIP**\n"
            "6️⃣ Tag de **VIP**\n"
        ),
        inline=False
    )

    embed.add_field(
        name="Beneficios No Servidor\n",
        value=(
            "7️ **Suporte Prioritário**\n"
            ":eight: ***E MUITO MAIS!!!***\n"
        ),
        inline=False
    )

    embed.set_footer(text="Todos os direitos reservados. © Cyber Void")

    file = discord.File("logo.png", filename="logo.png")
    embed.set_image(url="attachment://logo.png")

    await ctx.send(file=file, embed=embed)

# =====================================================
# Compra do vip
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def compra_vip(ctx):
    embed = discord.Embed(
        title="🥇・***VIP***",
        description="Compre o ***VIP*** por apenas **R$9,99 Mensal**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar!",
        color=discord.Color.purple()
    )

    button = Button(label="Comprar Vip", style=discord.ButtonStyle.green, emoji="💎")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "***Vip***")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# =====================================================
# Envia a mensagem do Produto 2 (ex: Rat)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def rat(ctx):
    embed = discord.Embed(
        title="🐭・Rat",
        description="Compre o seu Malware favorito por apenas **R$10,00**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.",
        color=discord.Color.purple()
    )

    button = Button(label="Comprar Rat", style=discord.ButtonStyle.green, emoji="💎")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "Rat")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)


# =====================================================
# Envia a mensagem do Produto 2 (ex: raider)
# =====================================================
@bot.command()
async def raider(ctx):
    embed = discord.Embed(
        title="🎲・raider Dicord",
        description="Compre seu script de bot para raidar servers por **R$20,00**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nTutorial incluso. Clique no botão abaixo para comprar.",
        color=discord.Color.blue()
    )
    button = Button(label="Comprar raider Dicord",style=discord.ButtonStyle.green, emoji="🎲")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "raider Dicord")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)


# =====================================================
# Envia a mensagem do Produto 3 (ex: Ransomware)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def Ransomware(ctx):
    embed = discord.Embed(
        title="💻・Ransomware",
        description="Compre seu Ransomware por **R$10,00**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.",
        color=discord.Color.gold()
    )

    button = Button(label="Comprar Ransomware", style=discord.ButtonStyle.green, emoji="💻")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "Ransomware")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# =====================================================
# Envia a mensagem do Produto 3 (ex: Keylloger)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def Keylloger(ctx):
    embed = discord.Embed(
        title="🎯・Keylloger",
        description="Compre seu Keylloger por **R$9,99**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.",
        color=discord.Color.purple()
    )

    button = Button(label="Comprar Keylloger", style=discord.ButtonStyle.green, emoji="🎯")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "Keylloger")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# =====================================================
# Envia a mensagem do Produto 3 (ex: Minerador)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def Minerador(ctx):
    embed = discord.Embed(
        title="💳・Minerador (BTC/MNR)",
        description="Compre seu Minerador e fique RICO! por **R$10,00**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.",
        color=discord.Color.gold()
    )

    button = Button(label="Comprar Minerador", style=discord.ButtonStyle.green, emoji="💳")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "Minerador")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# =====================================================
# Envia a mensagem do Produto 3 (ex: Killers)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def Killers(ctx):
    embed = discord.Embed(
        title="💀・Killers",
        description="Compre seu **Killer!** por **R$14,99**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.",
        color=discord.Color.purple()
    )

    button = Button(label="Comprar Killers", style=discord.ButtonStyle.green, emoji="💀")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "Killers")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# =====================================================
# Envia a mensagem do Produto 3 (ex: Jogos)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def Jogos(ctx):
    embed = discord.Embed(
        title="🎮・Jogos Steam",
        description="Compre qualquer jogo da Steam por **R$9,99**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.\n\nATENÇÃO!: fifa 25 não está funcionando",
        color=discord.Color.gold()
    )

    button = Button(label="Comprar Jogos na Steam",style=discord.ButtonStyle.green, emoji="🎮")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "Steam")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

# =====================================================
# Envia a mensagem do Produto 3 (ex: personalizado)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def personalizado(ctx):
    embed = discord.Embed(
        title="🔐・Programa personalizado",
        description="Compre qualquer programa por **Preço Personalizado**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para comprar.",
        color=discord.Color.gold()
    )

    button = Button(label="Começar",style=discord.ButtonStyle.green, emoji="🔐")

    async def button_callback(interaction):
        await criar_canal_compra(interaction, "personalizado")

    button.callback = button_callback

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)


# =====================================================
# Envia a mensagem do Produto 3 (ex: vip)
# =====================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def vip(ctx):
    embed = discord.Embed(
        title="💎・Vip",
        description="Compre qualquer programa por **COM DISCONTO DE 20%**!\nMetodo de pagamento: **Pix | Bitcoin**\n\nClique no botão abaixo para ir as compras!",
        color=discord.Color.gold()
    )

    button = Button(label="Começar",style=discord.ButtonStyle.green, emoji="🔐")

    canal_destino_id = 1371274071551250553    # Substitua pelo ID do canal 'rat'

    button = Button(label="Começar", style=discord.ButtonStyle.link, emoji="🔐",url=f"https://discord.com/channels/{ctx.guild.id}/{canal_destino_id}")

    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)
    
bind_dummy_port()
bot.run(TOKEN)
