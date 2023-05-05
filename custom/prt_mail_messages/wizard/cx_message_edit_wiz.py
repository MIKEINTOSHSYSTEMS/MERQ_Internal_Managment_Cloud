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

from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import AccessError


#################
# Edit message #
#################
class MessageEdit(models.TransientModel):
    _name = "cx.message.edit.wiz"
    _description = "Edit Message or Note"

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        active_ids = self._context.get("active_ids", False)
        if active_ids:
            message = self.env["mail.message"].browse(active_ids[0])
            result.update(message_id=message.id, body=message.body)
        return result

    message_id = fields.Many2one(string="Message", comodel_name="mail.message")
    body = fields.Html(string="Message")
    can_edit = fields.Boolean(compute="_compute_can_edit")

    def _can_edit_by_group(self, all_, own):
        author_id = self.message_id.author_id.id
        partner_id = self.env.user.partner_id.id
        has_group = self.env.user.has_group
        return has_group(all_) or (has_group(own) and author_id == partner_id)

    # -- Can edit message?
    @api.depends("message_id", "message_id.author_id", "message_id.subtype_id")
    def _compute_can_edit(self):
        if not self.message_id:
            self.can_edit = False
            return

        if not self.message_id.author_id:
            self.can_edit = False
            return

        # Superuser can edit everything:
        if self.env.is_superuser():
            self.can_edit = True
            return

        # Check access rule
        try:
            self.message_id.check_access_rule("write")
        except AccessError:
            self.can_edit = False
            return

        subtype = self.message_id.subtype_id
        # Note
        if subtype == self.env.ref("mail.mt_note"):
            self.can_edit = self._can_edit_by_group(
                "prt_mail_messages.group_notes_edit_all",
                "prt_mail_messages.group_notes_edit_own",
            )
            return
        # Message
        if subtype == self.env.ref("mail.mt_comment") or not subtype:
            self.can_edit = self._can_edit_by_group(
                "prt_mail_messages.group_messages_edit_all",
                "prt_mail_messages.group_messages_edit_own",
            )
            return
        # Other types are not editable
        self.can_edit = False

    # -- Save message
    def save(self):
        """Save editing message"""
        if self.message_id and self.can_edit:
            self.message_id.write(
                {
                    "body": self.body,
                    "cx_edit_uid": self.env.user.id,
                    "cx_edit_date": datetime.now(),
                }
            )
