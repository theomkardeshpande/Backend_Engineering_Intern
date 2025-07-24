from flask import jsonify
from datetime import datetime, timedelta
from sqlalchemy import func

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def low_stock_alerts(company_id):
    # Assumptions:
    # - Low stock threshold stored in Product.low_stock_threshold (numeric)
    # - Recent sales within last 30 days
    # - Days until stockout = current_stock / avg_daily_sales (if avg_daily_sales > 0 else None)
    
    try:
        today = datetime.utcnow()
        recent_period = today - timedelta(days=30)

        # Subquery: recent sales aggregated per product per warehouse
        recent_sales_subq = (
            db.session.query(
                Sales.product_id,
                Sales.warehouse_id,
                func.sum(Sales.quantity).label('total_sold')
            )
            .join(Warehouse, Warehouse.id == Sales.warehouse_id)
            .filter(Sales.sale_date >= recent_period, Warehouse.company_id == company_id)
            .group_by(Sales.product_id, Sales.warehouse_id)
            .subquery()
        )

        # Query inventory joined with recent sales and supplier info
        alerts_query = (
            db.session.query(
                Inventory.product_id,
                Product.name.label('product_name'),
                Product.sku,
                Inventory.warehouse_id,
                Warehouse.name.label('warehouse_name'),
                Inventory.quantity.label('current_stock'),
                Product.low_stock_threshold.label('threshold'),
                Supplier.id.label('supplier_id'),
                Supplier.name.label('supplier_name'),
                Supplier.contact_email,
                recent_sales_subq.c.total_sold
            )
            .join(Product, Product.id == Inventory.product_id)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .join(product_suppliers, product_suppliers.c.product_id == Product.id)
            .join(Supplier, Supplier.id == product_suppliers.c.supplier_id)
            .join(recent_sales_subq, 
                  (recent_sales_subq.c.product_id == Inventory.product_id) &
                  (recent_sales_subq.c.warehouse_id == Inventory.warehouse_id))
            .filter(Warehouse.company_id == company_id)
            .filter(Inventory.quantity <= Product.low_stock_threshold)
        ).all()

        alerts = []
        for row in alerts_query:
            avg_daily_sales = row.total_sold / 30 if row.total_sold else None
            days_until_stockout = (row.current_stock / avg_daily_sales) if avg_daily_sales and avg_daily_sales > 0 else None

            alerts.append({
                "product_id": row.product_id,
                "product_name": row.product_name,
                "sku": row.sku,
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "current_stock": row.current_stock,
                "threshold": row.threshold,
                "days_until_stockout": round(days_until_stockout) if days_until_stockout else None,
                "supplier": {
                    "id": row.supplier_id,
                    "name": row.supplier_name,
                    "contact_email": row.contact_email
                }
            })

        response = {
            "alerts": alerts,
            "total_alerts": len(alerts)
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
