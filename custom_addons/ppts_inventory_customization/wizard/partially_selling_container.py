# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class SellPartially(models.TransientModel):
    _name = 'sell.partially'

    partner_id = fields.Many2one('res.partner', string='Customer')
    container_id = fields.Many2one('stock.container', string='Container Name')
    selling_weight = fields.Float('Weight to Sell(Kg)', digits=(12,4))
    fraction_weight = fields.Float('Selected Fractions Weight(Kg)', digits=(12,4), related='container_id.net_weight')
    wizard_line_ids = fields.One2many('fraction.sell.line', 'wizard_id', string='Fractions sell line ref')

    def get_fraction_list(self):
        if self.selling_weight > self.fraction_weight:
            raise UserError('Selling weight it greater than the total weight of the container')
        if self.selling_weight:
            total_weight = 0.0
            remaining_weight = 0.0
            new_fraction_vals = []
            self.wizard_line_ids.unlink()
            fraction_vals = {}
            for line in self.container_id.fraction_line_ids:
                if total_weight != self.selling_weight:
                    if total_weight:
                        remaining_weight = self.selling_weight - total_weight
                    if remaining_weight:
                        if remaining_weight <= line.weight:
                            fraction_vals = {
                                'fraction_id': line.fraction_id.id,
                                'weight_of_fraction': remaining_weight,
                                'wizard_id': self.id,
                                'line_id': line.id,
                            }
                            new_fraction_vals.append(fraction_vals)
                            # line.write({'weight': line.weight - remaining_weight})
                            break
                        else:
                            if remaining_weight >= line.weight:
                                fraction_vals = {
                                    'fraction_id': line.fraction_id.id,
                                    'weight_of_fraction': remaining_weight - line.weight,
                                    'wizard_id': self.id,
                                    'line_id': line.id,
                                }
                                new_fraction_vals.append(fraction_vals)
                                total_weight += line.weight
                                # line.write({'weight': 0.00})
                    else:
                        if self.selling_weight <= line.weight:
                            fraction_vals = {
                                'fraction_id': line.fraction_id.id,
                                'weight_of_fraction': self.selling_weight,
                                'wizard_id': self.id,
                                'line_id': line.id,
                            }
                            new_fraction_vals.append(fraction_vals)
                            # line.write({'weight': line.weight - self.selling_weight})
                            break
                        else:
                            fr_weight = 0.0
                            if line.weight:
                                if self.selling_weight > line.weight:
                                    fr_weight = line.weight
                                else:
                                    fr_weight = self.selling_weight
                                fraction_vals = {
                                    'fraction_id': line.fraction_id.id,
                                    'weight_of_fraction': fr_weight,
                                    'wizard_id': self.id,
                                    'line_id': line.id,
                                }
                                new_fraction_vals.append(fraction_vals)
                                total_weight += line.weight
                            # if line.weight >= self.selling_weight:
                            #     line.write({'weight': line.weight - self.selling_weight})
                            # else:
                            #     line.write({'weight': 0.00})

            self.env['fraction.sell.line'].create(new_fraction_vals)

        vals = ({'default_partner_id': self.partner_id.id, 'default_container_id': self.container_id.id, 'default_selling_weight': self.selling_weight,
                 'default_wizard_line_ids': self.wizard_line_ids.ids, })
        return {
            'name': "Partially Sell Container",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sell.partially',
            'target': 'new',
            'context': vals,
        }

    def sell_container(self):
        if self.container_id.content_type_id.uom_id.uom_type == 'bigger':
            final_weight = self.selling_weight / self.container_id.content_type_id.uom_id.factor_inv
        elif self.container_id.content_type_id.uom_id.uom_type == 'smaller':
            final_weight = self.selling_weight * self.container_id.content_type_id.uom_id.factor_inv
        else:
            final_weight = self.selling_weight

        order_line = [(0, 0, {
            'product_id': self.container_id.content_type_id.id,
            'container_id': [(6, 0, [self.container_id.id])],
            'product_uom_qty': final_weight,
            'product_uom': self.container_id.content_type_id.uom_id.id,
            'weight': self.selling_weight
        })]
        price_list = self.env['product.pricelist'].search([('name', '=', 'Public Pricelist')])
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            # 'pricelist_id': price_list.id,
            'sale_by': 'weight',
            'order_line': order_line,
            'company_id':self.container_id.related_company_id.id or False
        })

        for rec in self.wizard_line_ids:
            rec.line_id.is_to_sell = True
            rec.line_id.sale_order_id = sale_order.id
            rec.line_id.weight = rec.line_id.weight - rec.weight_of_fraction

        if self.container_id.sale_order_ids:
            self.container_id.sale_order_ids = [(4, sale_order.id, None)]
        else:
            self.container_id.sale_order_ids = [(6, 0, [sale_order.id])]
        return {'type': 'ir.actions.act_window_close'}


class FractionSellLine(models.TransientModel):
    _name = 'fraction.sell.line'

    fraction_id = fields.Many2one('project.fraction', string='Fraction')
    weight_of_fraction = fields.Float('Weight(Kg)', digits=(12,4))
    wizard_id = fields.Many2one('sell.partially', string='Sell partially ref')
    line_id = fields.Many2one('fraction.line', string="Fraction Line")
