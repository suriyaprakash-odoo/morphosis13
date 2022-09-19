# -*- coding: utf-8 -*-
# Copyright 2017 Jarvis (www.odoomod.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from distutils.util import strtobool 


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        if partner_ids:
            for partner_id in partner_ids:
                get_users = self.env['res.users'].sudo().search([('partner_id','=',partner_id)],limit=1)
                if not get_users:
                    partner_ids.remove(partner_id)

        return super(MailThread, self).message_subscribe(partner_ids, channel_ids, subtype_ids)
        
        # ir_config = self.env['ir.config_parameter']
        # app_stop_subscribe = bool(strtobool(ir_config.sudo().get_param('app_stop_subscribe')))
        # if app_stop_subscribe:
        #     return
        # else:
        #     return super(MailThread, self).message_subscribe(partner_ids, channel_ids, subtype_ids)

    def _message_auto_subscribe(self, updated_fields, followers_existing_policy='update'):
        ir_config = self.env['ir.config_parameter']
        app_stop_subscribe = bool(strtobool(ir_config.sudo().get_param('app_stop_subscribe')))
        if app_stop_subscribe:
            return
        else:
            return super(MailThread, self)._message_auto_subscribe(updated_fields, followers_existing_policy='update')

    def _message_auto_subscribe_notify(self, partner_ids, template):
        ir_config = self.env['ir.config_parameter']
        app_stop_subscribe = bool(strtobool(ir_config.sudo().get_param('app_stop_subscribe')))
        if app_stop_subscribe:
            return
        else:
            return super(MailThread, self)._message_auto_subscribe_notify(partner_ids, template)