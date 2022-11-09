from datetime import timedelta
from datetime import datetime
from odoo import models
import calendar


class SaleForecast(models.AbstractModel):
    _name = 'report.hakbani_sale_forecast_report.sale_forecast_template'
    _description = "Sale Forecast XLSX Report"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, report_detail, wizard_data):

        main_merge_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': '13',
             "font_color": 'black',
            "bg_color": '#F7DC6F',
            'font_name': 'Metropolis',
        })
        main_in_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': '13',
             "font_color": 'black',
            "bg_color": '#73C6B6',
            'font_name': 'Metropolis',
        })
        main_out_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': '13',
             "font_color": 'black',
            "bg_color": '#EB984E',
            'font_name': 'Metropolis',
        })
        main_balance_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': '13',
             "font_color": 'black',
            "bg_color": '#B2F776',
            'font_name': 'Metropolis',
        })
        main_product_format = workbook.add_format({
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': '13',
             "font_color": 'black',
            "bg_color": '#E9ECE7',
            'font_name': 'Metropolis',
        })
        format_data_header = workbook.add_format({
            "bold": 1,
            "border": 1,
            "align": 'center',
            "valign": 'vcenter',
            "font_color": 'black',
            "bg_color": '#F7DC6F',
            'font_size': '8',
            'font_name': 'Metropolis',
        })
        format_data_right = workbook.add_format({
            "border": 1,
            "align": 'right',
            "valign": 'vcenter',
            "font_color": 'black',
            'font_size': '8',
            'font_name': 'Metropolis',
            "num_format": "#,##0.00",
        })
        format_data_right_red = workbook.add_format({
            "border": 1,
            "align": 'right',
            "valign": 'vcenter',
            "font_color": 'black',
            "bg_color": '#F72E0A',
            'font_size': '8',
            'font_name': 'Metropolis',
            "num_format": "#,##0.00",
        })
        format_data_left = workbook.add_format({
            "border": 1,
            "align": 'left',
            "valign": 'vcenter',
            "font_color": 'black',
            'font_size': '8',
            'font_name': 'Metropolis',
            "num_format": "#,##0.00",
        })

        today_date = datetime.today()
        start_month = today_date.month - int(wizard_data.avg_period)
        end_month = today_date.month - 1
        start_date = datetime(today_date.year, start_month, 1)
        res = calendar.monthrange(today_date.year, end_month)
        day = res[1]
        end_date = datetime(today_date.year, end_month, day, 23, 59, 59)

        sale_records = self.env['sale.order.line'].search([
            ('state', '=', 'sale'),
            ('order_id.date_order', '>=', start_date),
            ('order_id.date_order', '<=', end_date),
        ])

        worksheet = workbook.add_worksheet('Sale Forecast Report')

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:K', 12)

        worksheet.merge_range('A2:K3', 'Plan Sale Forecast Report', main_merge_format)

        row = 5
        col = 0

        worksheet.write_string(row, col, 'Item', format_data_header)
        worksheet.write_string(row, col+1, 'Qty Available', format_data_header)
        worksheet.write_string(row, col+2, 'Qty To Way', format_data_header)
        worksheet.write_string(row, col+3, 'Total', format_data_header)
        worksheet.write_string(row, col+4, 'Average', format_data_header)
        worksheet.write_string(row, col+5, '1 Month', format_data_header)
        worksheet.write_string(row, col+6, '2 Month', format_data_header)
        worksheet.write_string(row, col+7, '3 Month', format_data_header)
        worksheet.write_string(row, col+8, '4 Month', format_data_header)
        worksheet.write_string(row, col+9, '5 Month', format_data_header)
        worksheet.write_string(row, col+10, '6 Month', format_data_header)

        row += 1

        prod_list = []
        for order in sale_records:
            if order.product_id.id not in prod_list:
                prod_list.append(order.product_id.id)

        for prod in prod_list:
            purchase_qty = self.env['purchase.order.line'].search([
                ('state', '=', 'draft'),
                ('product_id', '=', prod),
                ('order_id.picking_ids', '=', False),
            ])
            sale_qty = self.env['sale.order.line'].search([
                ('state', '=', 'sale'),
                ('product_id', '=', prod),
                ('order_id.date_order', '>=', start_date),
                ('order_id.date_order', '<=', end_date),
            ])
            sale_quant = 0.0
            count = 0
            for sale in sale_qty:
                count += 1
                sale_quant += sale.product_uom_qty
            pur_qty = 0.0
            if purchase_qty:
                for rec in purchase_qty:
                    pur_qty += rec.product_qty
            product_rec = self.env['product.product'].search([
                ('id', '=', prod),
            ])

            total = product_rec.virtual_available + pur_qty
            average = sale_quant/int(wizard_data.avg_period)
            new_value = total - average

            # print(2222222222222222222222222222222222222222222, product_rec.name, product_rec.virtual_available, pur_qty, sale_quant, total, count)

            worksheet.write_string(row, col, product_rec.name or '', format_data_left)
            worksheet.write_number(row, col+1, product_rec.virtual_available, format_data_right)
            worksheet.write_number(row, col+2, pur_qty, format_data_right)
            worksheet.write_number(row, col+3, total, format_data_right)
            worksheet.write_number(row, col+4, average, format_data_right)
            if new_value < 0:
                worksheet.write_number(row, col+5, new_value, format_data_right_red)
            else:
                worksheet.write_number(row, col + 5, new_value, format_data_right)
            new_value -= average
            if new_value < 0:
                worksheet.write_number(row, col+6, new_value, format_data_right_red)
            else:
                worksheet.write_number(row, col + 6, new_value, format_data_right)
            new_value -= average
            if new_value < 0:
                worksheet.write_number(row, col+7, new_value, format_data_right_red)
            else:
                worksheet.write_number(row, col + 7, new_value, format_data_right)
            new_value -= average
            if new_value < 0:
                worksheet.write_number(row, col+8, new_value, format_data_right_red)
            else:
                worksheet.write_number(row, col + 8, new_value, format_data_right)
            new_value -= average
            if new_value < 0:
                worksheet.write_number(row, col+9, new_value, format_data_right_red)
            else:
                worksheet.write_number(row, col + 9, new_value, format_data_right)
            new_value -= average
            if new_value < 0:
                worksheet.write_number(row, col+10, new_value, format_data_right_red)
            else:
                worksheet.write_number(row, col + 10, new_value, format_data_right)
            row += 1
