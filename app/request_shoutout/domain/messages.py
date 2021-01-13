
class RequestShoutoutCommand:
    NAME = 'RequestShoutout'

    def __init__(
        self,
        order_hash_id,
        order_video_is_for,
        order_is_to,
        order_instruction,
        order_email,
        order_talent_id,
        order_amount_paid,
        order_is_public,
        customer_fullname,
        customer_birthdate,
        customer_phone_number,
        customer_area_code,
        customer_tax_document,
        credit_card_owner_fullname,
        credit_card_owner_birthdate,
        credit_card_owner_phone_number,
        credit_card_owner_area_code,
        credit_card_owner_tax_document,
        credit_card_hash,
        order_is_from=None,
    ):
        self.order_hash_id = order_hash_id
        self.order_video_is_for = order_video_is_for
        self.order_is_from = order_is_from
        self.order_is_to = order_is_to
        self.order_instruction = order_instruction
        self.order_email = order_email
        self.order_talent_id = order_talent_id
        self.order_amount_paid = order_amount_paid
        self.order_is_public = order_is_public
        self.customer_fullname = customer_fullname
        self.customer_birthdate = customer_birthdate
        self.customer_phone_number = customer_phone_number
        self.customer_area_code = customer_area_code
        self.customer_tax_document = customer_tax_document
        self.credit_card_owner_fullname = credit_card_owner_fullname
        self.credit_card_owner_birthdate = credit_card_owner_birthdate
        self.credit_card_owner_phone_number = credit_card_owner_phone_number
        self.credit_card_owner_area_code = credit_card_owner_area_code
        self.credit_card_owner_tax_document = credit_card_owner_tax_document
        self.credit_card_hash = credit_card_hash


class ShoutoutSuccessfullyRequestedEvent:
    NAME = 'ShoutoutSuccessfullyRequested'

    def __init__(self, order):
        self.order = order


class FulfillShoutoutRequestCommand:
    NAME = 'FulfillShoutoutRequest'

    def __init__(self, shoutout_hash, order_hash, talent_id, video_file):
        self.shoutout_hash = shoutout_hash
        self.order_hash = order_hash
        self.video_file = video_file
        self.talent_id = talent_id


class CapturePaymentFailedEvent:
    NAME = 'CapturePaymentFailed'

    def __init__(self, order_hash):
        self.order_hash = order_hash


class ShoutoutUploadedEvent:
    NAME = 'ShoutoutUploaded'

    def __init__(self, order_hash):
        self.order_hash = order_hash


class ShoutoutSuccessfullyTranscodedEvent:
    NAME = 'ShoutoutSuccessfullTranscoded'

    def __init__(self, order_id):

        self.order_id = order_id
