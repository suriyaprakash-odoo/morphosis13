from odoo import fields, models, api, _
from datetime import datetime
import xlwt
import base64
from odoo.exceptions import UserError

class ProjectEntries(models.Model):
    _inherit = 'project.entries'

    metal_profit = fields.Monetary("Metal Profit", currency_field='currency_id', compute='_calculate_metal_profit')

    def _calculate_metal_profit(self):
        for project in self:
            profit_total = 0.0
            if project.project_type == 'refine':
                so_total = 0.0
                po_total = 0.0
                total_offer_price = 0.0
                lbma_actual_total = 0.0

                if project.sale_order_ids:
                    for so in project.sale_order_ids:
                        so_total += so.untaxed_amount
                if project.purchase_ids:
                    for po in project.purchase_ids:
                        po_total += po.untaxed_amount
                if project.silver:
                    sl_total_lme = 0.0
                    sl_offer_total = 0.0
                    for sl in project.silver_cost_ids:
                        sl_total_lme += sl.price_per_gram * sl.actual_result
                        sl_offer_total += sl.offer_buying_price
                    total_offer_price += sl_offer_total
                    lbma_actual_total += sl_total_lme

                if project.gold:
                    gl_total_lme = 0.0
                    gl_offer_total = 0.0
                    for gl in project.gold_cost_ids:
                        gl_total_lme += gl.price_per_gram * gl.actual_result
                        gl_offer_total += gl.offer_buying_price
                    total_offer_price += gl_offer_total
                    lbma_actual_total += gl_total_lme

                if project.palladium:
                    pd_total_lme = 0.0
                    pd_offer_total = 0.0
                    for pd in project.palladium_cost_ids:
                        pd_total_lme += pd.price_per_gram * pd.actual_result
                        pd_offer_total += pd.offer_buying_price
                    total_offer_price += pd_offer_total
                    lbma_actual_total += pd_total_lme

                if project.platinum:
                    pt_total_lme = 0.0
                    pt_offer_total = 0.0
                    for pt in project.platinum_cost_ids:
                        pt_total_lme += pt.price_per_gram * pt.actual_result
                        pt_offer_total += pt.offer_buying_price
                    total_offer_price += pt_offer_total
                    lbma_actual_total += pt_total_lme

                if project.copper:
                    cu_total_lme = 0.0
                    cu_offer_total = 0.0
                    for cu in project.copper_cost_ids:
                        cu_total_lme += cu.price_per_gram  * cu.actual_result
                        cu_offer_total += cu.offer_buying_price
                    total_offer_price += cu_offer_total
                    lbma_actual_total += cu_total_lme

                if project.rhodium:
                    rh_total_lme = 0.0
                    rh_offer_total = 0.0
                    for rh in project.rhodium_cost_ids:
                        rh_total_lme += rh.price_per_gram * rh.actual_result
                        rh_offer_total += rh.offer_buying_price
                    total_offer_price += rh_offer_total
                    lbma_actual_total += rh_total_lme

                if project.ruthenium:
                    ru_total_lme = 0.0
                    ru_offer_total = 0.0
                    for ru in project.ruthenium_cost_ids:
                        ru_total_lme += ru.price_per_gram * ru.actual_result
                        ru_offer_total += ru.offer_buying_price
                    total_offer_price += ru_offer_total
                    lbma_actual_total += ru_total_lme

                if project.iridium:
                    ir_total_lme = 0.0
                    ir_offer_total = 0.0
                    for ir in project.iridium_cost_ids:
                        ir_total_lme += ir.price_per_gram * ir.actual_result
                        ir_offer_total += ir.offer_buying_price
                    total_offer_price += ir_offer_total
                    lbma_actual_total += ir_total_lme

                # profit_total = (lbma_actual_total - total_offer_price) + (so_total - po_total)
                profit_total = lbma_actual_total - total_offer_price
            project.update({
                'metal_profit':profit_total
            })

    def print_refining_report(self):
        if self.silver or self.gold or self.palladium or self.platinum or self.copper or self.rhodium or self.ruthenium or self.iridium:
            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet('Refining Report - ' + self.name, cell_overwrite_ok=True)
            sheet.show_grid = False
            sheet.col(0).width = 256 * 5
            sheet.col(1).width = 256 * 25
            sheet.col(2).width = 256 * 25
            sheet.col(3).width = 256 * 30
            sheet.col(4).width = 256 * 15
            sheet.col(5).width = 256 * 20
            sheet.col(6).width = 256 * 25
            sheet.col(7).width = 256 * 15
            sheet.col(8).width = 256 * 15
            sheet.col(9).width = 256 * 20
            sheet.col(10).width = 256 * 20
            sheet.col(11).width = 256 * 15
            sheet.col(12).width = 256 * 20
            sheet.col(13).width = 256 * 15

            style_top_border = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thick,bottom thin;')
            style_top_right = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thick,top thick,bottom thin;')
            style_top_right_1 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thick,top thin,bottom thin;',num_format_str="#,##0.0000 €")
            style_top_right_date= xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thick,top thin,bottom thin;', num_format_str='DD/MM/YYYY')
            style_top_bottom_right = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thick,top thin,bottom thick;',num_format_str="#,##0.0000 €")
            style_top_bottom_full = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thick;')
            style01 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;')
            style02 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;')
            style02_pr = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;',num_format_str = '0.00%')
            style04 = xlwt.easyxf('font: name Times New Roman,color-index black,bold True ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;')
            style05 = xlwt.easyxf('font: name Times New Roman,color-index black; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;',num_format_str="#,##0.0000 €")
            style06 = xlwt.easyxf('font: name Times New Roman,color-index black, bold True; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;', num_format_str="#,##0.00 €")

            so_total = 0.0
            orders = []
            if self .sale_order_ids:
                sales = 1
                orders = []
                for so in self.sale_order_ids:
                    if sales != len(self.sale_order_ids):
                        orders.append(so.sale_id.name + ', ')
                    else:
                        orders.append(so.sale_id.name)
                    sales += 1
                    so_total += so.untaxed_amount

            po_total = 0.0
            po_order = []
            if self.purchase_ids:
                purchases = 1
                po_order = []
                for po in self.purchase_ids:
                    if purchases != len(self.purchase_ids):
                        po_order.append(po.purchase_id.name + ', ')
                    else:
                        po_order.append(po.purchase_id.name)
                    purchases += 1
                    po_total += po.untaxed_amount

            sheet.write_merge(3, 3, 0, 1, "Référence de l'affaire", style_top_border)
            sheet.write(3, 2, self.name, style_top_right)
            sheet.write_merge(4, 4,0,1, 'Bon de Commande', style01)
            sheet.write(4, 2, self.origin.name, style_top_right_1)
            sheet.write_merge(5,5,0,1, 'Client', style01)
            sheet.write(5, 2, self.partner_id.name, style_top_right_1)
            sheet.write_merge(6,6,0,1, 'Date', style01)
            sheet.write(6, 2, datetime.today(), style_top_right_date)
            sheet.write_merge(7,7,0,1, 'Commande des prestations', style01)
            sheet.write(7, 2, orders, style_top_right_1)
            sheet.write_merge(8,8,0,1, 'Facture de prestation', style01)
            sheet.write(8, 2, so_total, style_top_right_1)
            sheet.write_merge(9,9,0,1, 'Frais de prestation ', style_top_bottom_full)
            sheet.write(9, 2, po_total, style_top_bottom_right)

            n = 11
            n += 0
            sheet.write(n, 0, '')
            sheet.write(n, 1, 'Référence du contenant')
            sheet.write(n, 2, 'Poids à la réception (kg)')
            sheet.write(n, 3, 'Déchets industriels pour traitement')
            sheet.write(n, 4, 'Variante')
            sheet.write(n, 5, 'Nature du déchet')
            sheet.write(n, 6, 'Analyse Préalable (CAP) g ')
            sheet.write(n, 7, 'Echantillon de référence g')
            sheet.write(n, 8, 'Résultat g')
            sheet.write(n, 9, 'Pourcentage de Réstitution')
            sheet.write(n, 10, 'Minimum Levy (g)')
            sheet.write(n, 11, 'Compte Poids Client (g)')
            sheet.write(n, 12, 'Pourcentage Remise LME')
            sheet.write(n, 13, 'Prix LME à la date €/g')
            sheet.write(n, 14, 'Prix offert')

            n += 1

            lme_total_price =0.0
            total_offer_price = 0.0
            lbma_actual_total = 0.0

            if self.silver:
                sheet.write(n, 0, 'Ag', style02)
                n += 1
                total_cnt_weight= 0.0
                analysis_weight = 0.0
                reference_weight = 0.0
                actual_result_weight = 0.0
                # sl_client_pr = 0.0
                sl_total_lme = 0.0
                sl_offer_total = 0.0
                sl_client_pr_total = 0.0
                for sl in self.silver_cost_ids:
                    container = []
                    weight = 0.0
                    sl_count = 1
                    main_product_sl =''
                    sub_product_sl = ''
                    sl_client_pr = 0.0
                    for cnt in sl.sample_ct_id:
                        if sl_count != len(sl.sample_ct_id):
                            container.append(cnt.name + ', ')
                        else:
                            container.append(cnt.name)
                            main_product_sl = cnt.main_product_id.name
                            sub_product_sl = cnt.sub_product_id.product_template_attribute_value_ids.name
                        sl_count += 1
                        weight += cnt.net_gross_weight

                    if sl.minimum_levy and sl.minimum_levy > (sl.actual_result * (sl.dedection_percentage / 100)):
                        sl_deduction = sl.minimum_levy
                        sl_deduction_pr = ''
                        sl_minimum_levy = sl.minimum_levy
                    else:
                        sl_deduction = sl.actual_result * (sl.dedection_percentage / 100)
                        sl_deduction_pr = (100 - sl.dedection_percentage) / 100
                        sl_minimum_levy = ''

                    sl_client_pr += sl.actual_result - sl_deduction

                    # sheet.write(n +  1 , 0, '', style02)
                    sheet.write(n - 1, 1, container, style02)
                    sheet.write(n - 1, 2, weight, style02)
                    sheet.write(n - 1, 3, main_product_sl, style02)
                    sheet.write(n - 1, 4, sub_product_sl, style02)
                    sheet.write(n - 1, 5, sl.waste_nature, style02)
                    sheet.write(n - 1, 6, sl.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, sl.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, sl.actual_result, style02)
                    sheet.write(n - 1, 9, sl_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, sl_minimum_levy, style02)
                    sheet.write(n - 1, 11, sl_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - sl.buy_price_discount)/100, style02_pr)
                    sheet.write(n - 1, 13, sl.price_per_gram, style05)
                    sheet.write(n - 1, 14, sl.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight += weight
                    analysis_weight += sl.analysis_for_certification
                    reference_weight += sl.reference_sample_analysis
                    actual_result_weight += sl.actual_result
                    # sl_client_pr += ((100 - sl.dedection_percentage)*sl.actual_result)/100
                    sl_total_lme += sl.price_per_gram * sl.actual_result
                    sl_offer_total += sl.offer_buying_price
                    sl_client_pr_total += sl_client_pr

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight, style04)
                sheet.write(n - 1, 7, reference_weight, style04)
                sheet.write(n - 1, 8, actual_result_weight, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, sl_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, sl_offer_total, style06)
                n += 1
                lme_total_price += sl_total_lme
                total_offer_price += sl_offer_total
                lbma_actual_total += sl_total_lme

            if self.gold:
                sheet.write(n, 0, 'Au', style02)
                n += 1
                total_cnt_weight_gl = 0.0
                analysis_weight_gl = 0.0
                reference_weight_gl = 0.0
                actual_result_weight_gl = 0.0
                gl_client_pr_total = 0.0
                gl_total_lme = 0.0
                gl_offer_total = 0.0
                main_product_gl = False
                sub_product_gl = False
                for gl in self.gold_cost_ids:
                    containers=[]
                    weight_gl =0.0
                    gl_client_pr = 0.0
                    count = 1

                    for gl_cnt in gl.sample_ct_id:
                        if count != len(gl.sample_ct_id):
                            containers.append(gl_cnt.name + ', ')
                        else:
                            containers.append(gl_cnt.name)
                            main_product_gl = gl_cnt.main_product_id.name
                            sub_product_gl = gl_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count +=1

                        weight_gl += gl_cnt.net_gross_weight

                    if gl.minimum_levy and gl.minimum_levy > (gl.actual_result * (gl.dedection_percentage / 100)):
                        gl_deduction = gl.minimum_levy
                        gl_deduction_pr = ''
                        gl_minimum_levy = gl.minimum_levy
                    else:
                        gl_deduction = gl.actual_result * (gl.dedection_percentage / 100)
                        gl_deduction_pr = (100 - gl.dedection_percentage) / 100
                        gl_minimum_levy = ''

                    gl_client_pr += gl.actual_result - gl_deduction


                    # sheet.write(n + 1, 0, '', style02)
                    sheet.write(n - 1, 1, containers, style02)
                    sheet.write(n - 1, 2, weight_gl, style02)
                    sheet.write(n - 1, 3, main_product_gl, style02)
                    sheet.write(n - 1, 4, sub_product_gl, style02)
                    sheet.write(n - 1, 5, gl.waste_nature, style02)
                    sheet.write(n - 1, 6, gl.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, gl.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, gl.actual_result, style02)
                    sheet.write(n - 1, 9, gl_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, gl_minimum_levy, style02)
                    sheet.write(n - 1, 11, gl_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - gl.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, gl.price_per_gram, style05)
                    sheet.write(n - 1, 14, gl.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_gl += weight_gl
                    analysis_weight_gl += gl.analysis_for_certification
                    reference_weight_gl += gl.reference_sample_analysis
                    actual_result_weight_gl += gl.actual_result
                    gl_client_pr_total += gl_client_pr
                    gl_total_lme += gl.price_per_gram * gl.actual_result
                    gl_offer_total += gl.offer_buying_price

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_gl, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_gl, style04)
                sheet.write(n - 1, 7, reference_weight_gl, style04)
                sheet.write(n - 1, 8, actual_result_weight_gl, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, gl_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, gl_offer_total, style06)
                n += 1
                lme_total_price += gl_total_lme
                total_offer_price += gl_offer_total
                lbma_actual_total += gl_total_lme

            if self.palladium:
                sheet.write(n, 0, 'Pd', style02)
                n += 1
                total_cnt_weight_pd = 0.0
                analysis_weight_pd = 0.0
                reference_weight_pd = 0.0
                actual_result_weight_pd = 0.0
                pd_client_pr_total = 0.0
                pd_total_lme = 0.0
                pd_offer_total = 0.0
                main_product_pd = False
                sub_product_pd = False
                for pd in self.palladium_cost_ids:
                    containers_pd = []
                    weight_pd = 0.0
                    pd_client_pr = 0.0

                    count_pd = 1
                    for pd_cnt in pd.sample_ct_id:
                        if count_pd != len(pd.sample_ct_id):
                            containers_pd.append(pd_cnt.name + ', ')
                        else:
                            containers_pd.append(pd_cnt.name)
                            main_product_pd = pd_cnt.main_product_id.name
                            sub_product_pd = pd_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count_pd += 1

                        weight_pd += pd_cnt.net_gross_weight

                    if pd.minimum_levy and pd.minimum_levy > (pd.actual_result * (pd.dedection_percentage / 100)):
                        pd_deduction = pd.minimum_levy
                        pd_deduction_pr = ''
                        pd_minimum_levy = pd.minimum_levy
                    else:
                        pd_deduction = pd.actual_result * (pd.dedection_percentage / 100)
                        pd_deduction_pr = (100 - pd.dedection_percentage) / 100
                        pd_minimum_levy = ''

                    pd_client_pr += pd.actual_result - pd_deduction

                    # sheet.write(n + 1, 0, '', style02)
                    sheet.write(n - 1, 1, containers_pd, style02)
                    sheet.write(n - 1, 2, weight_pd, style02)
                    sheet.write(n - 1, 3, main_product_pd, style02)
                    sheet.write(n - 1, 4, sub_product_pd, style02)
                    sheet.write(n - 1, 5, pd.waste_nature, style02)
                    sheet.write(n - 1, 6, pd.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, pd.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, pd.actual_result, style02)
                    sheet.write(n - 1, 9, pd_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, pd_minimum_levy, style02)
                    sheet.write(n - 1, 11, pd_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - pd.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, pd.price_per_gram, style05)
                    sheet.write(n - 1, 14, pd.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_pd += weight_pd
                    analysis_weight_pd += pd.analysis_for_certification
                    reference_weight_pd += pd.reference_sample_analysis
                    actual_result_weight_pd += pd.actual_result
                    pd_client_pr_total += pd_client_pr
                    pd_total_lme += pd.price_per_gram * pd.actual_result
                    pd_offer_total += pd.offer_buying_price


                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_pd, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_pd, style04)
                sheet.write(n - 1, 7, reference_weight_pd, style04)
                sheet.write(n - 1, 8, actual_result_weight_pd, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, pd_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, pd_offer_total, style06)
                n += 1
                lme_total_price += pd_total_lme
                total_offer_price += pd_offer_total
                lbma_actual_total += pd_total_lme

            if self.platinum:
                sheet.write(n, 0, 'Pt', style02)
                n += 1
                total_cnt_weight_pt = 0.0
                analysis_weight_pt = 0.0
                reference_weight_pt = 0.0
                actual_result_weight_pt = 0.0
                pt_client_pr_total = 0.0
                pt_total_lme = 0.0
                pt_offer_total = 0.0
                main_product_pt = ''
                sub_product_pt = ''
                for pt in self.platinum_cost_ids:
                    containers_pt = []
                    weight_pt = 0.0
                    pt_client_pr = 0.0

                    count_pt = 1
                    for pt_cnt in pt.sample_ct_id:
                        if count_pt != len(pt.sample_ct_id):
                            containers_pt.append(pt_cnt.name + ', ')
                        else:
                            containers_pt.append(pt_cnt.name)
                            main_product_pt = pt_cnt.main_product_id.name
                            sub_product_pt = pt_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count_pt += 1

                        weight_pt += pt_cnt.net_gross_weight

                    if pt.minimum_levy and pt.minimum_levy > (pt.actual_result * (pt.dedection_percentage / 100)):
                        pt_deduction = pt.minimum_levy
                        pt_deduction_pr = ''
                        pt_minimum_levy = pt.minimum_levy
                    else:
                        pt_deduction = pt.actual_result * (pt.dedection_percentage / 100)
                        pt_deduction_pr = (100 - pt.dedection_percentage) / 100
                        pt_minimum_levy = ''

                    pt_client_pr += pt.actual_result - pt_deduction

                    sheet.write(n - 1, 1, containers_pt, style02)
                    sheet.write(n - 1, 2, weight_pt, style02)
                    sheet.write(n - 1, 3, main_product_pt, style02)
                    sheet.write(n - 1, 4, sub_product_pt, style02)
                    sheet.write(n - 1, 5, pt.waste_nature, style02)
                    sheet.write(n - 1, 6, pt.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, pt.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, pt.actual_result, style02)
                    sheet.write(n - 1, 9, pt_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, pt_minimum_levy, style02)
                    sheet.write(n - 1, 11, pt_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - pt.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, pt.price_per_gram, style05)
                    sheet.write(n - 1, 14, pt.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_pt += weight_pt
                    analysis_weight_pt += pt.analysis_for_certification
                    reference_weight_pt += pt.reference_sample_analysis
                    actual_result_weight_pt += pt.actual_result
                    pt_client_pr_total += pt_client_pr
                    pt_total_lme += pt.price_per_gram * pt.actual_result
                    pt_offer_total += pt.offer_buying_price

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_pt, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_pt, style04)
                sheet.write(n - 1, 7, reference_weight_pt, style04)
                sheet.write(n - 1, 8, actual_result_weight_pt, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, pt_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, pt_offer_total, style06)
                n += 1
                lme_total_price += pt_total_lme
                total_offer_price += pt_offer_total
                lbma_actual_total += pt_total_lme

            if self.copper:
                sheet.write(n, 0, 'Cu', style02)
                n += 1
                total_cnt_weight_cu = 0.0
                analysis_weight_cu = 0.0
                reference_weight_cu = 0.0
                actual_result_weight_cu = 0.0
                cu_client_pr_total = 0.0
                cu_total_lme= 0.0
                cu_offer_total = 0.0
                main_product_cu = ''
                sub_product_cu = ''
                for cu in self.copper_cost_ids:
                    containers_cu = []
                    weight_cu = 0.0
                    cu_client_pr = 0.0

                    count_cu = 1
                    for cu_cnt in cu.sample_ct_id:
                        if count_cu != len(cu.sample_ct_id):
                            containers_cu.append(cu_cnt.name + ', ')
                        else:
                            containers_cu.append(cu_cnt.name)
                            main_product_cu = cu_cnt.main_product_id.name
                            sub_product_cu = cu_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count_cu += 1

                        weight_cu += cu_cnt.net_gross_weight

                    if cu.minimum_levy and cu.minimum_levy > (cu.actual_result * (cu.dedection_percentage / 100)):
                        cu_deduction = cu.minimum_levy
                        cu_deduction_pr = ''
                        cu_minimum_levy = cu.minimum_levy
                    else:
                        cu_deduction = cu.actual_result * (cu.dedection_percentage / 100)
                        cu_deduction_pr = (100 - cu.dedection_percentage) / 100
                        cu_minimum_levy = ''

                    cu_client_pr += cu.actual_result - cu_deduction

                    sheet.write(n - 1, 1, containers_cu, style02)
                    sheet.write(n - 1, 2, weight_cu, style02)
                    sheet.write(n - 1, 3, main_product_cu, style02)
                    sheet.write(n - 1, 4, sub_product_cu, style02)
                    sheet.write(n - 1, 5, cu.waste_nature, style02)
                    sheet.write(n - 1, 6, cu.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, cu.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, cu.actual_result, style02)
                    sheet.write(n - 1, 9, cu_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, cu_minimum_levy, style02)
                    sheet.write(n - 1, 11, cu_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - cu.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, cu.price_per_gram, style05)
                    sheet.write(n - 1, 14, cu.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_cu += weight_cu
                    analysis_weight_cu += cu.analysis_for_certification
                    reference_weight_cu += cu.reference_sample_analysis
                    actual_result_weight_cu += cu.actual_result
                    cu_total_lme += cu.price_per_gram * cu.actual_result
                    cu_offer_total += cu.offer_buying_price
                    cu_client_pr_total += cu_client_pr

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_cu, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_cu, style04)
                sheet.write(n - 1, 7, reference_weight_cu, style04)
                sheet.write(n - 1, 8, actual_result_weight_cu, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, cu_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, cu_offer_total, style06)
                n += 1
                lme_total_price += cu_total_lme
                total_offer_price += cu_offer_total
                lbma_actual_total += cu_total_lme

            if self.rhodium:
                sheet.write(n, 0, 'Rh', style02)
                n += 1
                total_cnt_weight_rh = 0.0
                analysis_weight_rh = 0.0
                reference_weight_rh = 0.0
                actual_result_weight_rh = 0.0
                rh_client_pr_total = 0.0
                rh_total_lme = 0.0
                rh_offer_total = 0.0
                main_product_rh =''
                sub_product_rh = ''
                for rh in self.rhodium_cost_ids:
                    containers_rh = []
                    weight_rh = 0.0
                    rh_client_pr = 0.0

                    count_rh = 1
                    for rh_cnt in rh.sample_ct_id:
                        if count_rh != len(rh.sample_ct_id):
                            containers_rh.append(rh_cnt.name + ', ')
                        else:
                            containers_rh.append(rh_cnt.name)
                            main_product_rh = rh_cnt.main_product_id.name
                            sub_product_rh = rh_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count_rh += 1

                        weight_rh += rh_cnt.net_gross_weight

                    if rh.minimum_levy and rh.minimum_levy > (rh.actual_result * (rh.dedection_percentage / 100)):
                        rh_deduction = rh.minimum_levy
                        rh_deduction_pr = ''
                        rh_minimum_levy = rh.minimum_levy
                    else:
                        rh_deduction = rh.actual_result * (rh.dedection_percentage / 100)
                        rh_deduction_pr = (100 - rh.dedection_percentage) / 100
                        rh_minimum_levy = ''

                    rh_client_pr += rh.actual_result - rh_deduction

                    # sheet.write(n + 1, 0, '', style02)
                    sheet.write(n - 1, 1, containers_rh, style02)
                    sheet.write(n - 1, 2, weight_rh, style02)
                    sheet.write(n - 1, 3, main_product_rh, style02)
                    sheet.write(n - 1, 4, sub_product_rh, style02)
                    sheet.write(n - 1, 5, rh.waste_nature, style02)
                    sheet.write(n - 1, 6, rh.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, rh.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, rh.actual_result, style02)
                    sheet.write(n - 1, 9, rh_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, rh_minimum_levy, style02)
                    sheet.write(n - 1, 11, rh_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - rh.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, rh.price_per_gram, style05)
                    sheet.write(n - 1, 14, rh.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_rh += weight_rh
                    analysis_weight_rh += rh.analysis_for_certification
                    reference_weight_rh += rh.reference_sample_analysis
                    actual_result_weight_rh += rh.actual_result
                    rh_client_pr_total += rh_client_pr
                    rh_total_lme += rh.price_per_gram * rh.actual_result
                    rh_offer_total += rh.offer_buying_price

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_rh, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_rh, style04)
                sheet.write(n - 1, 7, reference_weight_rh, style04)
                sheet.write(n - 1, 8, actual_result_weight_rh, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, rh_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, rh_offer_total, style06)
                n += 1

                lme_total_price += rh_total_lme
                total_offer_price += rh_offer_total
                lbma_actual_total += rh_total_lme

            if self.ruthenium:
                sheet.write(n, 0, 'Ru', style02)
                n += 1
                total_cnt_weight_ru = 0.0
                analysis_weight_ru = 0.0
                reference_weight_ru = 0.0
                actual_result_weight_ru = 0.0
                ru_client_pr_total = 0.0
                ru_total_lme =0.0
                ru_offer_total =0.0
                main_product_ru = 0.0
                sub_product_ru = 0.0
                for ru in self.ruthenium_cost_ids:
                    containers_ru = []
                    weight_ru = 0.0
                    ru_client_pr = 0.0

                    count_ru = 1
                    for ru_cnt in ru.sample_ct_id:
                        if count_ru != len(ru.sample_ct_id):
                            containers_ru.append(ru_cnt.name + ', ')
                        else:
                            containers_ru.append(ru_cnt.name)
                            main_product_ru = ru_cnt.main_product_id.name
                            sub_product_ru = ru_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count_ru += 1

                        weight_ru += ru_cnt.net_gross_weight

                    if ru.minimum_levy and ru.minimum_levy > (ru.actual_result * (ru.dedection_percentage / 100)):
                        ru_deduction = ru.minimum_levy
                        ru_deduction_pr = ''
                        ru_minimum_levy = ru.minimum_levy
                    else:
                        ru_deduction = ru.actual_result * (ru.dedection_percentage / 100)
                        ru_deduction_pr = (100 - ru.dedection_percentage) / 100
                        ru_minimum_levy = ''

                    ru_client_pr += ru.actual_result - ru_deduction

                    # sheet.write(n + 1, 0, '', style02)
                    sheet.write(n - 1, 1, containers_ru, style02)
                    sheet.write(n - 1, 2, weight_ru, style02)
                    sheet.write(n - 1, 3, main_product_ru, style02)
                    sheet.write(n - 1, 4, sub_product_ru, style02)
                    sheet.write(n - 1, 5, ru.waste_nature, style02)
                    sheet.write(n - 1, 6, ru.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, ru.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, ru.actual_result, style02)
                    sheet.write(n - 1, 9, ru_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, ru_minimum_levy, style02)
                    sheet.write(n - 1, 11, ru_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - ru.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, ru.price_per_gram, style05)
                    sheet.write(n - 1, 14, ru.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_ru += weight_ru
                    analysis_weight_ru += ru.analysis_for_certification
                    reference_weight_ru += ru.reference_sample_analysis
                    actual_result_weight_ru += ru.actual_result
                    ru_client_pr_total += ru_client_pr
                    ru_total_lme += ru.price_per_gram * ru.actual_result
                    ru_offer_total += ru.offer_buying_price

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_ru, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_ru, style04)
                sheet.write(n - 1, 7, reference_weight_ru, style04)
                sheet.write(n - 1, 8, actual_result_weight_ru, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, ru_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, ru_offer_total, style06)
                n += 1
                lme_total_price += ru_total_lme
                total_offer_price += ru_offer_total
                lbma_actual_total += ru_total_lme

            if self.iridium:
                sheet.write(n, 0, 'Ir', style02)
                n += 1
                total_cnt_weight_ir = 0.0
                analysis_weight_ir = 0.0
                reference_weight_ir = 0.0
                actual_result_weight_ir = 0.0
                ir_client_pr_total = 0.0
                ir_total_lme = 0.0
                ir_offer_total = 0.0
                main_product_ir = ''
                sub_product_ir = ''
                for ir in self.irthenium_cost_ids:
                    containers_ir = []
                    weight_ir = 0.0
                    ir_client_pr = 0.0

                    count_ir = 1
                    for ir_cnt in ir.sample_ct_id:
                        if count_ir != len(ir.sample_ct_id):
                            containers_ir.append(ir_cnt.name + ', ')
                        else:
                            containers_ir.append(ir_cnt.name)
                            main_product_ir = ir_cnt.main_product_id.name
                            sub_product_ir = ir_cnt.sub_product_id.product_template_attribute_value_ids.name
                        count_ir += 1

                        weight_ir += ir_cnt.net_gross_weight

                    if ir.minimum_levy and ir.minimum_levy > (ir.actual_result * (ir.dedection_percentage / 100)):
                        ir_deduction = ir.minimum_levy
                        ir_deduction_pr = ''
                        ir_minimum_levy = ir.minimum_levy
                    else:
                        ir_deduction = ir.actual_result * (ir.dedection_percentage / 100)
                        ir_deduction_pr = (100 - ir.dedection_percentage) / 100
                        ir_minimum_levy = ''

                    ir_client_pr += ir.actual_result - ir_deduction

                    sheet.write(n - 1, 1, containers_ir, style02)
                    sheet.write(n - 1, 2, weight_ir, style02)
                    sheet.write(n - 1, 3, main_product_ir, style02)
                    sheet.write(n - 1, 4, sub_product_ir, style02)
                    sheet.write(n - 1, 5, ir.waste_nature, style02)
                    sheet.write(n - 1, 6, ir.analysis_for_certification, style02)
                    sheet.write(n - 1, 7, ir.reference_sample_analysis, style02)
                    sheet.write(n - 1, 8, ir.actual_result, style02)
                    sheet.write(n - 1, 9, ir_deduction_pr, style02_pr)
                    sheet.write(n - 1, 10, ir_minimum_levy, style02)
                    sheet.write(n - 1, 11, ir_client_pr, style02)
                    sheet.write(n - 1, 12, (100 - ir.buy_price_discount) / 100, style02_pr)
                    sheet.write(n - 1, 13, ir.price_per_gram, style05)
                    sheet.write(n - 1, 14, ir.offer_buying_price, style05)
                    n += 1

                    total_cnt_weight_ir += weight_ir
                    analysis_weight_ir += ir.analysis_for_certification
                    reference_weight_ir += ir.reference_sample_analysis
                    actual_result_weight_ir += ir.actual_result
                    ir_client_pr_total += ir_client_pr
                    ir_total_lme += ir.price_per_gram * ir.actual_result
                    ir_offer_total += ir.offer_buying_price

                sheet.write(n - 1, 1, 'Total', style04)
                sheet.write(n - 1, 2, total_cnt_weight_ir, style04)
                sheet.write(n - 1, 3, '', style02)
                sheet.write(n - 1, 4, '', style02)
                sheet.write(n - 1, 5, '', style02)
                sheet.write(n - 1, 6, analysis_weight_ir, style04)
                sheet.write(n - 1, 7, reference_weight_ir, style04)
                sheet.write(n - 1, 8, actual_result_weight_ir, style04)
                sheet.write(n - 1, 9, '', style02)
                sheet.write(n - 1, 10, '', style02)
                sheet.write(n - 1, 11, ir_client_pr_total, style04)
                sheet.write(n - 1, 12, '', style02)
                sheet.write(n - 1, 13, '', style02)
                sheet.write(n - 1, 14, ir_offer_total, style06)
                n += 1
                lme_total_price += ir_total_lme
                total_offer_price += ir_offer_total
                lbma_actual_total += ir_total_lme


            profit_total = (lbma_actual_total - total_offer_price) + (so_total - po_total)
            sheet.write(n+2, 13, 'valeur des métaux', style02)
            sheet.write(n+2, 14, lbma_actual_total, style05)
            sheet.write(n+3, 13, 'Offre Total', style02)
            sheet.write(n+3, 14, total_offer_price, style05)
            sheet.write(n+4, 13, 'Bénéfice', style02)
            sheet.write(n+4, 14, profit_total, style05)


            filename = ('/tmp/Fixed Purchase Report.xls')
            workbook.save(filename)
            fixed_purchase_report_view = open(filename, 'rb')
            file_data = fixed_purchase_report_view.read()
            out = base64.encodestring(file_data)
            attach_value = {'name': 'Refining Report - '+ self.name +'.xls', 'refining_report_xl': out}

            act_id = self.env['refining.report'].create(attach_value)
            fixed_purchase_report_view.close()
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'refining.report',
                'res_id': act_id.id,
                'target': 'new',
            }
        else:
            raise UserError(_('Please some metals to the line item'))


class RefiningReportWizard(models.TransientModel):
    _name = "refining.report"

    refining_report_xl = fields.Binary("Download Excel Report")
    name = fields.Char("Excel File")
