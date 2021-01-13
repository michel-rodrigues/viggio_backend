from collections import namedtuple


MailRequest = namedtuple('MailRequest', 'to_email from_email template')

MailTemplate = namedtuple('GenericMailTemplate', 'name subject data')

OrderMailData = namedtuple(
    'OrderMailData',
    field_names=[
        'customer_name',
        'order_created_at',
        'talent_url',
        'talent_name',
        'order_instruction',
        'charge_amout_paid',
        'order_expiration_datetime',
    ]
)

NotifyTalentAboutNewOrderMailData = namedtuple(
    'NotifyTalentAboutNewOrderMailData',
    field_names=[
        'talent_name',
        'order_created_at',
        'customer_name',
        'order_instruction',
        'charge_amout_paid',
        'order_expiration_datetime',
        'order_is_to',
        'dashboard_url',
    ]
)

ShoutoutRequestFulfilledMailData = namedtuple(
    'ShoutoutRequestFulfilledMailData',
    field_names=[
        'order_is_to',
        'customer_name',
        'talent_name',
        'shoutout_absolute_url',
    ]
)

TalentEnrollmentMailData = namedtuple(
    'TalentEnrollmentMailData',
    field_names=[
        'email',
        'first_name',
        'last_name',
        'area_code',
        'phone_number',
        'main_social_media',
        'social_media_username',
        'number_of_followers',
    ]
)

ResetPasswordMailData = namedtuple(
    'ResetPasswordMailData',
    field_names=[
        'new_password',
        'first_name',
        'last_name',
    ]
)
