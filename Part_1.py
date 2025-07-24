from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json or {}

    # Validate required fields
    required_fields = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity']
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400
    
    # Check SKU uniqueness (assumes unique constraint on sku column)
    existing = Product.query.filter_by(sku=data['sku']).first()
    if existing:
        return jsonify({"error": "SKU already exists"}), 409
    
    try:
        # Convert price to Decimal
        price = Decimal(str(data['price']))
    except:
        return jsonify({"error": "Invalid price format"}), 400

    try:
        # Atomic transaction
        with db.session.begin_nested():
            product = Product(
                name=data['name'],
                sku=data['sku'],
                price=price,
                warehouse_id=data['warehouse_id']  # Consider if warehouse_id should be in product or only inventory
            )
            db.session.add(product)
            db.session.flush()  # Flush to get product.id for inventory FK
            
            inventory = Inventory(
                product_id=product.id,
                warehouse_id=data['warehouse_id'],
                quantity=int(data['initial_quantity'])
            )
            db.session.add(inventory)
        
        db.session.commit()
        return jsonify({"message": "Product created", "product_id": product.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
