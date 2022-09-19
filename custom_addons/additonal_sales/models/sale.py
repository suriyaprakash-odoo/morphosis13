from odoo import fields, models, api, _
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_entree_id = fields.Many2one("project.entries", string="Project ID")
    project_entry_line_id = fields.Many2one('project.entries.line', string="Project Entry Line ID", domain="[('project_entry_id','=',project_entree_id)]")

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.project_entree_id:
            self.env["additional.sale.orders"].create({'sale_id': res.id, 'amount': res.amount_total, 'untaxed_amount': res.amount_total, 'project_id': res.project_entree_id.id})
        
        # if res.project_entree_id.add_additional_sale_po and res.project_entree_id.project_type=="refine":
        #     res.update_additional_sales_po()

        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if self.project_entree_id:
            project_so = self.env['additional.sale.orders'].search([('sale_id', '=', self.id)])
            for so in project_so:
                so.amount = self.amount_total
                so.untaxed_amount = self.amount_untaxed
        
        # if self.project_entree_id.add_additional_sale_po and self.project_entree_id.project_type=="refine":
        #     self.update_additional_sales_po()

        return res
    

    # def update_additional_sales_po(self):

    #     get_po_line = self.env['purchase.order.line'].sudo().search([('order_id','=',self.project_entree_id.origin.id)],limit=1)

        # get_po_line_additional_sale = self.env['purchase.order.line'].sudo().search([('order_id','=',self.project_entree_id.origin.id),('line_origin','=','additional sale')])

        # total_additional_sale = 0
        # result = []

        # if get_po_line_additional_sale:
        #     get_po_line_additional_sale.sudo().unlink()

        # if self.project_entree_id and self.project_entree_id.project_type=="refine":
        #     for sale in self.project_entree_id.sale_order_ids:
        #         total_additional_sale += sale.sale_id.amount_total

        #         for sale_line in sale.sale_id.order_line:
        #             data = (0,0,{
        #                 'product_id': sale_line.product_id.id if sale_line.product_id else False ,
        #                 'name': sale_line.product_id.name if sale_line.product_id else '',
        #                 'product_qty':sale_line.product_uom_qty,
        #                 'price_unit':sale_line.price_unit,
        #                 'order_id':self.project_entree_id.origin.id,
        #                 'date_planned':datetime.now(),
        #                 'qty_received_method':'manual',
        #                 'product_uom':sale_line.product_uom.id if sale_line.product_uom else False,
        #                 'product_uom_qty':sale_line.product_uom_qty,
        #                 'crm_product_line_id':get_po_line.crm_product_line_id.id if get_po_line else False,
        #                 'line_origin': 'additional sale',
        #                 'partner_id': sale_line.order_id.partner_id.id if sale_line.order_id.partner_id else False,
        #                 'sale_order_line_id':sale_line.id,
        #             })
        #             result.append(data)

        #     self.project_entree_id.origin.order_line = result
        
    
    #update additional sales in po
    # def update_additional_sales_po(self):
    #     total_additional_sale = 0
    #     if self.project_entree_id and self.project_entree_id.project_type=="refine":
    #         for sale in self.project_entree_id.sale_order_ids:
    #             total_additional_sale += sale.sale_id.amount_total
        
    #     search_po_line = self.env['purchase.order.line'].sudo().search([('product_id.additional_sale','=',True),('order_id','=',self.project_entree_id.origin.id)],limit=1)

    #     get_po_line = self.env['purchase.order.line'].sudo().search([('order_id','=',self.project_entree_id.origin.id)],limit=1)

    #     if search_po_line:
    #         search_po_line.price_unit = total_additional_sale
    #     else:
    #         additional_sale_product = self.env['product.product'].sudo().search([('additional_sale','=',True)],limit=1)

    #         data = [(0,0,{
    #                 'product_id': additional_sale_product.id if additional_sale_product else False ,
    #                 'name': additional_sale_product.name if additional_sale_product else '',
    #                 'product_qty':1,
    #                 'price_unit':total_additional_sale,
    #                 'order_id':self.project_entree_id.origin.id,
    #                 'date_planned':datetime.now(),
    #                 'qty_received_method':'manual',
    #                 'product_uom':1,
    #                 'product_uom_qty':1,
    #                 'crm_product_line_id':get_po_line.crm_product_line_id.id if get_po_line else False,
    #                 'line_origin': 'additional sale',
    #                 'partner_id': get_po_line.partner_id.id if get_po_line else False,
    #             })]

    #         self.project_entree_id.origin.order_line = data
                

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
                
        if res.order_id.project_entree_id.add_additional_sale_po and res.order_id.project_entree_id.project_type=="refine":
            res.update_additional_sales_po()

        return res
    

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        
        if self.order_id.project_entree_id.add_additional_sale_po and self.order_id.project_entree_id.project_type=="refine":
            self.update_additional_sales_po()

        return res
    

    def unlink(self):
        for line in self:
            get_po_line = self.env['purchase.order.line'].sudo().search([('sale_order_line_id','=',self.id)])
            get_po_line.unlink()

        return super(SaleOrderLine, self).unlink()
    


    def update_additional_sales_po(self):

        get_po_line = self.env['purchase.order.line'].sudo().search([('order_id','=',self.order_id.project_entree_id.origin.id)],limit=1)

        get_po_sale_line = self.env['purchase.order.line'].sudo().search([('sale_order_line_id','=',self.id)],limit=1)

        if not get_po_sale_line:
            self.order_id.project_entree_id.origin.order_line = [(0,0,{
                        'product_id': self.product_id.id if self.product_id else False ,
                        'name': self.product_id.name if self.product_id else '',
                        'product_qty':self.product_uom_qty,
                        'price_unit':self.price_unit,
                        'order_id':self.order_id.project_entree_id.origin.id,
                        'date_planned':datetime.now(),
                        'qty_received_method':'manual',
                        'product_uom':self.product_uom.id if self.product_uom else False,
                        'product_uom_qty':self.product_uom_qty,
                        'crm_product_line_id':get_po_line.crm_product_line_id.id if get_po_line else False,
                        'line_origin': 'additional sale',
                        'partner_id': self.order_id.partner_id.id if self.order_id.partner_id else False,
                        'sale_order_line_id':self.id,
                    })]
        else:
            get_po_sale_line.update({
                        'product_id': self.product_id.id if self.product_id else False ,
                        'name': self.product_id.name if self.product_id else '',
                        'product_qty':self.product_uom_qty,
                        'price_unit':self.price_unit,
                        'order_id':self.order_id.project_entree_id.origin.id,
                        'date_planned':datetime.now(),
                        'qty_received_method':'manual',
                        'product_uom':self.product_uom.id if self.product_uom else False,
                        'product_uom_qty':self.product_uom_qty,
                        'crm_product_line_id':get_po_line.crm_product_line_id.id if get_po_line else False,
                        'line_origin': 'additional sale',
                        'partner_id': self.order_id.partner_id.id if self.order_id.partner_id else False,
                        'sale_order_line_id':self.id,
                    })
