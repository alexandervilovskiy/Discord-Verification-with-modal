import discord
import random

intents = discord.Intents.default()
intents.members = True
client = discord.Bot(intents=intents)

VERIFIED_ROLE_ID = 1234567890 #роль которая должна выдастя
ALLOWED_USER_ID = 1183243638659096728 #айди создателя(только одного)
user_codes = {}
registered_users = {}
verification_active = True

def generate_code():
    return str(random.randint(1000, 9999))

@client.event
async def on_ready():
    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.streaming,
            name="https://swated.ru"
        )
    )
    print(f'Logged in as: {client.user.name}#{client.user.discriminator}')

@client.slash_command(description="Активировать верификацию", guild_ids=None)
async def activate_verification(ctx):
    if ctx.user.id != ALLOWED_USER_ID:
        await ctx.respond("У вас нет прав для использования этой команды.", ephemeral=True)
        return

    global verification_active
    verification_active = True
    await ctx.respond("Верификация активирована! Теперь каждый может пройти верификацию.", ephemeral=True)

@client.slash_command(description="Зарегистрироваться", guild_ids=None)
async def register(ctx):
    if ctx.user.id in registered_users:
        await ctx.respond("Вы уже зарегистрированы!", ephemeral=True)
        return

    registered_users[ctx.user.id] = True
    await ctx.respond(
        "Вы успешно зарегистрированы! Теперь вы можете пройти верификацию, используя команду /send_verification.",
        ephemeral=True
    )

@client.slash_command(description="Отправить сообщение с верификацией", guild_ids=None)
async def send_verification(ctx):
    if not verification_active:
        await ctx.respond("Верификация еще не активирована. Пожалуйста, обратитесь к администратору.", ephemeral=True)
        return

    if ctx.user.id not in registered_users:
        await ctx.respond("Вы должны сначала зарегистрироваться, используя команду /register.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Верификация",
        description="Серверу требуется проверить,что ты не робот,пройди верефикацию,нажав на кнопку ниже:",
        color=0x000000  # Черный цвет через HEX-код
    )

    button = discord.ui.Button(label="Пройти верификацию", style=discord.ButtonStyle.primary)

    async def button_callback(interaction: discord.Interaction):
        if VERIFIED_ROLE_ID in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "Вы уже прошли верификацию!", ephemeral=True
            )
            return

        verification_code = generate_code()
        user_codes[interaction.user.id] = verification_code

        modal = discord.ui.Modal(
            title="Введите код верификации"
        )

        input_field = discord.ui.InputText(
            label="Код верификации",
            placeholder=f"Ваш код: {verification_code}"
        )
        modal.add_item(input_field)

        async def modal_callback(modal_interaction: discord.Interaction):
            user_input = input_field.value

            if user_input == user_codes.get(interaction.user.id):
                try:
                    role = discord.utils.get(interaction.guild.roles, id=VERIFIED_ROLE_ID)
                    await interaction.user.add_roles(role)
                    await modal_interaction.response.send_message(
                        f"Поздравляем, {interaction.user.mention}, вы успешно прошли верификацию!", ephemeral=True
                    )
                    user_codes.pop(interaction.user.id, None)
                except discord.Forbidden:
                    await modal_interaction.response.send_message(
                        "Ошибка: не удалось добавить роль. Проверьте права бота.", ephemeral=True
                    )
                except discord.HTTPException as e:
                    await modal_interaction.response.send_message(
                        f"Произошла ошибка при добавлении роли: {str(e)}", ephemeral=True
                    )
            else:
                await modal_interaction.response.send_message(
                    "Неверный код. Пожалуйста, попробуйте снова.", ephemeral=True
                )

        modal.callback = modal_callback
        await interaction.response.send_modal(modal)

    button.callback = button_callback

    view = discord.ui.View()
    view.add_item(button)

    await ctx.respond(embed=embed, view=view)

client.run('ТОКЕН БОТА')
