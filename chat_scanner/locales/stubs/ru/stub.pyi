from typing import Literal


class TranslatorRunner:
    def get(self, path: str, **kwargs) -> str: ...
    
    account: Account
    stop: Stop
    bonus: Bonus
    button: Button
    invite: Invite
    support: Support
    instruction: Instruction
    payment: Payment
    projects: Projects
    project: Project
    withdraw: Withdraw
    status: BotStatus
    # rate: RateStatus

    @staticmethod
    def start() -> Literal["""Главное меню"""]: ...

class BotStatus:
    def __call__(self) -> Literal["""Статус"""]: ...

    def on(self) -> Literal["""Активен"""]: ...

    def off(self) -> Literal["""Не активен"""]: ...

    def rate_off(self) -> Literal["""Не оплачено"""]: ...



class Account:
    bind: AccountBind
    dispatcher: AccountDispatcher
    button: AccountButton
    status: AccountStatus
    unbind: AccountUnbind
    restart: AccountRestart
    inviting: AccountInviting

    @staticmethod
    def menu() -> Literal["""Текущие подключенные аккаунты:"""]: ...

    @staticmethod
    def not_found() -> Literal["""Аккаунт не найден."""]: ...

    @staticmethod
    def deleted(*, identifier) -> Literal["""Аккаунт { $identifier } успешно удален."""]: ...

    @staticmethod
    def start_invite() -> Literal["""Введите ссылки на группы из которого и в который будут приглашены пользователи через тире.
Например: https://t.me/group1 - https://t.me/group2"""]: ...

    @staticmethod
    def invite_in_progress() -> Literal["""⏳ Приглашение пользователей уже запущено."""]: ...

    @staticmethod
    def invite_canceled() -> Literal["""⏹ Приглашение пользователей остановлено."""]: ...

    @staticmethod
    def invite_finished() -> Literal["""✅ Приглашение пользователей завершено."""]: ...

    @staticmethod
    def invite_not_started() -> Literal["""❌ Приглашение пользователей не запущено."""]: ...

    @staticmethod
    def invite_canceling() -> Literal["""⏳ Остановка приглашения пользователей..."""]: ...


class AccountBind:
    button: AccountBindButton

    @staticmethod
    def __call__(*, link) -> Literal["""Для подключения Userbot понадобятся следующие данные:

🔑 &lt;b&gt;api_id&lt;/b&gt;
🔑 &lt;b&gt;api_hash&lt;/b&gt;
📱 &lt;b&gt;Номер телефона&lt;/b&gt;

Получите 🔑 &lt;b&gt;api_id&lt;/b&gt; и 🔑 &lt;b&gt;api_hash&lt;/b&gt; по ссылке 👉🏻 { $link }."""]: ...

    @staticmethod
    def enter_phone() -> Literal["""📱 Введите номер на который хотите зарегистрировать аккаунт или нажмите на кнопку ниже для отправки номера телефона."""]: ...

    @staticmethod
    def cancel() -> Literal["""Вы отменили регистрацию аккаунта."""]: ...

    @staticmethod
    def enter_register_code() -> Literal["""🔢 Введите код подтверждения, который вам пришел в Telegram. 💬"""]: ...

    @staticmethod
    def register_error() -> Literal["""⚠️ Произошла ошибка при регистрации аккаунта:
Попробуйте еще раз или зарегистрируйте аккаунт вручную и введите данные выбрав пункт меню &#34;✅ Я уже зарегистрировался&#34;."""]: ...

    @staticmethod
    def wait() -> Literal["""⏳ Пожалуйста, подождите..."""]: ...

    @staticmethod
    def wait_register() -> Literal["""🔍 Идет регистрация аккаунта. ⏳ Пожалуйста, подождите..."""]: ...

    @staticmethod
    def got_code() -> Literal["""✅ Код подтверждения получен. ⏳ Пожалуйста, подождите..."""]: ...

    @staticmethod
    def got_data(*, api_id, api_hash, phone, data) -> Literal["""🎉 Данные api получены. Сохраните их в безопасном месте:
🔑 &lt;b&gt;api_id&lt;/b&gt;: { $api_id }
🔑 &lt;b&gt;api_hash&lt;/b&gt;: { $api_hash }
📱 &lt;b&gt;Номер телефона&lt;/b&gt;: { $phone }
&lt;code&gt;{ $data }&lt;/code&gt;"""]: ...

    @staticmethod
    def enter_data() -> Literal["""📝 Введите данные в формате &lt;code&gt;api_id:api_hash:phone_number&lt;/code&gt;.
Например: 123445:asdf31234fads:79622231741"""]: ...

    @staticmethod
    def limit(*, limit) -> Literal["""Вы не можете привязать больше { $limit } аккаунтов к этому аккаунту.
Пожалуйста, удалите один из них или купите подписку для привязки большего количества аккаунтов."""]: ...

    @staticmethod
    def invalid_data() -> Literal["""Неверный формат данных. Пожалуйста, введите данные в формате api_id:api_hash:phone_number.
Например: 123445:asdf31234fads:79622231741"""]: ...

    @staticmethod
    def already_exists() -> Literal["""Аккаунт с такими данными уже привязан к другому пользователю."""]: ...

    @staticmethod
    def enter_password(*, phone) -> Literal["""Введите пароль от 2FA для аккаунта { $phone }."""]: ...

    @staticmethod
    def enter_code(*, phone) -> Literal["""Введите код подтверждения для аккаунта { $phone }.
Код вводит с префиксом code, например code12345"""]: ...

    @staticmethod
    def incorrect_password() -> Literal["""Неверный пароль. Пожалуйста, попробуйте еще раз."""]: ...

    @staticmethod
    def incorrect_code_input() -> Literal["""Неправильно введен код подтверждения. Введите код с префиксом code, например code12345
Если введены только цифры Telegram аннулирует код."""]: ...

    @staticmethod
    def incorrect_code_string() -> Literal["""Введите только цифры кода подтверждения с префиксом code, например code12345"""]: ...

    @staticmethod
    def incorrect_code() -> Literal["""Неверный код подтверждения. Пожалуйста, попробуйте еще раз."""]: ...

    @staticmethod
    def timeout() -> Literal["""⏳🔌 Время ожидания подключения аккаунта истекло. 🔁 Для повторной попытки начните сначала."""]: ...

    @staticmethod
    def error(*, error) -> Literal["""Произошла ошибка при подключении аккаунта:
{ $error }
Пожалуйста, попробуйте еще раз."""]: ...

    @staticmethod
    def success(*, phone) -> Literal["""Аккаунт { $phone } привязан к вашему аккаунту."""]: ...


class AccountBindButton:
    @staticmethod
    def register_me() -> Literal["""🤖 Зарегистрируй за меня"""]: ...

    @staticmethod
    def i_registered() -> Literal["""✅ Я уже зарегистрировался"""]: ...

    @staticmethod
    def send_contact() -> Literal["""📱 Отправить контакт"""]: ...


class AccountDispatcher:
    start: AccountDispatcherStart


class AccountDispatcherStart:
    @staticmethod
    def error(*, error) -> Literal["""Произошла ошибка при запуске диспетчера.
{ $error }
Обратитесь к администратору."""]: ...

    @staticmethod
    def success(*, phone) -> Literal["""Диспетчер для аккаунта { $phone } успешно запущен."""]: ...


class AccountButton:
    update: AccountButtonUpdate

    @staticmethod
    def bind_account() -> Literal["""Привязать аккаунт"""]: ...

    @staticmethod
    def autoanswer() -> Literal["""🤖 Автоответы"""]: ...

    @staticmethod
    def unbind_account() -> Literal["""🗑 Удалить аккаунт"""]: ...

    @staticmethod
    def restart_account() -> Literal["""🔄 Перезапустить аккаунт"""]: ...

    @staticmethod
    def start_invite() -> Literal["""📩 Запустить рассылку приглашений"""]: ...

    @staticmethod
    def cancel_invite() -> Literal["""⏹ Остановить рассылку приглашений"""]: ...


class AccountButtonUpdate:
    @staticmethod
    def statistics() -> Literal["""🔃 Обновить статистику"""]: ...


class AccountStatus:
    @staticmethod
    def not_active() -> Literal["""❌ Неактивен"""]: ...

    @staticmethod
    def active() -> Literal["""✅ Активен"""]: ...

    @staticmethod
    def blocked() -> Literal["""🚫 Заблокирован"""]: ...


class AccountUnbind:
    @staticmethod
    def confirm(*, account) -> Literal["""Вы уверены, что хотите удалить аккаунт { $account }?"""]: ...


class Stop:
    dispatcher: StopDispatcher


class StopDispatcher:
    @staticmethod
    def success(*, identifier) -> Literal["""Диспетчер для аккаунта { $identifier } успешно остановлен."""]: ...

    @staticmethod
    def error() -> Literal["""Произошла ошибка при остановке диспетчера. Обратитесь к администратору."""]: ...


class AccountRestart:
    @staticmethod
    def success() -> Literal["""Аккаунт успешно перезапущен."""]: ...

    @staticmethod
    def failed(*, error) -> Literal["""Произошла ошибка при перезапуске аккаунта.
{ $error }
Возможно, аккаунт уже запущен или проходят технические работы на сервере.
Обратитесь к администратору."""]: ...


class AccountInviting:
    @staticmethod
    def __call__() -> Literal["""📩 Приглашение пользователей запущено."""]: ...

    @staticmethod
    def stats(*, invited, joined, left, time, speed, time_left, links) -> Literal["""📩 Приглашение пользователей запущено.
📊 Статистика:
📤 Отправлено приглашений: { $invited }
📥 Принято приглашений: { $joined }
📝 Осталось приглашений: { $left }
⏳ Время работы: { $time }
📈 Скорость: { $speed } приглашений в минуту
📉 Осталось времени: { $time_left }
📝 Ссылки:
{ $links }"""]: ...


class Bonus:
    button: BonusButton

    @staticmethod
    def __call__(*, bonus) -> Literal["""Мы дарим на твой реферальный счет { $bonus } ₽"""]: ...


class BonusButton:
    @staticmethod
    def continue_() -> Literal["""💼 Продолжить"""]: ...


class Button:
    language: ButtonLanguage

    @staticmethod
    def instruction() -> Literal["""📖 Инструкция"""]: ...

    @staticmethod
    def projects() -> Literal["""📁 Мои проекты"""]: ...

    @staticmethod
    def payment() -> Literal["""💳 Подписка"""]: ...

    @staticmethod
    def support() -> Literal["""📲 Тех поддержка"""]: ...

    @staticmethod
    def invite() -> Literal["""📨 Пригласить друга"""]: ...

    @staticmethod
    def accounts() -> Literal["""👥 Аккаунты"""]: ...

    @staticmethod
    def yes() -> Literal["""✅ Да"""]: ...

    @staticmethod
    def no() -> Literal["""❌ Нет"""]: ...

    @staticmethod
    def cancel() -> Literal["""❌ Отмена"""]: ...

    @staticmethod
    def back() -> Literal["""« Назад"""]: ...

    @staticmethod
    def menu() -> Literal["""🏠 В меню"""]: ...

    @staticmethod
    def name_project() -> Literal["""Без названия"""]: ...


class ButtonLanguage:
    @staticmethod
    def __call__() -> Literal["""🌐 Язык"""]: ...

    @staticmethod
    def ru() -> Literal["""🇷🇺 Русский"""]: ...

    @staticmethod
    def en() -> Literal["""🇺🇸 English"""]: ...


class Invite:
    button: InviteButton
    withdraw: InviteWithdraw

    @staticmethod
    def __call__(*, balance, count, list) -> Literal["""&lt;b&gt;💰 Зарабатывайте вместе с нами!&lt;/b&gt;

💳 Ваш баланс составляет: { $balance } ₽

👥 Количество приглашенных: { $count }

👥 Список последних 20 друзей, совершивших покупку:
    { $list }"""]: ...

    @staticmethod
    def instruction(*, min, percent, link) -> Literal["""&lt;b&gt;💳 Вывести средства&lt;/b&gt;

Вывод средств возможен от 💰{ $min } ₽
Для заказа трансфера свяжитесь с нашим менеджером, предоставив номер криптокошелька в боте Cryptobot 🤖

📨 Поделись своей реферальной ссылкой с другом и получи { $percent }% от всех его зачислений 👥💸

&lt;b&gt;Ссылка&lt;/b&gt;: { $link }"""]: ...


class InviteButton:
    @staticmethod
    def withdraw() -> Literal["""💳 Вывести средства"""]: ...


class InviteWithdraw:
    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;💳 Вывести средства&lt;/b&gt;

Отправьте номер криптокошелька, вид крипты, вид сети и сумму которые хотите вывести"""]: ...

    @staticmethod
    def not_enough(*, min) -> Literal["""&lt;b&gt;💳 Вывести средства&lt;/b&gt;

Минимальная сумма вывода: 💰 { $min } ₽"""]: ...

    @staticmethod
    def not_digit() -> Literal["""❌ Не верный формат суммы"""]: ...

    @staticmethod
    def sent() -> Literal["""&lt;b&gt;💳 Вывести средства&lt;/b&gt;

Ваш запрос отправлен. Вскоре с вами свяжется наш менеджер."""]: ...


class Support:
    sent: SupportSent

    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;📲 Тех поддержка&lt;/b&gt;

Напишите ваш вопрос👇"""]: ...


class SupportSent:
    button: SupportSentButton

    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;📲 Тех поддержка&lt;/b&gt;

&lt;i&gt;📨 Ваш вопрос отправлен. Вскоре вам ответит менеджер в этом окне, ожидайте...&lt;/i&gt;"""]: ...


class SupportSentButton:
    @staticmethod
    def again() -> Literal["""📨 Спросить еще"""]: ...

    @staticmethod
    def menu() -> Literal["""🏠 На главную"""]: ...


class Instruction:
    @staticmethod
    def __call__() -> Literal["""----"""]: ...


class Payment:
    button: PaymentButton
    subscription: PaymentSubscription
    tariff: PaymentTariff
    payment_system: PaymentPayment_system
    payment_system_cryptobot: PaymentPayment_system_cryptobot
    description: PaymentDescription

    @staticmethod
    def __call__(*, date, rate) -> Literal["""💳 Подписка Доступ к боту оплачен до { $date } { $rate }"""]: ...

    @staticmethod
    def loading() -> Literal["""⏳ Создание платежа... ⏳"""]: ...

    @staticmethod
    def created() -> Literal["""✅ Платеж создан

    Платеж успешно создан!
    Нажмите на кнопку ниже, чтобы перейти к оплате."""]: ...

    @staticmethod
    def i_paid() -> Literal["""💳 Проверка оплаты происходит автоматически в течение 1 минуты после оплаты
    Ожидайте уведомление об успешной оплате в течение этого времени.
    Если бот не увидел платеж, сообщите об этом нам в поддержку."""]: ...

    @staticmethod
    def success(*, duration) -> Literal["""✅ Успешная оплата

    Ваша подписка продлена на { $duration } дней"""]: ...


class PaymentButton:
    @staticmethod
    def extend() -> Literal["""💳 Продлить подписку"""]: ...

    @staticmethod
    def buy() -> Literal["""💳 Купить подписку"""]: ...

    @staticmethod
    def pay() -> Literal["""💳 Оплатить"""]: ...

    @staticmethod
    def i_paid() -> Literal["""✅ Я оплатил"""]: ...

    @staticmethod
    def cancel() -> Literal["""❌ Отказаться"""]: ...

    @staticmethod
    def upgrade_subscription() -> Literal["""Перейти на PRO"""]: ...


class PaymentTariff:
    button: PaymentTariffButton

    @staticmethod
    def __call__() -> Literal["""Выбрать тариф"""]: ...

class PaymentTariffButton:

    @staticmethod
    def standart() -> Literal["""Стандарт"""]: ...

    @staticmethod
    def pro() -> Literal["""Про"""]: ...


class PaymentSubscription:
    button: PaymentSubscriptionButton

    @staticmethod
    def __call__(*, rate) -> Literal["""💳 Оплата подписки 
    Выбранный тариф: { $rate }
    💰 Стоимость подписки зависит от выбранного пакета.
    😉 Рекомендуем выбрать максимальный пакет, чтобы получить приятную скидку"""]: ...

    @staticmethod
    def expired() -> Literal["""❌ Подписка истекла ❌
    Ваша подписка истекла, для продления подписки нажмите на кнопку ниже."""]: ...

    @staticmethod
    def expired_three_days() -> Literal["""Подписка истекла 3 дня назад - оплатите или удалим данные"""]: ...

    @staticmethod
    def expired_five_days() -> Literal["""Подписка истекла 5 дней назад - оплатите или удалим данные завтра"""]: ...

class PaymentSubscriptionButton:
    @staticmethod
    def month_1(*, price_1) -> Literal["""1 месяц - { $price_1 } руб"""]: ...

    @staticmethod
    def month_6(*, price_6) -> Literal["""6 месяцев - { $price_6 } руб"""]: ...

    @staticmethod
    def month_12(*, price_12) -> Literal["""12 месяцев - { $price_12 } руб"""]: ...



class PaymentPayment_system_cryptobot:#я делал
    button: PaymentPayment_system_cryptobotButton

    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;💳 Выбери монету для платежа &lt;/b&gt;"""]: ...

class PaymentPayment_system_cryptobotButton:

    @staticmethod
    def usdt() -> Literal["""USDT"""]: ...

    @staticmethod
    def ton() -> Literal["""TON"""]: ...

    @staticmethod
    def btc() -> Literal["""BTC"""]: ...


class PaymentPayment_system:
    button: PaymentPayment_systemButton

    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;💳 Выбери платежную систему&lt;/b&gt;"""]: ...


class PaymentPayment_systemButton:

    @staticmethod
    def wallet() -> Literal["""Wallet"""]: ...

    @staticmethod
    def yookassa() -> Literal["""ЮKassa"""]: ...

    @staticmethod
    def btc() -> Literal["""ЮKassa"""]: ...

    @staticmethod
    def usdt() -> Literal["""ЮKassa"""]: ...

    @staticmethod
    def ton() -> Literal["""ЮKassa"""]: ...

    @staticmethod
    def cryptobot() -> Literal["""cryptobot"""]: ...


class PaymentDescription:
    @staticmethod
    def __call__(*, month, currency, price, rate) -> Literal["""Подписка на { $month } - { $currency } { $price }"""]: ...

    @staticmethod
    def month_1() -> Literal["""1 месяц"""]: ...

    @staticmethod
    def month_6() -> Literal["""6 месяцев"""]: ...

    @staticmethod
    def month_12() -> Literal["""12 месяцев"""]: ...

    @staticmethod
    def upgrade_info() -> Literal["""Эта опция доступна только на тарифе PRO"""]: ...

class Projects:
    button: ProjectsButton

    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;📁 Мои проекты&lt;/b&gt;"""]: ...


class ProjectsButton:
    @staticmethod
    def create() -> Literal["""➕ Добавить проект"""]: ...

    @staticmethod
    def settings() -> Literal["""⚙️ Общие Настройки"""]: ...


class Project:
    button: ProjectButton
    delete: ProjectDelete
    status: ProjectStatus
    duplicates: ProjectDuplicates
    post_settings: ProjectPostSettings
    response: ProjectResponse
    name: ProjectName
    connect: ProjectConnect
    keyword: ProjectKeyword
    keywords: ProjectKeywords
    signatures: ProjectSignatures
    deferred_messages: ProjectDeferredMessages
    replacing_text: ProjectReplacingText
    replacing_text_1: ProjectReplacingText_1
    replacing_text_2: ProjectReplacingText_2


    @staticmethod
    def __call__(*, name) -> Literal["""&lt;i&gt;Проект&lt;/i&gt;: &lt;b&gt;{ $name }&lt;/b&gt;"""]: ...

    @staticmethod
    def deleted() -> Literal["""✅ Проект удален"""]: ...

    @staticmethod
    def not_found() -> Literal["""🚫 Проект не найден"""]: ...


class ProjectButton:
    keywords: ProjectButtonKeywords
    stop_keywords: ProjectButtonStop_keywords
    allowed_senders: ProjectButtonAllowed_senders
    stop_senders: ProjectButtonStop_senders
    keyword: ProjectButtonKeyword
    stop_keyword: ProjectButtonStop_keyword
    allowed_sender: ProjectButtonAllowed_sender
    stop_sender: ProjectButtonStop_sender
    add: ProjectButtonAdd


    @staticmethod
    def name() -> Literal["""📋 Переименовать проект"""]: ...

    @staticmethod
    def connect() -> Literal["""🌐 Подключение групп"""]: ...

    @staticmethod
    def delete() -> Literal["""🗑 Удалить проект"""]: ...

    @staticmethod
    def duplicates() -> Literal["""🎬 Автоудаление"""]: ...

    @staticmethod
    def post_settings() -> Literal["""Настройки сообщений"""]: ...

    @staticmethod
    def signatures() -> Literal["""Добавление подписей"""]: ...

    @staticmethod
    def delete_signature() -> Literal["""Удалить подпись"""]: ...

    @staticmethod
    def deferred_messages() -> Literal["""⌛ Отложенная отправка"""]: ...

    @staticmethod
    def replacing_text() -> Literal["""🔁 Замена текста"""]: ...

    @staticmethod
    def posting_all() -> Literal["""📮 Пересылка: Все посты"""]: ...

    @staticmethod
    def posting_keywords() -> Literal["""📮 Пересылка: по ключам"""]: ...



class ProjectDelete:
    @staticmethod
    def confirm() -> Literal["""🚫 Для подтверждения нажмите еще раз"""]: ...


class ProjectStatus:
    button: ProjectStatusButton
    settings: ProjectStatusSettings

    @staticmethod
    def enabled() -> Literal["""🆗 Проект успешно включен"""]: ...

    @staticmethod
    def disabled() -> Literal["""🆗 Проект успешно отключен"""]: ...


class ProjectStatusButton:
    @staticmethod
    def disable() -> Literal["""✅ Проект включен"""]: ...

    @staticmethod
    def enable() -> Literal["""❌ Проект выключен"""]: ...


class ProjectStatusSettings:
    button: ProjectStatusSettingsButton

    @staticmethod
    def disabled() -> Literal["""🆗 Общие настройки успешно отключены"""]: ...

    @staticmethod
    def enabled() -> Literal["""🆗 Общие настройки успешно включены"""]: ...


class ProjectStatusSettingsButton:
    @staticmethod
    def disable() -> Literal["""✅ Общие настройки включены"""]: ...

    @staticmethod
    def enable() -> Literal["""❌ Общие настройки выключены"""]: ...


class ProjectDuplicates:
    button: ProjectDuplicatesButton

    @staticmethod
    def __call__() -> Literal["""🎬 Автоудаление"""]: ...

class ProjectDuplicatesButton:
    @staticmethod
    def enabled() -> Literal["""✅"""]: ...

    @staticmethod
    def disabled() -> Literal["""❌"""]: ...

    @staticmethod
    def text() -> Literal["""🔠 Удаление по тексту"""]: ...

    @staticmethod
    def user_id() -> Literal["""👥 Удаление по пользователю"""]: ...


class ProjectDeferredMessages:
    button: ProjectDeferredMessagesButton

    @staticmethod
    def __call__() -> Literal["""⌛ Отложенная отправка"""]: ...

class ProjectDeferredMessagesButton:
    @staticmethod
    def enabled() -> Literal["""✅"""]: ...

    @staticmethod
    def disabled() -> Literal["""❌"""]: ...

    @staticmethod
    def min_5() -> Literal["""30 минут"""]: ...

    @staticmethod
    def min_30() -> Literal["""30 минут"""]: ...

    @staticmethod
    def hours_1() -> Literal["""1 час"""]: ...

    @staticmethod
    def hours_3() -> Literal["""1 час"""]: ...

    @staticmethod
    def hours_6() -> Literal["""6 часов"""]: ...

    @staticmethod
    def hours_24() -> Literal["""24 часа"""]: ...

class ProjectReplacingText:
    button: ProjectReplacingTextButton

    @staticmethod
    def __call__() -> Literal["""🔁 Замена текста"""]: ...

    @staticmethod
    def add_keyword() -> Literal["""Добавить ключ"""]: ...

    @staticmethod
    def warning_long() -> Literal["""Ограничение длины ключа"""]: ...

    @staticmethod
    def warning_dublicate() -> Literal["""Дубль"""]: ...

class ProjectReplacingTextButton:
    @staticmethod
    def add_keyword() -> Literal["""Добавить ключ"""]: ...

    @staticmethod
    def skip() -> Literal["""Пропустить"""]: ...

class ProjectReplacingText_1:
    @staticmethod
    def __call__() -> Literal["""🔁 Замена текста 1"""]: ...

class ProjectReplacingText_2:
    @staticmethod
    def __call__() -> Literal["""🔁 Замена текста 2"""]: ...


class ProjectPostSettings:
    # button: ProjectPostSettingsButton

    @staticmethod
    def __call__() -> Literal["""Настройка сообщений"""]: ...


class ProjectSignatures:

    @staticmethod
    def __call__() -> Literal["""Добавление подписей"""]: ...


class ProjectResponse:
    button: ProjectResponseButton

    @staticmethod
    def __call__() -> Literal["""Сообщения"""]: ...


class ProjectResponseButton:
    @staticmethod
    def __call__() -> Literal["""Сообщения"""]: ...

    @staticmethod
    def include_username() -> Literal["""👥 Отправлять username"""]: ...

    @staticmethod
    def include_project_name() -> Literal["""📁 Отправлять название проекта"""]: ...

    @staticmethod
    def include_media() -> Literal["""🖼 Отправлять медиа"""]: ...

    @staticmethod
    def include_hashtags() -> Literal["""#️⃣ Хэштеги"""]: ...

    @staticmethod
    def include_usernames() -> Literal["""#️⃣ Юзернеймы"""]: ...

    @staticmethod
    def include_links_from_text() -> Literal["""📊 Ссылки"""]: ...

    @staticmethod
    def include_emoji() -> Literal["""Эмоджи"""]: ...

    @staticmethod
    def include_text() -> Literal["""📝 Отправлять ключевое слово"""]: ...

    @staticmethod
    def enabled() -> Literal["""✅"""]: ...

    @staticmethod
    def disabled() -> Literal["""❌"""]: ...


class ProjectName:
    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;📋 Переименовать проект&lt;/b&gt;

👇 Введите новое имя проекта"""]: ...

    @staticmethod
    def updated() -> Literal["""✅ Сохранено"""]: ...


class ProjectConnect:
    button: ProjectConnectButton
    receiver: ProjectConnectReceiver
    sender: ProjectConnectSender
    instruction: ProjectConnectInstruction
    receiver_forum: ProjectConnectReceiverForum

    @staticmethod
    def __call__(*, sender, receiver) -> Literal["""<b>🌐 Подключение групп и каналов</b>

📌 Для работы этого бота, требуется добавить данные групп/каналов отправителя/получателя и дать боту права администратора в группе/канале получателя.

<i>Для простого и быстрого подключения, нажмите на соответствующие кнопки ниже</i>

Актуальные данные👇

📤 <b>Отправитель:</b>
<i>{ $sender }</i>
--------------------
📥 <b>Получатель:</b>
<i>{ $receiver }</i>"""]: ...


class ProjectConnectInstruction:
    @staticmethod
    def instruction() -> Literal["""🌐 Подключение получателя

📌 При добавлении группы/канала впервые, нажмите кнопку "+ Новая группа" или "+ Новый канал"

Если требуемая группа/канал уже присутствует в других проектах, то выберите ее из списка ниже

"""]: ...


class ProjectConnectButton:
    @staticmethod
    def instruction() -> Literal["""📄 Инструкция"""]: ...

    @staticmethod
    def sender() -> Literal["""📤 Отправитель"""]: ...

    @staticmethod
    def receiver() -> Literal["""📥 Получатель"""]: ...

    @staticmethod
    def chait() -> Literal["""ВАЛИДАЦИЯ"""]: ...

    @staticmethod
    def channel() -> Literal[""" + Канал"""]: ...

    @staticmethod
    def channel_1() -> Literal["""+ Группа"""]: ...


    @staticmethod
    def channel_2() -> Literal["""+ Форум"""]: ...

    @staticmethod
    def choose_forum() -> Literal["""Выберите Форум"""]: ...


class ProjectConnectReceiver:
    @staticmethod
    def not_owner() -> Literal["""🚫 Вы не являетесь владельцем группы-получателя"""]: ...

    @staticmethod
    def not_found() -> Literal["""🚫 Группа-получатель не найдена"""]: ...

    @staticmethod
    def success(*, name) -> Literal["""✅ Группа-получатель добавлена к проекту { $name }"""]: ...

    @staticmethod
    def already_set(*, name) -> Literal["""🆗 Эта группа-получатель уже добавлена к проекту { $name }"""]: ...

    @staticmethod
    def input_id() -> Literal["""Введите id топика"""]: ...

    @staticmethod
    def minichat_success() -> Literal["""✅ Миничат успешно добавлен к группе-поулчателю"""]: ...

    @staticmethod
    def minichat_not_found() -> Literal["""Неверный формат ссылки/идентификатора миничата Группа-получатель не подключена!"""]: ...

    @staticmethod
    def attention_chat_blocking(*, chat_id, duration) -> Literal["""ВНИМАНИЕ FLOOD КОНТРОЛЬ { $chat_id }, { $duration }"""]: ...


class ProjectConnectReceiverForum:
    @staticmethod
    def __call__() -> Literal["""Подключение форума / выбор топика"""]: ...


class ProjectConnectSender:
    @staticmethod
    def __call__() -> Literal["""&lt;b&gt;🔌 Подключение групп&lt;/b&gt;

Введите ID, @username или ссылку группы, откуда будут отправляться данные"""]: ...

    @staticmethod
    def absent() -> Literal["""Отсутствует"""]: ...

    @staticmethod
    def success(*, name) -> Literal["""✅ Группа-отправитель добавлена к проекту { $name }"""]: ...

    @staticmethod
    def already_set(*, name) -> Literal["""🆗 Эта группа-отправитель уже добавлена к проекту { $name }"""]: ...

    @staticmethod
    def error() -> Literal["""🚫 Ошибка при добавлении группы-отправителя"""]: ...

    @staticmethod
    def no_accounts() -> Literal["""🚫 Нет доступных аккаунтов, обратитесь к администратору"""]: ...

    @staticmethod
    def not_found() -> Literal["""🚫 Группа-отправитель не найдена"""]: ...

    @staticmethod
    def can_not_get_chat() -> Literal["""🚫 Не удалось получить информацию о группе-отправителе
Если вы уверены, что ссылка на группу верная, то обратитесь к администратору"""]: ...

    @staticmethod
    def processing() -> Literal["""🔄 Добавление группы-отправителя ..."""]: ...

    @staticmethod
    def minichat_success() -> Literal["""Миничат подключен к чату-отправителю ..."""]: ...


class ProjectKeyword:
    type: ProjectKeywordType
    create: ProjectKeywordCreate
    delete: ProjectKeywordDelete

    @staticmethod
    def not_found(*, keyword_type) -> Literal["""🚫 { $keyword_type } не найдено"""]: ...

    @staticmethod
    def deleted(*, keyword_type) -> Literal["""✅ { $keyword_type } удалено"""]: ...


class ProjectKeywordType:
    @staticmethod
    def contains() -> Literal["""🔍 Фразовое соответствие"""]: ...

    @staticmethod
    def exact() -> Literal["""❗ Точное соответствие"""]: ...



class ProjectButtonKeywords:
    @staticmethod
    def __call__() -> Literal["""🔑 Ключевые слова"""]: ...

    @staticmethod
    def possessive() -> Literal["""🔑 Ключевых слов"""]: ...


class ProjectButtonStop_keywords:
    @staticmethod
    def __call__() -> Literal["""🚫 Стоп-слова"""]: ...

    @staticmethod
    def possessive() -> Literal["""🚫 Стоп-слов"""]: ...


class ProjectButtonAllowed_senders:
    @staticmethod
    def __call__() -> Literal["""✅ Отправители"""]: ...

    @staticmethod
    def possessive() -> Literal["""✅ Разрешенных отправителей"""]: ...


class ProjectButtonStop_senders:
    @staticmethod
    def __call__() -> Literal["""❌ Отправители"""]: ...

    @staticmethod
    def possessive() -> Literal["""❌ Запрещенных отправителей"""]: ...


class ProjectButtonKeyword:
    @staticmethod
    def __call__() -> Literal["""🔑 Ключевое слово"""]: ...

    @staticmethod
    def possessive() -> Literal["""🔑 Ключевого слова"""]: ...


class ProjectButtonStop_keyword:
    @staticmethod
    def __call__() -> Literal["""🚫 Стоп-слово"""]: ...

    @staticmethod
    def possessive() -> Literal["""🚫 Стоп-слова"""]: ...


class ProjectButtonAllowed_sender:
    @staticmethod
    def __call__() -> Literal["""✅ Отправитель"""]: ...

    @staticmethod
    def possessive() -> Literal["""✅ Отправителя"""]: ...


class ProjectButtonStop_sender:
    @staticmethod
    def __call__() -> Literal["""❌ Отправитель"""]: ...

    @staticmethod
    def possessive() -> Literal["""❌ Отправителя"""]: ...


class ProjectButtonAdd:
    @staticmethod
    def keyword(*, sign, keyword_type) -> Literal["""➕{ $sign } Добавить { $keyword_type }"""]: ...


class ProjectKeywords:
    @staticmethod
    def __call__(*, sign, keyword_type, formats) -> Literal["""&lt;b&gt;{ $sign } Список { $keyword_type }&lt;/b&gt;

{ $formats }
&lt;b&gt;Для удаления ключа - нажмите на него&lt;/b&gt;"""]: ...

    @staticmethod
    def formats(*, types) -> Literal["""<i> Помните, что обработка ключевиков происходит в форматах

{ $types }
</i>"""]: ...


class ProjectKeywordCreate:
    @staticmethod
    def __call__(*, keyword_type) -> Literal["""<b>🆕 Создание { $keyword_type }</b>"""]: ...

    @staticmethod
    def type(*, keyword_type, keyword_type) -> Literal["""<b>Создание { $keyword_type }</b>

    Пример работы соответствий:

    <i>🔍"Мир" - сработает на "Мир", "Мирный"
    ❗"Мир" - сработает только на "Мир"</i>

    Выберите требуемый тип👇"""]: ...

    @staticmethod
    def word(*, keyword_type, keyword_type) -> Literal["""<b>🆕 Создание { $keyword_type }</b>"""]: ...

    @staticmethod
    def warning() -> Literal["""⚠️ Внимание! Такой ключ уже есть в проекте"""]: ...

    @staticmethod
    def success(*, keyword_type, keyword, project_name) -> Literal["""✅ { $keyword_type } &#34;{ $keyword }&#34; добавлен к проекту { $project_name }"""]: ...


class ProjectKeywordDelete:
    @staticmethod
    def confirm() -> Literal["""🚫 Для подтверждения нажмите еще раз"""]: ...

    @staticmethod
    def signature(*, signature) -> Literal["""Подпись проекта: {signature}"""]: ...


class Withdraw:
    what_currency: WithdrawWhat_currency

    @staticmethod
    def how_much() -> Literal["""Сколько планируете вывести?"""]: ...

    @staticmethod
    def what_wallet() -> Literal["""Номер вашего кошелька?"""]: ...

    @staticmethod
    def success() -> Literal["""Сообщение отправлено, ожидайте…"""]: ...


class WithdrawWhat_currency:
    button: WithdrawWhat_currencyButton

    @staticmethod
    def __call__() -> Literal["""В какой валюте?"""]: ...


class WithdrawWhat_currencyButton:
    @staticmethod
    def btc() -> Literal["""BTC"""]: ...

    @staticmethod
    def ton() -> Literal["""TON"""]: ...

    @staticmethod
    def usdt() -> Literal["""USDT"""]: ...

