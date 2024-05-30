account-bind =
    Для подключения Userbot понадобятся следующие данные:

    🔑 <b>api_id</b>
    🔑 <b>api_hash</b>
    📱 <b>Номер телефона</b>

    Получите 🔑 <b>api_id</b> и 🔑 <b>api_hash</b> по ссылке 👉🏻 { $link }.


account-bind-button-register_me = 🤖 Зарегистрируй за меня
account-bind-button-i_registered = ✅ Я уже зарегистрировался
account-bind-button-send_contact = 📱 Отправить контакт


account-bind-enter_phone = 📱 Введите номер на который хотите зарегистрировать аккаунт или нажмите на кнопку ниже для отправки номера телефона.
account-bind-cancel = Вы отменили регистрацию аккаунта.

account-bind-enter_register_code = 🔢 Введите код подтверждения, который вам пришел в Telegram. 💬

account-bind-register_error =
    ⚠️ Произошла ошибка при регистрации аккаунта:
    Попробуйте еще раз или зарегистрируйте аккаунт вручную и введите данные выбрав пункт меню "✅ Я уже зарегистрировался".


account-bind-wait = ⏳ Пожалуйста, подождите...
account-bind-wait_register = 🔍 Идет регистрация аккаунта. ⏳ Пожалуйста, подождите...
account-bind-got_code = ✅ Код подтверждения получен. ⏳ Пожалуйста, подождите...
account-bind-got_data =
    🎉 Данные api получены. Сохраните их в безопасном месте:
    🔑 <b>api_id</b>: { $api_id }
    🔑 <b>api_hash</b>: { $api_hash }
    📱 <b>Номер телефона</b>: { $phone }
    <code>{ $data }</code>

account-bind-enter_data = 📝 Введите данные в формате <code>api_id:api_hash:phone_number</code>.
    Например: 123445:asdf31234fads:79622231741


account-bind-limit =
    Вы не можете привязать больше { $limit } аккаунтов к этому аккаунту.
    Пожалуйста, удалите один из них или купите подписку для привязки большего количества аккаунтов.


account-bind-invalid_data =
    Неверный формат данных. Пожалуйста, введите данные в формате api_id:api_hash:phone_number.
    Например: 123445:asdf31234fads:79622231741

account-bind-already_exists = Аккаунт с такими данными уже привязан к другому пользователю.


account-bind-enter_password = Введите пароль от 2FA для аккаунта { $phone }.
account-bind-enter_code =
    Введите код подтверждения для аккаунта { $phone }.
    Код вводит с префиксом code, например code12345

account-bind-incorrect_password = Неверный пароль. Пожалуйста, попробуйте еще раз.
account-bind-incorrect_code_input = Неправильно введен код подтверждения. Введите код с префиксом code, например code12345
    Если введены только цифры Telegram аннулирует код.

account-bind-incorrect_code_string = Введите только цифры кода подтверждения с префиксом code, например code12345

account-bind-incorrect_code = Неверный код подтверждения. Пожалуйста, попробуйте еще раз.

account-bind-timeout = ⏳🔌 Время ожидания подключения аккаунта истекло. 🔁 Для повторной попытки начните сначала.

account-bind-error = Произошла ошибка при подключении аккаунта:
    { $error }
    Пожалуйста, попробуйте еще раз.

account-dispatcher-start-error = Произошла ошибка при запуске диспетчера.
    { $error }
    Обратитесь к администратору.

account-bind-success = Аккаунт { $phone } привязан к вашему аккаунту.
account-dispatcher-start-success = Диспетчер для аккаунта { $phone } успешно запущен.

account-button-bind_account = Привязать аккаунт
account-menu = Текущие подключенные аккаунты:
account-button-update-statistics = 🔃 Обновить статистику
account-button-autoanswer = 🤖 Автоответы
account-button-unbind_account = 🗑 Удалить аккаунт
account-button-restart_account = 🔄 Перезапустить аккаунт
account-status-not_active = ❌ Неактивен
account-status-active = ✅ Активен
account-status-blocked = 🚫 Заблокирован

account-not_found = Аккаунт не найден.
account-unbind-confirm = Вы уверены, что хотите удалить аккаунт { $account }?
stop-dispatcher-success = Диспетчер для аккаунта { $identifier } успешно остановлен.
stop-dispatcher-error = Произошла ошибка при остановке диспетчера. Обратитесь к администратору.
account-deleted = Аккаунт { $identifier } успешно удален.


account-restart-success = Аккаунт успешно перезапущен.
account-restart-failed =
    Произошла ошибка при перезапуске аккаунта.
    { $error }
    Возможно, аккаунт уже запущен или проходят технические работы на сервере.
    Обратитесь к администратору.


account-not_found = Аккаунт не найден.
account-start_invite =
    Введите ссылки на группы из которого и в который будут приглашены пользователи через тире.
    Например: https://t.me/group1 - https://t.me/group2

# Приглашение пользователей запущено

account-inviting =  📩 Приглашение пользователей запущено.
account-invite_in_progress = ⏳ Приглашение пользователей уже запущено.
account-invite_canceled = ⏹ Приглашение пользователей остановлено.
account-invite_finished = ✅ Приглашение пользователей завершено.
account-invite_not_started = ❌ Приглашение пользователей не запущено.

account-invite_canceling = ⏳ Остановка приглашения пользователей...

account-inviting-stats =  📩 Приглашение пользователей запущено.
    📊 Статистика:
    📤 Отправлено приглашений: { $invited }
    📥 Принято приглашений: { $joined }
    📝 Осталось приглашений: { $left }
    ⏳ Время работы: { $time }
    📈 Скорость: { $speed } приглашений в минуту
    📉 Осталось времени: { $time_left }
    📝 Ссылки:
    { $links }


account-button-start_invite = 📩 Запустить рассылку приглашений
account-button-cancel_invite = ⏹ Остановить рассылку приглашений