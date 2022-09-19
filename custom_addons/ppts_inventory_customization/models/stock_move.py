# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    bsd_annexe = fields.Selection([
        ('bsd' , 'BSD'),
        ('annexe7' , 'Annexe7')
        ],string='BSD/Annexe7')
    container_ids = fields.Many2many('stock.container',string='Container',domain="[('content_type_id', '=', product_id),('state','!=','sold')]")
    actual_weight = fields.Float('Actual weight(Kg)')

    @api.onchange('container_ids')
    def onchange_actual_weight(self):
        if self.container_ids:
            self.actual_weight = 0.0
            for rec in self.container_ids:
                self.actual_weight += rec.net_weight

    def update_bsd(self):
        logistics=False
        if self.picking_type_id.sequence_code=='IN':
            logistics = self.env['logistics.management'].search([('origin','=',self.picking_id.project_entry_id.id),('status','=','approved')],limit=1)
        if self.picking_type_id.sequence_code=='OUT':
            logistics = self.env['logistics.management'].search([('sales_origin.name','=',self.picking_id.origin),('status','=','approved')],limit=1)
        adr_lines = []
        for loop in logistics.adr_line:
            adr_vals = (0,0,{
                'tunnel_code_id' : loop.tunnel_code_id.id,
                'adr_class_id':loop.adr_class_id.id,
                'adr_pickup_type_id': loop.adr_pickup_type_id.id,
                'hazard_type_id' :loop.hazard_type_id.id,
                'un_code':loop.un_code.id,
                'logistics_id':loop.logistics_id.id,
                'adrline_id':loop.id
            })
            adr_lines.append(adr_vals)

        vals = ({
                    'default_logistics_id':logistics.id,
                    'default_number_bsd':logistics.number_bsd,
                    'default_pickup_partner_id':logistics.pickup_partner_id.id,
                    'default_company_id':logistics.company_id.id,
                    'default_pickup_street':logistics.pickup_street,
                    'default_pickup_city':logistics.pickup_city,
                    'default_pickup_zip':logistics.pickup_zip,
                    'default_pickup_state_id':logistics.pickup_state_id.id,
                    'default_pickup_countries_id':logistics.pickup_countries_id.id,
                    'default_phone':logistics.pickup_partner_id.phone,
                    'default_email':logistics.pickup_partner_id.email,
                    'default_contact_person_in':'',
                    'default_contact_person_out':'',
                    'default_delivery_partner_id':logistics.delivery_partner_id.id,
                    'default_delivery_street':logistics.delivery_street,
                    'default_delivery_zip':logistics.delivery_zip,
                    'default_delivery_city':logistics.delivery_city,
                    'default_delivery_state_id':logistics.delivery_state_id.id,
                    'default_delivery_countries_id':logistics.delivery_countries_id.id,
                    'default_delivery_phone':logistics.delivery_partner_id.phone,
                    'default_delivery_email':logistics.delivery_partner_id.email,
                    'default_logistics_contact':logistics.partner_id.id,
                    'default_pretreatment_code':logistics.pretreatment_code,
                    'default_waste_code':logistics.waste_code,
                    'default_waste_form':logistics.waste_form,
                    'default_product_id':self.product_id.id,
                    'default_is_adr':logistics.is_adr,
                    # 'default_adr_line':[(6, 0,logistics.adr_line.ids)],
                    'default_adr_line':adr_lines,
                    'default_packing_type':logistics.packing_type,
                    'default_container_count':logistics.container_count,
                    'default_gross_weight_on_bridge':logistics.gross_weight_on_bridge,
                    'default_transporter':logistics.partner_id.id,
                    'default_transporter_street':logistics.partner_id.street,
                    'default_transporter_zip':logistics.partner_id.zip,
                    'default_transporter_city':logistics.partner_id.city,
                    'default_transporter_phone':logistics.partner_id.phone,
                    'default_transporter_email':logistics.partner_id.email,
                    'default_transporter_contact':logistics.partner_id.id,
                    'default_reciption_date':logistics.pickup_latest_date,
                    'default_expected_delivery':logistics.expected_delivery,
                    'default_r_state_id':logistics.delivery_countries_id.id,
                    'default_subcontractor':logistics.partner_id.id,
                    'default_subcontractor_street':logistics.partner_id.street,
                    'default_subcontractor_zip':logistics.partner_id.zip,
                    'default_subcontractor_city':logistics.partner_id.city,
                    'default_subcontractor_phone':logistics.partner_id.phone,
                    'default_subcontractor_email':logistics.partner_id.email,
                    'default_subcontractor_contact':logistics.partner_id.id,
                    'default_buy_weight_confirmed':logistics.buy_weight_confirmed,
                    'default_buyer_reception_date':logistics.buyer_reception_date,
                    'default_buyer_accept_lot':logistics.buyer_accept_lot,
                    'default_buyer_reject_reason':logistics.buyer_reject_reason,
                    'default_buyer_treatment_date':logistics.buyer_treatment_date,
                    'default_buyer_treatment_code':logistics.buyer_treatment_code
                 })
        return {
            'name': "Update BSD",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.bsd.wizard',
            'target': 'new',
            'context': vals,
        }

    def update_annexe_7(self):
        logistics=False
        if self.picking_type_id.sequence_code=='IN':
            logistics = self.env['logistics.management'].search([('origin','=',self.picking_id.project_entry_id.id),('status','=','approved')],limit=1)
        if self.picking_type_id.sequence_code=='OUT':
            logistics = self.env['logistics.management'].search([('sales_origin.name','=',self.picking_id.origin),('status','=','approved')],limit=1)
        vals = ({
                    'default_number_bsd':logistics.number_bsd,
                    'default_company_id':logistics.company_id.id,
                    'default_pickup_street':logistics.company_id.street,
                    'default_pickup_city':logistics.company_id.city,
                    'default_pickup_zip':logistics.company_id.zip,
                    'default_pickup_state_id':logistics.company_id.state_id.id,
                    'default_pickup_countries_id':logistics.company_id.country_id.id,
                    'default_phone':logistics.company_id.phone,
                    'default_email':logistics.company_id.email,
                    'default_delivery_partner_id':logistics.delivery_partner_id.id,
                    'default_delivery_street':logistics.delivery_street,
                    'default_delivery_zip':logistics.delivery_zip,
                    'default_delivery_city':logistics.delivery_city,
                    'default_delivery_state_id':logistics.delivery_state_id.id,
                    'default_delivery_countries_id':logistics.delivery_countries_id.id,
                    'default_delivery_phone':logistics.delivery_partner_id.phone,
                    'default_delivery_email':logistics.delivery_partner_id.email,
                    'default_gross_weight_on_bridge':logistics.gross_weight_on_bridge,
                    'default_expected_delivery':logistics.expected_delivery,
                    'default_transporter1':logistics.partner_id.id,
                    'default_transporter1_street':logistics.partner_id.street,
                    'default_transporter1_zip':logistics.partner_id.zip,
                    'default_transporter1_city':logistics.partner_id.city,
                    'default_transporter1_phone':logistics.partner_id.phone,
                    'default_transporter1_email':logistics.partner_id.email,
                    'default_transporter1_contact':logistics.partner_id.id,
                    'default_scheduled_date':logistics.expected_delivery,
                    'default_is_transporter2':logistics.is_transporter2,
                    'default_transporter2':logistics.transporter2.id,
                    'default_transporter2_street':logistics.transporter2_street,
                    'default_transporter2_zip':logistics.transporter2_zip,
                    'default_transporter2_city':logistics.transporter2_city,
                    'default_transporter2_phone':logistics.transporter2_phone,
                    'default_transporter2_email':logistics.transporter2_email,
                    'default_transporter2_contact':logistics.transporter2_contact,
                    'default_second_carrier':logistics.second_carrier,
                    'default_is_transporter3':logistics.is_transporter3,
                    'default_transporter3':logistics.transporter3.id,
                    'default_transporter3_street':logistics.transporter3_street,
                    'default_transporter3_zip':logistics.transporter3_zip,
                    'default_transporter3_city':logistics.transporter3_city,
                    'default_transporter3_phone':logistics.transporter3_phone,
                    'default_transporter3_email':logistics.transporter3_email,
                    'default_transporter3_contact':logistics.transporter3_contact,
                    'default_third_carrier':logistics.third_carrier,
                    'default_client':logistics.sales_origin.partner_id.id,
                    'default_client_street':logistics.sales_origin.partner_id.street,
                    'default_client_zip':logistics.sales_origin.partner_id.zip,
                    'default_client_city':logistics.sales_origin.partner_id.city,
                    'default_client_phone':logistics.sales_origin.partner_id.phone,
                    'default_client_email':logistics.sales_origin.partner_id.email,
                    'default_cleint_contact':logistics.sales_origin.partner_id.id,
                    'default_contractor':logistics.partner_id.id,
                    'default_contractor_street':logistics.partner_id.street,
                    'default_contractor_zip':logistics.partner_id.zip,
                    'default_contractor_city':logistics.partner_id.city,
                    'default_contractor_phone':logistics.partner_id.phone,
                    'default_contractor_email':logistics.partner_id.email,
                    'default_contractor_contact':logistics.partner_id.id,
                    'default_buyer_treatment_code':logistics.buyer_treatment_code,
                    'default_material_type':logistics.material,
                    'default_waste_code':logistics.waste_code,
                    'default_despatch_country':logistics.despatch_country.id,
                    'default_transit_country_1':logistics.transit_country_1.id,
                    'default_transit_country_2':logistics.transit_country_2.id,
                    'default_transit_country_3':logistics.transit_country_3.id,
                    'default_destination_country': logistics.destination_country.id,
                    'default_declaration_date':logistics.declaration_date,
                    'default_reception_date':logistics.reception_date,
                    'default_confirmed_quantity':logistics.confirmed_quantity,
                    'default_logistics_id':logistics.id,
                 })
        return {
            'name': "Update Annexe",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'update.annexe.wizard',
            'target': 'new',
            'context': vals,
        }

