account-bind =
    To connect Userbot, you will need the following data:

    🔑 <b>api_id</b>
    🔑 <b>api_hash</b>
    📱 <b>Phone number</b>

    Obtain 🔑 <b>api_id</b> and 🔑 <b>api_hash</b> via the link 👉🏻 { $link }.


account-bind-button-register_me = 🤖 Register for me
account-bind-button-i_registered = ✅ I have already registered
account-bind-button-send_contact = 📱 Send contact


account-bind-enter_phone = 📱 Enter the number to which you want to register the account or press the button below to send the phone number.
account-bind-cancel = Account registration canceled.

account-bind-enter_register_code = 🔢 Enter the confirmation code that you received in Telegram. 💬

account-bind-register_error =
    ⚠️ An error occurred while registering the account:
    Please try again or register the account manually and enter the data by selecting the "✅ I have already registered" menu item.


account-bind-wait = ⏳ Please wait...
account-bind-wait_register = 🔍 Account registration is in progress. ⏳ Please wait...
account-bind-got_code = ✅ Confirmation code received. ⏳ Please wait...
account-bind-got_data =
    🎉 API data received. Save them in a secure place:
    🔑 <b>api_id</b>: { $api_id }
    🔑 <b>api_hash</b>: { $api_hash }
    📱 <b>Phone number</b>: { $phone }
    <code>{ $data }</code>

account-bind-enter_data = 📝 Enter the data in the format <code>api_id:api_hash:phone_number</code>.
    For example: 123445:asdf31234fads:79622231741


account-bind-limit =
    You cannot bind more than { $limit } accounts to this account.
    Please remove one of them or purchase a subscription to bind more accounts.


account-bind-invalid_data =
    Invalid data format. Please enter the data in the format api_id:api_hash:phone_number.
    For example: 123445:asdf31234fads:79622231741

account-bind-already_exists = An account with such data is already bound to another user.


account-bind-enter_password = Enter the 2FA password for the account { $phone }.
account-bind-enter_code =
    Enter the confirmation code for the account { $phone }.
    Enter the code with the prefix code, for example code12345.

account-bind-incorrect_password = Incorrect password. Please try again.
account-bind-incorrect_code_input = Incorrect confirmation code input. Enter the code with the prefix code, for example code12345.
    If only digits are entered, Telegram will cancel the code.

account-bind-incorrect_code_string = Enter only the digits of the confirmation code with the prefix code, for example code12345.

account-bind-incorrect_code = Incorrect confirmation code. Please try again.

account-bind-timeout = ⏳🔌 Account connection timeout. 🔁 To try again, start over.

account-bind-error = An error occurred while connecting the account:
    { $error }
    Please try again.

account-dispatcher-start-error = An error occurred while starting the dispatcher.
    { $error }
    Please contact the administrator.

account-bind-success = Account { $phone } is bound to your account.
account-dispatcher-start-success = Dispatcher for account { $phone } started successfully.

account-button-bind_account = Bind account
account-menu = Current connected accounts:
account-button-update-statistics = 🔃 Update statistics
account-button-autoanswer = 🤖 Auto answers
account-button-unbind_account = 🗑 Unbind account
account-button-restart_account = 🔄 Restart account
account-status-not_active = ❌ Not active
account-status-active = ✅ Active
account-status-blocked = 🚫 Blocked

account-not_found = Account not found.
account-unbind-confirm = Are you sure you want to delete account { $account }?
stop-dispatcher-success = Dispatcher for account { $identifier } stopped successfully.
stop-dispatcher-error = An error occurred while stopping the dispatcher. Please contact the administrator.
account-deleted = Account { $identifier } successfully deleted.


account-restart-success = Account successfully restarted.
account-restart-failed =
    An error occurred while restarting the account.
    { $error }
    Perhaps the account is already running or there are technical issues on the server.
    Please contact the administrator.


account-not_found = Account not found.
account-start_invite =
    Enter links to the groups from which and to which users will be invited separated by a hyphen.
    For example: https://t.me/group1 - https://t.me/group2

# User invitation started

account-inviting =  📩 User invitation started.
account-invite_in_progress = ⏳ User invitation already in progress.
account-invite_canceled = ⏹ User invitation stopped.
account-invite_finished = ✅ User invitation completed.
account-invite_not_started = ❌ User invitation not started.

account-invite_canceling = ⏳ Stopping user invitation...

account-inviting-stats =  📩 User invitation started.
    📊 Statistics:
    📤 Invitations sent: { $invited }
    📥 Invitations accepted: { $joined }
    📝 Invitations left: { $left }
    ⏳ Time worked: { $time }
    📈 Speed: { $speed } invitations per minute
    📉 Time left: { $time_left }
    📝 Links:
    { $links }


account-button-start_invite = 📩 Start invitation distribution
account-button-cancel_invite = ⏹ Stop invitation distribution
