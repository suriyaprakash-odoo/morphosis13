from odoo import fields, models, api, _
from odoo.exceptions import UserError
import base64
import io
import itertools

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from datetime import datetime


class BSDAnnexeReport(models.TransientModel):
    _name = 'bsd.annexe.report'

    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    bsd_annexe_no = fields.Many2one('logistics.management',string="BSD/Annexe7 No")


    def view_bsd_annexe_report(self):
        logistics_obj = self.env['logistics.management'].search([('reception_date', '<=', self.to_date),('reception_date', '>=', self.from_date)])

        logistics_report = []
        delivery_addrs = ''
        partner_addrs = ''
        handler = ''
        for rec in logistics_obj:
            
            if rec.delivery_partner_id:
                delivery_addrs=str(rec.delivery_street if rec.delivery_street else ' ')+' '+str(rec.delivery_city if rec.delivery_city else ' ')+' '+str(rec.delivery_zip if rec.delivery_zip else ' ')+' '+str(rec.delivery_state_id.name if rec.delivery_state_id.name else ' ')+' '+str(rec.delivery_countries_id.name if rec.delivery_countries_id else ' ')
            
            if rec.partner_id:
                partner_addrs=str(rec.partner_id.street if rec.partner_id.street else ' ')+' '+str(rec.partner_id.city if rec.partner_id.city else ' ')+' '+str(rec.partner_id.zip if rec.partner_id.zip else ' ')+' '+str(rec.partner_id.state_id.name if rec.partner_id.state_id else ' ')+' '+str(rec.partner_id.country_id.name if rec.partner_id.country_id else ' ')

            if rec.logistics_for == 'sale':
                handler = str(rec.sales_origin.partner_id.street if rec.sales_origin.partner_id.street else ' ')+' '+str(rec.sales_origin.partner_id.city if rec.sales_origin.partner_id.city else ' ')+' '+str(rec.sales_origin.partner_id.zip if rec.sales_origin.partner_id.zip else ' ')+' '+str(rec.sales_origin.partner_id.state_id.name if rec.sales_origin.partner_id.state_id else ' ')+' '+str(rec.sales_origin.partner_id.country_id.name if rec.sales_origin.partner_id.country_id else ' ')
            else:
                handler = str(rec.origin.user_id.partner_id.street if rec.origin.user_id.partner_id.street else ' ')+' '+str(rec.origin.user_id.partner_id.city if rec.origin.user_id.partner_id.city else ' ')+' '+str(rec.origin.user_id.partner_id.zip if rec.origin.user_id.partner_id.zip else ' ')+' '+str(rec.origin.user_id.partner_id.state_id.name if rec.origin.user_id.partner_id.state_id else ' ')+' '+str(rec.origin.user_id.partner_id.country_id.name if rec.origin.user_id.partner_id.country_id else ' ')

            log_report = self.env['logistics.report'].create({
                    'waste_form' : rec.waste_form,
                    'waste_code' : rec.waste_code,
                    'expected_delivery' : rec.expected_delivery,
                    'number_bsd' : rec.number_bsd,
                    'pretreatment_code' : rec.pretreatment_code,
                    'destination_company' : rec.delivery_partner_id.name,
                    'destination_siret' : rec.delivery_partner_id.siret,
                    'delivery_address': delivery_addrs,
                    'transporter_name': rec.partner_id.name,
                    'transporter_address' : partner_addrs,
                    'recipit' : rec.delivery_partner_id.recipit,
                    'expiration_date' : rec.delivery_partner_id.recipit_expiration,
                    'reception_date' : rec.reception_date,
                    'buyer_treatment_date' : rec.buyer_treatment_date,
                    'handler' : handler,
                })
            logistics_report.append(log_report.id)

        return {
            'name': "BSD/Annexe7 Report",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,pivot',
            'res_model': 'logistics.report',
            'target': 'current',
            'domain': [('id', '=', [x for x in logistics_report])],
            'views_id':False,
            'views':[(self.env.ref('ppts_inventory_customization.bad_annexe_report_tree_view').id or False, 'tree')],
        }
        
    # def bsd_annexe_report(self):
    #     if self.bsd_annexe_no.bsdannex in  ('bsd','annux7'):
    #         output = io.BytesIO()
    #         workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #         worksheet = workbook.add_worksheet('BSD_Annexe7 Report')
    #         style_highlight = workbook.add_format({ 'text_wrap': True,'bold': True, 'border':1,'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
    #         style_headline = workbook.add_format({ 'text_wrap': True,'font_size': 20,'border':1, 'align': 'center', 'bold': True, 'bg_color': '#E0E0E0'})
    #         style_normal = workbook.add_format({'align':'left','border':1, 'text_wrap': True})
    #         headers = ["Type of Waste","European Waste Code","Collection Date","BSD/Annexe numbers", "Pretreatment", "Destination Company", "SIRET of destination company", "Address",
    #                    "Transporteur","Reception Date" ,"Treatment date", "Handler"]
    #         row = 6;col = 0
    #         worksheet.merge_range(0, 0, 2, 11, 'BSD/Annexe7 Report', style_headline)
    #         worksheet.write(3, 0, 'Transport Request No. ', style_highlight)
    #         worksheet.write(3, 1, str(self.bsd_annexe_no.name), style_normal)
    #         if self.bsd_annexe_no.sales_origin:
    #             worksheet.write(4, 0, 'Sale Order', style_highlight)
    #             worksheet.write(4, 1, str(self.bsd_annexe_no.sales_origin.name), style_normal)
    #         if self.bsd_annexe_no.origin:
    #             worksheet.write(4, 0, 'Project Entry', style_highlight)
    #             worksheet.write(4, 1, str(self.bsd_annexe_no.origin.name), style_normal)

    #         for header in headers:
    #             worksheet.write(row, col, header, style_highlight)
    #             worksheet.set_column(col, col, 20)
    #             col += 1
    #         pro_row = 7
    #         pro_col = 0;sale_partner=' '; partner_addrs=' ';delivery_addrs=' '
    #         if self.bsd_annexe_no.delivery_partner_id:
    #             delivery_addrs=str(self.bsd_annexe_no.delivery_street if self.bsd_annexe_no.delivery_street else ' ')+', '+str(self.bsd_annexe_no.delivery_city if self.bsd_annexe_no.delivery_city else ' ')+', '+str(self.bsd_annexe_no.delivery_zip if self.bsd_annexe_no.delivery_zip else ' ')+', '+str(self.bsd_annexe_no.delivery_state_id.name if self.bsd_annexe_no.delivery_state_id.name else ' ')+', '+str(self.bsd_annexe_no.delivery_countries_id.name if self.bsd_annexe_no.delivery_countries_id else ' ')
    #         if self.bsd_annexe_no.partner_id:
    #             partner_addrs=str(self.bsd_annexe_no.partner_id.street if self.bsd_annexe_no.partner_id.street else ' ')+' '+str(self.bsd_annexe_no.partner_id.city if self.bsd_annexe_no.partner_id.city else ' ')+', '+str(self.bsd_annexe_no.partner_id.zip if self.bsd_annexe_no.partner_id.zip else ' ')+', '+str(self.bsd_annexe_no.partner_id.state_id.name if self.bsd_annexe_no.partner_id.state_id else ' ')+', '+str(self.bsd_annexe_no.partner_id.country_id.name if self.bsd_annexe_no.partner_id.country_id else ' ')
    #         if self.bsd_annexe_no.sales_origin:
    #             sale_partner = str(self.bsd_annexe_no.sales_origin.partner_id.street if self.bsd_annexe_no.sales_origin.partner_id.street else ' ')+', '+str(self.bsd_annexe_no.sales_origin.partner_id.city if self.bsd_annexe_no.sales_origin.partner_id.city else ' ')+', '+str(self.bsd_annexe_no.sales_origin.partner_id.zip if self.bsd_annexe_no.sales_origin.partner_id.zip else ' ')+', '+str(self.bsd_annexe_no.sales_origin.partner_id.state_id.name if self.bsd_annexe_no.sales_origin.partner_id.state_id else ' ')+', '+str(self.bsd_annexe_no.sales_origin.partner_id.country_id.name if self.bsd_annexe_no.sales_origin.partner_id.country_id else ' ')
    #         worksheet.write(pro_row, pro_col, str(self.bsd_annexe_no.waste_form if self.bsd_annexe_no.waste_form else ' '), style_normal)
    #         worksheet.write(pro_row, pro_col + 1, str(self.bsd_annexe_no.waste_code if self.bsd_annexe_no.waste_code else ' '),style_normal)
    #         worksheet.write(pro_row, pro_col + 2, self.bsd_annexe_no.expected_delivery if self.bsd_annexe_no.expected_delivery else ' ',style_normal)
    #         worksheet.write(pro_row, pro_col + 3, self.bsd_annexe_no.number_bsd if self.bsd_annexe_no.number_bsd else ' ', style_normal)
    #         worksheet.write(pro_row, pro_col + 4, self.bsd_annexe_no.pretreatment_code if self.bsd_annexe_no.pretreatment_code else ' ',style_normal)
    #         worksheet.write(pro_row, pro_col + 5, self.bsd_annexe_no.delivery_partner_id.name if self.bsd_annexe_no.delivery_partner_id.name else ' ', style_normal)
    #         worksheet.write(pro_row, pro_col + 6, self.bsd_annexe_no.delivery_partner_id.siret if self.bsd_annexe_no.delivery_partner_id.siret else ' ',style_normal)
    #         worksheet.write(pro_row, pro_col + 7, delivery_addrs, style_normal)
    #         worksheet.write(pro_row, pro_col + 8, partner_addrs ,style_normal)
    #         worksheet.write(pro_row, pro_col + 9, str(self.bsd_annexe_no.reception_date if self.bsd_annexe_no.reception_date else ' '), style_normal)
    #         worksheet.write(pro_row, pro_col + 10, str(self.bsd_annexe_no.buyer_treatment_date if self.bsd_annexe_no.buyer_treatment_date else ' '), style_normal)
    #         worksheet.write(pro_row, pro_col + 10, sale_partner ,style_normal)
    #         pro_row += 1
    #         workbook.close()
    #         output.seek(0)
    #         data = output.read()
    #         output.close()
    #         data = base64.encodestring(data)
    #         doc_id = self.env['ir.attachment'].create({'datas': data, 'name': 'BSD/Annexe Report ['+self.bsd_annexe_no.name +']'+ '.xls'})
    #         return {
    #             'type': 'ir.actions.act_url',
    #             'url': '/web/content/?id=%s&download=true' % (doc_id.id),
    #             'target': 'current',
    #         }
    #     else:
    #         raise UserError ('Please Add BSD/Annexe in Logistics')



class LogisticsReport(models.TransientModel):
    _name = 'logistics.report'

    waste_form = fields.Selection([('solide','Solide'),('liquide','Liquide'),('gaseux','Gaseux')],string="Type of Waste")
    waste_code = fields.Char('European Waste Code')
    expected_delivery = fields.Date('Collection Date')
    number_bsd = fields.Char(string="BSD/Annexe7 numbers")
    pretreatment_code = fields.Selection([
        ('d9' , 'D9'),
        ('r4' , 'R4'),
        ('r5' , 'R5'),
        ('r8' , 'R8'),
    ],string="Pretreatment")
    destination_company = fields.Char('Destination Company')
    destination_siret = fields.Char('SIRET of destination company')
    delivery_address = fields.Text('Address')
    transporter_name = fields.Char('Transporteur')
    transporter_address = fields.Text('Transporter Address')
    recipit = fields.Char('Récipissé')
    expiration_date = fields.Date('Expiration')
    reception_date = fields.Date("Reception Date")
    buyer_treatment_date = fields.Date("Date de traitement")
    handler = fields.Text('Handler')