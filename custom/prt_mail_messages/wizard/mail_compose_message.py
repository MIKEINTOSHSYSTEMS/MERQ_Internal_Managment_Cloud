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

from odoo import _, api, fields, models, tools

from ..models.common import DEFAULT_SIGNATURE_LOCATION


########################
# Mail.Compose Message #
########################
class MailComposer(models.TransientModel):
    _inherit = "mail.compose.message"

    wizard_mode = fields.Char()
    forward_ref = fields.Reference(
        string="Attach to record", selection="_referenceable_models_fwd", readonly=False
    )

    def _default_signature_location(self):
        """Set default signature location"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "cetmix.message_signature_location",
                DEFAULT_SIGNATURE_LOCATION,
            )
        )

    signature_location = fields.Selection(
        [("a", "Message bottom"), ("b", "Before quote"), ("n", "No signature")],
        default=_default_signature_location,
        required=True,
        help="Whether to put signature before or after the quoted text.",
    )

    # -- Send
    def _action_send_mail(self, auto_commit=False):
        return super(
            MailComposer,
            self.with_context(
                signature_location=self.signature_location,
                default_wizard_mode=self.wizard_mode,
            ),
        )._action_send_mail(auto_commit=auto_commit)

    # -- Ref models
    @api.model
    def _referenceable_models_fwd(self):
        return self.env["cx.model.reference"].referenceable_models()

    # -- Record ref change
    @api.onchange("forward_ref")
    def ref_change(self):
        self.ensure_one()
        if self.forward_ref:
            self.update(
                {"model": self.forward_ref._name, "res_id": self.forward_ref.id}
            )

    @api.model
    def _prepare_valid_record_partners(self, parent, partner_ids):
        """Prepare partners for record"""
        partner_ids = partner_ids + [
            (4, p.id)
            for p in parent.partner_ids.filtered(
                lambda rec: rec.email
                not in [self.env.user.email, self.env.user.company_id.email]
            )
        ]
        if self._context.get("is_private") and parent.author_id:
            # check message is private then add author also in partner list.
            partner_ids += [(4, parent.author_id.id)]
        return partner_ids

    @api.model
    def get_record_data(self, values):
        # Get record data
        result = super(MailComposer, self).get_record_data(values)
        subject = False
        subj = self._context.get("default_subject", False)
        if subj:
            return {"subject": tools.ustr(subj)}
        if values.get("parent_id"):
            parent = self.env["mail.message"].browse(values.get("parent_id"))
            result["partner_ids"] = self._prepare_valid_record_partners(
                parent, values.get("partner_ids", list())
            )
            subject = tools.ustr(parent.subject or parent.record_name or "")
        elif values.get("model") and values.get("res_id"):
            subject = tools.ustr(result.get("record_name"))

        # Change prefix in case we are forwarding
        if self._context.get("default_wizard_mode") == "forward" and subject:
            re_prefix = _("Fwd:")
            if not (subject.startswith("Fwd:") or subject.startswith(re_prefix)):
                result.update(subject="%s %s" % (re_prefix, subject))
        return result
