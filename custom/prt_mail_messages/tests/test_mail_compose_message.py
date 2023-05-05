###################################################################################
# 
#    Copyright (C) Cetmix OÜ
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo.tests import Form

from .common import MailMessageCommon


class TestMailComposeMessage(MailMessageCommon):
    """
    TEST 1 : Check valid fields value in forward mode
    TEST 2 : Check behavior get_record_data function
    TEST 3 : Check preparing partners by parent mail message record
    TEST 4 : Check default signature location
    """

    def setUp(self):
        super(TestMailComposeMessage, self).setUp()

    # -- TEST 1 : Check valid fields value in forward mode
    def test_valid_forward_reference(self):
        """Check valid fields value in forward mode"""
        with Form(
            self.env["mail.compose.message"].with_context(
                default_wizard_mode="forward",
            )
        ) as form:
            form.partner_ids.add(self.res_partner_kate)
            form.forward_ref = f"res.partner,{self.res_partner_kate.id}"
            form.subject = "Test Forward Compose"
            self.assertEqual(
                form.model, "res.partner", msg="Model must be equal to res.partner"
            )
            self.assertEqual(
                form.res_id,
                self.res_partner_kate.id,
                msg=f"Res ID must be equal to {self.res_partner_kate.id}",
            )

    # -- TEST 2 : Check behavior get_record_data function
    def test_compose_message_record_data(self):
        """Check behavior get_record_data function"""
        record_data = (
            self.env["mail.compose.message"]
            .with_context(default_subject="Custom Subject")
            .get_record_data({})
        )
        keys = list(record_data.keys())
        self.assertListEqual(keys, ["subject"], msg="Keys must be the same")
        self.assertEqual(
            record_data.get("subject"),
            "Custom Subject",
            msg="Subject value must be equal to 'Custom Subject'",
        )
        record_data = self.env["mail.compose.message"].get_record_data(
            {"parent_id": self.mail_message_parent.id}
        )
        keys = list(record_data.keys())
        self.assertListEqual(
            keys,
            ["record_name", "model", "res_id", "partner_ids", "subject"],
            msg="Keys must be the same",
        )
        self.assertEqual(
            record_data.get("record_name"),
            "Kate",
            msg="Record Name must be equal to 'Kate'",
        )
        self.assertListEqual(
            record_data.get("partner_ids"),
            [(4, self.res_partner_kate.id), (4, self.res_partner_mark.id)],
            msg="Partners must be the same",
        )
        self.assertEqual(
            record_data.get("model"),
            "res.partner",
            msg="Model must be equal to 'res.partner'",
        )
        self.assertEqual(
            record_data.get("res_id"),
            self.res_partner_kate.id,
            msg=f"Res ID must be equal to {self.res_partner_kate.id}",
        )
        self.assertEqual(
            record_data.get("subject"),
            "Re: Kate",
            msg="Subject value must be equal to 'Re: Kate'",
        )
        record_data = self.env["mail.compose.message"].get_record_data(
            {"model": "res.partner", "res_id": self.res_partner_kate.id}
        )
        keys = list(record_data.keys())
        self.assertListEqual(
            keys, ["record_name", "subject"], msg="Keys must be the same"
        )
        record_data = (
            self.env["mail.compose.message"]
            .with_context(default_wizard_mode="forward")
            .get_record_data(
                {"model": "res.partner", "res_id": self.res_partner_kate.id}
            )
        )
        keys = list(record_data.keys())
        self.assertListEqual(
            keys, ["record_name", "subject"], msg="Keys must be the same"
        )
        self.assertEqual(
            record_data.get("subject"),
            "Fwd: Kate",
            msg="Subject value must be equal to 'Fwd: Kate'",
        )

    # -- TEST 3 : Check preparing partners by parent mail message record
    def test_prepare_valid_record_partners(self):
        """Check preparing partners by parent mail message record"""
        MailCompose = self.env["mail.compose.message"]
        partner_ids = MailCompose._prepare_valid_record_partners(
            self.mail_message_parent, []
        )
        partners = [(4, self.res_partner_kate.id), (4, self.res_partner_mark.id)]
        self.assertListEqual(partner_ids, partners, msg="Partners must be the same")
        partner_ids = MailCompose._prepare_valid_record_partners(
            self.mail_message_parent, [(6, 0, self.res_partner_kate.ids)]
        )
        self.assertListEqual(
            partner_ids,
            [(6, 0, self.res_partner_kate.ids)] + partners,
            msg="Partners must be the same",
        )
        partner_ids = MailCompose.with_context(
            is_private=True
        )._prepare_valid_record_partners(self.mail_message_parent, [])
        self.assertListEqual(
            partner_ids,
            partners + [(4, self.res_partner_ann.id)],
            msg="Partners must be the same",
        )

    # -- TEST 4 : Check default signature location
    def test_default_signature_location(self):
        """Check default signature location"""
        MailCompose = self.env["mail.compose.message"]
        ICPSudo = self.env["ir.config_parameter"].sudo()

        ICPSudo.set_param("cetmix.message_signature_location", "a")
        self.assertEqual(
            MailCompose._default_signature_location(),
            "a",
            msg="Default signature location must be equal to 'a' (Message bottom)",
        )
        ICPSudo.set_param("cetmix.message_signature_location", "b")
        self.assertEqual(
            MailCompose._default_signature_location(),
            "b",
            msg="Default signature location must be equal to 'a' (Before quote)",
        )
        ICPSudo.set_param("cetmix.message_signature_location", "n")
        self.assertEqual(
            MailCompose._default_signature_location(),
            "n",
            msg="Default signature location must be equal to 'n' (No signature)",
        )
