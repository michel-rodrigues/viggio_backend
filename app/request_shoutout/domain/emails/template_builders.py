import os
from datetime import timedelta

from request_shoutout.domain.models import Order, SP_TZ
from .templates import (
    MailTemplate,
    NotifyTalentAboutNewOrderMailData,
    OrderMailData,
    ResetPasswordMailData,
    ShoutoutRequestFulfilledMailData,
    TalentEnrollmentMailData,
)


def customer_order_detail_template_builder(order, talent):
    expiration_datetime = order.expiration_datetime - timedelta(hours=SP_TZ)
    data = OrderMailData(
        customer_name=(order.is_from if order.video_is_for == Order.SOMEONE_ELSE else order.is_to),
        order_created_at=order.created_at.date().strftime('%d/%m/%Y'),
        talent_url=talent.profile_url,
        talent_name=talent.user.get_full_name(),
        order_instruction=order.instruction,
        charge_amout_paid=float(order.charge.amount_paid),
        order_expiration_datetime=expiration_datetime.strftime('%d/%m/%Y - %Hh'),
    )
    subject = f'Seu pedido foi enviado para {talent.user.get_full_name()}'
    return MailTemplate(name='order-detail', subject=subject, data=data)


def notify_talent_about_new_order_template_builder(order, talent):
    expiration_datetime = order.expiration_datetime - timedelta(hours=SP_TZ)
    data = NotifyTalentAboutNewOrderMailData(
        talent_name=talent.user.get_full_name(),
        order_created_at=order.created_at.date().strftime('%d/%m/%Y'),
        customer_name=order.is_from,
        order_instruction=order.instruction,
        charge_amout_paid=float(order.charge.amount_paid),
        order_expiration_datetime=expiration_datetime.strftime('%d/%m/%Y - %Hh'),
        order_is_to=order.is_to,
        dashboard_url=os.environ['SITE_URL'] + 'dashboard/',
    )
    subject = 'Você tem um novo pedido'
    return MailTemplate(name='notify-talent-about-new-order', subject=subject, data=data)


def notify_customer_about_shoutout_request_fulfilled_template_builder(order, talent, shoutout):
    data = ShoutoutRequestFulfilledMailData(
        customer_name=order.is_from,
        order_is_to=order.is_to,
        talent_name=talent.user.get_full_name(),
        shoutout_absolute_url=shoutout.get_absolute_url(),
    )
    subject = f'Seu viggio está pronto'
    if order.video_is_for == Order.SOMEONE_ELSE:
        subject = f'Seu viggio para {order.is_to} está pronto'
    return MailTemplate(name='notify-customer-that-his-viggio-is-ready', subject=subject, data=data)


def enroll_talent_template_builder(data):
    mail_data = TalentEnrollmentMailData(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone_number=data['phone_number'],
        area_code=data['area_code'],
        main_social_media=data['main_social_media'],
        social_media_username=data['social_media_username'],
        number_of_followers=data['number_of_followers'],
    )
    subject = 'Pedido de inscrição de talento'
    return MailTemplate('notify-staff-about-new-talent-enrollment', subject, mail_data)


def user_reset_password_template_builder(new_password, first_name, last_name):
    mail_data = ResetPasswordMailData(
        first_name=first_name,
        last_name=last_name,
        new_password=new_password
    )
    subject = 'Pedido de nova senha'
    return MailTemplate('user-new-password', subject, mail_data)
